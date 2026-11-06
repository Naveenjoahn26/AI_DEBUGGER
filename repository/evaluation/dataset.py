from repository.evaluation.cases import EVALUATION_CASES
from repository.evaluation.models import EvaluationCase

class EvaluationDataset:
    def __init__(
        self,
        cases: list[EvaluationCase] | None = None,
    ):
        self.cases = cases if cases is not None else EVALUATION_CASES

    def get_eval_cases(self) -> list[EvaluationCase]:
        return self.cases
