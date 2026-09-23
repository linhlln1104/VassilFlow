# Middleware execution and composition

VassilFlow uses LangChain agent middleware within its LangGraph runtime. The declared middleware list and hook execution order are related but not identical: before hooks run forward, after hooks run in reverse, and wrap hooks nest around the handler. A middleware's position must be chosen for the hook it implements.

## Three composition paths

| Composition path             | Source                                                                                                                   |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Full lead/personal agent     | [lead_agent/agent.py](../packages/harness/vassilflow/agents/lead_agent/agent.py), `build_middlewares()`                  |
| Shared lead/subagent runtime | [tool_error_handling_middleware.py](../packages/harness/vassilflow/agents/middlewares/tool_error_handling_middleware.py) |
| Pure-argument public factory | [factory.py](../packages/harness/vassilflow/agents/factory.py), `RuntimeFeatures` assembly                               |

They serve different contracts. The feature factory does not automatically reproduce every middleware in the full lead agent. Do not describe the system with a fixed middleware count.

## Full lead-agent declaration order

The current composition starts with the shared runtime chain, optionally prefixed by Agent policy. It then adds:

1. Dynamic context, server-owned capability middleware, skill activation, and durable context.
2. Configured summarization and optional Todo middleware.
3. Enabled token-budget middleware, followed by token-usage middleware when reporting or budget accounting is needed.
4. Title and memory middleware, plus vision middleware when the selected model supports it.
5. Deferred-tool filtering when needed, then system-message coalescing.
6. Optional subagent limit and loop detection, custom middleware, enabled safety-finish handling, and clarification last.

The shared runtime builder owns tool-result sanitization, thread/sandbox setup, upload handling for the lead, dangling-call repair, model/tool error handling, guardrails, sandbox audit, read-before-write checks, and progress reporting. Feature configuration determines which instances exist.

## Ordering constraints

- The lead declares `TokenBudgetMiddleware` before `TokenUsageMiddleware`. Reverse `after_model` execution then aggregates usage before budget enforcement decides whether the next tools may execute.
- Tool-progress wrapping is outside tool-error handling so completion/failure events reflect the handled outcome. The builder checks this relationship.
- Safety-finish handling runs before earlier after-model consumers can act on provider-truncated tool calls.
- Clarification is placed last in the lead chain. Keep its interrupt/resume behavior intact when adding middleware.
- Capability middleware instances are resolved by trusted server adapters; avoid mutable shared instances across unrelated runs.

Subagents receive their own configured guards, including independent budget instances. They do not inherit every lead-only feature merely because the parent uses it.

## Custom middleware

For configuration-driven composition, use the lead factory's custom middleware hook or a capability adapter. For direct factory composition, use `extra_middleware` with `Next`/`Prev` anchors, or provide a complete `middleware` list. The latter takes over the chain and cannot be combined with feature-driven assembly.

A synchronous hook that performs file, database, or network I/O can block asynchronous graph execution. Implement the async hook and offload blocking operations where needed; see [blocking I/O validation](BLOCKING_IO_DETECTION.md).

When changing order, test observable behavior: guard before side effect, usage before budget decision, one progress outcome per tool, safe handling of incomplete tool calls, and correct interrupt/resume. An assertion of list order alone is insufficient to establish those behaviors.
