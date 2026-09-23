# Backend setup

VassilFlow is a source base for building agents. The repository contains a reusable Python harness, a FastAPI Gateway with an embedded agent runtime, and a Next.js frontend. It does not ship an Office product or a separate LangGraph server.

All repository paths in these guides are relative to the repository root unless a command explicitly changes directory. See [path resolution](PATH_EXAMPLES.md) before moving runtime data.

## Requirements

Use Python 3.12 or newer and `uv` for the backend. The full application also needs Node.js, the pnpm version pinned in [frontend/package.json](../../frontend/package.json), and nginx. [scripts/check.py](../../scripts/check.py) checks the development prerequisites. Shell scripts require Bash; on Windows, the root Makefile uses the [Git Bash wrapper](../../scripts/run-with-git-bash.cmd).

## Full application

Run from the repository root:

```bash
make setup
make doctor
make dev
```

The setup wizard prepares local configuration. For manual setup, use `make config`, edit the generated `config.yaml` and environment files, and run `make install`. Configuration generation refuses to overwrite existing configuration. `make config-upgrade` merges newer example fields into an existing configuration; review its result.

The development entry point is `http://localhost:2026`. nginx forwards frontend requests to port 3000 and backend requests to Gateway port 8001. `make stop` stops the development services. See the [root Makefile](../../Makefile) for the separate production and Docker commands.

The default local sandbox runs on the host and does not enable bash execution by default. To use an isolated AIO sandbox, configure its provider first, then run `make setup-sandbox` to pull the configured image. See [container runtime selection](APPLE_CONTAINER.md).

## Gateway only

Run from the repository root:

```bash
cd backend
uv sync
uv run uvicorn app.gateway.app:app --host 127.0.0.1 --port 8001 --reload
```

Gateway exposes `/health`, `/health/ready`, `/docs`, and `/openapi.json`. The first reports liveness; readiness checks runtime dependencies and can return 503. A successful liveness response alone does not establish that an agent can run.

Use exactly one Gateway worker. This requirement also applies with PostgreSQL. The stream bridge, active runs, channel workers, and several coordination mechanisms are process-local. `GATEWAY_WORKERS` and `WEB_CONCURRENCY`, when set, must each be `1`.

## Configuration and data

- **Runtime variables**: Use `VASSILFLOW_*` variables for harness-specific settings. Authentication, Gateway, and provider integrations also have their own variables, such as `AUTH_JWT_SECRET`, `GATEWAY_CORS_ORIGINS`, and model API keys.
- **Runtime data**: State defaults to `.vassilflow` under the project root. For standalone harness calls, the project root defaults to the current working directory and can be set with `VASSILFLOW_PROJECT_ROOT`.
- The full-stack `make dev` launcher explicitly sets the project root to the checkout and defaults `VASSILFLOW_HOME` to `backend/.vassilflow`. Compose uses `/app/backend/.vassilflow` inside Gateway. These launcher choices differ from the standalone default.
- `database.sqlite_dir` resolves against the process working directory. Moving `VASSILFLOW_HOME` alone does not move the SQL database. Configure both paths explicitly when relocating state.
- `VASSILFLOW_CONFIG_PATH` selects a configuration file. [Configuration](CONFIGURATION.md) documents loading order, defaults, and restart requirements.

Open the application to initialize the first administrator. No default administrator password is generated at startup. See [authentication operations](AUTH_UPGRADE.md) and [SSO](SSO.md).

## Development checks

From `backend/`:

```bash
uv run pytest tests/test_vassilflow_docs.py -q
uv run pytest tests/ -v
uvx ruff check .
uvx ruff format --check .
```

Some integration tests require explicitly configured external services. For reproducible model-free contract checks, use [record/replay tests](REPLAY_E2E.md). See [blocking I/O checks](BLOCKING_IO_DETECTION.md) when changing asynchronous runtime code.

## Reuse in another project

Keep application-specific tools, prompts, and capability adapters outside the generic harness. Choose the [Python factory or client](rfc-create-vassilflow-agent.md) for direct embedding, or reuse Gateway and its authenticated APIs. The [architecture contract](ARCHITECTURE.md) describes the boundaries to preserve when developing a new agent product from this source base.
