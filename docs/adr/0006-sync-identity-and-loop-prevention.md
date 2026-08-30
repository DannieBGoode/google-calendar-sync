# Use durable origin identity for ownership and loop prevention

## Context

Users may configure `A -> B` and `B -> A`. Content matching is ambiguous, changes over time, and cannot prove that the application owns a destination event. A projection copied back as a source would create an event loop.

## Decision

Store an Event Mapping in SQLite and durable private origin metadata on every managed provider event. The metadata identifies the rule, source endpoint and event, and stable operation key. Managed projections are never eligible sources. Update and deletion require both mapping ownership and compatible provider metadata.

## Alternatives considered

- Matching title and time would risk deleting unrelated events and fail after transformations.
- An in-memory seen-set would not survive restarts or reverse-rule schedules.
- Hiding a marker in event text would leak implementation detail to users.

## Consequences

Reverse directional rules can coexist without loops, retries can recover external writes, and destructive actions have evidence. Provider metadata becomes a compatibility surface and must migrate deliberately.
