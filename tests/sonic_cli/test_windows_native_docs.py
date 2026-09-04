from pathlib import Path


def test_windows_native_install_path_docs_match_installer() -> None:
    doc = Path("website/docs/user-guide/windows-native.md").read_text()
    install = Path("scripts/install.ps1").read_text()

    assert "%LOCALAPPDATA%\\sonic\\sonic-agent\\venv\\Scripts" in doc
    assert "Get-Command sonic        # should print C:\\Users\\<you>\\AppData\\Local\\sonic\\sonic-agent\\venv\\Scripts\\sonic.exe" in doc
    assert '$sonicBin = "$InstallDir\\venv\\Scripts"' in install
