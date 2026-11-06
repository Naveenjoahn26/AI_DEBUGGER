def calculate_tool_selection_score(
    actual_tools: list[str],
    expected_tools: list[str],
) -> float:

    if not expected_tools:
        return 0.0

    return 1.0 if actual_tools == expected_tools else 0.0