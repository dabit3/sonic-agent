"""Regression tests for _apply_profile_override SONIC_HOME guard (issue #22502).

When SONIC_HOME is set to the sonic root (e.g. systemd hardcodes
SONIC_HOME=/root/.sonic), _apply_profile_override must still read
active_profile and update SONIC_HOME to the profile directory.

When SONIC_HOME is already a profile directory (.../profiles/<name>),
_apply_profile_override must trust it and return without re-reading
active_profile (child-process inheritance contract).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def _run_apply_profile_override(
    tmp_path, monkeypatch, *, sonic_home: str | None, active_profile: str | None,
    argv: list[str] | None = None,
):
    """Run _apply_profile_override in isolation.

    Returns the value of os.environ["SONIC_HOME"] after the call,
    or None if unset.
    """
    sonic_root = tmp_path / ".sonic"
    sonic_root.mkdir(parents=True, exist_ok=True)

    if active_profile is not None:
        (sonic_root / "active_profile").write_text(active_profile)

    if active_profile and active_profile != "default":
        (sonic_root / "profiles" / active_profile).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    if sonic_home is not None:
        monkeypatch.setenv("SONIC_HOME", sonic_home)
    else:
        monkeypatch.delenv("SONIC_HOME", raising=False)

    monkeypatch.setattr(sys, "argv", argv or ["sonic", "gateway", "start"])

    from sonic_cli.main import _apply_profile_override
    _apply_profile_override()

    return os.environ.get("SONIC_HOME")


class TestApplyProfileOverrideSonicHomeGuard:
    """Regression guard for issue #22502.

    Verifies that SONIC_HOME pointing to the sonic root does NOT suppress
    the active_profile check, while SONIC_HOME already pointing to a
    profile directory IS trusted as-is.
    """

    def test_sonic_home_at_root_with_active_profile_is_redirected(
        self, tmp_path, monkeypatch
    ):
        """SONIC_HOME=/root/.sonic + active_profile=coder must redirect
        SONIC_HOME to .../profiles/coder.

        Bug scenario from #22502: systemd sets SONIC_HOME to the sonic root
        and the user switches to a profile via `sonic profile use`.
        Before the fix, the guard returned early and active_profile was ignored.
        """
        sonic_root = tmp_path / ".sonic"
        sonic_root.mkdir(parents=True, exist_ok=True)

        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            sonic_home=str(sonic_root),
            active_profile="coder",
        )

        assert result is not None, "SONIC_HOME must be set after profile redirect"
        assert "profiles" in result, (
            f"Expected SONIC_HOME to point into profiles/ dir, got: {result!r}"
        )
        assert result.endswith("coder"), (
            f"Expected SONIC_HOME to end with 'coder', got: {result!r}"
        )

    def test_sonic_home_already_profile_dir_is_trusted(self, tmp_path, monkeypatch):
        """SONIC_HOME=.../profiles/coder must not be overridden even when
        active_profile says something different.

        Preserves the child-process inheritance contract: a subprocess spawned
        with SONIC_HOME already set to a specific profile must stay in that
        profile.
        """
        sonic_root = tmp_path / ".sonic"
        profile_dir = sonic_root / "profiles" / "coder"
        profile_dir.mkdir(parents=True, exist_ok=True)

        (sonic_root / "active_profile").write_text("other")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("SONIC_HOME", str(profile_dir))
        monkeypatch.setattr(sys, "argv", ["sonic", "gateway", "start"])

        from sonic_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("SONIC_HOME") == str(profile_dir), (
            "SONIC_HOME must remain unchanged when already pointing to a profile dir"
        )

    def test_sonic_home_unset_reads_active_profile(self, tmp_path, monkeypatch):
        """Classic case: SONIC_HOME unset + active_profile=coder must set
        SONIC_HOME to the profile directory (existing behaviour must not regress).
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            sonic_home=None,
            active_profile="coder",
        )

        assert result is not None
        assert "coder" in result

    def test_sonic_home_unset_default_profile_no_redirect(self, tmp_path, monkeypatch):
        """active_profile=default must not redirect SONIC_HOME."""
        sonic_root = tmp_path / ".sonic"
        sonic_root.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("SONIC_HOME", raising=False)
        monkeypatch.setattr(sys, "argv", ["sonic", "gateway", "start"])
        (sonic_root / "active_profile").write_text("default")

        from sonic_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("SONIC_HOME") is None
