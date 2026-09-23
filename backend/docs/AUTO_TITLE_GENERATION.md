# Automatic thread titles

[TitleMiddleware](../packages/harness/vassilflow/agents/middlewares/title_middleware.py) creates a title when the thread has no title and the first user/assistant exchange is available. Dynamic-context reminder messages are excluded from the user-turn count. Existing titles are preserved.

## Configuration

```yaml
title:
  enabled: true
  max_words: 6
  max_chars: 60
  model_name: null
```

These are the main [TitleConfig](../packages/harness/vassilflow/config/title_config.py) defaults. With `model_name: null`, title generation uses the first user's text locally and makes no title-specific model call. Set `model_name` to a configured model key to enable model-generated titles on the asynchronous path.

The optional `prompt_template` supports `{max_words}`, `{user_msg}`, and `{assistant_msg}`. The built prompt limits each conversation excerpt to 500 characters. `max_words` is a model prompt instruction, not an enforced word-count validator.

## Fallback behavior

The synchronous middleware path uses the local fallback even if a title model is configured. The asynchronous path uses that model when configured and falls back locally on errors or empty output. Model output is normalized, stripped of reasoning tags and surrounding quotes, and capped at `max_chars`.

The local fallback takes up to `min(max_chars, 50)` characters and appends `...` when truncated. Consequently the fallback can exceed that prefix limit by three characters. Empty input falls back to `New Conversation`. A cancelled/interrupted first turn can use a partial-exchange fallback through the runtime's title synchronization path.

## Persistence and display

The title is returned as a graph-state update. Gateway synchronizes thread display metadata from runtime state; the frontend reads that metadata and can also consume state updates. Title generation is separate from the assistant answer and is not a second conversation message.

Configured title-model calls inherit runtime callbacks, use `middleware:title` attribution, and suppress token streaming into the normal answer. They can add model latency and usage. See [implementation notes](TITLE_GENERATION_IMPLEMENTATION.md) and [streaming](STREAMING.md).

## Troubleshooting

| Symptom                                          | Check                                                                |
| ------------------------------------------------ | -------------------------------------------------------------------- |
| Title is a shortened user prompt                 | Expected default with no explicit title model                        |
| Existing title does not change                   | Middleware intentionally skips a nonempty title                      |
| Model title never appears                        | Configured model key, async execution, provider errors, and fallback |
| Title has slightly more characters than expected | Local fallback appends its ellipsis after truncation                 |
| Thread list differs from open conversation       | Inspect graph title and Gateway thread display metadata separately   |
