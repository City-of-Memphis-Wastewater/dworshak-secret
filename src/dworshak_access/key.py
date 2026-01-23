# key.py
from .paths import KEY_FILE

def get_key():
    key_text = KEY_FILE.read_text().strip()
    