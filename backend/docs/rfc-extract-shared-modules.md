# Shared upload and skill modules

Status: implemented extraction. This filename is retained from the original RFC. Gateway and the direct client now share the harness modules below; the historical proposal is not an outstanding migration task.

## Dependency boundary

```text
Gateway routers ???????
                     ???> vassilflow.uploads.manager
VassilFlowClient ??????    vassilflow.skills.installer
```

The shared modules contain filesystem/business rules and Python exceptions. Gateway adapts HTTP forms, request permissions, response models, and status codes. The client adapts local paths and synchronous calls. Neither shared module imports FastAPI or `app.*`.

## Upload manager

[uploads/manager.py](../packages/harness/vassilflow/uploads/manager.py) centralizes upload-directory resolution, filename normalization, safe destinations, duplicate naming, listing, deletion, and virtual/artifact path construction.

Gateway still owns HTTP byte limits, streamed staging, optional conversion, and sandbox synchronization in [routers/uploads.py](../app/gateway/routers/uploads.py). The client has a separate local file-copy path in [client.py](../packages/harness/vassilflow/client.py). Shared helpers do not imply identical transport limits or conversion defaults. See [uploads](FILE_UPLOAD.md).

## Skill installer

[skills/installer.py](../packages/harness/vassilflow/skills/installer.py) contains shared archive validation, safe extraction, metadata checks, and duplicate-install behavior. Keep path traversal, symlink, expansion-size, and archive metadata handling in this shared layer so both entry points inherit fixes.

Gateway's [skills router](../app/gateway/routers/skills.py) retains authorization and HTTP error mapping. The direct client exposes Python-level results and errors. Use typed exceptions such as `SkillAlreadyExistsError` instead of identifying duplicate installations through error-message text.

## Maintenance checks

From `backend/`:

```bash
uv run pytest tests/test_harness_boundary.py tests/test_uploads_manager.py tests/test_uploads_router.py tests/test_client.py -q
```

Also select the current installer/router tests in [tests/](../tests/) when changing skill installation. Test real temporary paths and malicious archive members; a mocked successful copy does not establish extraction safety.

New reusable logic belongs in the harness. HTTP status decisions, authenticated user lookup, and request lifecycle remain in Gateway. See [architecture](ARCHITECTURE.md).
