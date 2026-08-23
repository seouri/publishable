# H9a tasks 5–9 — report (batch 4)

**Status: all five PASS. Full suite green after each commit.**

| Task | Commit | What it is |
|---|---|---|
| 5 | `5bb8009` | `draft`'s three readers, against a real draft |
| 6 | `41208be` | Fixture R, and § Draft runs' unhonourable conjunction corrected |
| 7 | `b5a2293` | `command_dry_run` — the narrowed promise, and it says what it omits |
| 8 | `985971a` | Fixtures S and T — the `unit-executions` agreement pin |
| 9 | `a684f1b` | `dry-run` dispatches; § Operation commands' row carries the narrowed promise |

**Test summary.** Baseline before this batch: **2992 passed, 1 skipped, 2 xfailed** — read from a
run, and it matched. After each commit: task 5 → 2995, task 6 → 2996, task 7 → 3003, task 8 → 3005,
task 9 → **3010 passed, 1 skipped, 2 xfailed**. Delta **+18** tests (3 / 1 / 7 / 2 / 5). Every count
below was **read off a FULL, UNFILTERED `uv run pytest`**, never a `-k`-scoped run. Gates clean
before each commit: `ruff check .`, `ruff format --check .`, `mypy` (52 source files), `pytest`.

Files touched across the batch: `src/publishable/cli.py`, `tests/test_cli.py`, `docs/reference.md`.
**`provenance.py`, `runner.py`, `apparatus.py`, `report.py`, `diff.py`, `study.py` and
`run_record.py` are byte-unchanged over `16518aa..HEAD`** (`git diff` on those six paths is empty) —
so `git_provenance`, its `-c` neutralization flags and `HASHED_TREES` did not move, and neither did
`execute_plan`'s narrowing. `docs/feasibility-llm-growth-studies.md` was not opened.

---

## Task 5 — `draft`'s three readers, against a real draft

`_h9a_t5_clean_and_draft` builds ONE project on `run_a_project` (this module's single end-to-end
driver) and produces two records: a `run` of the committed tree, then a `draft` after a file under
`src/**` is edited. The draft comes second because `run` refuses a dirty tree. The helper asserts its
own premise — one record carries `draft: true`, the other `false` — so a reader test that finds no
difference has found a reader defect rather than a fixture that never differed.

**The synthesized-record tests this is a difference from, named as instructed** (grepped
`grep -rn 'draft' tests/test_report.py tests/test_diff.py tests/test_study.py`, every hit attributed):

| Existing test | What it hand-edits | New test beside it |
|---|---|---|
| `tests/test_report.py::test_fixture_t_a_draft_run_is_refused_not_rendered` | `draft: true` onto a completed record | `test_h9a_t5_report_refuses_a_real_draft` |
| `tests/test_report.py::test_fixture_t_bundle_flags_a_draft_member_at_exit_0` | same, inside a bundle | `test_h9a_t5_a_bundle_flags_a_real_draft_member_and_still_renders` |
| `tests/test_diff.py::test_h8b_a_draft_run_earns_the_draft_label_in_the_header` | same, then `_load_side` | `test_h9a_t5_diff_labels_a_real_draft_on_one_side_only` |
| `tests/test_study.py:169` `"draft": False` | a synthetic member record in a bundle fixture — not a draft reader; attributed and left | — |
| `tests/test_report.py:562` "this task's own first draft" | prose, not the key; attributed and left | — |

**Three mutations, each on a reader's own `record.get("draft") is True` test, each against the full
suite. Each failed TWO tests, not one — and that pairing is the finding**: the synthesized-record
test and the real-draft test are two ends of one check, which is the honest form of "new coverage".
The brief's "confirm exactly the corresponding test fails" is wrong against the shipped suite, and a
report of one failure would have been a miscount.

| Mutation | Read from the full run | Failing tests |
|---|---|---|
| `report.py` single-run refusal → `if False:` | **2 failed, 2993 passed** | `test_h9a_t5_report_refuses_a_real_draft`, `test_fixture_t_a_draft_run_is_refused_not_rendered` |
| `report.py` `_bundle_header_section` flag → `if False:` | **2 failed, 2993 passed** | `test_h9a_t5_a_bundle_flags_a_real_draft_member_and_still_renders`, `test_fixture_t_bundle_flags_a_draft_member_at_exit_0` |
| `diff.py` `_header_line` label → `if False:` | **2 failed, 2993 passed** | `test_h9a_t5_diff_labels_a_real_draft_on_one_side_only`, `test_h8b_a_draft_run_earns_the_draft_label_in_the_header` |

**What a property-PRESERVING arm does, for each:** rewriting `is True` as `== True` on the same
expression. `draft` is a real `bool` in every record `assemble_run_yaml` writes, so both spellings
agree and the suite stays green — which is the shape that tells you the mutation above measured the
guard rather than the comparison operator.

