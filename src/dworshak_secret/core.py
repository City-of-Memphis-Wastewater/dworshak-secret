# src/dworshak_secret/core.py
from __future__ import annotations
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Optional, Any

from .paths import DB_FILE
from . import vault

class DworshakSecret:
    """
    The 'Dworshak Standard' interface for secret management.
    Matches the pattern of DworshakEnv and DworshakConfig.
    """
    def __init__(self, db_path: Path | str | None = None):
        # Resolve the path immediately
        self.db_path = Path(db_path) if db_path else DB_FILE

    def get(self, service: str, item: str, fail: bool = False,  fernet: Any = None) -> str | None:
        """Retrieve and decrypt a secret."""
        # 1. Check health specifically for this path
        # Note: We rely on the caller/CLI to have initialized the vault
        status = vault.check_vault(self.db_path)
        if not status.is_valid:
            if fail:
                raise FileNotFoundError(f"Vault error at {self.db_path}: {status.message}")
            return None

        # 2. Extract from DB
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT encrypted_secret FROM credentials WHERE service=? AND item=?",
                (service, item)
            )
            row = cursor.fetchone()
        finally:
            conn.close()

        if not row:
            if fail:
                raise KeyError(f"No credential found for {service}/{item}")
            return None

        # 3. Decrypt
        f = fernet or self._get_fernet() 
        if not f:
            raise RuntimeError("Cryptography unavailable or Key file missing. Cannot process secret.")
            
        decrypted = f.decrypt(row[0])
        return decrypted.decode()

    def set_(self, service: str, item: str, value: str, overwrite: bool = True, fernet: Any = None):
        """Encrypt and store a secret."""
        
        # Ensure infra exists (Passively check, then let it fail if needed)
        # Or you could call vault.initialize_vault() here if you want to keep protection
        
        f = fernet or self._get_fernet() 
        if not f:
            raise RuntimeError("Cryptography unavailable or Key missing. Cannot encrypt.")

        payload = value.encode()
        encrypted_secret = f.encrypt(payload)

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT OR REPLACE INTO credentials (service, item, encrypted_secret) VALUES (?, ?, ?)",
                (service, item, encrypted_secret)
            )
            conn.commit()
        finally:
            conn.close()

    def set(self, service: str, item: str, value: str, overwrite: bool = True, fernet: Any = None):
        """
        Encrypt and store a secret.
        
        If overwrite is False, raises FileExistsError if the record already exists.
        """
        # 1. Existence check if overwrite is disallowed
        if not overwrite:
            existing = self.get(service, item)
            if existing is not None:
                raise FileExistsError(f"Credential for {service}/{item} already exists.")

        f = fernet or self._get_fernet() 
        if not f:
            raise RuntimeError("Cryptography unavailable or Key missing. Cannot encrypt.")

        payload = value.encode()
        encrypted_secret = f.encrypt(payload)

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT OR REPLACE INTO credentials (service, item, encrypted_secret) VALUES (?, ?, ?)",
                (service, item, encrypted_secret)
            )
            conn.commit()
        finally:
            conn.close()

    def list(self) -> List[tuple[str, str]]:
        """List all service/item pairs."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("SELECT service, item FROM credentials")
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            # Likely table doesn't exist yet
            return []
        finally:
            conn.close()
        return rows
    

    def remove(self, service: str, item: str) -> bool:
        """Delete a secret."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "DELETE FROM credentials WHERE service=? AND item=?",
                (service, item)
            )
            conn.commit()
            affected = cursor.rowcount
        finally:
            conn.close()
        return affected > 0
    
    # inside src/dworshak_secret/core.py

    def _get_fernet(self):
        """
        Internal helper to resolve the correct Fernet instance for this vault.
        """
        from .security import get_fernet

        return get_fernet(db_path=self.db_path)

# --- Legacy Functional API (Compatibility Layer) ---

def get_secret(service: str, item: str, fail: bool = False, db_path: Path | str | None = None) -> str | None:
    return DworshakSecret(db_path).get(service, item, fail=fail)

def store_secret(service: str, item: str, secret: str, overwrite: bool = True, db_path: Path | str | None = None):
    return DworshakSecret(db_path).set(service, item, secret)

def list_credentials(db_path: Path | str | None = None) -> List[tuple[str, str]]:
    return DworshakSecret(db_path).list()

def remove_secret(service: str, item: str, db_path: Path | str | None = None) -> bool:
    return DworshakSecret(db_path).remove(service, item)
