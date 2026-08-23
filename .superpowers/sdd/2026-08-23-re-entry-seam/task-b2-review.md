# Batch B2 review — H9a task 1 (the guard pin) and task 2 (the extraction)

**Reviewed 2026-08-23 on branch `h9a-re-entry-seam` at `ec43c95`.** Commits in scope: `190de68`
(task 1), `cd91adc` (task 2), `ec43c95` (the controller's pin retarget).

## Verdicts

| Commit | Verdict |
|---|---|
| `190de68` — task 1, the ten-test guard pin | **PASS** (2 Minor) |
| `cd91adc` — task 2, the extraction | **PASS** (1 Major, 1 Minor) |
| `ec43c95` — the controller's retarget | **PASS** — both claimed properties re-proven, plus a third |

**The extraction IS behaviour-preserving by my own independent measurement** (§ 2 below).

Gates, run by me: `uv run ruff check .` **All checks passed**; `uv run ruff format --check .`
**93 files already formatted**; `uv run mypy` **Success, 52 source files**; `uv run pytest`
**2984 passed, 1 skipped, 2 xfailed** in 209s — twice, once before any mutation and once after every
revert. `main` is 2973 passed; **+11 = task 1's ten arms + task 2's one credential fixture.**
Reconciled.

---

## 1. What I verified by BEHAVIOUR versus by READING

**By behaviour** (a command or a test actually run): both block-move diffs; the whole-statement cut;
the two-worktree comparison through two real console scripts; the parquet byte comparison; all ten
arms' liveness under ten production mutations; task 2's mutations a1, a2, b, c; the retargeted pin
under two different mutations; the credential redaction at `validate` and at `run` through the
installed console script, on the correct stream, on **both** trees; the `Condition`-quoting
runtime-only failure; every revert (re-run, not `git status`).

**By reading** (with a mechanical cross-check where one existed): the absence of a second executable
reader of `command_run`; the field-set completeness argument; the lifetime question the two static
gates cannot see; the ownership of correction 22; that the pin's enumeration widening is covered by
an independent behavioural pin.

---

## 2. Behaviour preservation — re-measured, and independently

### The two block-move diffs, against the committed pre-task file

`git show HEAD~2:src/publishable/cli.py` (**not** a scratch copy) → identical to the file the report
diffed against.

```
diff <(sed -n '2430,3924p' pre) <(sed -n '2625,4119p' src/publishable/cli.py)
→ (no output)                       # IDENTICAL, 1495 lines

diff <(sed -n '2010,2428p' pre) <(sed -n '2110,2528p' src/publishable/cli.py)
19c19
<     if git.code_dirty:
---
>     if git.code_dirty and not allow_dirty:      # ONE line in 419
```

`git diff HEAD~2 HEAD -- src/publishable/cli.py` has **five hunks and no sixth**: the two import
statements, the `Prepared`/`_prepare_run` header, the `return Prepared(...)`, the
`_execute_prepared` header plus its 35-line unpack, and the new `command_run`. Every added line is
scaffolding; nothing else in a 4470-line file moved.

**The cut is a whole-statement block move, not a re-indented fragment** — re-run on the pre-task
file: the only compound statement spanning line 2430 is `command_run` itself; the last top-level
statement before it ends at 2428 and the next begins at 2430.

### My own two-worktree comparison — two REAL console scripts

Stronger than the report's, in three ways: it uses the **installed console script** rather than an
in-process `main()`; it needs **no absolute-path or `hostname` normalization** because both runs use
the same project directory on the same machine, so those are compared *as values*; and it compares
every file by **sha256**, including the parquet the report exempted.

- Baseline verified: `git show d61df9d:src/publishable/cli.py` is byte-identical to the pre-task
  file, and `git diff main d61df9d -- src/` is empty.
- Two `uv venv`s, `uv pip install -e` on each tree. Positive control, printed:
  `OLD -> …/scratchpad/h9rev-old/src/publishable/__init__.py`,
  `NEW -> /Users/joon/src/tries/publishable/src/publishable/__init__.py`. **Two different trees.**
- Project scaffolded and committed **once** (`publishable new` → `generate experiment` →
  `generate template`), a project-local template with a real `aggregate` returning `mean_pred`, a
  `grid` sweep over two levels, two `seed` repeats, a 20-unit CSV roster, a seeded `self.rng` draw
  per unit. Outside this repository. Tree clean before each run.
- Normalization list, fixed before running from design § 5 and **not extended**: keys named `at`,
  `started_at`, `wall_seconds`, `run_id`, plus the run-directory name in paths/stdout.

| Surface | Compared as | Result |
|---|---|---|
| exit code | value | `0` vs `0` — EQUAL |
| `run.yaml` | leaf by leaf, dotted path + value, **in order** | **EQUAL, 147 leaves, 0 differing, order equal** |
| the run tree | path → (kind, size, **sha256**) | **26 paths**, all equal except `run.yaml` and `executions.jsonl` (same size, attributed below) |
| `units.parquet` ×4 | **`cmp`, byte for byte** | **IDENTICAL — all four** |
| stdout | line by line | **EQUAL, 4 lines** |
| stderr | full text | EQUAL (empty) |
| `sweep.yaml` | full text | **EQUAL, 30 lines** |
| `executions.jsonl` | leaf by leaf | **EQUAL**; raw text differs on `started_at` ×4 and `wall_seconds` ×1, nothing else |
| `run.yaml` raw text | `diff` after normalizing the run-dir name | **5 lines**: 4× `started_at`, 1× `wall_seconds` |

**Unattributed differences: ZERO.** `git.commit`, `code_hash` (`33aff53` both sides),
`parameters_hash`, `input_manifest_hash`, `units_hash` and `hostname` were compared **as values**
and are equal. My figures independently reproduce the report's (147 / 26 / 4 / 30).

**The normalization list predates the work and is not tailored.** It is design § 5's list verbatim
plus one narrowing (`git.commit` compared as a value — strictly stronger) and one weakening (parquet
by `(path,size)`). **The weakening bought nothing**: I compared those four files byte for byte and
they are identical. Nothing on the list was chosen after seeing a diff.

### Ruling S — the arm-plan resolution did NOT move

`_resolved_group_axes` 2314 → 2414 and `arm_members` 2332 → 2432: **both +100, the constant offset
of the whole phases-1–5 block** (2010 → 2110). They sit inside the 419-line block whose entire diff
is the dirty-gate line, so relative position and mutual order are preserved *mechanically*. No part
of that resolution crossed the seam.

### Ruling T — the gate relaxed, the pathspec did not widen

`git diff main HEAD --stat` names five files: `cli.py`, `test_apparatus.py`, `test_cli.py` and two
reports. **`provenance.py` is untouched** (`git diff … -- src/publishable/provenance.py | wc -l` →
0), so `git_provenance`, its `-c` flags and `HASHED_TREES` are byte-unchanged. The one changed line
is `git.code_dirty` → `git.code_dirty and not allow_dirty` and `command_run` passes
`allow_dirty=False`, so `not False` is `True` and the conjunction is the original predicate. A
relaxation reachable only by a caller that asks for it, and there is none yet. Behaviourally
confirmed: `test_h9a_arm_e_a_dirty_tree`, `test_run_refuses_a_dirty_code_tree` and
`test_run_refuses_an_untracked_file_a_global_exclude_hides` are all green, and all three fail when
the conjunction is neutered at **either** end (§ 4).

### The blind spot neither static gate can see — object LIFETIME — checked and closed

`F821` (nothing missing) and `F841` (nothing carried-unread) are **name** arguments. Neither says
anything about a value that was alive across the old seam because a phases-1–5 local held it and is
now freed when `_prepare_run` returns. Measured rather than assumed:

- The 19 locals of `_prepare_run` **not** carried in `Prepared` are
  `_columns, allow_dirty, dirty_c, empty_c, experiment, fold_level, hashed, labels, lv, r,
  resolver_io, roster_c, roster_code, strata, sweep_block, swept_paths, technical_n, u, warn_c`.
- **None of them shadows a module-level global in `cli.py`** — checked by AST. That is what makes
  the `F821`-clean argument complete: had one been both uncarried and a module global, a post-seam
  read would have silently resolved to the global and no gate would have fired.
- Only `r`, `u`, `warn_c` are loaded in `_execute_prepared`, and each is **stored there first**
  (`warn_c` at 4100 before its reads at 4101–4104; `r`/`u` are comprehension targets). Confirms the
  report's `warn_c` correction 17 handling.
- `experiment` was the prime lifetime suspect: it is dropped at the seam. `load_experiment` releases
  its `sys.path` entry **by identity in a `finally` inside the call**, `sys.modules` is purged at the
  *start* of a load and not at drop, and there is **no `__del__` and no `weakref` anywhere in
  `src/`**. Nothing in phases 6–10 reads it. **Closed — no lifetime dependency.**

### The field set

36 fields = `config_path` + the brief's 35 **in exactly the brief's order** (asserted by AST). The
`Prepared(...)` constructor's kwarg order equals the field order; the unpack block is exactly the 36
minus `c`. `_prepare_run` returns `Prepared` once, `EXIT_WRONG` four times, and
`unignored_under_hashed_trees(...)` from the nested `_include` — so **"phases 1–5 never return
`EXIT_OK`" holds**, checked by enumeration and not inherited.

---

## 3. Task 1 — all ten arms are green AND all ten can fail

Each mutation run in **production** code, reverted by editing back, `__pycache__` cleared, revert
verified by re-running (never by `git status`, never `git checkout`).

| Arm | Mutation | Result |
|---|---|---|
| A `..._run_yaml_leaf_by_leaf` | `run_record.py`: `cond["is_baseline"] = not meta.get(...)` | 1 failed — arm A |
| B `..._stdout_line_by_line` | `cli.py`: `run.yaml → …` → `wrote run.yaml at …` | 1 failed — arm B |
| C1 `..._completed_status_and_exit` | `{"completed": EXIT_PARTIAL, …}` | fails — arm C1 (blast radius: § 5, Minor 1) |
| C2 `..._failed_status_and_exit` | `.get(status, EXIT_PARTIAL)` | 1 failed — arm C2 |
| C3 `..._partial_status_and_exit` | drop the `"partial"` entry | 1 failed — arm C3 |
| D `..._executions_jsonl_line_key_set` | `runner.py`: add `"extra_field_h9a_mutation"` to the ledger line | 1 failed — arm D |
| E-a `..._config_that_fails_validation` | `validate.py:1101` `c.error("E-PARAM-VALUE", …)` → `pass` | 1 failed — arm E-a |
| E-b `..._a_dirty_tree` | `if False and git.code_dirty and not allow_dirty:` | 1 failed — arm E-b (+2 shipped, § 4) |
| E-c `..._a_roster_refusal` | `roster_code = "E-RESOLVER-RAISED"` hardcoded | 2 failed — arm E-c + the new credential fixture |
| E-d `..._the_zero_file_e_code_empty` | `if not hashed:` → `if False:` | 1 failed — arm E-d |

**Arms A–E never moved.** `git diff 190de68 HEAD -- tests/test_cli.py` has **zero deletion lines**,
and `git log -p 190de68..HEAD -- tests/test_cli.py | grep h9a_arm` is empty. No arm was edited, by
task 2 or by the controller. Ruling U held.

**Arm C's fourth sub-claim (apparatus-unreachable → 5), taken by citation: accepted.** I read the
cited test — `test_g_fixture_u_unreachable_mid_plan` carries `expect_exit=EXIT_EXTERNAL` and
`assert run["status"] == "partial"` as **separate statements**, so the citation holds the claim the
arm was asked for and rebuilding it would be the same list pinned twice.

**Arms F and G: cited, nothing re-captured, nothing edited.** Verified against the plan — task 9 is
arm F's sole authorized editor and its post-edit state is written in both the plan and the arm.

---

## 4. Task 2 — every mutation re-run, against the body of the test it names

| # | Mutation | My count | Which |
|---|---|---|---|
| a1 | body: `if False and git.code_dirty and not allow_dirty:` | **3** | `test_h9a_arm_e_a_dirty_tree`, `test_run_refuses_a_dirty_code_tree`, `test_run_refuses_an_untracked_file_a_global_exclude_hides` |
| a2 | call site: `allow_dirty=False` → `True` | **3** | the same three |
| b | move `credentials = credential_values(...)` below the roster `try/except` | **7** + `ruff` F821 | `…_redacted_rather_than_printed_whole` ×4, `test_h9a_arm_e_a_roster_refusal`, `test_command_run_threads_the_real_wide_cfg_to_its_own_resolver_call_too`, `test_h9a_b2_…_survives_the_roster_raise` |
| c | delete `roster_c.credentials = credentials` | **5**, `ruff` and `mypy` **clean** | the four parametrizations + `test_h9a_b2_…`, the last on its `<redacted:PUBLISHABLE_TEST_AZURE>` assertion with the sentinel present in the message |

**All four match the report exactly, test for test.** Two conclusions of the report are therefore
confirmed rather than taken on trust:

- **The design's "blind mutation" prediction for b is falsified.** `ruff` reports
  `F821 Undefined name 'credentials'` and the runtime is `UnboundLocalError`. The ordering is pinned,
  loudly, and by a static gate.
- **Mutation c is the arm that matters**, because b crashes before reaching the redaction and so says
  nothing about whether anything asserts it. c is `ruff`- and `mypy`-clean, raises nothing, and
  simply publishes the credential — and the new fixture is what catches it. The replacement fixture
  is **not vacuous**, and I confirmed its failure is on the redaction assertion specifically, not
  merely a count.

**a1 and a2 are the same property at the body and at the call site** — the *mutation applied to a
proxy* trap, avoided by running both.

### The credential wrapper crossed the seam — probed end to end, on BOTH trees

*Copying a recipe's calls without its containment* is the fault this had to be checked for. The
419-line byte-identical diff already proves the `try` moved with the calls; I built the case anyway.

A real plugin (`leakplug`, entry point `publishable.resolvers` → `leaky`) installed into **both**
venvs; a project-local template declaring
`Param("cohort_assay.provider", choices=["azure_openai"], requires_env={"azure_openai": ["PUBLISHABLE_REV_AZURE"]})`;
a `.env` setting that variable to `sk-rev-sentinel-DEADBEEF`; the resolver raising a `ContractError`
carrying it.

- **`validate`**: `error E-UNITS-SOURCE-MISSING data.units / resolver could not reach the store:
  token=<redacted:PUBLISHABLE_REV_AZURE>`, exit 1, sentinel absent from stdout+stderr.
- **`run`, at the run-side roster `try/except` specifically** — a call-counting resolver that
  succeeds on `validate`'s dispatch and raises on the run-side call, so the diagnostic comes from
  the `except` block and not from the validate gate: redacted, **on stderr**, exit 1, sentinel
  absent, resolver called twice.
- **Both, byte-identical between the pre-extraction and post-extraction console scripts** (`cmp` on
  stdout and stderr for each of the four invocations).

§ Secrets' promise holds at both surfaces after the move, verified through the installed console
script rather than by reading.

### The retargeted pin (`ec43c95`) — three properties, not two

1. **The controller's mutation.** `phase=apparatus.PHASE_RUN_START` → `phase="run_start"` at
   `cli.py:2760`: the test fails. Checked **both** assertions rather than only the first pytest
   reports — `positive assertion holds: False`, `negative assertion holds: False`. The negative arm
   is now **non-vacuous**, which is exactly what the retarget was for.
2. **The other property the review asked for — an OFF-LIST move.** I extracted the call into a new
   module-level `_offlist_run_start(observer)` and called that from `_execute_prepared`. The pin
   **fails**, and it is the **only** test in `tests/test_apparatus.py` to fail (1 failed, 65 passed).
   The retarget bought exactly what was claimed.
3. **The widening it also introduced costs nothing.** The enumeration admits all three bodies, so a
   move *between* them passes silently — but the round's position is held independently by
   `test_the_run_start_fire_leaves_no_run_yaml_no_executions_and_no_lock`, which asserts exactly one
   run directory exists when the first `append_observation` fires. A move ahead of
   `allocate_run_dir` (i.e. into `_prepare_run`) makes that zero and fails it. Verified by reading
   the fixture; the pin is green.

The commit's own scope is the source read plus its docstring and nothing else — the four asserted
literals and the `runner_source` arm are untouched.

### The runtime-only failure both static gates passed — reproduced

Unquoting `conditions: "list[Condition]"`:

```
uv run ruff check .   → All checks passed!
uv run mypy           → Success: no issues found in 52 source files
uv run python -c "import publishable.cli"
                      → NameError: name 'Condition' is not defined
```

Confirmed. `Condition` is `TYPE_CHECKING`-only and this module has no
`from __future__ import annotations`, so a dataclass field annotation is evaluated at import. **The
report's framing is right and the rule is worth carrying**: the next slice adding a field to
`Prepared` gets no help from either gate, and only running catches it.

### No second executable reader — the sweep, in more spellings than the report used

The report swept `getsource` and two `setattr` spellings. That is *a grep for one spelling*, so I
widened it: `getsource`, `__code__`, `co_names`, `import dis`, `ast.parse`, `mock.patch`,
`patch.object`, `setattr("publishable…`, `setattr('publishable…`, `inspect.` over `tests/`.
Thirteen hits, every one attributed: two `ast.parse` calls, neither aimed at `cli.py`
(`test_secrets.py:177` walks `secrets.py`'s own file; `test_cli.py:786` walks a *generated
template*), two `inspect.getsource` calls (the retargeted pin and its `runner.execute_plan` arm),
one `inspect.signature` in `test_report.py`, three `uv_add` monkeypatches, three
`publishable.stats`/`artifacts` string patches, one `inspect.isgenerator`. **No second executable
reader is aimed at `command_run`.** The report's load-bearing claim survives a wider sweep.

---

## 5. Findings

### Major 1 — correction 22 has no durable owner, and its own enumeration undercounts by two sites

**Not task 2's to fix** (`*.md` was on its must-not-touch list, and it was right not to
self-authorize). It is a gap in the *filing*, and the repo has a rule for exactly this: *a ledger
line saying "filed" is not a filing*, and an owner named as "whichever task already does X" points
at nothing.

