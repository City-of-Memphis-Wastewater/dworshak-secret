# src/dworshak_secret/crytpo/fernet.py
from __future__ import annotations
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from .base import CryptoBackend
from ..security import (get_fernet, get_key_str_from_key_path)
from ..paths import resolve_key_path_for_db
from ..errors import WrongKeyError

class FernetBackend(CryptoBackend):
    def __init__(self, db_path, key_path=None):
        final_key_path = resolve_key_path_for_db(db_path=db_path, key_path=key_path)
        key_str = get_key_str_from_key_path(key_path=final_key_path)
        self.fernet = get_fernet(key_str=key_str)
        
        if not self.fernet:
            raise RuntimeError("Crypto unavailable")

    def encrypt(self, data: bytes) -> bytes:
        try:
            return self.fernet.encrypt(data)
        except InvalidToken:
            raise WrongKeyError("Invalid encryption key or corrupted data.") from None

    
    def decrypt(self, data: bytes) -> bytes:
        try:
            return self.fernet.decrypt(data)
        except InvalidToken:
            raise WrongKeyError("Invalid encryption key or corrupted data.") from None
