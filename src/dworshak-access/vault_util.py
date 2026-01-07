import sqlite3
from pathlib import Path
from cryptography.fernet import Fernet

def get_secret(service: str, item: str):
    root = Path.home() / ".dworshak"
    
    # 1. Get the Key
    key = (root / ".key").read_bytes()
    f = Fernet(key)
    
    # 2. Query the DB
    with sqlite3.connect(root / "vault.db") as conn:
        res = conn.execute(
            "SELECT secret FROM credentials WHERE service = ? AND item = ?", 
            (service, item)
        ).fetchone()
    
    # 3. Decrypt
    return f.decrypt(res[0]).decode() if res else None
