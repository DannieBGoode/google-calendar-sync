import base64
import hashlib
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

from calendar_sync.bootstrap.config import Settings
from calendar_sync.domain.model import ConnectedAccountId
from calendar_sync.infrastructure.google.oauth import (
    CALENDAR_SCOPES,
    ConnectedGoogleAccountDisconnected,
    CredentialCipher,
    GoogleAccountAccessCheckFailed,
    GoogleCalendarPermissionRequired,
    GoogleOAuthService,
    InvalidMasterKey,
    InvalidOAuthState,
    SqliteConnectedAccountStore,
)
from calendar_sync.infrastructure.persistence.sqlite import initialize_database


def test_credential_cipher_round_trip_is_not_plaintext() -> None:
    cipher = CredentialCipher(CredentialCipher.generate_key())
    plaintext = '{"refresh_token":"synthetic-secret"}'

    encrypted = cipher.encrypt(plaintext)

    assert plaintext.encode() not in encrypted
    assert cipher.decrypt(encrypted) == plaintext


def test_invalid_master_key_is_rejected() -> None:
    with pytest.raises(InvalidMasterKey):
        CredentialCipher("not-a-32-byte-key")


def test_connected_account_upsert_preserves_identity(tmp_path: Path) -> None:
    database = tmp_path / "test.db"
    initialize_database(database)
    store = SqliteConnectedAccountStore(database, CredentialCipher(CredentialCipher.generate_key()))

    first = store.save("Personal", "person@example.test", '{"token":"one"}')
    updated = store.save("Renamed", "person@example.test", '{"token":"two"}')

    assert updated.id == first.id
    assert updated.display_name == "Renamed"
    assert len(store.list()) == 1


def test_disconnect_discards_credentials_and_reauthorization_preserves_identity(
    tmp_path: Path,
) -> None:
    database = tmp_path / "test.db"
    initialize_database(database)
    cipher = CredentialCipher(CredentialCipher.generate_key())
    store = SqliteConnectedAccountStore(database, cipher)
    account = store.save("Personal", "person@example.test", '{"refresh_token":"synthetic-secret"}')
    disconnected = store.disconnect(account.id)

    assert disconnected.state == "disconnected"
    with pytest.raises(ConnectedGoogleAccountDisconnected, match="reauthorize"):
        store.credentials(account.id)
    with sqlite3.connect(database) as connection:
        cleared = bytes(
            connection.execute(
                "SELECT encrypted_credentials FROM connected_accounts WHERE id = ?",
                (account.id.value,),
            ).fetchone()[0]
        )
    assert cipher.decrypt(cleared) == "{}"
    assert b"synthetic-secret" not in cleared

    reauthorized = store.save(
        "Personal", "person@example.test", '{"refresh_token":"replacement-secret"}'
    )
    assert reauthorized.id == account.id
    assert reauthorized.state == "connected"


def test_oauth_state_is_single_use(tmp_path: Path) -> None:
    database = tmp_path / "test.db"
    initialize_database(database)
    store = SqliteConnectedAccountStore(database, CredentialCipher(CredentialCipher.generate_key()))
    oauth = GoogleOAuthService(Settings(database), store)

    oauth._store_state("synthetic-state")
    oauth._consume_state("synthetic-state")

    with pytest.raises(InvalidOAuthState, match="already used"):
        oauth._consume_state("synthetic-state")


def test_expired_oauth_state_is_rejected(tmp_path: Path) -> None:
    database = tmp_path / "test.db"
    initialize_database(database)
    store = SqliteConnectedAccountStore(database, CredentialCipher(CredentialCipher.generate_key()))
    oauth = GoogleOAuthService(Settings(database), store)
    oauth._store_state("expired-state")
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE oauth_states SET expires_at = ?",
            ("2000-01-01T00:00:00+00:00",),
        )

    with pytest.raises(InvalidOAuthState, match="expired"):
        oauth._consume_state("expired-state")


