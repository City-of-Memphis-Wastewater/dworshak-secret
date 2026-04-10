# src/dworshak_access/security.py
from __future__ import annotations
from pathlib import Path

from .paths import DB_FILE, ensure_secure_permissions, get_key_path_for_db
from .registry import get_registered_key, register_vault_key

def get_fernet(db_path: Path | str | None = None, allow_create: bool = False):
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

    # 1. Try to find the key via Registry
    final_key_path = get_registered_key(db_path)
    
    # 2. Fallback to legacy path logic if not in registry
    if not final_key_path:
        final_key_path = get_key_path_for_db(db_path)

    #final_key_path = get_key_path_for_db(db_path)

    if not final_key_path.exists():
        # Only auto-generate for the DEFAULT vault to prevent key-spam
        # We check if db_path is None or points to the default DB_FILE
        is_default = (db_path is None) or (Path(db_path) == DB_FILE)
        
        if is_default or allow_create:
            final_key_path.parent.mkdir(parents=True, exist_ok=True)
            key = Fernet.generate_key()
            final_key_path.write_bytes(key)
            ensure_secure_permissions(final_key_path)

            # REGISTER he new key: Link this DB to this Key forever
            register_vault_key(db_path, {
                "key_path": str(final_key_path),
                "status": "active"
            })

        else:
            # For custom vaults, if the key isn't there, we don't invent one.
            return None

    try:
        key = final_key_path.read_bytes()
        return Fernet(key)
    except Exception:
        return None
