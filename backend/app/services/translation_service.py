import time
from typing import Optional, Dict, Any
import torch

from .model_service import model_service
from .evaluation_service import evaluation_service
from .resource_monitor import resource_monitor
from ..schemas.schemas import (
    TranslateRequest,
    TranslateResponse,
    CompareRequest,
    CompareResponse,
    DecodingMetrics
)
from ..utils.logger import logger

class TranslationService:
    def __init__(self):
        self.model_svc = model_service

    def _generate_with_metrics(
        self,
        inputs: Dict[str, Any],
        lang_meta: Dict[str, Any],
        method: str,
        beam_width: int,
        max_new_tokens: int,
        length_penalty: float,
        reference_text: Optional[str] = None
    ) -> DecodingMetrics:
        """
        Executes generation using specified decoding parameters and records high-resolution metrics.
        Distinguishes pure inference latency from model initialization and text preprocessing.
        """
        # Ensure model is ready
        if not self.model_svc.is_loaded:
            self.model_svc.load_model()

        model = self.model_svc.model
        mem_before = resource_monitor.get_process_memory_mb()
        
        # Determine explicit special token IDs
        pad_token_id = getattr(self.model_svc.tokenizer, "pad_token_id", 1)
        eos_token_id = getattr(self.model_svc.tokenizer, "eos_token_id", 2)
        bos_token_id = getattr(self.model_svc.tokenizer, "bos_token_id", 0)
        decoder_start_token_id = getattr(model.config, "decoder_start_token_id", eos_token_id)

        # Clone input tensors to prevent in-place mutation across runs
        gen_kwargs = {
            k: (v.clone() if isinstance(v, torch.Tensor) else v) for k, v in inputs.items()
        }
        gen_kwargs["max_new_tokens"] = max_new_tokens
        gen_kwargs["pad_token_id"] = pad_token_id
        gen_kwargs["eos_token_id"] = eos_token_id
        gen_kwargs["bos_token_id"] = bos_token_id
        gen_kwargs["decoder_start_token_id"] = decoder_start_token_id
        gen_kwargs["use_cache"] = False  # Clean forward pass across PyTorch/Transformers CPU builds

        if method == "greedy" or beam_width == 1:
            actual_method = "greedy"
            actual_beam = 1
            gen_kwargs["num_beams"] = 1
            gen_kwargs["do_sample"] = False
        else:
            actual_method = "beam"
            actual_beam = beam_width
            gen_kwargs["num_beams"] = beam_width
            gen_kwargs["do_sample"] = False
            gen_kwargs["length_penalty"] = length_penalty
            gen_kwargs["early_stopping"] = True

        # High-resolution timing of pure autoregressive generation
        t0 = time.perf_counter()
        with torch.no_grad():
            outputs = model.generate(**gen_kwargs)
        t1 = time.perf_counter()

        inference_duration_sec = max(t1 - t0, 1e-6)
        latency_ms = round(inference_duration_sec * 1000.0, 2)
        mem_after = resource_monitor.get_process_memory_mb()
        mem_delta = round(max(0.0, mem_after - mem_before), 2)

        # Output decoding and postprocessing with IndicProcessor
        tgt_code = lang_meta.get("tgt_code", "eng_Latn")
        src_code = lang_meta.get("src_code", "tam_Taml")
        original_text = lang_meta.get("original_text", "")
        translation = self.model_svc.decode_output(
            outputs,
            tgt_code=tgt_code,
            src_text=original_text,
            src_code=src_code
        )
        
        # Token metrics: count generated tokens in output sequence (excluding decoder start token)
        raw_tokens = outputs[0].tolist() if hasattr(outputs, "shape") else list(outputs[0])
        if len(raw_tokens) > 1 and raw_tokens[0] == decoder_start_token_id:
            tokens_generated = len(raw_tokens) - 1
        else:
            tokens_generated = len(raw_tokens)
        tokens_per_sec = round(tokens_generated / inference_duration_sec, 2)

        # Diagnostic logging (Task 7)
        logger.info(
            f"[Inference Diagnostic] model={self.model_svc.model_name} | "
            f"direction={lang_meta.get('src_code', 'unknown')}->{tgt_code} | "
            f"method={actual_method} (k={actual_beam}) | "
            f"max_new_tokens={max_new_tokens} | "
            f"latency={latency_ms}ms | tokens_gen={tokens_generated} ({tokens_per_sec} tok/s) | "
            f"token_ids={raw_tokens} | "
            f"decoded='{translation}'"
        )

        # Quality metrics (sentence-level only when valid reference provided)
        eval_metrics = evaluation_service.compute_sentence_metrics(translation, reference_text)

        return DecodingMetrics(
            method=actual_method,
            beam_width=actual_beam,
            translation=translation,
            latency_ms=latency_ms,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_sec,
            process_memory_mb=mem_after,
            memory_delta_mb=mem_delta,
            sentence_bleu=eval_metrics.get("sentence_bleu"),
            sentence_chrf=eval_metrics.get("sentence_chrf"),
            evaluation_note=eval_metrics.get("note")
        )

    def translate(self, req: TranslateRequest) -> TranslateResponse:
        """Translates a single source sentence using the requested decoding strategy."""
        inputs, lang_meta = self.model_svc.prepare_input(req.source_text, req.source_lang, req.target_lang)
        
        metrics = self._generate_with_metrics(
            inputs=inputs,
            lang_meta=lang_meta,
            method=req.decoding_method,
            beam_width=req.beam_width,
            max_new_tokens=req.max_new_tokens,
            length_penalty=req.length_penalty,
            reference_text=req.reference_text
        )

        return TranslateResponse(
            source_text=req.source_text,
            source_lang=req.source_lang,
            target_lang=req.target_lang,
            result=metrics
        )

    def compare(self, req: CompareRequest) -> CompareResponse:
        """
        Runs both Greedy Search and Beam Search on the IDENTICAL input and model state,
        enabling rigorous pair-wise scientific comparison.
        """
        inputs, lang_meta = self.model_svc.prepare_input(req.source_text, req.source_lang, req.target_lang)

        # 1. Greedy Search Run (num_beams=1)
        greedy_metrics = self._generate_with_metrics(
            inputs=inputs,
            lang_meta=lang_meta,
            method="greedy",
            beam_width=1,
            max_new_tokens=req.max_new_tokens,
            length_penalty=1.0,
            reference_text=req.reference_text
        )

        # 2. Beam Search Run (num_beams=k)
        beam_metrics = self._generate_with_metrics(
            inputs=inputs,
            lang_meta=lang_meta,
            method="beam",
            beam_width=req.beam_width,
            max_new_tokens=req.max_new_tokens,
            length_penalty=req.length_penalty,
            reference_text=req.reference_text
        )

        latency_diff = round(beam_metrics.latency_ms - greedy_metrics.latency_ms, 2)
        ratio = round(beam_metrics.latency_ms / max(greedy_metrics.latency_ms, 0.1), 2)
        identical = (greedy_metrics.translation.strip().lower() == beam_metrics.translation.strip().lower())

        return CompareResponse(
            source_text=req.source_text,
            source_lang=req.source_lang,
            target_lang=req.target_lang,
            reference_text=req.reference_text,
            greedy=greedy_metrics,
            beam=beam_metrics,
            latency_difference_ms=latency_diff,
            latency_ratio=ratio,
            identical_output=identical
        )

translation_service = TranslationService()
