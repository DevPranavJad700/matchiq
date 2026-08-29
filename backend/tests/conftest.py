"""Pytest configuration and environment fixtures for MatchIQ tests."""

import os
import sys
from pathlib import Path

# Add project root and backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Set test environment defaults
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-ci-only")
os.environ.setdefault("MODEL_DIR", str(project_root / "ml" / "models"))
