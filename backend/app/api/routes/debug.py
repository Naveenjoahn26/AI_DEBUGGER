"""
backend/app/api/routes/debug.py

POST /debug  — accepts a repo URL + bug description, returns AI diagnosis.

Business logic lives in DebugService; the router only coordinates:
    - request validation (handled by Pydantic)
    - calling the service
    - mapping domain exceptions to HTTP responses
"""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.debug import DebugRequest, DebugResponse
from app.services.debug_service import DebugService
from app.services import event_bus
from repository.exceptions import CloneFailedError, InvalidRepositoryURLError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["Debugging"])

_service = DebugService()
_executor = ThreadPoolExecutor(max_workers=2)


@router.post(
    "/",
    response_model=DebugResponse,
    status_code=status.HTTP_200_OK,
    summary="Debug a public Git repository",
    description=(
        "Clone a public repository, index its Python code, and ask the "
        "AI Debugger to diagnose the provided bug description."
    ),
)
def debug(
    request: DebugRequest,
    session_id: str = Query(default=None, description="Optional session ID for SSE streaming"),
) -> DebugResponse:
    """
    End-to-end debug endpoint.

    - 422 if request body is invalid (handled by FastAPI/Pydantic).
    - 400 if the repository URL is malformed or unsupported.
    - 502 if git clone fails (remote unreachable, repo not found, etc.).
    - 500 for unexpected errors (internal stack traces are NOT exposed).
    """
    logger.info(
        "debug_request_received",
        extra={"repo_url": request.repo_url},
    )

    try:
        return _service.run(request, session_id=session_id)

    except InvalidRepositoryURLError as exc:
        logger.warning("invalid_url: %s", exc)
        if session_id:
            event_bus.emit(session_id, "debug_error", str(exc), {"type": "invalid_url"})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except CloneFailedError as exc:
        logger.error("clone_failed: %s", exc)
        if session_id:
            event_bus.emit(session_id, "debug_error", str(exc), {"type": "clone_failed"})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Failed to clone the repository. "
                "Ensure the URL is correct and the repository is public."
            ),
        ) from exc

    except Exception as exc:
        logger.exception("debug_unexpected_error: %s", exc)
        err_msg = str(exc) or "An internal error occurred."
        if session_id:
            event_bus.emit(session_id, "debug_error", err_msg, {"type": "internal"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=err_msg,
        ) from exc


@router.post("/session")
def create_debug_session():
    """Create an SSE session. Returns a session_id the frontend uses for streaming."""
    session_id = str(uuid.uuid4())
    event_bus.create_session(session_id)
    return {"session_id": session_id}
