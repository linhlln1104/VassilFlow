# Title generation implementation notes

Status: implemented. This file retains its historical name; [automatic titles](AUTO_TITLE_GENERATION.md) is the user-facing guide.

## Ownership

- [TitleConfig](../packages/harness/vassilflow/config/title_config.py) owns defaults and prompt settings.
- [TitleMiddleware](../packages/harness/vassilflow/agents/middlewares/title_middleware.py) selects the first exchange and returns a `title` state update.
- [Lead-agent composition](../packages/harness/vassilflow/agents/lead_agent/agent.py) supplies the run's configuration snapshot.
- [Gateway services](../app/gateway/services.py) and the [run worker](../packages/harness/vassilflow/runtime/runs/worker.py) integrate completion/interruption and display-name synchronization.

## Runtime details

`_should_generate_title()` requires no existing title and one real user turn. Normal generation also requires an assistant message. The partial-exchange path relaxes that condition for interrupted runs.

`after_model()` performs local title generation. `aafter_model()` can call an explicitly selected model. The async model call disables thinking, inherits callbacks, sets `middleware:title`, and uses the no-stream tag. It must not attach a second copy of the graph's tracing callbacks.

Content normalization handles strings, text blocks, and nested content. Reasoning-tag removal prevents hidden-thinking markup from becoming the displayed title. Failure or empty model output returns the local fallback rather than failing the conversation solely because title generation failed.

## Regression checklist

When changing this feature, cover local default behavior, explicit async model selection, no duplicate callback attachment, title preservation, dynamic-context exclusion, multimodal content, reasoning-tag removal, fallback, and interrupted first turns. Check both graph state and thread-list metadata; a correct state update alone does not prove the sidebar will refresh.

Use the current title-related tests in [backend/tests](../tests/) and the [replay title-render scenario](REPLAY_E2E.md). Historical timing measurements and completion claims are not part of this contract.
