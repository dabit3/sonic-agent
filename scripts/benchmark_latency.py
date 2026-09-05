from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import threading
import time


ROOT = Path(__file__).resolve().parents[1]


def measure(fn, runs):
    samples = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000)
    return {"median_ms": round(statistics.median(samples), 3), "samples_ms": [round(s, 3) for s in samples]}


def worker(runs):
    from agent.display import KawaiiSpinner
    from agent.prompt_caching import apply_anthropic_cache_control
    from agent.transports.chat_completions import ChatCompletionsTransport
    from tools.registry import _module_registers_tools

    paths = sorted((ROOT / "tools").glob("*.py"))
    scan = lambda: [_module_registers_tools(path) for path in paths]
    results = {"tool_discovery_cold": measure(scan, 1), "tool_discovery_warm": measure(scan, runs)}

    def spinner_cycle():
        started = threading.Event()
        spinner = KawaiiSpinner("benchmark", print_fn=lambda _: started.set())
        spinner._out = io.StringIO()
        spinner.start()
        try:
            if not started.wait(2):
                raise RuntimeError("Spinner did not start")
        finally:
            spinner.stop()

    results["spinner_cycle"] = measure(spinner_cycle, runs)
    messages = [{"role": "system", "content": "System prompt"}] + [
        {
            "role": "user" if i % 2 == 0 else "assistant",
            "content": [{"type": "text", "text": f"Message {i}: " + "content " * 100} for _ in range(8)],
            "_internal": True,
        }
        for i in range(500)
    ]
    results["cache_markers_500_messages"] = measure(lambda: apply_anthropic_cache_control(messages), runs)
    transport = ChatCompletionsTransport()
    results["transport_cleanup_500_messages"] = measure(lambda: transport.convert_messages(messages), runs)

    from sonic_cli.config import DEFAULT_CONFIG, load_config_readonly, _LOAD_CONFIG_CACHE
    import yaml

    config_path = Path(os.environ["SONIC_HOME"]) / "config.yaml"
    config_path.write_text(yaml.safe_dump(DEFAULT_CONFIG), encoding="utf-8")

    def config_load():
        _LOAD_CONFIG_CACHE.clear()
        return load_config_readonly()

    results["config_cold"] = measure(config_load, runs)
    results["config_warm"] = measure(load_config_readonly, runs)

    from run_agent import AIAgent

    agent = AIAgent.__new__(AIAgent)
    agent.provider = "openai"
    agent._client_log_context = lambda: "benchmark"
    agent._client_kwargs = {"api_key": "benchmark-only", "base_url": "http://127.0.0.1:1/v1"}
    agent.client = agent._create_openai_client(agent._client_kwargs, reason="benchmark", shared=True)

    def request_cycle():
        client = agent._create_request_openai_client(reason="benchmark")
        agent._close_request_openai_client(client, reason="request_complete")

    try:
        results["request_client_cycle"] = measure(request_cycle, runs)
    finally:
        agent.release_clients()
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--startup", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be positive")
    sys.path.insert(0, str(ROOT))
    if args.worker:
        with contextlib.redirect_stdout(io.StringIO()):
            results = worker(args.runs)
        print(json.dumps(results, indent=2))
        return
    with tempfile.TemporaryDirectory(prefix="sonic-benchmark-") as home:
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": home,
            "SONIC_HOME": home,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
        }
        proc = subprocess.run(
            [sys.executable, __file__, "--worker", "--runs", str(args.runs)],
            cwd=ROOT, env=env, capture_output=True, text=True, check=True,
        )
        results = json.loads(proc.stdout)
        if args.startup:
            for module in ("sonic_cli.main", "run_agent", "cli", "tui_gateway.server"):
                def cold_import():
                    subprocess.run(
                        [sys.executable, "-c", f"import importlib; importlib.import_module({module!r})"],
                        cwd=ROOT, env=env, capture_output=True, check=True,
                    )
                results[f"import_{module}"] = measure(cold_import, args.runs)
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
