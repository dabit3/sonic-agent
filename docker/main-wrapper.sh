#!/bin/sh
# /opt/sonic/docker/main-wrapper.sh — wraps the container's CMD with
# the same argument-routing logic the pre-s6 entrypoint.sh used. Runs
# as /init's "main program" (Docker CMD) so it inherits stdin/stdout/
# stderr from the container.
#
# Routing:
#   no args                       → exec `sonic` (the default)
#   first arg is an executable    → exec it directly (sleep, bash, sh, …)
#   first arg is anything else    → exec `sonic <args>` (subcommand passthrough)
#
# We drop to the sonic user via `s6-setuidgid` so the supervised
# workload runs unprivileged (UID 10000 by default).
set -e

cd /opt/data
# shellcheck disable=SC1091
. /opt/sonic/.venv/bin/activate

if [ $# -eq 0 ]; then
    exec s6-setuidgid sonic sonic
fi

if command -v "$1" >/dev/null 2>&1; then
    # Bare executable — pass through directly.
    exec s6-setuidgid sonic "$@"
fi

# Sonic subcommand pass-through.
exec s6-setuidgid sonic sonic "$@"
