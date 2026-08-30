# Agent guidance

Read `CONTEXT.md`, `docs/domain-model.md`, and the relevant architecture decision records before
changing synchronization behavior. Preserve the inward dependency direction documented in
`docs/architecture.md`, and never add real credentials or personal calendar data to the repository.

Run the backend and frontend quality checks documented in `README.md` before proposing changes.
Keep provider payloads at the infrastructure boundary and include domain tests when synchronization
behavior changes.
