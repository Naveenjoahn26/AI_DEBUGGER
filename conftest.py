"""Root conftest.py — ensures the project root is on sys.path for all tests."""
import sys
from pathlib import Path

# Add the project root so `repository.*` imports resolve correctly.
sys.path.insert(0, str(Path(__file__).parent))

# Add backend directory so `app.*` imports resolve correctly.
sys.path.insert(0, str(Path(__file__).parent / "backend"))

