# Backend documentation

These guides describe the current VassilFlow source base: a reusable harness, an embedded FastAPI Gateway runtime, and the shared frontend/channel integrations. The base ships no built-in Office product or product-specific renderer.

Start with [setup](SETUP.md), [architecture](ARCHITECTURE.md), and [configuration](CONFIGURATION.md). For a new agent built directly from this source, read [Python integration](rfc-create-vassilflow-agent.md) and the architecture's extension contracts.

## Conventions

- Repository paths are relative to the checkout root; source links resolve from this directory.
- Commands state their working directory. Bash environment prefixes are not PowerShell syntax.
- Runtime paths such as `{runtime_home}` and IDs in braces are placeholders, not checkout files.
- Examples with model/provider identifiers or external endpoints require deployment-specific values.
- Code defaults, example configuration, and launcher overrides can differ. [Path resolution](PATH_EXAMPLES.md) explains the distinction.
- This review reflects the source on 2026-09-23. Test plans describe procedures, not inherited release-certification claims.

## Core guides

| Guide                                                        | Contents                                                                                          |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| [SETUP.md](SETUP.md)                                         | Full-stack and Gateway-only development                                                           |
| [ARCHITECTURE.md](ARCHITECTURE.md)                           | Harness boundaries, Agent identity, capabilities, Actions, lifecycle, readiness, and repositories |
| [CONFIGURATION.md](CONFIGURATION.md)                         | Configuration loading, defaults, environment, and restart boundaries                              |
| [API.md](API.md)                                             | Gateway routes, authentication, examples, and compatibility limits                                |
| [PATH_EXAMPLES.md](PATH_EXAMPLES.md)                         | Project/runtime roots, owner storage, sandbox paths, and artifact URLs                            |
| [STREAMING.md](STREAMING.md)                                 | Graph modes, SSE, reconnect retention, direct client, and history                                 |
| [middleware-execution-flow.md](middleware-execution-flow.md) | Composition paths and hook ordering                                                               |

## Authentication and channels

| Guide                                                  | Contents                                                             |
| ------------------------------------------------------ | -------------------------------------------------------------------- |
| [AUTH_DESIGN.md](AUTH_DESIGN.md)                       | Sessions, CSRF, internal requests, authorization, and limits         |
| [AUTH_UPGRADE.md](AUTH_UPGRADE.md)                     | Initialization, upgrade, backup, and administrator recovery          |
| [SSO.md](SSO.md)                                       | OIDC configuration and callback behavior                             |
| [IM_CHANNEL_CONNECTIONS.md](IM_CHANNEL_CONNECTIONS.md) | User bindings, bot configuration, owner mapping, and credentials     |
| [AUTH_TEST_PLAN.md](AUTH_TEST_PLAN.md)                 | Automated checks and manual acceptance matrix                        |
| [AUTH_TEST_DOCKER_GAP.md](AUTH_TEST_DOCKER_GAP.md)     | Current container validation checklist; historical filename retained |

## Agent features

| Guide                                                                    | Contents                                                       |
| ------------------------------------------------------------------------ | -------------------------------------------------------------- |
| [FILE_UPLOAD.md](FILE_UPLOAD.md)                                         | Upload API, limits, conversion, and sandbox visibility         |
| [MCP_SERVER.md](MCP_SERVER.md)                                           | MCP transports, discovery, routing, OAuth, and interceptors    |
| [GUARDRAILS.md](GUARDRAILS.md)                                           | Tool-call providers, policy, attribution, and failure behavior |
| [plan_mode_usage.md](plan_mode_usage.md)                                 | Todo tracking and runtime flags                                |
| [task_tool_improvements.md](task_tool_improvements.md)                   | Current delegated-task lifecycle and limits                    |
| [summarization.md](summarization.md)                                     | Context compaction, skill preservation, and history            |
| [AUTO_TITLE_GENERATION.md](AUTO_TITLE_GENERATION.md)                     | Local default and configured model-generated titles            |
| [TITLE_GENERATION_IMPLEMENTATION.md](TITLE_GENERATION_IMPLEMENTATION.md) | Title implementation and regression concerns                   |
| [MEMORY_IMPROVEMENTS.md](MEMORY_IMPROVEMENTS.md)                         | Current memory storage, extraction, injection, and management  |
| [MEMORY_IMPROVEMENTS_SUMMARY.md](MEMORY_IMPROVEMENTS_SUMMARY.md)         | Memory behavior and limitations at a glance                    |
| [MEMORY_SETTINGS_REVIEW.md](MEMORY_SETTINGS_REVIEW.md)                   | Disposable-account UI review procedure                         |
| [memory-settings-sample.json](memory-settings-sample.json)               | Fictional Memory Settings fixture                              |

## Runtime operations and validation

| Guide                                                      | Contents                                             |
| ---------------------------------------------------------- | ---------------------------------------------------- |
| [APPLE_CONTAINER.md](APPLE_CONTAINER.md)                   | Local Apple Container/Docker selection and lifecycle |
| [SANDBOX_MEMORY_PROFILING.md](SANDBOX_MEMORY_PROFILING.md) | Kubernetes workload measurement procedure            |
| [BLOCKING_IO_DETECTION.md](BLOCKING_IO_DETECTION.md)       | Static inventory and async runtime regression checks |
| [REPLAY_E2E.md](REPLAY_E2E.md)                             | Model-free replay and full-stack contract validation |
| [TODO.md](TODO.md)                                         | Current limits and candidate extension work          |

## Implemented design records

The RFC filenames below remain stable for existing links. Their contents describe implemented APIs and remaining boundaries, not unimplemented proposals.

| Guide                                                            | Contents                                               |
| ---------------------------------------------------------------- | ------------------------------------------------------ |
| [rfc-create-vassilflow-agent.md](rfc-create-vassilflow-agent.md) | Factory, RuntimeFeatures, and direct client signatures |
| [rfc-extract-shared-modules.md](rfc-extract-shared-modules.md)   | Shared upload/skill helpers and transport boundaries   |
| [rfc-grep-glob-tools.md](rfc-grep-glob-tools.md)                 | Implemented file-search tools                          |

See also [repository setup](../../docs/SETUP.md), [persistence operations](../../docs/PERSISTENCE.md), [backend contribution guidance](../CONTRIBUTING.md), and [backend package metadata](../pyproject.toml).
