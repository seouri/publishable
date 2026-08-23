# Task 2 report — H9a the extraction (`Prepared`, `_prepare_run`, `_execute_prepared`)

**Written 2026-08-23 against branch `h9a-re-entry-seam`.** Ruling S, T and U all bind; each is
answered in its own section below.

---

## § 0 The normalization list, written BEFORE the work

Fixed here before a single line moved, so that no normalization can be one chosen after seeing a
diff. It is design § 5's list **verbatim**, plus one narrowing and one addition, both stated with
their reason:

Design § 5's list, as written there:

1. timestamps — `at`, `started_at`, `wall_seconds`
2. `run_id` and everything derived from it — the run-directory name, `latest`
3. absolute paths
4. `hostname`

**One narrowing, with its reason.** `provenance.git.commit` is **not** normalized here, and it was
normalized in task 1's arm A. The reason is that the two fixtures differ in kind: `run_a_project`
makes a **fresh commit per invocation**, so a commit SHA is timestamp-sensitive there, while this
comparison **scaffolds and commits the project exactly once** and then runs the *same* project
directory twice, under two different `publishable` trees. `git.commit`, `code_hash`,
`parameters_hash`, `input_manifest_hash`, `uv_lock_hash` and `units_hash` are therefore all
**stable across the two sides and are compared as values**, which makes this comparison strictly
stronger than arm A's on those six leaves. Narrowing a normalization list is only safe in that
direction, and this is the direction.

**One addition, with its reason.** For non-text artifacts inside the run directory (`units.parquet`,
`measurements.parquet`) the comparison is `(path, size)` rather than `(path, bytes)`. Parquet
writers embed a `created_by`/metadata block, so a byte comparison of those files answers a question
about `pyarrow`, not about this extraction. The three text artifacts a run writes — `run.yaml`,
`sweep.yaml`, `executions.jsonl` — are compared as **full text**, leaf by leaf for `run.yaml`.

**Anything not in that list is a difference that must be attributed individually.**

## § 0b The seam is a clean statement boundary — the sentence that licenses "moved verbatim"

```
python3 -c "
import ast; fn=[n for n in ast.parse(open('src/publishable/cli.py').read()).body if getattr(n,'name',None)=='command_run'][0]
for n in ast.walk(fn):
    if isinstance(n,(ast.Try,ast.With,ast.For,ast.While,ast.If,ast.FunctionDef)) and n.lineno<2430<=n.end_lineno: print(type(n).__name__,n.lineno,n.end_lineno)
"
→ FunctionDef 2009 3924
```

The **only** compound statement spanning line 2430 is `command_run` itself. The enclosing statement
list confirms it: the last top-level statement of phases 1–5 is the `upstream_resolver` assignment
at 2426–2428, the next is `run_dir = allocate_run_dir(...)` at 2430, and 2429 is blank. So the cut
is a block move of whole statements and not a re-indentation of a fragment.

---

## § 1 What was built

`src/publishable/cli.py`, three new top-level objects where `command_run` stood, plus `command_run`
itself as a four-line caller:

| Object | Lines (new file) | What it is |
|---|---|---|
| `Prepared` | 2010–2092 | Frozen dataclass, **36** fields |
| `_prepare_run(config_path, *, allow_dirty)` | 2095–2567 | Phases 1–5; returns `Prepared \| int` |
| `_execute_prepared(prepared, *, draft)` | 2570–4119 | Phases 6–10; unpacks 35 of the 36 |
| `command_run(config_path)` | 4122–4133 | `_prepare_run(..., allow_dirty=False)`, `isinstance`, `_execute_prepared(..., draft=False)` |

Two imports added, both type-only: `GitInfo` (from `publishable.provenance`), `Repeat` and
`RepeatLevel` (from `publishable.replication`).

## § 2 The extraction is a block move — the two slice diffs

The comparison is against `src/publishable/cli.py` **as it stood before this task**, copied to
scratch before the first edit. Both diffs are taken **after** `ruff format`, so no reflow is hiding
in them.