Measured, not judged:

- `grep -n 'command_run\|correction 22\|H9a\|_prepare_run' docs/superpowers/spec-defects.md` → **no
  H9a entry, no correction-22 entry.** The only home of this filing is a task report.
- Plan **task 6** is scoped to § Draft runs (`must not touch: … § Operation commands' rows`); plan
  **task 9** is scoped to § Operation commands' `dry-run` row and says *"must not touch: … any other
  `Status` cell"*. **Neither names a § Errors row.** The report's suggested owners do not own it.
- The enumeration itself: the report says *"**Five** in `docs/reference.md` are false about
  **where**"* and then lists **four** (lines 1150, 1151, 1152, 1153). It omits two further
  false-location sites in the same section that it did not name at all:
  - **line 1112** (prose, not a row): *"the dirty gate and the empty-file-list gate, both inside
    `command_run`"* — both are now in `_prepare_run`.
  - **line 1149** (`E-NO-GIT-REPO`): *"`command_run` and the `generate`/`init` dispatch call it
    uncaught"* — that `find_repo_root` call is now in `_prepare_run`.

  So: **six sites, filed as five, listed as four, owned by nobody.**

**Adjudication of "is a signpost enough".** For the ~45 `src/` and `tests/` prose sites, **yes** —
the signpost lives in `command_run`'s own docstring, which is precisely where a reader who greps
`command_run` lands, so every one of them resolves in one hop; and rewriting them would require
deciding which half of the split each sentence names, which is the *a rewrite invents* hazard. For
the **normative § Errors rows, no.** § Errors carries one row per code, the rows name a function that
no longer holds the code they describe, and *a § Errors row narrower than (or wrong about) its code*
is the shape that produced whole-branch Majors on three sub-slices. The signpost mitigates
misdirection; it does not make the row true.

