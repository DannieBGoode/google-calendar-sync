import sqlite3
from pathlib import Path

import pytest

from calendar_sync.bootstrap.config import Settings
from calendar_sync.infrastructure.google.oauth import (
    CredentialCipher,
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
