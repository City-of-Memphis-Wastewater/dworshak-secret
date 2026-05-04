from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional, Any
import sys

from .paths import DB_FILE
from .vault import initialize_vault, ensure_vault, check_vault
from .crypto.fernet import FernetBackend


class DworshakSecret:
    """
    Stateless client wrapper over a persistent vault.

    Lifecycle is external:
        - initialize_vault() → creates vault + key
        - ensure_vault() → validates only
        - get/set/remove → require existing vault
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        key_path: Path | str | None = None,
        crypto_backend: Any | None = None,
    ):
        self.db_path = Path(db_path) if db_path else DB_FILE
        self._key_path_override = Path(key_path) if key_path else None

        # IMPORTANT: do NOT initialize crypto here
        self._crypto_backend = crypto_backend

    # ----------------------------
    # Path resolution
    # ----------------------------

    def resolve_key_path(self) -> Path:
        from .paths import get_key_path_for_db
        key_path = get_key_path_for_db(self.db_path, self._key_path_override)
        print(f"key_path = {key_path}",file=sys.stderr)
        return 

    # ----------------------------
    # Lazy crypto backend
    # ----------------------------

    @property
    def crypto_backend(self):
        if self._crypto_backend:
            return self._crypto_backend

        from .crypto.fernet import FernetBackend
        self._crypto_backend = FernetBackend(
            db_path=self.db_path,
            key_path=self.resolve_key_path(),
        )
        return self._crypto_backend

    # ----------------------------
    # Vault lifecycle wrappers
    # ----------------------------

    def initialize_vault(self, **kwargs):
        return initialize_vault(
            db_path=self.db_path,
            key_path=self.resolve_key_path(),
            **kwargs
        )

    def ensure_vault(self):
        return ensure_vault(
            db_path=self.db_path,
            key_path=self.resolve_key_path(),
        )

    def check_vault(self, **kwargs):
        return check_vault(
            db_path=self.db_path,
            key_path=self.resolve_key_path(),
            **kwargs
        )

    # ----------------------------
    # Core operations
    # ----------------------------

    def get(self, service: str, item: str, fail: bool = False):
        self.ensure_vault()

        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT encrypted_secret FROM credentials WHERE service=? AND item=?",
                (service, item)
            ).fetchone()
        finally:
            conn.close()

        if not row:
            if fail:
                raise KeyError(f"Missing {service}/{item}")
            return None

        return self.crypto_backend.decrypt(row[0]).decode()

    def set(self, service: str, item: str, value: str, overwrite: bool = True):
        self.ensure_vault()

        backend = self.crypto_backend
        encrypted = backend.encrypt(value.encode())

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO credentials
                (service, item, encrypted_secret)
                VALUES (?, ?, ?)
                """,
                (service, item, encrypted),
            )
            conn.commit()
        finally:
            conn.close()

    def remove(self, service: str, item: str) -> bool:
        self.ensure_vault()

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "DELETE FROM credentials WHERE service=? AND item=?",
                (service, item),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def list_contents(self):
        self.ensure_vault()

        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(
                "SELECT service, item FROM credentials"
            ).fetchall()
        finally:
            conn.close()
