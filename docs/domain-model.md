# Domain model

The canonical glossary is [CONTEXT.md](../CONTEXT.md). This document explains aggregate boundaries and invariants.

## Directional Sync Rule aggregate

A Directional Sync Rule identifies one source Calendar Endpoint and one destination Calendar Endpoint. Each endpoint combines a Connected Account identity with a provider calendar identity, so a rule may cross Google identities. Rules may form one-to-many or many-to-one topologies, but an exact directional relationship is unique.

The rule owns its Transformation Policy, all-day eligibility, initial lookback, and lifecycle. A new or materially changed rule must pass Rule Preview before enabling.

Invariants:

- Source and destination endpoints cannot be identical.
- Busy-only is the default transformation policy.
- All-day events are included by default and may be excluded per rule.
- Destination content is never authoritative.
- Managed projections are never eligible sources.

## Event Mapping aggregate

An Event Mapping is the durable ownership link between one source Event Reference and one destination Event Reference under one rule. It stores identities, source revision, and a non-reversible Projection Fingerprint, not event content.

Invariants:

- A mapping belongs to exactly one directional rule.
- One source maps to at most one destination under a rule.
- One managed destination maps to at most one source under a rule.
- Update or deletion requires a valid mapping and matching origin metadata.
- Identity ambiguity is a Conflict; content difference is Drift.

## Calendar Event values

A Calendar Event is a transient provider-neutral representation. Its time is either a timezone-aware Timed Interval or an All-Day Range with an exclusive end date. Recurring events retain Event Series, Occurrence, and Occurrence Exception identity so the current pre-alpha policy can exclude them safely until complete series mapping is available.

Attendees, organizer identity, conferencing links, and attachments do not enter an Event Projection. Event content is processed in memory and excluded from operational persistence.

## State machines

```text
Draft -> DryRunValidated -> Enabled -> Paused
                          |     |
                          |     -> Degraded
                          -> Disabled
```

Only a successfully previewed configuration can become Enabled. An Enabled Rule can be Paused from
the Web UI. A Degraded Rule performs no writes until the account is reauthorized and the rule passes
a new recovery preview; re-enabling starts with both preserved incremental positions.
