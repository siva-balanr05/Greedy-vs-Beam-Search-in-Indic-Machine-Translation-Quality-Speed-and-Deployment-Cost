import pytest
from backend.app.services.evaluation_service import evaluation_service
from backend.app.services.cost_estimator import cost_estimator
from backend.app.services.resource_monitor import resource_monitor
from backend.app.schemas.schemas import CostEstimateRequest

def test_evaluation_service_exact_match():
    hyp = "Hello world from Tamil Nadu"
    ref = "Hello world from Tamil Nadu"
    res = evaluation_service.compute_sentence_metrics(hyp, ref)
    assert res["sentence_bleu"] is not None
    assert res["sentence_bleu"] == 100.0
    assert res["sentence_chrf"] is not None
    assert res["sentence_chrf"] == 100.0

def test_evaluation_service_partial_match():
    hyp = "Hello world from Tamil"
    ref = "Hello world from Tamil Nadu"
    res = evaluation_service.compute_sentence_metrics(hyp, ref)
    assert res["sentence_bleu"] is not None
    assert 0 < res["sentence_bleu"] < 100.0
    assert 0 < res["sentence_chrf"] < 100.0

def test_evaluation_service_missing_reference():
    hyp = "Hello world"
    res = evaluation_service.compute_sentence_metrics(hyp, None)
    assert res["sentence_bleu"] is None
    assert res["sentence_chrf"] is None
    assert "Reference translation not provided" in res["note"]

def test_corpus_evaluation():
    hyps = ["The cat sat on the mat.", "I like natural language processing."]
    refs = ["The cat sat on the mat.", "I like language processing."]
    res = evaluation_service.compute_corpus_metrics(hyps, refs)
    assert res["corpus_bleu"] is not None
    assert res["corpus_bleu"] > 50.0
    assert res["corpus_chrf"] is not None
    assert res["evaluated_samples"] == 2

def test_resource_monitor():
    mem = resource_monitor.get_process_memory_mb()
    assert mem > 0.0
    sys_m = resource_monitor.get_system_metrics()
    assert sys_m["system_ram_gb"] > 0.0
    assert 0.0 <= sys_m["ram_usage_percent"] <= 100.0

def test_cost_estimator_math():
    req = CostEstimateRequest(
        workload_sentences=1000,
        sentences_per_second_greedy=10.0,  # 100 seconds
        sentences_per_second_beam=2.0,     # 500 seconds
        cloud_cpu_hourly_cost=3.60         # $0.001 per second
    )
    res = cost_estimator.estimate_costs(req)
    assert res.cloud_cpu_greedy.inference_seconds == 100.0
    assert res.cloud_cpu_beam.inference_seconds == 500.0
    assert abs(res.cloud_cpu_greedy.total_workload_cost - 0.10) < 1e-4
    assert abs(res.cloud_cpu_beam.total_workload_cost - 0.50) < 1e-4
