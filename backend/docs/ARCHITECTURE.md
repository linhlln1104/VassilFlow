# Backend Architecture

This document is the canonical architecture contract for the VassilFlow
backend. It describes stable ownership and dependency boundaries rather than
enumerating every middleware, tool, or route. Feature-specific behavior belongs
in the linked documents at the end. Repository paths are relative to the checkout
root; public Python imports use `vassilflow.*`. For direct source reuse, start
with the [factory and client guide](rfc-create-vassilflow-agent.md).

## Design Goals

VassilFlow is a reusable agent harness. The base distribution provides the
default lead Agent, personal Agents, and delegated workers, with zero built-in
product Agents. A specialized Agent can add tools, trusted inputs, middleware,
readiness checks, and domain storage through the retained extension contracts
without creating a second execution runtime.

The architecture is designed to preserve these properties:

- one thread, run, stream, checkpoint, memory, sandbox, and tool runtime;
- server-owned Agent identity and policy;
- domain packages behind generic capability and repository contracts;
- durable domain projects that do not depend on one conversation;
- explicit provenance for mutations outside conversational run status;
- a shared frontend chat shell with reviewed local domain extensions;
- fail-closed authorization, integrity checks, and runtime readiness.

## System Topology

```text
Browser, SDK clients, and IM channels
                  |
                  v
        Nginx entry point :2026
          |             |
          |             +----------------------+
          v                                    v
  Gateway API :8001                     Next.js UI :3000
  - REST and SSE                        - Agent catalog
  - LangGraph-compatible API            - Shared chat shell
  - embedded Agent runtime              - Personal Agent management
  - extension composition
          |
          +-------------------+--------------------+
          |                   |                    |
          v                   v                    v
  Application database   VASSILFLOW_HOME     External services
  - users and threads    - workspaces        - model providers
  - run/checkpoint data  - Action journal    - MCP/search providers
                         - lifecycle journal  - sandbox/provisioner
```

Nginx routes `/api/langgraph/*` to the Gateway's compatible `/api/*` runtime
surface, routes other `/api/*` requests to the Gateway, and serves the frontend
for non-API routes. The default deployment does not require a separate
LangGraph server.

The base has no product-specific renderer, project/template API, or domain
workspace. External services are configured only for the enabled runtime tools
and providers.

## Dependency Direction