**What this needs:** a controller ruling appending the six sites to a named task with the edit
specified — per *a ruling that overrules a brief has to reach the brief*, the ledger alone reaches no
implementer.

### Minor 1 — task 1's mutation failure counts are single-test-scoped and reported without their scope

The b1 report states *"Result: 1 failed"* for each of the ten arms. That is the count over a
single-test selection, and it is not stated as such. Arm C1's mutation
(`{"completed": EXIT_PARTIAL, …}`) actually produces:

```
uv run pytest tests/test_cli.py -q         → 247 failed, 196 passed, 1 skipped
uv run pytest tests/test_cli.py -k h9a     →   4 failed, 7 passed
uv run pytest -k h9a_arm_c_completed       →   1 failed          ← the reported figure
```

Arm liveness — the property the brief demanded — is unaffected: every arm does fail, and I verified
all ten. But the full suite was never run under any arm mutation, so **a mutation whose collateral
damage lay outside the arm could not have been detected**, and a reader takes "1 failed" for a suite
count. (Task 2's report is the contrast: it ran the full unfiltered suite for every mutation and
stated the counts, and all four of its numbers reproduced exactly.)

### Minor 2 — both of arm D's required greps are miscounted, and 30 hits went unattributed

The brief required both greps *"with every hit attributed."* At `main`:

