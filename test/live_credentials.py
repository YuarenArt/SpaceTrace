"""Credentials for opt-in live tests from the environment or OS keyring."""

import os

import keyring
from keyring.errors import PasswordDeleteError


SERVICE = "SpaceTrace.SpaceTrack.LiveTests.v2"


def load_credentials():
    login = os.environ.get("SPACETRACE_LOGIN")
    password = os.environ.get("SPACETRACE_PASSWORD")
    if login is not None or password is not None:
        if not login or not password:
            raise RuntimeError("Both SPACETRACE_LOGIN and SPACETRACE_PASSWORD are required.")
        return login, password

    login = keyring.get_password(SERVICE, "login")
    password = keyring.get_password(SERVICE, "password")
    if not login or not password:
        raise RuntimeError(
            "SpaceTrack credentials are not configured. "
            "Run scripts/manage_spacetrack_credentials.py set locally."
        )
    return login, password


def save_credentials(login, password):
    if not login or not password:
        raise ValueError("Login and password are required")
    keyring.set_password(SERVICE, "login", login)
    keyring.set_password(SERVICE, "password", password)


def delete_credentials():
    for field in ("login", "password"):
        try:
            keyring.delete_password(SERVICE, field)
        except PasswordDeleteError:
            pass
