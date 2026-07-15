"""Regression tests for _apply_profile_override LIGHTNING_HOME guard (issue #22502).

When LIGHTNING_HOME is set to the lightning root (e.g. systemd hardcodes
LIGHTNING_HOME=/root/.lightning), _apply_profile_override must still read
active_profile and update LIGHTNING_HOME to the profile directory.

When LIGHTNING_HOME is already a profile directory (.../profiles/<name>),
_apply_profile_override must trust it and return without re-reading
active_profile (child-process inheritance contract).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def _run_apply_profile_override(
    tmp_path, monkeypatch, *, lightning_home: str | None, active_profile: str | None,
    argv: list[str] | None = None,
):
    """Run _apply_profile_override in isolation.

    Returns the value of os.environ["LIGHTNING_HOME"] after the call,
    or None if unset.
    """
    lightning_root = tmp_path / ".lightning"
    lightning_root.mkdir(parents=True, exist_ok=True)

    if active_profile is not None:
        (lightning_root / "active_profile").write_text(active_profile)

    if active_profile and active_profile != "default":
        (lightning_root / "profiles" / active_profile).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    if lightning_home is not None:
        monkeypatch.setenv("LIGHTNING_HOME", lightning_home)
    else:
        monkeypatch.delenv("LIGHTNING_HOME", raising=False)

    monkeypatch.setattr(sys, "argv", argv or ["lightning", "gateway", "start"])

    from lightning_cli.main import _apply_profile_override
    _apply_profile_override()

    return os.environ.get("LIGHTNING_HOME")


class TestApplyProfileOverrideLightningHomeGuard:
    """Regression guard for issue #22502.

    Verifies that LIGHTNING_HOME pointing to the lightning root does NOT suppress
    the active_profile check, while LIGHTNING_HOME already pointing to a
    profile directory IS trusted as-is.
    """

    def test_lightning_home_at_root_with_active_profile_is_redirected(
        self, tmp_path, monkeypatch
    ):
        """LIGHTNING_HOME=/root/.lightning + active_profile=coder must redirect
        LIGHTNING_HOME to .../profiles/coder.

        Bug scenario from #22502: systemd sets LIGHTNING_HOME to the lightning root
        and the user switches to a profile via `lightning profile use`.
        Before the fix, the guard returned early and active_profile was ignored.
        """
        lightning_root = tmp_path / ".lightning"
        lightning_root.mkdir(parents=True, exist_ok=True)

        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            lightning_home=str(lightning_root),
            active_profile="coder",
        )

        assert result is not None, "LIGHTNING_HOME must be set after profile redirect"
        assert "profiles" in result, (
            f"Expected LIGHTNING_HOME to point into profiles/ dir, got: {result!r}"
        )
        assert result.endswith("coder"), (
            f"Expected LIGHTNING_HOME to end with 'coder', got: {result!r}"
        )

    def test_lightning_home_already_profile_dir_is_trusted(self, tmp_path, monkeypatch):
        """LIGHTNING_HOME=.../profiles/coder must not be overridden even when
        active_profile says something different.

        Preserves the child-process inheritance contract: a subprocess spawned
        with LIGHTNING_HOME already set to a specific profile must stay in that
        profile.
        """
        lightning_root = tmp_path / ".lightning"
        profile_dir = lightning_root / "profiles" / "coder"
        profile_dir.mkdir(parents=True, exist_ok=True)

        (lightning_root / "active_profile").write_text("other")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("LIGHTNING_HOME", str(profile_dir))
        monkeypatch.setattr(sys, "argv", ["lightning", "gateway", "start"])

        from lightning_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("LIGHTNING_HOME") == str(profile_dir), (
            "LIGHTNING_HOME must remain unchanged when already pointing to a profile dir"
        )

    def test_lightning_home_unset_reads_active_profile(self, tmp_path, monkeypatch):
        """Classic case: LIGHTNING_HOME unset + active_profile=coder must set
        LIGHTNING_HOME to the profile directory (existing behaviour must not regress).
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            lightning_home=None,
            active_profile="coder",
        )

        assert result is not None
        assert "coder" in result

    def test_lightning_home_unset_default_profile_no_redirect(self, tmp_path, monkeypatch):
        """active_profile=default must not redirect LIGHTNING_HOME."""
        lightning_root = tmp_path / ".lightning"
        lightning_root.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("LIGHTNING_HOME", raising=False)
        monkeypatch.setattr(sys, "argv", ["lightning", "gateway", "start"])
        (lightning_root / "active_profile").write_text("default")

        from lightning_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("LIGHTNING_HOME") is None
