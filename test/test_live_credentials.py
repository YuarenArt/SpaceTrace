"""Credential adapter tests never access the real system keyring."""

import pytest
from keyring.errors import PasswordDeleteError

from test import live_credentials


@pytest.mark.unit
def test_live_credentials_round_trip_uses_keyring(monkeypatch):
    monkeypatch.delenv("SPACETRACE_LOGIN", raising=False)
    monkeypatch.delenv("SPACETRACE_PASSWORD", raising=False)
    stored = {}

    def get_password(service, field):
        assert service == live_credentials.SERVICE
        return stored.get(field)

    def set_password(service, field, value):
        assert service == live_credentials.SERVICE
        stored[field] = value

    def delete_password(service, field):
        assert service == live_credentials.SERVICE
        if field not in stored:
            raise PasswordDeleteError("missing")
        del stored[field]

    monkeypatch.setattr(live_credentials.keyring, "get_password", get_password)
    monkeypatch.setattr(live_credentials.keyring, "set_password", set_password)
    monkeypatch.setattr(live_credentials.keyring, "delete_password", delete_password)

    with pytest.raises(RuntimeError, match="not configured"):
        live_credentials.load_credentials()
    live_credentials.save_credentials("user@example.invalid", "secret")
    assert live_credentials.load_credentials() == ("user@example.invalid", "secret")
    live_credentials.delete_credentials()
    live_credentials.delete_credentials()
    with pytest.raises(RuntimeError, match="not configured"):
        live_credentials.load_credentials()


@pytest.mark.unit
def test_live_credentials_use_environment_without_keyring(monkeypatch):
    monkeypatch.setenv("SPACETRACE_LOGIN", "user@example.invalid")
    monkeypatch.setenv("SPACETRACE_PASSWORD", "test-password")
    monkeypatch.setattr(live_credentials.keyring, "get_password", lambda *_: pytest.fail("keyring used"))
    assert live_credentials.load_credentials() == ("user@example.invalid", "test-password")


@pytest.mark.unit
@pytest.mark.parametrize("login,password", [("user@example.invalid", ""), ("", "test-password")])
def test_live_credentials_reject_incomplete_environment(monkeypatch, login, password):
    monkeypatch.setenv("SPACETRACE_LOGIN", login)
    monkeypatch.setenv("SPACETRACE_PASSWORD", password)
    with pytest.raises(RuntimeError, match="Both SPACETRACE_LOGIN"):
        live_credentials.load_credentials()
