# src/dworshak_secret/registry.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from .paths import KEY_REGISTRY_FILE

def load_key_registry() -> dict:
    if not KEY_REGISTRY_FILE.exists():
        return {}
    try:
        return json.loads(KEY_REGISTRY_FILE.read_text())
    except json.JSONDecodeError:
        return {}

def save_key_registry(data: dict):
    KEY_REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_REGISTRY_FILE.write_text(json.dumps(data, indent=2))
    # Standard dworshak permission safety
    from .paths import ensure_secure_permissions
    ensure_secure_permissions(KEY_REGISTRY_FILE)

def register_vault_key(db_path: Path | str, metadata: dict):
    """Generic registration for any vault-related metadata."""
    registry = load_key_registry()
    path_key = str(Path(db_path).resolve())
    
    current_entry = registry.get(path_key, {})
    current_entry.update(metadata)
    current_entry["last_seen"] = datetime.now().isoformat()
    
    registry[path_key] = current_entry
    save_key_registry(registry)

def get_registered_key(db_path: Path | str) -> Path | None:
    """Retrieve the key path for a specific vault."""
    registry = load_key_registry()
    path_key = str(Path(db_path).resolve())
    entry = registry.get(path_key)
    if entry and "key_path" in entry:
        return Path(entry["key_path"])
    return None