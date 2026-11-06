"""Pydantic models for evaluation API responses."""

from pydantic import BaseModel, Field


class MetricComparison(BaseModel):
    label: str
    baseline: float | None = None
    improved: float | None = None
    unit: str = "%"
    description: str = ""


class EvaluationSummaryResponse(BaseModel):
    dataset: str
    total_cases: int
    metrics: list[MetricComparison] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
