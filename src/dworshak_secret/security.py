# src/dworshak_access/security.py
from __future__ import annotations
from pathlib import Path

from .paths import DB_FILE, ensure_secure_permissions, get_key_path_for_db
from .registry import get_registered_key, register_vault_key
from .errors import MissingKeyError

def get_fernet(
    db_path: Path | str | None = None, 
    key_path: Path | str | None = None):
    """
    Returns a Fernet instance using the master key.
    Generates key if missing.
    """
    # Check without dying
    from .key import installation_check
    if not installation_check(die=False):
        return None
    from cryptography.fernet import Fernet

    # Resolve which key file to use
    db_path = Path(db_path) if db_path else DB_FILE

    final_key_path = get_key_path_for_db(db_path, key_path)
    
    if not final_key_path.exists():
        raise MissingKeyError(
            f"Encryption key not found for vault: {db_path}",
            db_path=db_path,
            key_path=final_key_path,
        )

    try:
        key = final_key_path.read_bytes()
        return Fernet(key)
    except Exception:
        return None