**A. Phases 6–10, old `2430,3924` versus new `2625,4119`:**

```
diff <(sed -n '2430,3924p' cli.py.prework) <(sed -n '2625,4119p' src/publishable/cli.py)
→ (no output)     IDENTICAL, 1495 lines
```

**Zero differing lines in the 1495-line body.** That is what the one `p = prepared` unpack block
buys, and it is the only mechanical check a reviewer has on a move this size.

**B. Phases 1–5, old `2010,2428` versus new `2110,2528`:**

```
diff <(sed -n '2010,2428p' cli.py.prework) <(sed -n '2110,2528p' src/publishable/cli.py)
19c19
<     if git.code_dirty:
---
>     if git.code_dirty and not allow_dirty:
```

**Exactly one differing line in 419**, and it is Ruling T's one intended change.

**C. Scope.** `git diff --stat` names `src/publishable/cli.py` and `tests/test_cli.py` and nothing
else. `git diff src/publishable/provenance.py | wc -l` → **0**: `git_provenance`, its `-c`
neutralization flags and `HASHED_TREES` are byte-unchanged, which is Ruling T's stated evidence.
`runner.py`, `apparatus.py`, `run_record.py` and every `*.md` are untouched.

## § 3 Ruling S — what was NOT moved

`_resolved_group_axes` is called at **new line 2414** and `arm_members` at **2431**, both inside the
419-line block whose diff is the single dirty-gate line. So their positions relative to every
neighbouring statement, and their relative order to each other, are preserved **mechanically** —
the diff proves it rather than an inspection asserting it. Nothing about *when* they run changed.

**I found no reason the hoist would have made this extraction cleaner.** The two calls sit in the
middle of a block that moved verbatim; hoisting them would have turned a one-line diff into a
reordering that no fixture in this slice separates, and it is H3c-3's task 2. Not done, and there
was no temptation to do it.

## § 4 Corrections against the code — TWO, both new, one of which is a blocked gate

### Correction 20 (blocking) — `tests/test_apparatus.py::test_cli_and_runner_call_sites_pass_the_named_constants` reads `command_run`'s SOURCE, and the extraction moves what it reads

```
cli_source = inspect.getsource(cli_mod.command_run)
assert "phase=apparatus.PHASE_RUN_START" in cli_source
assert 'phase="run_start"' not in cli_source
```

The run-start probe round is in phases 6–10 (design Decision 6 measured it at old line 2565, after
`allocate_run_dir` and inside `with RunLock`), so it now lives in `_execute_prepared` and
`getsource(command_run)` returns the four-line caller. The test fails on the first assertion.

**Not edited, and the branch is left red on purpose.** The task 2 brief: *"If any existing test's
expectation moves, STOP and report it rather than editing it — a moved expectation is either a
finding or a disclosure, never a fix."* H6b left its branch red for the same class of thing and it
was right; H6a's fault was self-authorizing.

Greps run before reporting it, every hit attributed:

- `grep -rn 'getsource' tests/` → **3** hits. `tests/test_apparatus.py:1396` (this one, over
  `cli.command_run`), `tests/test_apparatus.py:1400` (over `runner.execute_plan` — untouched by
  this task, and it passes), and `tests/test_cli.py:4892`, which is prose inside a docstring
  *about* a superseded `getsource` count, not a call.
- `grep -rn 'command_run' tests/` → 30+ hits; **every one except `test_apparatus.py:1396` is prose
  inside a docstring or comment**, so no other test's reader is aimed at the function.
- `grep -rn 'getsource\|call_sites_pass_the_named_constants\|test_apparatus'` over the plan and the
  design → **no hit naming this pin**. It is in no fixed-file list and has no pre-written post-edit
  state, which is exactly why it needs a ruling rather than an edit.
