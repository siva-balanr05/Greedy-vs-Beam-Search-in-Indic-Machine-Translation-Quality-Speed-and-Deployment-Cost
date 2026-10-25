import os
import threading
import time
from typing import Optional, Dict, Any, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from transformers.dynamic_module_utils import get_class_from_dynamic_module

# Ensure forward compatibility with transformers 5.x for IndicTransToolkit
try:
    import transformers.tokenization_utils
    import transformers.tokenization_utils_base
    if not hasattr(transformers.tokenization_utils, "PreTrainedTokenizerBase"):
        transformers.tokenization_utils.PreTrainedTokenizerBase = transformers.tokenization_utils_base.PreTrainedTokenizerBase
    from IndicTransToolkit import IndicProcessor
    INDIC_PROCESSOR_AVAILABLE = True
except Exception as _exc:
    INDIC_PROCESSOR_AVAILABLE = False
    IndicProcessor = None

from ..config import settings
from ..utils.logger import logger
from .resource_monitor import resource_monitor

class ModelService:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.model_name = settings.DEFAULT_MODEL_NAME
        self.device = settings.DEVICE
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        self.load_error = None
        self.init_duration_sec = 0.0
        self.is_indictrans = False
        try:
            self.indic_processor = IndicProcessor(inference=True) if INDIC_PROCESSOR_AVAILABLE else None
        except Exception as e:
            logger.warning(f"Failed to initialize IndicProcessor: {e}")
            self.indic_processor = None

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = ModelService()
            return cls._instance

    def _apply_indictrans_patches(self, repo_id: str):
        """
        Dynamically patches IndicTrans2 tokenizer and model classes
        to ensure forward-compatibility with modern Hugging Face Transformers (v5.x).
        """
        try:
            # 1. Patch Tokenizer __init__ to initialize _special_tokens_map
            tok_cls = get_class_from_dynamic_module(
                "tokenization_indictrans.IndicTransTokenizer", repo_id
            )
            orig_tok_init = tok_cls.__init__
            def patched_tok_init(self, *args, **kwargs):
                self._special_tokens_map = {}
                orig_tok_init(self, *args, **kwargs)
            tok_cls.__init__ = patched_tok_init

            # 2. Patch Model tie_weights to accept modern recompute_mapping kwargs
            model_cls = get_class_from_dynamic_module(
                "modeling_rotary_indictrans.RotaryIndicTransForConditionalGeneration", repo_id
            )
            def patched_tie_weights(self, *args, **kwargs):
                if hasattr(self, "model") and hasattr(self.model, "decoder") and hasattr(self, "lm_head"):
                    self.lm_head.weight = self.model.decoder.embed_tokens.weight
            model_cls.tie_weights = patched_tie_weights
            
            logger.info("Successfully applied modern Transformers patches for IndicTrans2.")
            return tok_cls, model_cls
        except Exception as e:
            logger.warning(f"Could not apply dynamic IndicTrans patches: {e}")
            return None, None

    def load_model(self, model_name: Optional[str] = None):
        """Loads the model and tokenizer lazily with thread synchronization."""
        with self._lock:
            if self.is_loaded and (model_name is None or model_name == self.model_name):
                return True

            target_model = model_name or self.model_name
            logger.info(f"Loading MT model: {target_model} on device: {self.device}...")
            start_time = time.perf_counter()
            self.load_error = None

            try:
                if "indictrans" in target_model.lower():
                    self.is_indictrans = True
                    tok_cls, model_cls = self._apply_indictrans_patches(target_model)
                    
                    if tok_cls and model_cls:
                        self.tokenizer = tok_cls.from_pretrained(target_model)
                        self.model = model_cls.from_pretrained(target_model)
                    else:
                        self.tokenizer = AutoTokenizer.from_pretrained(target_model, trust_remote_code=True)
                        self.model = AutoModelForSeq2SeqLM.from_pretrained(target_model, trust_remote_code=True)
                else:
                    self.is_indictrans = False
                    self.tokenizer = AutoTokenizer.from_pretrained(target_model)
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(target_model)

                self.model.to(self.device)
                self.model.eval()

                self.model_name = target_model
                self.is_loaded = True
                self.init_duration_sec = round(time.perf_counter() - start_time, 2)
                logger.info(f"Model {target_model} loaded in {self.init_duration_sec}s. Process RSS: {resource_monitor.get_process_memory_mb()}MB")

                # Pre-warm model execution kernels on CPU (Task 10/11: warm-up)
                try:
                    logger.info("Pre-warming model kernels on CPU...")
                    warm_inputs = self.tokenizer("tam_Taml eng_Latn வணக்கம்", return_tensors="pt")
                    warm_inputs = {k: v.to(self.device) for k, v in warm_inputs.items()}
                    with torch.no_grad():
                        _ = self.model.generate(**warm_inputs, max_new_tokens=4, use_cache=False)
                    logger.info("Model pre-warming complete.")
                except Exception as warm_err:
                    logger.warning(f"Model pre-warm warning (non-fatal): {warm_err}")

                return True

            except Exception as e:
                self.is_loaded = False
                self.load_error = str(e)
                logger.error(f"Failed to load model {target_model}: {e}", exc_info=True)
                raise RuntimeError(f"Model loading failed: {e}")

    def prepare_input(self, text: str, src_lang: str, tgt_lang: str) -> Tuple[Any, Dict[str, Any]]:
        """Formats the input text with language tags according to model architecture."""
        if not self.is_loaded:
            self.load_model()

        src_meta = settings.SUPPORTED_LANGUAGES.get(src_lang, {"code": "tam_Taml"})
        tgt_meta = settings.SUPPORTED_LANGUAGES.get(tgt_lang, {"code": "eng_Latn"})
        src_code = src_meta["code"]
        tgt_code = tgt_meta["code"]
        clean_text = text.strip()

        if self.is_indictrans:
            # IndicTrans2 uses script unification (mapping Indic scripts to Devanagari)
            # and prefixing "{src_code} {tgt_code} {normalized_text}".
            if not INDIC_PROCESSOR_AVAILABLE or IndicProcessor is None:
                raise RuntimeError(
                    "IndicProcessor from IndicTransToolkit is required for IndicTrans2 script unification. "
                    "Cannot translate without script unification as raw script causes severe hallucinations."
                )
            
            ip = IndicProcessor(inference=True)
            preprocessed = ip.preprocess_batch([clean_text], src_lang=src_code, tgt_lang=tgt_code)
            formatted_text = preprocessed[0]
            inputs = self.tokenizer(formatted_text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        else:
            # NLLB or generic Seq2Seq
            if hasattr(self.tokenizer, "src_lang"):
                self.tokenizer.src_lang = src_code
            inputs = self.tokenizer(clean_text, return_tensors="pt", padding=True, truncation=True, max_length=512)

        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        return inputs, {
            "src_lang": src_lang,
            "tgt_lang": tgt_lang,
            "src_code": src_code,
            "tgt_code": tgt_code,
            "original_text": clean_text
        }

    def decode_output(
        self,
        output_tokens,
        tgt_code: str = "eng_Latn",
        src_text: Optional[str] = None,
        src_code: str = "tam_Taml"
    ) -> str:
        """Decodes model output tokens into natural text and applies postprocessing."""
        if hasattr(output_tokens, "dim") and output_tokens.dim() == 1:
            output_tokens = output_tokens.unsqueeze(0)

        if self.is_indictrans:
            decoded_list = self.tokenizer.batch_decode(output_tokens, src=False, skip_special_tokens=True)
            if INDIC_PROCESSOR_AVAILABLE and IndicProcessor is not None and decoded_list:
                try:
                    # IndicProcessor requires a paired preprocess call to populate its placeholder entity map queue
                    # before postprocess_batch is called. An isolated instance ensures thread safety and prevents
                    # Queue.get() deadlocks on consecutive or concurrent generations.
                    ip = IndicProcessor(inference=True)
                    ip.preprocess_batch([src_text or ""], src_lang=src_code, tgt_lang=tgt_code)
                    decoded_list = ip.postprocess_batch(decoded_list, lang=tgt_code)
                except Exception as e:
                    logger.warning(f"IndicProcessor postprocessing fallback: {e}")
        else:
            decoded_list = self.tokenizer.batch_decode(output_tokens, skip_special_tokens=True)
        
        if decoded_list:
            text = decoded_list[0].strip()
            # Clean any leading or trailing token markers
            text = text.replace("</s>", "").replace("<s>", "").replace("<pad>", "").strip()
            return text
        return ""

    def get_info(self) -> Dict[str, Any]:
        """Returns model status and metadata."""
        src_langs = [{"code": k, "name": v["name"]} for k, v in settings.SUPPORTED_LANGUAGES.items() if k != "en"]
        tgt_langs = [{"code": "en", "name": "English"}]
        
        return {
            "model_name": self.model_name,
            "model_type": "IndicTrans2-Distilled-200M" if self.is_indictrans else "Seq2Seq-Transformer",
            "loaded": self.is_loaded,
            "device": self.device,
            "supported_source_languages": src_langs,
            "supported_target_languages": tgt_langs,
            "default_beam_widths": settings.SUPPORTED_BEAMS,
            "memory_rss_mb": resource_monitor.get_process_memory_mb(),
            "init_duration_sec": self.init_duration_sec,
            "load_error": self.load_error
        }

model_service = ModelService.get_instance()
