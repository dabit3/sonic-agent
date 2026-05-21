"""Tests for uv-tool install detection in the update path (issue #29700).

``uv tool install sonic-agent`` lives outside any venv, so the previous
``uv pip install --upgrade`` update path failed with ``No virtual
environment found``. ``is_uv_tool_install`` should detect this layout and
both the user-facing recommended command and the actual
``_cmd_update_pip`` subprocess invocation should switch to
``uv tool upgrade sonic-agent``.
"""
from __future__ import annotations

import subprocess
from types import SimpleNamespace
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# is_uv_tool_install
# ---------------------------------------------------------------------------


class TestIsUvToolInstall:
    def test_returns_true_when_sys_prefix_matches_uv_tool_layout(self):
        from sonic_cli import config

        with patch.object(config.sys, "prefix", "/home/user/.local/share/uv/tools/sonic-agent"):
            assert config.is_uv_tool_install("uv") is True

    def test_returns_true_when_uv_tool_list_includes_sonic_agent(self):
        from sonic_cli import config

        completed = subprocess.CompletedProcess(
            ["uv", "tool", "list"],
            0,
            stdout="sonic-agent v0.14.0\n- sonic\n- sonic-bot\nblack v23.0.0\n- black\n",
            stderr="",
        )
        with patch.object(config.sys, "prefix", "/some/unrelated/venv"), \
             patch("subprocess.run", return_value=completed) as mock_run:
            assert config.is_uv_tool_install("/usr/local/bin/uv") is True
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0] == ["/usr/local/bin/uv", "tool", "list"]

    def test_returns_false_when_uv_tool_list_lacks_sonic_agent(self):
        from sonic_cli import config

        completed = subprocess.CompletedProcess(
            ["uv", "tool", "list"], 0, stdout="black v23.0.0\n- black\nruff v0.5.0\n- ruff\n", stderr=""
        )
        with patch.object(config.sys, "prefix", "/some/unrelated/venv"), \
             patch("subprocess.run", return_value=completed):
            assert config.is_uv_tool_install("uv") is False

    def test_returns_false_when_uv_tool_list_fails(self):
        from sonic_cli import config

        completed = subprocess.CompletedProcess(["uv", "tool", "list"], 2, stdout="", stderr="oops")
        with patch.object(config.sys, "prefix", "/some/unrelated/venv"), \
             patch("subprocess.run", return_value=completed):
            assert config.is_uv_tool_install("uv") is False

    def test_returns_false_when_subprocess_raises(self):
        from sonic_cli import config

        with patch.object(config.sys, "prefix", "/some/unrelated/venv"), \
             patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["uv"], 15)):
            assert config.is_uv_tool_install("uv") is False

    def test_returns_false_when_no_uv_available(self):
        from sonic_cli import config

        with patch.object(config.sys, "prefix", "/some/unrelated/venv"), \
             patch("shutil.which", return_value=None):
            assert config.is_uv_tool_install() is False

    def test_indented_alias_line_does_not_false_positive(self):
        """A tool whose alias line is ``- sonic-agent`` shouldn't match."""
        from sonic_cli import config

        completed = subprocess.CompletedProcess(
            ["uv", "tool", "list"],
            0,
            stdout="some-other-tool v1.0.0\n- sonic-agent\n",
            stderr="",
        )
        with patch.object(config.sys, "prefix", "/some/unrelated/venv"), \
             patch("subprocess.run", return_value=completed):
            assert config.is_uv_tool_install("uv") is False


# ---------------------------------------------------------------------------
# recommended_update_command_for_method
# ---------------------------------------------------------------------------


class TestRecommendedUpdateCommandForUvTool:
    def test_uv_tool_install_recommends_uv_tool_upgrade(self):
        from sonic_cli import config

        with patch("shutil.which", return_value="/usr/local/bin/uv"), \
             patch.object(config, "is_uv_tool_install", return_value=True):
            cmd = config.recommended_update_command_for_method("pip")
            assert cmd == "uv tool upgrade sonic-agent"

    def test_uv_pip_install_keeps_legacy_recommendation(self):
        """Existing behavior: uv is on PATH but Sonic is a regular pip install."""
        from sonic_cli import config

        with patch("shutil.which", return_value="/usr/local/bin/uv"), \
             patch.object(config, "is_uv_tool_install", return_value=False):
            cmd = config.recommended_update_command_for_method("pip")
            assert cmd == "uv pip install --upgrade sonic-agent"

    def test_no_uv_falls_back_to_plain_pip(self):
        from sonic_cli.config import recommended_update_command_for_method

        with patch("shutil.which", return_value=None):
            cmd = recommended_update_command_for_method("pip")
            assert cmd == "pip install --upgrade sonic-agent"


# ---------------------------------------------------------------------------
# _cmd_update_pip subprocess command
# ---------------------------------------------------------------------------


class TestCmdUpdatePipUsesUvTool:
    @patch("subprocess.run")
    def test_runs_uv_tool_upgrade_when_uv_tool_install(self, mock_run):
        """The actual subprocess invocation must switch to ``uv tool upgrade``."""
        from sonic_cli.main import _cmd_update_pip

        mock_run.return_value = subprocess.CompletedProcess(["uv"], 0, stdout="", stderr="")
        with patch("shutil.which", return_value="/usr/local/bin/uv"), \
             patch("sonic_cli.config.is_uv_tool_install", return_value=True):
            _cmd_update_pip(SimpleNamespace())

        assert mock_run.call_args[0][0] == ["/usr/local/bin/uv", "tool", "upgrade", "sonic-agent"]

    @patch("subprocess.run")
    def test_runs_uv_pip_install_when_not_uv_tool(self, mock_run):
        """Existing behavior preserved when uv is present but Sonic isn't a tool install."""
        from sonic_cli.main import _cmd_update_pip

        mock_run.return_value = subprocess.CompletedProcess(["uv"], 0, stdout="", stderr="")
        with patch("shutil.which", return_value="/usr/local/bin/uv"), \
             patch("sonic_cli.config.is_uv_tool_install", return_value=False):
            _cmd_update_pip(SimpleNamespace())

        assert mock_run.call_args[0][0] == [
            "/usr/local/bin/uv",
            "pip",
            "install",
            "--upgrade",
            "sonic-agent",
        ]

    @patch("subprocess.run")
    def test_falls_back_to_pip_when_no_uv(self, mock_run):
        from sonic_cli.main import _cmd_update_pip

        mock_run.return_value = subprocess.CompletedProcess(["pip"], 0, stdout="", stderr="")
        with patch("shutil.which", return_value=None):
            _cmd_update_pip(SimpleNamespace())

        cmd = mock_run.call_args[0][0]
        assert cmd[1:] == ["-m", "pip", "install", "--upgrade", "sonic-agent"]

    @patch("subprocess.run")
    def test_exits_nonzero_on_subprocess_failure(self, mock_run):
        from sonic_cli.main import _cmd_update_pip

        mock_run.return_value = subprocess.CompletedProcess(["uv"], 1, stdout="", stderr="")
        with patch("shutil.which", return_value="/usr/local/bin/uv"), \
             patch("sonic_cli.config.is_uv_tool_install", return_value=True):
            with pytest.raises(SystemExit) as exc_info:
                _cmd_update_pip(SimpleNamespace())
        assert exc_info.value.code == 1
