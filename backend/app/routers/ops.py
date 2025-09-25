from fastapi import APIRouter, Depends

from ..deps import get_ops_service, get_llm_provider
from ..models.schemas import (
    OpsChecklistRequest,
    OpsChecklistResponse,
    OpsDashboardResponse,
    OpsGeneratedTask,
)
from ..services.ops_service import OpsService
from ..services.llm_provider import LLMProvider

router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/dashboard", response_model=OpsDashboardResponse)
async def ops_dashboard(service: OpsService = Depends(get_ops_service)):
    return service.dashboard()


@router.post("/checklist", response_model=OpsChecklistResponse)
async def ops_checklist(
    payload: OpsChecklistRequest,
    service: OpsService = Depends(get_ops_service),
    llm: LLMProvider = Depends(get_llm_provider),
):
    return await service.generate_checklist(payload.model_dump(), llm)


@router.get("/generated-tasks", response_model=list[OpsGeneratedTask])
async def ops_generated_tasks(service: OpsService = Depends(get_ops_service)):
    return service.generated_tasks()
