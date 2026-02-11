**dworshak-secret** is a light-weight library for local credential access. By adding **dworshak-secret** as a dependency to your Python project, you enable your program or script to leverage credentials that have been established using the sister package, the **Dworshak CLI** tool.

## Functions exposed in **dworshak-secret**:
- `initialize_vault() -> VaultResponse` – Create the vault directory, encryption key, and SQLite database. Safe to call multiple times.
- `check_vault() -> VaultStatus` – Check the health of the vault.
- `store_secret(service: str, item: str, plaintext: str)` – Encrypt and store a credential in the vault.
- `get_secret(service: str, item: str) -> str | None` – Retrieve and decrypt a credential.
- `remove_secret(service: str, item: str) -> bool` – Remove a credential from the vault.
- `list_credentials() -> list[tuple[str, str]]` – List all stored service/item pairs.
- `export_vault(output_path: Path | str | None = None) -> str | None` - Export vault to JSON file.

All secrets are stored Fernet-encrypted in the database under the secret column.
No opaque blobs — every entry is meaningful and decryptable via the library.

### Example

```zsh
uv add "dworshak-secret[crypto]"
```

```python
from dworshak_secret import initialize_vault, store_secret, get_secret, list_credentials

# Initialize the vault (create key and DB if missing)
initialize_vault()

# Store credentials
store_secret("rjn_api", "username", "admin")
store_secret("rjn_api", "password", "s3cr3t")

# Retrieve credentials
username = get_secret("rjn_api", "username")
password = get_secret("rjn_api", "password")

# List stored items
for service, item in list_credentials():
    print(f"{service}/{item}")
```

---

## Include Cryptography Library 

(When Building **dworshak-secret** From Source or When Using It A Dependency in Your Project)

The only external Python library used is `cryptography`, for the **Fernet** class.

On a Termux system, cryptography can **(B)** be built from source or **(A)** the precompiled python-cryptography dedicated Termux package can be used.

### Termux Installation

#### A. Use python-cryptography (This is faster but pollutes your local venv with other system site packages.)

```zsh
pkg install python-cryptography
uv venv --system-site-packages
uv sync
```

`uv venv --system-site-packages` is a modern,faster alternative to `python -m venv .venv --system-site-packages`.
Because **uv** manages the build-time dependencies (**setuptools-rust** and **cffi**) in an isolated environment and coordinates the hand-off to the Rust compiler more robustly than **pip**, it is the recommended way to install **cryptography** from source on Termux.


#### B. Allow cryptography to build from source (uv is better at this compared to using pip)

```zsh
pkg install rust binutils
uv sync --extra crypto # standard for any environment.
```

---


# Sister Project: 
CLI: `Dworshak` 

GitHub: https://github.com/City-of-Memphis-Wastewater/dworshak 

PyPI: https://pypi.org/project/dworshak/ 

```
pipx install dworshak
```

---
