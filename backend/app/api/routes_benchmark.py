import json
from fastapi import APIRouter, HTTPException
from typing import List

from ..config import settings
from ..schemas.schemas import (
    BenchmarkRequest,
    BenchmarkJobStatus,
    BenchmarkSample
)
from ..services.benchmark_service import benchmark_service
from ..utils.logger import logger

router = APIRouter(prefix="/benchmark", tags=["Benchmark"])

@router.post("", response_model=dict)
async def start_benchmark(req: BenchmarkRequest):
    """
    Submits a benchmark evaluation job across specified beam widths.
    """
    # 1. Determine evaluation samples
    samples: List[BenchmarkSample] = []
    
    if req.samples and len(req.samples) > 0:
        samples = req.samples[:req.max_samples] if req.max_samples else req.samples
    else:
        # Load from sample dataset
        sample_file = settings.SAMPLE_DIR / "flores200_sample.json"
        if sample_file.exists():
            with open(sample_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    samples.append(BenchmarkSample(
                        source_text=item["source_text"],
                        reference_text=item.get("reference_text")
                    ))
            if req.max_samples:
                samples = samples[:req.max_samples]
        else:
            raise HTTPException(status_code=404, detail="Default sample dataset not found.")

    if not samples:
        raise HTTPException(status_code=400, detail="No evaluation samples provided.")

    try:
        job_id = benchmark_service.start_benchmark(req, samples)
        return {
            "message": "Benchmark job initiated successfully.",
            "job_id": job_id,
            "sample_count": len(samples),
            "beam_widths": req.beam_widths
        }
    except Exception as e:
        logger.error(f"Failed to start benchmark: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=BenchmarkJobStatus)
async def get_benchmark_status(job_id: str):
    """
    Retrieves progress, status, and results for a benchmark job.
    """
    status = benchmark_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Benchmark job not found.")
    return status

@router.post("/{job_id}/cancel", response_model=dict)
async def cancel_benchmark(job_id: str):
    """
    Cancels an active benchmark job.
    """
    success = benchmark_service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Job could not be cancelled or does not exist.")
    return {"message": f"Benchmark job {job_id} cancelled."}
