from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    device: str
    system_ram_gb: float
    ram_usage_percent: float
    cpu_percent: float

class ModelInfoResponse(BaseModel):
    model_name: str
    model_type: str
    loaded: bool
    device: str
    supported_source_languages: List[Dict[str, str]]
    supported_target_languages: List[Dict[str, str]]
    default_beam_widths: List[int]
    memory_rss_mb: float

class TranslateRequest(BaseModel):
    source_text: str = Field(..., min_length=1, max_length=2000, description="Input text to translate")
    source_lang: str = Field(default="ta", description="Source language code (e.g., 'ta')")
    target_lang: str = Field(default="en", description="Target language code (e.g., 'en')")
    decoding_method: str = Field(default="greedy", description="'greedy' or 'beam'")
    beam_width: int = Field(default=4, ge=1, le=10, description="Beam width (1 for greedy, 2-10 for beam)")
    max_new_tokens: int = Field(default=128, ge=16, le=512)
    length_penalty: float = Field(default=1.0, ge=0.1, le=3.0)
    reference_text: Optional[str] = Field(default=None, description="Optional ground truth reference for BLEU/chrF")

class DecodingMetrics(BaseModel):
    method: str
    beam_width: int
    translation: str
    latency_ms: float
    tokens_generated: int
    tokens_per_second: float
    process_memory_mb: float
    memory_delta_mb: float
    sentence_bleu: Optional[float] = None
    sentence_chrf: Optional[float] = None
    evaluation_note: Optional[str] = None

class TranslateResponse(BaseModel):
    source_text: str
    source_lang: str
    target_lang: str
    result: DecodingMetrics

class CompareRequest(BaseModel):
    source_text: str = Field(..., min_length=1, max_length=2000)
    source_lang: str = Field(default="ta")
    target_lang: str = Field(default="en")
    beam_width: int = Field(default=4, ge=2, le=8)
    max_new_tokens: int = Field(default=128, ge=16, le=512)
    length_penalty: float = Field(default=1.0)
    reference_text: Optional[str] = None

class CompareResponse(BaseModel):
    source_text: str
    source_lang: str
    target_lang: str
    reference_text: Optional[str] = None
    greedy: DecodingMetrics
    beam: DecodingMetrics
    latency_difference_ms: float
    latency_ratio: float
    identical_output: bool

class BenchmarkSample(BaseModel):
    source_text: str
    reference_text: Optional[str] = None

class BenchmarkRequest(BaseModel):
    dataset_name: str = Field(default="flores200_sample")
    source_lang: str = Field(default="ta")
    target_lang: str = Field(default="en")
    beam_widths: List[int] = Field(default=[1, 2, 4, 8])
    max_samples: Optional[int] = Field(default=25, ge=1, le=200)
    max_new_tokens: int = Field(default=128)
    samples: Optional[List[BenchmarkSample]] = None

class BenchmarkMetricSummary(BaseModel):
    method: str
    beam_width: int
    evaluated_samples: int
    corpus_bleu: Optional[float] = None
    corpus_chrf: Optional[float] = None
    total_time_seconds: float
    avg_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    sentences_per_second: float
    tokens_per_second: float
    peak_memory_mb: float
    errors: int

class BenchmarkJobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed, cancelled
    progress_percent: float
    current_step: str
    total_steps: int
    completed_steps: int
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    results: Optional[List[BenchmarkMetricSummary]] = None

class CostEstimateRequest(BaseModel):
    workload_sentences: int = Field(default=10000, ge=1)
    sentences_per_second_greedy: float = Field(default=5.0, ge=0.01)
    sentences_per_second_beam: float = Field(default=1.5, ge=0.01)
    cloud_cpu_hourly_cost: float = Field(default=0.08, ge=0.0)  # e.g., AWS c6i.large ~$0.085/hr
    cloud_gpu_hourly_cost: float = Field(default=0.52, ge=0.0)  # e.g., AWS g4dn.xlarge ~$0.526/hr
    local_power_watts: float = Field(default=65.0, ge=1.0)
    local_kwh_cost: float = Field(default=0.15, ge=0.0)

class CostBreakdown(BaseModel):
    inference_seconds: float
    cost_per_1000_sentences: float
    total_workload_cost: float
    monthly_continuous_cost: float

class CostEstimateResponse(BaseModel):
    workload_sentences: int
    local_cpu_greedy: CostBreakdown
    local_cpu_beam: CostBreakdown
    cloud_cpu_greedy: CostBreakdown
    cloud_cpu_beam: CostBreakdown
    cloud_gpu_greedy: CostBreakdown
    cloud_gpu_beam: CostBreakdown
    methodology_note: str

class ExperimentSummary(BaseModel):
    id: int
    experiment_name: str
    model_name: str
    source_lang: str
    target_lang: str
    dataset_name: str
    sample_count: int
    created_at: str
    greedy_bleu: Optional[float] = None
    greedy_chrf: Optional[float] = None
    greedy_latency_ms: Optional[float] = None
    beam_bleu: Optional[float] = None
    beam_chrf: Optional[float] = None
    beam_latency_ms: Optional[float] = None
    best_beam_width: Optional[int] = None

class ExperimentDetail(BaseModel):
    summary: ExperimentSummary
    metrics: List[BenchmarkMetricSummary]
    sentence_records: List[Dict[str, Any]]
