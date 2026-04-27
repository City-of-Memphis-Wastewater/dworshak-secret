# src/dworshak_secret/core.py
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Optional, Any
import logging

from .paths import DB_FILE

from .actions import backup_vault
from .actions import export_vault
from .actions import import_records
from .vault import initialize_vault
from .vault import check_vault
from .key import rotate_key

logger = logging.getLogger(__name__)

class DworshakSecret:
    """
    The 'Dworshak Standard' interface for secret management.
    Matches the pattern of DworshakEnv and DworshakConfig.
    """
    def __init__(self, 
        db_path: Path | str | None = None,
        key_path: Path | str | None = None
        ):
        # Resolve the path immediately
        self.db_path = Path(db_path) if db_path else DB_FILE
        self.key_path = Path(key_path) if key_path else None
        
    def get(self, service: str, item: str, fail: bool = False,  fernet: Any = None) -> str | None:
        """Retrieve and decrypt a secret."""
        # 1. Check health specifically for this path
        # Note: We rely on the caller/CLI to have initialized the vault
        self.initialize_vault()
        status = self.check_vault()
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

    def set(self, service: str, item: str, value: str, overwrite: bool = True, fernet: Any = None):
        """
        Encrypt and store a secret.
        
        If overwrite is False, raises FileExistsError if the record already exists.
        """
        self.initialize_vault()
        # 1. Existence check if overwrite is disallowed
        logger.debug(f"self.list_contents() = {self.list_contents()}")
        if not overwrite and (service, item) in self.list_contents():
            logger.warning(
                f"Skipping set of {service}/{item} — already exists and overwrite=False"
            )
            return
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

    def list_contents(self) -> List[tuple[str, str]]:
        """List all service/item pairs."""
        self.initialize_vault()
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
        self.initialize_vault()
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

        return get_fernet(db_path=self.db_path,key_path=self.key_path)
    
    # --- Wrappers around vault functions ---
    # To pass the db_path attribute. Use **kwargs to relieve maintenance burden for wrappers.
    
    def initialize_vault(self,**kwargs):
        return initialize_vault(self.db_path,**kwargs)
    def check_vault(self,**kwargs):
        return check_vault(self.db_path,**kwargs)
    def export_vault(self,**kwargs):
        return export_vault(self.db_path,**kwargs)
    def rotate_key(self,**kwargs):
        return rotate_key(self.db_path,**kwargs)
    def backup_vault(self,**kwargs):
        return backup_vault(self.db_path,**kwargs)
    def import_records(self,json_path:str|Path,**kwargs): 
        # json_path keyword explcitly provided because the function is otherwise useless
        return import_records(json_path,self.db_path,**kwargs) 
        