- `grep -rn wall_seconds tests/` → **9** hits, not 8. `tests/test_cli.py:18041`
  (`wall_seconds=0.0`, an `ExecutionResult` built directly) is unattributed — the report attributed
  that shape in `test_stats.py`, `test_runner.py` and `test_run_record.py` and missed
  `test_cli.py`'s own.
- `grep -n 'keys()) ==' tests/test_cli.py` → **30** hits, not 1. **Twenty-nine unattributed.**

**The conclusion survives**, and I checked it rather than assuming: I enumerated all 30 and none
asserts an `executions.jsonl` **line's** key set — `:16970` is the execution block's top level
(`["shared", "conditions", "summary"]`), exactly as reported, and the rest are `run.yaml`, `sweep.yaml`,
`provenance`, metric-entry and parquet-row key lists. So arm D really is new coverage. But a grep
reported as one hit when it is thirty is *the count standing in for the enumeration*, in a task whose
brief singled that grep out.

### Minor 3 — "two imports added, both type-only"

Three names in two statements (`GitInfo`; `Repeat`, `RepeatLevel`), added as **runtime** module-scope
imports. They must be runtime imports, for the same reason `Condition` must be quoted — it is the same
fact as the report's own § 4 finding, described as if it were the opposite.

### Not a defect, worth recording

