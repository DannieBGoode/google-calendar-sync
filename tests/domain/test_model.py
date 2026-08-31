from datetime import date

import pytest

from calendar_sync.domain.errors import DomainValidationError, InvalidStateTransition
from calendar_sync.domain.model import (
    AllDayRange,
    SyncRule,
    SyncRuleState,
)
from tests.helpers import endpoint, rule


def test_rule_can_cross_connected_accounts() -> None:
    cross_account = rule(state=SyncRuleState.DRAFT)

    assert (
        cross_account.source.connected_account_id != cross_account.destination.connected_account_id
    )


def test_rule_cannot_target_its_source_endpoint() -> None:
    same = endpoint("account", "calendar")

    with pytest.raises(DomainValidationError, match="cannot target its source"):
        SyncRule(id=rule().id, source=same, destination=same)


def test_rule_requires_preview_before_enablement() -> None:
    draft = rule(state=SyncRuleState.DRAFT)

    with pytest.raises(InvalidStateTransition):
        draft.enable()

    assert draft.mark_dry_run_validated().enable().state is SyncRuleState.ENABLED


def test_validated_rule_can_be_degraded_before_enablement() -> None:
    validated = rule(state=SyncRuleState.DRY_RUN_VALIDATED)

    assert validated.degrade().state is SyncRuleState.DEGRADED

    with pytest.raises(InvalidStateTransition):
        rule(state=SyncRuleState.DRAFT).degrade()


def test_all_day_range_uses_exclusive_end_date() -> None:
    value = AllDayRange(date(2026, 8, 30), date(2026, 8, 31))

    assert value.ends_before == date(2026, 8, 31)

    with pytest.raises(DomainValidationError):
        AllDayRange(date(2026, 8, 30), date(2026, 8, 30))
