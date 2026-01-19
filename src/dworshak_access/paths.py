# src/dowrshak_access/paths.py
from __future__ import annotations
from pathlib import Path

APP_DIR = Path.home() / ".dworshak"
DB_FILE = APP_DIR / "vault.db"
KEY_FILE = APP_DIR / ".key"
CONFIG_FILE = APP_DIR / "config.json"