- `grep -rn 'monkeypatch.setattr(cli_mod\|setattr(cli,' tests/` → 8 hits, all aimed at **module
  globals** (`resolve_units` ×4, `execute_plan`, `assignment_for`, `_resolved_resample`,
  `cli_mod.apparatus._probe_for`). Moving code *within* the module does not change a global lookup,
  and all eight tests pass. This is the `CLAUDE.md` sweep for *a monkeypatch left aimed at a name
  the code no longer calls*, run because this task moved 1900 lines of call sites.

**The ruling this needs is TWO edits, not one**, and both must be authorized together or it
authorizes half of one:

1. `inspect.getsource(cli_mod.command_run)` → `inspect.getsource(cli_mod._execute_prepared)`.
2. The pin's own docstring sentence — *"This pin's own scope is exactly these two function bodies
   (batch B2 review, Minor 3) — it inspects `command_run` and `execute_plan` and nothing else"* —
   goes **false** when the reader moves. A retarget that leaves it standing ships a false claim
   inside a pin, which is the habit `CLAUDE.md` says costs the most.

The four asserted literals do not move under either edit. **I am reporting that distinction, not
acting on it** — deciding that "the reader moved, not the expectation" licenses an edit would be
answering *may I edit this?* with a proxy, and that is the substitution this repo has paid for
twice.

### Correction 21 — the crossing set is 36, not 35, and the plan's measurement could not have seen the 36th

`Prepared` has **36** fields. `config_path` is the one the plan's list is short by, and the reason
is mechanical rather than careless: the plan's measurement was an `ast` walk for names in **`Store`
context**, and **a parameter is an `arg` node, never a `Name` in `Store` context.** `config_path`
is read after the seam at the one site H8b Decision 7 added:

```
(run_dir / "config.yaml").write_bytes(config_path.read_bytes())
```

It was found by **`ruff`'s `F821`** on the first check after the surgery — not by the walk, not by
`mypy`. `ruff`'s scope analysis is complete for undefined names, and it reported exactly one, which
is the mechanical evidence that `config_path` is the **only** omission. It is field **1**, before
`c`, because it is bound at function entry and the fields are in assignment order.

**The plan's 35 is otherwise exactly right, verified by re-running the measurement rather than by
eye.** A raw Store-walk gives **38** names assigned before the `allocate_run_dir` call and loaded
after it; removing `u` and `r` (comprehension targets, comprehension-scoped in Python 3, so they
never touch an outer binding) and `warn_c` (re-bound at old line 3905 before its read at 3906)
leaves 35, and the assertion `raw_minus_three == BRIEF_LIST` is **`True` including order**. That
reconciles with the plan's own corrections 13 and 17 rather than minting a fourth number: 38 − 3 =
35, and 35 + `config_path` = 36.

### The `c` field — the docstring's stated ground was false and was replaced by the measurement

The brief's docstring says `c` is carried *"because phases 6-10 append to the same collector."*
**That is false against the code.** Every post-seam occurrence of the name `c` is a comprehension
target — old lines **2459**, **2724** and **3754** — and comprehension targets have their own scope
in Python 3, so none of them is the outer `Collector`. Phase 9's three collectors are each **fresh**
(`warn_c` at 3905, `aggregate_c`, `drift_c`). Nothing in phases 6–10 reads or appends to `c`.

Per `CLAUDE.md` — *prefer deleting a claim to rewriting it* — the false clause is **deleted** and
replaced with the measurement: `c` is carried because a second entry into phases 1–5 needs the
diagnostic channel those phases rendered from, and **no statement in phases 6–10 reads it at this
commit**. The consequence is visible in the code rather than only in the docstring: `c` is the one
field `_execute_prepared` does **not** unpack, because a local nothing reads is an `F841`. So of the
36 fields, 35 are read in phases 6–10 and `c` is not.

### Finding — a runtime-only failure that both static gates passed

