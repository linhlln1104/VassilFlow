# Glob and grep tools

Status: implemented. The historical RFC filename is retained. These tools search through the sandbox abstraction without requiring the model to construct a shell command.

## Tool contracts

The tool definitions are in [sandbox/tools.py](../packages/harness/vassilflow/sandbox/tools.py). The runtime argument is injected by the graph; the model supplies the arguments below.

| Tool   | Required arguments               | Optional arguments                                                      |
| ------ | -------------------------------- | ----------------------------------------------------------------------- |
| `glob` | `description`, `pattern`, `path` | `include_dirs=false`, `max_results=200`                                 |
| `grep` | `description`, `pattern`, `path` | `glob=null`, `literal=false`, `case_sensitive=false`, `max_results=100` |

`path` is an absolute search root visible to the sandbox. Glob patterns are relative to that root. Grep searches matching lines in text files; its default is case-insensitive regular-expression matching. Set `literal: true` for a plain-text search.

Example model tool arguments:

```json
{
  "description": "Locate Python source files",
  "pattern": "**/*.py",
  "path": "/mnt/user-data/workspace",
  "max_results": 100
}
```

```json
{
  "description": "Find configuration references",
  "pattern": "VASSILFLOW_HOME",
  "path": "/mnt/user-data/workspace",
  "glob": "**/*.py",
  "literal": true,
  "case_sensitive": true,
  "max_results": 50
}
```

## Results and limits

Glob returns formatted matching paths. Grep returns formatted file/line matches. These tool responses are text for the model, not a separate Gateway REST search API. Results report truncation; narrow the root or pattern when it occurs.

Requested counts are clamped by implementation limits and configured per-tool limits. Do not interpret a truncated response as a complete repository inventory. Invalid patterns and inaccessible roots return tool errors.

Local mode validates and maps virtual paths using thread data and configured read roots. Returned host paths are masked back to their virtual equivalents. Other sandbox providers implement the same search interface. Async tool adapters initialize the sandbox asynchronously and offload synchronous work.

## Extension rules

A new sandbox provider must implement compatible glob/grep behavior and preserve owner/path boundaries. Do not add unrestricted host-shell fallbacks when a provider lacks a search capability. Check the local and AIO implementations under [sandbox](../packages/harness/vassilflow/sandbox/) and [aio_sandbox](../packages/harness/vassilflow/community/aio_sandbox/).

For path meanings, see [PATH_EXAMPLES.md](PATH_EXAMPLES.md). For authorization, see [guardrails](GUARDRAILS.md) and the [Agent policy contract](ARCHITECTURE.md).
