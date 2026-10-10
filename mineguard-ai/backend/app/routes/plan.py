from fastapi import APIRouter
from app.models.schemas import PlanRequest, PlanResponse

router = APIRouter(prefix="/plan", tags=["plan"])


@router.post("", response_model=PlanResponse)
async def create_plan(request: PlanRequest):
    """
    PHASE F — TO BE IMPLEMENTED.
    Constraint-aware migration scheduling.
    """
    return PlanResponse(phases=[], total_cost_usd=0, total_weeks=0, feasible=False)
