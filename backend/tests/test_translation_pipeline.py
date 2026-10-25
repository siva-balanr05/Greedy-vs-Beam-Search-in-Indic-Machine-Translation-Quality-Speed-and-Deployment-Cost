import pytest
from unittest.mock import MagicMock, patch
import torch

from backend.app.services.model_service import model_service
from backend.app.services.translation_service import translation_service
from backend.app.schemas.schemas import TranslateRequest, CompareRequest, DecodingMetrics

def test_generation_config_greedy_vs_beam_mocked():
    """Verifies generation parameters (num_beams, do_sample, early_stopping, special tokens) without running full model."""
    mock_model = MagicMock()
    mock_model.generate.return_value = torch.tensor([[2, 10, 2]])
    mock_model.config.decoder_start_token_id = 2

    mock_tokenizer = MagicMock()
    mock_tokenizer.pad_token_id = 1
    mock_tokenizer.eos_token_id = 2
    mock_tokenizer.bos_token_id = 0
    mock_tokenizer.batch_decode.return_value = ["Hello world"]

    with patch.object(model_service, "model", mock_model), \
         patch.object(model_service, "tokenizer", mock_tokenizer), \
         patch.object(model_service, "is_loaded", True), \
         patch.object(model_service, "decode_output", return_value="Hello world"):

        # 1. Test Greedy Generation kwargs
        inputs = {"input_ids": torch.tensor([[16, 4, 10, 2]]), "attention_mask": torch.tensor([[1, 1, 1, 1]])}
        metrics_greedy = translation_service._generate_with_metrics(
            inputs=inputs,
            lang_meta={"src_code": "tam_Taml", "tgt_code": "eng_Latn"},
            method="greedy",
            beam_width=1,
            max_new_tokens=64,
            length_penalty=1.0
        )

        assert metrics_greedy.method == "greedy"
        assert metrics_greedy.beam_width == 1
        _, kwargs_greedy = mock_model.generate.call_args
        assert kwargs_greedy["num_beams"] == 1
        assert kwargs_greedy["do_sample"] is False
        assert kwargs_greedy["max_new_tokens"] == 64
        assert kwargs_greedy["decoder_start_token_id"] == 2

        # 2. Test Beam Generation kwargs (k=4)
        metrics_beam = translation_service._generate_with_metrics(
            inputs=inputs,
            lang_meta={"src_code": "tam_Taml", "tgt_code": "eng_Latn"},
            method="beam",
            beam_width=4,
            max_new_tokens=64,
            length_penalty=1.2
        )

        assert metrics_beam.method == "beam"
        assert metrics_beam.beam_width == 4
        _, kwargs_beam = mock_model.generate.call_args
        assert kwargs_beam["num_beams"] == 4
        assert kwargs_beam["do_sample"] is False
        assert kwargs_beam["early_stopping"] is True
        assert kwargs_beam["length_penalty"] == 1.2


def test_compare_request_uses_same_inputs_and_direction():
    """Verifies that compare runs both strategies on the identical input and direction."""
    req = CompareRequest(
        source_text="வணக்கம்",
        source_lang="ta",
        target_lang="en",
        beam_width=4,
        max_new_tokens=50
    )

    dummy_greedy = DecodingMetrics(
        method="greedy",
        beam_width=1,
        translation="Hello",
        latency_ms=100.0,
        tokens_generated=3,
        tokens_per_second=30.0,
        process_memory_mb=500.0,
        memory_delta_mb=0.0
    )

    dummy_beam = DecodingMetrics(
        method="beam",
        beam_width=4,
        translation="Hello",
        latency_ms=250.0,
        tokens_generated=3,
        tokens_per_second=12.0,
        process_memory_mb=500.0,
        memory_delta_mb=0.0
    )

    with patch.object(translation_service, "_generate_with_metrics", side_effect=[dummy_greedy, dummy_beam]) as mock_gen, \
         patch.object(model_service, "prepare_input", return_value=({"input_ids": torch.tensor([[1]])}, {"src_code": "tam_Taml", "tgt_code": "eng_Latn"})):

        resp = translation_service.compare(req)

        assert mock_gen.call_count == 2
        # First call is greedy (beam_width=1)
        first_call_kwargs = mock_gen.call_args_list[0].kwargs
        assert first_call_kwargs["method"] == "greedy"
        assert first_call_kwargs["beam_width"] == 1

        # Second call is beam (beam_width=4)
        second_call_kwargs = mock_gen.call_args_list[1].kwargs
        assert second_call_kwargs["method"] == "beam"
        assert second_call_kwargs["beam_width"] == 4

        assert resp.source_text == "வணக்கம்"
        assert resp.greedy.translation == "Hello"
        assert resp.beam.translation == "Hello"
        assert resp.identical_output is True
        assert resp.latency_ratio == 2.5


