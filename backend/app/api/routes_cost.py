from fastapi import APIRouter
from ..schemas.schemas import CostEstimateRequest, CostEstimateResponse
from ..services.cost_estimator import cost_estimator

router = APIRouter(prefix="/cost", tags=["Cost"])

@router.post("/estimate", response_model=CostEstimateResponse)
async def estimate_deployment_cost(req: CostEstimateRequest):
    """
    Computes transparent deployment cost estimates comparing Greedy and Beam Search
    under local CPU, cloud CPU, and cloud GPU environments.
    """
    return cost_estimator.estimate_costs(req)
