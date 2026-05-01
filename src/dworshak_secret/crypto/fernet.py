# src/dworshak_secret/crytpo/fernet.py
from __future__ import annotations
from cryptography.fernet import Fernet
from .base import CryptoBackend
from ..security import get_fernet


class FernetBackend(CryptoBackend):
    def __init__(self, db_path, key_path=None):
        self.fernet = get_fernet(db_path=db_path, key_path=key_path)

        if not self.fernet:
            raise RuntimeError("Crypto unavailable")

    def encrypt(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        return self.fernet.decrypt(data)
