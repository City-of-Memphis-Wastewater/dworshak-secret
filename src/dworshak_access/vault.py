# src/dowrshak_access/vault.py
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import NamedTuple, List
from .paths import DB_FILE, APP_DIR
from .security import get_fernet

class VaultStatus(NamedTuple):
    is_valid: bool
    message: str
    root_path: Path

def initialize_vault() -> None:
    """Create vault DB with encrypted secret column."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            service TEXT NOT NULL,
            item TEXT NOT NULL,
            secret BLOB NOT NULL,
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
    return VaultStatus(True, "Vault healthy", APP_DIR)

def store_secret(service: str, item: str, username: str, password: str):
    """Encrypts and stores both username/password as a single blob."""
    payload = json.dumps({"u": username, "p": password}).encode()
    fernet = get_fernet()
    encrypted_blob = fernet.encrypt(payload)

    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT OR REPLACE INTO credentials (service, item, encrypted_blob) VALUES (?, ?, ?)",
        (service, item, encrypted_blob)
    )
    conn.commit()
    conn.close()

def store_secret_(service: str, item: str, plaintext: str):
    f = get_fernet()
    encrypted_secret = f.encrypt(plaintext.encode())
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT OR REPLACE INTO credentials (service, item, secret) VALUES (?, ?, ?)",
        (service, item, encrypted_secret)
    )
    conn.commit()
    conn.close()

def get_secret(service: str, item: str) -> dict[str, str]:
    """Returns decrypted blob as a dict with 'u' and 'p'."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute(
        "SELECT encrypted_blob FROM credentials WHERE service=? AND item=?",
        (service, item)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise KeyError(f"No credential found for {service}/{item}")

    fernet = get_fernet()
    decrypted = fernet.decrypt(row[0])
    return json.loads(decrypted)

def get_secret_(service: str, item: str) -> str:
    f = get_fernet()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute(
        "SELECT secret FROM credentials WHERE service = ? AND item = ?",
        (service, item)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise KeyError(f"No credential found for {service}/{item}")
    return f.decrypt(row[0]).decode()

def list_credentials() -> List[tuple[str, str]]:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute("SELECT service, item FROM credentials")
    rows = cursor.fetchall()
    conn.close()
    return rows
