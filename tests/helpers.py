from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from calendar_sync.domain.model import (
    AllDayRange,
    CalendarEndpoint,
    CalendarEvent,
    CalendarId,
    ConnectedAccountId,
    EventId,
    EventRef,
    SyncRule,
    SyncRuleId,
    SyncRuleState,
    TimedInterval,
)

NOW = datetime(2026, 8, 30, 10, 0, tzinfo=UTC)


def endpoint(account: str, calendar: str) -> CalendarEndpoint:
    return CalendarEndpoint(ConnectedAccountId(account), CalendarId(calendar))


def rule(*, state: SyncRuleState = SyncRuleState.ENABLED) -> SyncRule:
    return SyncRule(
        id=SyncRuleId("rule-1"),
        source=endpoint("personal-account", "personal-calendar"),
        destination=endpoint("work-account", "work-calendar"),
        state=state,
    )


def event(
    event_id: str = "source-event",
    *,
    calendar: CalendarEndpoint | None = None,
    revision: str = "revision-1",
    title: str = "Private appointment",
) -> CalendarEvent:
    return CalendarEvent(
        reference=EventRef(calendar or rule().source, EventId(event_id)),
        time=TimedInterval(NOW, NOW + timedelta(hours=1)),
        revision=revision,
        title=title,
        description="Sensitive description",
        location="Sensitive location",
    )


def all_day_event() -> CalendarEvent:
    return CalendarEvent(
        reference=EventRef(rule().source, EventId("all-day")),
        time=AllDayRange(date(2026, 8, 30), date(2026, 8, 31)),
        revision="all-day-revision",
        title="Day off",
    )
