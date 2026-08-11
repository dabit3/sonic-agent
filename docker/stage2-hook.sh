#!/bin/sh
# s6-overlay stage2 hook — runs as root after the supervision tree is
# up but before user services start. Handles UID/GID remap, volume
# chown, config seeding, and skills sync.
#
# Per-service privilege drop happens inside each service's `run` script
# (and in main-wrapper.sh) via s6-setuidgid, not here.
#
# Wired into the image as /etc/cont-init.d/01-sonic-setup by the
# Dockerfile. The shim at docker/entrypoint.sh forwards to this script
# so external references to docker/entrypoint.sh still work.
#
# NB: cont-init.d scripts run with no arguments — the user's CMD args
# are NOT visible here. That's fine: we use Architecture B (s6-overlay
# main-program model), so main-wrapper.sh runs the CMD with full
# stdin/stdout/stderr access and handles arg parsing there.

set -eu

SONIC_HOME="${SONIC_HOME:-/opt/data}"
INSTALL_DIR="/opt/sonic"

# --- UID/GID remap ---
if [ -n "${SONIC_UID:-}" ] && [ "$SONIC_UID" != "$(id -u sonic)" ]; then
    echo "[stage2] Changing sonic UID to $SONIC_UID"
    usermod -u "$SONIC_UID" sonic
fi
if [ -n "${SONIC_GID:-}" ] && [ "$SONIC_GID" != "$(id -g sonic)" ]; then
    echo "[stage2] Changing sonic GID to $SONIC_GID"
    # -o allows non-unique GID (e.g. macOS GID 20 "staff" may already
    # exist as "dialout" in the Debian-based container image).
    groupmod -o -g "$SONIC_GID" sonic 2>/dev/null || true
fi

# --- Fix ownership of data volume ---
actual_sonic_uid=$(id -u sonic)
needs_chown=false
if [ -n "${SONIC_UID:-}" ] && [ "$SONIC_UID" != "10000" ]; then
    needs_chown=true
elif [ "$(stat -c %u "$SONIC_HOME" 2>/dev/null)" != "$actual_sonic_uid" ]; then
    needs_chown=true
fi
if [ "$needs_chown" = true ]; then
    echo "[stage2] Fixing ownership of $SONIC_HOME to sonic ($actual_sonic_uid)"
    # In rootless Podman the container's "root" is mapped to an
    # unprivileged host UID — chown will fail. That's fine: the volume
    # is already owned by the mapped user on the host side.
    chown -R sonic:sonic "$SONIC_HOME" 2>/dev/null || \
        echo "[stage2] Warning: chown failed (rootless container?) — continuing"
    # The .venv must also be re-chowned when UID is remapped, otherwise
    # lazy_deps.py cannot install platform packages (discord.py, etc.).
    chown -R sonic:sonic "$INSTALL_DIR/.venv" 2>/dev/null || \
        echo "[stage2] Warning: chown .venv failed (rootless container?) — continuing"
fi

# Always reset ownership of $SONIC_HOME/profiles to sonic on every
# boot. Profile dirs and files can land owned by root when commands
# are invoked via `docker exec <container> sonic …` (which defaults
# to root unless `-u` is passed), and that breaks the cont-init
# reconciler (02-reconcile-profiles) which runs as sonic and walks
# the profiles dir. Idempotent; skipped on rootless containers where
# chown would fail.
if [ -d "$SONIC_HOME/profiles" ]; then
    chown -R sonic:sonic "$SONIC_HOME/profiles" 2>/dev/null || true
fi

# --- config.yaml permissions ---
# Ensure config.yaml is readable by the sonic runtime user even if it
# was edited on the host after initial ownership setup.
if [ -f "$SONIC_HOME/config.yaml" ]; then
    chown sonic:sonic "$SONIC_HOME/config.yaml" 2>/dev/null || true
    chmod 640 "$SONIC_HOME/config.yaml" 2>/dev/null || true
fi

# --- Seed directory structure as sonic user ---
# Run as sonic via s6-setuidgid so dirs end up owned correctly (matters
# under rootless Podman where chown back to root would fail).
#
# Use direct `mkdir -p` invocation (no `sh -c "..."` wrapper) so the
# shell isn't a second interpreter — defends against $SONIC_HOME values
# containing shell metacharacters. PR #30136 review item O2.
s6-setuidgid sonic mkdir -p \
    "$SONIC_HOME/cron" \
    "$SONIC_HOME/sessions" \
    "$SONIC_HOME/logs" \
    "$SONIC_HOME/hooks" \
    "$SONIC_HOME/memories" \
    "$SONIC_HOME/skills" \
    "$SONIC_HOME/skins" \
    "$SONIC_HOME/plans" \
    "$SONIC_HOME/workspace" \
    "$SONIC_HOME/home"

# --- Install-method stamp (read by detect_install_method() in sonic status) ---
# Preserved from the tini-era entrypoint (PR #27843). Must be written as
# the sonic user so ownership matches the file's documented owner.
# tee is invoked directly via s6-setuidgid (no `sh -c` wrapper) for the
# same shell-metacharacter safety described above.
printf 'docker\n' | s6-setuidgid sonic tee "$SONIC_HOME/.install_method" >/dev/null \
    || true

# --- Seed config files (only on first boot) ---
seed_one() {
    dest=$1
    src=$2
    if [ ! -f "$SONIC_HOME/$dest" ] && [ -f "$INSTALL_DIR/$src" ]; then
        s6-setuidgid sonic cp "$INSTALL_DIR/$src" "$SONIC_HOME/$dest"
    fi
}
seed_one ".env" ".env.example"
seed_one "config.yaml" "cli-config.yaml.example"
seed_one "SOUL.md" "docker/SOUL.md"

# .env holds API keys and secrets — restrict to owner-only access. Applied
# unconditionally (not only on first-seed) so a host-mounted .env that was
# created with a permissive umask gets tightened on every container start.
if [ -f "$SONIC_HOME/.env" ]; then
    chown sonic:sonic "$SONIC_HOME/.env" 2>/dev/null || true
    chmod 600 "$SONIC_HOME/.env" 2>/dev/null || true
fi

# auth.json: bootstrap from env on first boot only. Same semantics as the
# pre-s6 entrypoint — the [ ! -f ] guard is critical to avoid clobbering
# rotated refresh tokens on container restart.
if [ ! -f "$SONIC_HOME/auth.json" ] && [ -n "${SONIC_AUTH_JSON_BOOTSTRAP:-}" ]; then
    printf '%s' "$SONIC_AUTH_JSON_BOOTSTRAP" > "$SONIC_HOME/auth.json"
    chown sonic:sonic "$SONIC_HOME/auth.json" 2>/dev/null || true
    chmod 600 "$SONIC_HOME/auth.json"
fi

# --- Sync bundled skills ---
# Invoke the venv's python by absolute path so we don't need a `sh -c`
# wrapper to source the activate script. This is safe because
# skills_sync.py doesn't depend on any environment exports beyond what
# the python binary's own bin-stub already sets up (sys.path is rooted
# at the venv's site-packages by virtue of running .venv/bin/python).
if [ -d "$INSTALL_DIR/skills" ]; then
    s6-setuidgid sonic "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/tools/skills_sync.py" \
        || echo "[stage2] Warning: skills_sync.py failed; continuing"
fi

echo "[stage2] Setup complete; starting user services"
