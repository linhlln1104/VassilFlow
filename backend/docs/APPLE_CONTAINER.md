# Apple Container and Docker sandbox runtimes

The AIO sandbox provider can use a local container runtime or a remote provisioner. This guide describes the current local runtime selection, not a performance comparison or an installation guide for an external container product.

## Selection

`AioSandboxProvider` delegates local lifecycle operations to [LocalContainerBackend](../packages/harness/vassilflow/community/aio_sandbox/local_backend.py). On macOS it checks `container --version`; a successful check selects Apple Container. Otherwise it selects Docker. Other platforms use Docker.

This is startup-time selection. A successful version check does not prove that the daemon, image, networking, or mounts are ready. Runtime command failures do not imply an automatic retry through a different provider. If `sandbox.provisioner_url` is set, the provider selects its remote backend instead of this local path.

## Configure and prepare

```yaml
sandbox:
  use: vassilflow.community.aio_sandbox:AioSandboxProvider
```

Use the image and optional settings documented in [config.example.yaml](../../config.example.yaml) and the [provider source](../packages/harness/vassilflow/community/aio_sandbox/aio_sandbox_provider.py). Ensure the chosen image supports the host architecture. Do not infer universal image compatibility or better performance merely from the selected runtime.

From the repository root:

```bash
make setup-sandbox
```

The [setup script](../../scripts/setup-sandbox.sh) pulls the configured/default image using available tooling. A successful pre-pull is useful preparation but does not validate a complete agent workload. Start the chosen container service separately and check its availability before running Gateway.

## Paths and networking

Thread workspace, uploads, and outputs are mounted under `/mnt/user-data`. Docker-outside-of-Docker requires a host-visible mount source and a reachable sandbox address. See [path mapping](PATH_EXAMPLES.md) and [configuration](CONFIGURATION.md) for `VASSILFLOW_HOST_BASE_DIR` and `VASSILFLOW_SANDBOX_BIND_HOST`.

Docker mount arguments are constructed separately from Apple Container arguments, including Windows drive handling. Do not assume the two CLIs accept every flag identically.

## Lifecycle and troubleshooting

The provider tracks active sandboxes, a warm pool, capacity, idle cleanup, and orphan reconciliation. Acquire/reuse verifies cached containers; confirmed dead entries are dropped so a replacement can be provisioned. A transient runtime inspection failure is not proof that a container is dead. Discovery does not adopt a container it cannot verify.

If provisioning fails, check the selected runtime, service availability, image architecture, port allocation, host mount paths, and Gateway reachability in that order. Inspect the provider logs without exposing container environment secrets. Do not rename or move an installed system CLI to force runtime selection.

The repository includes [cleanup-containers.sh](../../scripts/cleanup-containers.sh). It stops containers matching a prefix; inspect the target deployment before invoking cleanup, especially on a shared host. `make stop` also performs development cleanup.

## Validation

From `backend/`:

```bash
uv run pytest tests/test_aio_sandbox_provider.py tests/test_docker_sandbox_mode_detection.py -q
```

These regression tests do not replace live runtime checks. Verify command execution, upload visibility, artifact download, owner/thread separation, release, and warm reuse with the selected runtime. Use [memory profiling](SANDBOX_MEMORY_PROFILING.md) for measured capacity comparisons.
