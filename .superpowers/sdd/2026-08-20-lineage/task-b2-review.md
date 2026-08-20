# Batch B2 review — tasks 2 (`resolve_run`) and 4 (`resolve_step`)

Reviewed at `559167e` on branch `h8a-lineage`, 2026-08-20.

**Gates, all run:** `uv run ruff check .` clean; `uv run ruff format --check .` → 84 files;
`uv run mypy` → 47 source files; `uv run pytest` → **2482 passed, 1 skipped, 2 xfailed** (135s).
Tree left clean (`git status --porcelain` empty).

## Verdicts

- **Spec compliance: PASS.** Decision 1's two forms, its single predicate, the locator-as-given
  comparison, and the `latest` asymmetry in both directions are implemented and pinned. Decision 4's
  `shared`/`summary`-only rule, its blanket refusal of a `conditions`-listed step, and the three
  step refusals match the design. Nothing was wired: the whole-branch diffstat is three files
  (`task-b2-report.md`, `src/publishable/lineage.py`, `tests/test_lineage.py`), and
  `grep -rn 'reuse_from\|resolve_run\|resolve_step\|UpstreamResolver' src/` hits only `lineage.py`.
- **Task quality: PASS.** One Major and eight Minors, none blocking. The batch's own reported
  disagreement (the brief's mutation-5 prose) is correct and I reproduced it; the Major is the step
  it stopped short of.

---

## Findings

### Major 1 — the `repo_root` proxy is correct but effectively unpinned; the discriminating fixture does not exist
`src/publishable/lineage.py:118` (the guard) / `tests/test_lineage.py:248`
(`test_containment_guard_control_reads_when_moved_outside_the_repo`).

**Verified by running.** The batch's report is right that the brief's prose is wrong: I applied the
prescribed mutation (`resolves_inside_repo(resolved, find_repo_root(resolved))`) and the **full,
unfiltered** suite gave exactly `3 failed, 2479 passed` — the moved-directory arm, the
absolute-`latest` arm and the containment control — each a `ContractError(code="E-GIT-NO-REPO")`
raised at `src/publishable/provenance.py:47`, i.e. a **crash** because `tmp_path` on this machine has
no `.git` above it. The refused in-repo arm passed unchanged. That is a different mechanism from the
one the plan names, and it pins a different property: *"`find_repo_root` is not reached from an
isolated temp directory"*, not *"the question is answered with the caller's `repo_root`"*.

I then built the fixture the plan's property actually needs and **ran it**: `run_a_project` under
`tmp_path`, plus a sibling `tmp_path/other_repo` with its own `git init` holding a synthesized
upstream, called as `resolve_run(str(other_repo/"up"), output_dir=<unused>, repo_root=project["root"])`.
Precondition checked by printing both paths: `project["root"]` is `tmp_path/proj`, a sibling of
`other_repo`. Unmutated code **reads** it (`record["run_id"]` returned). Under the mutation it
**refuses** with `E-UPSTREAM-REPO-CONTAINED` — an assertion failure, not a crash, because the walk-up
finds `other_repo`'s own `.git`. So a discriminator exists, discriminates, and is absent from the
shipped suite.

The guard itself is correct — it uses the caller's `repo_root` and never re-derives. This is a pin
gap, not a behaviour defect, and it is exactly the shape `CLAUDE.md` names under *a mutation applied
to a proxy* and *a seam named in the brief and instantiated by no fixture*. Remedy: add the
own-repo-sibling arm (it costs one `git init`), or hand it to task 5 with the property named.

### Minor 1 — a docstring claims an assertion on raw text that is a re-render of the parsed structure
`tests/test_lineage.py:154-160` (docstring) and `:168` (the assertion).

The docstring says *"Asserted on the RAW rendered text (`yaml.safe_dump`), not a parsed structure,
per the design's ... rule"*, but `yaml.safe_dump(record)` re-renders the dict `read_run_record`
already parsed — which is precisely the reader normalisation the plan's own rationale for that rule
warns about (*"a YAML-alias defect once shipped past two tests"*). **Verified by running:**
`yaml.safe_dump(yaml.safe_load("a: &id001 moved_run\nb: *id001\n"))` returns
`'a: moved_run\nb: moved_run\n'` — the alias structure is gone before any assertion could see it. The
assertion is also redundant with `record["run_id"] == run_id` on the preceding line: no mutant inside
`resolve_run` can fail one without failing the other, because this function renders nothing. The
substance is defensible (nothing is *written* until task 7) — the false half is the docstring's claim
about what it asserts on. Prefer deleting that clause to rewriting it.

### Minor 2 — one `-RUNID-MISMATCH` message, two faults, and the clause is a non-sequitur for one
`src/publishable/lineage.py:135-140`.

**Verified by running** the renamed-directory fault directly: the message is
`'run_renamed' does not name a run_id — the run directory at … records run_id 'run_…_eeeeeee'.
`latest` is a path, not a run_id, and only the absolute form may follow a path`. The second sentence
is about `latest` and says nothing true about a renamed directory. Both tests
(`test_output_dir_latest_via_relative_form_is_runid_mismatch`,
`test_a_renamed_run_directory_disagrees_with_its_own_record`) assert only `e.value.code`, so nothing
catches it. This is **not** batch 1's trap — see below, there is one raise site — but it is a
message serving two faults where one clause fits only one.

### Minor 3 — `resolve_step`'s docstring states a repeat path that is false for a single-repeat run
`src/publishable/lineage.py:170-173`.

The parenthetical reads `(<run_dir>/<repeat>/<step>/, never under conditions/)`. **Verified by
running** two real runs: with `repeats: [{kind: seed, n: 2}]` the tree holds
`seed40/step01_summarize_units/units.parquet` and `seed47/…` (the claim holds); with `n: 1` it holds
`step01_summarize_units/units.parquet` — **no repeat segment**, because `runner.step_dir_for` appends
`repeat_label` only when repeats are not collapsed. The load-bearing half (*never under
`conditions/`*) is true in both. Correction 9 carries the same partial claim, so a deletion of the
`<repeat>` segment (or "under the run directory") is the smaller repair.

### Minor 4 — a `reference.md` section is cited for a predicate it does not state
`src/publishable/lineage.py:86-88`.

*"§ Lineage between runs gives a locator two readings, told apart by `Path(locator).is_absolute()`
and by nothing else"*. **Verified by reading** `docs/reference.md` § Lineage between runs: it gives
the two readings and it states neither the predicate nor the "and by nothing else" exclusion — those
are the design's Decision 1. Attributing them to the document is the paraphrase-attributed-to-a-section
shape. Cite Decision 1 for the predicate.

### Minor 5 — the real repeat-nested `steps` shape is instantiated by no fixture
`tests/test_lineage.py:268-281` (`_execution_with_all_scopes`).

`run_record._execution_block:91` writes a **repeat**-scoped step as
`cond["steps"][step] = {repeat_label: entry}`, not as an entry. The fixture writes the flat
condition-scoped shape only, so the plan's own claim that *"membership in `conditions` is the whole
test and this slice never has to tell those two apart"* is asserted by nothing. **Verified by
running** against a real record that it holds anyway: a real unswept run's repeat-scoped
`step01_summarize_units` (entry `{"seed47": {...}}`) routes to `E-UPSTREAM-STEP-SCOPED` with the
right message. Code correct, seam untested.

### Minor 6 — a non-mapping `execution` entry is an `AttributeError`, not a diagnostic
`src/publishable/lineage.py:203` (`entry.get("status")`).

`read_run_record` validates only `schema_version` and `run_id`, so a hand-edited record whose
`shared.<step>` is a scalar reaches `.get` on a non-mapping. Read, not run — there is no call site,
and once one exists `execute_plan`'s bare `except Exception` records it as a failed execution rather
than a traceback, so this is low severity. Named here so task 5 decides rather than discovers.

### Minor 7 — the report's arm-count parenthetical
`.superpowers/sdd/2026-08-20-lineage/task-b2-report.md` § Test summary.

*"`tests/test_cli.py -k h8a` (task 11's four guard-pin arms) still passes 3/3"*. **Verified by
running:** that selector reaches three tests, because arm D is
`tests/test_artifacts.py::test_h8a_arm_d_the_shipped_positive_read_upstream_read`. The 3/3 result is
right; the parenthetical mislabels the selector. Arm D is covered by the full-suite run regardless.

### Minor 8 — the relative form skips containment, and a symlink under `output_dir` bypasses the invariant
`src/publishable/lineage.py:132-141`.

**The code matches Decision 1 exactly; the finding is in the decision's grounds.** Decision 1 exempts
the relative branch from `resolves_inside_repo` because it *"inherits the guarantee for free —
`output_dir` was checked at `validate` and again by `run`"*. That holds for a real subdirectory and
not for a symlink, and core itself writes a symlink under `output_dir` (`point_latest`), so one there
is not exotic. **Verified by running:** a git repo with an `in_repo_run/run.yaml` recording
`run_id: run_abc`, plus `<output_dir>/run_abc` symlinked to it, and
`resolve_run("run_abc", output_dir=..., repo_root=repo)` **reads it** — returning a path whose
`.resolve()` sits under `repo_root`, with no containment check anywhere on that branch. The invariant
`CLAUDE.md` calls load-bearing (*`input_dir`/`output_dir` may never resolve inside the git repo*) is
bypassable through the branch the design exempted.

Second half of the same finding: the absolute branch returns `path.resolve()` while the relative
branch returns `output_dir / locator` **unresolved** (`resolved.is_symlink()` was `True` in the probe
above). Task 5 will locate artifacts from that return value and task 7 will record provenance from it,
so the two forms hand back different kinds of path today.

Not a batch-2 compliance failure — `spec-defects.md`-shaped, owner whoever wires the resolver
(tasks 3/5), who should either resolve the relative branch and check containment on both, or record
why the exemption is safe against a symlink.

---

## What I verified and found no finding in

- **Attack 1, the `latest` asymmetry, verified by running in the strong form.** Mutated
  `record.get("run_id") != locator` → `!= resolved.resolve().name` (the weak `resolved.name` form
  would still raise and give a false green). Result:
  `test_output_dir_latest_via_relative_form_is_runid_mismatch` fails with
  `Failed: DID NOT RAISE ContractError` at `tests/test_lineage.py:197` — an assertion-class failure.
  **The converse holds in the same run:** `test_output_dir_latest_via_absolute_form_reads_through_the_symlink`
  passed (21 passed alongside the one failure), and it creates its own symlink and asserts a
  successful read, so a rule refusing `latest` in *both* forms would fail it. Reverted by editing
  back; `diff` against a pre-mutation copy byte-identical; re-ran green.
- **Attack 3, arm C.** Unedited — `tests/test_cli.py` is not in the batch diffstat at all. Green in
  the full run. **Re-broken independently:** routing `summary` into `shared` in
  `run_record._execution_block` fails
  `test_h8a_arm_c_the_execution_blocks_scope_routing_run_and_summary` (1 failed, 2 passed under
  `-k h8a`). Reverted from a copy; tree verified clean.
- **Attack 4, batch 1's trap.** Structurally absent: each of the six codes this batch mints has
  **exactly one** raise site (`grep -o 'code="E-[A-Z-]*"' | sort | uniq -c` —
  `-LOCATOR`, `-RUNID-MISMATCH`, `-REPO-CONTAINED`, `-STEP-SCOPED`, `-STEP-UNKNOWN`,
  `-STEP-INCOMPLETE` all 1; only batch 1's `-RECORD-UNREADABLE` has 3), so no fixture can fall
  through to a second site raising the same code. All six guards deleted in turn, each caught on an
  assertion and isolated to the predicted test: `-REPO-CONTAINED` → `DID NOT RAISE` on the refused
  arm, control still green; `-LOCATOR` → `'E-UPSTREAM-RECORD-MISSING' == 'E-UPSTREAM-LOCATOR'`;
  `-RUNID-MISMATCH` → both its arms `DID NOT RAISE`; `-STEP-SCOPED` →
  `'E-UPSTREAM-STEP-UNKNOWN' == 'E-UPSTREAM-STEP-SCOPED'`; `-STEP-INCOMPLETE` → `DID NOT RAISE`; and
  the fall-back-to-`shared` mutant for `-STEP-UNKNOWN` → `DID NOT RAISE`, the bait file being what it
  would have read. Every wrong-code case is distinguishable **because** the tests assert the code
  rather than the raising.
- **Attack 5, the unswept case, verified by running two real runs plus a real failure.** A real
  record's `execution.shared.<step>` entry is
  `{status, started_at, wall_seconds, attempts}` and `resolve_step` returns
  `<run_dir>/shared/<step>` where `cohort.json` genuinely sits; a real unswept repeat-scoped step
  routes to `-STEP-SCOPED` (not `-STEP-UNKNOWN`, not a silent resolution); and a real run-scoped step
  that raises produces `status: failed` in `shared` and `resolve_step` returns
  `E-UPSTREAM-STEP-INCOMPLETE` with the recorded status quoted. Nothing is mis-routed.
- **Attack 6, brief claims re-verified independently.** (a) `point_latest` symlinks to
  `run_dir.name` with a `latest.txt` fallback — `src/publishable/run_identity.py:40-48`, read;
  (b) `run_a_project` selects `next(results_dir.glob("run_*"), None)` — `tests/test_cli.py:272`,
  read; (c) correction 8's step prefixing — **run**: `extra_steps=["step09_publish"]` produced
  `step02_step09_publish`; (d) correction 9's `_execution_block` shape — **run**, matches, with the
  `<repeat>` nuance in Minor 3; (e) correction 5's class assignment — none of the six codes is in the
  `ArtifactError` set, so all six are `ContractError`, correct; (f) Fixture S's bait is sited through
  the real `sweep.condition_dir_name`, which `runner.step_dir_for:410-414` also uses, so it is the
  location a mutant would actually resolve to rather than a hand-written string.
- **Attack 7, prose.** No docstring in `lineage.py` or `tests/test_lineage.py` claims a § Errors row
  (none exists yet for any `E-UPSTREAM-*` — grepped the four documents and the feasibility analysis),
  names a fixture that does not exist, cites a brief, or says anything "cannot happen". No positional
  locator and no count phrase is added by this batch (the `above`/`below` pair at
  `tests/test_lineage.py:50,67` is batch 1's). No `x`-for-`×`, no en dash, no trailing whitespace or
  tab in the added lines.
- **Attack 8.** No sentence in the diff — code, tests or report — claims a config count moved
  (grepped the added lines for `executable`, `no remaining core-side`, `of nine`, `configs`, and the
  count spellings: no hits).

## What I could not check

- **Whether the `repo_root` `command_run` will hand in is already `.resolve()`d.** `resolves_inside_repo`
  is a pure prefix test, so an unresolved `repo_root` would fail open on macOS (`/tmp` vs
  `/private/tmp`). `find_repo_root` resolves its walk-up, so it is fine today, but the call site is
  task 3's and does not exist yet.
- **Five of the six guard deletions, and the `latest` mutation, were run against
  `tests/test_lineage.py` rather than the full suite.** Justification, stated so it can be
  disagreed with: `grep` shows no importer of `lineage.py` anywhere outside that file, and the one
  lineage mutation I *did* put through the full unfiltered suite (Major 1's) produced failures in
  that file and nowhere else. Three full unfiltered runs were made in total (twice unmutated, once
  under the Major 1 mutation).
- **Anything reachable only through a call site** — `io` has no resolver, so nothing here can reach a
  run. That is the batch's stated seam and it holds.
