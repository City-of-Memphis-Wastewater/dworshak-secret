from __future__ import annotations
import pytest
from unittest.mock import patch, Mock
from dworshak_secret.core import DworshakSecret


@patch("dworshak_secret.security.get_fernet")
def test_get_secret_logic(mock_get_fernet, tmp_path):
    fake_fernet = Mock()
    fake_fernet.encrypt.return_value = b"encrypted-secret"
    fake_fernet.decrypt.return_value = b"secret"

    mock_get_fernet.return_value = fake_fernet

    mgr = DworshakSecret(db_path=tmp_path / "vault.db")

    mgr.set("service", "item", "secret")
    result = mgr.get("service", "item")

    assert result == "secret"
