# Backend configuration

The canonical schema is [AppConfig](../packages/harness/vassilflow/config/app_config.py), with section models in [config/](../packages/harness/vassilflow/config/). The annotated [config.example.yaml](../../config.example.yaml) is a starting configuration, not a statement that every displayed feature is enabled by default. Its current `config_version` is 21.

## Loading order

`AppConfig.from_file()` selects an explicit path first, then `VASSILFLOW_CONFIG_PATH`, then `config.yaml` under the caller's project root. Repository compatibility fallbacks search the backend/repository locations. Pin the path when embedding the harness or running a service from a different directory.

`VASSILFLOW_PROJECT_ROOT` sets the caller project root; otherwise it is the current working directory. `.env` loading and `$VARIABLE` substitution supply secret values. A configuration string beginning with `$` is resolved as an environment reference; missing variables fail configuration loading. This is not shell expansion. Keep secret-bearing local files out of version control.

Most missing optional sections use their Pydantic defaults. A required `sandbox` section must be valid. Unknown top-level fields are allowed for extension configuration, so a misspelled optional key may not fail validation.

## Minimal configuration

This local example uses a placeholder model identifier. Replace `your-provider-model` with a model supported by your provider and supply `OPENAI_API_KEY` before starting:

```yaml
config_version: 21
models:
  - name: primary
    use: langchain_openai:ChatOpenAI
    model: your-provider-model
    api_key: $OPENAI_API_KEY
sandbox:
  use: vassilflow.sandbox.local:LocalSandboxProvider
database:
  backend: sqlite
  sqlite_dir: .vassilflow/data
run_events:
  backend: db
```

Run Gateway from `backend/` for this relative SQLite directory to resolve to `backend/.vassilflow/data`. A database filename of `vassilflow.db` is appended. `database.backend` supports `memory`, `sqlite`, and `postgres`.

There are two distinct defaults: constructing `DatabaseConfig()` in Python defaults to `memory`; loading a config file with the database section absent defaults to `sqlite`. Run events separately default to `memory`, so select `run_events.backend: db` or `jsonl` if event history must survive a restart. Checkpoints, run events, and filesystem artifacts are different stores.

## Models and tools

A model's `name` is the configuration lookup key used by requests, title generation, memory, summarization, and subagents. `use` is an importable `module:object` adapter. Remaining provider arguments, supported capabilities, and credential loading are adapter-specific; see [model_config.py](../packages/harness/vassilflow/config/model_config.py) and [models/](../packages/harness/vassilflow/models/). Do not assume every adapter supports every provider option.

Tools use importable `use` paths and named tool groups. Keep new product-specific implementations in your application package and register them through configuration or the agent factory. Generic file tools, web integrations, MCP, skills, and subagent delegation do not require an Office product module.

The Codex and Claude model adapters can use their respective local credential loaders. Their presence in a host home directory does not make those credentials available inside Docker. Inspect the optional Compose credential mounts before enabling them; the default stack does not mount the entire host credential directories.

## Section reference

The table describes code defaults, unless explicitly identified as an example-file choice. Follow each source link for complete fields and constraints.

