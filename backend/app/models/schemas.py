from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class HealthResponse(BaseModel):
    status: str

class ClassifyRequest(BaseModel):
    text: str
    labels: List[str]

class ClassifyResponse(BaseModel):
    label: str
    scores: dict

class SummarizeRequest(BaseModel):
    text: str
    max_tokens: int = 150

class SummarizeResponse(BaseModel):
    summary: str

class IngestRequest(BaseModel):
    texts: List[str]

class QueryRequest(BaseModel):
    question: str
    k: int = Field(default=5, ge=1, le=20)

class QueryResponseChunk(BaseModel):
    text: str
    score: float

class QueryResponse(BaseModel):
    answer: str
    chunks: List[QueryResponseChunk]


class OpsLocationStat(BaseModel):
    location: str
    surgeries_today: int
    sedation_cases: int
    risk_patients: int
    team_lead: str
    status: str


class OpsScheduleItem(BaseModel):
    patient: str
    procedure: str
    start: str
    location: str
    surgeon: str
    stage: str
    notes: str


class OpsTaskItem(BaseModel):
    title: str
    owner: str
    due: str
    priority: str


class OpsInventoryAlert(BaseModel):
    item: str
    location: str
    status: str
    on_hand: int
    par_level: int


class OpsFollowUpItem(BaseModel):
    patient: str
    type: str
    due: str
    status: str


class OpsSedationTrendPoint(BaseModel):
    day: str
    sedation_cases: int
    total_cases: int


class OpsDashboardMeta(BaseModel):
    total_surgeries: int
    total_sedation_cases: int
    at_risk_centers: int
    open_tasks: int


class OpsDashboardResponse(BaseModel):
    meta: OpsDashboardMeta
    locations: List[OpsLocationStat]
    schedule: List[OpsScheduleItem]
    tasks: List[OpsTaskItem]
    inventory_alerts: List[OpsInventoryAlert]
    followups: List[OpsFollowUpItem]
    sedation_trend: List[OpsSedationTrendPoint]


class OpsChecklistRequest(BaseModel):
    patient_name: str
    procedure: str
    location: str
    sedation: str
    notes: Optional[str] = None


class OpsChecklistResponse(BaseModel):
    title: str
    checklist: List[str]
    follow_up: List[str]


class OpsGeneratedTask(BaseModel):
    id: int
    patient_name: str
    task: str
    owner: str
    due_at: Optional[str]
    status: str
    created_at: Optional[str]


class AutomationSuggestionItem(BaseModel):
    title: str
    problem: str
    automation: str
    impact: str
    confidence: Optional[str] = None


class AutomationSuggestionRequest(BaseModel):
    focus: str
    count: int = Field(default=3, ge=1, le=8)


class AutomationSuggestionResponse(BaseModel):
    suggestions: List[AutomationSuggestionItem]


class AutomationImplementRequest(BaseModel):
    title: str
    problem: str
    automation: str
    impact: Optional[str] = None
    confidence: Optional[str] = None


class AutomationImplementationPlan(BaseModel):
    id: int
    title: str
    status: str
    implementation_plan: Dict[str, Any]
    created_at: Optional[str]
