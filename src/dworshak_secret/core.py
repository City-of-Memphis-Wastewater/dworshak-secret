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

    def set(self, service: str, item: str, value: str, fernet: Any = None):
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
        from .paths import DB_FILE

        # Logic: If using a custom DB path, assume the .key is in the same folder.
        # Otherwise, let get_fernet() use the default KEY_FILE.
        key_file = None
        if self.db_path != DB_FILE:
            key_file = self.db_path.parent / ".key"

        return get_fernet(key_path=key_file)

# --- Legacy Functional API (Compatibility Layer) ---

def get_secret(service: str, item: str, fail: bool = False, db_path: Path | str | None = None) -> str | None:
    return DworshakSecret(db_path).get(service, item, fail=fail)

def store_secret(service: str, item: str, secret: str, db_path: Path | str | None = None):
    return DworshakSecret(db_path).set(service, item, secret)

def list_credentials(db_path: Path | str | None = None) -> List[tuple[str, str]]:
    return DworshakSecret(db_path).list()

def remove_secret(service: str, item: str, db_path: Path | str | None = None) -> bool:
    return DworshakSecret(db_path).remove(service, item)

## DEAD CODE
'''

def store_secret(
    service: str, 
    item: str, 
    secret: str,
    fernet=None
):
    """Encrypts and stores a single secret string to the vault"""
    from .security import get_fernet
    _early_exit_no_db()

    payload = secret.encode()
    f = fernet or get_fernet()
    encrypted_secret = f.encrypt(payload)

    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT OR REPLACE INTO credentials (service, item, encrypted_secret) VALUES (?, ?, ?)",
        (service, item, encrypted_secret)
    )
    conn.commit()
    conn.close()

def get_secret(
        service: str, 
        item: str,
        fail: bool = False,
        ) -> str | None:
    """
    Returns decrypted secret for service/item.

    Args:
        service: The service name.
        item: The credential key.
        fail: If True, raise KeyError when secret is missing.
              If False, return None.

    Returns:
        Decrypted string if found, else None (unless fail=True)
    """

    # Ensure vault exists before querying
    _early_exit_no_db()
    from .security import get_fernet
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute(
        "SELECT encrypted_secret FROM credentials WHERE service=? AND item=?",
        (service, item)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        if fail:
            raise KeyError(f"No credential found for {service}/{item}")
        return None
    fernet = get_fernet()
    decrypted = fernet.decrypt(row[0])
    return decrypted.decode()

def remove_secret(service: str, item: str) -> bool:
    """
    Remove a secret from the vault.

    Args:
        service: The service name.
        item: The credential key.

    Returns:
        True if a row was deleted, False if nothing was found.
    """
    _early_exit_no_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute(
        "DELETE FROM credentials WHERE service=? AND item=?",
        (service, item)
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0
    
def list_credentials() -> List[tuple[str, str]]:
    _early_exit_no_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute("SELECT service, item FROM credentials")
    rows = cursor.fetchall()
    conn.close()
    return rows

def _early_exit_no_db(fail: bool = False) -> bool:
    status = check_vault()
    
    if not status.is_valid:
        if fail:
            raise KeyError(f"Vault Issue: {status.message}")
            
        # Use health_code here to match the NamedTuple definition
        if status.health_code in (VaultCode.DIR_MISSING, VaultCode.DB_MISSING):
            initialize_vault()
        else:
            # Permission/Key issues shouldn't be auto-initialized
            print(f"Warning: {status.message}")
        return True
    return False


'''