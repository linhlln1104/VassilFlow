# Current limits and extension work

This file records architectural limits and candidate work, not a promise that a feature is scheduled. Check current source and tests before treating an item as an open defect. The canonical boundaries are in [ARCHITECTURE.md](ARCHITECTURE.md).

## Current limits

- Gateway supports one worker. Active runs, stream retention, memory queueing, and several coordination services remain process-local, including with PostgreSQL.
- Redis stream transport is declared in the schema but is not implemented. Buffered reconnection is not durable replay after process loss.
- Some LangGraph-compatible request fields have no full Platform implementation; `enqueue` is unsupported. See [API.md](API.md).
- Pending memory extraction is best effort and can be lost on process exit. Memory injection uses confidence ordering, not semantic retrieval.
- Token budgets are checked from returned provider usage; they do not reserve a shared allowance before concurrent work.
- File-backed Action/lifecycle storage requires a single writer. SQL state, filesystem state, and optional domain repositories do not share one atomic transaction.
- A timed-out synchronous readiness probe can continue occupying a worker thread until it returns.
- Runtime IM bot setup can persist deployment secrets in a protected local JSON file. This is distinct from encrypted per-connection credentials.

## Candidate extensions

Distributed execution requires a coordinated design for run ownership, cancellation, stream transport, scheduling, channel workers, and storage concurrency. Replacing one database or stream class alone is insufficient.

Durable memory scheduling would need persisted jobs, owner-aware retries, shutdown/recovery semantics, and protection against stale updates. Semantic retrieval would need explicit ranking, scope, deletion, and injection-budget contracts.

New product agents should be added through capability, policy, Action, lifecycle, repository, and frontend extension contracts. The base currently ships no Office product, project/template API, or product renderer. Generic uploads and format conversion remain available.

## Already available

Local authentication, OIDC, user-owned IM bindings, sandbox warm reuse, generic agent factories, shared upload/skill helpers, and glob/grep tools are implemented. Do not revive old RFC checklists that describe them as entirely unimplemented; use their current guides in [the index](README.md).
