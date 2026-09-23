# Agent factory and direct Python integration

Status: the factory and feature-composition API are implemented. The historical RFC filename is retained for links. This document describes current signatures; earlier proposed client arguments are not a supported contract.

## Choose an entry point

| Entry point                                          | Use it for                                                                                 |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `vassilflow.agents.factory.create_vassilflow_agent`  | Construct a graph from a model, tools, middleware, and feature flags                       |
| `vassilflow.agents.lead_agent.agent.make_lead_agent` | Compose the full configuration-driven lead/personal-agent runtime                          |
| `vassilflow.client.VassilFlowClient`                 | Synchronous in-process chat/stream plus management helpers using application configuration |
| Gateway                                              | Authenticated HTTP/SSE, run lifecycle, persistence, and frontend/channel integration       |

The harness package is [backend/packages/harness/vassilflow](../packages/harness/vassilflow/). Application-specific modules may depend on it; it must not import `app.*`.

## Factory example

This function accepts an already-created compatible chat model. It does not make a model request until the returned graph is invoked:

```python
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool

from vassilflow.agents.factory import create_vassilflow_agent
from vassilflow.agents.features import RuntimeFeatures


@tool
def add(left: int, right: int) -> int:
    """Add two integers."""
    return left + right


def build_agent(model: BaseChatModel):
    return create_vassilflow_agent(
        model=model,
        tools=[add],
        system_prompt="Answer arithmetic questions using the available tool.",
        features=RuntimeFeatures(sandbox=False),
        name="arithmetic",
    )
```

The factory accepts `model`, optional `tools`, and keyword arguments `system_prompt`, `middleware`, `features`, `extra_middleware`, `plan_mode`, `state_schema`, `checkpointer`, and `name`. It returns a compiled LangGraph graph and defaults to VassilFlow's `ThreadState`.

Factory assembly reads no YAML itself. Selected runtime components can still read global configuration or acquire infrastructure when invoked, particularly sandbox, memory, and delegated-task components. A config-free factory does not imply that every enabled feature is config-free at runtime.

## Feature composition

[RuntimeFeatures](../packages/harness/vassilflow/agents/features.py) defaults to sandbox and loop detection enabled. Memory, summarization, subagent delegation, vision, automatic title, guardrail, and token budget features default to disabled in this factory. These defaults differ from the full lead-agent runtime.

Most feature values accept `True`, `False`, or a middleware instance. Summarization and guardrail require a configured middleware instance when enabled; `True` alone raises an error because there is no parameter-free default implementation for those factory features.

`extra_middleware` inserts additional middleware into the automatically assembled chain. `Next` and `Prev` decorators position middleware relative to an anchor middleware type. Use [features.py](../packages/harness/vassilflow/agents/features.py) and [factory.py](../packages/harness/vassilflow/agents/factory.py) for ordering and validation details.

Passing `middleware=[...]` takes over the complete chain. It cannot be combined with `features` or a nonempty `extra_middleware`. Full takeover also means the automatic feature tools and safeguards are not assembled for you. Feature-injected tools are deduplicated by name, with explicitly supplied tools taking priority.

## Direct client

From the repository root, after installing backend dependencies and configuring a model:

```python
from langgraph.checkpoint.memory import InMemorySaver

from vassilflow.client import VassilFlowClient

client = VassilFlowClient(
    config_path="config.yaml",
    checkpointer=InMemorySaver(),
    subagent_enabled=False,
    plan_mode=False,
)
print(client.chat("Hello", thread_id="example-thread"))
```

This example performs a real model call. An explicit checkpointer is required to preserve multi-turn graph state between calls using the same thread ID; the client constructor defaults to no checkpointer.

Current client options include `model_name`, `thinking_enabled`, `subagent_enabled`, `plan_mode`, `agent_name`, `available_skills`, `middlewares`, and `environment`. It does **not** accept the old RFC's proposed `config`, `features`, or `extra_middleware` constructor arguments. Use the factory for that level of composition.

The direct client does not start Gateway or provide its HTTP authentication boundary. The embedding application owns identity, trusted configuration, lifecycle, and isolation. See [client.py](../packages/harness/vassilflow/client.py), [streaming](STREAMING.md), and the [architecture contract](ARCHITECTURE.md).