| Section                | Purpose and default behavior                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `log_level`            | `info`; startup logging configuration                                                                                    |
| `max_recursion_limit`  | `1000`; graph recursion ceiling                                                                                          |
| `models`               | Configured model list; empty in the base schema                                                                          |
| `sandbox`              | Required provider configuration; example uses the local provider                                                         |
| `tools`, `tool_groups` | Tool imports and grouping                                                                                                |
| `skills`               | Skill directories and container paths; [schema](../packages/harness/vassilflow/config/skills_config.py)                  |
| `skill_scan`           | Scanning and skill-content limits; [schema](../packages/harness/vassilflow/config/skill_scan_config.py)                  |
| `skill_evolution`      | Skill change workflow; [schema](../packages/harness/vassilflow/config/skill_evolution_config.py)                         |
| `extensions`           | Extension configuration loading; [MCP guide](MCP_SERVER.md)                                                              |
| `tool_output`          | Tool-result size handling; [schema](../packages/harness/vassilflow/config/tool_output_config.py)                         |
| `tool_search`          | Deferred tool discovery; [schema](../packages/harness/vassilflow/config/tool_search_config.py)                           |
| `title`                | Enabled; local title fallback unless `model_name` is explicitly set; [guide](AUTO_TITLE_GENERATION.md)                   |
| `summarization`        | Disabled; context compaction thresholds and retained messages; [guide](summarization.md)                                 |
| `memory`               | Enabled with injection enabled; 30-second debounce, 100 facts, confidence threshold 0.7; [guide](MEMORY_IMPROVEMENTS.md) |
| `token_usage`          | Reporting controls; [schema](../packages/harness/vassilflow/config/token_usage_config.py)                                |
| `token_budget`         | Disabled; when enabled, default total limit 200,000 tokens; [details below](#token-accounting-and-budgets)               |
| `agents_api`           | Personal-agent API controls; [schema](../packages/harness/vassilflow/config/agents_api_config.py)                        |
| `acp_agents`           | External ACP workers; [schema](../packages/harness/vassilflow/config/acp_config.py)                                      |
| `subagents`            | Built-in overrides and custom workers; [guide](task_tool_improvements.md)                                                |
| `guardrails`           | Disabled; provider-based tool authorization; [guide](GUARDRAILS.md)                                                      |
| `suggestions`          | Follow-up suggestions; [schema](../packages/harness/vassilflow/config/suggestions_config.py)                             |
| `circuit_breaker`      | Runtime failure limiting; defined in [AppConfig](../packages/harness/vassilflow/config/app_config.py)                    |
| `loop_detection`       | Repeated tool-call detection; [schema](../packages/harness/vassilflow/config/loop_detection_config.py)                   |
| `read_before_write`    | File editing checks; [schema](../packages/harness/vassilflow/config/read_before_write_config.py)                         |
| `tool_progress`        | Tool progress events; [schema](../packages/harness/vassilflow/config/tool_progress_config.py)                            |
| `safety_finish_reason` | Provider safety-stop handling; [schema](../packages/harness/vassilflow/config/safety_finish_reason_config.py)            |
| `auth`                 | OIDC configuration, disabled by default; local session authentication is configured separately; [SSO](SSO.md)            |
| `database`             | Unified SQL/checkpointer backend; file-loading default is SQLite                                                         |
| `checkpointer`         | Optional legacy checkpointer configuration; prefer the unified database section                                          |
| `run_events`           | `memory`, `db`, or `jsonl`; default `memory`                                                                             |
| `stream_bridge`        | Optional; defaults to in-process memory, queue size 256. Redis is declared in the schema but is not implemented          |
| `channels`             | Deployment-level IM bot configuration; [guide](IM_CHANNEL_CONNECTIONS.md)                                                |
| `channel_connections`  | User-owned channel binding controls; [guide](IM_CHANNEL_CONNECTIONS.md)                                                  |
| `uploads`              | Gateway upload limits and optional document conversion; [guide](FILE_UPLOAD.md)                                          |

## Token accounting and budgets

```yaml
token_budget:
  enabled: true
  max_tokens: 200000
  max_input_tokens: null
  max_output_tokens: null
  warn_threshold: 0.8
  hard_stop_threshold: 1.0
```

Limits use usage metadata returned by providers. They are checked after responses, so an individual response or concurrent child activity can overshoot a limit. They are not a prepaid or globally reserved token pool.

The lead graph aggregates reported child usage before its budget hook decides whether to allow further tools. Each subagent graph receives its own budget middleware when globally enabled. Accounting remains enabled for enforcement when `token_usage.enabled` is false; reporting and attribution controlled by that flag remain disabled. The middleware order matters; see [execution flow](middleware-execution-flow.md).

## Sandbox choices

- `vassilflow.sandbox.local:LocalSandboxProvider`: host filesystem tools; shell execution is disabled unless explicitly enabled. This is not container isolation.
- `vassilflow.community.aio_sandbox:AioSandboxProvider`: container-backed AIO implementation, with local Docker/Apple runtime and provisioner modes. See [provider source](../packages/harness/vassilflow/community/aio_sandbox/aio_sandbox_provider.py).

Set `VASSILFLOW_SANDBOX_BIND_HOST` explicitly when the Gateway-to-sandbox network layout requires a reachable address. Local container ports default to loopback; Docker-outside-of-Docker uses a different host-routing path. Binding `0.0.0.0` exposes the port on all host interfaces and requires appropriate network restrictions.

Keep project root, runtime home, host mount source, and SQLite directory distinct. [Path examples](PATH_EXAMPLES.md) documents them precisely.

## Environment variables

Runtime variables use the `VASSILFLOW_*` names below. These names do not replace the separate authentication, Gateway, and provider variables.

- `VASSILFLOW_PROJECT_ROOT` - Caller project root for project-relative resources.
- `VASSILFLOW_HOME` - Runtime state directory.
- `VASSILFLOW_CONFIG_PATH` - Configuration file path.
- `VASSILFLOW_EXTENSIONS_CONFIG_PATH` - Extension configuration file path.
- `VASSILFLOW_SKILLS_PATH` - Skills directory override.
- `VASSILFLOW_HOST_BASE_DIR` - Host-visible counterpart of runtime home for container bind mounts.
- `VASSILFLOW_SANDBOX_BIND_HOST` - Sandbox port binding override.
- `VASSILFLOW_AUTH_DISABLED` - Explicit local authentication bypass; see [authentication](AUTH_DESIGN.md).
- `VASSILFLOW_INTERNAL_AUTH_TOKEN` - Shared internal Gateway token override; otherwise process-generated.
- `AUTH_JWT_SECRET` - Session signing secret; otherwise persisted in runtime home's `.jwt_secret`.
- `AUTH_TRUSTED_PROXIES` - Trusted proxy addresses/networks for login client-IP handling.
- `GATEWAY_CORS_ORIGINS` - Allowed browser origins for a split frontend/Gateway deployment.
- `GATEWAY_WORKERS`, `WEB_CONCURRENCY` - Must each be `1` if supplied.

## Reload and restart

Request-scoped configuration can be reloaded for subsequent runs; it does not rebuild startup resources. Restart Gateway after changing `database`, `checkpointer`, `run_events`, `stream_bridge`, `sandbox`, `log_level`, `channels`, or `channel_connections`. The authoritative registry is [reload_boundary.py](../packages/harness/vassilflow/config/reload_boundary.py). Environment changes also require restarting the process that consumes them.

## PostgreSQL and upgrades

PostgreSQL shares a database URL between application persistence and the checkpointer, with separate connection pools. From `backend/`, run `uv sync --extra postgres`; the [backend extra](../pyproject.toml) includes the [harness PostgreSQL extra](../packages/harness/pyproject.toml). Then set `database.backend: postgres` and `database.postgres_url: $DATABASE_URL`. PostgreSQL does not enable multiple Gateway workers.

Version 21 removes legacy built-in Office tool registrations. Generic uploads and document conversion remain available. Back up persistent SQL and runtime files before an upgrade; use the registered migration/repair tools described in [architecture](ARCHITECTURE.md), and inspect their plans before applying changes.
