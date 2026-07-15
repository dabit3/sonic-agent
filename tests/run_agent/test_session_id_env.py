"""Test that SONIC_SESSION_ID is exposed as an env var and ContextVar."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from run_agent import AIAgent


@pytest.fixture(autouse=True)
def _cleanup_env():
    """Remove SONIC_SESSION_ID before/after each test."""
    os.environ.pop("SONIC_SESSION_ID", None)
    yield
    os.environ.pop("SONIC_SESSION_ID", None)


def test_session_id_env_set_on_init():
    """AIAgent.__init__ sets SONIC_SESSION_ID in the environment."""
    agent = AIAgent(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
    )
    assert os.environ.get("SONIC_SESSION_ID") == agent.session_id
    assert len(agent.session_id) > 0


def test_session_id_env_uses_provided_id():
    """When session_id is passed explicitly, SONIC_SESSION_ID reflects it."""
    custom_id = "20260511_120000_abc12345"
    agent = AIAgent(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        session_id=custom_id,
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
    )
    assert os.environ["SONIC_SESSION_ID"] == custom_id
    assert agent.session_id == custom_id


def test_session_id_contextvar_set():
    """AIAgent.__init__ also sets the ContextVar for concurrency safety."""
    custom_id = "20260511_130000_def67890"
    AIAgent(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        session_id=custom_id,
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
    )
    from gateway.session_context import get_session_env
    assert get_session_env("SONIC_SESSION_ID") == custom_id
