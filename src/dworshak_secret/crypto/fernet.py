# src/dworshak_secret/crytpo/fernet.py
from __future__ import annotations
from cryptography.fernet import Fernet
from .base import CryptoBackend
from ..security import (get_fernet, get_fernet_from_key_path, get_key_str_from_key_path, get_resolved_key_path


class FernetBackend(CryptoBackend):
    def __init__(self, db_path, key_path=None):
        final_key_path = get_resolved_key_path(db_path=db_path, key_path=key_path)
        key_str = get_key_str_from_key_path(key_path=final_key_path)
        self.fernet = get_fernet(key_str=key_str)
        
        if not self.fernet:
            raise RuntimeError("Crypto unavailable")

    def encrypt(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        return self.fernet.decrypt(data)