`conditions: list[Condition]` is written **quoted**. `Condition` is a `TYPE_CHECKING`-only import
(`cli.py` line ~147) and a dataclass field annotation **is** evaluated at runtime — this module has
no `from __future__ import annotations`. `uv run ruff check .` passed clean and `uv run mypy`
reported *"Success: no issues found in 52 source files"* with the bare name; the first `import
publishable.cli` raised `NameError: name 'Condition' is not defined`. **Only running caught it**,
and it was caught by the two-worktree comparison's own driver, before any test ran. Recorded as a
finding rather than as an incidental fix: it is this transcript's own instance of *a probe that runs
is what catches what a static gate cannot*, and the next slice adding a field to `Prepared` needs to
know the rule.

### A brief claim, grepped rather than repeated

`_prepare_run`'s docstring asserts **"Phases 1-5 never return `EXIT_OK` today."** Enumerated by
listing every `return` inside the new function body: **four** `return EXIT_WRONG` (at new 2118,
2134, 2214, 2490), one `return unignored_under_hashed_trees(...)` inside the nested `_include` def —
which is plan correction 14's fifth-that-is-not-an-early-exit, confirmed — and the closing
`return Prepared(...)`. **No `EXIT_OK`, no other code.** The claim holds and was checked, not
inherited.

## § 5 The two-worktree comparison

One config, one project directory, two `publishable` trees. `main` at `d61df9d` was checked out to
a scratch `git worktree`; the branch is this tree. The project — `publishable new`, a `generic`
experiment with a `grid` sweep over `analysis.method` (`pearson`/`spearman`), two `seed` repeats, a
20-unit roster, and a real derived metric through `aggregate` — was **scaffolded and committed
once**, then run twice against the same directory. It lives outside this repository (a probe that
runs a creation command belongs outside it).

**The positive control that keeps the comparison from being vacuous.** An editable install
registers a `sys.meta_path` finder, and a meta-path finder runs **before** any `sys.path` entry — so
both runs could have imported the *same* package and produced a byte-identical answer for the wrong
reason. The driver asserts the resolved module path after importing:

```
run 1: IMPORTED …/scratchpad/wt-main/src/publishable/__init__.py
run 2: IMPORTED /Users/joon/src/tries/publishable/src/publishable/__init__.py
```

Two different trees. The comparison is real.

### Results

| Surface | Compared as | Result |
|---|---|---|
| exit code | value | `0` vs `0` — **EQUAL** |
| `run.yaml` | **leaf by leaf**, dotted path and value, in order | **EQUAL, 147 leaves** |
| the run tree | **path by path** — kind, size, symlink target | **EQUAL, 26 paths** |
| stdout | **line by line** | **EQUAL, 4 lines** |
| stderr | full text | **EQUAL** (empty) |
| `sweep.yaml` | full text | **EQUAL, 30 lines** |
| `executions.jsonl` | full text | **DIFFERS** — attributed below |

The four stdout lines, in full, so the comparison is legible rather than asserted:

```
1:   warning W-ENV-UNLOCKED       environment
2:           no uv.lock found at <abs>/cmp/p/proj; the environment is not pinned, and `reproduce` will not be able to restore it
3: 1 problem (0 errors, 1 warning)
4: run.yaml → <abs>/cmp/p/results/<run_dir>/run.yaml
```

Lines 1–3 are worth naming: that is the `W-ENV-UNLOCKED` print site **inside phases 1–5**, one of
the six print sites the brief requires to stay on its current stream. It printed the same bytes to
the same stream from `_prepare_run` as it did from `command_run`.

### Every remaining difference, attributed individually

`executions.jsonl` differs as text. Re-compared **leaf by leaf under the same normalization list**
it is **EQUAL**, and the un-normalized differing keys are, per line:

| Line | Differing keys | On § 0's list? |
|---|---|---|
| 1 | `started_at`, `wall_seconds` | yes — item 1, timestamps |
| 2 | `started_at` | yes — item 1 |
| 3 | `started_at` | yes — item 1 |
| 4 | `started_at` | yes — item 1 |

