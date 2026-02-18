# src/dowrshak_access/paths.py
from __future__ import annotations
from pathlib import Path
import time
import datetime
import os
import stat

APP_DIR = Path.home() / ".dworshak"
DB_FILE = APP_DIR / "vault.db"
KEY_FILE = APP_DIR / ".key"
CONFIG_FILE = APP_DIR / "config.json"

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
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
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

def ensure_secure_permissions(path: Path) -> bool:
    """
    Ensures a file has 0o600 permissions. 
    Returns True if permissions are correct or fixed, False if failed.
    """
    if os.name == "nt" or not path.exists():
        return True
    
    current_mode = stat.S_IMODE(path.stat().st_mode)
    if current_mode != 0o600:
        try:
            path.chmod(0o600)
            return True
        except Exception:
            return False
    return True

def get_key_path_for_db(db_path: Path | str | None = None) -> Path:
    """Resolves the associated .key path for a given database file."""
    db_p = Path(db_path) if db_path else DB_FILE
    if db_p == DB_FILE:
        return KEY_FILE
    return db_p.parent / ".key"