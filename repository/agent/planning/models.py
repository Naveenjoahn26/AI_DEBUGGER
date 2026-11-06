from enum import Enum
from pydantic import BaseModel, Field

class PlanStepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

class PlanStep(BaseModel):
    description: str
    status: PlanStepStatus = PlanStepStatus.PENDING

class Plan(BaseModel):
    steps: list[PlanStep] = Field(default_factory=list)
    current_step: int = 0
