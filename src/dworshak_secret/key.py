# src/dworshak_secret/key.py
"""
Helper module focused on Fernet key operations:
- loading the current key
- generating new keys
- orchestrating key rotation (with dry-run support)

"""

from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Tuple, List, Optional

from .paths import get_key_path_for_db

try:
    from cryptography.fernet import Fernet, InvalidToken, MultiFernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

from .paths import KEY_FILE, DB_FILE

MSG_CRYPTO_HELP = (
    "Encryption is not available. Install with crypto extra:\n"
    "  uv add \"dworshak-secret[crypto]\"\n"
    "  or\n"
    "  pip install \"dworshak-secret[crypto]\"\n"
    "On Termux, use \"pkg add python-cryptography\"\n"
    "On iSH alpine, use \"apk add py3-cryptography\"\n"
    "For Termux and iSH, ensure that you include --system-site-packages."
)


def load_current_key(db_path: Path | str | None = None) -> bytes:
    """Resolves and reads the Fernet key based on the DB path."""
    
    target_key_path = get_key_path_for_db(db_path)
    if not target_key_path.exists():
        raise FileNotFoundError(f"Encryption key not found at {target_key_path}")
    return target_key_path.read_bytes()


def generate_new_key() -> bytes:
    """Generate a fresh Fernet-compatible key (32 bytes base64-encoded)."""
    installation_check()
    return Fernet.generate_key()


def rotate_key(
    db_path: Path | str | None = None,
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
    from .vault import (
        check_vault,
        backup_vault,
    )
    from .core import (
        get_secret,
        store_secret,
        list_credentials,
    )
    from .paths import ensure_secure_permissions

    db_path = Path(db_path) if db_path else DB_FILE
    key_path = get_key_path_for_db(db_path)

    installation_check()
    status = check_vault(db_path=db_path)
    if not status.is_valid:
        return False, f"Vault is unhealthy: {status.message}", None

    # ── Backup phase ──
    backup_path: Optional[Path] = None
    if auto_backup:
        backup_path = backup_vault(
            extra_suffix=extra_backup_suffix,
            include_timestamp=True,
        )
        if backup_path is None:
            return False, "Automatic backup failed — rotation aborted", None

    backup_info = f"Backup created at {backup_path}" if backup_path else "No backup performed"

    # ── Prepare keys ──
    try:
        old_key = load_current_key(key_path)
    except FileNotFoundError as exc:
        return False, f"Cannot rotate: {exc}", None

    new_key = generate_new_key()

    # MultiFernet allows decrypting with old key while encrypting with new
    transition_fernet = MultiFernet([Fernet(new_key), Fernet(old_key)])

    # ── Re-encryption phase ──
    credentials = list_credentials()
    if not credentials:
        return True, f"No credentials to rotate. {backup_info}", []

    affected: List[str] = []
    conn = None

    try:
        conn = sqlite3.connect(db_path)
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
                f"Dry run. A true key rotation would re-encrypt {len(affected)} credential(s). {backup_info}",
                affected,
            )

        conn.commit()

        # Atomically replace the key file
        key_path.write_bytes(new_key)
        ensure_secure_permissions(key_path)

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

def rotate_key_dry_run(db_path: Path | str | None = None) -> Tuple[bool, str, Optional[List[str]]]:
    """
    Convenience wrapper — always runs in dry-run mode.
    Checks the key relative to a db path.
    """
    return rotate_key(db_path = db_path, dry_run=True, auto_backup=False)

def installation_check(die = False):
    if not CRYPTO_AVAILABLE:
        if die:
            print(MSG_CRYPTO_HELP)
            import sys
            sys.exit(1)
        return False
    return True

if __name__ == "__main__":
    if not CRYPTO_AVAILABLE:
        print(MSG_CRYPTO_HELP)
    
