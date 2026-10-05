"""Vercel serverless entrypoint for the NoteTaker Flask app.

Vercel's Python runtime looks for a WSGI callable named ``app`` at module level.
Local development still uses ``python src/main.py``.
"""

import os
import sys

# Make the repository root importable so `src.*` packages resolve.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import app  # noqa: E402  (must follow the sys.path setup)
