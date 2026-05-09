from dworshak_secret.core import DworshakSecret

def test_set_get_roundtrip(tmp_path):
    db = tmp_path / "vault.db"
    key = tmp_path / "key.key"

    mgr = DworshakSecret(db_path=db, key_path=key)
    mgr.initialize_vault()

    mgr.set("github", "token", "secret123")
    value = mgr.get("github", "token")

    assert value == "secret123"
