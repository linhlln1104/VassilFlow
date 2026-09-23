# Record/replay end-to-end tests

Replay checks backend/frontend contracts using recorded model responses. Replaying does not need a provider API key; recording a new conversation makes real model calls. Test fixtures are test data and must not contain secrets or private conversation content.

## Layers

| Layer             | Implementation                                                            | What it checks                                                             |
| ----------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Backend golden    | [test_replay_golden.py](../tests/test_replay_golden.py)                   | Real Gateway/runtime response and SSE contracts with replayed model output |
| Full-stack render | [frontend/tests/e2e-real-backend](../../frontend/tests/e2e-real-backend/) | Real frontend, replay Gateway, and Chromium DOM behavior                   |

The full-stack suite also includes seeded multi-run history scenarios. [seed_runs_router.py](../tests/seed_runs_router.py) is mounted only by the test replay setup when `VASSILFLOW_ENABLE_TEST_SEED=1`. It seeds owned runs/messages without a checkpoint so the frontend must reconstruct history from the run APIs. Do not mount this router in production.

## Run existing fixtures

From the repository root, run each command in its indicated directory:

```bash
cd backend
uv run pytest tests/test_replay_golden.py -q
```

From `frontend/`, after dependencies and Playwright Chromium are installed:

```bash
pnpm exec playwright test -c playwright.real-backend.config.ts
```

[playwright.real-backend.config.ts](../../frontend/playwright.real-backend.config.ts) owns test-server startup. The [CI workflow](../../.github/workflows/replay-e2e.yml) runs the backend and full-stack jobs; the full-stack job uploads the Playwright report and render artifacts. It does not build a product-specific renderer.

## Matching and limitations

[ReplayChatModel](../tests/replay_provider.py) matches recorded assistant turns by a normalized hash of caller and conversation. Caller attribution separates lead, title, suggestions, and subagent requests. Normalization removes volatile material such as dates, UUIDs, temporary paths, and system reminders.

System prompts are excluded from the match key. This makes replay useful for transport/render contracts, but it cannot validate whether a changed system prompt produces good live-model behavior. [The fixture builder](../tests/_replay_fixture.py) pins test configuration and disables unrelated variable features.

A missing replay match must fail the test. Gateway can turn a model exception into an ordinary error response with valid SSE shape, so backend golden tests also inspect recorded replay misses. Matching event shapes alone is insufficient.

## Record and rebuild

Inspect [playwright.record.config.ts](../../frontend/playwright.record.config.ts) and [build_fixture_from_jsonl.py](../scripts/build_fixture_from_jsonl.py) before recording. The recorder consumes `OPENAI_API_KEY`, `OPENAI_API_BASE`, `RECORD_MODEL`, and `VASSILFLOW_RECORD_OUT` from the environment. Set them outside committed files, then run from `frontend/`:

```bash
pnpm exec playwright test -c playwright.record.config.ts
```

Convert the recording with the fixture script's `--jsonl`, `--meta`, `--out`, and `--model` arguments. Run `uv run python scripts/build_fixture_from_jsonl.py --help` from `backend/` for current options. Review and redact the generated fixture before adding it to [tests/fixtures/replay](../tests/fixtures/replay/).

To intentionally regenerate golden expectations, set `VASSILFLOW_WRITE_GOLDEN=1` for the backend golden test command and review the diff. In PowerShell, use `$env:VASSILFLOW_WRITE_GOLDEN = "1"`; in Bash, prefix the command with `VASSILFLOW_WRITE_GOLDEN=1`. Remove the variable afterward so ordinary checks cannot rewrite expectations.

Re-record when the graph's model-call sequence or conversation contract changes. Visual baselines can depend on OS/rendering environment; distinguish DOM assertions from screenshot inspection in validation reports.
