import csv
import io
import json
from fastapi import APIRouter, HTTPException, Response
from typing import List, Dict, Any

from ..database.db import list_experiments, get_experiment_detail
from ..schemas.schemas import ExperimentSummary
from ..utils.logger import logger

router = APIRouter(prefix="/experiments", tags=["Experiments"])

@router.get("", response_model=List[Dict[str, Any]])
async def get_experiments():
    """Returns a list of all recorded benchmark runs with summary scores."""
    try:
        return list_experiments()
    except Exception as e:
        logger.error(f"Failed to fetch experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{experiment_id}", response_model=Dict[str, Any])
async def get_experiment(experiment_id: int):
    """Returns detailed metrics and per-sentence translations for a specific experiment."""
    exp = get_experiment_detail(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    return exp

@router.get("/{experiment_id}/export")
async def export_experiment(experiment_id: int, format: str = "json"):
    """
    Exports full experiment results as downloadable JSON or CSV.
    """
    exp = get_experiment_detail(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            "sentence_index", "source_text", "reference_text",
            "method", "beam_width", "translation", "latency_ms",
            "sentence_bleu", "sentence_chrf", "tokens_count"
        ])
        
        for s in exp["sentence_records"]:
            writer.writerow([
                s["sentence_index"],
                s["source_text"],
                s.get("reference_text", ""),
                s["method"],
                s["beam_width"],
                s["translation"],
                s["latency_ms"],
                s.get("sentence_bleu", ""),
                s.get("sentence_chrf", ""),
                s.get("tokens_count", 0)
            ])
            
        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=experiment_{experiment_id}_export.csv"}
        )
    else:
        json_content = json.dumps(exp, indent=2, ensure_ascii=False)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=experiment_{experiment_id}_export.json"}
        )
