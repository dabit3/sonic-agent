from unittest.mock import patch


def test_pip_install_detected_when_no_git_dir(tmp_path):
    """When PROJECT_ROOT has no .git, detect as pip install."""
    with patch("sonic_cli.config.get_managed_system", return_value=None), \
         patch("sonic_cli.config.get_sonic_home", return_value=tmp_path):
        from sonic_cli.config import detect_install_method
        method = detect_install_method(project_root=tmp_path)
        assert method == "pip"


def test_git_install_detected_when_git_dir_exists(tmp_path):
    """When PROJECT_ROOT has .git, detect as git install."""
    (tmp_path / ".git").mkdir()
    with patch("sonic_cli.config.get_managed_system", return_value=None), \
         patch("sonic_cli.config.get_sonic_home", return_value=tmp_path):
        from sonic_cli.config import detect_install_method
        method = detect_install_method(project_root=tmp_path)
        assert method == "git"


def test_managed_install_takes_precedence(tmp_path):
    """When SONIC_MANAGED is set, that takes precedence over git detection."""
    (tmp_path / ".git").mkdir()
    with patch("sonic_cli.config.get_managed_system", return_value="NixOS"), \
         patch("sonic_cli.config.get_sonic_home", return_value=tmp_path):
        from sonic_cli.config import detect_install_method
        method = detect_install_method(project_root=tmp_path)
        assert method == "nixos"


def test_recommended_update_command_pip():
    """Pip installs recommend pip install --upgrade."""
    from sonic_cli.config import recommended_update_command_for_method
    cmd = recommended_update_command_for_method("pip")
    assert "pip install" in cmd or "uv pip install" in cmd
    assert "--upgrade" in cmd
    assert "sonic-agent" in cmd


def test_stamp_file_takes_precedence(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".install_method").write_text("docker\n")
    with patch("sonic_cli.config.get_managed_system", return_value=None), \
         patch("sonic_cli.config.get_sonic_home", return_value=tmp_path):
        from sonic_cli.config import detect_install_method
        assert detect_install_method(project_root=tmp_path) == "docker"


def test_container_without_stamp_is_not_docker(tmp_path):
    """An unstamped install in a generic container must NOT be flagged as docker.

    Regression for issue #34397. The two supported installs both stamp
    ``.install_method`` (the curl installer -> ``git``, covered by
    ``test_stamp_file_takes_precedence``; the published image -> ``docker``),
    so neither hits this path. An unsupported manual install dropped into a
    container has no stamp and was wrongly classified as the published Docker
    image, so ``sonic update`` refused to run. With a ``.git`` checkout it
    must resolve to ``git``.
    """
    (tmp_path / ".git").mkdir()
    with patch("sonic_cli.config.get_managed_system", return_value=None), \
         patch("sonic_cli.config.get_sonic_home", return_value=tmp_path), \
         patch("sonic_constants.is_container", return_value=True):
        from sonic_cli.config import detect_install_method
        assert detect_install_method(project_root=tmp_path) == "git"


def test_recommended_update_command_docker():
    from sonic_cli.config import recommended_update_command_for_method
    assert "docker pull" in recommended_update_command_for_method("docker")
