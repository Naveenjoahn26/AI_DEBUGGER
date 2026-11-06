"""
backend/app/schemas/debug.py

Pydantic request/response models for the POST /debug endpoint.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class DebugRequest(BaseModel):
    """Incoming request to debug a public Git repository."""

    repo_url: str = Field(
        description="Public Git repository URL (https:// or similar).",
        examples=["https://github.com/owner/repo.git"],
    )
    bug_description: str = Field(
        description="Natural language description of the bug to investigate.",
        min_length=10,
        max_length=2000,
        examples=["Discount is applied twice when user checks out."],
    )
    branch: str | None = Field(
        default=None,
        description="Optional git branch to clone.",
    )

    @field_validator("repo_url")
    @classmethod
    def repo_url_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("repo_url must not be empty.")
        return v.strip()

    @field_validator("bug_description")
    @classmethod
    def bug_description_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("bug_description must not be empty.")
        return v.strip()


class DebugMetadata(BaseModel):
    """Token usage and performance metadata from the agent run."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    iterations: int = 0
    files_indexed: int = 0
    chunks_indexed: int = 0
    tool_calls: int = 0
    retrieved_chunks: int = 0
    latency_seconds: float = 0.0


class ToolCallInfo(BaseModel):
    name: str
    tool_call_id: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class IterationInfo(BaseModel):
    iteration: int
    tool_calls: list[ToolCallInfo] = Field(default_factory=list)
    observation_preview: str | None = None
    is_final: bool = False


class EvidenceItem(BaseModel):
    file_path: str
    function_name: str | None = None
    start_line: int = 0
    end_line: int = 0
    code: str = ""


class DebugResponse(BaseModel):
    """Response returned from POST /debug."""

    status: str = Field(
        description="'success' or 'failed'.",
    )
    diagnosis: str = Field(
        description="AI-generated root cause diagnosis.",
    )
    repository: str = Field(
        description="The repository URL that was analysed (sanitized).",
    )
    metadata: DebugMetadata = Field(
        default_factory=DebugMetadata,
        description="Token usage and processing statistics.",
    )
    evidence: list[EvidenceItem] = Field(default_factory=list)
    iterations: list[IterationInfo] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
