# Authentication setup and upgrade operations

This guide applies to the current embedded Gateway runtime. [Authentication design](AUTH_DESIGN.md) explains the session and ownership model; [SSO](SSO.md) covers external identity providers.

## Initialize a new deployment

1. Configure a persistent database and runtime directory using [setup](SETUP.md).
2. Start one Gateway worker and open the application through the configured frontend origin.
3. Complete the first-administrator setup page. The backend creates no default administrator/password at startup.
4. Confirm `/api/v1/auth/me` returns the intended account and that creating a thread works.

Local initialization and registration use JSON email/password fields. Local login uses form `username`/`password`. The session is an HttpOnly cookie; do not store a returned JWT in browser storage because the login body does not return one.

## Upgrade an existing deployment

Before upgrading, back up the application database, runtime directory, local configuration, and the signing secret. For SQLite, use a consistent database backup rather than copying only the main database file while WAL writes are active. Keep the filesystem backup aligned with that database snapshot.

Review `make config-upgrade` output and keep the existing `AUTH_JWT_SECRET` or persisted `.jwt_secret` when sessions should survive. Restart Gateway for database, checkpointer, run-event, sandbox, and channel configuration changes.

Startup can assign ownerless legacy LangGraph thread-store metadata to an existing administrator. This compatibility step does not constitute a full filesystem migration or a transfer of all historical domain data. Inspect actual paths and owners before moving legacy files; see [path examples](PATH_EXAMPLES.md).

Existing IM deployments should review `channel_connections.require_bound_identity`. With bindings enabled, its default is true: authenticated deployments reject ordinary unbound messages before creating runs. Intentionally open/operator-owned bots must configure their policy explicitly.

## Reset a local administrator

Run from `backend/` with the same environment, database configuration, and runtime home as the application:

```bash
uv run python -m app.gateway.auth.reset_admin --help
uv run python -m app.gateway.auth.reset_admin
```

Use the command's `--email` option when selecting an account is necessary. The reset writes temporary credentials to `{runtime_home}/admin_initial_credentials.txt` using owner-only file permissions where supported and prints the path, not the password. Read the file locally, sign in, and complete the required password change. Remove the temporary credential file after recovery.

The reset increments the account's token version, invalidating older sessions. It is for local accounts; an external identity provider manages its own account credentials.

## Troubleshooting

| Symptom                                              | Checks                                                                             |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Session lost after restart                           | Same database, JWT secret, runtime mount, cookie hostname, and request scheme      |
| Mutating request returns 403                         | Session cookie, current CSRF cookie/header pair, origin, and route permissions     |
| Login returns 429                                    | Per-IP failed-login limiter; trusted proxy configuration                           |
| Initialization returns conflict                      | An administrator already exists or another initialization request won              |
| Memory or files appear missing                       | Effective user ID and runtime home; SQL and filesystem paths may differ            |
| Works through nginx but not a separate frontend port | Credentialed fetch, allowed origin, hostnames, SameSite behavior, forwarded scheme |

Do not delete the database to fix a login problem. Use a separate runtime/database for disposable validation, and use the reset command for account recovery.
