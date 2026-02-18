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
from dworshak_secret import DworshakSecret, initialize_vault, list_credentials
from dworshak_prompt import DworshakObtain

# Initialize the vault (create key and DB if missing)
initialize_vault()

# Store and retrieve credentials by prompting the user on their local machine
username = DworshakObtain.secret("rjn_api", "username")
secret = DworshakObtain.secret("rjn_api", "password")

# ---

# Alternatively, store secrets with a script ....
## (NOT recommended to keep in your codebase or in system history)
DworshakSecret.get("rjn_api", "username", "davey.davidson")
DworshakSecret.get("rjn_api", "password", "s3cr3t")

## ...and then retrieve credentials in your codebase.
username = DworshakSecret.get("rjn_api", "username")
password = DworshakSecret.get("rjn_api", "password")

# ---

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

`uv venv --system-site-packages` is a modern,faster alternative to `python -m venv .venv --system-site-packages`.
Because **uv** manages the build-time dependencies (**setuptools-rust** and **cffi**) in an isolated environment and coordinates the hand-off to the Rust compiler more robustly than **pip**, it is the recommended way to install **cryptography** from source on Termux.


#### B. Allow cryptography to build from source (uv is better at this compared to using pip)

```zsh
pkg install rust binutils
uv sync --extra crypto # standard for any environment.
```

---

## Why Dworshak over keyring?

Keyring is the go-to for desktop Python apps thanks to native OS backends, but it breaks on Termux because there's no keyring daemon or secure fallback, leaving you with insecure plaintext or install headaches. 
Dworshak avoids that entirely with a portable, self-contained Fernet-encrypted SQLite vault that works the same on Linux, macOS, Windows, and Termux on Android tablets. 
You get reliable programmatic access via `dworshak_secret.DworshakSecret.get()` (or `dworshak_prompt.DworshakObtain.secret()`). 
The Dworshak ecosystem is field-ready for real scripting workflows like API pipelines and skip-the-playstore localhost webapps. 
When keyring isn't viable, Dworshak just works.

---

## Sister Projects in the Dworshak Ecosystem

* **CLI/Orchestrator:** [dworshak](https://github.com/City-of-Memphis-Wastewater/dworshak)
* **Interactive UI:** [dworshak-prompt](https://github.com/City-of-Memphis-Wastewater/dworshak-prompt)
* **Secrets Storage:** [dworshak-secret](https://github.com/City-of-Memphis-Wastewater/dworshak-secret)
* **Plaintext Pathed Configs:** [dworshak-config](https://github.com/City-of-Memphis-Wastewater/dworshak-config)
* **Classic .env Injection:** [dworshak-env](https://github.com/City-of-Memphis-Wastewater/dworshak-env)

```python
pipx install dworshak
pip install dworshak-secret
pip install dworshak-config
pip install dworshak-env
pip install dworshak-prompt
