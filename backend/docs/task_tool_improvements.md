# Delegated tasks and subagents

Status: implemented behavior. The historical filename is retained. The `task` tool delegates work and returns its result after completion; the model does not need to poll a separate task-status tool.

## Available workers

The shipped types are `general-purpose` and `bash`. The bash specialist is available only when the configured sandbox permits shell access. The local sandbox disables host bash by default. Additional worker types can be declared under `subagents.custom_agents`.

Delegated workers are not the same as user-owned personal agents or built-in product agents. The base product-agent registry is empty; delegation remains available independently.

Enable delegation through `subagent_enabled` in Gateway runtime context or `VassilFlowClient(subagent_enabled=True)`. The direct factory has a `RuntimeFeatures.subagent` option. Agent policy can further restrict delegation and tool availability.

## Tool input and lifecycle

The model supplies `description`, `prompt`, and `subagent_type`. Runtime identity and execution context are injected by the graph. Example arguments:

```json
{
  "description": "Review uploaded source",
  "prompt": "Inspect the files under /mnt/user-data/uploads and summarize their structure without modifying them.",
  "subagent_type": "general-purpose"
}
```

The [task tool](../packages/harness/vassilflow/tools/builtins/task_tool.py) starts background execution, checks status in the backend at five-second intervals, emits progress events, and waits before returning the result to the parent. It does not make additional model calls merely to poll status. The tool itself can remain active for the full child runtime.

Events include task start, incremental messages, completion, failure, cancellation, and timeout. The execution timeout and polling safety buffer are different limits. A failed or max-turn-limited child can return partial information; inspect its outcome rather than treating all returned text as success.

## Configuration

```yaml
subagents:
  timeout_seconds: 1800
  max_turns: null
  agents:
    general-purpose:
      timeout_seconds: 900
      max_turns: 40
      skills: []
  custom_agents:
    reviewer:
      description: Review text files without editing them
      system_prompt: Read the provided source and report specific findings.
      tools: [read_file, ls, glob, grep]
      skills: []
      model: inherit
      max_turns: 30
      timeout_seconds: 900
```

Built-in workers use the global 1800-second default unless overridden. A custom worker has its own default timeout of 900 seconds and max turns of 50. Per-agent overrides take precedence where supported. A null skill list inherits enabled skills; an empty list provides none. Tool inheritance remains constrained by parent policy.

Concurrent-child limits are runtime settings applied by [SubagentLimitMiddleware](../packages/harness/vassilflow/agents/middlewares/subagent_limit_middleware.py), separate from the timeout section above. Avoid documenting one global hard-coded concurrency or timeout for every entry point.

## Guards and limits

Delegated graphs use the shared runtime guardrails and enabled loop/budget/safety guards. When application token budgets are enabled, each child gets its own budget instance. The lead separately aggregates reported child usage before allowing subsequent tools. This does not reserve a shared remaining token pool and cannot prevent every overshoot from concurrent responses.

The executor and active tasks are process-local; they are not durable distributed jobs. Parent cancellation and shutdown require cleanup of owned tasks. New tools should not bypass that ownership by starting untracked background work.

See [subagents source](../packages/harness/vassilflow/subagents/), [middleware ordering](middleware-execution-flow.md), and [streaming](STREAMING.md).
