def test_initialize_vault_creates_key_and_db(tmp_path):
    from dworshak_secret.core import DworshakSecret
    
    mgr = DworshakSecret(db_path=tmp_path / "vault.db")
    mgr.initialize_vault()

    assert (tmp_path / "vault.db").exists()
    key_path= mgr.resolve_key_path()
    assert key_path.exists()
    assert key_path.read_bytes() != b""