def test_tamil_greeting_semantic_plausibility():
    """
    Integration test: checks semantic plausibility of Tamil greeting translation.
    Input: 'வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?'
    Expected semantic concept: inquiry about well-being / greeting ('hello', 'how', 'you', 'doing', 'are').
    """
    if not model_service.is_loaded:
        try:
            model_service.load_model()
        except Exception as e:
            pytest.skip(f"Model checkpoint not available or cannot load in test environment: {e}")

    req = TranslateRequest(
        source_text="வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
        source_lang="ta",
        target_lang="en",
        decoding_method="greedy",
        beam_width=1,
        max_new_tokens=64
    )

    resp = translation_service.translate(req)
    translation = resp.result.translation.lower()

    # Verify plausible greeting / inquiry semantic markers
    plausible_tokens = ["how", "are", "you", "doing", "hello", "well"]
    matched = [t for t in plausible_tokens if t in translation]

    assert len(matched) >= 2, (
        f"Translation '{resp.result.translation}' lacks plausible semantic greeting markers. "
        f"Expected at least 2 tokens from {plausible_tokens}."
    )

    # Ensure it's not the broken hallucinated outputs from before
    assert "theres a lot of people" not in translation
    assert "in addition to this" not in translation


def test_tamil_greeting_beam_semantic_plausibility():
    """
    Integration test: checks semantic plausibility of Beam Search (k=4) on Tamil greeting.
    Input: 'வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?'
    Expected semantic concept: inquiry about well-being / greeting ('hello', 'how', 'are', 'you').
    """
    if not model_service.is_loaded:
        try:
            model_service.load_model()
        except Exception as e:
            pytest.skip(f"Model checkpoint not available or cannot load in test environment: {e}")

    req = TranslateRequest(
        source_text="வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
        source_lang="ta",
        target_lang="en",
        decoding_method="beam",
        beam_width=4,
        max_new_tokens=64
    )

    resp = translation_service.translate(req)
    translation = resp.result.translation.lower()

    plausible_tokens = ["how", "are", "you", "doing", "hello", "well"]
    matched = [t for t in plausible_tokens if t in translation]

    assert len(matched) >= 2, (
        f"Beam translation '{resp.result.translation}' lacks plausible semantic greeting markers."
    )
    assert "theres a lot of people" not in translation
    assert "in addition to this" not in translation


def test_tamil_greeting_compare_side_by_side_live():
    """
    Integration test: verifies compare() executes both Greedy and Beam (k=4) consecutively
    without deadlock or state corruption on the live model.
    """
    if not model_service.is_loaded:
        try:
            model_service.load_model()
        except Exception as e:
            pytest.skip(f"Model checkpoint not available or cannot load in test environment: {e}")

    req = CompareRequest(
        source_text="வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
        source_lang="ta",
        target_lang="en",
        beam_width=4,
        max_new_tokens=64,
        reference_text="Hello, how are you?"
    )

    resp = translation_service.compare(req)

    assert resp.greedy.translation != ""
    assert resp.beam.translation != ""
    assert resp.greedy.latency_ms > 0
    assert resp.beam.latency_ms > 0
    assert resp.greedy.tokens_per_second > 0
    assert resp.beam.tokens_per_second > 0

    # Ensure valid human reference produces BLEU/chrF
    assert resp.greedy.sentence_bleu is not None
    assert resp.beam.sentence_bleu is not None
    assert resp.beam.sentence_bleu == 100.0  # Exact match for Beam search

    # Hallucination check
    assert "theres a lot of people" not in resp.greedy.translation.lower()
    assert "in addition to this" not in resp.beam.translation.lower()

