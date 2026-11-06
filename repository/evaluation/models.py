from typing import List
from pydantic import BaseModel,Field

class EvaluationCase(BaseModel):
    """A known debugging problem used to evaluate the AI Debugger."""
    
    case_id: str = Field(description="Unique identifier for the evaluation case.")

    bug_description: str = Field(
        description="Description of the bug given to the AI Debugger."
    )

    expected_files: List[str] = Field(
        default_factory=list,
        description="Files expected to contain relevant code for the bug.",
    )

    expected_tools: List[str] = Field(
        default_factory=list,
        description="Tools expected to be useful for solving the case.",
    )

    expected_diagnosis: str = Field(
        description="Expected root-cause diagnosis for the bug."
    )
class EvaluationResult(BaseModel):
    """Stores the result produced when an evaluation case is executed."""

    case_id: str = Field(
        description="ID of the evaluation case that was executed."
    )

    actual_answer: str = Field(
        description="Final answer produced by the AI Debugger."
    )

    passed: bool = Field(
        default=False,
        description="Whether the evaluation case passed."
    )

    scores: dict[str, float] = Field(
        default_factory=dict,
        description="Metric scores produced during evaluation."
    )

class RetrievalEvaluation(BaseModel):
    case_id: str = Field(
        description="Unique identifier for the evaluation case."
    )

    retrieved_files: list[str] = Field(
        default_factory=list,
        description="Files retrieved by the retriever."
    )

    expected_files: list[str] = Field(
        default_factory=list,
        description="Files expected to be retrieved."
    )

    score: float = Field(
        description="Recall score for this evaluation case."
    )

class ToolSelectionEvaluation(BaseModel):
    """Stores the result of evaluating an agent's tool selection."""

    case_id: str = Field(
        description="Unique identifier for the evaluation case."
    )

    expected_tools: list[str] = Field(
        default_factory=list,
        description="Tools expected to be selected by the agent."
    )

    actual_tools: list[str] = Field(
        default_factory=list,
        description="Tools actually selected by the agent."
    )

    score: float = Field(
        description="Tool selection accuracy score."
    )
class DiagnosisEvaluation(BaseModel):
    """Stores the result of evaluating the agent's diagnosis."""

    case_id: str = Field(
        description="Unique identifier for the evaluation case."
    )

    expected_diagnosis: str = Field(
        description="The known correct diagnosis."
    )

    actual_diagnosis: str = Field(
        description="The diagnosis produced by the agent."
    )

    score: float = Field(
        description="Diagnosis correctness score."
    )

class OverallEvaluation(BaseModel):
    """Stores the combined evaluation score for one agent run."""

    case_id: str = Field(
        description="Unique identifier for the evaluation case."
    )

    retrieval_score: float = Field(
        description="Recall score for code retrieval."
    )

    tool_selection_score: float = Field(
        description="Score for selecting the expected tools."
    )

    diagnosis_score: float = Field(
        description="Score for diagnosis correctness."
    )

    overall_score: float = Field(
        description="Weighted overall agent score."
    )

class BenchmarkResult(BaseModel):
    """Stores aggregate results from a complete evaluation run."""

    total_cases: int = Field(
        description="Total number of evaluation cases."
    )

    average_retrieval_score: float = Field(
        description="Average retrieval score across all cases."
    )

    average_tool_selection_score: float = Field(
        description="Average tool selection score across all cases."
    )

    average_diagnosis_score: float = Field(
        description="Average diagnosis score across all cases."
    )

    average_overall_score: float = Field(
        description="Average overall score across all cases."
    )

class EvaluationReport(BaseModel):
    """Final report for an evaluation benchmark."""

    total_cases: int

    average_retrieval_score: float

    average_tool_selection_score: float

    average_diagnosis_score: float

    average_overall_score: float

    case_results: List[OverallEvaluation] = Field(
        default_factory=list
    )
class BenchmarkResult(BaseModel):
    """Stores aggregate results from a complete evaluation run."""

    total_cases: int = Field(
        description="Total number of evaluation cases."
    )

    average_retrieval_score: float = Field(
        description="Average retrieval score across all cases."
    )

    average_tool_selection_score: float = Field(
        description="Average tool selection score across all cases."
    )

    average_diagnosis_score: float = Field(
        description="Average diagnosis score across all cases."
    )

    average_overall_score: float = Field(
        description="Average overall score across all cases."
    )
class EvaluationReport(BaseModel):
    """Final report for an evaluation benchmark."""

    total_cases: int

    average_retrieval_score: float

    average_tool_selection_score: float

    average_diagnosis_score: float

    average_overall_score: float

    case_results: List[OverallEvaluation] = Field(
        default_factory=list
    )