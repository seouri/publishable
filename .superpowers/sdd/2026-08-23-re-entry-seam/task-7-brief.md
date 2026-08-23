## Task 7

**Ruling R binds this task (design Decision 1): `dry-run` prints step directories and fixed files,
never `io.write` names from step bodies.** § Operation commands promises *"every artifact path that
would be written"*, which needs the calls inside user Python — and `reference.md` itself says core
never inspects the body of user Python. **A promise that requires breaking a stated non-promise is the
document being wrong**, and the document changes first (task 9 edits the row; task 12 edits the
transcript). **The narrowed output must say what it omits and why** — a line that quietly printed less
would reproduce the defect in the direction the reader cannot see.

**Ruling S also binds:** you call `_prepare_run`; you may not move the arm-plan resolution.

**Design Decisions 8 and 16 bind:** `dry-run` passes `allow_dirty=True` (it writes no record, so there
is no identity claim for the gate to protect), and it prints **no comparison list** — nothing here may
reach `contrasts.resolve_contrasts`, which is reached only from phase 8 and whose unguarded
unhashable-side crash is a standing precondition on H9.

**What to build.** `cli.command_dry_run(config_path: Path) -> int`, calling
`_prepare_run(config_path, allow_dirty=True)`, then printing — derived from `Prepared`, nothing
transcribed:

```
sweep: <n> conditions (baseline + grid) × <m> repeats = <e> executions
  <one line per condition: index_label and its values>
repeats: <the repeat plan, from `prepared.repeats`>
  seeds: [...]  (auto, from design digest)
  comparisons: paired (allocation: within)
steps: <step (scope) -> ...> from `prepared.plan`
statistics: basis units (n=<resolved> resolved); <derived-by note>
scale:  <u> unit-executions (<e> executions × <k> units handed to each)
would create <d> step directories under <output_dir>/<experiment>/run_.../
  <the fixed files a run writes, named>
artifact files inside a step directory are named by `io.write` in step code and
  are declared nowhere in the config, so they cannot be listed before the run
```

The step-directory count is **one per planned (step, condition, repeat) triple**, which is exactly
what `runner.step_dir_for` returns — call it, do not re-derive the path scheme. Print the directories
themselves, not only the count. The fixed files are `config.yaml`, `sweep.yaml`, `manifest/input.json`,
`environment/pyproject.toml`, `environment/repo_root.txt`, `executions.jsonl`, `run.yaml`, plus
`environment/uv.lock` when a lockfile resolved, `allocation.json` when a drawn axis is declared, and
`apparatus/probes.jsonl` when a probe is declared. **Derive each condition from `Prepared`, never from
a hard-coded list** — `lock_path is not None` decides the lockfile, and a reserved NAME standing in for
a structural fact is the proxy move this repo keeps paying for.

**`unit-executions` is task 8's.** Print the line, wired to task 8's function, and leave the
narrowing to that task if you are dispatched in parallel; otherwise build both.

**Fixture U** — the step-directory list **and the fixed-file list**, both compared **set to set**
against the tree a real `run` of the same config creates, not against a count and not against a
literal: a count literal that happens to match is the fixture-agrees-with-the-bug shape. **The
fixed-file list has three conditional branches and each needs a config that exercises it** —
`environment/uv.lock` (`lock_path is not None`), `allocation.json` (a drawn axis declared), and
`apparatus/probes.jsonl` (a probe declared). Without them the command's whole output rests on three
untested predicates, which is the *seam named in the brief and instantiated by no fixture* shape:
naming a branch is not testing it.

**Mutation:** drop the degenerate-level collapse by calling `step_dir_for(..., collapse_repeats=True)`
unconditionally → Fixture U must fail. Choose the fixture's repeat count so `True` and `False` give
different trees (n ≥ 2), and **say in the report why n = 1 would have made the mutation blind.**

**Must not touch:** `runner.py`, `apparatus.py` (task 10 owns the probe), `NOT_BUILT_COMMANDS` and
`OPERATION_COMMANDS` (task 9), any `*.md` (tasks 9 and 12).

---

