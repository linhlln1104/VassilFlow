# Persistent memory

Memory stores user context, historical summaries, and individual facts for later conversations. It is separate from thread checkpoints and from conversation summarization. The implementation is in [agents/memory](../packages/harness/vassilflow/agents/memory/) and [MemoryMiddleware](../packages/harness/vassilflow/agents/middlewares/memory_middleware.py).

## Configuration

```yaml
memory:
  enabled: true
  injection_enabled: true
  storage_path: ""
  storage_class: vassilflow.agents.memory.storage.FileMemoryStorage
  debounce_seconds: 30
  model_name: null
  max_facts: 100
  fact_confidence_threshold: 0.7
  max_injection_tokens: 2000
  token_counting: tiktoken
  guaranteed_categories: [correction]
  guaranteed_token_budget: 500
  staleness_review_enabled: true
  staleness_age_days: 90
  staleness_min_candidates: 3
  staleness_max_removals_per_cycle: 10
  staleness_protected_categories: [correction]
```

See [MemoryConfig](../packages/harness/vassilflow/config/memory_config.py) for exact field names and validation limits. A null memory model selects the runtime's default model; unlike title generation, memory extraction can therefore make model calls without an explicitly named memory model.

## Storage and scope

Authenticated default-agent memory is `{runtime_home}/users/{user_id}/memory.json`. Personal-agent memory is under that user's `agents/{agent_name}/memory.json`. Legacy direct calls without user context can use a global file. An absolute `storage_path` overrides the normal user memory file and can share data across users; use the default owner-scoped path unless sharing is intentional.

`FileMemoryStorage` caches by user/agent and file modification time, and saves through a temporary file followed by replacement. Its interface is `load`, `reload`, and `save`, with an explicit `user_id` keyword. A custom storage class must implement `MemoryStorage`; an invalid class configuration falls back to the file implementation with an error log.

## Extraction and queueing

Conversation processing is debounced and queued in process memory. Work is scoped to its owner and agent. Completion schedules pending work; busy workers do not spin through zero-delay timers. Timer generations prevent stale callbacks from acting as current timers, and explicit flush/cancellation paths retain scope.

The queue is best effort: it is not a durable job queue, and a process crash can lose pending extraction. A completed chat response does not establish that memory has already been saved. Inspect `/api/memory/status` when validating extraction.

The extraction prompt distinguishes user context, historical summaries, and categorized facts, including explicit corrections. Uploaded-file context is filtered so ephemeral upload paths do not become persistent memory. Model-proposed stale removals pass the configured age, candidate, removal, and protected-category checks.

## Prompt injection

[format_memory_for_injection()](../packages/harness/vassilflow/agents/memory/prompt.py) formats sections and selects facts under token budgets. Fact selection uses confidence ordering; it does not implement semantic retrieval or query-specific vector search.

Guaranteed categories are selected first within their own budget. They normally displace regular facts within the ordinary budget, and the final truncation protects the selected facts block. The effective ceiling can be additive when guaranteed content exceeds the ordinary limit; `max_injection_tokens` is not an unconditional hard cap on all injected text.

`tiktoken` counting uses a lazy cache and falls back when encoding is unavailable; `char` uses estimation. Token estimates and model billing are different measurements.

## Management APIs

The authenticated memory API supports read, clear, reload, fact create/update/delete, import/export, effective configuration, and queue/status inspection. Use [API.md](API.md) and the running OpenAPI schema for bodies and scope parameters. Clearing or importing memory affects persisted state; use an isolated account for UI review.

See [settings validation](MEMORY_SETTINGS_REVIEW.md), the [sample fixture](memory-settings-sample.json), and [memory behavior summary](MEMORY_IMPROVEMENTS_SUMMARY.md).
