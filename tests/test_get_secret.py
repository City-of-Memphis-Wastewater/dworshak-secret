from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock, mock_open
from dworshak_access.vault import get_secret

@patch("dworshak_access.vault.Fernet")
@patch("sqlite3.connect")
@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.read_bytes", return_value=b"fake-key-bytes")
def test_get_secret_logic(mock_read, mock_exists, mock_connect, mock_fernet):
    # 1. Setup the Mock Database Response
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Simulate the DB returning an encrypted blob
    mock_cursor.fetchone.return_value = (b"encrypted-blob",)
    mock_conn.execute.return_value = mock_cursor
    mock_connect.return_value.__enter__.return_value = mock_conn

    # 2. Setup the Mock Decryption
    mock_fernet_instance = mock_fernet.return_value
    mock_fernet_instance.decrypt.return_value = b"decrypted-password"

    # 3. Execution
    result = get_secret("service", "item")

    # 4. Assertion
    assert result == "decrypted-password"
