import csv
import io
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Dict, Any, Optional

from ..config import settings
from ..schemas.schemas import BenchmarkSample
from ..utils.logger import logger

router = APIRouter(prefix="/datasets", tags=["Datasets"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_datasets():
    """Lists preloaded and sample parallel corpora."""
    datasets = []
    
    # 1. FLORES-200 sample
    flores_path = settings.SAMPLE_DIR / "flores200_sample.json"
    if flores_path.exists():
        with open(flores_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            datasets.append({
                "id": "flores200_sample",
                "name": "FLORES-200 Evaluation Sample (Tamil-English)",
                "source_lang": "ta",
                "target_lang": "en",
                "sample_count": len(data),
                "has_references": True,
                "description": "Authentic parallel sentences across everyday, literary, and scientific domains."
            })

    return datasets

@router.post("/parse", response_model=Dict[str, Any])
async def parse_dataset_file(
    file: UploadFile = File(...),
    source_column: str = Form("source_text"),
    reference_column: Optional[str] = Form("reference_text")
):
    """
    Parses an uploaded CSV or JSON parallel dataset without executing arbitrary code,
    validating headers and extracting sentence pairs safely.
    """
    content = await file.read()
    filename = file.filename.lower()
    samples: List[BenchmarkSample] = []

    try:
        if filename.endswith(".json"):
            text_data = content.decode("utf-8")
            data = json.loads(text_data)
            if not isinstance(data, list):
                raise ValueError("JSON must contain an array of sentence objects.")
                
            for row in data:
                src = row.get(source_column, "").strip()
                ref = row.get(reference_column, "").strip() if reference_column else None
                if src:
                    samples.append(BenchmarkSample(source_text=src, reference_text=ref))
                    
        elif filename.endswith(".csv"):
            text_data = content.decode("utf-8")
            f = io.StringIO(text_data)
            reader = csv.DictReader(f)
            
            for row in reader:
                src = row.get(source_column, "").strip()
                ref = row.get(reference_column, "").strip() if reference_column and reference_column in row else None
                if src:
                    samples.append(BenchmarkSample(source_text=src, reference_text=ref))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a CSV or JSON file.")

        if not samples:
            raise HTTPException(status_code=400, detail="No valid sentences found in uploaded file.")

        return {
            "filename": file.filename,
            "total_samples": len(samples),
            "preview": [s.dict() for s in samples[:5]],
            "samples": [s.dict() for s in samples]
        }
        
    except Exception as e:
        logger.error(f"Dataset parsing error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse dataset: {str(e)}")
