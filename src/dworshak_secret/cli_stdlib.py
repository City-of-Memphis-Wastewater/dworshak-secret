from __future__ import annotations 
import sys
import argparse
import getpass
from .__init__ import get_secret, store_secret, list_credentials, initialize_vault

def print_err(msg):
    sys.stderr.write(f"SECRET-STD: {msg}\n")

def main():
    parser = argparse.ArgumentParser(description="Dworshak Secret Stdlib Fallback")
    subparsers = parser.add_subparsers(dest="command")

    # Only implement the "Lifeboat" commands
    subparsers.add_parser("init", help="Initialize vault")
    
    get_p = subparsers.add_parser("get", help="Get a secret")
    get_p.add_argument("service")
    get_p.add_argument("item")

    store_p = subparsers.add_parser("store", help="Store a secret")
    store_p.add_argument("service")
    store_p.add_argument("item")

    subparsers.add_parser("list", help="List services")

    args = parser.parse_args()

    if args.command == "init":
        res = initialize_vault()
        print_err(res.message)

    elif args.command == "get":
        val = get_secret(args.service, args.item)
        if val:
            print(val) # Raw output for scripts
        else:
            sys.exit(1)

    elif args.command == "store":
        # Use getpass for the secret so it's not in shell history
        secret = getpass.getpass(f"Enter secret for {args.service}/{args.item}: ")
        if secret:
            store_secret(args.service, args.item, secret)
            print_err("Stored.")

    elif args.command == "list":
        for s, i in list_credentials():
            print(f"{s}/{i}")

if __name__ == "__main__":
    main()