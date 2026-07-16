"""Resolve SONIC_HOME for standalone skill scripts.

Skill scripts may run outside the Sonic process (e.g. system Python,
nix env, CI) where ``sonic_constants`` is not importable.  This module
provides the same ``get_sonic_home()`` and ``display_sonic_home()``
contracts as ``sonic_constants`` without requiring it on ``sys.path``.

When ``sonic_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``sonic_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``SONIC_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from sonic_constants import display_sonic_home as display_sonic_home
    from sonic_constants import get_sonic_home as get_sonic_home
except (ModuleNotFoundError, ImportError):

    def get_sonic_home() -> Path:
        """Return the Sonic home directory (default: ~/.sonic).

        Mirrors ``sonic_constants.get_sonic_home()``."""
        val = os.environ.get("SONIC_HOME", "").strip()
        return Path(val) if val else Path.home() / ".sonic"

    def display_sonic_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``sonic_constants.display_sonic_home()``."""
        home = get_sonic_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)