**Unattributed differences: ZERO.** And the six leaves the § 0 narrowing left un-normalized —
`git.commit`, `code_hash`, `parameters_hash`, `input_manifest_hash`, `uv_lock_hash`, `units_hash` —
are compared **as values** and are equal, which is where this comparison is stronger than arm A's.

## § 6 Mutations — every one against the FULL, UNFILTERED suite, with the count I read

Post-extraction baseline for every row below: **1 failed, 2983 passed, 1 skipped, 2 xfailed** — the
one failure being correction 20's `getsource` pin, which fails identically in all six runs and is
subtracted in the *new failures* column. Each was checked against the body of the test it names
before being run. Every revert was done by **editing back** (never `git checkout`), `__pycache__`
cleared, and verified by `diff` against a pre-mutation copy **and** by re-running.

| # | Mutation | Read | New failures | Which |
|---|---|---|---|---|
| **a1** | in `_prepare_run`, `if git.code_dirty and not allow_dirty:` → `if False and …` | `4 failed, 2980 passed` | **3** | `test_h9a_arm_e_a_dirty_tree` (arm E, as prescribed), `test_run_refuses_a_dirty_code_tree`, `test_run_refuses_an_untracked_file_a_global_exclude_hides` |
| **a1′** | the property-**preserving** arm: `if not allow_dirty and git.code_dirty:` — same conjunction, both operands pure | `1 failed, 2983 passed` | **0** | identical to baseline, so a1's three failures are the property and not the line being touched |
| **a2** | **at the call site**: `command_run`'s `allow_dirty=False` → `True` | `4 failed, 2980 passed` | **3** | the same three |
| **b** | move `credentials = credential_values(...)` below the roster `try/except` | `8 failed, 2976 passed` + **`ruff` F821** | **7** | see below — **NOT blind** |
| **c** | delete `roster_c.credentials = credentials`, ordering untouched | `6 failed, 2978 passed` | **5** | see below |

**a1 and a2 are the same property mutated at two places, deliberately.** The trap is *a mutation
applied to a proxy — the extracted helper's body rather than the call site*; a1 is the body, a2 is
the call site, and both were run.

**Mutation b was named blind in advance by the design, and the measurement falsifies that.** It is
caught **statically** by `uv run ruff check .` — `F821 Undefined name 'credentials'` at the
`roster_c.credentials = credentials` line — because the `except` arm reads a name whose assignment
has moved below it. At runtime it is `UnboundLocalError` and **7** tests fail:
`test_a_resolvers_raise_at_run_is_redacted_rather_than_printed_whole` (all four parametrizations),
`test_h9a_arm_e_a_roster_refusal`, `test_command_run_threads_the_real_wide_cfg_to_its_own_resolver_call_too`,
and this task's own new fixture. **So the ordering is pinned, and loudly.** The design's prediction
was reasoned rather than measured, and this is the correction; the brief's instruction to *check each
mutation against the body of the test it names first* is what surfaced it. Property-preserving arm:
moving the same statement **up**, above `resolver_io = ResolverIO(input_dir)` — still before the
roster call — leaves the property and the suite intact.

**Mutation c is the one that proves the replacement fixture is not vacuous**, and it is why b alone
would not have been enough: b crashes *before reaching* the redaction, so it says nothing about
whether anything asserts the redaction. c leaves the ordering alone, passes `ruff` and `mypy`
clean, raises nothing, and simply publishes the credential — **5** tests fail, including
`test_h9a_b2_a_parameter_declared_credential_survives_the_roster_raise` on its
`<redacted:PUBLISHABLE_TEST_AZURE>` assertion with the sentinel present. Reading b's silence about
the fixture as confirmation would have been the *mutation's silence read as confirmation* shape.
Property-preserving arm: attaching a freshly recomputed but equal set
(`roster_c.credentials = credential_values(declared_credential_names(doc, run_template, conditions))`)
— same value, property held.

