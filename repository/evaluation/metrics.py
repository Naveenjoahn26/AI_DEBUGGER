def calculate_recall_at_k(retrieved_files: list[str], expected_files: list[str]) -> float:
    """
    Calculates the recall score based on retrieved vs expected files.
    
    Formula: (Relevant files retrieved) / (Total expected files)
    """
    if not expected_files:
        return 0.0

    retrieved_set = set(retrieved_files)
    expected_set = set(expected_files)
    
    relevant_found = retrieved_set.intersection(expected_set)
    recall_score = len(relevant_found) / len(expected_set)
    return recall_score
