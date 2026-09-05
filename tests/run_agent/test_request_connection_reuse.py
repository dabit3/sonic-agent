import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event, Thread
from unittest.mock import patch

import pytest

from agent.chat_completion_helpers import interruptible_api_call
from run_agent import AIAgent


@pytest.fixture
def provider():
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_HEAD(self):
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if "messages" not in request:
                self.send_error(404)
                return
            self.server.requests.append((self.client_address, dict(self.headers), request))
            if request.get("stream"):
                chunk = {
                    "id": "test-stream", "object": "chat.completion.chunk", "created": 1,
                    "model": "gpt-4o-mini", "choices": [{
                        "index": 0, "delta": {"content": "ok"}, "finish_reason": "stop",
                    }],
                }
                body = f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n\n".encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
            elif request["messages"][-1]["content"] == "fail":
                body = json.dumps({"error": {"message": "test failure", "type": "server_error"}}).encode()
                self.send_response(500)
            else:
                body = json.dumps({
                    "id": "test-response", "object": "chat.completion", "created": 1,
                    "model": "test-model", "choices": [{
                        "index": 0, "message": {"role": "assistant", "content": "ok"},
                        "finish_reason": "stop",
                    }],
                }).encode()
                self.send_response(200)
            if not request.get("stream"):
                self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.requests = []
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield server, f"http://127.0.0.1:{server.server_port}/v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(2)


def make_agent(base_url):
    agent = AIAgent.__new__(AIAgent)
    agent.provider = "openai"
    agent.model = "test-model"
    agent.base_url = base_url
    agent.api_mode = "chat_completions"
    agent._client_log_context = lambda: "test"
    agent._compute_non_stream_stale_timeout = lambda _: 5
    agent._touch_activity = lambda *_: None
    agent._interrupt_requested = False
    agent._client_kwargs = {"api_key": "test-only", "base_url": base_url, "timeout": 2}
    agent.client = agent._create_openai_client(agent._client_kwargs, reason="test", shared=True)
    return agent


def request(agent, content="hello"):
    return interruptible_api_call(agent, {
        "model": agent.model, "messages": [{"role": "user", "content": content}],
    })


def test_successive_worker_threads_reuse_one_real_http_connection(provider):
    server, base_url = provider
    agent = make_agent(base_url)
    try:
        for _ in range(3):
            assert request(agent).choices[0].message.content == "ok"
        assert len({address for address, _, _ in server.requests}) == 1
    finally:
        agent.release_clients()


@pytest.mark.parametrize("streaming", [False, True])
def test_real_conversation_turns_reuse_clients_without_changing_the_prefix(provider, tmp_path, monkeypatch, streaming):
    server, base_url = provider
    monkeypatch.setenv("SONIC_HOME", str(tmp_path))
    (tmp_path / "config.yaml").write_text(
        "speed:\n  enabled: false\nmodel:\n  context_length: 128000\n", encoding="utf-8",
    )
    deltas = []
    agent = AIAgent(
        provider="openai", api_key="test-only", base_url=base_url, model="gpt-4o-mini",
        enabled_toolsets=[], skip_context_files=True, skip_memory=True, quiet_mode=True,
        stream_delta_callback=deltas.append if streaming else None,
    )
    agent._disable_streaming = not streaming
    history = None
    request_clients = []
    try:
        for _ in range(3):
            result = agent.run_conversation("hello", conversation_history=history)
            assert not result.get("failed")
            assert result["final_response"] == "ok"
            history = result["messages"]
            request_clients.append(agent._idle_request_client[2])
        requests = [body for _, _, body in server.requests]
        assert len(requests) == 3
        assert all(client is request_clients[0] for client in request_clients)
        if not streaming:
            assert len({address for address, _, _ in server.requests}) == 1
        assert all(body["messages"][0] == requests[0]["messages"][0] for body in requests)
        assert requests[1]["messages"][:len(requests[0]["messages"])] == requests[0]["messages"]
        if streaming:
            assert "".join(deltas) == "okokok"
    finally:
        agent.close()


def test_prewarm_connection_is_used_by_the_completion_worker(provider):
    from agent.agent_init import _prewarm_provider_connection

    server, base_url = provider
    agent = make_agent(base_url)
    try:
        _prewarm_provider_connection(agent)
        idle = agent._idle_request_client[2]
        assert request(agent).choices[0].message.content == "ok"
        assert agent._idle_request_client[2] is idle
        assert len(server.requests) == 1
    finally:
        agent.release_clients()


