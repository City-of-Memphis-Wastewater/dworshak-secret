# src/dworshak-access/vault.py
import sqlite3
import os
from pathlib import Path
from typing import NamedTuple, List, Tuple, Optional
from cryptography.fernet import Fernet

DEFAULT_ROOT = Path.home() / ".dworshak"

class VaultStatus(NamedTuple):
    is_valid: bool
    message: str
    root_path: Path

def check_vault(root: Path = DEFAULT_ROOT) -> VaultStatus:
    """Diagnose the health of the Dworshak environment."""
    if not root.exists():
        return VaultStatus(False, "Vault directory does not exist.", root)
    if not (root / ".key").exists():
        return VaultStatus(False, "Security key (.key) is missing.", root)
    if not (root / "vault.db").exists():
        return VaultStatus(False, "Credential database (vault.db) is missing.", root)
    
    try:
        with sqlite3.connect(root / "vault.db") as conn:
            conn.execute("SELECT 1 FROM credentials LIMIT 1")
    except sqlite3.Error as e:
        return VaultStatus(False, f"Database error: {e}", root)
        
    return VaultStatus(True, "Vault is healthy.", root)

def get_secret(service: str, item: str, root: Path = DEFAULT_ROOT) -> str:
    """Retrieve and decrypt a specific secret."""
    key_path = root / ".key"
    db_path = root / "vault.db"

    if not key_path.exists():
        raise FileNotFoundError(f"Dworshak key not found at {key_path}")

    fernet = Fernet(key_path.read_bytes())

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT secret FROM credentials WHERE service = ? AND item = ?",
            (service, item)
        )
        row = cursor.fetchone()

    if not row:
        raise KeyError(f"No credential found for {service}/{item}")

    return fernet.decrypt(row[0]).decode()
