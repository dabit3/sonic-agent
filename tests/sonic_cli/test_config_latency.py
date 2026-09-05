from concurrent.futures import ThreadPoolExecutor

import pytest
import yaml

from agent import skill_utils
from sonic_cli.config import load_config, load_config_readonly, read_raw_config
from sonic_cli.plugins import PluginManager


@pytest.mark.parametrize("use_python_loader", [False, True])
def test_safe_yaml_loader_preserves_data_and_rejects_python_tags(monkeypatch, use_python_loader):
    monkeypatch.setattr(skill_utils, "_yaml_load_fn", None)
    if use_python_loader:
        monkeypatch.delattr(yaml, "CSafeLoader", raising=False)
    text = 'base: &base {enabled: true, limit: 12}\ncopy: *base\nname: "caf\u00e9"\n'
    assert skill_utils.yaml_load(text) == yaml.safe_load(text)
    with pytest.raises(yaml.constructor.ConstructorError):
        skill_utils.yaml_load("!!python/tuple [1, 2]")


def test_config_reads_preserve_profile_isolation_and_mutable_copies(tmp_path, monkeypatch):
    profiles = [tmp_path / name for name in ("first", "second")]
    for profile in profiles:
        profile.mkdir()
        (profile / "config.yaml").write_text(
            f"model:\n  default: {profile.name}\nspeed:\n  enabled: false\n", encoding="utf-8",
        )
    for profile in profiles + profiles[:1]:
        monkeypatch.setenv("SONIC_HOME", str(profile))
        with ThreadPoolExecutor(max_workers=4) as pool:
            configs = list(pool.map(lambda _: load_config_readonly(), range(12)))
        assert all(config["model"]["default"] == profile.name for config in configs)
        assert all(config is configs[0] for config in configs)
        mutable = load_config()
        mutable["model"]["default"] = "changed"
        assert load_config_readonly()["model"]["default"] == profile.name
        assert read_raw_config()["model"]["default"] == profile.name


def test_plugin_manifest_uses_safe_yaml_semantics(tmp_path):
    path = tmp_path / "plugin.yaml"
    path.write_text("name: example\nversion: 1\nrequires_env: [SERVICE_TOKEN]\n", encoding="utf-8")
    manager = PluginManager()
    manifest = manager._parse_manifest(path, tmp_path, "user", "")
    assert manifest.name == "example"
    assert manifest.requires_env == ["SERVICE_TOKEN"]
    path.write_text("!!python/tuple [1, 2]\n", encoding="utf-8")
    assert manager._parse_manifest(path, tmp_path, "user", "") is None
