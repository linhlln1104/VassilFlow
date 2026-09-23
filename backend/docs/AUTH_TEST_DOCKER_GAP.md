# Container authentication validation

This filename is retained for existing links. It now contains the current container validation checklist rather than a historical claim about one release machine or an untested Docker gap.

## Topology and prerequisites

The [Compose file](../../docker/docker-compose.yaml) runs Gateway with its embedded runtime, the frontend, and nginx, with additional services selected by configuration. There is no separate LangGraph application server or Office renderer.

Use a disposable deployment with a working Docker daemon and Docker Compose. Inspect resolved mounts and environment configuration locally before starting it. Do not publish a resolved Compose configuration containing secrets.

Gateway must run with one worker. `GATEWAY_WORKERS=1` is the supported value; increasing it is a rejected configuration, including with PostgreSQL.

## Checks

| Case             | Procedure                                                                      | Evidence                                                                                                     |
| ---------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Persistent state | Initialize an account, create a thread, and upload a file; restart Gateway     | Account, thread, checkpoint/event history selected for persistence, and artifact remain accessible           |
| Session secret   | Keep the database and `AUTH_JWT_SECRET` or mounted `.jwt_secret`; restart      | Existing unexpired cookie remains valid                                                                      |
| Secret rotation  | Rotate only the signing secret in the disposable deployment                    | Old session is rejected; fresh login succeeds                                                                |
| Owner separation | Create resources as account A; request them as B                               | No cross-owner reads or mutations                                                                            |
| Proxy headers    | Test through external HTTPS and inspect cookie flags                           | Secure/HttpOnly/SameSite behavior matches [auth design](AUTH_DESIGN.md)                                      |
| CSRF             | Submit a protected mutation without and with the matching cookie/header        | Invalid pair rejected; valid authorized pair succeeds                                                        |
| Worker guard     | Start the disposable Gateway with worker count above one                       | Startup rejects the unsupported configuration                                                                |
| IM dispatch      | Connect a configured bot and send a message                                    | Internal authentication works; run owner matches the binding                                                 |
| Reset file       | Run the reset CLI inside Gateway with the deployment environment               | Credential file appears in mounted runtime home with restricted access; plaintext is absent from normal logs |
| Readiness        | Request `/health/ready` with dependencies healthy and deliberately unavailable | Readiness distinguishes usable runtime from unavailable dependencies                                         |

Run reset commands with `docker compose exec` against the correct Compose project and Gateway service. The command is `uv run python -m app.gateway.auth.reset_admin` from `backend/`; inspect `--help` before selecting an account.

## Path verification

Inside the current Gateway container, runtime home is `/app/backend/.vassilflow`. The host source of the mount is configured separately. `database.sqlite_dir` is also separate from runtime home; verify that the selected database is covered by persistent storage. See [paths](PATH_EXAMPLES.md).

A persistent runtime volume can retain `.jwt_secret` without an explicit `AUTH_JWT_SECRET`; an environment secret is not mandatory for restart continuity. Losing both the environment secret and fallback secret invalidates existing sessions.

Record actual image/commit identifiers, mount layout, worker count, configuration choices, and results. Unit tests cover application behavior but cannot establish that a deployment's mounts, network routes, or proxy headers are correct.
