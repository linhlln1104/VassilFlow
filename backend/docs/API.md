# Gateway API reference

This is the reference for the VassilFlow backend APIs implemented by [app/gateway](../app/gateway/). Gateway embeds the agent runtime; its LangGraph-compatible endpoints are a supported subset, not a complete LangGraph Platform implementation.

## Addresses and schema

| Access path                         | Address                                        |
| ----------------------------------- | ---------------------------------------------- |
| Full application through nginx      | `http://localhost:2026`                        |
| Direct Gateway in local development | `http://localhost:8001`                        |
| Native API prefix                   | `/api`                                         |
| nginx compatibility prefix          | `/api/langgraph` (rewritten to Gateway `/api`) |
| Interactive OpenAPI documentation   | Gateway `/docs`                                |
| Machine-readable schema             | Gateway `/openapi.json`                        |

The route inventory below was checked against `app.openapi()` on 2026-09-23. Use the running Gateway's schema for all request fields, response models, query parameters, and validation constraints. Proxy routing is defined in [docker/nginx](../../docker/nginx/).

## Authentication and ownership

Most API routes require the `access_token` HttpOnly session cookie. Local login uses form fields `username` (email) and `password`. Registration and first-administrator initialization use JSON. The JWT is not returned in the login response body.

Mutating authenticated requests normally also need a `csrf_token` cookie and a matching `X-CSRF-Token` header. Browser clients must send credentials to Gateway. Login, logout, registration, and initialization use the bootstrap origin checks instead of the normal double-submit requirement. See [authentication design](AUTH_DESIGN.md) for exceptions and internal channel authentication.

Thread, run, artifact, memory, and personal-agent access use the effective owner from authentication. A supplied user ID or metadata field does not grant ownership. Administrator-only configuration routes additionally check role. Consult the route's permission decorator, not just whether OpenAPI displays a security scheme.

## Create a thread and run

Run this Python example from an environment with `httpx` installed. It assumes an existing local account and a configured model. It prompts for credentials and performs a real model run:

```python
from getpass import getpass

import httpx

with httpx.Client(base_url="http://localhost:8001", timeout=180) as client:
    response = client.post(
        "/api/v1/auth/login/local",
        data={"username": input("Email: "), "password": getpass()},
    )
    response.raise_for_status()
    client.headers["X-CSRF-Token"] = client.cookies["csrf_token"]

    response = client.post("/api/threads", json={"assistant_id": "lead_agent"})
    response.raise_for_status()
    thread_id = response.json()["thread_id"]

    response = client.post(
        f"/api/threads/{thread_id}/runs/wait",
        json={"input": {"messages": [{"role": "user", "content": "Hello"}]}},
    )
    response.raise_for_status()
    print(response.json())
```

`assistant_id` binds the thread to its canonical Agent identity. The default is `lead_agent`; select other available identities from `/api/agent-catalog`. A run cannot rebind an existing thread by changing metadata or runtime context. The shipped built-in product-agent registry is empty; personal agents and delegated workers are distinct concepts.

Use `/runs/stream` for SSE and `/runs/wait` for a completed state response. `/runs` creates a background run. Check the final run status rather than interpreting HTTP acceptance as successful agent completion. See [streaming semantics](STREAMING.md).

## Compatibility limits

- Supported multitask strategies are `reject`, `interrupt`, and `rollback`; `enqueue` is declared in the request schema but is not implemented.
- `webhook`, `after_seconds`, `feedback_keys`, and `stream_resumable` are compatibility request fields without the corresponding full Platform delivery, scheduling, feedback-registration, or durable replay service. Do not build those guarantees around their presence in OpenAPI.
- Gateway does not support the graph `events` streaming mode. Its persisted run-event endpoints are a different API.
- Active runs and the memory stream bridge require one Gateway worker. PostgreSQL persistence does not change this limit.

## Pagination and history

Thread search uses a JSON body with `limit` and `offset`; the current schema permits limits from 1 to 1000. Follow the actual response and pagination headers. Run and message endpoints have their own pagination contracts; they are not interchangeable with thread search.

Runs are listed newest first. Frontend history reconstruction must order runs and messages deliberately and preserve current messages if an older-page request fails. A graph checkpoint may contain only compacted context; persisted run messages supply earlier history when configured. See [summarization](summarization.md) and [replay tests](REPLAY_E2E.md).

## Deletion and local files

Remove VassilFlow-managed local thread files through the authenticated thread deletion API, which coordinates core thread state and registered lifecycle hooks. Do not implement deletion as a direct directory removal.

`runtime_home` defaults to `.vassilflow` under the caller project root; repository launchers can override it. Authenticated files are under `{runtime_home}/users/{user_id}/threads/{thread_id}/`. See [path resolution](PATH_EXAMPLES.md) and [durable lifecycle behavior](ARCHITECTURE.md).

## Route inventory

Methods and paths below are the native Gateway surface. A route's presence does not bypass feature configuration, permissions, or external-service requirements.

