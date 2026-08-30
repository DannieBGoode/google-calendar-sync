from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from types import TracebackType
from typing import Self

from calendar_sync.application.ports import (
    AuditEntry,
    AuditRepository,
    EventMappingRepository,
    SyncCursorRepository,
    SyncRuleRepository,
    UnitOfWork,
)
from calendar_sync.domain.model import (
    CalendarEndpoint,
    EventMapping,
    EventRef,
    SyncRule,
    SyncRuleId,
)


@dataclass(slots=True)
class MemoryState:
    rules: dict[SyncRuleId, SyncRule] = field(default_factory=dict)
    mappings: dict[tuple[SyncRuleId, EventRef], EventMapping] = field(default_factory=dict)
    cursors: dict[SyncRuleId, str] = field(default_factory=dict)
    destination_cursors: dict[SyncRuleId, str] = field(default_factory=dict)
    audit: list[AuditEntry] = field(default_factory=list)


class InMemorySyncRuleRepository:
    def __init__(self, state: MemoryState) -> None:
        self._state = state

    def get(self, rule_id: SyncRuleId) -> SyncRule | None:
        return self._state.rules.get(rule_id)

    def list(self) -> tuple[SyncRule, ...]:
        return tuple(self._state.rules.values())

    def add(self, rule: SyncRule) -> None:
        if rule.id in self._state.rules:
            raise KeyError(rule.id)
        self._state.rules[rule.id] = rule

    def save(self, rule: SyncRule) -> None:
        if rule.id not in self._state.rules:
            raise KeyError(rule.id)
        self._state.rules[rule.id] = rule

    def relationship_exists(self, source: CalendarEndpoint, destination: CalendarEndpoint) -> bool:
        return any(
            rule.source == source and rule.destination == destination
            for rule in self._state.rules.values()
        )


class InMemoryEventMappingRepository:
    def __init__(self, state: MemoryState) -> None:
        self._state = state

    def for_source(self, rule_id: SyncRuleId, source: EventRef) -> EventMapping | None:
        return self._state.mappings.get((rule_id, source))

    def for_destination(self, rule_id: SyncRuleId, destination: EventRef) -> EventMapping | None:
        return next(
            (
                mapping
                for mapping in self._state.mappings.values()
                if mapping.rule_id == rule_id and mapping.destination == destination
            ),
            None,
        )

    def for_rule(self, rule_id: SyncRuleId) -> tuple[EventMapping, ...]:
        return tuple(
            mapping for mapping in self._state.mappings.values() if mapping.rule_id == rule_id
        )

    def save(self, mapping: EventMapping) -> None:
        for existing in self._state.mappings.values():
            if (
                existing.rule_id == mapping.rule_id
                and existing.destination == mapping.destination
                and existing.source != mapping.source
            ):
                raise ValueError("managed destination is already mapped to another source")
        self._state.mappings[(mapping.rule_id, mapping.source)] = mapping

    def delete(self, mapping: EventMapping) -> None:
        self._state.mappings.pop((mapping.rule_id, mapping.source), None)


class InMemorySyncCursorRepository:
    def __init__(self, cursors: dict[SyncRuleId, str]) -> None:
        self._cursors = cursors

    def get(self, rule_id: SyncRuleId) -> str | None:
        return self._cursors.get(rule_id)

    def save(self, rule_id: SyncRuleId, cursor: str) -> None:
        self._cursors[rule_id] = cursor


class InMemoryAuditRepository:
    def __init__(self, state: MemoryState) -> None:
        self._state = state

    def append(self, entry: AuditEntry) -> None:
        self._state.audit.append(entry)


class InMemoryUnitOfWork:
    rules: SyncRuleRepository
    mappings: EventMappingRepository
    cursors: SyncCursorRepository
    destination_cursors: SyncCursorRepository
    audit: AuditRepository

    def __init__(self, target: MemoryState) -> None:
        self._target = target
        self._working: MemoryState | None = None
        self._committed = False

    def __enter__(self) -> Self:
        self._working = deepcopy(self._target)
        self.rules = InMemorySyncRuleRepository(self._working)
        self.mappings = InMemoryEventMappingRepository(self._working)
        self.cursors = InMemorySyncCursorRepository(self._working.cursors)
        self.destination_cursors = InMemorySyncCursorRepository(self._working.destination_cursors)
        self.audit = InMemoryAuditRepository(self._working)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return None

    def commit(self) -> None:
        assert self._working is not None
        self._target.rules = self._working.rules
        self._target.mappings = self._working.mappings
        self._target.cursors = self._working.cursors
        self._target.destination_cursors = self._working.destination_cursors
        self._target.audit = self._working.audit
        self._committed = True


class InMemoryUnitOfWorkFactory:
    def __init__(self, state: MemoryState | None = None) -> None:
        self.state = state or MemoryState()

    def __call__(self) -> UnitOfWork:
        return InMemoryUnitOfWork(self.state)
