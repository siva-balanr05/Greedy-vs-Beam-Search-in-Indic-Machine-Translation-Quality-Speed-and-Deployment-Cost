from fastapi import APIRouter, HTTPException
from ..schemas.schemas import (
    TranslateRequest,
    TranslateResponse,
    CompareRequest,
    CompareResponse
)
from ..services.translation_service import translation_service
from ..utils.logger import logger

router = APIRouter(prefix="/translate", tags=["Translation"])

@router.post("", response_model=TranslateResponse)
def translate_text(req: TranslateRequest):
    """
    Translates a source sentence using the requested decoding method (greedy or beam search).
    Synchronous definition enables FastAPI's worker threadpool to handle CPU-bound PyTorch operations.
    """
    try:
        return translation_service.translate(req)
    except Exception as e:
        logger.error(f"Translation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare", response_model=CompareResponse)
def compare_decoding(req: CompareRequest):
    """
    Executes both Greedy Search and Beam Search on identical source input,
    returning translations, timing, throughput, and memory measurements.
    Synchronous definition enables FastAPI's worker threadpool to handle CPU-bound PyTorch operations.
    """
    try:
        return translation_service.compare(req)
    except Exception as e:
        logger.error(f"Comparison error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
