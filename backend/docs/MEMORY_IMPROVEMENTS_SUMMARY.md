# Memory behavior summary

Status: implemented behavior and current limits. The canonical guide is [Persistent memory](MEMORY_IMPROVEMENTS.md).

| Concern          | Current behavior                                                                          |
| ---------------- | ----------------------------------------------------------------------------------------- |
| Persistence      | File-based provider by default; custom `MemoryStorage` implementations supported          |
| Scope            | Effective user and optional personal agent                                                |
| Extraction       | Model-assisted updates, debounced and queued                                              |
| Scheduling       | Completion-driven pending work; stale timer generations are ignored                       |
| Injection        | Context/history sections and confidence-ranked facts under configurable budgets           |
| Corrections      | Configurable guaranteed categories; corrections protected by default                      |
| Staleness        | Model-assisted review constrained by age, count, removal, and protected-category settings |
| Uploads          | Ephemeral uploaded-file context filtered from extraction input                            |
| Management       | Authenticated fact CRUD, import/export, reload, clear, config, and status APIs            |
| Durability limit | Pending extraction jobs are in memory and can be lost on process exit                     |
| Retrieval limit  | No semantic/vector retrieval in the injection formatter                                   |

Memory is not the conversation transcript. Use checkpoints and run-event/message storage for conversation history. Automatic summarization can notify the memory extraction hook before messages are compacted, but it does not turn the queue into a synchronous durable transaction.

For exact configuration and caveats, see [MemoryConfig](../packages/harness/vassilflow/config/memory_config.py), [storage](../packages/harness/vassilflow/agents/memory/storage.py), and [prompt formatting](../packages/harness/vassilflow/agents/memory/prompt.py).
