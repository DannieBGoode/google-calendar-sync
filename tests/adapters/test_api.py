import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from calendar_sync.application.ports import AuditEntry
from calendar_sync.bootstrap.config import Settings
from calendar_sync.bootstrap.container import build_container
from calendar_sync.domain.model import SyncRuleId
from calendar_sync.interfaces.api.app import create_app
from tests.helpers import rule


def test_first_run_admin_and_protected_dashboard(tmp_path: Path) -> None:
    app = create_app(build_container(Settings(tmp_path / "test.db")))

    with TestClient(app) as client:
        assert client.get("/api/v1/setup").json() == {"administrator_configured": False}
        assert client.get("/api/v1/dashboard").status_code == 401

        response = client.post(
            "/api/v1/setup/admin", json={"password": "correct horse battery staple"}
        )

        assert response.status_code == 200
        assert response.json() == {"authenticated": True}
        dashboard = client.get("/api/v1/dashboard")
        assert dashboard.status_code == 200
        assert dashboard.json() == {
            "health": "healthy",
            "connected_accounts": 0,
            "sync_rules": 0,
            "open_incidents": 0,
        }


def test_create_cross_account_rule_through_api(tmp_path: Path) -> None:
    app = create_app(build_container(Settings(tmp_path / "test.db")))

    with TestClient(app) as client:
        client.post("/api/v1/setup/admin", json={"password": "correct horse battery staple"})
        payload = {
            "source": {
                "connected_account_id": "personal",
                "calendar_id": "personal-calendar",
            },
            "destination": {
                "connected_account_id": "work",
                "calendar_id": "work-calendar",
            },
            "privacy_policy": "busy_only",
            "sync_all_day_events": False,
        }

        response = client.post("/api/v1/rules", json=payload)

        assert response.status_code == 201
        assert response.json()["source"]["connected_account_id"] == "personal"
        assert response.json()["destination"]["connected_account_id"] == "work"
        assert response.json()["sync_all_day_events"] is False


def test_activity_and_incidents_require_admin_and_return_operational_data(
    tmp_path: Path,
) -> None:
    database = tmp_path / "test.db"
    container = build_container(Settings(database))
    with container.unit_of_work() as uow:
        uow.audit.append(
            AuditEntry(
                occurred_at=datetime(2026, 8, 30, tzinfo=UTC),
                rule_id=SyncRuleId("rule-1"),
                action="create",
                outcome="completed",
                detail="source has no managed projection",
            )
        )
        uow.commit()
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO incidents (
                id, deduplication_key, rule_id, category, state,
                summary, opened_at, updated_at
            ) VALUES (?, ?, ?, ?, 'open', ?, ?, ?)
            """,
            (
                "incident-1",
                "provider:rule-1",
                "rule-1",
                "authentication",
                "Google authorization expired",
                "2026-08-30T10:00:00+00:00",
                "2026-08-30T10:00:00+00:00",
            ),
        )

    app = create_app(container)
    with TestClient(app) as client:
        assert client.get("/api/v1/activity").status_code == 401
        client.post("/api/v1/setup/admin", json={"password": "correct horse battery staple"})

        activity = client.get("/api/v1/activity").json()
        incidents = client.get("/api/v1/incidents").json()

        assert activity[0]["action"] == "create"
        assert "event" not in activity[0]
        assert incidents[0]["summary"] == "Google authorization expired"


def test_logout_revokes_session_and_wrong_password_cannot_restore_it(tmp_path: Path) -> None:
    app = create_app(build_container(Settings(tmp_path / "test.db")))

    with TestClient(app) as client:
        client.post("/api/v1/setup/admin", json={"password": "correct horse battery staple"})
        assert client.get("/api/v1/dashboard").status_code == 200

        assert client.delete("/api/v1/session").status_code == 204
        assert client.get("/api/v1/dashboard").status_code == 401
        assert (
            client.post("/api/v1/session", json={"password": "this password is wrong"}).status_code
            == 401
        )
        assert (
            client.post(
                "/api/v1/session", json={"password": "correct horse battery staple"}
            ).status_code
            == 200
        )
        assert client.get("/api/v1/dashboard").status_code == 200


def test_admin_setup_is_single_use_and_secure_cookie_setting_is_honored(tmp_path: Path) -> None:
    app = create_app(build_container(Settings(tmp_path / "test.db", secure_cookies=True)))

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/setup/admin", json={"password": "correct horse battery staple"}
        )
        second = client.post(
            "/api/v1/setup/admin", json={"password": "another correct battery staple"}
        )

        assert "Secure" in first.headers["set-cookie"]
        assert "HttpOnly" in first.headers["set-cookie"]
        assert "SameSite=lax" in first.headers["set-cookie"]
        assert second.status_code == 409


def test_rule_validation_rejects_unknown_policy_same_endpoint_and_duplicate(
    tmp_path: Path,
) -> None:
    app = create_app(build_container(Settings(tmp_path / "test.db")))
    base_payload = {
        "source": {"connected_account_id": "personal", "calendar_id": "calendar"},
        "destination": {"connected_account_id": "work", "calendar_id": "calendar"},
        "privacy_policy": "busy_only",
        "sync_all_day_events": True,
    }

    with TestClient(app) as client:
        client.post("/api/v1/setup/admin", json={"password": "correct horse battery staple"})
        unknown = client.post("/api/v1/rules", json={**base_payload, "privacy_policy": "unknown"})
        same_endpoint = client.post(
            "/api/v1/rules",
            json={
                **base_payload,
                "destination": {
                    "connected_account_id": "personal",
                    "calendar_id": "calendar",
                },
            },
        )
        first = client.post("/api/v1/rules", json=base_payload)
        duplicate = client.post("/api/v1/rules", json=base_payload)

        assert unknown.status_code == 422
        assert same_endpoint.status_code == 422
        assert first.status_code == 201
        assert duplicate.status_code == 409


def test_google_routes_report_unconfigured_installation(tmp_path: Path) -> None:
    app = create_app(build_container(Settings(tmp_path / "test.db")))

    with TestClient(app) as client:
        client.post("/api/v1/setup/admin", json={"password": "correct horse battery staple"})

        assert client.get("/api/v1/google/configuration").json() == {"configured": False}
        assert client.get("/api/v1/oauth/google/start").status_code == 503
        assert client.get("/api/v1/accounts").json() == []
        assert client.post("/api/v1/rules/missing/preview").status_code == 503


def test_frontend_fallback_cannot_serve_files_outside_static_root(tmp_path: Path) -> None:
    app = create_app(build_container(Settings(tmp_path / "test.db")))

    with TestClient(app) as client:
        response = client.get("/%2e%2e/app.py")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Calendar Sync" in response.text
    assert "from __future__ import annotations" not in response.text


def test_enabled_rule_can_be_paused_through_api(tmp_path: Path) -> None:
    container = build_container(Settings(tmp_path / "test.db"))
    with container.unit_of_work() as uow:
        uow.rules.add(rule())
        uow.commit()
    app = create_app(container)

    with TestClient(app) as client:
        client.post("/api/v1/setup/admin", json={"password": "correct horse battery staple"})
        paused = client.post("/api/v1/rules/rule-1/pause")
        repeated = client.post("/api/v1/rules/rule-1/pause")

    assert paused.status_code == 200
    assert paused.json()["state"] == "paused"
    assert repeated.status_code == 409
