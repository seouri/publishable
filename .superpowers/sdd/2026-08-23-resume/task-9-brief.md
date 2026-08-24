## Task 9

**Pointer: Decision 14 binds this task, and it is the second change to a shipped code path in two
slices. Ruling V's refusals are task 16's; the entry point is yours.**

Wire `resumed` into `_execute_prepared`, at the phase-6 sites and the `execute_plan` call **only**:

- `run_dir = resumed.run_dir` instead of `allocate_run_dir(...)`;
- skip the run-start artifact writes — `manifest/`, `environment/`, `config.yaml`,
  `environment/repo_root.txt`, `identity.json`, `sweep.yaml`, `allocation.json` — because they exist
  and § The other files a run writes says they are never touched again;
- order the plan by `sweep.yaml`'s recorded `execution_order` (task 10 supplies the reader) and
  **never** by re-realizing the shuffle;
- filter the plan to triples with no `completed` ledger record;
- `planned=len(full_plan)` — the **unfiltered** length — into `run_status`;
- `results = list(resumed.prior_results) + execute_plan(...)`;
- `manifest = resumed.recorded_manifest`, so phase 8's `verify_manifest` asks whether the inputs moved
  during **this** attempt and `run.yaml`'s `input_manifest_hash` is the original figure;
- `attempts` into `assemble_run_yaml`;
- `resumed.baseline` into the `Observer` (task 13 supplies it).

Add `cli.command_resume(run_dir: Path) -> int` doing, in order: read `identity.json`; resolve the repo
root and the config; refuse a `run.yaml`; compare the three hashes and the manifest; take the lock
(task 14); read the ledger, `sweep.yaml`, `allocation.json` and the probe ledger; reconstitute;
`_prepare_run(config_path, allow_dirty=identity["draft"])`; `_execute_prepared(prepared,
draft=identity["draft"], resumed=…)`. **`isinstance(prepared, Prepared)`, never truthiness** —
`EXIT_OK` is `0`.

**Decision 12: a resumed draft stays a draft.** `allow_dirty` and `draft` both come from the recorded
flag. A resumed draft that recorded `draft: false` would be **citable**, and `report`'s refusal,
`study`'s bundle flag and `diff`'s label would all read it as final.

**Ruling S from H9a still binds: you may not move the arm-plan resolution.** `_resolved_group_axes` and
`arm_members` stay where they are, in their current order; H3c-3's remaining 14 owns that hoist. Task
11 overrides their *results* from `allocation.json` through `dataclasses.replace`; it does not move the
calls. If you find a reason the hoist would make this cleaner, that is a finding to report.

**Must not touch:** the 36-field unpack block (correction 19 — your diff must show it unchanged);
`provenance.py`; `run_status`; the `max_failed_fraction` pin; guard-pin arms.

**Mutations:** pass the **filtered** plan's length as `planned` (caught by arm A: `run_status` returns
`completed` for a run that should be `partial`, and by a deliberate check that the assert still fires
for a genuinely short list); drop the prior results (arm A); rebuild the manifest instead of using the
recorded one (task 12's fixture); re-realize the order (task 10's fixture).

**This batch's review is a real-command review of the `resumed=None` path** — `run` on `main` versus
the branch, leaf by leaf, normalization list in advance, every difference attributed. Green tests are
not the evidence.

---