**§ 0's one weakening was unnecessary.** Parquet compared by `(path, size)` rather than bytes, on the
ground that a writer's embedded metadata makes a byte comparison a question about `pyarrow`. In my
comparison all four `units.parquet` files are **byte-identical** (`cmp` on each). The exemption cost
nothing and bought nothing; a future comparison can compare them as bytes.

### Undisclosed drops — none found

Both briefs diffed against what shipped. Task 1: arms A–E built, F and G cited as instructed, arm C's
fourth sub-claim by citation **disclosed** in the report's own Concerns. Task 2: 35 fields → 36
disclosed as correction 21 (and the extra field is `config_path`, in the position the report claims,
with the brief's 35 in the brief's exact order); the false `c` docstring ground **deleted rather than
rewritten**, which is the right move and which I confirmed against the code (`c` is not unpacked, and
`ruff`'s `F821`-clean status is what makes "no post-seam statement reads it" a complete argument);
`draft` accepted-and-unused disclosed with `[tool.ruff.lint] select = ["E","F","I","UP","B"]` verified
(**no `ARG`**, so it is a judgement and not a forced deviation); the credential fixture built rather
than substituted by an AST assertion. `command_run` gained a docstring the brief's four-line sketch
did not show — disclosed as the correction-22 signpost, and it sits below both moved bodies so neither
diff is affected (re-checked: `return Prepared(` at 2530, exec body at 2625). **Nothing dropped
silently.**

---

## 6. Reconciliation

`main` 2973 passed → HEAD 2984 passed. **+11**: task 1's ten arms (A ×1, B ×1, C ×3, D ×1, E ×4) and
task 2's one credential fixture. Skips (1) and xfails (2) unchanged. Every mutation reverted by
editing back and **every revert verified by re-running**, not by `git status`; the final full suite is
byte-for-byte the same result as the pre-mutation baseline.
