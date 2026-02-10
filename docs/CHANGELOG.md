# Changelog
All notable changes to this project will be documented in this file.
The format is (read: strives to be) based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.2.1] - 2026-02-09
### Changed
- **Project Renamed**: Rebranded from `dworshak-access` to `dworshak-secret` to better reflect the "Vault" nature of the library, and to fit nicely within the wider `dworshak` ecosystem, which includes `dworshak-prompt` and `dworshak-config`.
- Updated internal package structure to `dworshak_secret`.

---

## [1.1.1] – 2026-01-26
### Changed:
- Improve installation_check() msg to include information about `--system-site-packages`.
- Bump to 1.1.1! We are live.

### Added:
- "Development Status :: 5 - Production/Stable" 🎉

---

## [0.1.29] – 2026-01-25
### Fixed:
- Removed all required dependencies to instead use optional 'crypto' section.
- Update README 

---

## [0.1.28] – 2026-01-25
### Changed:
- No longer install cryptography by default. Make it an optional dependency.
- Guard against missing dependency with an installation suggestion.

---

## [0.1.26] – 2026-01-24
### Added:
- rotate_key()
- backup_vault()

---

## [0.1.25] – 2026-01-24
### Added:
- Add 'yes' arg to export command to guard decryption.

---

## [0.1.24] – 2026-01-24
### Internal:
- Mysterious non-0o600 permissions seen in health check after new vault initialization.

---

## [0.1.23] – 2026-01-24
### Changed:
- Metadata keys in export.

### Internal:
- Chose not to add suffix to export files differentiating encryption vs decryption.
- Mysterious non-0o600 permissions seen in health check after new vault initialization.

---

## [0.1.22] – 2026-01-23
### Added:
- vault.import_records()
- encryption vs decryption in export handled
- Auto copy db to backup when there is an intersection and when overwrite is true.

---

## [0.1.21] – 2026-01-23
### Changed:
- Most of the functions in vault have been tweaked, to handle mismatch betwen DB schema versioning.
- initialize_vault returns VaultStatus.

### Added:
- vault.export_vault()
- paths.get_default_export_path()

---

## [0.1.20] – 2026-01-19
### Added:
- remove_secret(): will return bool, true is successfully removed, false if nothing found.

---

## [0.1.18] – 2026-01-19
### Changed:
- Store single secret values for each item and service value, rather than pairs of username and password.

---


## [0.1.17] – 2026-01-19
### Changed:
- Ensure and check for 0o600 permissions on vault and .key file

---

## [0.1.16] – 2026-01-19
### Changed:
- Consistent variable naming: encrypted_secret

---

## [0.1.12] – 2026-01-19
### Changed:
- Complete refactor to align with Dworshak CLI


---

## [0.1.11] – 2026-01-08
### Changed:
- uv.lock added to .gitignore, and --locked flag remove from 'uv run --locked --dev pytest' in publish.yml

---

## [0.1.10] – 2026-01-08
### Added:
- ./tests/
- Add ./tests/ to publish.yml
- Add *.pyc and __pycache__/ to .gitignore
- Add .pytest_cache/ and .dworshak/ to .gitignore

### Changed:
- Remove uv.toml from the .gitignore, to allow it to be tracked.

---

## [0.1.9] – 2026-01-08
### Changed:
- Minimum Python version set to 3.9
- Use `from __future__ import annotations` in each .py file to ensure type hinting compatibility down to Python 3.9.

---

## [0.1.8] – 2026-01-08
### Changed:
- Polish top level description, to make clear that dworshak-access is meant to be added as a dependency, and why.

---

## [0.1.7] – 2026-01-08
### Added:
- Add github release .whl upload to package.yml

---

## [0.1.6] – 2026-01-08
### Changed:
- Update README for accuracy regarding uv and pip dependency management.
- Convert dependency installation approaches into codeblocks

### Fixed:
- Typo: python-crypography -> python-cryptography

---

## [0.1.5] – 2026-01-08
### Changed:
- Flesh out the README sections for the Termux options for including cryptopgraphy as a dependency.

### Fixed:
- Typos.
- In README example, do not use 'pass' as a var name; this collides with a Python reserved keyword.

---

## [0.1.4] – 2026-01-08
### Fixed:
- Correct get_credential() -> get_secret() in publish.yml
- Corrent Extra s, dworshak_accesss -> dworshak_access, in __init__.py

---

## [0.1.3] – 2026-01-08
### Fixed:
- In publish.yml, the import statement in the test needs to use the underscored `dworshak_access` rather than the hyphenated `dworshak-access`

---

## [0.1.2] – 2026-01-08
### Added:
- .github/workflows/ci.yml and .github/workflows/publish.yml. Now pushing to PyPI.

---

## [0.1.1] – 2026-01-07
### Changed:
- Change file name of the central file from **vault_util.py** to **vault.py**; Ensure that this is updated in the __init__ import and that no other references are made. 

### Fixed:
- Remove parentheses from the imports in the __init__.py file.
- Fix the underscore in **./src/dworshak-access/** -> **./src/dworshak_access/**.

### Added:
- Add example and library sections to README. Notes concerning uv and termux may be erroneous or too colloquial. Lighten up. At least I wrote them by hand.

---

## [0.1.0] – 2026-01-07
### Initialization
Welcome to the world **dworshak-access**. You will be a light-weight library that users can leverage to easily access locally stored credentials (a la the Dworshak CLI) for other scripts and programs.

