**dworshak-access** is a lightweight library. 

## Purpose
Allow a program to leverage credentials that have been established using the Drowshak CLI tool, which is a separate package.

## Functions exposed in **dworshak-access**:
- check_vault() # For troubleshooting automated testing.
- get_credential() # The meat and potatoes.


### Example

```python
from dworshak_access import get_credential

service_name = "MyThirdFavoriteAPI"
item_id_u = "username"
item_id_p = "password"

user = get_credential(service_name,item_id_u)
pass = get_credential(service_name,item_id_p)

# Then use these in your program

```

---

## Cryptography Library

The only external Python library used is crytography, for the Fernet class.

On a Termux system, cryptography can be built from source if the user first installs Rust with `pkg install rust`.
Is `uv sync` better at accomplishing this, due to the rust packagig location? Argue and let me know.
Alteratively, a Termux user can run `pkg install python-crytophy`, then build a fresh venv folder using the --system-site-packages flag to include the now system-wide crytography package. Or maybe you don't need a venv at all. Hm.
