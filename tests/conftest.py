"""Pytest configuration for the CRAB KEY (dr_no) package."""

import os
import sys

# Force the headless matplotlib backend before any plotting import.
os.environ.setdefault("MPLBACKEND", "Agg")

# Add the package src/ to sys.path so imports work from a clean environment.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
for _path in (SRC, ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)
