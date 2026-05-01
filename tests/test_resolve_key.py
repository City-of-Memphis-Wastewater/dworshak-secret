from __future__ import annotations
from pathlib import Path

from dworshak_secret.registry import register_vault_key
from dworshak_secret.paths import get_key_path_for_db

def test_registry_missing_key_returns_none(tmp_path):
    from dworshak_secret.registry import get_registered_key

    fake_db = tmp_path / "vault.db"

    result = get_registered_key(fake_db)

    assert result is None

def test_registry_overrides_default(tmp_path):
    db = tmp_path / "vault.db"
    key = tmp_path / "custom.key"

    register_vault_key(db, {"key_path": str(key)})

    resolved = get_key_path_for_db(db)

    assert resolved == key.resolve()

def test_registry_relative_path(tmp_path, monkeypatch):
    from dworshak_secret import registry
    from dworshak_secret.paths import get_key_path_for_db

    # Redirect registry file to temp dir
    fake_registry = tmp_path / "keys.json"
    monkeypatch.setattr(registry, "KEY_REGISTRY_FILE", fake_registry)

    db = tmp_path / "vault.db"
    key = Path("relative.key")

    registry.register_vault_key(db, {"key_path": str(key)})

    resolved = get_key_path_for_db(db)

    assert resolved == (tmp_path / "relative.key").resolve()
