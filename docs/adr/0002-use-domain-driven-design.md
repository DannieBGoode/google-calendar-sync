# Use domain-driven design at the synchronization core

## Context

Most product risk lies in calendar identity, authority, recurrence, deletion ownership, loops, drift, and partial failure rather than HTTP or UI mechanics.

## Decision

Express those rules with provider-independent entities, value objects, state machines, and domain services. Maintain the canonical language in `CONTEXT.md` and keep framework imports outside the domain.

## Alternatives considered

- A provider-script model would ship fewer files but bind correctness to Google response dictionaries and persistence side effects.
- Framework-owned models would make CRUD convenient but turn database or HTTP schemas into the domain model.

## Consequences

Core decisions are fast to test and portable across adapters. Contributors must protect dependency direction and avoid adding abstraction without an actual boundary or invariant.
