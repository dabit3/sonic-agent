import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from run_agent import AIAgent


@pytest.mark.parametrize("tool_delay", [None, 0.25])
def test_sequential_tools_have_no_default_pacing_but_honor_explicit_delay(tmp_path, monkeypatch, tool_delay):
    monkeypatch.setenv("SONIC_HOME", str(tmp_path))
    (tmp_path / "config.yaml").write_text(
        "speed:\n  enabled: false\nmodel:\n  context_length: 128000\n", encoding="utf-8",
    )
    kwargs = {} if tool_delay is None else {"tool_delay": tool_delay}
    with patch("run_agent.OpenAI"):
        agent = AIAgent(
            provider="openai", api_key="test-only", base_url="http://127.0.0.1:1/v1",
            model="gpt-4o-mini", enabled_toolsets=["todo"], quiet_mode=True,
            skip_context_files=True, skip_memory=True, **kwargs,
        )
    calls = [
        SimpleNamespace(id=f"call-{i}", type="function", function=SimpleNamespace(
            name="todo", arguments=json.dumps({"todos": [{"id": "1", "content": "Test task", "status": status}]}),
        ))
        for i, status in enumerate(("in_progress", "completed"))
    ]
    messages = []
    try:
        with patch("agent.tool_executor.time.sleep") as sleep:
            agent._execute_tool_calls_sequential(SimpleNamespace(tool_calls=calls), messages, "latency-test")
        assert [message["tool_call_id"] for message in messages] == [call.id for call in calls]
        assert all("error" not in json.loads(message["content"]) for message in messages)
        assert [call.args[0] for call in sleep.call_args_list] == ([] if tool_delay is None else [tool_delay])
    finally:
        agent.close()
