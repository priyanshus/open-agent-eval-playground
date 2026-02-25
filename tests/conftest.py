"""Pytest configuration and shared fixtures for trajectory tests."""
import os

import pytest

CHAT_API_BASE_URL = os.getenv("CHAT_API_BASE_URL", "http://localhost:8080")


@pytest.fixture(scope="module")
def chat_api_url() -> str:
    return CHAT_API_BASE_URL.rstrip("/")
