# src/dowrshak_access/security.py
from __future__ import annotations
import os

from .paths import KEY_FILE
from .key import installation_check

def get_fernet() -> Fernet:
    """
    Returns a Fernet instance using the master key.
    Generates key if missing.
    """
    installation_check()
    if not KEY_FILE.exists():
        APP_DIR = KEY_FILE.parent
        APP_DIR.mkdir(parents=True, exist_ok=True)
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
        os.chmod(KEY_FILE, 0o600)

    key_bytes = KEY_FILE.read_bytes()
    return Fernet(key_bytes)

