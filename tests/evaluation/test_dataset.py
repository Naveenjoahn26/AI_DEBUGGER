from repository.evaluation.dataset import EvaluationDataset
from repository.evaluation.models import EvaluationCase


def test_dataset_contains_evaluation_cases():
    dataset = EvaluationDataset()

    cases = dataset.get_eval_cases()

    assert len(cases) == 3
    assert all(isinstance(case, EvaluationCase) for case in cases)


def test_dataset_case_ids_are_unique():
    dataset = EvaluationDataset()

    cases = dataset.get_eval_cases()
    case_ids = [case.case_id for case in cases]

    assert len(case_ids) == len(set(case_ids))
