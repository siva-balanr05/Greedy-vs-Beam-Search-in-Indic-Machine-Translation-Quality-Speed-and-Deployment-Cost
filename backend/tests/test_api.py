import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "system_ram_gb" in data
    assert "cpu_percent" in data

def test_model_info():
    response = client.get("/api/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "supported_source_languages" in data
    assert any(lang["code"] == "ta" for lang in data["supported_source_languages"])

def test_translation_validation_empty_text():
    response = client.post("/api/translate", json={
        "source_text": "",
        "source_lang": "ta",
        "target_lang": "en",
        "decoding_method": "greedy"
    })
    # Pydantic validation failure returns 422
    assert response.status_code == 422

def test_translation_validation_invalid_beam():
    response = client.post("/api/translate", json={
        "source_text": "வணக்கம்",
        "source_lang": "ta",
        "target_lang": "en",
        "beam_width": 25  # Exceeds max 10
    })
    assert response.status_code == 422

def test_translate_endpoint_mocked():
    from unittest.mock import patch
    from backend.app.schemas.schemas import TranslateResponse, DecodingMetrics

    dummy_metrics = DecodingMetrics(
        method="greedy",
        beam_width=1,
        translation="Hello world",
        latency_ms=120.0,
        tokens_generated=3,
        tokens_per_second=25.0,
        process_memory_mb=450.0,
        memory_delta_mb=0.0
    )
    dummy_resp = TranslateResponse(
        source_text="வணக்கம்",
        source_lang="ta",
        target_lang="en",
        result=dummy_metrics
    )

    with patch("backend.app.api.routes_translation.translation_service.translate", return_value=dummy_resp):
        response = client.post("/api/translate", json={
            "source_text": "வணக்கம்",
            "source_lang": "ta",
            "target_lang": "en",
            "decoding_method": "greedy",
            "beam_width": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert data["source_text"] == "வணக்கம்"
        assert data["result"]["translation"] == "Hello world"
        assert data["result"]["method"] == "greedy"
        assert data["result"]["tokens_per_second"] == 25.0


def test_compare_endpoint_mocked():
    from unittest.mock import patch
    from backend.app.schemas.schemas import CompareResponse, DecodingMetrics

    dummy_greedy = DecodingMetrics(
        method="greedy",
        beam_width=1,
        translation="How are you doing?",
        latency_ms=100.0,
        tokens_generated=5,
        tokens_per_second=50.0,
        process_memory_mb=450.0,
        memory_delta_mb=0.0,
        sentence_bleu=20.0,
        sentence_chrf=45.0
    )
    dummy_beam = DecodingMetrics(
        method="beam",
        beam_width=4,
        translation="Hello, how are you?",
        latency_ms=150.0,
        tokens_generated=5,
        tokens_per_second=33.3,
        process_memory_mb=450.0,
        memory_delta_mb=0.0,
        sentence_bleu=100.0,
        sentence_chrf=100.0
    )
    dummy_resp = CompareResponse(
        source_text="வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
        source_lang="ta",
        target_lang="en",
        reference_text="Hello, how are you?",
        greedy=dummy_greedy,
        beam=dummy_beam,
        latency_difference_ms=50.0,
        latency_ratio=1.5,
        identical_output=False
    )

    with patch("backend.app.api.routes_translation.translation_service.compare", return_value=dummy_resp):
        response = client.post("/api/translate/compare", json={
            "source_text": "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
            "source_lang": "ta",
            "target_lang": "en",
            "beam_width": 4,
            "reference_text": "Hello, how are you?"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["greedy"]["translation"] == "How are you doing?"
        assert data["beam"]["translation"] == "Hello, how are you?"
        assert data["latency_ratio"] == 1.5
        assert data["identical_output"] is False
        assert data["beam"]["sentence_bleu"] == 100.0


def test_datasets_list():
    response = client.get("/api/datasets")
    assert response.status_code == 200
    datasets = response.json()
    assert len(datasets) > 0
    assert datasets[0]["id"] == "flores200_sample"

def test_cost_estimate():
    response = client.post("/api/cost/estimate", json={
        "workload_sentences": 5000,
        "sentences_per_second_greedy": 5.0,
        "sentences_per_second_beam": 2.0,
        "cloud_cpu_hourly_cost": 0.08,
        "cloud_gpu_hourly_cost": 0.50,
        "local_power_watts": 65.0,
        "local_kwh_cost": 0.15
    })
    assert response.status_code == 200
    data = response.json()
    assert data["workload_sentences"] == 5000
    assert data["cloud_cpu_greedy"]["inference_seconds"] == 1000.0
    assert data["cloud_cpu_beam"]["inference_seconds"] == 2500.0
    assert data["cloud_cpu_greedy"]["total_workload_cost"] < data["cloud_cpu_beam"]["total_workload_cost"]
