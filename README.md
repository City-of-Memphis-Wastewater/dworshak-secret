`dworshak-secret` is a light-weight library for local credential access. By adding `dworshak-secret` as a dependency to your Python project, you enable your program or script to leverage secure credentials, typically added with the `dworshak-prompt.Obtain().secret()` function or managed directly with the `dworshak` CLI.

All secrets are stored Fernet-encrypted in a SQL database file.
No opaque blobs — every entry is meaningful and decryptable via the library.

### Example

Typical package inclusion. See below for guidance concerning Termux and iSH Alpine.

```zsh
uv add "dworshak-secret[crypto]"
```

```python
from dworshak_secret import DworshakSecret, initialize_vault, list_credentials
from dworshak_prompt import Obtain

# Initialize the vault (create key and DB if missing)
initialize_vault()

# Store and retrieve credentials by prompting the user on their local machine
username = Obtain().secret("rjn_api", "username")
secret = Obtain().secret("rjn_api", "password")

# ---

# Alternatively, store secrets with a script ....
## (NOT recommended to keep in your codebase or in system history)
DworshakSecret().set("rjn_api", "username", "davey.davidson")
DworshakSecret().set("rjn_api", "password", "s3cr3t")

## ...and then retrieve credentials in your codebase.
username = DworshakSecret().get("rjn_api", "username")
password = DworshakSecret().get("rjn_api", "password")

# ---

# List stored items
for service, item in list_credentials():
    print(f"{service}/{item}")
```

Capture stdout environment variables for bash scripting by using the `--emit` flag
```zsh
TESTSET=$(dworshak-secret set "myservice" "myitem" "myvalue" --emit)
echo $TESTSET

TESTGET=$(dworshak-secret get "myservice" "myitem" --emit)
echo $TESTGET
```

It is not recommended to type a secret in console using the `dworshak secret set` command like this.
Ideally, keep your secrets out of console history.
Running `dworshak-secret set "myservice" "myitem"` will prompt the user for input, which will be hidden; this prompting fails when the `dworshak secret set` is wrapped for assignment to an environment variable. 
 
Alternatively, install the `dworshak` CLI and use:
```zsh
TESTOBTAIN=$(dworshak prompt obtain secret "myservice" "myitem" --emit`)
echo $TESTOBTAIN
```
This works because the multiplexer will skip the console input and route the user to the web interface or the GUI.

---

## Include Cryptography Library 

Here we cover using `dworshak-secret` as a dependency in your project.

The central question is how to properly include the `cryptography` package.

On a Termux system, `cryptography` can **(B)** be built from source or **(A)** the precompiled python-cryptography dedicated Termux package can be used.

### Termux Installation

#### A. Use python-cryptography 

This is faster but pollutes your local venv with other system site packages.

```
pkg install python-cryptography
uv venv --system-site-packages
uv add dworshak-secret
```

#### B. Allow cryptography to build from source (uv is better at this compared to using pip)

```zsh
pkg install rust binutils
uv add "dworshak-secret[crypto]"
```

---

### iSH Alpine installation

```
apk add py3-cryptography
uv venv --system-site-packages
uv add dworshak-secret
```
---

## Why Dworshak Over **keyring**?

Keyring is the go-to for desktop Python apps thanks to native OS backends, but it breaks on Termux because there's no keyring daemon or secure fallback, leaving you with insecure plaintext or install headaches. 
Dworshak avoids that entirely with a portable, self-contained Fernet-encrypted SQLite vault that works the same on Linux, macOS, Windows, and Termux on Android tablets. 
You get reliable programmatic access via `dworshak_secret.DworshakSecret().get()` (or `dworshak_prompt.Obtain().secret()`). 
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
```

---

## CLI

`dworshak` is the intended CLI layer, but the `dworshak-secret` CLI can also be used directly.

```
pipx install "dworshak-secret[typer,crypto]"
dworshak-secret helptree
```

<p align="center">
  <img src="https://raw.githubusercontent.com/City-of-Memphis-Wastewater/dworshak-secret/main/assets/dworshak-secret_v1.2.11_helptree.svg" width="100%" alt="Screenshot of the Dworshak CLI helptree">
</p>

`helptree` is utility function for Typer CLIs, imported from the `typer-helptree` library.

- GitHub: https://github.com/City-of-Memphis-Wastewater/typer-helptree
- PyPI: https://pypi.org/project/typer-helptree/

---