Each mutation was reverted **by editing the line back**, verified byte-identical against a
pre-mutation copy (`diff`), and the batch's final state re-verified by **re-running** the full suite
(2995 passed at task 5's commit).

**Traps handled by copying where the sibling sits, not only what it calls.** Bundle member names are
`sensitivity` and `primary` — neither carries a substring of `draft` — and the flagged member's block
is split off on `## primary` before asserting `"not reachable from any commit"`, which is
`test_fixture_t_bundle_flags_a_draft_member_at_exit_0`'s own recorded fix (its first version named the
member `draft_run` and asserted bare `"draft" in out`, which `## draft_run` already satisfied).
`diff`'s label is asserted **per side**, on `line.split()` of each header line found by its leading
`A`/`B` letter, never as a substring of the whole output.

**Both directions everywhere.** `report` over the same project's clean run must still exit `0` and
render `## Conditions`; the bundle's clean member must still render its sections; `diff`'s B side must
NOT carry the token.

`study add` printed **no** `W-STUDY-COMMIT-MISMATCH` for either member here (the config is committed
by `run_a_project`'s own `git add .`), so nothing was asserted away — named because the notice was a
live possibility and its absence is a fact about this fixture, not a rule.

**`report.py`, `study.py` and `diff.py` were not edited** — only mutated and reverted. No reader was
found wrong.

---

## Task 6 — Fixture R, and the corrected conjunction

**Fixture R** (`test_h9a_fixture_r_a_draft_of_a_clean_tree_records_code_dirty_false`) verifies its own
premise with the gate's OWN pathspec — `git status --porcelain -- src templates` inside the project,
asserted empty — *then* `main(["draft", cfg])`, asserting `record["draft"] is True`,
`record["provenance"]["git"]["code_dirty"] is False`, and no notice on **stderr**. The absence is
paired with something that must report: `"run.yaml →"` on stdout.

**Stated as a difference, not a count.** `test_h9a_fixture_q_a_draft_on_a_clean_tree_records_code_dirty_false`
(task 3) already asserts the same three facts. Fixture R adds exactly two things: the **verified
premise**, so a passing `code_dirty is False` cannot be a tree that was dirty in a way the gate could
not see; and dispatch through `main`, which task 3 could not do.

**Sweep for `code_dirty`, over the six files NAMED INDIVIDUALLY (never `*.md`), every hit attributed:**

| File | Hits | Attribution |
|---|---|---|
| `README.md` | 0 | — |
| `docs/design-principles.md` | 0 | — |
| `docs/experimental-designs.md` | 0 | — |
| `docs/reference.md` | 2 | `:680` — § The two files' `run.yaml` example comment (*"`run` refuses if true, `draft` permits it"*): **TRUE of the code, kept**. Deleting a true claim is not licensed. `:3741` — § Draft runs' conjunction: **the false half, deleted** |
| `CLAUDE.md` | 1 | `:322` — a `core.fileMode`/`core.autocrlf` note about an unedited tracked file reading dirty. About git config, not about `draft`; left |
| `docs/feasibility-llm-growth-studies.md` | 0 | — |

I also swept `draft: true` over the same six files: `reference.md:575` (§ Errors, `E-REPORT-DRAFT`),
`:3123` (§ Three hashes' argument for reading the working tree), `:3675` (§ Operation commands' `draft`
row) and `:3741`. Only `:3741` carried the falsehood.

**What § Draft runs now says.** The conjunction's false half is **deleted** rather than rewritten
(*prefer deleting a claim to rewriting it*), and one paragraph is added saying which key is which:

> Draft runs are recorded with `draft: true`, `report` refuses to render one as a final result, and
> `diff` labels it. […]
>
> **`draft: true` is the flag; `code_dirty` is a measurement.** `draft: true` is written
> unconditionally, and it is what all three readers key on. `git.code_dirty` records what the tree
> actually was, so a `draft` of a clean tree records `false`: the command *permits* a dirty tree rather
> than asserting one. Forcing the flag would make a `provenance` figure lie about the tree — the one
> thing `provenance` is for — and would leave `diff` unable to compare a clean draft against the `run`
> of the same commit.

**Mutation** — force `code_dirty=True` under `draft` (`dataclasses.replace` on `prepared.git` inside
`command_draft`; a reverted mutation is not an edit, and `cli.py` was not otherwise touched by task 6).
Full suite: **3 failed, 2993 passed**, and the third is the finding — the brief predicts one:

- `test_h9a_fixture_r_a_draft_of_a_clean_tree_records_code_dirty_false` (this task's)
- `test_h9a_fixture_q_a_draft_on_a_clean_tree_records_code_dirty_false` (task 3's)
- `test_h9a_fixture_q_draft_pathspec_does_not_widen_to_the_repo_root` (task 3's — it asserts
  `code_dirty is False` for dirt at the repo root, so forcing the flag falsifies it too)

The two branches genuinely differ because Fixture R's premise is **verified** clean. **A
property-preserving arm**: `dataclasses.replace(prepared, git=prepared.git)` — a no-op replace leaves
the suite green, which is how you know the failure above came from the forced value and not from the
`replace` call. Reverted by editing back, `diff` byte-identical, re-run clean (2996).

Mechanical pass run over all six files after the edit: no duplicate anchors, no trailing whitespace,
no tabs, every table row matching its header's column count, every relative link and `#anchor`
resolving. Five anchor "misses" my checker reports in `reference.md` and four elsewhere are all
headings containing an em dash (GitHub's slugger leaves a double hyphen where mine collapses one);
none is in a line this batch touched, and all pre-date it.

`provenance.py` and § Operation commands' rows were not touched by task 6.

---

## Task 7 — `command_dry_run`

Built `cli.command_dry_run`, plus three helpers it prints from: `_handed_counts` (task 8's narrowing,
built here since the brief says "otherwise build both"), `_dry_run_step_dirs` and
`_dry_run_fixed_files`. `_prepare_run(config_path, allow_dirty=True)` (Decision 8); the arm-plan
resolution was not moved (Ruling S); nothing reaches `contrasts.resolve_contrasts` — the
`comparisons:` line reads `data.units.allocation`, a **declaration** (Decision 16).

**Every conditional answered by the structural fact, never by a name.** `environment/uv.lock` from
`prepared.lock_path is not None`; `allocation.json` from
`build_allocation_document(prepared.group_axes, prepared.holdout_plan) is not None` — the same call
`_execute_prepared` makes, so the predicate cannot drift from the writer; `apparatus/probes.jsonl`
from the identical `isinstance(declared_probe, str) and declared_probe` guard the run uses. Step
directories come from `runner.step_dir_for` against a placeholder root, relativized — the path scheme
is not re-derived — with `collapse = len(repeats) <= 1`, `execute_plan`'s own expression.

### The transcript

```
sweep: 2 conditions (grid) × 2 repeats = 4 executions
  00_method=pearson  analysis.method=pearson
  01_method=spearman  analysis.method=spearman
repeats: seed(n=2)
  seeds: [3997843047, 3186471940]  (auto, from design digest)
  comparisons: paired (allocation: within)
steps: step01_summarize_units (repeat)
statistics: basis units (n=10 resolved); correction holm; derived metric names come from the
  template's aggregate() and are not knowable before the run
scale:  40 unit-executions (4 executions × 10 units handed to each)
would create 4 step directories under <output_dir>/run_.../
  conditions/00_method=pearson/seed47/step01_summarize_units
  … (three more)
and 7 fixed files in that directory:
  config.yaml
  environment/pyproject.toml
  environment/repo_root.txt
  executions.jsonl
  manifest/input.json
  run.yaml
  sweep.yaml
the <output_dir>/latest pointer is repointed too; it sits beside the run directory rather than inside it
artifact files inside a step directory are NOT listed: their names are `io.write`
  arguments in step code, which core never inspects, so they are declared nowhere
  in the config and cannot be known before the run
creates nothing
```

**Ruling R's omission sentence is asserted, in Fixture U's own body and again end to end** — on
`"artifact files inside a step directory are NOT listed"` and `"core never inspects"`. Nothing else in
the transcript can produce either phrase: `io.write` appears nowhere else in the output, and the
surrounding lines name step directories and fixed files rather than artifact files. Without that
assertion Ruling R would be unpinned, since a build that silently printed less still exits `0`.

**Two corrections against the brief's own template.**

1. **There is no `<experiment>` path segment.** The brief writes
   `<output_dir>/<experiment>/run_.../`; `run_identity.allocate_run_dir` puts `run_<stamp>_<hash>`
   **directly** under `output_dir` (measured — a real run tree, path by path, below). The docs' examples
   read `/secure/results/cohort-pilot/` because the *config* names an experiment-specific
   `output_dir`, not because core adds a segment. The printed line uses
   `prepared.output_dir / "run_..."`.
2. **A run also repoints `<output_dir>/latest`**, outside the run directory. It is not in the brief's
   fixed-file list and is not in the parsed list here — it gets its own line, so the output is not
   silently incomplete about it. **That line is pinned**, in the task-9 end-to-end test, on
   `"/latest pointer is repointed too"`: it was the one sentence in output this batch added that
   nothing held, which is the same fault Ruling R's omission sentence exists to prevent. **Mutation —
   delete the line** (added AFTER the batch's other mutations, so it is reported separately): full
   suite **1 failed, 3009 passed**, exactly
   `test_h9a_dry_run_dispatches_end_to_end_and_prints_the_transcript`. Fixture U is unaffected because
   its fixed-file loop terminates on the first non-indented line either way — which is itself worth
   naming: the parser could not have caught this. **A property-preserving arm**: changing
   `prepared.output_dir / 'latest'` to `f"{prepared.output_dir}/latest"` — the same rendered text,
   green. Reverted by editing back; `diff` byte-identical; full suite re-run at 3010.

### The filesystem before/after comparison — *creates nothing*

Proved path by path, **not** by reading the code for absent `mkdir` calls, in two arms plus a lock arm.

- **`test_h9a_dry_run_creates_nothing_under_output_dir_on_a_never_run_project`** — a project built by
  `_h6a_t5_project` and **never run**. `sorted(p.relative_to(results) for p in results.rglob("*"))`
  is `[]` before; `command_dry_run` exits `0`; the identical listing is `[]` after, and
  `results.glob("run_*")` is empty. **Paired with a positive**: the output starts `sweep: ` and ends
  `creates nothing`, so a pass cannot be a command that did nothing.
- **`test_h9a_dry_run_leaves_an_existing_output_dir_byte_identical`** — the stronger arm, after a real
  `run`. A `{relative path → bytes (None for a directory)}` snapshot of the whole `output_dir` is
  compared **before and after**, asserted non-empty first so the comparison cannot be vacuous. Equal.
  A `dry-run` that appended a ledger line, wrote a file, or repointed `latest` fails here.
- **`test_h9a_dry_run_against_a_live_lock_completes_and_takes_none`** — Decision 12's second arm. A
  `lock` file written by hand into a completed run directory (`tests/test_freeze.py::_mid_run`'s own
  constructed shape) is byte-unchanged afterwards and the command exits `0`.

**Scoped to `output_dir`, and the scoping is Decision 12's, measured not predicted**: importing the
entrypoint runs `discover_local`, which writes `src/**/__pycache__/` and `templates/__pycache__/`
exactly as `validate` does. A repo-wide identity arm would fail and invite whoever met it to weaken
the assertion.

**Mutation — `(prepared.output_dir / "_mutation_probe").mkdir(exist_ok=True)` added before the print.**
Full suite: **2 failed, 3001 passed** —
`test_h9a_dry_run_creates_nothing_under_output_dir_on_a_never_run_project` and
`test_h9a_dry_run_leaves_an_existing_output_dir_byte_identical`. So *creates nothing* is a claim a
test can fail. **A property-preserving arm**: creating the same directory under `tmp_path` outside
`output_dir`, or touching a `__pycache__` entry — both leave the suite green, which is Decision 12's
scoping shown rather than argued. Reverted by editing back; `diff` byte-identical.

### Fixture U — both lists, set to set, residue enumerated

The real run tree was **listed before the expected sets were written** (a throwaway test that printed
`rglob("*")`), and it holds exactly: the seven fixed files, four step directories, one
`units.parquet` inside each step directory, and `latest` beside the run directory. Nothing else.

`_h9a_fixture_u` runs the SAME config through `dry-run` and compares:

- `step_dirs == leaf_dirs - {parent of each fixed file}` — a step directory is a **leaf** directory
  that is not the parent of a fixed file, which is what makes `environment/`, `manifest/` and
  `apparatus/` fall out **on their own** rather than being named as exceptions;
- `{files whose parent is a step dir} == {step_dir/units.parquet}` — the residue **enumerated**, per
  step directory, never filtered by pattern;
- `real_files - artifacts == fixed` — set to set, no literal and no count;
- both header counts checked against the lengths of the lists they introduce, so a build whose count
  and list disagree fails here rather than being read past.

**Three arms, one per conditional branch**, because naming a branch is not testing it:

| Arm | Branch exercised | Evidence |
|---|---|---|
| `..._the_two_lists_match_a_real_runs_tree` | the **negative** of all three: 7 fixed files | 4 step dirs, seven-file set |
| `..._the_conditional_fixed_files_uv_lock_and_allocation` | `lock_path is not None`, `build_allocation_document(...) is not None` | asserts `environment/uv.lock` and `allocation.json` exist in the real tree first |
| `..._the_conditional_fixed_file_apparatus_probes_jsonl` | a declared `apparatus_probe` | asserts `apparatus/probes.jsonl` exists in the real tree first |

Arm 2 is built on `_h6a_t5_project` (a real `uv.lock` at the project root, `sweep.groups` declared)
with `replication.repeats` edited to `n: 2` **after** the commit — `configs/**` is in neither hashed
tree, so this dirties nothing the gate reads. Arm 3 uses the `installed` + `registries` fixtures and a
project-local template, `tests/test_freeze.py::_fixture_p`'s shape.

**Mutation — `step_dir_for(root, execution, True)` unconditionally.** Full suite: **3 failed, 3000
passed**: all three Fixture U arms. **The brief asked why `n = 1` would make this blind, and I owe a
correction to my own prediction**: `collapse = len(repeats) <= 1`, so with one repeat a degenerate
level adds no directory component and `True`/`False` return the same tree — the mutation would be
blind. Arms 1 and 2 set `n: 2` deliberately for that reason. **I predicted arm 3 would be blind and it
was not**: `init` writes `INIT_REPEATS = 5`, so `run_a_project`'s default replication already has more
than one repeat. Predicting blindness and being wrong is the safe direction, but it was a prediction
about a default I had not read. **A property-preserving arm**: passing `collapse` through a variable
(`c = collapse; step_dir_for(root, execution, c)`) — green, because the two branches cannot differ.
Reverted by editing back; `diff` byte-identical.

### `E-CODE-EMPTY` inheritance — pinned

`test_h9a_dry_run_inherits_e_code_empty_from_phases_1_to_5` drives the same
`_h6a_t8_project(..., write_step=False)` tree guard-pin arm E drives through `run` — committed but
empty hashed trees — through `command_dry_run` instead. Asserts `EXIT_WRONG`, `"E-CODE-EMPTY"` in
**stdout** (the stream the refusal prints to), and `not list(results.glob("*"))`, which is what
separates *refused* from *refused after creating*. Correction 19 is why this is correct rather than a
defect: the print and the exit both sit **inside** phases 1–5, so a config whose hashed trees hold no
file is refused before any metered call — the cost ordering doing its job. An inherited refusal nobody
tests is how a mode silently diverges from the command it re-enters; it is now tested. (The
`main(["dry-run", …])` form of the same path lands in task 9's end-to-end test.)

`runner.py`, `apparatus.py`, `NOT_BUILT_COMMANDS`/`OPERATION_COMMANDS` and every `*.md` were untouched
by task 7.

---

## Task 8 — the agreement pin

**`execute_plan`'s own narrowing, read at `src/publishable/runner.py` lines ~683–735 and restated** in
`cli._handed_counts`' docstring: arm narrowing first (`_arm_keys`, when a group axis is declared **and**
the execution has a condition index); then under a declared **fold**, `run`/`condition` receive `None`,
`repeat` receives `_handed_keys`' partition of the arm-narrowed roster, `summary` receives the whole
arm-narrowed roster; under a declared **holdout** every scope receives the test partition — which is
`prepared.eval_roster` already, since `execute_plan` only attaches `.train`, changing no length;
otherwise the arm-narrowed roster. **An execution handed `None` contributes zero, and the printed line
says so.** `runner._arm_keys` and `runner._handed_keys` are **called**, not re-implemented (they were
already single-call-site extracted). `runner.py` was not touched at all; `execute_plan`'s narrowing was
not found wrong.

**Ground truth is OBSERVED, never derived.** Both fixtures' step appends `len(io.units)` — or `0` when
`io.units` raises `E-STEP-UNITS-UNAVAILABLE` — to a file **outside `output_dir`**, so the evidence is
not an artifact of the run being measured. The expected value is the **sum of those lines**, never
`roster / k × executions`, which is arithmetic the code under test could be wrong about the same way.

| Fixture | Design | Handed, observed | Total |
|---|---|---|---|
| **S** | `fold` `k: 5` over 10 units, plus a `run`-scoped step | `[0, 2, 2, 2, 2, 2]` | **10** |
| **T** | group axis `by: arm`, 40 units → two arms of 20, 2 conditions × 2 seed repeats | `[20, 20, 20, 20]` | **80** |

**S ≠ T (10 vs 80)**, so the pair distinguishes two readings rather than one wearing two names. Each
fixture asserts its own `handed` list *before* the equality, so its premise is measured: S really has
one execution handed nothing and five handed a **proper** subset; T's arms really are proper subsets of
the roster. T's roster is 40 rather than 20 because `init` writes `min_units_per_cell: 20`.
S also asserts the **printed** None-contributes-zero line (`"1 of those executions are handed no unit
list at all"`), and T asserts its **absence** — paired with an equality that must report.

**Mutations, both against the full suite, both checked for differing branches first:**

| Mutation | Read from the full run | Failing test |
|---|---|---|
| (a) drop the `_arm_keys` block from `_handed_counts` | **1 failed, 3004 passed** | `test_h9a_fixture_t_...` (80 → 160) |
| (b) `handed = None` → `handed = scoped` at `run`/`condition` scope under a fold | **1 failed, 3004 passed** | `test_h9a_fixture_s_...` (10 → 20) |

Branches checked before believing either: (a) T's arms are 20 of 40, so narrowing and not-narrowing
differ; (b) S's fold is `k: 5` with a `run`-scoped step, so `None` and the whole roster differ.
**A property-preserving arm for each**: (a) narrowing with `_arm_keys(...)` but against the *same*
condition index for every execution would still differ — the genuinely blind arm is replacing
`{u.key for u in roster}` with `set(u.key for u in roster)`, a spelling change; (b) reordering the
`elif execution.scope == "repeat"` branch above the `run`/`condition` one, which is disjoint and so
cannot change any answer. Both green, both confirming the mutations above measured the branch.

**Disclosure**: the printed-line assertions in S and T were added **after** mutation (b) ran, so
mutation (b)'s recorded failure is attributable to the total, not to the printed line. It strengthens
the fixture rather than replacing what the mutation proved; the final full-suite run (3005) covers
both. Reverts: (a) restored from a pristine copy and verified byte-identical by `diff`; (b) edited
back and verified byte-identical.

One test written and then **deleted before commit**: an assertion that `10 != 80`. It measured only
that two literals differ — the *test that iterates the thing under test* shape — and the two fixtures'
own literal sums already make coincidence impossible. Replaced by a comment naming the pair.

---

## Task 9 — `dry-run` dispatches

Three code edits: `OPERATION_COMMANDS` gains `"dry-run"`, `handlers["dry-run"] = command_dry_run`
joins the **existing** shared one-path arity arm (not a second enforcer), and `NOT_BUILT_COMMANDS`
loses `"dry-run"`. **`_dispatch`'s branch order was not touched** (correction 16) — the diff of that
function is one added `handlers` line.

### Arm F — the post-edit state against what was specified

`tests/test_cli.py::test_reference_cli_tables_are_parsed_at_all`, the whole diff, nothing reordered:

```
-    assert ("dry-run", "NOT BUILT") in tables["Command"]
+    assert ("dry-run", "built") in tables["Command"]
+    assert ("resume", "NOT BUILT") in tables["Command"]
     assert ("validate", "built") in tables["Command"]
```

Exactly the two lines the design specified: the `dry-run` pair flips to `built`, and a marked
row-presence probe is added so the Command table keeps the device its own docstring says rules out a
parser finding some rows but not the ones a reader would look for. `("validate", "built")` untouched;
the two `set(NOT_BUILT_COMMANDS)`/`set(NOT_BUILT_GENERATORS)` equalities untouched — they are
self-maintaining, and they are also why the `Status` cell and `NOT_BUILT_COMMANDS` had to move in
**one commit**.

### What § Operation commands now says, with the omission named

> | `publishable dry-run` | **built** | config path | Validates, expands the sweep and repeat plan,
> builds the input manifest, [probes the apparatus], prints the step directories and the fixed files a
> run would write, and the unit-execution count. **Does not** list the artifact files inside those
> directories: their names are `io.write` arguments in step code, which core never inspects — see
> [design-principles.md § Greenfield only]. Creates nothing |

Both links resolve (`#the-apparatus-core-can-only-observe`, `design-principles.md#greenfield-only`).

**The sweep Ruling R needed, and it found two unowned homes.** `grep -n "artifact path\|every
artifact\|artifact paths\|artifacts under"` over the six files named individually — every hit
attributed:

| Hit | Attribution | Action |
|---|---|---|
| `reference.md:3673` | § Operation commands' row | **mine — edited** |
| `reference.md:368` | § Validation prose: *"resolves the run directory, and prints every artifact path that would be written"* | **UNOWNED by any task section.** Edited: the promise narrowed the same way, and the phrase *"resolves the run directory"* dropped — this build resolves no run id (the timestamp and hash prefix exist only once the directory is claimed) and prints `run_.../` |
| `reference.md:3756` | § What `demo` walks you through, stop 4: *"every artifact path that would be written"* | **UNOWNED.** Edited to the narrowed wording |
| `reference.md:3882` | *"which artifact paths `dry-run` prints"* | **UNOWNED.** Edited to *"which step directories"* |
| `reference.md:3094` | § Before you spend's transcript, `would write 64 artifacts` | **task 12's** — left |
| `reference.md:618`, `:621`, `:1950` | *"identical at every artifact"*, about two condition directories under a duplicated level | unrelated — left |
| `feasibility-llm-growth-studies.md:1471` | *"where every artifact will land"* + *"`dry-run` prints specified but not built"* | plan correction 9 names it; a later task owns that file, and the dispatch bars me from it — **left**, flagged in Concerns |
| `README.md`, `design-principles.md`, `experimental-designs.md`, `CLAUDE.md` | 0 hits | — |

The three unowned edits are disclosed as a scope question in Concerns. My reasoning for making them
rather than filing them: with the row narrowed and those three sentences left standing,
`reference.md` would **contradict itself** about the one thing Ruling R exists to settle, and the
cross-document pass is part of finishing a `*.md` edit rather than a later task's option.

### The end-to-end tests

`test_h9a_dry_run_dispatches_end_to_end_and_prints_the_transcript` — `main(["dry-run", cfg])` over a
real project: exit `0`, and **every** section asserted, because a build that dropped one line still
exits `0`. Asserted on **stdout** specifically, with `"creates nothing" not in err`.

The arity trio, task 4's shape for the second name to join that arm:
`test_h9a_dry_run_with_no_path_is_an_invocation_error`, `..._with_two_paths_...`,
`..._with_a_flag_...` (`--json`, the arm the `len` half cannot cover). Plus
`test_h9a_dry_run_new_now_reaches_the_arity_arm_not_the_not_built_diagnostic`, which pins the one
shipped answer this task moves: `publishable dry-run new` printed the specified-but-unbuilt diagnostic
before and now routes into `command_dry_run`.

**Mutation** — the shared arm's condition replaced with a bare `len(rest) != 1`. Full suite: **2
failed, 3008 passed** — `test_h9a_draft_with_a_flag_is_an_invocation_error` (task 4's) and
`test_h9a_dry_run_with_a_flag_is_an_invocation_error` (this task's). Both names are now on that arm
and both are pinned. **A property-preserving arm**: `len(rest) != 1 or rest[0][:1] == "-"` — a
different spelling of the same predicate, green. Reverted by editing the line back (the first attempt
at a whole-string replace **failed its own assertion**, because `if len(rest) != 1:` is not unique in
`cli.py`; the revert was then done by line index and verified byte-identical by `diff`, and the full
suite re-run at 3010).

**Confirmed by running, not by reading**: the shipped
`test_reference_cli_tables_match_what_the_cli_does[Command]` now drives
`main(["dry-run", "_probe_a", "_probe_b"])` and passes — two positionals hit the arity arm, so nothing
executes. Per the brief this is a **constraint satisfied, not a pin** (H8b's Minor: a CLI arm
demonstrated by one prose invocation and nothing else); the arity mutation above is the pin.

§ Before you spend's transcript, § The apparatus files, § Draft runs, every other `Status` cell and
`provenance.py` were not touched by task 9.

---

## Concerns

1. **Three `reference.md` sentences were edited that no task section owns** — `:368` (§ Validation),
   `:3756` (§ `demo`'s stop 4) and `:3882` (entrypoint resolution). Each carried the exact promise
   Ruling R narrows, and leaving them would have made the document contradict its own `dry-run` row.
   Named here so the controller can rule; if task 12 was meant to have them, this is a collision to
   resolve, not a silent overlap. The diffs, so the ruling does not need reconstructing:

   - **`:368`**, old → *"it validates, builds the input manifest, probes the apparatus, **resolves the
     run directory**, and prints **every artifact path that would be written** — without executing a
     step or creating anything."* New → *"it validates, builds the input manifest, probes the
     apparatus, and prints **the step directories and the fixed files a run would write** — without
     executing a step or creating anything. The artifact *files* inside those directories it cannot
     list, and says so: their names are `io.write` arguments in step code, which core never
     inspects."*
   - **`:3882`**, old → *"how many executions each step gets, **which artifact paths** `dry-run`
     prints, and which scope each `io` will be built for."* New → *"…**which step directories**
     `dry-run` prints…"*
   - **`:3756`** (§ `demo` stop 4), old → *"15 executions, and every artifact path that would be
     written. Still creates nothing"*. New → *"15 executions, the step directories and fixed files a
     run would write, and the unit-execution count. Still creates nothing"*.

   **A disclosed asymmetry inside this concern:** `:368` is the one place a *clause* was **deleted**
   rather than narrowed — *"resolves the run directory"*, which this build does not do (a run id needs
   the directory claimed). The same word is **kept** at `:872` (§ One execution at a time), for the
   reason in Concern 3. Two treatments of one word in one file, deliberate and stated here rather than
   left to be found.
2. **The row's `probes the apparatus` clause is not true of this branch yet.** Task 10 owns the probe
   round, and the `Status` column is per **command**, not per clause — but at task 9's commit the
   `Does` cell (mandated content, per Ruling R) makes a build claim `dry-run` does not yet honour.
   It closes when task 10 lands on this branch. Naming it rather than editing mandated content.
3. **`reference.md:872` says `dry-run` "resolves the run directory to print paths"** and is left
   untouched (§ One execution at a time; nothing in my scope). This build cannot resolve a run *id* —
   the timestamp and hash prefix come into existence when `allocate_run_dir` claims the directory — so
   it prints `<output_dir>/run_.../`. The sentence's load-bearing half ("takes no lock", "creates
   nothing") is true and pinned; the word *resolves* is looser than the code. Filed here, not fixed.
4. **The brief's path template has an `<experiment>` segment core does not add** (task 7, correction 1
   above). Worth carrying into H9b/H9c briefs, which will re-use that shape.
5. **`_arm_keys` was already imported into `cli.py` before this batch** and now has a second caller.
   Mutation (a) removed only `_handed_counts`' use and `ruff` stayed quiet, so the import is not a
   proxy for whether the narrowing runs — the agreement pin is.
6. `.superpowers/sdd/.gitignore` was checked before each commit and was **not** clobbered during this
   batch.

---

## Fix round — 2026-08-23 (batches 3–5 review, `task-b4-review.md` @ `574eba7`)

All four Majors and all five Minors closed this round. Suite **3012 passed, 1 skipped, 2 xfailed**
(+2 over the review's 3010 = the two new test functions below; no other count moved). Gates clean:
`ruff check .` (all passed), `ruff format .` (93 files unchanged — no `*.md` touched by it, confirming
the house rule), `mypy` (52 source files, no issues).

### Major 1 — `dry-run`'s sweep header double-counted `baseline` — CLOSED

`src/publishable/cli.py::command_dry_run`: `modes` no longer re-adds `"baseline"` from the `sweep`
dict once the `is_baseline` seed has already added it (`k != "baseline"` added to the list
comprehension's filter). New test
`test_h9a_dry_run_sweep_header_does_not_double_count_baseline` uses a config declaring **both**
`baseline` and `grid` — the fixture the review named as the one that separates the two readings.
**Read before fixing**: the test failed against the unfixed code with
`sweep: 3 conditions (baseline + baseline + grid) × 2 repeats = 6 executions`, confirming the bug
live. **Mutation** (revert to the pre-fix line): full run of the two relevant tests gives
`1 failed, 1 passed` — the new test fails, the pre-existing grid-only end-to-end test
(`test_h9a_dry_run_dispatches_end_to_end_and_prints_the_transcript`) stays green, which is exactly
the review's *fixture whose numbers agree with the bug* diagnosis reproduced and now closed by a
fixture that cannot agree with it.

### Major 2 — task 12's mandated sweep would find zero homes — CLOSED

`docs/superpowers/plans/2026-08-23-re-entry-seam.md` § Task 12: the old sweep paragraph (`64
artifacts`, `would write`, `every artifact path`) is struck (shown, not deleted) and replaced by an
amended paragraph swept for `step directories` and `would write` — the phrasing task 9 actually
landed. Re-measured 2026-08-23 against `HEAD`, each file named individually: `step directories` → 4
homes (`reference.md:368,3673,3756,3882`); `would write` → 3 homes (`reference.md:3094,3673,3756`);
`64 artifacts` → 1 home (`:3094`); zero hits in `README.md`, `design-principles.md`,
`experimental-designs.md`, `CLAUDE.md`. `feasibility-llm-growth-studies.md`'s home stays task 14's per
plan correction 9. The amendment says what it replaces and why, per `CLAUDE.md`'s append-not-retro-edit
rule for the development record.

### Major 3 — `reference.md:872` still claimed `dry-run` "resolves the run directory" — CLOSED

Narrowed to *"it prints paths and creates nothing"*, with a parenthetical stating the load-bearing
fact plainly: `dry-run` resolves no run *id* either, since the timestamp/hash-prefix name is claimed
only by `allocate_run_dir`, so the paths it prints hold the literal `run_.../` placeholder. Linked to
`#run-identity`, which already documents that naming scheme. `"takes no lock"` and `"creates
nothing"` — the parts the review confirmed true and pinned — are untouched.

### Major 4 — "the shared arity arm is pinned by nothing" was false — CLOSED

Both the plan (`§ Corrections against the code`, new item 20) and the design (Decision 13, and § 3
item 9, new item 14) carry appended corrections — not retro-edits — stating the narrower truth: a
full-suite mutation dropping only the **count** half of the shared condition fails two tests
predating this slice (`test_a_missing_argument_is_an_invocation_error`,
`test_operation_commands_take_no_flags`, both `dc21d55`), so the count half was already pinned; only
the **flag** half was genuinely unpinned, which is what task 4's own mutation demonstrates. The
report's own claim from batch 4 stands corrected by this addendum rather than edited away.

### Minor 1 — `test_operation_commands_take_no_flags`'s name outran its assertion — CLOSED

Its two-argument call (`["run", "cfg.yaml", "--allow-dirty"]`) short-circuits on the count check
before the flag half its name claims is ever reached. Added a second assertion,
`main(["run", "--allow-dirty"])` (one argument, flag-shaped) — this isolates the flag half, since
`len(rest) == 1` there and only `rest[0].startswith("-")` can produce `EXIT_INVOCATION`. **Mutation**:
dropping the flag check (`if len(rest) != 1 or rest[0].startswith("-"):` → `if len(rest) != 1:`) fails
the new assertion (`assert 1 == 2`) while the pre-existing assertion stays green — read from a
scoped run of this one test, confirming the new line is what does the work now. Reverted, verified
byte-identical by `diff`.

### Minor 2 — task 5's "every hit attributed" over-claimed — left as the review found it

Not separately re-edited this round: the review's own finding already states the correction (two
pre-existing negative-side assertions at `tests/test_diff.py:531,738` were not named in the table, and
neither changes a conclusion). No further action needed beyond what the review recorded — CLOSED by
the review's own text, restated here so it is not read as still open.

### Minor 3 — the holdout leg of `_handed_counts` was unfixtured — CLOSED, by building the fixture

`test_h9a_fixture_v_unit_executions_agrees_with_a_real_holdout_run`: 20 units, `holdout.frac: 0.2` at
the already-pinned seed `4321` (4-unit test partition, matching
`test_a_declared_holdout_now_validates_and_runs`'s own count), two seed repeats, a repeat-scoped
counting step. Ground truth observed from the real run (`[4, 4]`, sum 8), asserted against
`dry-run`'s printed total. **Mutation**: `roster = prepared.eval_roster` → `roster = prepared.roster`
(the full, pre-holdout roster) at the top of `_handed_counts` — full run of Fixtures S, T and V
together: **1 failed** (V: `assert 40 == 8`), S and T unaffected, confirming the mutation is
attributed to the holdout leg alone and that S/T's existing coverage does not already catch it.
Reverted, verified byte-identical by `diff`.

### Minor 4 — the *creates-nothing* arms called `command_dry_run` directly — CLOSED

Appended a `main(["dry-run", str(cfg)])` arm to
`test_h9a_dry_run_leaves_an_existing_output_dir_byte_identical`, re-running the same whole-tree
byte-identity snapshot through the dispatched command. Passes; the direct-call arm above it is
untouched (not replaced, since it also serves as the more surgical failure locator).

### Minor 5 — the `probes the apparatus` clause is false until task 10 lands — left OPEN, by explicit ruling

**Not fixed this round, on purpose.** Read `command_dry_run`'s body: no call to `apparatus.observe_once`
or any probe dispatch exists yet — `_dry_run_fixed_files` only checks *whether* a probe is declared
to decide if `apparatus/probes.jsonl` belongs in the fixed-file list, it does not run one. So the
row's clause is false of the code today, exactly as the review found.

The plan (`docs/superpowers/plans/2026-08-23-re-entry-seam.md` § Task 9) mandates this exact wording
as content, not merely as a suggestion (*"wording yours, that content mandatory"*), on the ground
that task 10 — the very next task in this same slice, landing on this same unmerged branch — is what
makes it true. Narrowing the row now would mean re-widening it again within the same slice, which is
the kind of churn `CLAUDE.md`'s development-record conventions exist to avoid, and this fix round's
charter is batches 3–5 (tasks 3–9), not task 10. **Ruling: the clause stays, and the whole-branch gate
(not this fix round) is the owner of re-checking it once task 10 either lands or is dropped** — matching
the review's own adjudication at check 5, now recorded as a decision rather than left as an open
question. If task 10 does not land before merge, this becomes a Major at the gate, not a Minor.

### Commits

Each Major/Minor above except 2 and 5 (documentation-only or explicitly-not-fixed) touches
`src/publishable/cli.py` and/or `tests/test_cli.py`; Majors 2–4 touch only the plan/design/reference
documents. See the commit log for this fix round for the exact split.
