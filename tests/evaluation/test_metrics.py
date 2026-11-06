from repository.evaluation.metrics import calculate_recall_at_k


def test_recall_when_relevant_file_is_retrieved():
    score = calculate_recall_at_k(
        retrieved_files=["auth.py", "pricing.py", "utils.py"],
        expected_files=["pricing.py"],
    )

    assert score == 1.0


def test_recall_when_relevant_file_is_not_retrieved():
    score = calculate_recall_at_k(
        retrieved_files=["auth.py", "utils.py"],
        expected_files=["pricing.py"],
    )

    assert score == 0.0
