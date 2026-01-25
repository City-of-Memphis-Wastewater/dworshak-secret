# src/dowrshak_access/paths.py
from __future__ import annotations
from pathlib import Path
import time
import datetime

APP_DIR = Path.home() / ".dworshak"
DB_FILE = APP_DIR / "vault.db"
KEY_FILE = APP_DIR / ".key"
CONFIG_FILE = APP_DIR / "config.json"


# ---
"""
# Default name
_ACTIVE_VAULT_NAME = "vault"

def set_active_vault(name: str):
    global _ACTIVE_VAULT_NAME
    _ACTIVE_VAULT_NAME = name

@property
def DB_FILE_() -> Path:
#def DB_FILE() -> Path: # suppressed for now to not conflex with DB_FILE
    return APP_DIR / f"{_ACTIVE_VAULT_NAME}.db"
"""
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

def get_vault_backup_filename(
    extra_suffix: str = "",
    include_timestamp: bool = True,
) -> str:
    """
    Generate filename for vault.db backups.
    Examples:
    - vault.db.bak_20260124_182530.db
    - vault.db.bak_pre-import_20260124_182530.db
    - vault.db.bak_20260124_182530.db  (no extra suffix)
    """
    base = "vault.db.bak"
    parts = [base]

    if include_timestamp:
        ts = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
        parts.append(ts)

    if extra_suffix:
        cleaned = extra_suffix.strip("_ -")
        if cleaned:
            parts.append(cleaned)

    return "_".join(parts) + ".db"

def get_backup_path(
    extra_suffix: str = "",
    dest_dir: Path | str | None = None,
    include_timestamp: bool = True,
) -> Path:
    """Full path for a vault backup file."""
    parent = APP_DIR if dest_dir is None else Path(dest_dir).resolve()
    parent.mkdir(parents=True, exist_ok=True)

    filename = get_vault_backup_filename(
        extra_suffix=extra_suffix,
        include_timestamp=include_timestamp,
    )
    return parent / filename

def secure_chmod(path: Path):
    """Apply restrictive 0o600 permissions if not on Windows."""
    if os.name != "nt":
        try:
            path.chmod(0o600)
        except Exception as e:
            print(f"Warning: Failed to set permissions on {path}: {e}")
