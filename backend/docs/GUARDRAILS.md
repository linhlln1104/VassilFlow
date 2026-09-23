# Tool-call guardrails

`vassilflow.guardrails` provides provider-based authorization immediately around tool execution. Guardrails complement Agent tool policy and sandbox restrictions; they do not replace resource ownership checks or make an unsafe tool implementation safe.

## Enable the built-in provider

```yaml
guardrails:
  enabled: true
  fail_closed: true
  passport: null
  provider:
    use: vassilflow.guardrails.builtin:AllowlistProvider
    config:
      allowed_tools: [read_file, ls, glob, grep]
      denied_tools: [bash]
```

The [configuration model](../packages/harness/vassilflow/config/guardrails_config.py) defaults to disabled, `fail_closed: true`, and no provider. Both enabled configuration and a provider are required for the configuration-driven runtime to install this middleware.

[AllowlistProvider](../packages/harness/vassilflow/guardrails/builtin.py) compares exact tool names. A nonempty allowlist rejects other names; a denylist rejects listed names even when allowed. An empty allowlist is treated as no allowlist restriction, **not** deny-all. For restricted product agents, retain the explicit Agent policy contract described in [architecture](ARCHITECTURE.md).

## Provider interface

[provider.py](../packages/harness/vassilflow/guardrails/provider.py) defines `GuardrailRequest`, `GuardrailDecision`, `GuardrailReason`, and the provider protocol. A provider supplies `name`, synchronous `evaluate(request)`, and asynchronous `aevaluate(request)` methods.

```python
from vassilflow.guardrails.provider import (
    GuardrailDecision,
    GuardrailReason,
    GuardrailRequest,
)


class ReadOnlyProvider:
    name = "read-only-example"

    def evaluate(self, request: GuardrailRequest) -> GuardrailDecision:
        allowed = request.tool_name in {"read_file", "ls", "glob", "grep"}
        return GuardrailDecision(
            allow=allowed,
            reasons=[GuardrailReason(
                code="example.allowed" if allowed else "example.denied",
                message="Read-only tool policy",
            )],
            policy_id="read-only-v1",
        )

    async def aevaluate(self, request: GuardrailRequest) -> GuardrailDecision:
        return self.evaluate(request)
```

This example evaluates only in-memory data. A provider that reads files or calls a remote policy service must implement nonblocking async I/O or offload blocking work in its async method.

Configure custom providers with an importable `module:Class` path and constructor arguments under `provider.config`. The loader injects `framework="vassilflow"` only when the constructor supports that parameter or `**kwargs`, unless explicitly supplied. External policy/passport packages must implement this interface; their installation and policy semantics are owned by those packages, not by this repository.

## Attribution and outcomes

Requests include tool name/input and available user, role, OAuth identity, thread, run, tool-call, Agent/passport, subagent, and timestamp context. Optional fields may be absent for direct embedding. Use trusted runtime identity; do not authorize a mutation solely from model-authored tool arguments.

An allow decision invokes the tool. A denial returns a tool-facing denial result. A provider exception blocks the call when `fail_closed` is true; with false, the tool may execute despite evaluator failure. Choose that setting explicitly for the deployment's intended behavior.

The shared runtime builder installs configured guardrails for lead and delegated graphs. The pure-argument factory instead accepts a configured middleware instance through `RuntimeFeatures.guardrail`; `guardrail=True` alone is not supported. See [middleware composition](middleware-execution-flow.md).

## Verification

From `backend/`:

```bash
uv run pytest tests/test_guardrail_middleware.py -q
```

For a new provider, test that the underlying side effect is not called on denial or fail-closed exceptions, that attribution survives subagent execution, and that the asynchronous evaluator does not block the event loop. Tool-name checks cannot inspect hidden effects inside an allowed custom tool; test that tool's domain authorization separately.
