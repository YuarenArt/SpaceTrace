"""Local credential setup. Never accepts passwords through command arguments."""
import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test.live_credentials import delete_credentials, load_credentials, save_credentials


def main():
    parser = argparse.ArgumentParser(description="SpaceTrace live-test credentials")
    parser.add_argument("action", choices=("set", "status", "delete"))
    action = parser.parse_args().action

    if action == "set":
        login = input("SpaceTrack login (email): ").strip()
        if not login:
            raise SystemExit("Login cannot be empty")
        password = getpass.getpass("SpaceTrack password: ")
        if not password:
            raise SystemExit("Password cannot be empty")
        save_credentials(login, password)
        print("Credentials saved to the system keyring; no repository file was created.")
    elif action == "status":
        try:
            load_credentials()
        except RuntimeError:
            print("SpaceTrack credentials: missing (system keyring)")
            raise SystemExit(1)
        print("SpaceTrack credentials: configured (system keyring)")
    else:
        delete_credentials()
        print("SpaceTrack credentials removed from the system vault.")


if __name__ == "__main__":
    main()
