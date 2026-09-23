# Plan mode and task tracking

Plan mode adds [TodoMiddleware](../packages/harness/vassilflow/agents/middlewares/todo_middleware.py) and the `write_todos` tool for tracking multi-step work. It is a task-tracking feature, not a read-only mode or a requirement for human approval before tools execute.

## Enable it

Gateway's run configuration recognizes `is_plan_mode` in runtime context. For example, this is a request body for a thread's `/runs/stream` endpoint:

```json
{
  "input": {
    "messages": [
      {
        "role": "user",
        "content": "Inspect the uploaded project and propose a migration plan."
      }
    ]
  },
  "context": { "is_plan_mode": true },
  "stream_mode": ["values", "messages-tuple", "custom"]
}
```

Authentication, ownership, and the selected agent's tool policy still apply. Do not use this flag as an authorization boundary.

For the direct client, use `VassilFlowClient(plan_mode=True)`. For the pure-argument factory, use `create_vassilflow_agent(..., plan_mode=True)`. For the configuration-driven lead factory, supply `is_plan_mode` through its runtime configuration. See [Python integration](rfc-create-vassilflow-agent.md).

## State and behavior

Todo items have a `content` string and a `status`: `pending`, `in_progress`, or `completed`. The tool updates the todo list in graph state. Middleware prompts encourage an active task, timely completion updates, and avoiding unnecessary plans for simple requests; these prompt rules are not a transactional workflow engine.

The middleware also restores todo context when the original tool call has been compacted away. If the model attempts a clean final answer with incomplete items, it can queue a bounded completion reminder and return to the model. These reminders do not turn plan mode into an approval gate.

The frontend displays plan state received through the normal graph stream. Checkpoints preserve graph state only when a checkpointer is configured. A direct client without a checkpointer will not retain a multi-turn plan automatically.

## Verify changes

Check that enabling the mode exposes `write_todos`, disabling it omits the middleware, updates preserve the expected state shape, and streaming/resume renders the current list. When adding side-effect restrictions or approval steps to a product agent, implement them separately in policy, guardrails, or trusted capability code.
