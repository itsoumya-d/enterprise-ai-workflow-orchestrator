from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IssueCategory(str, Enum):
    CI_RUNNER_FAILURE = "CI_RUNNER_FAILURE"
    AUTH_PERMISSIONS = "AUTH_PERMISSIONS"
    DATABASE_MIGRATION = "DATABASE_MIGRATION"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    STORAGE_REGISTRY = "STORAGE_REGISTRY"
    GENERAL_INQUIRY = "GENERAL_INQUIRY"

class IssueTicket(BaseModel):
    ticket_id: str
    title: str
    description: str
    raw_logs: Optional[str] = None
    component: Optional[str] = None
    environment: str = "production"

class TriageAssessment(BaseModel):
    ticket_id: str
    category: IssueCategory
    severity: SeverityLevel
    confidence: float = Field(ge=0.0, le=1.0)
    detected_components: List[str]
    suggested_runbook: str
    automated_action_eligible: bool
    reasoning: str
