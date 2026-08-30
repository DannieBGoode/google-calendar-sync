# Use directional sync rules

## Context

Calendar synchronization needs explicit authority. A “calendar pair” can hide whether edits, cancellations, and privacy transformations flow one way or both ways.

## Decision

A Directional Sync Rule always relates exactly one source calendar to exactly one destination calendar. Two rules express opposite directions. One-to-many and many-to-one topologies are valid, while an exact directional relationship is unique.

## Alternatives considered

- A bidirectional aggregate would combine two sources of truth and require routine content conflict resolution.
- A many-calendar rule would make ownership, preview, and failure isolation less explicit.

## Consequences

Source authority and audit language stay unambiguous. Reverse rules require durable loop-prevention metadata, and each rule progresses and fails independently.
