[1mdiff --git a/src/dworshak_secret/crypto/fernet.py b/src/dworshak_secret/crypto/fernet.py[m
[1mindex b92fec6..98064b5 100644[m
[1m--- a/src/dworshak_secret/crypto/fernet.py[m
[1m+++ b/src/dworshak_secret/crypto/fernet.py[m
[36m@@ -2,12 +2,12 @@[m
 from __future__ import annotations[m
 from cryptography.fernet import Fernet[m
 from .base import CryptoBackend[m
[31m-from ..security import (get_fernet, get_fernet_from_key_path, get_key_str_from_key_path, get_resolved_key_path)[m
[31m-[m
[32m+[m[32mfrom ..security import (get_fernet, get_key_str_from_key_path)[m
[32m+[m[32mfrom ..paths import get_key_path_for_db[m
 [m
 class FernetBackend(CryptoBackend):[m
     def __init__(self, db_path, key_path=None):[m
[31m-        final_key_path = get_resolved_key_path(db_path=db_path, key_path=key_path)[m
[32m+[m[32m        final_key_path = get_key_path_for_db(db_path=db_path, key_path=key_path)[m
         key_str = get_key_str_from_key_path(key_path=final_key_path)[m
         self.fernet = get_fernet(key_str=key_str)[m
         [m
[1mdiff --git a/src/dworshak_secret/paths.py b/src/dworshak_secret/paths.py[m
[1mindex b9ae60b..c28b321 100644[m
[1m--- a/src/dworshak_secret/paths.py[m
[1m+++ b/src/dworshak_secret/paths.py[m
[36m@@ -6,6 +6,8 @@[m [mimport datetime[m
 import os[m
 import stat[m
 [m
[32m+[m[32mfrom .errors import MissingKeyError[m
[32m+[m
 APP_DIR = Path.home() / ".dworshak"[m
 DB_FILE = APP_DIR / "vault.db"[m
 KEY_FILE = APP_DIR / ".key"[m
[36m@@ -106,7 +108,7 @@[m [mdef get_key_path_for_db([m
 [m
     # 1. Ensure Path type[m
     if key_path:[m
[31m-        return Path(key_path).expanduser().resolve()[m
[32m+[m[32m        final_key_path = Path(key_path).expanduser().resolve()[m
     # 2. Registry lookup[m
     registered = get_registered_key(db_p)[m
     if registered:[m
[36m@@ -116,10 +118,19 @@[m [mdef get_key_path_for_db([m
         if not registered.is_absolute():[m
             registered = db_p.parent / registered[m
 [m
[31m-        return registered[m
[32m+[m[32m        final_key_path = registered[m
 [m
     # 3. Default fallback[m
     if db_p == DB_FILE:[m
[31m-        return KEY_FILE[m
[32m+[m[32m        final_key_path = KEY_FILE[m
[32m+[m
[32m+[m[32m    final_key_path = db_p.parent / ".key"[m
 [m
[31m-    return db_p.parent / ".key"[m
[32m+[m[32m    if not final_key_path.exists():[m
[32m+[m[32m        raise MissingKeyError([m
[32m+[m[32m            f"Encryption key not found for vault: {db_path}",[m
[32m+[m[32m            db_path=db_path,[m
[32m+[m[32m            key_path=final_key_path,[m
[32m+[m[32m        )[m
[32m+[m[41m    [m
[32m+[m[32m    return final_key_path[m
[1mdiff --git a/src/dworshak_secret/security.py b/src/dworshak_secret/security.py[m
[1mindex b18b85f..b2872d1 100644[m
[1m--- a/src/dworshak_secret/security.py[m
[1m+++ b/src/dworshak_secret/security.py[m
[36m@@ -2,9 +2,7 @@[m
 from __future__ import annotations[m
 from pathlib import Path[m
 [m
[31m-from .paths import DB_FILE, ensure_secure_permissions, get_key_path_for_db[m
[31m-from .registry import get_registered_key, register_vault_key[m
[31m-from .errors import MissingKeyError[m
[32m+[m[32mfrom .paths import get_key_path_for_db[m
 [m
 def get_fernet_from_key_path([m
     db_path: Path | str | None = None, [m
[36m@@ -21,44 +19,16 @@[m [mdef get_fernet_from_key_path([m
     from cryptography.fernet import Fernet[m
 [m
     # Resolve which key file to use[m
[31m-    db_path = Path(db_path) if db_path else DB_FILE[m
 [m
     final_key_path = get_key_path_for_db(db_path, key_path)[m
[31m-    [m
[31m-    if not final_key_path.exists():[m
[31m-        raise MissingKeyError([m
[31m-            f"Encryption key not found for vault: {db_path}",[m
[31m-            db_path=db_path,[m
[31m-            key_path=final_key_path,[m
[31m-        )[m
 [m
     try:[m
[31m-        key_str = final_key_path.read_bytes()[m
[32m+[m[32m        key_str = get_key_str_from_key_path(final_key_path)[m
         return get_fernet(key_str)[m
     except Exception:[m
         return None[m
[31m-        [m
[31m-def get_resolved_key_path([m
[31m-    db_path: Path | str | None = None, [m
[31m-    key_path: Path | str | None = None[m
[31m-    )->str:[m
[31m-    """[m
[31m-    Returns a Fernet instance using the master key.[m
[31m-    Generates key if missing.[m
[31m-    """[m
[31m-    # Resolve which key file to use[m
[31m-    db_path = Path(db_path) if db_path else DB_FILE[m
[31m-[m
[31m-    final_key_path = get_key_path_for_db(db_path, key_path)[m
     [m
[31m-    if not final_key_path.exists():[m
[31m-        raise MissingKeyError([m
[31m-            f"Encryption key not found for vault: {db_path}",[m
[31m-            db_path=db_path,[m
[31m-            key_path=final_key_path,[m
[31m-        )[m
[31m-    #key_str = final_key_path.read_bytes()[m
[31m-    return final_key_path[m
[32m+[m
 [m
 def get_key_str_from_key_path([m
     key_path: Path | str | None = None[m
