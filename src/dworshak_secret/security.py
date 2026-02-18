# src/dowrshak_access/security.py
from __future__ import annotations
from pathlib import Path

from .paths import DB_FILE, ensure_secure_permissions, get_key_path_for_db

def get_fernet(db_path: Path | str | None = None):
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
    final_key_path = get_key_path_for_db(db_path)

    if not final_key_path.exists():
        # Only auto-generate for the DEFAULT vault to prevent key-spam
        # We check if db_path is None or points to the default DB_FILE
        from .paths import DB_FILE
        is_default = (db_path is None) or (Path(db_path) == DB_FILE)
        
        if is_default:
            final_key_path.parent.mkdir(parents=True, exist_ok=True)
            key = Fernet.generate_key()
            final_key_path.write_bytes(key)
            ensure_secure_permissions(final_key_path)
        else:
            # For custom vaults, if the key isn't there, we don't invent one.
            return None

    try:
        key = final_key_path.read_bytes()
        return Fernet(key)
    except Exception:
        return None
