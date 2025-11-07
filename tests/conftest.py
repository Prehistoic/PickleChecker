"""Pytest configuration and fixtures."""

import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_hf_token(monkeypatch):
    """Mock HuggingFace token for tests."""
    monkeypatch.setenv("HF_TOKEN", "test_token")