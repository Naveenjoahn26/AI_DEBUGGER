"""
backend/app/api/routes/debug_stream.py

GET /debug/stream/{session_id}  — Server-Sent Events endpoint.

Streams real-time lifecycle events from the debug pipeline to the frontend.
The frontend opens this SSE connection BEFORE submitting the POST /debug/ request.
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.event_bus import get_session, DebugEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["Debugging"])


@router.get("/stream/{session_id}")
async def stream_debug_events(session_id: str):
    """
    Stream debug pipeline events for the given session_id.

    The client should open this SSE connection first, then submit
    POST /debug/?session_id=<same_id> to start the pipeline.
    Events are streamed until a terminal event (debug_service_success,
    debug_service_failed, or debug_error) is received.
    """
    queue = get_session(session_id)
    if queue is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Call POST /debug/session first.",
        )

    async def event_generator():
        terminal_events = {
            "debug_service_success",
            "debug_service_failed",
            "debug_error",
        }
        try:
            while True:
                try:
                    event: DebugEvent = await asyncio.wait_for(
                        queue.get(), timeout=120.0
                    )
                    yield event.to_sse()

                    if event.event in terminal_events:
                        break
                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            logger.info("stream_cancelled", extra={"session_id": session_id})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
