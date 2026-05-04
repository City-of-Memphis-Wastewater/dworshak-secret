# src/dworshak_access/security.py
from __future__ import annotations
from pathlib import Path

from .paths import get_key_path_for_db

def get_fernet_from_key_path(
    db_path: Path | str | None = None, 
    key_path: Path | str | None = None
    ):
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

    final_key_path = get_key_path_for_db(db_path, key_path)

    try:
        key_str = get_key_str_from_key_path(final_key_path)
        return get_fernet(key_str)
    except Exception:
        return None
    


def get_key_str_from_key_path(
    key_path: Path | str | None = None
    )->str:
    """
    Returns a Fernet instance using the master key.
    Generates key if missing.
    """
    key_str = key_path.read_bytes()
    return key_str
    
def get_fernet(
    key_str: str | None = None
    ):
    """
    Returns a Fernet instance using the master key.
    Generates key if missing.
    """
    # Check without dying
    from .key import installation_check
    if not installation_check(die=False):
        return None
    from cryptography.fernet import Fernet

    return Fernet(key_str)

    """
    try:
        return Fernet(key_str)
    except Exception:
        return None

    """
