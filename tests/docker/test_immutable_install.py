"""Runtime smoke tests for Docker immutable install tree and install-method stamp.

Build the real image and verify at runtime:

  1. /opt/sonic is not writable by the sonic user (immutable install tree)
  2. PYTHONDONTWRITEBYTECODE and SONIC_DISABLE_LAZY_INSTALLS are set
  3. /opt/sonic/.install_method contains "docker" (code-scoped stamp)
  4. $SONIC_HOME/.install_method is NOT stamped as "docker" by stage2
  5. A stale "docker" stamp in $SONIC_HOME is healed (removed) on boot
"""
from __future__ import annotations

from tests.docker.conftest import (
    docker_exec,
    docker_exec_sh,
    restart_container,
    start_container,
)


def test_install_tree_not_writable_by_sonic(
    built_image: str, container_name: str,
) -> None:
    """The sonic user must not be able to modify /opt/sonic.

    The install tree (source, venv, TUI bundle, node_modules) must remain
    root-owned and non-writable so an agent session cannot self-modify
    the installation and brick the gateway.
    """
    start_container(built_image, container_name)

    r = docker_exec_sh(
        container_name,
        # Try to create a file under /opt/sonic as the sonic user
        "touch /opt/sonic/test_write 2>&1 && "
        "echo WRITE_SUCCEEDED || echo WRITE_FAILED",
        timeout=10,
    )
    assert "WRITE_FAILED" in r.stdout, (
        f"sonic user can write to /opt/sonic (install tree not immutable): "
        f"{r.stdout}"
    )

    # Also check a key subdirectory
    r = docker_exec_sh(
        container_name,
        "touch /opt/sonic/.venv/test_write 2>&1 && "
        "echo WRITE_SUCCEEDED || echo WRITE_FAILED",
        timeout=10,
    )
    assert "WRITE_FAILED" in r.stdout, (
        f"sonic user can write to /opt/sonic/.venv: {r.stdout}"
    )


def test_sonic_disable_lazy_installs_and_dont_write_bytecode(
    built_image: str, container_name: str,
) -> None:
    """The container must set PYTHONDONTWRITEBYTECODE and
    SONIC_DISABLE_LAZY_INSTALLS=1 so no .pyc files are written to the
    immutable install tree and no lazy installs attempt to modify it."""
    start_container(built_image, container_name)

    r = docker_exec_sh(
        container_name,
        'test "$PYTHONDONTWRITEBYTECODE" = "1" && '
        'test "$SONIC_DISABLE_LAZY_INSTALLS" = "1" && '
        'echo ENV_OK || echo ENV_MISSING',
        timeout=10,
    )
    assert "ENV_OK" in r.stdout, (
        f"expected PYTHONDONTWRITEBYTECODE=1 and "
        f"SONIC_DISABLE_LAZY_INSTALLS=1, got: {r.stdout} stderr={r.stderr}"
    )


def test_install_method_stamp_is_code_scoped(
    built_image: str, container_name: str,
) -> None:
    """The 'docker' install-method stamp must be baked at
    /opt/sonic/.install_method (code-scoped), NOT in $SONIC_HOME."""
    start_container(built_image, container_name)

    # Code-scoped stamp must exist and say "docker"
    r = docker_exec_sh(
        container_name,
        "cat /opt/sonic/.install_method",
        timeout=10,
    )
    assert r.returncode == 0, (
        f"/opt/sonic/.install_method not found: {r.stderr}"
    )
    assert r.stdout.strip() == "docker", (
        f"expected 'docker' stamp, got: {r.stdout.strip()!r}"
    )

    # $SONIC_HOME must NOT have a 'docker' stamp
    r = docker_exec_sh(
        container_name,
        "cat /opt/data/.install_method 2>/dev/null || echo NONE",
        timeout=10,
    )
    assert r.stdout.strip() != "docker", (
        f"$SONIC_HOME/.install_method is stamped 'docker' - stage2 must "
        f"not stamp the data volume (shared with host installs)"
    )


def test_stale_docker_stamp_in_home_is_healed_on_boot(
    built_image: str, container_name: str,
) -> None:
    """A stale 'docker' stamp left in $SONIC_HOME by an older image
    must be removed on boot so shared homes self-heal."""
    # Start container, write a stale stamp
    start_container(built_image, container_name)

    # Write a stale 'docker' stamp as root
    docker_exec(
        container_name, "sh", "-c",
        "printf 'docker\\n' > /opt/data/.install_method",
        user="root", timeout=5,
    )
    # Verify it exists
    r = docker_exec_sh(container_name, "cat /opt/data/.install_method", timeout=5)
    assert r.stdout.strip() == "docker"

    # Restart - stage2 should heal it
    restart_container(container_name)

    # The stale stamp must be gone
    r = docker_exec_sh(
        container_name,
        "test -f /opt/data/.install_method && "
        "cat /opt/data/.install_method || echo HEALED",
        timeout=10,
    )
    assert "HEALED" in r.stdout or r.stdout.strip() != "docker", (
        f"stale 'docker' stamp in $SONIC_HOME was not healed on boot: "
        f"{r.stdout}"
    )
