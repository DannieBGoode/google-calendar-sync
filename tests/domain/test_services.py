from dataclasses import replace

from calendar_sync.domain.model import (
    AllDaySyncPolicy,
    CalendarEvent,
    EventId,
    EventMapping,
    EventMappingId,
    EventRef,
    EventStatus,
    ManagedOrigin,
    PrivacyPolicy,
    Recurrence,
    SyncAction,
    TransformationPolicy,
)
from calendar_sync.domain.services import (
    EventProjector,
    ProjectionFingerprinter,
    ReconciliationService,
    SyncDecisionService,
)
from tests.helpers import all_day_event, event, rule

projector = EventProjector()
fingerprinter = ProjectionFingerprinter()
decisions = SyncDecisionService(projector, fingerprinter)


def _mapping(source: CalendarEvent, destination: CalendarEvent) -> EventMapping:
    projection = projector.project(source, rule())
    return EventMapping(
        EventMappingId("mapping-1"),
        rule().id,
        source.reference,
        destination.reference,
        source.revision,
        fingerprinter.fingerprint(projection),
    )


def _destination(source: CalendarEvent, title: str = "Busy") -> CalendarEvent:
    return CalendarEvent(
        EventRef(rule().destination, EventId("destination-event")),
        source.time,
        "destination-revision",
        title=title,
        managed_origin=ManagedOrigin(rule().id, source.reference),
    )


def test_busy_only_projection_omits_private_content() -> None:
    projection = projector.project(event(), rule())

    assert projection.title == "Busy"
    assert projection.description == ""
    assert projection.location == ""


def test_details_policy_is_rule_wide() -> None:
    details_rule = replace(
        rule(), transformation=TransformationPolicy(privacy=PrivacyPolicy.COPY_DETAILS)
    )

    projection = projector.project(event(), details_rule)

    assert projection.title == "Private appointment"
    assert projection.description == "Sensitive description"


def test_destination_drift_is_overwritten_not_conflicted() -> None:
    source = event()
    destination = _destination(source, title="Edited on destination")

    decision = decisions.decide(rule(), source, _mapping(source, destination), destination)

    assert decision.action is SyncAction.UPDATE
    assert decision.projection is not None
    assert decision.projection.title == "Busy"


def test_current_projection_is_ignored() -> None:
    source = event()
    destination = _destination(source)

    decision = decisions.decide(rule(), source, _mapping(source, destination), destination)

    assert decision.action is SyncAction.IGNORE


def test_cancelled_mapped_source_deletes_owned_projection() -> None:
    source = replace(event(), status=EventStatus.CANCELLED)
    destination = _destination(source)

    decision = decisions.decide(rule(), source, _mapping(source, destination), destination)

    assert decision.action is SyncAction.DELETE


def test_mismatched_destination_origin_blocks_update_and_delete() -> None:
    source = event()
    wrong_origin = event("different-source").reference
    destination = replace(
        _destination(source, title="Edited"),
        managed_origin=ManagedOrigin(rule().id, wrong_origin),
    )
    mapping = _mapping(source, destination)

    update = decisions.decide(rule(), source, mapping, destination)
    deletion = decisions.decide(
        rule(), replace(source, status=EventStatus.CANCELLED), mapping, destination
    )

    assert update.action is SyncAction.CONFLICT
    assert deletion.action is SyncAction.CONFLICT
    assert "ownership metadata" in update.reason


def test_excluded_all_day_event_is_not_created() -> None:
    exclude_rule = replace(
        rule(),
        transformation=TransformationPolicy(all_day=AllDaySyncPolicy.EXCLUDE),
    )

    decision = decisions.decide(exclude_rule, all_day_event(), None, None)

    assert decision.action is SyncAction.IGNORE


def test_managed_projection_cannot_become_a_source() -> None:
    source = replace(event(), managed_origin=ManagedOrigin(rule().id, event().reference))

    decision = decisions.decide(rule(), source, None, None)

    assert decision.action is SyncAction.IGNORE
    assert "cannot become sources" in decision.reason


def test_recurring_event_is_blocked_until_series_mapping_is_supported() -> None:
    source = replace(event(), recurrence=Recurrence(("RRULE:FREQ=WEEKLY",)))

    decision = decisions.decide(rule(), source, None, None)

    assert decision.action is SyncAction.CONFLICT
    assert "not supported yet" in decision.reason


def test_reconciliation_reports_missing_and_unexpected_events() -> None:
    source = event()
    destination = _destination(source)
    mapping = _mapping(source, destination)
    unexpected = replace(
        destination,
        reference=EventRef(rule().destination, EventId("unexpected-managed")),
    )
    service = ReconciliationService(fingerprinter)

    report = service.reconcile(
        rule(),
        [mapping],
        {source.reference: projector.project(source, rule())},
        {unexpected.reference: unexpected},
    )

    assert {item.kind.value for item in report.drift} == {"missing", "unexpected"}
