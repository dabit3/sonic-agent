"""Resolve LIGHTNING_HOME for standalone skill scripts.

Skill scripts may run outside the Lightning process (e.g. system Python,
nix env, CI) where ``lightning_constants`` is not importable.  This module
provides the same ``get_lightning_home()`` and ``display_lightning_home()``
contracts as ``lightning_constants`` without requiring it on ``sys.path``.

When ``lightning_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``lightning_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``LIGHTNING_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from lightning_constants import display_lightning_home as display_lightning_home
    from lightning_constants import get_lightning_home as get_lightning_home
except (ModuleNotFoundError, ImportError):

    def get_lightning_home() -> Path:
        """Return the Lightning home directory (default: ~/.lightning).

        Mirrors ``lightning_constants.get_lightning_home()``."""
        val = os.environ.get("LIGHTNING_HOME", "").strip()
        return Path(val) if val else Path.home() / ".lightning"

    def display_lightning_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``lightning_constants.display_lightning_home()``."""
        home = get_lightning_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)
