from __future__ import annotations
from pathlib import Path
from dworshak_secret.core import DworshakSecret

def test_check_vault_reports_missing_dir(tmp_path):
    fake_db = tmp_path / "non_existent_vault.db"
    secret_manager = DworshakSecret(db_path=fake_db)
    status = secret_manager.check_vault()

    assert status.is_valid is False
    assert "missing" in status.message.lower()
