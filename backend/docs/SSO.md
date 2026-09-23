# OpenID Connect single sign-on

VassilFlow supports single sign-on through OpenID Connect (OIDC), using the OAuth 2.0 authorization-code flow. OIDC is optional; local authentication remains available. The implementation lives in [Gateway auth](../app/gateway/auth/) and the [auth router](../app/gateway/routers/auth.py).

## Configuration

This configuration fragment illustrates a local Keycloak realm. The realm, confidential client, and redirect URI must already exist at the identity provider; the example does not install a provider.

```yaml
auth:
  oidc:
    enabled: true
    frontend_base_url: http://localhost:2026
    providers:
      keycloak:
        display_name: Keycloak
        issuer: http://localhost:8080/realms/vassilflow
        client_id: vassilflow
        client_secret: $OIDC_CLIENT_SECRET
        redirect_uri: http://localhost:2026/api/v1/auth/callback/keycloak
        scopes: [openid, email, profile]
        token_endpoint_auth_method: client_secret_post
        auto_create_users: true
        require_verified_email: true
        allowed_email_domains: []
        admin_emails: []
        pkce_enabled: true
        nonce_enabled: true
```

Provider IDs such as `keycloak` appear in API paths. `client_id` and `issuer` are required. `client_secret`, explicit `redirect_uri`, and endpoint overrides are optional in the [schema](../packages/harness/vassilflow/config/auth_config.py). Supported token endpoint authentication methods are `client_secret_post`, `client_secret_basic`, and `none`.

Use the deployment's external HTTPS origin in real deployment configuration. Gateway must be able to reach the provider's discovery, token, and JWKS endpoints, while the browser must reach its authorization endpoint. In Docker, `localhost` inside Gateway is the Gateway container; browser and container issuer routing must be planned consistently.

## Flow and validation

1. The frontend lists enabled providers through `/api/v1/auth/providers`.
2. `/api/v1/auth/oauth/{provider}` prepares signed, short-lived login state and redirects to authorization.
3. The callback validates state and expiry, exchanges the code, and validates the ID token against provider metadata and signing keys.
4. The service checks issuer, audience, expiry, nonce when enabled, and the subject returned by userinfo when used.
5. Account provisioning applies verified-email, allowed-domain, automatic-creation, and administrator-email settings.
6. Gateway sets its normal local session cookie and redirects to the frontend authentication callback.

PKCE and nonce are enabled by default. The OIDC state cookie is HttpOnly, SameSite=Lax, and has a five-minute lifetime. An unsigned token (`alg: none`) is not accepted. Endpoint overrides do not turn off ID-token verification.

`allowed_email_domains` and `admin_emails` are authorization-related configuration, not display settings. Review them with the provider's email verification behavior. External accounts are identified by provider and subject. Matching a local account's email does not automatically link or take over that account; collisions can return a conflict.

The frontend callback is `/auth/callback`; it resolves the local session before navigation. The `next` parameter is validated as an internal destination to prevent an arbitrary external redirect.

## Operations

Keep the client secret on Gateway through environment substitution. Use the current configured callback URL exactly at the provider; a hostname, scheme, port, or path mismatch can fail the code exchange. Restart after changing deployment environment values.

OIDC signs users into a VassilFlow session. Logout clears that local browser session; this implementation does not promise provider-wide logout or revocation of copied local JWTs. See [session limits](AUTH_DESIGN.md).

## Validation

From `backend/`:

```bash
uv run pytest tests/test_oidc_auth.py tests/test_auth.py tests/test_csrf_middleware.py -q
```

These tests validate the local implementation with controlled provider responses. Complete a real-provider login, rejected-email case, state/nonce failure case, and logout in the target deployment before treating that provider configuration as verified. See [AUTH_TEST_PLAN.md](AUTH_TEST_PLAN.md).
