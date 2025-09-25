from fastapi import APIRouter, Depends

from ..deps import get_automation_service
from ..models.schemas import (
    AutomationSuggestionRequest,
    AutomationSuggestionResponse,
    AutomationImplementRequest,
    AutomationImplementationPlan,
)
from ..services.automation_service import AutomationService

router = APIRouter(prefix="/ops/automation", tags=["ops-automation"])


@router.post("/suggest", response_model=AutomationSuggestionResponse)
async def suggest_automations(
    payload: AutomationSuggestionRequest,
    service: AutomationService = Depends(get_automation_service),
):
    suggestions = await service.suggest(payload.focus, payload.count)
    return {"suggestions": suggestions}


@router.post("/implement", response_model=AutomationImplementationPlan)
async def implement_automation(
    payload: AutomationImplementRequest,
    service: AutomationService = Depends(get_automation_service),
):
    record = await service.implement(payload.model_dump())
    return record
