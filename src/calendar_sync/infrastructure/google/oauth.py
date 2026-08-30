from __future__ import annotations

import base64
import hashlib
import json
import secrets
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow  # type: ignore[import-untyped]
from googleapiclient.discovery import build  # type: ignore[import-untyped]

from calendar_sync.bootstrap.config import Settings
from calendar_sync.domain.model import ConnectedAccountId

CALENDAR_SCOPES = (
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
)


class GoogleOAuthNotConfigured(RuntimeError):
    pass


class InvalidOAuthState(ValueError):
    pass


class InvalidMasterKey(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ConnectedGoogleAccount:
    id: ConnectedAccountId
    display_name: str
    email: str
    state: str


@dataclass(frozen=True, slots=True)
class DiscoveredCalendar:
    id: str
    summary: str
    access_role: str
    primary: bool


class CredentialCipher:
    def __init__(self, encoded_key: str) -> None:
        try:
            key = base64.urlsafe_b64decode(encoded_key.encode())
        except Exception as error:
            raise InvalidMasterKey("master key must be URL-safe base64") from error
        if len(key) != 32:
            raise InvalidMasterKey("master key must decode to exactly 32 bytes")
        self._cipher = AESGCM(key)

    def encrypt(self, plaintext: str) -> bytes:
        nonce = secrets.token_bytes(12)
        return nonce + self._cipher.encrypt(nonce, plaintext.encode(), None)

    def decrypt(self, ciphertext: bytes) -> str:
        nonce, encrypted = ciphertext[:12], ciphertext[12:]
        return self._cipher.decrypt(nonce, encrypted, None).decode()

    @staticmethod
    def generate_key() -> str:
        return base64.urlsafe_b64encode(AESGCM.generate_key(bit_length=256)).decode()


class SqliteConnectedAccountStore:
    def __init__(self, database_path: Path, cipher: CredentialCipher) -> None:
        self._database_path = database_path
        self._cipher = cipher

    def list(self) -> tuple[ConnectedGoogleAccount, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, display_name, email, state FROM connected_accounts ORDER BY email"
            ).fetchall()
        return tuple(
            ConnectedGoogleAccount(
                ConnectedAccountId(str(row["id"])),
                str(row["display_name"]),
                str(row["email"]),
                str(row["state"]),
            )
            for row in rows
        )

    def save(self, display_name: str, email: str, credential_json: str) -> ConnectedGoogleAccount:
        now = datetime.now(UTC).isoformat()
        account_id = str(uuid.uuid4())
        encrypted = self._cipher.encrypt(credential_json)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO connected_accounts (
                    id, provider, display_name, email, encrypted_credentials,
                    state, created_at, updated_at
                ) VALUES (?, 'google', ?, ?, ?, 'connected', ?, ?)
                ON CONFLICT(provider, email) DO UPDATE SET
                    display_name = excluded.display_name,
                    encrypted_credentials = excluded.encrypted_credentials,
                    state = 'connected',
                    updated_at = excluded.updated_at
                """,
                (account_id, display_name, email, encrypted, now, now),
            )
            row = connection.execute(
                "SELECT id, display_name, email, state FROM connected_accounts WHERE email = ?",
                (email,),
            ).fetchone()
        assert row is not None
        return ConnectedGoogleAccount(
            ConnectedAccountId(str(row["id"])),
            str(row["display_name"]),
            str(row["email"]),
            str(row["state"]),
        )

    def credentials(self, account_id: ConnectedAccountId) -> Credentials:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT encrypted_credentials FROM connected_accounts WHERE id = ?",
                (account_id.value,),
            ).fetchone()
        if row is None:
            raise KeyError(f"connected account {account_id.value} does not exist")
        payload = json.loads(self._cipher.decrypt(bytes(row["encrypted_credentials"])))
        credentials = Credentials.from_authorized_user_info(  # type: ignore[no-untyped-call]
            payload, scopes=CALENDAR_SCOPES
        )
        return cast(Credentials, credentials)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection


class GoogleOAuthService:
    def __init__(
        self,
        settings: Settings,
        accounts: SqliteConnectedAccountStore,
    ) -> None:
        self._settings = settings
        self._accounts = accounts

    def authorization_url(self) -> str:
        self._require_client_configuration()
        state = secrets.token_urlsafe(32)
        self._store_state(state)
        flow = self._flow(state)
        url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return str(url)

    def complete(self, state: str, authorization_response: str) -> ConnectedGoogleAccount:
        self._consume_state(state)
        flow = self._flow(state)
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        calendars = self._calendar_items(service)
        primary = next((calendar for calendar in calendars if calendar.get("primary")), None)
        if primary is None:
            raise RuntimeError("Google account did not expose a primary calendar")
        email = str(primary.get("id") or "")
        if not email:
            raise RuntimeError("Google primary calendar did not expose an identity")
        display_name = str(primary.get("summary") or email)
        return self._accounts.save(display_name, email, credentials.to_json())

    def calendars(self, account_id: ConnectedAccountId) -> tuple[DiscoveredCalendar, ...]:
        credentials = self._accounts.credentials(account_id)
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        return tuple(
            DiscoveredCalendar(
                id=str(item["id"]),
                summary=str(item.get("summary") or item["id"]),
                access_role=str(item.get("accessRole") or "reader"),
                primary=bool(item.get("primary")),
            )
            for item in self._calendar_items(service)
            if isinstance(item.get("id"), str)
        )

    def service_for(self, account_id: ConnectedAccountId) -> Any:
        credentials = self._accounts.credentials(account_id)
        return build("calendar", "v3", credentials=credentials, cache_discovery=False)

    def _flow(self, state: str) -> Flow:
        client_config = {
            "web": {
                "client_id": self._settings.google_client_id,
                "client_secret": self._settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self._settings.google_redirect_uri],
            }
        }
        return Flow.from_client_config(
            client_config,
            scopes=CALENDAR_SCOPES,
            state=state,
            redirect_uri=self._settings.google_redirect_uri,
        )

    @staticmethod
    def _calendar_items(service: Any) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            response = service.calendarList().list(pageToken=page_token).execute()
            items.extend(response.get("items", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                return items

    def _require_client_configuration(self) -> None:
        if not (
            self._settings.google_client_id
            and self._settings.google_client_secret
            and self._settings.google_redirect_uri
        ):
            raise GoogleOAuthNotConfigured(
                "configure the Google OAuth client ID, secret, and redirect URI"
            )

    def _store_state(self, state: str) -> None:
        now = datetime.now(UTC)
        with sqlite3.connect(self._settings.database_path) as connection:
            connection.execute(
                "INSERT INTO oauth_states(state_hash, created_at, expires_at) VALUES (?, ?, ?)",
                (
                    _state_hash(state),
                    now.isoformat(),
                    (now + timedelta(minutes=10)).isoformat(),
                ),
            )

    def _consume_state(self, state: str) -> None:
        now = datetime.now(UTC)
        with sqlite3.connect(self._settings.database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE oauth_states SET consumed_at = ?
                WHERE state_hash = ? AND consumed_at IS NULL AND expires_at > ?
                """,
                (now.isoformat(), _state_hash(state), now.isoformat()),
            )
        if cursor.rowcount != 1:
            raise InvalidOAuthState("OAuth state is missing, expired, or already used")


def _state_hash(state: str) -> str:
    return hashlib.sha256(state.encode()).hexdigest()
