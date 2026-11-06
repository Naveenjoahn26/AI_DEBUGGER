from pydantic import BaseModel, Field


class DebugEvidenceSchema(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    explanation: str


class DebugResponseSchema(BaseModel):
    root_cause: str
    explanation: str
    suggested_fix:str
    evidence: list[DebugEvidenceSchema] = Field(
        default_factory=list
    )
    confidence: str
