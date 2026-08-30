# Use Vite, React, and shadcn/ui for the Web interface

## Context

The authenticated interface needs guided setup, rule preview, health, incidents, and audit access while preserving one lightweight deployable service. Server rendering and a second production runtime provide little value for a local tool.

## Decision

Build the interface with React and TypeScript through Vite, use shadcn/ui source components, and serve the compiled static assets from FastAPI in the same container. Use TanStack Query for API state.

## Alternatives considered

- Next.js would add a second server runtime and deployment boundary.
- Server-rendered templates would reduce frontend tooling but make the requested shadcn interaction system awkward.
- A separate Web container would complicate local deployment without independent scaling value.

## Consequences

Frontend and backend build pipelines remain distinct but ship as one image. The compiled asset boundary is replaceable, and UI components remain owned source rather than a runtime dependency on a hosted design service.
