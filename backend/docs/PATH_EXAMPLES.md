# Paths and runtime storage

Repository paths in this documentation start at the checkout root. Python imports use `vassilflow.*`; the package source is [backend/packages/harness/vassilflow](../packages/harness/vassilflow/). Gateway source is [backend/app/gateway](../app/gateway/). There is no `backend/src` package.

## Resolve the roots first

The implementation is in [runtime_paths.py](../packages/harness/vassilflow/config/runtime_paths.py) and [paths.py](../packages/harness/vassilflow/config/paths.py).

| Setting                        | Resolution                                                                  |
| ------------------------------ | --------------------------------------------------------------------------- |
| Project root                   | `VASSILFLOW_PROJECT_ROOT`, otherwise the caller's current working directory |
| Runtime home                   | `VASSILFLOW_HOME`, otherwise `{project_root}/.vassilflow`                   |
| Explicit `Paths(base_dir=...)` | Overrides runtime home for that `Paths` instance                            |
| Docker host runtime home       | `VASSILFLOW_HOST_BASE_DIR`, otherwise the runtime base directory            |
| SQLite directory               | `database.sqlite_dir`, resolved against the process working directory       |

Relative environment paths resolve against the process working directory. Prefer absolute paths in service configuration. A configured project root must already exist and be a directory.

The root `make dev` launcher pins the project root to the checkout and defaults runtime home to `backend/.vassilflow`. Starting Python directly from the checkout instead defaults runtime home to `.vassilflow` there. Starting directly from `backend/` defaults it to `backend/.vassilflow`. These are different directories.

## Authenticated user layout

```text
{runtime_home}/
  .jwt_secret
  users/{user_id}/
    memory.json
    agents/{agent_name}/
      config.yaml
      SOUL.md
      memory.json
    actions/
    lifecycle/
    threads/{thread_id}/
      user-data/
        workspace/
        uploads/
        outputs/
```

Use the effective authenticated owner when resolving paths. Identifiers are validated before filesystem access. `make_safe_user_id()` normalizes external identities and adds a digest when normalization is lossy. Do not replace it with a hand-written character substitution.

Legacy or direct calls without a user identity can use `{runtime_home}/memory.json`, `{runtime_home}/agents/{agent_name}/`, and `{runtime_home}/threads/{thread_id}/`. Those paths do not represent a signed-in user's storage.

An absolute `memory.storage_path` overrides the default user memory file and therefore opts out of its normal per-user path separation. Personal-agent memory still uses the user/agent directory.

## Host, sandbox, and HTTP paths

For owner `user-123`, thread `thread-456`, and uploaded file `report.pdf`:

| Consumer           | Example                                                                         |
| ------------------ | ------------------------------------------------------------------------------- |
| Gateway filesystem | `{runtime_home}/users/user-123/threads/thread-456/user-data/uploads/report.pdf` |
| Agent tool         | `/mnt/user-data/uploads/report.pdf`                                             |
| Browser            | `/api/threads/thread-456/artifacts/mnt/user-data/uploads/report.pdf`            |

The sandbox sees `/mnt/user-data/workspace`, `/mnt/user-data/uploads`, and `/mnt/user-data/outputs`. An ACP workspace uses its separate mapping; do not assume it is the same directory as `user-data/workspace`.

Use host paths only in trusted backend code. Give virtual paths to agent tools and artifact URLs to browsers. Artifact requests still require authentication and thread ownership; the URL is not a public sharing token. URL-encode dynamic path segments and use URLs returned by the upload API when available.

## Backend example

This example assumes authorization has already established the owner and thread. It resolves a fixed filename, not an untrusted path:

```python
from vassilflow.config.paths import get_paths

uploads_dir = get_paths().sandbox_uploads_dir(
    "thread-456", user_id="user-123"
)
report_path = uploads_dir / "report.pdf"
```

For arbitrary virtual paths, use `Paths.resolve_virtual_path()` and the Gateway's existing path/authorization helpers. Do not join user-supplied paths directly to a runtime directory.

## Docker-outside-of-Docker

When Gateway controls the host Docker daemon, the daemon resolves bind mounts on the host. Set `VASSILFLOW_HOST_BASE_DIR` to the host path corresponding to Gateway's `VASSILFLOW_HOME`. A path valid only inside Gateway is not a valid host bind-mount source. Native Windows paths must retain their drive and separators; use the supplied host-path helpers.

See [uploads](FILE_UPLOAD.md), [configuration](CONFIGURATION.md), and the actual mounts in [docker/docker-compose.yaml](../../docker/docker-compose.yaml).
