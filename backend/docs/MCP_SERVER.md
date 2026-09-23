# MCP server configuration

MCP integrations extend the tool catalog through a local `extensions_config.json`. Copy [extensions_config.example.json](../../extensions_config.example.json) to that filename in the repository root, then configure only the servers needed by the deployment. `VASSILFLOW_EXTENSIONS_CONFIG_PATH` selects another file.

The schema is [extensions_config.py](../packages/harness/vassilflow/config/extensions_config.py); transport construction is [mcp/client.py](../packages/harness/vassilflow/mcp/client.py).

## Transports

Supported transport names are `stdio`, `http`, and `sse`. Stdio requires `command` and optional `args`/`env`; HTTP and SSE require `url` and may supply `headers` and OAuth configuration.

This disabled example is a template for an application-owned server. Replace its executable and arguments before enabling it:

```json
{
  "mcpServers": {
    "warehouse": {
      "enabled": false,
      "type": "stdio",
      "command": "warehouse-mcp",
      "args": [],
      "env": { "WAREHOUSE_TOKEN": "$WAREHOUSE_TOKEN" },
      "tool_call_timeout": 60,
      "routing": {
        "mode": "prefer",
        "priority": 50,
        "keywords": ["orders", "warehouse"]
      },
      "tools": {
        "query": {
          "routing": { "priority": 90, "keywords": ["order status"] }
        }
      }
    }
  }
}
```

Environment references must be available to the process loading the configuration. The server command must be installed and reachable in Gateway's execution environment, including inside Docker when applicable.

## Discovery, policy, and timeouts

Enabled servers contribute discovered tools to the runtime catalog, subject to Agent tool policy and configured deferred discovery. `tool_search` can promote deferred schemas into the model's visible tool set. Enabling a server does not override a restricted Agent's MCP allowlist.

Routing hints are soft model preferences, not authorization. `mode: off` disables a hint; `prefer` enables it. Priority ranges from 0 to 100. Use brief descriptive keywords without secrets or instructions. Per-tool overrides use the server's original tool name, before the server prefix is added.

`tool_call_timeout` applies to individual stdio calls. HTTP/SSE use their transport timeout behavior; a stdio-only timeout configured on those transports is ignored with a warning. Stdio sessions are pooled; the HTTP/SSE lifecycle differs and should not be inferred from the stdio implementation.

After editing configuration, reset the MCP cache through the admin API or restart Gateway when validating a changed server. Do not assume an already-running graph has adopted a newly edited schema. The endpoints are `/api/mcp/config` and `/api/mcp/cache/reset`; authentication, CSRF, and role checks apply.

The configuration file uses `mcpServers`, while the HTTP update body uses `mcp_servers`. API-managed stdio commands must be single executable names from an allowlist (default `npx` and `uvx`); `VASSILFLOW_MCP_STDIO_COMMAND_ALLOWLIST` adds names. The custom executable in the file example above requires that additional configuration if submitted through the API. Local configuration files are a separate trusted boundary. GET responses mask environment/header values and OAuth secrets; the update router preserves existing masked values according to its merge rules.

## HTTP/SSE OAuth

The integration supports configured `client_credentials` and `refresh_token` grants with token acquisition and refresh. This is not a browser authorization-code setup flow.

```json
{
  "mcpServers": {
    "warehouse": {
      "enabled": false,
      "type": "http",
      "url": "https://warehouse.example.com/mcp",
      "oauth": {
        "enabled": true,
        "token_url": "https://identity.example.com/token",
        "grant_type": "client_credentials",
        "client_id": "$MCP_CLIENT_ID",
        "client_secret": "$MCP_CLIENT_SECRET",
        "scope": "warehouse.read",
        "refresh_skew_seconds": 60
      }
    }
  }
}
```

These are placeholder endpoints. Use the actual provider endpoints and least required scope. See [mcp/](../packages/harness/vassilflow/mcp/) for token handling and supported extra parameters.

## Interceptors

The optional `mcpInterceptors` field accepts a `module:builder` string or a list of strings. Each no-argument builder returns an async interceptor callable, or `None` to skip. Invalid imports, builder failures, and non-callable results are logged and skipped. Therefore, this optional hook must not be the sole fail-closed authorization boundary for a sensitive tool.

Interceptors follow the installed MCP adapter's request/handler interface. Read trusted request context when attaching credentials; do not forward arbitrary model-authored metadata as authorization. Configuration and server implementations are trusted code.

## Files and workspace boundaries

Use the built-in file tools for VassilFlow thread workspaces. This implementation does not publish per-thread MCP Roots to a generic filesystem server or promise that `/mnt/user-data/...` is understood by every external server. Stdio workspace/result adaptation is implemented in [mcp/tools.py](../packages/harness/vassilflow/mcp/tools.py), but it is not a substitute for a server's own filesystem restrictions.

See [path conventions](PATH_EXAMPLES.md), [guardrails](GUARDRAILS.md), and [Agent policy](ARCHITECTURE.md).