def test_active_leases_are_exclusive_and_idle_cache_is_bounded(provider):
    _, base_url = provider
    agent = make_agent(base_url)
    first = second = None
    try:
        first = agent._create_request_openai_client(reason="test")
        second = agent._create_request_openai_client(reason="test")
        assert first is not second
        assert first is not agent.client
        agent._close_request_openai_client(first, reason="request_complete")
        agent._close_request_openai_client(second, reason="request_complete")
        assert not first.is_closed()
        assert second.is_closed()
        reused = agent._create_request_openai_client(reason="test")
        assert reused is first
        assert reused.max_retries == 0
        agent._close_request_openai_client(reused, reason="request_complete")
    finally:
        agent.release_clients()
        for client in (first, second):
            if client is not None:
                client.close()


def test_aborted_lease_is_not_reused_and_does_not_close_another_lease(provider):
    _, base_url = provider
    agent = make_agent(base_url)
    first = agent._create_request_openai_client(reason="test")
    second = agent._create_request_openai_client(reason="test")
    try:
        with patch.object(first, "close", wraps=first.close) as close:
            agent._abort_request_openai_client(first, reason="interrupt_abort")
            close.assert_not_called()
        agent._close_request_openai_client(first, reason="request_complete")
        assert first.is_closed()
        assert not second.is_closed()
        agent._close_request_openai_client(second, reason="request_complete")
        reused = agent._create_request_openai_client(reason="test")
        assert reused is second
        agent._close_request_openai_client(reused, reason="request_complete")
    finally:
        agent.release_clients()
        first.close()
        second.close()


def test_provider_errors_discard_the_request_client(provider):
    server, base_url = provider
    agent = make_agent(base_url)
    try:
        request(agent)
        original = agent._idle_request_client[2]
        with pytest.raises(Exception, match="test failure"):
            request(agent, "fail")
        assert original.is_closed()
        assert request(agent).choices[0].message.content == "ok"
        assert server.requests[-1][0] != server.requests[0][0]
    finally:
        agent.release_clients()


@pytest.mark.parametrize("change", ["api_key", "default_headers", "rebuild"])
def test_config_changes_invalidate_idle_clients(provider, change):
    _, base_url = provider
    agent = make_agent(base_url)
    try:
        request(agent)
        original = agent._idle_request_client[2]
        if change == "rebuild":
            assert agent._replace_primary_openai_client(reason="test")
        else:
            agent._client_kwargs[change] = "new-test-key" if change == "api_key" else {"X-Test": "changed"}
        request(agent)
        assert agent._idle_request_client[2] is not original
        assert original.is_closed()
    finally:
        agent.release_clients()


def test_release_clients_discards_idle_and_late_returning_leases(provider):
    _, base_url = provider
    agent = make_agent(base_url)
    first = agent._create_request_openai_client(reason="test")
    second = agent._create_request_openai_client(reason="test")
    agent._close_request_openai_client(first, reason="request_complete")
    agent.release_clients()
    assert first.is_closed()
    assert not second.is_closed()
    agent._close_request_openai_client(second, reason="request_complete")
    assert second.is_closed()
    assert getattr(agent, "_idle_request_client", None) is None


def test_abort_and_owner_return_are_serialized(provider):
    _, base_url = provider
    agent = make_agent(base_url)
    client = agent._create_request_openai_client(reason="test")
    abort_started = Event()
    finish_abort = Event()
    returned = Event()

    def shutdown(_client):
        abort_started.set()
        assert finish_abort.wait(2)
        return 0

    def release():
        agent._close_request_openai_client(client, reason="request_complete")
        returned.set()

    try:
        with patch.object(agent, "_force_close_tcp_sockets", side_effect=shutdown):
            abort = Thread(target=lambda: agent._abort_request_openai_client(client, reason="interrupt_abort"))
            abort.start()
            assert abort_started.wait(2)
            owner = Thread(target=release)
            owner.start()
            assert not returned.wait(0.02)
            finish_abort.set()
            abort.join(2)
            owner.join(2)
        assert returned.is_set()
        assert client.is_closed()
    finally:
        finish_abort.set()
        agent.release_clients()
        client.close()
