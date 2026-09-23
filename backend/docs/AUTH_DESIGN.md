# Authentication and authorization

This document describes the current Gateway implementation. Operational setup is in [AUTH_UPGRADE.md](AUTH_UPGRADE.md); OIDC configuration is in [SSO.md](SSO.md).

## Request identity

[AuthMiddleware](../app/gateway/auth_middleware.py) resolves a validated internal token or a local session cookie and sets request identity plus the runtime user context. Protected APIs use that identity for permission checks and owner-scoped persistence. The harness consumes generic user context and does not import Gateway authentication code.

Health and API-documentation paths, OIDC initiation/callback paths, and the local bootstrap endpoints are public. Public middleware matching includes prefixes; use the source's public-path list when adding a route. Route-level validation still applies to public requests.

`VASSILFLOW_AUTH_DISABLED` is an explicit development bypass. It supplies a synthetic default user and disables CSRF enforcement. In that mode, missing or invalid session cookies can fall back to the default identity. It is not a multi-user authentication mode.

## Local accounts and sessions

The [auth router](../app/gateway/routers/auth.py) implements initialization, registration, form login, logout, password changes, setup status, and the current-user endpoint.

- First boot has no generated administrator account. `/api/v1/auth/initialize` creates the first administrator; concurrent or later initialization attempts are rejected once an administrator exists.
- Registration creates an ordinary local account. Passwords require at least eight characters and must not match the implementation's common-password denylist; the API does not require a particular mixture of character classes.
- [Password hashing](../app/gateway/auth/password.py) supports legacy hash verification and upgrades, with blocking hashing work offloaded from asynchronous request handling.
- Login failures are tracked per client IP in process memory. Five failed attempts trigger a five-minute lockout. A process restart clears this limiter.
- A signed session includes a token version checked against the user record. Password changes and administrator reset increment the version and invalidate older sessions. Password changes issue a new cookie for the current session.
- Logout deletes the browser session cookie. It does not revoke a copied JWT at the server; that token remains subject to expiry and token-version checks.

The signing secret comes from `AUTH_JWT_SECRET` or `{runtime_home}/.jwt_secret`. The fallback is created and persisted with owner-only permissions where supported, so a stable runtime volume preserves sessions across restarts. Changing the secret invalidates existing cookies.

The default JWT lifetime is seven days. Session cookies are HttpOnly and SameSite=Lax. HTTPS requests receive Secure cookies with a lifetime; plain HTTP uses a browser-session cookie, while JWT expiry still applies. Cookie construction uses the forwarded request scheme, so the reverse proxy must control forwarded headers.

## CSRF and browser origins

[CSRFMiddleware](../app/gateway/csrf_middleware.py) uses a readable `csrf_token` cookie and matching `X-CSRF-Token` header for normal POST, PUT, PATCH, and DELETE requests. The CSRF cookie uses SameSite=Strict. Frontend requests must preserve cookies, including when the frontend and Gateway use separate ports on the same host.

Bootstrap POST endpoints for login, logout, registration, and initialization are exempt from double-submit validation but validate a supplied browser Origin against the request origin and configured `GATEWAY_CORS_ORIGINS`. Missing Origin is allowed for non-browser clients. The middleware can refresh the CSRF cookie on authentication responses, including logout; do not assume logout deletes both cookies.

CORS, CSRF, authentication, and resource ownership are separate checks. Allowing an origin does not give its users access to another user's thread.

## Internal requests and channels

[internal_auth.py](../app/gateway/internal_auth.py) defines `X-VassilFlow-Internal-Token`. The token comes from `VASSILFLOW_INTERNAL_AUTH_TOKEN` or is generated for the process. Only a successfully authenticated internal request may use `X-VassilFlow-Owner-User-Id` to select an effective owner. An external request cannot gain ownership by copying the header name.

Channel workers use internal Gateway authentication and the required CSRF pair. A connected platform identity maps to the binding's VassilFlow owner. It does not automatically use the default user's storage. Unbound-message behavior depends on `channel_connections.require_bound_identity` and authentication mode; see [IM connections](IM_CHANNEL_CONNECTIONS.md).

## Authorization and storage

[authz.py](../app/gateway/authz.py) defines resource permissions and owner checks. Thread-bound runs, uploads, artifacts, feedback, and state access must retain those checks. Server-resolved `assistant_id` and trusted capability inputs are additional boundaries, described in [architecture](ARCHITECTURE.md).

Users and authentication data use the application persistence backend. Filesystem memory, agent files, and thread workspaces use owner-scoped runtime paths. Moving the SQL database without its associated runtime files does not migrate the complete application.

## Deployment constraints

Run exactly one Gateway worker, including with PostgreSQL. Authentication is only one of several components that depend on process-local state. `AUTH_TRUSTED_PROXIES` controls whether a peer's `X-Real-IP` can influence login rate limiting; it is not a blanket trust switch for all forwarded headers. Configure the reverse proxy to replace untrusted forwarding headers.

See [automated and manual auth checks](AUTH_TEST_PLAN.md) and [container checks](AUTH_TEST_DOCKER_GAP.md). Those documents are validation procedures, not claims that a deployment has passed them.
