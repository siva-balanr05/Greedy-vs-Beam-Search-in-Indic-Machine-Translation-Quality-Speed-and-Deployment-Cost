import time
import uuid
import threading
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from .model_service import model_service
from .translation_service import translation_service
from .evaluation_service import evaluation_service
from .resource_monitor import resource_monitor
from ..database.db import save_experiment
from ..schemas.schemas import (
    BenchmarkRequest,
    BenchmarkJobStatus,
    BenchmarkMetricSummary,
    BenchmarkSample
)
from ..utils.logger import logger

class BenchmarkService:
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def start_benchmark(self, req: BenchmarkRequest, samples: List[BenchmarkSample]) -> str:
        """Initiates an asynchronous benchmarking job."""
        job_id = str(uuid.uuid4())[:8]
        
        with self._lock:
            self.jobs[job_id] = {
                "job_id": job_id,
                "status": "pending",
                "progress_percent": 0.0,
                "current_step": "Initializing benchmark...",
                "total_steps": len(req.beam_widths) * len(samples),
                "completed_steps": 0,
                "created_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "error_message": None,
                "cancel_requested": False,
                "results": None,
                "experiment_id": None
            }

        # Spawn background execution thread
        thread = threading.Thread(
            target=self._run_benchmark_job,
            args=(job_id, req, samples),
            daemon=True
        )
        thread.start()
        return job_id

    def cancel_job(self, job_id: str) -> bool:
        """Signals cancellation to an active benchmark job."""
        with self._lock:
            if job_id in self.jobs and self.jobs[job_id]["status"] in ("pending", "running"):
                self.jobs[job_id]["cancel_requested"] = True
                self.jobs[job_id]["status"] = "cancelled"
                self.jobs[job_id]["current_step"] = "Benchmark cancelled by user."
                return True
        return False

    def get_job_status(self, job_id: str) -> Optional[BenchmarkJobStatus]:
        """Returns the current status and metrics of a benchmark job."""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return None
            return BenchmarkJobStatus(
                job_id=job["job_id"],
                status=job["status"],
                progress_percent=round(job["progress_percent"], 1),
                current_step=job["current_step"],
                total_steps=job["total_steps"],
                completed_steps=job["completed_steps"],
                error_message=job["error_message"],
                created_at=job["created_at"],
                completed_at=job["completed_at"],
                results=job["results"]
            )

    def _run_benchmark_job(self, job_id: str, req: BenchmarkRequest, samples: List[BenchmarkSample]):
        """Worker thread loop executing the benchmark across beam widths."""
        with self._lock:
            self.jobs[job_id]["status"] = "running"
            self.jobs[job_id]["current_step"] = "Warming up model..."

        try:
            # 1. Warm-up inference
            if not model_service.is_loaded:
                model_service.load_model()
            
            # Short warm-up on dummy sample
            try:
                warm_inp, warm_meta = model_service.prepare_input("வணக்கம்", req.source_lang, req.target_lang)
                _ = model_service.model.generate(**warm_inp, max_new_tokens=10, use_cache=False)
            except Exception as e:
                logger.warning(f"Warm-up run encountered note: {e}")

            all_summaries: List[BenchmarkMetricSummary] = []
            all_sentence_records: List[Dict[str, Any]] = []
            
            total_steps = len(req.beam_widths) * len(samples)
            completed_steps = 0

            # 2. Iterate through each beam width
            for beam in req.beam_widths:
                # Check for cancellation
                with self._lock:
                    if self.jobs[job_id]["cancel_requested"]:
                        logger.info(f"Benchmark job {job_id} cancelled.")
                        return

                method_label = "greedy" if beam == 1 else "beam"
                with self._lock:
                    self.jobs[job_id]["current_step"] = f"Evaluating {method_label.upper()} (Beam width {beam})..."

                latencies_ms: List[float] = []
                tokens_count_list: List[int] = []
                hypotheses: List[str] = []
                references: List[str] = []
                errors = 0
                peak_mem = resource_monitor.get_process_memory_mb()

                t_start = time.perf_counter()

                for idx, sample in enumerate(samples):
                    with self._lock:
                        if self.jobs[job_id]["cancel_requested"]:
                            return

                    try:
                        inputs, lang_meta = model_service.prepare_input(
                            sample.source_text, req.source_lang, req.target_lang
                        )
                        
                        m = translation_service._generate_with_metrics(
                            inputs=inputs,
                            lang_meta=lang_meta,
                            method=method_label,
                            beam_width=beam,
                            max_new_tokens=req.max_new_tokens,
                            length_penalty=1.0,
                            reference_text=sample.reference_text
                        )
                        
                        latencies_ms.append(m.latency_ms)
                        tokens_count_list.append(m.tokens_generated)
                        hypotheses.append(m.translation)
                        ref = sample.reference_text or ""
                        references.append(ref)
                        peak_mem = max(peak_mem, m.process_memory_mb)

                        all_sentence_records.append({
                            "sentence_index": idx,
                            "source_text": sample.source_text,
                            "reference_text": ref,
                            "method": method_label,
                            "beam_width": beam,
                            "translation": m.translation,
                            "latency_ms": m.latency_ms,
                            "sentence_bleu": m.sentence_bleu,
                            "sentence_chrf": m.sentence_chrf,
                            "tokens_count": m.tokens_generated
                        })

                    except Exception as err:
                        errors += 1
                        logger.error(f"Error on sample {idx} (beam {beam}): {err}")
                        hypotheses.append("")
                        references.append(sample.reference_text or "")

                    completed_steps += 1
                    with self._lock:
                        self.jobs[job_id]["completed_steps"] = completed_steps
                        self.jobs[job_id]["progress_percent"] = (completed_steps / total_steps) * 100.0

                t_end = time.perf_counter()
                total_duration_sec = round(t_end - t_start, 2)

                # Compute statistical percentiles
                if latencies_ms:
                    avg_lat = round(float(np.mean(latencies_ms)), 2)
                    med_lat = round(float(np.median(latencies_ms)), 2)
                    p95_lat = round(float(np.percentile(latencies_ms, 95)), 2)
                else:
                    avg_lat, med_lat, p95_lat = 0.0, 0.0, 0.0

                total_evaluated = len(latencies_ms)
                sps = round(total_evaluated / max(total_duration_sec, 0.001), 2)
                total_tokens = sum(tokens_count_list)
                tps = round(total_tokens / max(total_duration_sec, 0.001), 2)

                # Corpus-level SacreBLEU & chrF
                corpus_scores = evaluation_service.compute_corpus_metrics(hypotheses, references)

                summary = BenchmarkMetricSummary(
                    method=method_label,
                    beam_width=beam,
                    evaluated_samples=total_evaluated,
                    corpus_bleu=corpus_scores.get("corpus_bleu"),
                    corpus_chrf=corpus_scores.get("corpus_chrf"),
                    total_time_seconds=total_duration_sec,
                    avg_latency_ms=avg_lat,
                    median_latency_ms=med_lat,
                    p95_latency_ms=p95_lat,
                    sentences_per_second=sps,
                    tokens_per_second=tps,
                    peak_memory_mb=round(peak_mem, 2),
                    errors=errors
                )
                all_summaries.append(summary)

            # 3. Save completed experiment to SQLite Database
            exp_id = save_experiment(
                experiment_name=f"Bench_{req.dataset_name}_{req.source_lang}-{req.target_lang}_{int(time.time())}",
                model_name=model_service.model_name,
                source_lang=req.source_lang,
                target_lang=req.target_lang,
                dataset_name=req.dataset_name,
                sample_count=len(samples),
                metrics=[s.dict() for s in all_summaries],
                sentence_records=all_sentence_records,
                environment_info=resource_monitor.get_system_metrics()
            )

            with self._lock:
                self.jobs[job_id]["status"] = "completed"
                self.jobs[job_id]["progress_percent"] = 100.0
                self.jobs[job_id]["current_step"] = "Benchmark completed successfully."
                self.jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
                self.jobs[job_id]["results"] = all_summaries
                self.jobs[job_id]["experiment_id"] = exp_id

        except Exception as e:
            logger.error(f"Benchmark job {job_id} failed: {e}", exc_info=True)
            with self._lock:
                self.jobs[job_id]["status"] = "failed"
                self.jobs[job_id]["error_message"] = str(e)
                self.jobs[job_id]["current_step"] = f"Failed: {str(e)}"

benchmark_service = BenchmarkService()