**The `isinstance(prepared, Prepared)` → truthiness mutation is blind and stays unpinned**, on the
design's own stated ground: `Prepared` has no falsy instance and `EXIT_OK` is `0`, and § 4's
enumeration above confirms phases 1–5 return **only `EXIT_WRONG`**, so `0` is unreachable as an
`int` return. `mypy` is the enforcer and arm E pins the four codes end to end. The rule is stated in
`_prepare_run`'s docstring, which is where a caller reads it.

## § 7 The blind mutation's replacement fixture

`tests/test_cli.py::test_h9a_b2_a_parameter_declared_credential_survives_the_roster_raise`. A
project-local template declaring `Param("llm.provider", requires_env={"azure_openai":
["PUBLISHABLE_TEST_AZURE"]})`, that variable set to the sentinel through a `.env`, `resolve_units`
raising a `ContractError` whose message carries the sentinel, and three assertions: the diagnostic
**is** produced (`E-UNITS-SOURCE-MISSING` present — the positive companion, without which a sweep
for an absent sentinel passes on a run that never raised), `<redacted:PUBLISHABLE_TEST_AZURE>`
present, and the sentinel absent from stdout+stderr.

**Why this is not an existing test pinned twice.** The shipped
`test_a_resolvers_raise_at_run_is_redacted_rather_than_printed_whole` reaches the credential set
through the template's own **`required_env`**. This one reaches it through the *other* half of the
union `declared_credential_names(doc, run_template, conditions)` computes — a
`Param(requires_env=)` resolved against the level a declared parameter actually holds — which is
precisely **why** `credentials` needs `conditions` and `run_template` and therefore cannot be
computed at the top of the command. Greps run before writing it, every hit attributed:
`grep -n requires_env tests/test_cli.py` → **3** hits — the `_LOCAL_CRED_TEMPLATE` literal (11703),
a docstring above `test_a_project_local_template_s_credentials_are_redacted_too` naming it (11718),
and `test_..._declared_credential_names_for_and_check_requires_env` (11851). **None of the three
raises from the roster**: the first two leak from a **step's** own error, which is `execute_plan`'s
redaction at a different site, and the third is a unit test of the name resolution with no run at
all.

**It is not an assertion over `_prepare_run`'s own AST**, deliberately. Statement position answers
*where does this sit*, not *does a credential leak*, and answering with a position is the proxy
substitution the brief forbids. Mutation c above is the evidence it can fail.

## § 8 `draft` is accepted and unused, and task 3 owns the wiring

`_execute_prepared` takes `draft: bool` and does not read it. `assemble_run_yaml` already has
`draft: bool = False` (measured, `run_record.py` § `assemble_run_yaml`) and this task leaves its
call site unchanged, because **task 3's own section owns that wiring** (*"`_execute_prepared` passes
`draft=draft` to `assemble_run_yaml`, which already takes it"*) together with fixture Q and the
mutation that catches it. It is threaded now rather than added later so `command_draft` is one call
and not a second copy of a 1495-line function.

Checked before leaving it unused: `[tool.ruff.lint] select = ["E", "F", "I", "UP", "B"]` — **no
`ARG`**, so an unused argument is not a gate failure and this is a judgement rather than a forced
deviation. Wiring it would have broken § 2's zero-line body diff, which is the only mechanical
check on the move. `_execute_prepared`'s docstring names task 3 as the owner so a reader does not
meet the parameter as an omission.

## § 9 Gates

| Gate | Result |
|---|---|
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 93 files already formatted |
| `uv run mypy` | Success, no issues, 52 source files |
| `uv run pytest` (full, unfiltered, foreground, caches cleared) | **1 failed, 2983 passed, 1 skipped, 2 xfailed** in 221s |

The arithmetic, because it is the behaviour-preservation claim: baseline before this task was
**2983 passed, 1 skipped, 2 xfailed, 0 failed**. This task adds **one** test. 2983 + 1 − 1 = 2983
passed, so **exactly one previously-passing test moved**, and it is correction 20's source-text
reader — not a behaviour. **All ten of task 1's arms A–E pass**, which is the evidence Ruling U's
pin was captured to produce: a 1916-line shipped command's `run.yaml`, stdout, exit codes, ledger
key set and four early exits are unchanged.

