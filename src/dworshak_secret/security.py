# src/dowrshak_access/security.py
from __future__ import annotations
import os
from pathlib import Path

from .paths import KEY_FILE, secure_chmod

def get_fernet(key_path: Path | str | None = None):
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
    final_key_path = Path(key_path) if key_path else KEY_FILE

    if not final_key_path.exists():
        # Only auto-generate if we are using the DEFAULT key file
        if key_path is None:
            # Ensure the directory exists before writing the key
            final_key_path.parent.mkdir(parents=True, exist_ok=True)
            
            key = Fernet.generate_key()
            final_key_path.write_bytes(key)
            secure_chmod(final_key_path)
        else:
            # If a specific path was requested but doesn't exist, 
            # we don't auto-generate (prevents key fragmentation)
            return None

    try:
        key = final_key_path.read_bytes()
        return Fernet(key)
    except Exception:
        return None