```text
frontend
   |
   | HTTP/SSE contracts
   v
app/gateway
   |
   | imports and composes
   v
packages/harness/vassilflow
   |
   +-- generic runtime contracts
   |     agents, actions, capabilities, persistence, runtime
   |
   `-- optional integrations
         community/* and downstream domain packages
```

The dependency rules are:

1. The harness package never imports `app.*`.
2. Generic runtime modules do not statically import concrete domain implementations.
3. Domain packages may depend on generic harness contracts, but not on Gateway
   routers or request objects.
4. Gateway composition roots and domain routers may import concrete domain
   implementations.
5. Built-in capability adapters are loaded only from server-owned definitions.
6. Frontend catalog metadata may select only a locally registered extension.
   It cannot load arbitrary remote components.

The important composition roots are:

- [backend/app/gateway/app.py](../app/gateway/app.py) for routers, runtime services, and health;
- [backend/app/gateway/domain_lifecycle.py](../app/gateway/domain_lifecycle.py) for enabled lifecycle handlers;
- `vassilflow.config.builtin_agents` for curated Agent definitions;
- `vassilflow.persistence.repository_registry` for operational repositories;
- [frontend/src/components/workspace/agents/agent-chat-extension.tsx](../../frontend/src/components/workspace/agents/agent-chat-extension.tsx) for
  reviewed chat extensions.

## Two-Plane Model

VassilFlow has one execution runtime. The retained domain contracts allow an
extension to add a separate project state plane when needed; the base does not
ship a project product.

| Plane                  | Owns                                                                                     | Source of truth                                            |
| ---------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Conversation execution | Threads, messages, runs, checkpoints, stream state, thread files, model/tool execution   | Gateway runtime stores, checkpointer, and thread workspace |
| Domain project         | Projects, immutable revisions, templates, reviews, final selections, and render evidence | Domain repository and canonical domain artifacts           |

### Conversation Execution Plane

```text
assistant_id
     |
     v
canonical Agent identity
     |
     +--> server-owned runtime policy
     +--> trusted capability input resolution
     +--> required readiness enforcement
     |
     v
RunRecord -> embedded Agent runtime -> model/middleware/tools -> SSE/events
```

The conversation plane owns execution. It resolves the model, tools, skills,
memory, sandbox, middleware, streaming, and checkpoint state. Built-in and
personal Agents reuse this same path.

`assistant_id` is the authoritative external Agent identity. Client-supplied
copies in metadata or context are rejected when they conflict. A thread remains
bound to its canonical assistant identity after creation.

### Domain Project Plane

```text
Domain tool or authenticated domain API
                  |
                  v
       domain service and integrity checks
                  |
          +-------+--------+
          |                |
          v                v
   immutable Action   canonical project
   start/outcome      revision or template
                           |
                           v
                  derived render evidence
```

A domain extension can own durable product state that survives conversation
deletion or branching. The following are design constraints for such an
extension, not built-in product functionality:

- source and result hashes bind every committed revision;
- revisions are immutable and append-only;
- restore creates another revision rather than changing history;
- review and final selection are explicit records;
- render evidence is derived from one exact revision;
- a thread output is a materialized working copy, not the project source of
  truth.

### Links Between The Planes

The planes are linked explicitly but are not one transaction:

- Action records can reference thread, run, project, revision, artifact, and
  object-path identities.
- Domain projects can retain attached or detached conversation links.
- Materialization records describe where a canonical artifact was copied into
  a thread workspace and whether that copy is current, stale, or missing.
- Thread deletion dispatches a lifecycle event. Registered domain handlers can
  detach a conversation while preserving their own project history.
- A current-thread branch can clone the domain conversation link; a historical
  branch with no workspace clone does not claim a copied materialization.

Conversational run success does not prove every domain mutation succeeded. The
canonical domain state and its semantic receipts are the mutation authority;
Action records provide linked provenance evidence and may lag if terminal
finalization fails.

## Stable Contracts

### Agent Identity And Product Contract

`vassilflow.config.agent_contract` normalizes external assistant identities and
defines trusted runtime policy metadata.

`vassilflow.config.builtin_agents` retains the registration contract for
immutable curated Agent definitions. Its shipped registry is empty. A downstream
built-in definition declares:

- stable name and catalog identity;
- chat or project launch behavior;
- required and allowed tools;
- allowed thread-data scopes;
- skills and system instructions;
- capability adapter import paths;
- optional frontend chat-extension key.

The Agent catalog merges these built-ins with user-owned personal Agents.
Product metadata is separate from prompt-management APIs and reports
`available`, `degraded`, or `unavailable`.

### Runtime Policy Contract

The Gateway validates canonical identity claims and strips or rejects attempts
to set protected runtime metadata. During Agent graph construction, the harness
derives built-in policy from the canonical server-owned definition and enforces
it before model or tool execution.

Tool allowlists and thread-data scopes are enforced in the harness. Unknown
policy versions deserialize to deny-all rather than widening access. A
restricted policy defaults MCP and ACP/subagent access to denied. The built-in
definition contract has no opt-in fields for those channels; default and
unrestricted personal Agents may instead inherit the general harness behavior
through `policy=None`.

Domain repository authorization is separate from thread-path policy. Domain
routers and adapters resolve the authenticated user before reading a project,
template, revision, or Action record.

### Capability Adapter Contract

`vassilflow.capabilities.AgentCapabilityAdapter` is the boundary between a
curated Agent and specialized domain behavior. An adapter may contribute:

- optimistic-input validation and trusted runtime context;
- fresh Agent middleware instances;
- bounded, sanitized readiness checks;
- scoped operational repository instances.

A registered extension may send an optimistic capability envelope. The Gateway
dispatches it to the selected Agent's server-owned adapter, which resolves
canonical user-owned state before injecting trusted context. A client cannot
directly author trusted capability context. No concrete capability adapter is
registered by the base distribution.

Adapters are not a remote plugin surface. Their import paths come from immutable
built-in definitions, and every frontend extension remains a reviewed local
component.

### Action And Provenance Contract

`vassilflow.actions` provides a generic append-only mutation journal:

- the start record is immutable;
- the terminal outcome is separately immutable;
- public projection states are `running`, `succeeded`, `rejected`, `failed`,
  and `partial`;
- references and artifacts are bounded and normalized;
- user-facing APIs never expose another user's records.

Agent tools and direct domain APIs can use the same Action envelope. Domain-specific
semantic receipts remain domain records and are linked by Action ID rather than
flattened into a generic schema.

Action outcome persistence is separate from a domain commit. The repair
contract scans only stale `running` Actions, routes each owned operation to one
domain reconciler, and appends a terminal outcome only when that reconciler
finds an exact canonical Action marker or receipt. Missing, ambiguous, legacy,
or unsupported evidence remains `indeterminate`; current domain state alone is
not treated as proof that a particular Action caused it.

New Actions carry a renewable worker lease. Integrations using the Action
contract must heartbeat the lease while a mutation is executing. Repair can
inspect an Action only after the lease expires and must acquire an atomic,
short-lived claim before canonical reconciliation. Normal completion and repair
completion use the same store lock, so they cannot publish competing terminal
outcomes.

Direct domain APIs should treat the typed domain commit as the handoff boundary. The
domain mutation returns canonical identities and artifact facts, the router
finalizes the Action from that commit, and only then performs response readback
or projection. If the mutation call raises after it may have committed, the
domain reconciler checks the exact Action marker immediately. A proven commit or
non-commit receives that canonical outcome; an unresolved server error remains
`running` for later repair rather than being guessed into `failed`.

### Thread Lifecycle Contract

`vassilflow.runtime.thread_lifecycle` defines domain-neutral deletion and branch
events. Gateway routers prepare a durable source intent before changing core
thread state. They then publish an immutable `source_committed` or
`source_aborted` marker. Enabled domain handlers receive only committed events
and project the lifecycle change into their own stores.

Before invoking a handler, the dispatcher records an immutable attempt start.
Success and failure outcomes are stored per stable handler key. Repeated
dispatch and operator replay skip completed handlers, retry failed handlers,
and reclaim an interrupted `running` attempt only after its lease expires.
Each active attempt heartbeats a renewable lease with a monotonically
increasing generation. A replay that reclaims an expired attempt owns the next
generation; the older worker is fenced from renewing or publishing an outcome.
Prepared intents without a source outcome remain visible but are never replayed
automatically.

Lifecycle projection is still not a distributed transaction. A thread mutation
is not rolled back when a later domain projection fails, and a handler that
updates multiple resources can stop between resources. Handlers must therefore
remain idempotent. The source intent closes the unrecorded cross-store gap; if
the process stops before a source outcome can be written, the prepared state
requires diagnosis rather than automatic guessing.

### Repository Contract

`vassilflow.persistence.project_repository` is an operational contract, not a
generic project CRUD model. Each domain continues to own its resource schema and
artifact logic while exposing:

- immutable repository identity and deployment metadata;
- non-mutating readiness;
- bounded schema inventory;
- explicit migration planning;
- exact migration apply.

The registry rejects unknown, stale, altered, overlapping, cross-kind, or
incomplete plans and re-inventories after apply. Multi-writer repositories must
declare transactional migration safety. Current file-backed Action and lifecycle
repositories are single-writer and require a maintenance window. Domain repositories declare their own concurrency
and migration safety.

### Readiness Contract

`GET /health` is process liveness. `GET /health/ready` is the versioned
operational readiness document.

Readiness combines:

- Gateway initialization;
- application database connectivity and durability mode;
- operational repository checks;
- aggregate durable projection repair state;
- built-in Agent tool requirements;
- capability dependencies declared by registered Agent extensions.

The projection check is deadline-bounded and reads only lifecycle backlog and
Action lease state. It does not run domain reconciliation or scan canonical
domain evidence; those reads belong to the explicit operator repair command.

Independent Agent probes run concurrently. The caller's wait is
deadline-bounded, single-flight, sanitized, and cached in-process for at most 15
seconds. A timed-out synchronous probe can continue in its worker thread.
Required failures make an Agent unavailable and are enforced again before a run
record is created. Optional failures make an Agent degraded.

Readiness evidence is not authorization and can become stale. Every operation
retains its own dependency, ownership, and integrity checks.

## Request Flows

### Generic Or Personal Agent Run

1. The Gateway authenticates the request and resolves `assistant_id`.
2. It validates thread ownership and the thread's stored assistant identity.
3. It removes server-owned metadata from client input.
4. It resolves runtime configuration and creates the run.
5. The embedded runtime executes and publishes SSE, run events, token usage,
   and workspace changes.

### Built-In Agent Run With Domain Input

1. The frontend submits an ordinary run plus an optimistic capability envelope.
2. The Gateway verifies that the selected built-in Agent owns the adapter.
3. The adapter reloads the referenced user-owned resource and validates
   revision, hash, object path, and fingerprint.
4. The Gateway injects only the resolved trusted payload.
5. Required tool and capability readiness is enforced before `RunRecord`
   creation.
6. The shared runtime builds policy-filtered tools and adapter middleware.
7. Domain tools record Action provenance and commit domain revisions.

### Direct Domain Action

1. A domain router authenticates the user and resolves the resource in that
   user's store.
2. It records an immutable Action start.
3. The domain service performs approval, integrity, and conflict checks.
4. It commits the domain result and semantic receipt, then returns a typed
   commit containing the facts needed for provenance.
5. The router writes the terminal Action outcome from that commit before
   optional response readback or projection.
6. If the mutation call raises with an uncertain outcome, the owning domain
   reconciler checks exact canonical Action evidence. Proven outcomes are
   finalized immediately; unresolved server errors remain `running`.
7. The router projects the API response. A response failure cannot rewrite an
   already committed Action into `failed`.

If terminal Action persistence itself fails, the domain mutation may already be
committed and the Action can remain projected as `running`.

Direct management actions do not create artificial LLM runs.

## Frontend Architecture

The frontend has one workspace shell and three extension levels:

1. Catalog metadata controls discovery, filtering, status, pins, and launch
   path.
2. `ThreadChatPage` provides the shared chat, stream, clarification,
   regeneration, and composer behavior.
3. A local extension registry can wrap that shell with typed domain context.
   The base ships an empty domain extension registry and the generic chat shell.

The extension surface is intentionally narrow: context header, initial composer
value, typed submit options, thread-path projection, and run-finish callback.
Unknown extension keys fall back to the generic shell. A checked-in frontend
manifest must match the local component registry, and backend tests require
every built-in `chat_extension` key to appear in that manifest.

A project Agent may also own workspace routes for recent projects, templates,
revision evidence, preview, review, restore, and final selection. These pages
call authenticated domain APIs; they do not become a second chat implementation.

An unavailable Agent disables new messages, regeneration, and clarification
resume in existing chat routes. A degraded Agent remains launchable and explains
the limited dependency.

## Storage Authority

| Data                                                       | Current authority                   | Important constraint                             |
| ---------------------------------------------------------- | ----------------------------------- | ------------------------------------------------ |
| Users, thread metadata, and configured application records | Application database                | Backend may be memory, SQLite, or PostgreSQL     |
| LangGraph checkpoint state                                 | Configured checkpointer             | Conversation state only                          |
| Active run and stream bridge                               | Gateway process                     | Requires one Gateway worker today                |
| Thread uploads, workspace, and outputs                     | User-scoped `VASSILFLOW_HOME` paths | Deleted with thread data                         |
| Action journal                                             | User-scoped append-only repository  | Single writer                                    |
| Optional domain data                                       | Extension-owned repositories        | No concrete project repository ships in the base |

Changing the application database does not migrate file-backed domain state.
See [persistence operations](../../docs/PERSISTENCE.md) for deployment, backup, inventory, and migration
operations.

## Adding A Capability Or Agent

Choose the smallest product shape that owns the requirement.

| Need                                                       | Preferred extension                            |
| ---------------------------------------------------------- | ---------------------------------------------- |
| Reusable instructions with existing tools                  | Skill                                          |
| External service or callable operation                     | Tool or MCP server                             |
| User-specific prompt, model, tools, or skills              | Personal chat Agent                            |
| Curated policy and product entry using the shared runtime  | Built-in chat Agent                            |
| Durable revisions, evidence, templates, or management APIs | Built-in project Agent with a domain workspace |

For a new curated Agent:

1. Define the user workflow and decide whether it is chat-only or project-backed.
2. Register one canonical built-in definition with stable identity, launch
   metadata, required tools, allowlists, skills, and data scopes.
3. Implement tools as ordinary harness tools. Keep domain logic out of Gateway
   service modules.
4. Add a capability adapter only when the Agent needs trusted typed inputs,
   domain middleware, readiness, or operational repositories.
5. For project state, define domain-owned resource schemas and immutable
   identities. Implement the operational repository contract without forcing
   domain CRUD into a universal schema.
6. Wrap every mutation in the generic Action contract and keep rich semantic
   evidence in the domain.
7. Add a lifecycle handler only if thread deletion or branching affects domain
   links or materializations.
8. Add authenticated domain routers for direct project management. Reuse
   service functions between routers and tools where their authorization
   contexts differ.
9. Add server catalog metadata. Reuse the shared chat shell and register a
   reviewed local extension key only when typed chat context is necessary. Add
   the same key to the frontend extension manifest; CI rejects missing built-in
   registrations and the frontend rejects manifest/registry drift.
10. Test identity conflicts, tool/data denial, optimistic-input revalidation,
    readiness states, repository ownership, mutation provenance, lifecycle
    projection, generic chat behavior, and project UI behavior.

Do not:

- create a separate Agent runtime, stream protocol, or checkpoint stack;
- trust an Agent name or domain payload copied from frontend metadata;
- import a concrete domain package into generic runtime modules;
- use a thread workspace file as the canonical project artifact;
- put an entire project in thread checkpoints;
- duplicate the chat shell for each Agent;
- treat readiness cache entries as authorization;
- generalize a domain schema before a second production domain proves the
  shared shape.

## Operational Constraints

- Gateway run and stream coordination is process-local. Keep
  `GATEWAY_WORKERS=1` and `WEB_CONCURRENCY=1` when set. Startup rejects
  other values, including with PostgreSQL. A shared stream bridge and
  cross-worker run manager are not yet implemented.
- Pending memory extraction is an in-process best-effort queue; a process crash
  can lose pending updates. Token budgets use returned provider usage and can
  overshoot during a response or concurrent child work.
- File-backed Action and lifecycle repositories are single-writer storage.
  Optional domain repositories must declare their own concurrency contract.
- There is no global transaction across the application database, Action
  journal, thread files, and domain repositories.
- Lifecycle source intents precede core thread mutations, but the source
  outcome marker and thread store are still separate writes. A crash can leave
  a prepared intent that requires diagnosis. Multi-resource handlers can
  partially apply and must remain idempotent.
- Lifecycle handler leases heartbeat in the Gateway process. Process loss makes
  the attempt reclaimable only after its last durable lease expires; generation
  fencing prevents the displaced worker from later publishing an outcome.
- Stale Action repair is evidence-driven. It cannot finalize legacy,
  unsupported, or ambiguous records and reports them for operator review.
- Worker lease heartbeat is process-local. Process loss delays Action repair
  until the last durable lease expires.
- A timed-out synchronous readiness probe cannot be forcibly terminated; its
  result is ignored and the response fallback is cached. Repeated permanently
  hung probes still consume worker threads.

## Code Map

| Concern                                         | Primary path                                                                                                                                                                                                                                                      |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Gateway composition and health                  | [backend/app/gateway/app.py](../app/gateway/app.py)                                                                                                                                                                                                               |
| Run lifecycle and trusted request normalization | [backend/app/gateway/services.py](../app/gateway/services.py)                                                                                                                                                                                                     |
| Agent product catalog                           | [backend/app/gateway/agent_catalog.py](../app/gateway/agent_catalog.py)                                                                                                                                                                                           |
| Canonical Agent identity and policy             | [backend/packages/harness/vassilflow/config/agent_contract.py](../packages/harness/vassilflow/config/agent_contract.py)                                                                                                                                           |
| Built-in Agent registry                         | [backend/packages/harness/vassilflow/config/builtin_agents.py](../packages/harness/vassilflow/config/builtin_agents.py)                                                                                                                                           |
| Capability adapter protocol                     | [backend/packages/harness/vassilflow/capabilities/adapter.py](../packages/harness/vassilflow/capabilities/adapter.py)                                                                                                                                             |
| Action contract and store                       | [backend/packages/harness/vassilflow/actions/](../packages/harness/vassilflow/actions/)                                                                                                                                                                           |
| Thread lifecycle protocol and journal           | [backend/packages/harness/vassilflow/runtime/thread_lifecycle.py](../packages/harness/vassilflow/runtime/thread_lifecycle.py) and [backend/packages/harness/vassilflow/runtime/lifecycle_journal.py](../packages/harness/vassilflow/runtime/lifecycle_journal.py) |
| Projection repair composition                   | [backend/app/gateway/domain_repair.py](../app/gateway/domain_repair.py)                                                                                                                                                                                           |
| Operational repository protocol                 | [backend/packages/harness/vassilflow/persistence/project_repository.py](../packages/harness/vassilflow/persistence/project_repository.py)                                                                                                                         |
| Agent catalog UI                                | [frontend/src/core/agents/](../../frontend/src/core/agents/) and [frontend/src/components/workspace/agents/](../../frontend/src/components/workspace/agents/)                                                                                                     |

## Related Documentation

- [API Reference](API.md)
- [Authentication Design](AUTH_DESIGN.md)
- [Configuration](CONFIGURATION.md)
- [Streaming](STREAMING.md)
- [Persistence And Readiness](../../docs/PERSISTENCE.md)
- [Fresh Clone Setup](../../docs/SETUP.md)
