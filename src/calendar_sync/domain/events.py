from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from calendar_sync.domain.model import SyncRuleId


class DomainEvent(Protocol):
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class SyncCompleted:
    rule_id: SyncRuleId
    occurred_at: datetime
    created: int
    updated: int
    deleted: int
    ignored: int


@dataclass(frozen=True, slots=True)
class SyncFailed:
    rule_id: SyncRuleId
    occurred_at: datetime
    category: str
    detail: str


@dataclass(frozen=True, slots=True)
class ReconciliationCompleted:
    rule_id: SyncRuleId
    occurred_at: datetime
    drift_count: int
