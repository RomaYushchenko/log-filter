"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest

# Add src directory to path so tests can import modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_log_record() -> str:
    """Fixture providing a sample log record."""
    return """2025-01-07 10:00:00.000+0000 ERROR
Connection to Kafka broker failed
Caused by: java.net.ConnectException: Connection refused
    at java.net.PlainSocketImpl.socketConnect(Native Method)
    at com.example.Main.main(Main.java:45)"""


@pytest.fixture
def sample_multiline_log() -> str:
    """Fixture providing a multiline log."""
    return """2025-01-07 10:00:00.000+0000 ERROR Application startup failed
Exception in thread "main" java.lang.RuntimeException: Fatal error
    at com.example.App.start(App.java:123)
    at com.example.Main.main(Main.java:45)
Caused by: java.io.IOException: Config file not found
    at com.example.Config.load(Config.java:67)
    ... 2 more"""
