# src/dowrshak_access/vault.py
from __future__ import annotations
import sqlite3
import os
import stat
from pathlib import Path
from typing import NamedTuple
from enum import IntEnum
from dataclasses import dataclass
from .paths import DB_FILE, APP_DIR, KEY_FILE

CURRENT_TOOL_SCHEMA_VERSION = 2

class VaultCode(IntEnum):
    DIR_MISSING = 0
    DB_MISSING = 1
    KEY_MISSING = 2
    HEALTHY_WITH_RW_WARNINGS = 3
    HEALTHY = 4
    DB_CORRUPTED = 5

class VaultStatus(NamedTuple):
    is_valid: bool
    message: str
    root_path: Path
    rw_code: int | None
    health_code: int
    vault_db_version: int

@dataclass
class VaultResponse:
    success: bool
    message: str
    is_new: bool = False

def initialize_vault() -> VaultResponse:
    """Infrastructure setup: ensures directories and base schema exist."""
    from .security import get_fernet
    APP_DIR.mkdir(parents=True, exist_ok=True)
    get_fernet()

    conn = sqlite3.connect(DB_FILE)
    try:
        existing_version = conn.execute("PRAGMA user_version").fetchone()[0]
        if existing_version == 0:
            _create_base_schema(conn)
            conn.execute(f"PRAGMA user_version = {CURRENT_TOOL_SCHEMA_VERSION}")
            conn.commit()
            return VaultResponse(success=True, message="New vault initialized.", is_new=True)
        return VaultResponse(success=True, message="Vault verified.", is_new=False)
    finally:
        conn.close()

def check_vault(db_path: Path | str | None = None) -> VaultStatus:
    """The source of truth for vault health."""
    from .security import get_fernet
    db_path = Path(db_path) if db_path else DB_FILE

    if not APP_DIR.exists():
        return VaultStatus(False, "Vault directory missing", APP_DIR, None, VaultCode.DIR_MISSING, CURRENT_TOOL_SCHEMA_VERSION)
    if not db_path.exists():
        return VaultStatus(False, "Vault DB missing", APP_DIR, None, VaultCode.DB_MISSING, CURRENT_TOOL_SCHEMA_VERSION)
    if is_db_corrupted(db_path):
        return VaultStatus(False, "Vault DB corrupted", APP_DIR, _get_rw_mode(db_path), VaultCode.DB_CORRUPTED, CURRENT_TOOL_SCHEMA_VERSION)
    
    # Logic: Key check
    fernet = get_fernet()
    if not KEY_FILE.exists() or not fernet:
        return VaultStatus(True, "Key missing/Crypto unavailable", APP_DIR, _get_rw_mode(db_path), VaultCode.KEY_MISSING, CURRENT_TOOL_SCHEMA_VERSION)

    # Permission checks for non-Windows
    warnings = []
    if os.name != "nt":
        if not _is_600(db_path): warnings.append("vault.db permissions not 600")
        if not _is_600(KEY_FILE): warnings.append(".key permissions not 600")

    if warnings:
        return VaultStatus(True, f"Healthy (warnings: {'; '.join(warnings)})", APP_DIR, _get_rw_mode(db_path), VaultCode.HEALTHY_WITH_RW_WARNINGS, CURRENT_TOOL_SCHEMA_VERSION)

    return VaultStatus(True, "Vault healthy", APP_DIR, _get_rw_mode(db_path), VaultCode.HEALTHY, CURRENT_TOOL_SCHEMA_VERSION)

def is_db_corrupted(db_path: Path) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        return result != "ok"
    finally:
        conn.close()

def _create_base_schema(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            service TEXT NOT NULL,
            item TEXT NOT NULL,
            encrypted_secret BLOB NOT NULL,
            PRIMARY KEY(service, item)
        )
    """)



def _get_rw_mode(path: Path) -> int | None:
    try: return stat.S_IMODE(path.stat().st_mode)
    except Exception: return None

def _is_600(path: Path) -> bool:
    return _get_rw_mode(path) == 0o600