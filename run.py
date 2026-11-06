"""
run.py — start the AI Debugger FastAPI server.

Run from the project root:
    python run.py

This script ensures both the project root (for `repository.*`) and the
`backend/` directory (for `app.*`) are on sys.path before uvicorn is started.
"""

import sys
import os
from pathlib import Path

# Project root  → resolves `repository.*`
ROOT = Path(__file__).parent
# Backend dir   → resolves `app.*`
BACKEND = ROOT / "backend"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(ROOT)],
    )
