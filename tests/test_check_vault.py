from __future__ import annotations
from pathlib import Path
from dworshak_secret.vault import check_vault

def test_check_vault_reports_missing_dir(tmp_path):
    fake_db = tmp_path / "non_existent_vault.db"

    status = check_vault(db_path=fake_db)

    assert status.is_valid is False
    assert "missing" in status.message.lower()
