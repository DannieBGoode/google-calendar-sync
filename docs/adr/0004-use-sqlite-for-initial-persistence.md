# Use SQLite for initial persistence

## Context

The first deployment target is one self-hosted instance on resource-constrained hardware. It needs durable mappings, cursors, incidents, sessions, and migrations without another service.

## Decision

Use SQLite behind small repository and Unit of Work ports. Enable foreign keys, define explicit uniqueness constraints for mapping invariants, and apply versioned forward migrations at startup.

## Alternatives considered

- PostgreSQL offers greater write concurrency but adds an operational dependency the initial workload does not need.
- Flat JSON files make transactional invariants and upgrades unsafe.

## Consequences

Deployment and backup remain simple. Synchronization for the same installation must respect SQLite's write-concurrency limits; repository contracts allow a future PostgreSQL adapter if evidence justifies it.
