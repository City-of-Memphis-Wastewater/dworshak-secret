from __future__ import annotations
from pathlib import Path
from dworshak_access.vault import check_vault

def test_check_vault_reports_missing_dir(tmp_path):
    """
    If the folder doesn't exist, check_vault should 
    return a valid status object indicating it's missing.
    """
    # Point to a directory we know doesn't exist
    fake_path = tmp_path / "non_existent_vault"
    
    status = check_vault(root=fake_path)
    
    # We don't want a crash/exception; we want a 'False' status
    assert status.is_valid is False
    assert "does not exist" in status.message
    assert status.root_path == fake_path
