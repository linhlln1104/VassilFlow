# Memory Settings review

Use [memory-settings-sample.json](memory-settings-sample.json) to review the Memory Settings interface with fictional data. It is a UI fixture, not a profile of a real user and not a record of completed implementation work.

## Prepare isolated data

Start VassilFlow locally using [setup](SETUP.md), then sign in to a disposable account. Export or back up its existing memory before importing the sample through Settings or the authenticated memory import API. Import replaces the stored memory document for the selected scope; it is not a merge-by-fact operation. Read the current schema before scripting it.

The legacy loader remains available from the repository root:

```bash
python scripts/load_memory_sample.py --help
```

When using it, supply `--target` with the exact test account's resolved memory file. Its default is `backend/.vassilflow/memory.json`, or `{VASSILFLOW_HOME}/memory.json` when that variable is set. Those are global/legacy targets and do not normally populate a signed-in account's `{runtime_home}/users/{user_id}/memory.json`.

The loader creates a timestamped backup of an existing target unless `--no-backup` is supplied. Stop concurrent memory updates before writing the file directly, then reload memory in the application. Prefer authenticated import for routine UI review.

## Review checklist

1. Confirm context/history summaries and the fixture's ten facts render without overflow.
2. Search for `review`, clear the search, and check that the complete fact list returns.
3. Combine category/confidence filters and verify the empty-results state.
4. Edit `fact_review_010`; reload and verify persistence.
5. Delete `fact_review_009`; verify other facts remain.
6. Export the resulting memory and confirm it is valid JSON with the expected edits.
7. Clear memory in the disposable account and check both the empty state and a reload.
8. Sign in as another account and confirm the fixture did not populate that account's memory.

Restore the exported backup or remove the disposable account's sample through the supported UI/API when finished. Do not delete a shared runtime directory as cleanup.