`mypy` lost no narrowing across the seam — the `| None` fields (`roster`, `eval_roster`,
`partitions`, `clusters`, `weights`) are each re-narrowed by a guard that moved with them, so no
`assert` was added and no line of the body changed for the type checker's benefit.

## § 10 Concerns

1. **Correction 20 leaves the branch red and needs a controller ruling** — the two edits are written
   out above so it costs one line to grant. Not self-authorized.
2. **The design's "blind" prediction for mutation b was wrong** (§ 6). Worth carrying: the shape is
   the same as the plan's own § Corrections — a prediction reasoned from the intent rather than
   measured. The replacement fixture was built anyway and mutation c shows why that was right.
3. `Prepared` is 36 fields and will be unpleasant to read; design Decision 5 already accepts that
   cost. The `config_path` addition does not change the argument.
4. Non-text run artifacts (`units.parquet`) are compared by `(path, size)` and not by bytes (§ 0's
   one addition). A parquet writer's embedded metadata makes a byte comparison a question about
   `pyarrow` rather than about this extraction. If a reviewer wants bytes, the two run directories
   are still on disk under the scratch `cmp/` path.

---

## § 11 The sweep in the OTHER direction, and two additions to correction 20

### The baseline the § 2 diffs rest on is now VERIFIED, not asserted

`cli.py.prework` is a scratch copy taken in a session that had earlier inserted and reverted 35
`reveal_type` lines, so its provenance was worth proving rather than assuming:

```
git show HEAD~1:src/publishable/cli.py | diff - <scratch>/cli.py.prework
→ (no output)     BASELINE VERIFIED AGAINST HEAD~1
```

So § 2's *IDENTICAL, 1495 lines* and *exactly one differing line in 419* are against the committed
pre-task file, not against a working copy.

Two lint facts belong beside them, because they discharge the field-set claim by a **gate** rather
than by a walk. `ruff` selects `F`, so: **`F841` clean** means every one of the 35 unpacked locals in
`_execute_prepared` is actually read — an unread one would fail the gate — and **`F821` clean** means
none is missing. That is how `config_path` was found, and it is why no 37th can be hiding.

### Correction 22 — ~45 prose references attribute a behaviour to `command_run` and mean *the `run` command*

I swept `tests/` for readers aimed at what I moved (§ 4) and **did not sweep `src/` or the four
documents** — which is `CLAUDE.md` § Habits' *sweep for the claim, not for the file the claim was
first noticed in*, run in one direction. Corrected here. `grep -rn 'command_run'` over
`src/`, `tests/`, `README.md` and `docs/*.md` → **216 hits**, attributed:

| Where | Hits | Status |
|---|---|---|
| `src/publishable/cli.py` | 32 | mine; the signpost below answers them |
| `src/publishable/validate.py` | 13 | prose only |
| `src/publishable/apparatus.py` | 10 | prose only; **must-not-touch** |
| `src/publishable/units.py` | 6 | prose only |
| `src/publishable/runner.py` | 6 | prose only; **must-not-touch** |
| `src/publishable/artifacts.py`, `lineage.py` | 5 each | prose only |
| `sweep.py` (4), `freeze.py` (3), `diagnostics.py` (2), `report.py` (2), `stats.py` (2), `hashes.py` (1), `run_record.py` (1) | 18 | prose only; `run_record.py` **must-not-touch** |
| `docs/reference.md` | **18** | prose only; `*.md` is **forbidden to this task** |
| `README.md`, `design-principles.md`, `experimental-designs.md` | **0** | nothing to correct |
| `tests/` (8 files) | 99 | prose in docstrings, except the ONE reader already filed as correction 20 |

