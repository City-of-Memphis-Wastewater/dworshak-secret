def test_initialize_vault_creates_key_and_db(tmp_path):
    from dworshak_secret.core import DworshakSecret

    mgr = DworshakSecret(db_path=tmp_path / "vault.db")
    mgr.initialize_vault()

    assert (tmp_path / "vault.db").exists()
    assert (tmp_path / ".key").exists()
