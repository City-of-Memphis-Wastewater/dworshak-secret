from __future__ import annotations
import pytest
from unittest.mock import patch, Mock
from dworshak_secret.core import DworshakSecret


@patch("dworshak_secret.crypto.get_fernet")
def test_secret_roundtrip_with_mocked_crypto(mock_get_fernet, tmp_path):
    fake_fernet = Mock()
    fake_fernet.encrypt.return_value = b"encrypted-secret"
    fake_fernet.decrypt.return_value = b"secret"

    mock_get_fernet.return_value = fake_fernet

    mgr = DworshakSecret(db_path=tmp_path / "vault.db")

    mgr.initialize_vault()
    mgr.set("service", "item", "secret")
    result = mgr.get("service", "item")

    assert result == "secret"

class FakeFernet:
    def encrypt(self, data):
        return b"encrypted:" + data

    def decrypt(self, data):
        return data.replace(b"encrypted:", b"")

class FakeCryptoBackend:
    def encrypt(self, data: bytes) -> bytes:
        return b"enc:" + data

    def decrypt(self, data: bytes) -> bytes:
        return data.replace(b"enc:", b"")

def test_get_secret_logic(tmp_path):
    mgr = DworshakSecret(db_path=tmp_path / "vault.db")

    fake = FakeFernet()
    
    mgr.initialize_vault()
    mgr.set("service", "item", "secret", fernet=fake)
    result = mgr.get("service", "item", fernet=fake)

    assert result == "secret"

def test_get_secret_logic_crypto_backend(tmp_path):
    mgr = DworshakSecret(
        db_path=tmp_path / "vault.db",
        crypto_backend=FakeCryptoBackend()
    )
    mgr.initialize_vault()

    mgr.set("service", "item", "secret")
    result = mgr.get("service", "item")

    assert result == "secret"