def test_pkce_verifier_survives_oauth_flow_reconstruction(tmp_path: Path) -> None:
    database = tmp_path / "test.db"
    initialize_database(database)
    master_key = CredentialCipher.generate_key()
    store = SqliteConnectedAccountStore(database, CredentialCipher(master_key))
    oauth = GoogleOAuthService(
        Settings(
            database,
            master_key=master_key,
            google_client_id="synthetic.apps.googleusercontent.com",
            google_client_secret="synthetic-secret",
        ),
        store,
    )
    state = "synthetic-state"

    start_flow = oauth._flow(state)
    authorization_url, _ = start_flow.authorization_url()
    callback_flow = oauth._flow(state)

    verifier = callback_flow.code_verifier
    assert verifier is not None
    expected_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    )
    query = parse_qs(urlparse(authorization_url).query)
    assert start_flow.code_verifier == verifier
    assert verifier != state
    assert query["code_challenge"] == [expected_challenge]
    assert query["code_challenge_method"] == ["S256"]


def test_oauth_completion_exchanges_explicit_code_without_parsing_callback_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class StubCredentials:
        def to_json(self) -> str:
            return '{"token":"synthetic-token"}'

    class StubFlow:
        def __init__(self) -> None:
            self.credentials = StubCredentials()
            self.fetch_token_calls: list[dict[str, Any]] = []

        def fetch_token(self, **kwargs: Any) -> None:
            self.fetch_token_calls.append(kwargs)

    class StubCalendarRequest:
        def execute(self) -> dict[str, Any]:
            return {
                "items": [
                    {
                        "id": "person@example.test",
                        "summary": "Personal",
                        "primary": True,
                    }
                ]
            }

    class StubCalendarList:
        def list(self, *, pageToken: str | None = None) -> StubCalendarRequest:
            assert pageToken is None
            return StubCalendarRequest()

    class StubCalendarService:
        def calendarList(self) -> StubCalendarList:
            return StubCalendarList()

    database = tmp_path / "test.db"
    initialize_database(database)
    store = SqliteConnectedAccountStore(database, CredentialCipher(CredentialCipher.generate_key()))
    oauth = GoogleOAuthService(Settings(database), store)
    oauth._store_state("synthetic-state")
    flow = StubFlow()

    def fake_flow(state: str) -> StubFlow:
        assert state == "synthetic-state"
        return flow

    def fake_build(*args: Any, **kwargs: Any) -> StubCalendarService:
        assert args == ("calendar", "v3")
        assert kwargs["credentials"] is flow.credentials
        assert kwargs["cache_discovery"] is False
        return StubCalendarService()

    monkeypatch.setattr(oauth, "_flow", fake_flow)
    monkeypatch.setattr("calendar_sync.infrastructure.google.oauth.build", fake_build)

    account = oauth.complete("synthetic-state", "synthetic-code")

    assert flow.fetch_token_calls == [{"code": "synthetic-code"}]
    assert account.email == "person@example.test"


def test_oauth_completion_rejects_a_grant_without_all_calendar_scopes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class StubCredentials:
        granted_scopes = (CALENDAR_SCOPES[0],)

    class StubFlow:
        credentials = StubCredentials()

        def fetch_token(self, **kwargs: Any) -> None:
            assert kwargs == {"code": "synthetic-code"}

    database = tmp_path / "test.db"
    initialize_database(database)
    store = SqliteConnectedAccountStore(database, CredentialCipher(CredentialCipher.generate_key()))
    oauth = GoogleOAuthService(Settings(database), store)
    oauth._store_state("synthetic-state")
    monkeypatch.setattr(oauth, "_flow", lambda _: StubFlow())

    with pytest.raises(GoogleCalendarPermissionRequired, match="Calendar permission"):
        oauth.complete("synthetic-state", "synthetic-code")

    assert store.list() == ()


def test_access_check_verifies_calendar_list_and_event_permissions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class StubCalendarRequest:
        def execute(self) -> dict[str, Any]:
            return {
                "items": [
                    {"id": "primary@example.test", "primary": True, "accessRole": "owner"},
                    {"id": "shared@example.test", "accessRole": "reader"},
                ]
            }

    class StubCalendarList:
        def list(self, *, pageToken: str | None = None) -> StubCalendarRequest:
            assert pageToken is None
            return StubCalendarRequest()

    class StubEventRequest:
        def execute(self) -> dict[str, Any]:
            return {"items": [{"id": "synthetic-event-id"}]}

    class StubEvents:
        def list(self, **parameters: Any) -> StubEventRequest:
            assert parameters == {
                "calendarId": "primary@example.test",
                "maxResults": 1,
                "showDeleted": False,
                "singleEvents": False,
                "fields": "items(id)",
            }
            return StubEventRequest()

    class StubCalendarService:
        def calendarList(self) -> StubCalendarList:
            return StubCalendarList()

        def events(self) -> StubEvents:
            return StubEvents()

    database = tmp_path / "test.db"
    initialize_database(database)
    store = SqliteConnectedAccountStore(database, CredentialCipher(CredentialCipher.generate_key()))
    oauth = GoogleOAuthService(Settings(database), store)
    monkeypatch.setattr(store, "credentials", lambda _: object())
    monkeypatch.setattr(
        "calendar_sync.infrastructure.google.oauth.build",
        lambda *args, **kwargs: StubCalendarService(),
    )

    access = oauth.verify_access(ConnectedAccountId("account-1"))

    assert access.calendars_visible == 2
    assert access.writable_calendars == 1


