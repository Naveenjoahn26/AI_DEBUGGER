"""
backend/app/services/event_bus.py

Lightweight in-memory event bus for streaming debug pipeline events
to the frontend via SSE.

Each debug session gets a unique session_id. Events are pushed into
an asyncio.Queue keyed by session_id. The SSE endpoint reads from
the queue and yields events to the client.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Global registry: session_id → asyncio.Queue
_sessions: Dict[str, asyncio.Queue] = {}


@dataclass
class DebugEvent:
    """A single lifecycle event from the debug pipeline."""
    event: str                   # e.g. "cloning_repository", "agent_started"
    message: str                 # Human-readable description
    timestamp: float = field(default_factory=time.time)
    data: Optional[Dict[str, Any]] = None

    def to_sse(self) -> str:
        payload = {
            "event": self.event,
            "message": self.message,
            "timestamp": self.timestamp,
        }
        if self.data:
            payload["data"] = self.data
        return f"data: {json.dumps(payload)}\n\n"


def create_session(session_id: str) -> asyncio.Queue:
    """Create a new event queue for a debug session."""
    q = asyncio.Queue()
    _sessions[session_id] = q
    logger.info("event_bus: session created", extra={"session_id": session_id})
    return q


def get_session(session_id: str) -> Optional[asyncio.Queue]:
    """Get the event queue for a session, or None."""
    return _sessions.get(session_id)


def emit(session_id: str, event: str, message: str, data: dict | None = None):
    """
    Push an event to the session queue (thread-safe).
    
    This is called from synchronous code (DebugService), so we use
    put_nowait which works even without an event loop in the current thread.
    """
    q = _sessions.get(session_id)
    if q is None:
        return
    evt = DebugEvent(event=event, message=message, data=data)
    try:
        q.put_nowait(evt)
    except asyncio.QueueFull:
        logger.warning("event_bus: queue full, dropping event", extra={"event": event})


def close_session(session_id: str):
    """Remove the session queue."""
    _sessions.pop(session_id, None)
    logger.info("event_bus: session closed", extra={"session_id": session_id})
