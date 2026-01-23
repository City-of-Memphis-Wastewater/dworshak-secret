# src/dowrshak_access/vault.py
from __future__ import annotations
import sqlite3
import os
import stat
from pathlib import Path
from typing import NamedTuple, List
from enum import IntEnum

from .paths import DB_FILE, APP_DIR
from .security import get_fernet

CURRENT_DB_VERSION = 2  # Increment this when you change the table structure

class VaultStatus(NamedTuple):
    is_valid: bool
    message: str
    root_path: Path
    code: int

class VaultCode(IntEnum):
    DIR_MISSING = 0
    DB_MISSING = 1
    KEY_MISSING = 2
    HEALTHY_WITH_WARNINGS = 3
    HEALTHY = 4

def initialize_vault() -> None:
    """Create vault DB with encrypted_secret column."""
    existing_version = None
    APP_DIR.mkdir(parents=True, exist_ok=True)
    get_fernet() 
    
    conn = sqlite3.connect(DB_FILE)
    try:
        existing_version = conn.execute("PRAGMA user_version").fetchone()[0]
        if existing_version == 0:
            # INITIAL BUILD (Same as your previous logic)
            _create_base_schema(conn)
        
        elif existing_version < CURRENT_DB_VERSION:
            print(f"Your DB_FILE ({DB_FILE}) has a version mismatch with your version of the Dworshak CLI.")
            print(f"Vault database schema version = {existing_version}")
            print(f"CLI database schema version = {CURRENT_DB_VERSION}")
            _dont_run_migrations(existing_version)
            # ACTUAL HEALING
            # #_run_migrations(conn, existing_version)
            
        conn.execute(f"PRAGMA user_version = {CURRENT_DB_VERSION}")
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        return existing_version
    finally:
        conn.close()
    return existing_version

def _dont_run_migrations():
    print(f"This version of Dworshak CLI does not provide auto-migration of db-healing.")

def _run_migrations(conn: sqlite3.Connection, from_version: int):
    """
    Sequentially applies all migrations from current version up to 
    CURRENT_DB_VERSION.

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
        if version > from_version and version <= CURRENT_DB_VERSION:
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


def check_vault() -> VaultStatus:
    if not APP_DIR.exists():
        return VaultStatus(False, "Vault directory missing", APP_DIR, VaultCode.DIR_MISSING)
    if not DB_FILE.exists():
        return VaultStatus(False, "Vault DB missing", APP_DIR, VaultCode.DB_MISSING)
    if not get_fernet():
        return VaultStatus(False, "Encryption key missing", APP_DIR, VaultCode.KEY_MISSING)
    
    # Section to check for 0o600 permissions of KEY_FILE and DB_FILE
    warnings = []

    if os.name != "nt":
        if not _is_600(DB_FILE):
            warnings.append("vault.db permissions are not 600")

        from .paths import KEY_FILE
        if not _is_600(KEY_FILE):
            warnings.append(".key permissions are not 600")

    if warnings:
        return VaultStatus(
            True,
            "Vault healthy (warnings: " + "; ".join(warnings) + ")",
            APP_DIR,
            VaultCode.HEALTHY_WITH_WARNINGS 
        )

    return VaultStatus(True, "Vault healthy", APP_DIR, VaultCode.HEALTHY)

def store_secret(service: str, item: str, secret: str):
    """Encrypts and stores a single secret string to the vault"""
    _early_exit_no_db()

    payload = secret.encode()
    fernet = get_fernet()
    encrypted_secret = fernet.encrypt(payload)

    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT OR REPLACE INTO credentials (service, item, encrypted_secret) VALUES (?, ?, ?)",
        (service, item, encrypted_secret)
    )
    conn.commit()
    conn.close()

def get_secret(
        service: str, 
        item: str,
        fail: bool = False,
        ) -> dict[str, str]:
    """
    Returns decrypted secret for service/item.

    Args:
        service: The service name.
        item: The credential key.
        fail: If True, raise KeyError when secret is missing.
              If False, return None.

    Returns:
        Decrypted string if found, else None (unless fail=True)
    """

    # Ensure vault exists before querying
    _early_exit_no_db()
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute(
        "SELECT encrypted_secret FROM credentials WHERE service=? AND item=?",
        (service, item)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        if fail:
            raise KeyError(f"No credential found for {service}/{item}")
        return None
    fernet = get_fernet()
    decrypted = fernet.decrypt(row[0])
    return decrypted.decode()

def remove_secret(service: str, item: str) -> bool:
    """
    Remove a secret from the vault.

    Args:
        service: The service name.
        item: The credential key.

    Returns:
        True if a row was deleted, False if nothing was found.
    """
    _early_exit_no_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute(
        "DELETE FROM credentials WHERE service=? AND item=?",
        (service, item)
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0
    
def list_credentials() -> List[tuple[str, str]]:
    _early_exit_no_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute("SELECT service, item FROM credentials")
    rows = cursor.fetchall()
    conn.close()
    return rows

def _is_600(path: Path) -> bool:
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
        return mode == 0o600
    except Exception:
        return False

def _early_exit_no_db(fail: bool = False):
    status = check_vault()
    
    if not status.is_valid:
        if fail:
            raise KeyError(f"Vault Issue: {status.message}")
            
        # Logic is now anchored to specific states, not strings
        if status.code in (VaultCode.DIR_MISSING, VaultCode.DB_MISSING):
            initialize_vault()
        else:
            # Permission/Key issues shouldn't be auto-initialized
            print(f"Warning: {status.message}")
        return True
    return False