def test_access_check_explains_calendar_api_permission_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class PermissionDenied(Exception):
        resp = SimpleNamespace(status=403)

    class StubCalendarRequest:
        def execute(self) -> dict[str, Any]:
            raise PermissionDenied

    class StubCalendarList:
        def list(self, *, pageToken: str | None = None) -> StubCalendarRequest:
            return StubCalendarRequest()

    class StubCalendarService:
        def calendarList(self) -> StubCalendarList:
            return StubCalendarList()

    database = tmp_path / "test.db"
    initialize_database(database)
    store = SqliteConnectedAccountStore(database, CredentialCipher(CredentialCipher.generate_key()))
    oauth = GoogleOAuthService(Settings(database), store)
    monkeypatch.setattr(store, "credentials", lambda _: object())
    monkeypatch.setattr(
        "calendar_sync.infrastructure.google.oauth.build",
        lambda *args, **kwargs: StubCalendarService(),
    )

    with pytest.raises(GoogleAccountAccessCheckFailed, match="Calendar API is enabled"):
        oauth.verify_access(ConnectedAccountId("account-1"))


@pytest.mark.parametrize(
    ("status_code", "expected_detail"),
    [
        (401, "authorization has expired"),
        (None, "could not be verified; try again"),
    ],
)
def test_access_check_classifies_expired_and_unexpected_provider_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status_code: int | None,
    expected_detail: str,
) -> None:
    class ProviderFailure(Exception):
        resp = SimpleNamespace(status=status_code)

    class StubCalendarRequest:
        def execute(self) -> dict[str, Any]:
            raise ProviderFailure

    class StubCalendarList:
        def list(self, *, pageToken: str | None = None) -> StubCalendarRequest:
            assert pageToken is None
            return StubCalendarRequest()

    class StubCalendarService:
        def calendarList(self) -> StubCalendarList:
            return StubCalendarList()

    database = tmp_path / "test.db"
    initialize_database(database)
    store = SqliteConnectedAccountStore(database, CredentialCipher(CredentialCipher.generate_key()))
    oauth = GoogleOAuthService(Settings(database), store)
    monkeypatch.setattr(store, "credentials", lambda _: object())
    monkeypatch.setattr(
        "calendar_sync.infrastructure.google.oauth.build",
        lambda *args, **kwargs: StubCalendarService(),
    )

    with pytest.raises(GoogleAccountAccessCheckFailed, match=expected_detail):
        oauth.verify_access(ConnectedAccountId("account-1"))


def test_access_check_rejects_an_account_without_visible_calendars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class StubCalendarRequest:
        def execute(self) -> dict[str, Any]:
            return {"items": []}

    class StubCalendarList:
        def list(self, *, pageToken: str | None = None) -> StubCalendarRequest:
            assert pageToken is None
            return StubCalendarRequest()

    class StubCalendarService:
        def calendarList(self) -> StubCalendarList:
            return StubCalendarList()

    database = tmp_path / "test.db"
    initialize_database(database)
    store = SqliteConnectedAccountStore(database, CredentialCipher(CredentialCipher.generate_key()))
    oauth = GoogleOAuthService(Settings(database), store)
    monkeypatch.setattr(store, "credentials", lambda _: object())
    monkeypatch.setattr(
        "calendar_sync.infrastructure.google.oauth.build",
        lambda *args, **kwargs: StubCalendarService(),
    )

    with pytest.raises(GoogleAccountAccessCheckFailed, match="did not expose a calendar"):
        oauth.verify_access(ConnectedAccountId("account-1"))
