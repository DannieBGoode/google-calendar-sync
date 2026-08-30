from dataclasses import replace
from datetime import datetime

from calendar_sync.application.preview import PreviewSyncRule
from calendar_sync.domain.model import Recurrence, SyncRuleState
from calendar_sync.domain.services import EventProjector
from calendar_sync.infrastructure.persistence.memory import InMemoryUnitOfWorkFactory
from tests.application.test_execute_sync_rule import FakeCalendarProvider
from tests.helpers import NOW, event, rule


class FixedClock:
    def now(self) -> datetime:
        return NOW


def test_preview_is_side_effect_free_and_unlocks_enablement() -> None:
    draft = rule(state=SyncRuleState.DRAFT)
    unit_of_work = InMemoryUnitOfWorkFactory()
    unit_of_work.state.rules[draft.id] = draft
    provider = FakeCalendarProvider(event())
    use_case = PreviewSyncRule(unit_of_work, provider, EventProjector(), FixedClock())

    preview = use_case.execute(draft.id)

    assert preview.eligible_events == 1
    assert preview.sample[0].projected_title == "Busy"
    assert provider.destination is None
    assert unit_of_work.state.rules[draft.id].state is SyncRuleState.DRY_RUN_VALIDATED


def test_preview_revalidates_a_degraded_rule_after_reauthorization() -> None:
    degraded = rule(state=SyncRuleState.DEGRADED)
    unit_of_work = InMemoryUnitOfWorkFactory()
    unit_of_work.state.rules[degraded.id] = degraded
    provider = FakeCalendarProvider(event())
    use_case = PreviewSyncRule(unit_of_work, provider, EventProjector(), FixedClock())

    use_case.execute(degraded.id)

    assert unit_of_work.state.rules[degraded.id].state is SyncRuleState.DRY_RUN_VALIDATED


def test_preview_excludes_recurring_events_until_occurrences_are_supported() -> None:
    draft = rule(state=SyncRuleState.DRAFT)
    recurring = replace(event(), recurrence=Recurrence(("RRULE:FREQ=WEEKLY",)))
    unit_of_work = InMemoryUnitOfWorkFactory()
    unit_of_work.state.rules[draft.id] = draft
    provider = FakeCalendarProvider(recurring)
    use_case = PreviewSyncRule(unit_of_work, provider, EventProjector(), FixedClock())

    preview = use_case.execute(draft.id)

    assert preview.eligible_events == 0
    assert preview.excluded_events == 1
