# src/dowrshak_access/paths.py
from __future__ import annotations
from pathlib import Path
import time

APP_DIR = Path.home() / ".dworshak"
DB_FILE = APP_DIR / "vault.db"
KEY_FILE = APP_DIR / ".key"
CONFIG_FILE = APP_DIR / "config.json"


# ---

# Default name
_ACTIVE_VAULT_NAME = "vault"

def set_active_vault(name: str):
    global _ACTIVE_VAULT_NAME
    _ACTIVE_VAULT_NAME = name

@property
def DB_FILE_() -> Path:
#def DB_FILE() -> Path: # suppressed for now to not conflex with DB_FILE
    return APP_DIR / f"{_ACTIVE_VAULT_NAME}.db"

# ---

def get_default_export_path(subject: str="dworshark_export", suffix: str = ".json") -> Path:
    """
    Standardizes output paths: ~/.dworshak/exports/dworshark_export_1706000000.json
    """
    # 1. Resolve Home with Fallback
    try:
        base_home = Path.home() / ".dworshak"
    except Exception:
        base_home = Path("/tmp/.dworshak_temp")
    
    export_dir = base_home / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    # 2. Build filename with Unix Timestamp
    unix_ts = int(time.time())
    filename = f"{subject}_{unix_ts}{suffix}"
    
    return export_dir / filename