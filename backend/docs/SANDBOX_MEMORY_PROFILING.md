# Sandbox memory profiling

Use [scripts/sandbox_memory_profile.py](../../scripts/sandbox_memory_profile.py) to collect Kubernetes sandbox capacity evidence. This guide does not claim a measured memory footprint or a preferred alternative runtime.

## Prerequisites and capture

Run from the repository root with Python, `kubectl`, access to the target namespace, and cluster metrics available:

```bash
python scripts/sandbox_memory_profile.py --help
python scripts/sandbox_memory_profile.py --namespace vassilflow --selector app=vassilflow-sandbox --sample empty --include-processes --format markdown
python scripts/sandbox_memory_profile.py --namespace vassilflow --selector app=vassilflow-sandbox --sample after-python --format json
```

Replace namespace and selector with the actual deployment. `--include-processes` executes `ps` inside selected pods; the pod image and access policy must support that command. Save raw JSON with the commit, image identifiers, workload, concurrency, and timestamps.

## Comparable workload phases

Measure an empty ready sandbox, a basic shell command, representative Python imports, Node tasks if used, file generation under `/mnt/user-data/outputs`, release/warm reuse, and the intended concurrency levels. Use the same workload and deployment resources for each runtime candidate.

Kubernetes/container working-set measurements are not exclusive process RSS or PSS. Pod measurements can include multiple containers and charged cache. Process samples explain where memory is used but should not be expected to sum exactly to cgroup totals.

## Evidence matrix

| Area                  | Record                                                                                 |
| --------------------- | -------------------------------------------------------------------------------------- |
| Capacity              | Instance count, total/average/maximum memory, resource requests and limits             |
| Startup               | Ready latency at tested concurrency levels, failures, and retries                      |
| Commands              | Output, timeout, exit status, and cancellation behavior                                |
| Files                 | Read/write/update/list/glob/grep and path-boundary behavior                            |
| Uploads and artifacts | Gateway uploads visible to tools; outputs downloadable through authenticated artifacts |
| Isolation             | Different owners and threads cannot access each other's data                           |
| Cleanup               | Release, idle timeout, restart, orphan reconciliation, and warm reuse                  |
| Operations            | Runtime prerequisites, networking, storage, privileges, and upgrade behavior           |

The existing AIO provider already has warm-pool and cleanup behavior. Measure it before proposing pooling as a missing feature. A lower empty-pod measurement alone does not establish lower cost for a complete VassilFlow workload.

See [container runtimes](APPLE_CONTAINER.md) and [path semantics](PATH_EXAMPLES.md).
