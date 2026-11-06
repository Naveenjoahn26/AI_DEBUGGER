from repository.evaluation.models import EvaluationCase


EVALUATION_CASES = [
    EvaluationCase(
        case_id="BUG-001",
        bug_description=(
            "The calculate_discount function returns the wrong total "
            "when a customer is eligible for a discount."
        ),
        expected_files=["pricing.py"],
        expected_tools=["search_code"],
        expected_diagnosis=(
            "The discount is added to the price instead of being "
            "subtracted from the price."
        ),
    ),
    EvaluationCase(
        case_id="BUG-002",
        bug_description=(
            "The user creation API fails when the email field is missing."
        ),
        expected_files=["users.py"],
        expected_tools=["search_code"],
        expected_diagnosis=(
            "The endpoint accesses the email field directly without "
            "handling a missing input value."
        ),
    ),
    EvaluationCase(
        case_id="BUG-003",
        bug_description=(
            "The application crashes instead of returning a useful "
            "response when a requested user does not exist."
        ),
        expected_files=["user_service.py"],
        expected_tools=["search_code"],
        expected_diagnosis=(
            "The code does not handle the user-not-found case before "
            "accessing the returned user object."
        ),
    ),
]