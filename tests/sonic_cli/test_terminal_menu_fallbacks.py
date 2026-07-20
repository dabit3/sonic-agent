"""Regression tests for numbered fallbacks when arrow-key menus cannot initialize."""

import subprocess
import sys
import types

from sonic_cli.config import load_config, save_config


class _BrokenTerminalMenu:
    def __init__(self, *args, **kwargs):
        raise subprocess.CalledProcessError(2, ["tput", "clear"])


def test_prompt_model_selection_falls_back_on_non_tty(monkeypatch):
    """On non-TTY stdin the model picker uses the numbered input fallback."""
    from sonic_cli.auth import _prompt_model_selection

    # Force non-TTY so curses path is skipped (matches piped/test environments).
    class _FakeStdin:
        def isatty(self):
            return False

    monkeypatch.setattr(sys, "stdin", _FakeStdin())
    responses = iter(["2"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    selected = _prompt_model_selection(["model-a", "model-b"])

    assert selected == "model-b"


def test_prompt_model_selection_arrow_keys_via_curses(monkeypatch):
    """When curses is available, arrow-key selection is used."""
    from sonic_cli.auth import _prompt_model_selection

    class _FakeStdin:
        def isatty(self):
            return True

    monkeypatch.setattr(sys, "stdin", _FakeStdin())
    # Index 1 → model-b
    monkeypatch.setattr(
        "sonic_cli.curses_ui.curses_radiolist",
        lambda *args, **kwargs: 1,
    )

    selected = _prompt_model_selection(["model-a", "model-b"])
    assert selected == "model-b"


def test_prompt_model_selection_curses_cancel(monkeypatch):
    """ESC/q in the curses picker returns None (no change)."""
    from sonic_cli.auth import _prompt_model_selection

    class _FakeStdin:
        def isatty(self):
            return True

    monkeypatch.setattr(sys, "stdin", _FakeStdin())
    monkeypatch.setattr(
        "sonic_cli.curses_ui.curses_radiolist",
        lambda *args, **kwargs: -1,
    )

    selected = _prompt_model_selection(["model-a", "model-b"])
    assert selected is None


def test_prompt_reasoning_effort_falls_back_on_terminalmenu_runtime_error(monkeypatch):
    from sonic_cli.main import _prompt_reasoning_effort_selection

    monkeypatch.setitem(
        sys.modules,
        "simple_term_menu",
        types.SimpleNamespace(TerminalMenu=_BrokenTerminalMenu),
    )
    responses = iter(["3"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    selected = _prompt_reasoning_effort_selection(["low", "medium", "high"], current_effort="")

    assert selected == "high"


def test_remove_custom_provider_falls_back_on_terminalmenu_runtime_error(tmp_path, monkeypatch):
    from sonic_cli.main import _remove_custom_provider

    monkeypatch.setenv("SONIC_HOME", str(tmp_path))
    monkeypatch.setitem(
        sys.modules,
        "simple_term_menu",
        types.SimpleNamespace(TerminalMenu=_BrokenTerminalMenu),
    )

    cfg = load_config()
    cfg["custom_providers"] = [
        {"name": "Local A", "base_url": "http://localhost:8001/v1"},
        {"name": "Local B", "base_url": "http://localhost:8002/v1"},
    ]
    save_config(cfg)

    responses = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    _remove_custom_provider(cfg)

    reloaded = load_config()
    assert reloaded["custom_providers"] == [
        {"name": "Local B", "base_url": "http://localhost:8002/v1"},
    ]


def test_named_custom_provider_model_picker_falls_back_on_non_tty(tmp_path, monkeypatch):
    from sonic_cli.main import _model_flow_named_custom

    monkeypatch.setenv("SONIC_HOME", str(tmp_path))

    class _FakeStdin:
        def isatty(self):
            return False

    monkeypatch.setattr(sys, "stdin", _FakeStdin())
    monkeypatch.setattr("sonic_cli.models.fetch_api_models", lambda *args, **kwargs: ["model-a", "model-b"])
    monkeypatch.setattr("sonic_cli.auth.deactivate_provider", lambda: None)

    cfg = load_config()
    save_config(cfg)

    responses = iter(["2"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))

    _model_flow_named_custom(
        cfg,
        {
            "name": "Local",
            "base_url": "http://localhost:8000/v1",
            "api_key": "",
            "model": "",
        },
    )

    reloaded = load_config()
    assert reloaded["model"]["provider"] == "custom"
    assert reloaded["model"]["base_url"] == "http://localhost:8000/v1"
    assert reloaded["model"]["default"] == "model-b"
