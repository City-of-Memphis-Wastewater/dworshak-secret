# Changelog

All notable changes to this project will be documented in this file.

The format is (read: strives to be) based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

