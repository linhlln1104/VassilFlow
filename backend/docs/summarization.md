# Conversation summarization

[VassilFlowSummarizationMiddleware](../packages/harness/vassilflow/agents/middlewares/summarization_middleware.py) compacts older graph messages while retaining recent context and selected skill content. It wraps the installed LangChain summarization implementation. The feature is disabled by default.

## Configuration

This example enables message-count-triggered compaction:

```yaml
summarization:
  enabled: true
  model_name: null
  trigger:
    type: messages
    value: 50
  keep:
    type: messages
    value: 20
  trim_tokens_to_summarize: 4000
  preserve_recent_skill_count: 5
  preserve_recent_skill_tokens: 25000
  preserve_recent_skill_tokens_per_skill: 5000
  skill_file_read_tool_names: [read_file, read, view, cat]
```

`model_name` selects a configured model key; null uses the default model with thinking disabled. It does not automatically find a cheaper model. Summary calls inherit graph tracing and use `middleware:summarize` attribution.

`trigger` accepts one threshold or a list of thresholds, with any threshold sufficient to trigger. Threshold and `keep` types are `messages`, `tokens`, and `fraction`. Fraction-based thresholds require compatible model context-size metadata. Choose values for the selected model and workload rather than copying a provider-independent percentage blindly.

The schema default for `trigger` is null; set an explicit threshold for predictable automatic behavior. `keep` defaults to twenty messages. A retention target is subject to keeping valid message/tool-call relationships.

`trim_tokens_to_summarize` defaults to 4000. The current factory forwards this setting only when non-null. Setting it to null therefore leaves the upstream middleware default in effect; it does not reliably mean unlimited summary input. `summary_prompt`, when non-null, is forwarded to the underlying middleware.

## Skill preservation and memory

The wrapper recognizes configured file-read tool names and the configured skills container root. It can preserve recent skill-read bundles within count, total-token, and per-skill caps. Repeated reads of a skill are deduplicated during selection; oversized bundles are not rescued merely because they are recent.

Before compaction, registered hooks receive the messages being summarized and preserved. When memory is enabled, the factory attaches `memory_flush_hook`. Hook failures are logged; this is not a distributed transaction between checkpoint compaction and memory persistence. See [memory](MEMORY_IMPROVEMENTS.md).

## Manual compaction and history

Gateway exposes `POST /api/threads/{thread_id}/compact` with authenticated ownership checks. Its request/response schema and active-run restrictions are defined in the [threads router](../app/gateway/routers/threads.py). Automatic and manual compaction share the configured middleware factory to avoid different model/retention behavior.

Compaction changes active graph context. It does not mean that the original conversation remains in the latest checkpoint. Durable run-event/message storage supplies historical messages when configured, and the frontend must reconstruct ordering correctly across runs. The stream update key `VassilFlowSummarizationMiddleware.before_model` participates in UI reconciliation.

## Validation

From `backend/`:

```bash
uv run pytest tests/test_summarization_middleware.py -q
```

Also use [full-stack replay](REPLAY_E2E.md) when changing history reconstruction. Cover tool-call pairing, preserved skill bundles, trigger/retention thresholds, custom prompts, memory hooks, and the manual endpoint. Mocked summary text alone does not validate the frontend's post-compaction history order.
