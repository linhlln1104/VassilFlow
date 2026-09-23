# Streaming and history contracts

VassilFlow has an asynchronous HTTP/SSE path through Gateway and a synchronous in-process path through `VassilFlowClient`. Both execute the harness, but they have different transport envelopes and lifecycle owners.

## Gateway path

```text
HTTP run request -> Gateway services -> background run worker -> graph.astream()
                                              |
                                              v
                                  in-process stream bridge -> SSE subscribers
                                              |
                                              v
                                    run journal / event store
```

[Gateway services](../app/gateway/services.py) authorize and prepare the run. The [worker](../packages/harness/vassilflow/runtime/runs/worker.py) executes the graph and publishes serialized events. [thread_runs.py](../app/gateway/routers/thread_runs.py) exposes streaming, join, cancellation, messages, and event queries.

SSE frames carry an event name, JSON data, and event ID where applicable. Parse SSE framing with an SSE-capable client; network chunks are not necessarily complete frames or JSON documents. The browser SDK's transport names are not identical to raw graph modes.

## Modes and payloads

| Mode or surface       | Meaning                                                                       |
| --------------------- | ----------------------------------------------------------------------------- |
| Graph `values`        | Complete state snapshot after graph updates                                   |
| Graph `updates`       | Updates associated with graph nodes                                           |
| Graph `messages`      | Model message chunks plus metadata                                            |
| HTTP `messages-tuple` | Compatibility transport for message/chunk plus metadata                       |
| `custom`              | Tool/subagent/runtime progress payloads                                       |
| Persisted run events  | Journal records for history/inspection, separate from raw graph `events` mode |

Gateway does not support graph `events` mode; requesting it is skipped with a log message. Only request modes consumed by the client.

Message chunks represent deltas; a later `values` snapshot can contain the complete message. Deduplicate by message identity and reconcile the snapshot rather than appending both as new answer text. Tool-call chunks and usage-only chunks need separate handling from visible text.

## Reconnection and cancellation

[MemoryStreamBridge](../packages/harness/vassilflow/runtime/stream_bridge/memory.py) uses a bounded per-run event log with a condition for subscribers. Its historical `queue_maxsize` configuration controls the retained event count, default 256. It is not a durable queue.

A valid retained `Last-Event-ID` resumes after that event. A missing, malformed, foreign, or evicted ID falls back to the earliest retained event. A slow subscriber can fall behind retention. Client reconciliation must tolerate replay and must not assume an unbroken stream from process start to finish.

Run `on_disconnect` defaults to `cancel`; `continue` requests continued execution after the initial SSE connection ends. Rejoin and persisted history are separate from a durable cross-process streaming guarantee. The schema's `stream_resumable` field does not provide a separate durable replay service.

Cancellation, graph interruption, model failure, and successful completion are different outcomes. Inspect run status and final events. A closed socket or an accepted POST is not evidence that the task completed successfully.

One Gateway worker is required. Redis appears in the configuration type but its provider raises `NotImplementedError`; PostgreSQL does not make the in-memory bridge or active task registry distributed.

## In-process client

[client.py](../packages/harness/vassilflow/client.py) calls `graph.stream()` and yields its own `StreamEvent(type, data)` objects. It does not call Gateway. The client's `messages-tuple` event data is a normalized dictionary; do not assume it is the raw HTTP tuple envelope.

```python
from vassilflow.client import VassilFlowClient

client = VassilFlowClient(config_path="config.yaml")
for event in client.stream("Hello", thread_id="stream-example"):
    print(event.type, event.data)
```

This performs a real model call. Add an explicit checkpointer for multi-turn state. The client requests values, messages, and custom modes and emits an end event with accumulated usage.

Text deduplication, streamed-message tracking, and usage deduplication are distinct concerns. A message may have streamed text already while its final usage arrives later. Combining those tracking sets can either duplicate text or drop usage. `chat()` assembles text deltas for the final answer; it does not concatenate every complete state snapshot.

## History and tests

Checkpoints preserve execution state, while run events preserve the configured history/trace record. After summarization, older messages may be absent from the checkpoint. Runs are listed newest first; consumers must reconstruct chronological messages deliberately and preserve the open conversation when an older-history request fails.

Use [replay E2E](REPLAY_E2E.md) for backend/frontend contracts. Relevant backend tests include [stream bridge tests](../tests/test_stream_bridge.py), [client tests](../tests/test_client.py), and [multi-turn graph streaming tests](../tests/test_multiturn_message_stream_graph_integration.py). Keep tests for late subscription, replay cursors, cancellation, message identity, usage-only chunks, subagent events, and compacted history.
