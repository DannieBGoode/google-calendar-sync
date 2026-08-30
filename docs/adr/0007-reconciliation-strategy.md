# Reconcile independently from incremental synchronization

## Context

Provider change feeds optimize incremental work but do not prove every destination projection still exists or matches source authority. Cursor bugs, manual destination changes, and partial failures can create drift.

## Decision

Reconcile mappings touched by every Sync Run, run Full Reconciliation daily, and expose Reconcile Now. Derive expected projections from current sources, fetch managed destination state independently, automatically repair drift, and open incidents rather than guessing when identity is ambiguous.

## Alternatives considered

- Trusting only incremental tokens would leave silent drift undetected.
- Rebuilding every projection on every five-minute poll would consume quota and obscure real failures.
- A report-only reconciler would detect problems but leave routine destination edits unrepaired despite source authority.

## Consequences

Correctness is continuously demonstrated rather than assumed. Full reconciliation adds provider reads and needs account-level rate limiting, while remaining executable separately from the normal sync path.
