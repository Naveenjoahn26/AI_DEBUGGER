"""
tests/backend/test_debug_route.py

Tests for the POST /debug API endpoint.
Mocks out the DebugService to isolate API logic.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.debug import DebugMetadata, DebugResponse
from repository.exceptions import CloneFailedError, InvalidRepositoryURLError

client = TestClient(app)


def test_debug_endpoint_valid_request():
    """A valid request should return 200 and the diagnosis."""
    mock_response = DebugResponse(
        status="success",
        diagnosis="The bug is here.",
        repository="https://github.com/owner/repo.git",
        metadata=DebugMetadata(iterations=2),
    )

    with patch("app.api.routes.debug._service.run") as mock_run:
        mock_run.return_value = mock_response
        
        response = client.post(
            "/debug/",
            json={
                "repo_url": "https://github.com/owner/repo.git",
                "bug_description": "Something is broken here.",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["diagnosis"] == "The bug is here."


def test_debug_endpoint_invalid_url_returns_400():
    """An invalid URL (raised by service) should return a 400 Bad Request."""
    with patch("app.api.routes.debug._service.run") as mock_run:
        mock_run.side_effect = InvalidRepositoryURLError("Bad URL")

        response = client.post(
            "/debug/",
            json={
                "repo_url": "invalid",
                "bug_description": "Something is broken here.",
            },
        )

    assert response.status_code == 400
    assert "Bad URL" in response.json()["detail"]


def test_debug_endpoint_clone_failed_returns_502():
    """A clone failure (raised by service) should return 502 Bad Gateway."""
    with patch("app.api.routes.debug._service.run") as mock_run:
        mock_run.side_effect = CloneFailedError("Clone failed")

        response = client.post(
            "/debug/",
            json={
                "repo_url": "https://github.com/owner/does-not-exist.git",
                "bug_description": "Something is broken here.",
            },
        )

    assert response.status_code == 502
    assert "Failed to clone" in response.json()["detail"]


def test_debug_endpoint_unexpected_error_returns_500():
    """Any unexpected error should return a generic 500 without leaking stack traces."""
    with patch("app.api.routes.debug._service.run") as mock_run:
        mock_run.side_effect = RuntimeError("Internal Secret Explosion")

        response = client.post(
            "/debug/",
            json={
                "repo_url": "https://github.com/owner/repo.git",
                "bug_description": "Something is broken here.",
            },
        )

    assert response.status_code == 500
    # Make sure our custom detail is returned, not the raw exception
    assert "Internal Secret Explosion" not in response.json()["detail"]
    assert "internal error occurred" in response.json()["detail"]


def test_debug_endpoint_validation_error():
    """FastAPI/Pydantic should reject missing required fields with 422."""
    response = client.post(
        "/debug/",
        json={
            # Missing repo_url
            "bug_description": "Something is broken here.",
        },
    )
    assert response.status_code == 422

    response = client.post(
        "/debug/",
        json={
            "repo_url": "https://github.com/owner/repo.git",
            "bug_description": "",  # Empty description fails validation
        },
    )
    assert response.status_code == 422
