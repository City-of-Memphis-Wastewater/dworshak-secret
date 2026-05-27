"""
Entry point for dworshak-secret. 
Favors the Rich/Typer CLI but falls back to a zero-dependency stdlib version.
"""
TYPERSUCCESS=None
try:
    import typer
    TYPERSUCCESS=True
except (ImportError, ModuleNotFoundError):
    # Fallback to the 'lifeboat' CLI
    #from .cli_stdlib import main as run
    TYPERSUCCESS=FALSE

if TYPERSUCCESS:
    # Attempt to use the feature-rich CLI
    from .cli import app
    def run():
        app()
else:
    import sys
    def run():
        print(
            "Please install this package with the 'typer' extra to utilize the CLI.", 
            file=sys.stderr
        )
        sys.exit(1)

if __name__ == "__main__":
    run()
