"""
Entry point for dworshak-secret. 
Favors the Rich/Typer CLI but falls back to a zero-dependency stdlib version.
"""
try:
    # Attempt to use the feature-rich CLI
    from .cli import app
    def run():
        app()
except (ImportError, ModuleNotFoundError):
    # Fallback to the 'lifeboat' CLI
    from .cli_stdlib import main as run

if __name__ == "__main__":
    run()