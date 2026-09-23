# Authentication validation plan

This is a repeatable test plan for the current Gateway. It replaces the historical release checklist; it does not assert that any particular deployment or identity provider has passed. Record the commit, configuration, test environment, commands, and results for each validation run.

## Test environment

Use an isolated runtime home and database with two ordinary accounts and one administrator. Keep `VASSILFLOW_AUTH_DISABLED` unset for authentication tests. Start exactly one Gateway worker. Include both direct Gateway access and the actual reverse-proxy/frontend origin. Use disposable accounts for resets, ownership transfer, and deletion cases.

Do not point test cleanup at a working user's runtime directory. A different `VASSILFLOW_HOME` alone is insufficient when `database.sqlite_dir` still points to the working database.

## Automated checks

From `backend/`:

```bash
uv run pytest tests/test_auth.py tests/test_auth_middleware.py tests/test_auth_config.py tests/test_auth_errors.py tests/test_auth_type_system.py tests/test_csrf_middleware.py tests/test_internal_auth.py tests/test_langgraph_auth.py tests/test_oidc_auth.py -q
uv run pytest tests/test_channel_connections_router.py tests/test_channel_connections_repository.py tests/test_channels_router.py -q
```

The first group covers local accounts, sessions, middleware, CSRF, internal identity, and controlled OIDC responses. The second covers binding APIs and ownership persistence. Test collection is the authoritative inventory; do not copy a fixed test count into this guide.

## Manual acceptance matrix

| Area                  | Procedure                                                             | Expected result                                                                             |
| --------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| First boot            | Open setup with an empty test database                                | Setup is available; no generated default password                                           |
| Bootstrap race        | Submit two valid administrator initializations concurrently           | One administrator is created; the other request conflicts                                   |
| Repeat initialization | Call initialize after an administrator exists                         | Rejected; existing credentials remain valid                                                 |
| Registration          | Register a new email; repeat it; try a short/common password          | Ordinary account created once; duplicates and invalid passwords rejected                    |
| Login                 | Submit valid and invalid form credentials                             | Valid login sets HttpOnly session; response body contains no JWT                            |
| Rate limiting         | Fail login five times from one test IP                                | Further attempts are limited for the lockout period                                         |
| Proxy IP              | Repeat through a trusted and untrusted peer with `X-Real-IP`          | Only configured trusted peers influence client-IP resolution                                |
| Session persistence   | Restart with the same database and signing secret                     | Unexpired session remains usable                                                            |
| Invalid session       | Alter the cookie, expire it, or use an invalid token version          | Protected endpoint rejects it when auth bypass is off                                       |
| Password change       | Change password, then replay an older session                         | Current session renewed; older token version rejected                                       |
| Administrator reset   | Run reset CLI against the test account                                | Temporary credentials written to a protected file; old sessions invalidated; setup required |
| Logout                | Log out, then call a protected endpoint with the browser's cookies    | Browser is signed out; copied-token revocation is not promised                              |
| CSRF                  | Omit or mismatch header on a protected mutation                       | Request rejected; valid matching pair succeeds                                              |
| Bootstrap origin      | POST login from an unrelated browser Origin                           | Rejected unless the origin is explicitly allowed                                            |
| Separate ports        | Use frontend and Gateway on supported distinct ports                  | Credentialed requests and CSRF work; ownership remains enforced                             |
| Thread ownership      | Account B reads/updates/deletes account A's thread                    | No cross-owner resource access                                                              |
| Derived resources     | B requests A's run, checkpoint, upload, artifact, feedback, or branch | No content or mutation through a derived-resource route                                     |
| Agent identity        | Change `assistant_id` or conflicting metadata on an existing thread   | Canonical binding is preserved or request rejected                                          |
| Admin operations      | Ordinary account changes deployment MCP/channel configuration         | Role check rejects the request                                                              |
| Internal token        | Send owner override with missing/invalid internal token               | Override does not grant access                                                              |
| Bound IM identity     | Connect a bot identity, then send a message                           | Thread/run belongs to the connected VassilFlow user                                         |
| Unbound IM identity   | Send an ordinary message with required bindings enabled               | No thread/run is created for the unbound identity                                           |
| Binding transfer      | Bind the same platform identity to another test account               | Previous binding loses ownership; no dual active owners                                     |
| Development bypass    | In a separate process, explicitly enable auth bypass                  | Synthetic local identity is used; this result is not auth coverage                          |

## OIDC matrix

With a real configured provider, verify successful login, auto-provisioning policy, denied domain, missing/unverified email, local-email collision, and an account with administrator mapping. Verify callback failure for invalid/expired state, mismatched nonce, invalid issuer/audience/signature, and unsafe external `next` values using controlled test inputs.

An upstream provider failure must not create a partially authenticated session. Test callback URLs through the deployment proxy, including HTTPS cookie attributes and frontend callback navigation. Mocked unit tests do not prove external provider reachability or deployment redirect configuration.

## Container and release evidence

Follow [container authentication checks](AUTH_TEST_DOCKER_GAP.md) for mounted data, restart behavior, secret persistence, proxy headers, and reset-file accessibility. Do not run multi-worker authentication acceptance tests as a supported deployment scenario; the current startup guard requires one worker.

A validation report should distinguish: automated tests passed, manual cases passed, cases failed with reproduction, and cases not run with prerequisites. Never carry a historical pass/fail status forward as evidence for a new commit.
