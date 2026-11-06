from typing import List

from repository.evaluation.models import (
    BenchmarkResult,
    OverallEvaluation,
    EvaluationReport,
)


class EvaluationReportGenerator:

    def generate(
        self,
        benchmark: BenchmarkResult,
        case_results: List[OverallEvaluation],
    ) -> EvaluationReport:

        return EvaluationReport(
            total_cases=benchmark.total_cases,
            average_retrieval_score=(
                benchmark.average_retrieval_score
            ),
            average_tool_selection_score=(
                benchmark.average_tool_selection_score
            ),
            average_diagnosis_score=(
                benchmark.average_diagnosis_score
            ),
            average_overall_score=(
                benchmark.average_overall_score
            ),
            case_results=case_results,
        )