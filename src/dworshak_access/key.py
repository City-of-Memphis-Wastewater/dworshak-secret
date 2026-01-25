# key.py
from cryptography.fernet import Fernet, InvalidToken
from .paths import KEY_FILE

def get_key():
    key_text = KEY_FILE.read_text().strip()
    

def rotate_key(yes: bool = False, dry_run: bool = False) -> bool:
    """High-level key rotation orchestrator."""
    from .vault import check_vault
    if not check_vault().is_valid:
        print("Cannot rotate: vault unhealthy.")
        return False

    if not yes and not _confirm_rotation():
        print("Rotation cancelled.")
        return False

    print("Starting key rotation...")

    backup_path = backup_vault(suffix="pre-key-rotation")
    if not backup_path:
        print("Backup failed → aborting rotation.")
        return False

    try:
        _perform_rotation(dry_run=dry_run)
        print("Key rotation complete." if not dry_run else "[DRY RUN] Complete – no changes.")
        return True
    except Exception as e:
        print(f"Rotation failed: {e}")
        print("Check backup if needed.")
        return False


def _confirm_rotation() -> bool:
    msg = (
        "This will generate a NEW encryption key and re-encrypt ALL secrets.\n"
        "Old key will be permanently replaced.\n"
        "Proceed? [y/N] "
    )
    return input(msg).strip().lower().startswith('y')


def _perform_rotation(dry_run: bool = False):
    """Core rotation logic – assumes backup already done."""
    old_fernet = get_fernet()
    new_key = Fernet.generate_key()
    new_fernet = Fernet(new_key)

    conn = sqlite3.connect(DB_FILE)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT service, item, encrypted_secret FROM credentials"
        ).fetchall()

        if not rows:
            print("No secrets to rotate.")
            return

        print(f"Rotating {len(rows)} secret(s)...")

        for row in rows:
            service, item = row["service"], row["item"]
            try:
                plaintext = old_fernet.decrypt(row["encrypted_secret"]).decode()
            except InvalidToken:
                raise RuntimeError(f"Decryption failed for {service}/{item} – data may be corrupted.")

            if dry_run:
                #print(f"[DRY] Would re-encrypt {service}/{item}")
                continue

            new_enc = new_fernet.encrypt(plaintext.encode())
            conn.execute(
                "UPDATE credentials SET encrypted_secret = ? WHERE service = ? AND item = ?",
                (new_enc, service, item)
            )

        if not dry_run:
            conn.commit()
            KEY_FILE.write_bytes(new_key)
            secure_chmod(KEY_FILE)
            print(f"New key written to {KEY_FILE}")
        # else: rollback not needed in dry_run

    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()
