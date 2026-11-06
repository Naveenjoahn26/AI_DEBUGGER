import pytest
from pydantic import ValidationError

from repository.debugging.schemas import DebugResponseSchema, DebugEvidenceSchema


def test_valid_evidence():
    evidence = DebugEvidenceSchema(
        file_path="auth.py",
        start_line=10,
        end_line=15,
        explanation="Creates token"
    )
    assert evidence.file_path == "auth.py"


def test_missing_fields_in_evidence():
    with pytest.raises(ValidationError):
        DebugEvidenceSchema(
            file_path="auth.py",
            # missing start_line, end_line, explanation
        )


def test_invalid_type_in_evidence():
    with pytest.raises(ValidationError):
        DebugEvidenceSchema(
            file_path="auth.py",
            start_line="not an int",  # invalid
            end_line=15,
            explanation="Test"
        )


def test_valid_response():
    response = DebugResponseSchema(
        root_cause="Bug",
        explanation="Explanation",
        suggested_fix="Fix it",
        confidence="high",
        evidence=[
            {
                "file_path": "auth.py",
                "start_line": 10,
                "end_line": 15,
                "explanation": "Creates token"
            }
        ]
    )
    assert response.root_cause == "Bug"
    assert len(response.evidence) == 1
    assert response.evidence[0].file_path == "auth.py"


def test_missing_fields_in_response():
    with pytest.raises(ValidationError):
        DebugResponseSchema(
            root_cause="Bug"
            # missing explanation, suggested_fix, confidence
        )
