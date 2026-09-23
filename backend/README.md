# VassilFlow backend

VassilFlow provides a reusable agent harness and a FastAPI Gateway with an embedded LangGraph runtime. Use the source base to build new agents with shared tools, skills, memory, sandbox access, delegation, persistence, and streaming. The base ships the default lead agent and personal-agent support, with no built-in product agents or Office renderer.

Start with the [backend documentation index](docs/README.md). The [architecture contract](docs/ARCHITECTURE.md) defines Agent identity, capability adapters, Actions, lifecycle hooks, readiness, and repository boundaries for future products.

## Source layout

```text
backend/
  app/
    gateway/                  # HTTP APIs, authentication, runtime composition
    channels/                 # IM integrations and user binding flows
  packages/harness/
    pyproject.toml            # Reusable harness package
    vassilflow/               # Public Python import namespace
      agents/                 # Factories, prompts, middleware, memory
      capabilities/           # Generic capability adapter contracts
      actions/                # Mutation provenance
      config/                 # Configuration and runtime paths
      runtime/                # Runs, streams, checkpoints, lifecycle
      persistence/            # Application and repository contracts
      sandbox/                # Sandbox interfaces, local provider, file tools
      subagents/              # Delegated workers
      tools/                  # Built-in tools
      community/              # Configurable integrations and AIO provider
      mcp/                    # MCP discovery, sessions, and tools
      models/                 # Model adapters and factory
      skills/                 # Skill discovery and installation
      client.py               # Direct in-process client
  tests/
  docs/
```

Application code may import `vassilflow.*`; the harness must not import `app.*`.

## Start Gateway

From the repository root, after preparing configuration:

```bash
cd backend
uv sync
uv run uvicorn app.gateway.app:app --host 127.0.0.1 --port 8001 --reload
```

Gateway exposes `/health`, `/health/ready`, `/docs`, and `/openapi.json`. For the complete application, follow [setup](docs/SETUP.md); nginx on port 2026 routes frontend traffic to port 3000 and API traffic to Gateway on port 8001.

Use one Gateway worker, including with PostgreSQL. `GATEWAY_WORKERS` and `WEB_CONCURRENCY`, when set, must each be `1`. Runtime-home defaults differ between direct embedding and repository launchers, and SQLite has its own directory setting; see [path resolution](docs/PATH_EXAMPLES.md).

The local sandbox runs on the host and disables bash by default. Container-backed execution is a separate provider choice. Token limits use returned provider usage and can overshoot during concurrent work; pending memory extraction is an in-process best-effort queue. The feature guides document these limits rather than promising uniform isolation or durability.

## Build a new agent

Use the [pure-argument factory](docs/rfc-create-vassilflow-agent.md) to compose a model, tools, middleware, and `RuntimeFeatures`, or use `VassilFlowClient` for configuration-driven synchronous embedding. Gateway provides authenticated HTTP/SSE and application lifecycle integration.

Keep product-specific code outside the generic harness. Use the existing capability and policy contracts when adding trusted inputs, specialized tools, domain storage, and frontend extensions.

## Validate changes

From `backend/`:

```bash
uv run pytest tests/ -v
uvx ruff check .
uvx ruff format --check .
```

See [contribution guidance](CONTRIBUTING.md), [blocking I/O checks](docs/BLOCKING_IO_DETECTION.md), and [replay E2E](docs/REPLAY_E2E.md). External-service integration tests require their configured prerequisites; replay tests provide a model-key-free contract check.
