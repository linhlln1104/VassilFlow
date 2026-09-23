# Blocking I/O detection

Static and runtime detectors help keep synchronous filesystem, database, and network work off the asynchronous event-loop thread. Neither detector proves that every runtime path is nonblocking.

## Static inventory

From the repository root:

```bash
make detect-blocking-io
```

The root target delegates to [backend/Makefile](../Makefile), which runs [scripts/detect_blocking_io_static.py](../../scripts/detect_blocking_io_static.py). Its output is `.vassilflow/blocking-io-findings.json` under the repository root, even though the command executes from `backend/`. The Make target fixes this report path; it is not the launcher-selected runtime home.

Review findings before changing code. The static detector reports candidates and can include synchronous helpers that are already invoked off the loop. A finding is not proof of an observed event-loop stall.

## Runtime gate

From `backend/`:

```bash
make test-blocking-io
```

The tests in [tests/blocking_io](../tests/blocking_io/) exercise production async entry points under Blockbuster. Detector setup is centralized in [blocking_io_runtime.py](../tests/support/detectors/blocking_io_runtime.py), which scans `app` and `vassilflow` modules.

The gate only protects paths that tests execute. Add a test when a confirmed blocking surface lacks coverage. Add a detector rule only when the blocking primitive itself is not intercepted; adding rules cannot compensate for never calling the production path.

## Maintenance workflow

1. Run the static inventory and inspect the real caller chain.
2. Reproduce the blocking operation through its async production entry point.
3. Move blocking work to an appropriate executor or use a native asynchronous implementation.
4. Add a focused runtime regression that fails if the operation returns to the event loop.
5. Run the affected tests and the blocking-I/O suite.

Use real temporary filesystem inputs when filesystem operations are the issue. Mock external service boundaries, not the exact I/O operation the test is intended to catch. Do not wrap the production entry point in a test-only `asyncio.to_thread()` call that hides the bug.

Existing coverage includes checkpointer setup, subagent skill loading, JSONL events, upload paths, and channel state operations. Consult the current test directory instead of relying on a frozen coverage count. [scan_changed_blocking_io.py](../../scripts/scan_changed_blocking_io.py) supports review of changed code; run its `--help` for current options.
