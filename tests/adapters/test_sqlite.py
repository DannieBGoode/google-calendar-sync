from pathlib import Path

import pytest

from calendar_sync.application.errors import DuplicateDirectionalRelationship
from calendar_sync.domain.model import (
    EventId,
    EventMapping,
    EventMappingId,
    EventRef,
    ProjectionFingerprint,
    SyncRuleId,
)
from calendar_sync.infrastructure.persistence.sqlite import (
    SqliteUnitOfWorkFactory,
    initialize_database,
)
from tests.helpers import endpoint, event, rule


def test_sqlite_rule_repository_round_trip(tmp_path: Path) -> None:
    database = tmp_path / "calendar-sync.db"
    initialize_database(database)
    factory = SqliteUnitOfWorkFactory(database)

    with factory() as uow:
        uow.rules.add(rule())
        uow.commit()

    with factory() as uow:
        restored = uow.rules.get(rule().id)

    assert restored == rule()


def test_database_migration_is_idempotent(tmp_path: Path) -> None:
    database = tmp_path / "calendar-sync.db"

    initialize_database(database)
    initialize_database(database)

    with SqliteUnitOfWorkFactory(database)() as uow:
        assert uow.rules.list() == ()


def test_recreated_projection_updates_existing_mapping_and_destination_cursor(
    tmp_path: Path,
) -> None:
    database = tmp_path / "calendar-sync.db"
    initialize_database(database)
    factory = SqliteUnitOfWorkFactory(database)
    source = event().reference
    first_destination = EventRef(endpoint("work-account", "work-calendar"), EventId("first"))
    restored_destination = EventRef(endpoint("work-account", "work-calendar"), EventId("restored"))
    original = EventMapping(
        EventMappingId("stable-mapping"),
        rule().id,
        source,
        first_destination,
        "revision-1",
        ProjectionFingerprint("fingerprint-1"),
    )
    restored = EventMapping(
        original.id,
        original.rule_id,
        original.source,
        restored_destination,
        "revision-2",
        ProjectionFingerprint("fingerprint-2"),
    )

    with factory() as uow:
        uow.rules.add(rule())
        uow.mappings.save(original)
        uow.destination_cursors.save(rule().id, "destination-cursor")
        uow.commit()
    with factory() as uow:
        uow.mappings.save(restored)
        uow.commit()
    with factory() as uow:
        assert uow.mappings.for_source(rule().id, source) == restored
        assert uow.mappings.for_destination(rule().id, restored_destination) == restored
        assert uow.destination_cursors.get(rule().id) == "destination-cursor"


def test_sqlite_unique_relationship_is_translated_to_application_error(tmp_path: Path) -> None:
    database = tmp_path / "calendar-sync.db"
    initialize_database(database)
    factory = SqliteUnitOfWorkFactory(database)
    duplicate = rule()
    second_id = type(duplicate)(
        id=SyncRuleId("rule-2"),
        source=duplicate.source,
        destination=duplicate.destination,
        transformation=duplicate.transformation,
        initial_lookback_days=duplicate.initial_lookback_days,
        state=duplicate.state,
    )

    with factory() as uow:
        uow.rules.add(duplicate)
        uow.commit()
    with pytest.raises(DuplicateDirectionalRelationship), factory() as uow:
        uow.rules.add(second_id)
