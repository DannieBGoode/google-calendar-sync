# Development

## Prerequisites

- Python 3.12
- Node.js 22 or later
- Docker with Compose for container validation

## Setup

```sh
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
cd web && npm ci
```

Run FastAPI on port 8000 and Vite on port 5173. Vite proxies `/api` and `/health` to FastAPI.

## Quality checks

```sh
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/pytest --cov
cd web && npm run typecheck && npm run lint && npm run test && npm run build
```

Fixtures in `tests/fixtures` are synthetic. Never copy provider responses from a personal account into the repository.

## Architecture rules

- Domain code cannot import application, infrastructure, interfaces, or bootstrap modules.
- Application code cannot import concrete adapters.
- Provider dictionaries are translated at the Google adapter boundary.
- Use constructor injection and small protocols; do not introduce a dependency-injection framework.
