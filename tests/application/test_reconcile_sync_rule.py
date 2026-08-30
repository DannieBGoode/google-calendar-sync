from calendar_sync.application.reconciliation import ReconcileSyncRule
from calendar_sync.application.synchronization import ExecuteSyncRule
from calendar_sync.domain.services import (
    EventProjector,
    ProjectionFingerprinter,
    ReconciliationService,
    SyncDecisionService,
)
from calendar_sync.infrastructure.persistence.memory import InMemoryUnitOfWorkFactory
from tests.application.test_execute_sync_rule import FakeCalendarProvider, FixedClock
from tests.helpers import event, rule


def test_reconciliation_independently_proves_managed_projection() -> None:
    unit_of_work = InMemoryUnitOfWorkFactory()
    unit_of_work.state.rules[rule().id] = rule()
    provider = FakeCalendarProvider(event())
    projector = EventProjector()
    fingerprinter = ProjectionFingerprinter()
    ExecuteSyncRule(
        unit_of_work,
        provider,
        SyncDecisionService(projector, fingerprinter),
        fingerprinter,
        FixedClock(),
    ).execute(rule().id)

    report = ReconcileSyncRule(
        unit_of_work,
        provider,
        projector,
        ReconciliationService(fingerprinter),
    ).execute(rule().id)

    assert report.checked_mappings == 1
    assert report.is_consistent
