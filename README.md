**dworshak-access** is a lightweight library. 

## Purpose
Allow a program to leverage credentials that have been established using the Drowshak CLI tool, which is a separate package.

## Functions exposed in **dworshak-access**:
- check_vault() # For troubleshooting automated testing.
- get_secret() # The meat and potatoes.


### Example

```python
from dworshak_access import get_secret

service_name = "MyThirdFavoriteAPI"
item_id_u = "username"
item_id_p = "password"

un = get_secret(service_name,item_id_u)
pw = get_secret(service_name,item_id_p)

# Then use these in your program

```

---

## Cryptography Library (When Building **dworshak-access** From Source or When Using It A Dependency in Your Project)

The only external Python library used is `crytography`, for the **Fernet** class.

On a Termux system, cryptography can **(A)** be built from source or **(B)** the precompiled python-crytography dedicated Termux package can be used.

#### A. Allow cryptography to build from source (uv is better at this compared to using pip)

```zsh
pkg install rust binutils
uv sync
```

#### B. Use python-cryptography (This is faster but pollutes your local venv with other system site packages.)

```zsh
pkg install python-cryptography
uv venv --system-site-packages
uv sync
```

`uv venv --system-site-packages` is a modern,faster alternative to `python -m venv .venv --system-site-packages`.
Because **uv** manages the build-time dependencies (**setuptools-rust** and **cffi**) in an isolated environment and coordinates the hand-off to the Rust compiler more robustly than **pip**, it is the recommended way to install **cryptography** from source on Termux.

---
