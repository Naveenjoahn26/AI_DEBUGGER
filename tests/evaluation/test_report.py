from repository.evaluation.report import EvaluationReportGenerator
from repository.evaluation.models import BenchmarkResult, OverallEvaluation


def test_generate_evaluation_report():

    benchmark = BenchmarkResult(
        total_cases=2,
        average_retrieval_score=0.75,
        average_tool_selection_score=1.0,
        average_diagnosis_score=0.70,
        average_overall_score=0.775,
    )

    case_result = OverallEvaluation(
        case_id="BUG-001",
        retrieval_score=1.0,
        tool_selection_score=1.0,
        diagnosis_score=0.8,
        overall_score=0.9,
    )

    generator = EvaluationReportGenerator()

    report = generator.generate(
        benchmark,
        [case_result],
    )

    assert report.total_cases == 2
    assert report.average_overall_score == 0.775
    assert len(report.case_results) == 1
    assert report.case_results[0].case_id == "BUG-001"
