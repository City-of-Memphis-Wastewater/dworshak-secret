# src/dworshak_access/key.py
"""
Helper module focused on Fernet key operations:
- loading the current key
- generating new keys
- orchestrating key rotation (with dry-run support)

Does NOT contain interactive prompts — those belong in the CLI layer.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Tuple, List, Optional

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from .paths import KEY_FILE, DB_FILE
from .vault import (
    check_vault,
    backup_vault,
    get_fernet,
    secure_chmod,
    get_secret,
    store_secret,
    list_credentials,
)

def get_key():
    key_text = KEY_FILE.read_text().strip()

def load_current_key() -> bytes:
    """Read the Fernet key from disk. Raises FileNotFoundError if missing."""
    if not KEY_FILE.exists():
        raise FileNotFoundError(f"Encryption key not found at {KEY_FILE}")
    return KEY_FILE.read_bytes()


def generate_new_key() -> bytes:
    """Generate a fresh Fernet-compatible key (32 bytes base64-encoded)."""
    return Fernet.generate_key()


def rotate_key(
    dry_run: bool = False,
    auto_backup: bool = True,
    extra_backup_suffix: str = "pre-key-rotation",
) -> Tuple[bool, str, Optional[List[str]]]:
    """
    Perform (or simulate) a full key rotation.

    Steps:
    1. Check vault health
    2. (Optional) Create backup
    3. Generate new key
    4. Use MultiFernet to decrypt with old key, encrypt with new
    5. Re-write every credential (only if not dry_run)
    6. Replace key file on disk (only if not dry_run)

    Returns:
        (success: bool, message: str, affected_credentials: list[str] | None)
    """
    status = check_vault()
    if not status.is_valid:
        return False, f"Vault is unhealthy: {status.message}", None

    # ── Backup phase ───────────────────────────────────────────────────────────────
    backup_path: Optional[Path] = None
    if auto_backup:
        backup_path = backup_vault(
            extra_suffix=extra_backup_suffix,
            include_timestamp=True,
        )
        if backup_path is None:
            return False, "Automatic backup failed — rotation aborted", None

    backup_info = f"Backup created at {backup_path}" if backup_path else "No backup performed"

    # ── Prepare keys ───────────────────────────────────────────────────────────────
    try:
        old_key = load_current_key()
    except FileNotFoundError as exc:
        return False, f"Cannot rotate: {exc}", None

    new_key = generate_new_key()

    # MultiFernet allows decrypting with old key while encrypting with new
    transition_fernet = MultiFernet([Fernet(new_key), Fernet(old_key)])

    # ── Re-encryption phase ────────────────────────────────────────────────────────
    credentials = list_credentials()
    if not credentials:
        return True, f"No credentials to rotate. {backup_info}", []

    affected: List[str] = []
    conn = None

    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row

        for service, item in credentials:
            plaintext = get_secret(service, item)
            if plaintext is None:
                return False, f"Failed to read secret {service}/{item}", affected

            affected.append(f"{service}/{item}")

            if dry_run:
                continue

            # Re-store using transition fernet (encrypts with primary = new key)
            store_secret(service, item, plaintext, fernet=transition_fernet)

        if dry_run:
            return (
                True,
                f"Dry run: would re-encrypt {len(affected)} credential(s). {backup_info}",
                affected,
            )

        conn.commit()

        # Atomically replace the key file
        KEY_FILE.write_bytes(new_key)
        secure_chmod(KEY_FILE)

        return (
            True,
            f"Successfully rotated key and re-encrypted {len(affected)} credential(s). {backup_info}",
            affected,
        )

    except InvalidToken as exc:
        return False, f"Decryption failure during rotation: {exc}", affected
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Rotation failed: {exc}", affected
    finally:
        if conn:
            conn.close()


def rotate_key_dry_run() -> Tuple[bool, str, Optional[List[str]]]:
    """Convenience wrapper — always runs in dry-run mode."""
    return rotate_key(dry_run=True, auto_backup=False)
