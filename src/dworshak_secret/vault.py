# src/dowrshak_access/vault.py
from __future__ import annotations
import sqlite3
import os
import stat
from pathlib import Path
from typing import NamedTuple, List
from enum import IntEnum, Enum
import json
import datetime
import shutil
from dataclasses import dataclass


from .paths import (
    DB_FILE, 
    APP_DIR, 
    get_default_export_path,
    secure_chmod,
    get_backup_path
)

CURRENT_TOOL_SCHEMA_VERSION = 2  # Increment this when table structure changes

class VaultStatus(NamedTuple):
    is_valid: bool
    message: str
    root_path: Path
    rw_code: int | None
    health_code: int
    vault_db_version: int

class VaultCode(IntEnum):
    DIR_MISSING = 0
    DB_MISSING = 1
    KEY_MISSING = 2
    HEALTHY_WITH_RW_WARNINGS = 3
    HEALTHY = 4
    DB_CORRUPTED = 5


@dataclass
class VaultResponse:
    success: bool
    message: str
    is_new: bool = False

def initialize_vault() -> VaultResponse:
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
        
        if existing_version < CURRENT_TOOL_SCHEMA_VERSION:
            _dont_run_migrations(existing_version)
            # ACTUAL HEALING (tbd)
            # #_run_migrations(conn, existing_version)
            return VaultResponse(success=False, message=f"Version mismatch: {existing_version} < {CURRENT_TOOL_SCHEMA_VERSION}")

        return VaultResponse(success=True, message="Existing vault verified and ready.", is_new=False)
    finally:
        conn.close()


def _dont_run_migrations():
    print(f"This version of Dworshak CLI does not provide auto-migration of db-healing.")

def _run_migrations(conn: sqlite3.Connection, from_version: int):
    """
    Sequentially applies all migrations from current version up to 
    CURRENT_TOOL_SCHEMA_VERSION.

    status: psuedo-code.
    """
    
    def _migrate_to_v1(conn):
        _create_base_schema(conn)

    def _migrate_to_v2(conn):
        # Example: Column rename via Temp Table Pattern
        conn.execute("CREATE TABLE encrypted_secret (...)")
        conn.execute("INSERT INTO encrypted_secret SELECT ... FROM secret")
        conn.execute("ALTER TABLE encrypted_secret RENAME TO secret")
        conn.execute("DROP TABLE encrypted_secret")

    def _migrate_to_v3(conn):
        # Future expansion
        pass

    # Map of (target_version): migration_function
    MIGRATIONS = {
        1: _migrate_to_v1,
        2: _migrate_to_v2,
        3: _migrate_to_v3,
    }

    # Run every migration that is newer than the file's current version
    for version in sorted(MIGRATIONS.keys()):
        if version > from_version and version <= CURRENT_TOOL_SCHEMA_VERSION:
            print(f"Heal: Migrating vault to version {version}...")
            MIGRATIONS[version](conn)

def _create_base_schema(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            service TEXT NOT NULL,
            item TEXT NOT NULL,
            encrypted_secret BLOB NOT NULL,
            PRIMARY KEY(service, item)
        )
    """)

def is_db_corrupted(db_file = DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    return _check_for_corruption(conn)
    
def _check_for_corruption(conn):
    cursor = conn.execute("PRAGMA integrity_check")
    result = cursor.fetchone()[0]
    return result != "ok"
    
def check_vault(db_path: Path | str | None) -> VaultStatus:
    from .paths import KEY_FILE
    from .security import get_fernet

    # Resolve the path immediately
    db_path = Path(db_path) if db_path else DB_FILE
    
    if not APP_DIR.exists():
        return VaultStatus(False, "Vault directory missing", APP_DIR, _get_rw_mode(None),VaultCode.DIR_MISSING, CURRENT_TOOL_SCHEMA_VERSION)
    if not db_path.exists():
        return VaultStatus(False, "Vault DB missing", APP_DIR, _get_rw_mode(None), VaultCode.DB_MISSING, CURRENT_TOOL_SCHEMA_VERSION)
    if is_db_corrupted(db_path):
        return VaultStatus(False, "Vault DB corrupted", APP_DIR, _get_rw_mode(db_path), VaultCode.DB_CORRUPTED, CURRENT_TOOL_SCHEMA_VERSION)
    if not KEY_FILE.exists():
        return VaultStatus(True, "Encryption key file missing", APP_DIR, _get_rw_mode(db_path), VaultCode.KEY_MISSING, CURRENT_TOOL_SCHEMA_VERSION)
    if not get_fernet():
        return VaultStatus(True, "Cryptography library not available", APP_DIR, _get_rw_mode(db_path), VaultCode.KEY_MISSING, CURRENT_TOOL_SCHEMA_VERSION)
    
    # Section to check for 0o600 permissions of KEY_FILE and db_path
    warnings = []

    if os.name != "nt":
        if not _is_600(db_path):
            warnings.append("vault.db permissions are not 600")

        if not _is_600(KEY_FILE):
            warnings.append(".key permissions are not 600")

    if warnings:
        return VaultStatus(
            True,
            "Vault healthy (warnings: " + "; ".join(warnings) + ")",
            APP_DIR,
            _get_rw_mode(db_path),
            VaultCode.HEALTHY_WITH_RW_WARNINGS,
            CURRENT_TOOL_SCHEMA_VERSION
        )

    return VaultStatus(True, "Vault healthy", APP_DIR, _get_rw_mode(db_path), VaultCode.HEALTHY, CURRENT_TOOL_SCHEMA_VERSION)

def _get_rw_mode(path: Path | None = None) -> int | None: 
    if path is None:
        return None
    try:
        # stat.S_IMODE returns an int
        return stat.S_IMODE(path.stat().st_mode)
    except Exception as e:
        # Don't print inside a low-level helper if it can be avoided
        # but for debugging it's fine.
        return None

def _is_600(path: Path) -> bool:
    try:
        mode = _get_rw_mode(path)
        return mode == 0o600 # <-- notice that this is not a string. it is a hexidecimal integer.
    except Exception:
        return False

def backup_vault(
    db_path: Path | str | None,
    extra_suffix: str = "",
    include_timestamp: bool = True,
    dest_dir: Path | str | None = None,
) -> Path | None:
    
    # Resolve the path immediately
    db_path = Path(db_path) if db_path else DB_FILE
    if not db_path.exists():
        print("No vault database to back up.")
        return None

    backup_path = get_backup_path(
        extra_suffix=extra_suffix,
        dest_dir=dest_dir,
        include_timestamp=include_timestamp,
    )

    try:
        shutil.copy2(db_path, backup_path)
        secure_chmod(backup_path)
        #print(f"Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        #print(f"Backup failed: {e}")
        return None
