from __future__ import annotations
import sys
import argparse
import getpass
import traceback
from .__init__ import get_secret, store_secret, list_credentials, initialize_vault
from ._version import __version__

def stdlib_notify(msg: str):
    """Print to stderr so it doesn't break shell piping or variable assignment."""
    sys.stderr.write(f"SECRET-STD: {msg}\n")
    sys.stderr.flush()

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="dworshak-secret",
        description=f"Dworshak Secret Stdlib Fallback (v{__version__})",
        add_help=False
    )
    
    # Global flags
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--debug", action="store_true", help="Enable diagnostic stack traces")

    subparsers = parser.add_subparsers(dest="command", title="Commands")

    # --- Lifeboat Commands ---
    subparsers.add_parser("init", help="Initialize vault infrastructure", add_help=False)
    
    get_p = subparsers.add_parser("get", help="Retrieve a decrypted secret", add_help=False)
    get_p.add_argument("service", help="Service name")
    get_p.add_argument("item", help="Item key")
    get_p.add_argument("-h", "--help", action="help", help="Show help")

    store_p = subparsers.add_parser("store", help="Store an encrypted secret", add_help=False)
    store_p.add_argument("service", help="Service name")
    store_p.add_argument("item", help="Item key")
    store_p.add_argument("-h", "--help", action="help", help="Show help")

    subparsers.add_parser("list", help="List all stored service/item pairs", add_help=False)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "init":
            res = initialize_vault()
            stdlib_notify(res.message)
            return 0 if res.success else 1

        elif args.command == "get":
            val = get_secret(args.service, args.item)
            if val:
                # Raw print for shell capture: PASS=$(dworshak-secret get s i)
                print(val)
                return 0
            stdlib_notify(f"Error: No secret found for {args.service}/{args.item}")
            return 1

        elif args.command == "store":
            # getpass ensures the password doesn't leak into the terminal's bash history
            secret = getpass.getpass(f"Enter secret for {args.service}/{args.item}: ")
            if secret:
                store_secret(args.service, args.item, secret)
                stdlib_notify("Stored successfully.")
                return 0
            stdlib_notify("Error: Secret cannot be empty.")
            return 1

        elif args.command == "list":
            creds = list_credentials()
            if not creds:
                stdlib_notify("Vault is empty.")
            for s, i in creds:
                print(f"{s}/{i}")
            return 0

    except KeyboardInterrupt:
        stdlib_notify("\nInterrupted.")
        return 130
    except Exception as e:
        stdlib_notify(f"Critical Error: {e}")
        if args.debug:
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())