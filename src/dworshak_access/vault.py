# src/dowrshak_access/vault.py
from __future__ import annotations
import sqlite3
import os
import stat
from pathlib import Path
from typing import NamedTuple, List
from enum import IntEnum
import json
import datetime
import shutil


from .paths import DB_FILE, APP_DIR, get_default_export_path
from .security import get_fernet

CURRENT_TOOL_SCHEMA_VERSION = 2  # Increment this when table structure changes

class VaultStatus(NamedTuple):
    is_valid: bool
    message: str
    root_path: Path
    rw_code: int | None
    health_code: int
    db_version: int

class VaultCode(IntEnum):
    DIR_MISSING = 0
    DB_MISSING = 1
    KEY_MISSING = 2
    HEALTHY_WITH_RW_WARNINGS = 3
    HEALTHY = 4

def initialize_vault() -> VaultStatus:
    """Create vault DB with encrypted_secret column."""
    existing_version = None
    APP_DIR.mkdir(parents=True, exist_ok=True)
    get_fernet() 
    
    conn = sqlite3.connect(DB_FILE)
    try:
        existing_version = conn.execute("PRAGMA user_version").fetchone()[0]
        if existing_version == 0:
            # INITIAL BUILD (Same as your previous logic)
            _create_base_schema(conn)
        
        elif existing_version < CURRENT_TOOL_SCHEMA_VERSION:
            print(f"Your DB_FILE ({DB_FILE}) has a version mismatch with your version of the Dworshak CLI.")
            print(f"Vault database schema version = {existing_version}")
            print(f"CLI database schema version = {CURRENT_TOOL_SCHEMA_VERSION}")
            _dont_run_migrations(existing_version)
            # ACTUAL HEALING
            # #_run_migrations(conn, existing_version)
            
        conn.execute(f"PRAGMA user_version = {CURRENT_TOOL_SCHEMA_VERSION}")
        conn.commit()

    finally:
        conn.close()
            
    return check_vault()

def _dont_run_migrations():
    print(f"This version of Dworshak CLI does not provide auto-migration of db-healing.")

def _run_migrations(conn: sqlite3.Connection, from_version: int):
    """
    Sequentially applies all migrations from current version up to 
    CURRENT_TOOL_SCHEMA_VERSION.

    status: psuedo-code.
    """
    
    def _migrate_to_v1(conn):
        _create_base_schema(conn)

    def _migrate_to_v2(conn):
        # Example: Column rename via Temp Table Pattern
        conn.execute("CREATE TABLE encrypted_secret (...)")
        conn.execute("INSERT INTO encrypted_secret SELECT ... FROM secret")
        conn.execute("ALTER TABLE encrypted_secret RENAME TO secret")
        conn.execute("DROP TABLE encrypted_secret")

    def _migrate_to_v3(conn):
        # Future expansion
        pass

    # Map of (target_version): migration_function
    MIGRATIONS = {
        1: _migrate_to_v1,
        2: _migrate_to_v2,
        3: _migrate_to_v3,
    }

    # Run every migration that is newer than the file's current version
    for version in sorted(MIGRATIONS.keys()):
        if version > from_version and version <= CURRENT_TOOL_SCHEMA_VERSION:
            print(f"Heal: Migrating vault to version {version}...")
            MIGRATIONS[version](conn)

