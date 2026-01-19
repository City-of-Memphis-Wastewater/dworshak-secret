# src/dowrshak_access/vault.py
from __future__ import annotations
import sqlite3
import os
import stat
from pathlib import Path
from typing import NamedTuple, List
from .paths import DB_FILE, APP_DIR
from .security import get_fernet

class VaultStatus(NamedTuple):
    is_valid: bool
    message: str
    root_path: Path

def initialize_vault() -> None:
    """Create vault DB with encrypted_secret column."""
    APP_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure key exists (and permissions are set there)
    get_fernet()

    first_time = not DB_FILE.exists()
    conn = sqlite3.connect(DB_FILE)

    if first_time:
        os.chmod(DB_FILE, 0o600)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            service TEXT NOT NULL,
            item TEXT NOT NULL,
            encrypted_secret BLOB NOT NULL,
            PRIMARY KEY(service, item)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL
        )
    """)
    # Set version 1 if empty
    cursor = conn.execute("SELECT COUNT(*) FROM schema_version")
    if cursor.fetchone()[0] == 0:
        conn.execute("INSERT INTO schema_version (version) VALUES (1)")
    conn.commit()
    conn.close()

def check_vault() -> VaultStatus:
    if not APP_DIR.exists():
        return VaultStatus(False, "Vault directory missing", APP_DIR)
    if not DB_FILE.exists():
        return VaultStatus(False, "Vault DB missing", APP_DIR)
    if not get_fernet():
        return VaultStatus(False, "Encryption key missing", APP_DIR)
    
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
        )

    return VaultStatus(True, "Vault healthy", APP_DIR)

def store_secret(service: str, item: str, secret: str):
    """Encrypts and stores a single secret string to the vault"""
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

def get_secret(service: str, item: str) -> dict[str, str]:
    """Returns decrypted blob single secret string from the vault."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute(
        "SELECT encrypted_secret FROM credentials WHERE service=? AND item=?",
        (service, item)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise KeyError(f"No credential found for {service}/{item}")

    fernet = get_fernet()
    decrypted = fernet.decrypt(row[0])
    return decrypted.decode()

def list_credentials() -> List[tuple[str, str]]:
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
