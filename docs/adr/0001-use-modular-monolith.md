# Use a modular monolith

## Context

The synchronization, provider integration, identity, reconciliation, and operations responsibilities have distinct language and change drivers, but the initial Raspberry Pi deployment must stay lightweight and easy to operate.

## Decision

Use one repository, deployable application, SQLite database, and Docker Compose service. Preserve bounded-context boundaries in modules and dependency direction rather than network processes.

## Alternatives considered

- Microservices would make independent deployment possible but add networking, distributed consistency, and operational overhead without a current scaling need.
- A single unstructured package would be simple initially but obscure the synchronization domain and let provider concerns spread inward.

## Consequences

All contexts release together and share one process. Internal ports and composition still allow provider or persistence adapters to change without rewriting domain behavior.
