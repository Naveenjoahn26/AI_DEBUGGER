from repository.evaluation.models import EvaluationCase
from repository.evaluation.metrics import calculate_recall_at_k
from repository.evaluation.models import RetrievalEvaluation
from pydantic import BaseModel, Field

class RetrievalEvaluator:

    def __init__(self, retriever):
        self.retriever = retriever

    def evaluate_case(
        self,
        case: EvaluationCase,
        top_k: int = 5,
    ) -> RetrievalEvaluation:

        chunks = self.retriever.retrieve(
            case.bug_description,
            top_k=top_k,
        )

        retrieved_files = [
            chunk.file_path
            for chunk in chunks
        ]

        score = calculate_recall_at_k(
            retrieved_files,
            case.expected_files,
        )

        return RetrievalEvaluation(
            case_id=case.case_id,
            retrieved_files=retrieved_files,
            expected_files=case.expected_files,
            score=score,
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