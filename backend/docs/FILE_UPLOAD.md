# Uploads and document conversion

Gateway stores uploaded files in an owner-scoped thread workspace and exposes authenticated artifact URLs. Generic PDF and Office-format conversion remains available after removal of the built-in Office product; it does not provide a document-editing product or renderer.

## API

| Method | Path                                          | Purpose                                          |
| ------ | --------------------------------------------- | ------------------------------------------------ |
| POST   | `/api/threads/{thread_id}/uploads`            | Multipart upload using repeated `files` fields   |
| GET    | `/api/threads/{thread_id}/uploads/limits`     | Effective limits                                 |
| GET    | `/api/threads/{thread_id}/uploads/list`       | Current uploaded files                           |
| DELETE | `/api/threads/{thread_id}/uploads/{filename}` | Delete a file and its managed conversion sidecar |

Authentication, CSRF for mutations, and ownership rules apply. A newly chosen thread ID can be used for pre-message uploads subject to owner checks; an existing thread cannot be accessed by another owner. See [API examples](API.md).

The upload response contains `success`, `files`, `message`, and `skipped_files`. Each file includes `filename`, `size`, host `path`, agent `virtual_path`, and browser `artifact_url`. Renamed duplicates can include `original_filename`. Successful conversion adds `markdown_file`, `markdown_path`, `markdown_virtual_path`, and `markdown_artifact_url`.

Inspect both the HTTP status and response content. Unsafe destinations can be skipped, and a response may contain fewer files than the submitted form.

## Limits and conversion

```yaml
uploads:
  max_files: 10
  max_file_size: 52428800
  max_total_size: 104857600
  auto_convert_documents: false
```

These are Gateway defaults: ten files, 50 MiB per file, and 100 MiB total per request. They are not a total thread-storage quota. The router also accepts legacy `max_file_count` and `max_single_file_size` keys, but new configuration should use the names above.

Automatic document conversion is disabled by default for Gateway uploads. When enabled, supported conversion candidates are `.pdf`, `.ppt`, `.pptx`, `.xls`, `.xlsx`, `.doc`, and `.docx`. A converter may fail or produce incomplete text for a particular input. Do not assume every PDF contains extractable text or that a Markdown sidecar will always exist. The original upload remains the source file.

The direct Python client's `upload_files()` has its own local-copy and conversion path; do not assume it enforces every HTTP request limit or follows Gateway's conversion toggle.

## File handling

The [router](../app/gateway/routers/uploads.py) streams uploads with byte accounting, stages writes, normalizes filenames, and checks destinations. Duplicate filenames within one request are renamed. Uploading a single file with an existing name retains replacement behavior; callers should not treat upload as an immutable revision API.

Thread-data mounts make files visible directly to compatible sandboxes. Other providers receive an explicit file sync. Uploaded file permissions are adjusted so the sandbox process can read them; the containing runtime directory remains sensitive user data.

[UploadsMiddleware](../packages/harness/vassilflow/agents/middlewares/uploads_middleware.py) supplies virtual-path file context to the agent. Use `/mnt/user-data/uploads/...` in tools and returned artifact URLs in the browser. Never send a Gateway host path as though it were a sandbox path.

## Example

This function uses an already authenticated `httpx.Client` configured with the current CSRF header as shown in [API.md](API.md):

```python
from pathlib import Path

import httpx


def upload_report(client: httpx.Client, thread_id: str, path: Path) -> dict:
    with path.open("rb") as handle:
        response = client.post(
            f"/api/threads/{thread_id}/uploads",
            files=[("files", (path.name, handle))],
        )
    response.raise_for_status()
    result = response.json()
    if not result["success"] or not result["files"]:
        raise RuntimeError(result["message"])
    return result
```

For artifact download, use the returned URL with the authenticated client; `download=true` requests download behavior. Artifact serving validates thread ownership and path access. Uploading a file does not make its URL public.

## Sources and verification

- [Shared upload manager](../packages/harness/vassilflow/uploads/manager.py)
- [File conversion](../packages/harness/vassilflow/utils/file_conversion.py)
- [Artifact router](../app/gateway/routers/artifacts.py)
- [Path conventions](PATH_EXAMPLES.md)

From `backend/`:

```bash
uv run pytest tests/test_uploads_router.py tests/test_uploads_manager.py tests/test_uploads_middleware_core_logic.py -q
```