**Every one of the 216 is prose except a single executable reader** — `test_apparatus.py:1396`'s
`inspect.getsource` — which is correction 20 and is already filed. That is the load-bearing finding
of this sweep: no second reader is aimed at the function.

**Which of the prose claims actually go false.** All of them are *location* claims about a function
that still exists and is still the entry point for `run`; none is false about behaviour. Five in
`docs/reference.md` are false about **where** and would misdirect a reader who greps:

- line 1150 — `E-GIT-NO-COMMIT`: *"reached from exactly one place, `cli.command_run`, while computing
  the `GitInfo` the dirty gate reads next"* → the `git_provenance` call is in `_prepare_run`.
- line 1151 — `E-CODE-DIRTY`: *"Checked inside `command_run`"* → `_prepare_run`. (Also worth the
  owner's attention: the gate is now `git.code_dirty and not allow_dirty`, and **`run` passes
  `False`, so nothing about the pathspec or the refusal changed** — Ruling T.)
- line 1152 — `E-CODE-EMPTY`: *"Checked at `command_run`'s single hashing site"* → `_prepare_run`,
  and the row's *"positioned after unit resolution … and before `allocate_run_dir`"* is still exactly
  true, which is plan correction 19 holding.
- line 1153 — `E-CODE-FILE-LIST`: *"the one `check-ignore` call `command_run`'s single hashing site
  makes"* → `_prepare_run`.
- the six **dual-surface** rows (`E-RESOLVER-RAISED`, `-SWEPT-PARAM`, `E-UNITS-ATTR-MISSING`,
  `-EMPTY`, `-KEY-DUPLICATE`, `-SOURCE-UNREADABLE`) all say *"`command_run` … reports it there too"*
  — true as statements about the `run` **command**, imprecise as statements about the function.

**Not corrected here, and the reasons are three.** `*.md` is on this task's must-not-touch list;
four of the `src/` files are too; and a rewrite of the remainder would have to **decide which half of
the split each sentence now names**, which is the *a rewrite invents* hazard `CLAUDE.md` names —
against the alternative of a pointer, which invents nothing.

**What I did instead, and it is one edit rather than forty-five.** `command_run`'s docstring gains a
**signpost** naming which phases live in which helper, so every existing "`cli.command_run` does X"
reference resolves in one hop. It sits *below* both moved bodies, so § 2's two diffs are unaffected —
re-checked after the edit, the exec body still begins at 2625 and `return Prepared(` still at 2530.
Correction 22 is filed for an owner who may edit `*.md`; `docs/reference.md`'s five location rows are
the concrete work, and the natural owner is whichever task in this slice already edits § CLI
reference and § Errors (task 9 edits the `Status` column; task 6 corrects § Draft runs).

### Correction 20, two additions

**The pin's second assertion now passes VACUOUSLY**, and that changes the character of the ruling.

```
cli_source = inspect.getsource(cli_mod.command_run)
assert "phase=apparatus.PHASE_RUN_START" in cli_source     # FAILS
assert 'phase="run_start"' not in cli_source               # passes — because nothing is there
```

The negative arm is satisfied by an absence produced by the reader looking at the wrong function,
which is precisely this repo's *a control asserting only absences passes identically if nothing ran*.
So the pin is **half red and half silently useless**, not merely red — which is the argument for why
it cannot be left sitting.

The ruling therefore needs **three** items, not two:

1. `inspect.getsource(cli_mod.command_run)` → `inspect.getsource(cli_mod._execute_prepared)`.
2. Correct the docstring sentence *"it inspects `command_run` and `execute_plan` and nothing else"*,
   which goes false the moment the reader moves.
3. **Prove the retargeted pin can still fail**: mutate `phase=apparatus.PHASE_RUN_START` back to
   `phase="run_start"` in `_execute_prepared` and show **both** assertions fail. H6b's Major 2 is
   exactly *proving an arm cannot move is not proof the line is pinned*, and item 1 alone would leave
   the negative arm unproven for a second time.

Still not self-authorized, and the branch stays red.