| Method | Path                                                            | Operation                           |
| ------ | --------------------------------------------------------------- | ----------------------------------- |
| GET    | `/api/models`                                                   | List All Models                     |
| GET    | `/api/models/{model_name}`                                      | Get Model Details                   |
| GET    | `/api/mcp/config`                                               | Get MCP Configuration               |
| PUT    | `/api/mcp/config`                                               | Update MCP Configuration            |
| POST   | `/api/mcp/cache/reset`                                          | Reset MCP Tools Cache               |
| GET    | `/api/memory`                                                   | Get Memory Data                     |
| DELETE | `/api/memory`                                                   | Clear All Memory Data               |
| POST   | `/api/memory/reload`                                            | Reload Memory Data                  |
| POST   | `/api/memory/facts`                                             | Create Memory Fact                  |
| DELETE | `/api/memory/facts/{fact_id}`                                   | Delete Memory Fact                  |
| PATCH  | `/api/memory/facts/{fact_id}`                                   | Patch Memory Fact                   |
| GET    | `/api/memory/export`                                            | Export Memory Data                  |
| POST   | `/api/memory/import`                                            | Import Memory Data                  |
| GET    | `/api/memory/config`                                            | Get Memory Configuration            |
| GET    | `/api/memory/status`                                            | Get Memory Status                   |
| GET    | `/api/skills`                                                   | List All Skills                     |
| POST   | `/api/skills/install`                                           | Install Skill                       |
| GET    | `/api/skills/custom`                                            | List Custom Skills                  |
| GET    | `/api/skills/custom/{skill_name}`                               | Get Custom Skill Content            |
| PUT    | `/api/skills/custom/{skill_name}`                               | Edit Custom Skill                   |
| DELETE | `/api/skills/custom/{skill_name}`                               | Delete Custom Skill                 |
| GET    | `/api/skills/custom/{skill_name}/history`                       | Get Custom Skill History            |
| POST   | `/api/skills/custom/{skill_name}/rollback`                      | Rollback Custom Skill               |
| GET    | `/api/skills/{skill_id}`                                        | Get Skill Details                   |
| PUT    | `/api/skills/{skill_id}`                                        | Update Skill                        |
| GET    | `/api/threads/{thread_id}/artifacts/{path}`                     | Get Artifact File                   |
| POST   | `/api/threads/{thread_id}/uploads`                              | Upload Files                        |
| GET    | `/api/threads/{thread_id}/uploads/limits`                       | Get Upload Limits                   |
| GET    | `/api/threads/{thread_id}/uploads/list`                         | List Uploaded Files                 |
| DELETE | `/api/threads/{thread_id}/uploads/{filename}`                   | Delete Uploaded File                |
| DELETE | `/api/threads/{thread_id}`                                      | Delete Thread Data                  |
| PATCH  | `/api/threads/{thread_id}`                                      | Patch Thread                        |
| GET    | `/api/threads/{thread_id}`                                      | Get Thread                          |
| POST   | `/api/threads`                                                  | Create Thread                       |
| POST   | `/api/threads/{thread_id}/branches`                             | Branch Thread                       |
| POST   | `/api/threads/search`                                           | Search Threads                      |
| GET    | `/api/threads/{thread_id}/state`                                | Get Thread State                    |
| POST   | `/api/threads/{thread_id}/state`                                | Update Thread State                 |
| POST   | `/api/threads/{thread_id}/compact`                              | Compact Thread                      |
| POST   | `/api/threads/{thread_id}/history`                              | Get Thread History                  |
| GET    | `/api/agent-catalog`                                            | List Agent Catalog                  |
| GET    | `/api/agents`                                                   | List Agents                         |
| POST   | `/api/agents`                                                   | Create Custom Agent                 |
| GET    | `/api/agents/check`                                             | Check Agent Name                    |
| GET    | `/api/agents/{name}`                                            | Get Agent                           |
| PUT    | `/api/agents/{name}`                                            | Update Custom Agent                 |
| DELETE | `/api/agents/{name}`                                            | Delete Custom Agent                 |
| GET    | `/api/user-profile`                                             | Get User Profile                    |
| PUT    | `/api/user-profile`                                             | Update User Profile                 |
| GET    | `/api/actions`                                                  | List Actions                        |
| GET    | `/api/actions/{action_id}`                                      | Get Action                          |
| GET    | `/api/suggestions/config`                                       | Get Suggestions Configuration       |
| POST   | `/api/threads/{thread_id}/suggestions`                          | Generate Follow-up Questions        |
| GET    | `/api/channels/providers`                                       | Get Channel Providers               |
| GET    | `/api/channels/connections`                                     | Get Channel Connections             |
| DELETE | `/api/channels/connections/{connection_id}`                     | Disconnect Channel Connection       |
| DELETE | `/api/channels/{provider}/runtime-config`                       | Disconnect Channel Provider Runtime |
| POST   | `/api/channels/{provider}/runtime-config`                       | Configure Channel Provider Runtime  |
| POST   | `/api/channels/{provider}/connect`                              | Connect Channel Provider            |
| GET    | `/api/channels/`                                                | Get Channels Status                 |
| POST   | `/api/channels/{name}/restart`                                  | Restart Channel                     |
| GET    | `/api/console/stats`                                            | Console Stats                       |
| GET    | `/api/console/runs`                                             | List Runs Across Threads            |
| GET    | `/api/console/usage`                                            | Token Usage Over Time               |
| POST   | `/api/assistants/search`                                        | Search Assistants                   |
| GET    | `/api/assistants/{assistant_id}`                                | Get Assistant Compat                |
| GET    | `/api/assistants/{assistant_id}/graph`                          | Get Assistant Graph                 |
| GET    | `/api/assistants/{assistant_id}/schemas`                        | Get Assistant Schemas               |
| POST   | `/api/v1/auth/login/local`                                      | Login Local                         |
| POST   | `/api/v1/auth/register`                                         | Register                            |
| POST   | `/api/v1/auth/logout`                                           | Logout                              |
| POST   | `/api/v1/auth/change-password`                                  | Change Password                     |
| GET    | `/api/v1/auth/me`                                               | Get Me                              |
| GET    | `/api/v1/auth/setup-status`                                     | Setup Status                        |
| POST   | `/api/v1/auth/initialize`                                       | Initialize Admin                    |
| GET    | `/api/v1/auth/providers`                                        | List Auth Providers                 |
| GET    | `/api/v1/auth/oauth/{provider}`                                 | Oauth Login                         |
| GET    | `/api/v1/auth/callback/{provider}`                              | Oauth Callback                      |
| PUT    | `/api/threads/{thread_id}/runs/{run_id}/feedback`               | Upsert Feedback                     |
| DELETE | `/api/threads/{thread_id}/runs/{run_id}/feedback`               | Delete Run Feedback                 |
| POST   | `/api/threads/{thread_id}/runs/{run_id}/feedback`               | Create Feedback                     |
| GET    | `/api/threads/{thread_id}/runs/{run_id}/feedback`               | List Feedback                       |
| GET    | `/api/threads/{thread_id}/runs/{run_id}/feedback/stats`         | Feedback Stats                      |
| DELETE | `/api/threads/{thread_id}/runs/{run_id}/feedback/{feedback_id}` | Delete Feedback                     |
| POST   | `/api/threads/{thread_id}/runs/regenerate/prepare`              | Prepare Regenerate Run              |
| POST   | `/api/threads/{thread_id}/runs`                                 | Create Run                          |
| GET    | `/api/threads/{thread_id}/runs`                                 | List Runs                           |
| POST   | `/api/threads/{thread_id}/runs/stream`                          | Stream Run                          |
| POST   | `/api/threads/{thread_id}/runs/wait`                            | Wait Run                            |
| GET    | `/api/threads/{thread_id}/runs/{run_id}`                        | Get Run                             |
| POST   | `/api/threads/{thread_id}/runs/{run_id}/cancel`                 | Cancel Run                          |
| GET    | `/api/threads/{thread_id}/runs/{run_id}/join`                   | Join Run                            |
| POST   | `/api/threads/{thread_id}/runs/{run_id}/stream`                 | Stream Existing Run                 |
| GET    | `/api/threads/{thread_id}/runs/{run_id}/stream`                 | Stream Existing Run                 |
| GET    | `/api/threads/{thread_id}/messages`                             | List Thread Messages                |
| GET    | `/api/threads/{thread_id}/runs/{run_id}/messages`               | List Run Messages                   |
| GET    | `/api/threads/{thread_id}/runs/{run_id}/events`                 | List Run Events                     |
| GET    | `/api/threads/{thread_id}/runs/{run_id}/workspace-changes`      | Get Run Workspace Changes           |
| GET    | `/api/threads/{thread_id}/token-usage`                          | Thread Token Usage                  |
| POST   | `/api/runs/stream`                                              | Stateless Stream                    |
| POST   | `/api/runs/wait`                                                | Stateless Wait                      |
| GET    | `/api/runs/{run_id}/messages`                                   | Run Messages                        |
| GET    | `/api/runs/{run_id}/feedback`                                   | Run Feedback                        |
| GET    | `/health`                                                       | Health Check                        |
| GET    | `/health/ready`                                                 | Readiness Check                     |

## Related guides

- [Uploads and conversion](FILE_UPLOAD.md)
- [MCP configuration](MCP_SERVER.md)
- [Memory behavior](MEMORY_IMPROVEMENTS.md)
- [IM channel bindings](IM_CHANNEL_CONNECTIONS.md)
- [Authentication validation](AUTH_TEST_PLAN.md)

New endpoints belong in this inventory only after their router is mounted in [app.py](../app/gateway/app.py). Regenerate the OpenAPI inventory without starting the application lifespan when a route changes, then review implementation-specific behavior separately.
