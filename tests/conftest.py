# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture(scope="session", autouse=True)
def isolate_key_registry(tmp_path_factory):
    """Redirect the live key registry to a session-isolated temporary file.
    
    This catches all registrations across all test modules automatically,
    without needing to intercept individual function calls.
    """
    from dworshak_secret import registry
    
    # Create a clean tracking file just for this pytest run
    tmp_dir = tmp_path_factory.mktemp("dworshak_test_registry")
    fake_registry_file = tmp_dir / "keys.json"
    
    # Hot-swap the module's file target
    registry.KEY_REGISTRY_FILE = fake_registry_file
    
    yield