def _create_base_schema(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            service TEXT NOT NULL,
            item TEXT NOT NULL,
            encrypted_secret BLOB NOT NULL,
            PRIMARY KEY(service, item)
        )
    """)

def check_vault() -> VaultStatus:
    if not APP_DIR.exists():
        return VaultStatus(False, "Vault directory missing", APP_DIR, _get_rw_mode(None),VaultCode.DIR_MISSING, CURRENT_TOOL_SCHEMA_VERSION)
    if not DB_FILE.exists():
        return VaultStatus(False, "Vault DB missing", APP_DIR, _get_rw_mode(None), VaultCode.DB_MISSING, CURRENT_TOOL_SCHEMA_VERSION)
    if not get_fernet():
        return VaultStatus(False, "Encryption key missing", APP_DIR, _get_rw_mode(DB_FILE), VaultCode.KEY_MISSING, CURRENT_TOOL_SCHEMA_VERSION)
    
    # Section to check for 0o600 permissions of KEY_FILE and DB_FILE
    warnings = []

    if os.name != "nt":
        if not _is_600(DB_FILE):
            warnings.append("vault.db permissions are not 600")

        from .paths import KEY_FILE
        if not _is_600(KEY_FILE):
            warnings.append(".key permissions are not 600")

    if warnings:
        return VaultStatus(
            True,
            "Vault healthy (warnings: " + "; ".join(warnings) + ")",
            APP_DIR,
            _get_rw_mode(DB_FILE),
            VaultCode.HEALTHY_WITH_RW_WARNINGS,
            CURRENT_TOOL_SCHEMA_VERSION
        )

    return VaultStatus(True, "Vault healthy", APP_DIR, _get_rw_mode(DB_FILE), VaultCode.HEALTHY, CURRENT_TOOL_SCHEMA_VERSION)

def store_secret(service: str, item: str, secret: str):
    """Encrypts and stores a single secret string to the vault"""
    _early_exit_no_db()

    payload = secret.encode()
    fernet = get_fernet()
    encrypted_secret = fernet.encrypt(payload)

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


def _get_rw_mode(path: Path | None = None) -> int | None: 
    if path is None:
        return None
    try:
        # stat.S_IMODE returns an int
        return stat.S_IMODE(path.stat().st_mode)
    except Exception as e:
        # Don't print inside a low-level helper if it can be avoided
        # but for debugging it's fine.
        return None

def _is_600(path: Path) -> bool:
    try:
        mode = _get_rw_mode(path)
        return mode == 0o600 # <-- notice that this is not a string. it is a hexidecimal integer.
    except Exception:
        return False


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

def export_vault(output_path: Path | str | None = None, decrypt: bool = False) -> str | None:
    """Pure Python schema-agnostic export. No external dependencies."""
    if output_path is None:
        output_path = get_default_export_path()
    output_path = Path(output_path)
    if not DB_FILE.exists():
        return False

    status = check_vault()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row 
    try:

        table_data = _fill_db_dump_decrypted(conn) if decrypt else _fill_db_dump_encrypted(conn)

        # 2. Build the full package with Metadata
        export_package = {
            "metadata": {
                "export_time": datetime.datetime.now(datetime.UTC).isoformat(),
                "decrypted": decrypt,
                "vault_schema_version": status.db_version,  # The actual DB PRAGMA version
                "vault_health_message": status.message,
                "vault_health_code": status.health_code,
                "dworshak_tool_schema_version": CURRENT_TOOL_SCHEMA_VERSION, # The CLI version
                
            },
            "tables": table_data
        }
        
        with open(output_path, "w") as f:
            json.dump(export_package, f, indent=4)

        # RESTRICT ACCESS IMMEDIATELY
        if os.name != "nt":
            output_path.chmod(0o600)

        return str(output_path)
    except Exception as e:
        print(f"Export failed: {e}")
        return None
    finally:
        conn.close()

def _fill_db_dump_encrypted(conn: sqlite3.Connection)->dict:
    # Get all table names first to be truly agnostic
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    db_dump = {}

    for table in tables:
        t_name = table['name']

        cursor = conn.execute(f"SELECT * FROM {t_name}")
        # Convert rows to dicts; convert bytes to hex strings for JSON compatibility
        db_dump[t_name] = [
            {k: (v.hex() if isinstance(v, bytes) else v) for k, v in dict(row).items()}
            for row in cursor.fetchall()
        ]
    return db_dump


def _fill_db_dump_decrypted(conn: sqlite3.Connection) -> dict:
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    db_dump = {}
    error_count = 0

    for table in tables:
        t_name = table['name']
        cursor = conn.execute(f"SELECT * FROM {t_name}")
        rows = [dict(row) for row in cursor.fetchall()]
        
        decrypted_rows = []
        for row in rows:
            # 1. Handle Secret Decryption
            if "service" in row and "item" in row and "encrypted_secret" in row:
                try:
                    # Overwrite the binary data with the decrypted string
                    # We keep the name 'encrypted_secret' so the schema stays static
                    row["encrypted_secret"] = get_secret(row["service"], row["item"])
                except Exception as e:
                    # Log the specific error to stderr once or twice
                    if error_count < 1:
                        print(f"Decryption error encountered: {e}")
                    error_count += 1
                    row["encrypted_secret"] = f"DECRYPTION_FAILED"

            # 2. General Hex Handling (The "Don't Crash JSON" Guard)
            # Loop through all remaining keys to catch any other BLOBs
            for k, v in row.items():
                if isinstance(v, bytes):
                    row[k] = v.hex()
            
            decrypted_rows.append(row)
            
        db_dump[t_name] = decrypted_rows
    if error_count > 0:
        print(f"Warning: {error_count} entries could not be decrypted (likely bad key).")

    return db_dump


def import_records(json_path: Path | str, overwrite: bool = False):
    """
    Imports/merges credential records from a JSON export into the local vault.
    
    If 'overwrite' is True, existing local records with matching service/item 
    keys.
    """
    json_path = Path(json_path)
    with open(json_path, "r") as f:
        data = json.load(f)

    if not _validate_import_meta(data.get("metadata", {})):
        return

    creds = data.get("tables", {}).get("credentials", [])
    overlap = _get_overlap(creds)
    # Backup the DB before a destructive overwrite is allowed to proceeed
    if overlap and overwrite:
        _trigger_safety_backup()


    # 2. Processing
    creds = data.get("tables", {}).get("credentials", [])
    stats = {"added": 0, "updated": 0, "skipped": 0}


    for row in creds:
        service, item = row.get("service"), row.get("item")
        secret = row.get("encrypted_secret") # This is plaintext in decrypted exports

        if not (service and item and secret):
            continue

        existing = get_secret(service, item)
        
        if existing is None:
            store_secret(service, item, secret)
            stats["added"] += 1
        elif overwrite:
            # The "Power User" path
            store_secret(service, item, secret)
            stats["updated"] += 1
        else:
            # The "Safety" path
            #print(f"Skipping entry, service = {service}, item = {item}. There is an existing entry. overwrite = False")
            stats["skipped"] += 1

    # print(f"Finished: {stats['added']} new, {stats['updated']} updated, {stats['skipped']} skipped.")
    return stats
    

def _validate_import_meta(meta: dict) -> bool:
    """Ensure the JSON is a valid decrypted export."""
    if not meta.get("decrypted"):
        print("Import Rejected: JSON must be a decrypted export.")
        return False
    return True

def _get_overlap(incoming_creds: list) -> set[tuple[str, str]]:
    """Compare incoming keys against local DB keys."""
    incoming_keys = {
        (row['service'], row['item']) 
        for row in incoming_creds 
        if 'service' in row and 'item' in row
    }
    existing_keys = set(list_credentials()) # Returns List[tuple[str, str]]
    return incoming_keys.intersection(existing_keys)

def _trigger_safety_backup():
    """Create a timestamped copy of the DB file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_FILE.with_suffix(f".db.bak_{timestamp}")
    shutil.copy2(DB_FILE, backup_path)
    print(f"Safety backup created: {backup_path.name}")
    return backup_path