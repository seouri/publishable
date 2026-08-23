# H9a batch 6+7 — tasks 10-14 — the probe round, *Creates nothing*, the documents and the records

**Branch `h9a-re-entry-seam`. Five commits, one per task, in order.**

| Task | Commit | What it is |
|---|---|---|
| 10 | `204fbf7` | `dry-run` probes the apparatus, appends nothing — `_dry_run_probe`, Fixtures V, W, X |
| 11 | `42019f5` | Fixture Y gains the arm that can see the probe round, and `_h9a_snapshot` |
| 12 | `efad33c` | § Before you spend it's transcript; fifteen § Errors / § Warnings rows widened |
| 13 | `c925416` | § The apparatus files, § Mistakes core prevents, `apparatus.py`, `spec-defects.md`, `CLAUDE.md` |
| 14 | `e133833` | Both consistency passes; § Executability's dated entry |

**Gates, all clean at `e133833`:** `uv run ruff check .` → *All checks passed!*;
`uv run ruff format --check .` → *93 files already formatted*; `uv run mypy` → *Success: no issues
found in 52 source files*; `uv run pytest` → **3019 passed, 1 skipped, 2 xfailed** in 215.94s.
**The dispatch's target was 3012 and the suite is 3019: +7, which is exactly the seven new test
functions** (five in task 10 — Fixture V's three arms, W, X — and two in task 11 — Fixture Y's new
arm and the snapshot helper's can-fail proof). No other count moved.

**No guard-pin arm was opened.** Arms A-E have no authorized editor and F was task 9's; none was
touched. `git diff main...HEAD -- tests/` is additive at every hunk in this batch.

---

## Task 10 — and YES, the `probes the apparatus` clause is now true, verified by RUNNING

The batch 3-5 review left Minor 5 open by explicit ruling: `reference.md`'s `dry-run` row claimed
`probes the apparatus` and this branch did not, with the escalation *"it promotes to a Major at the
gate if task 10 does not land."* **Task 10 landed and the clause is true.**

**Three homes, not one — the finding the review's own wording could hide.** Minor 5 was filed against
the § CLI reference **row**. `grep -rn "probes the apparatus" README.md docs/ src/ tests/ CLAUDE.md`
attributes **three** homes in `reference.md` carrying the clause about `dry-run`: `:368` (§ Operation
commands' prose), `:3103` (§ Before you spend it's *"real credentials and a reachable apparatus"* —
the strongest of the three), and `:3673`/now `:3708` (the row Minor 5 named). All three are now true;
reporting only the row would have been *sweeping for the file the claim was noticed in*.

**Verified by running, outside this repository, through the real console script** — not by a test and
not by reading. An out-of-repo project with a project-local template declaring `apparatus_probe`, and
the probe supplied by a real installed distribution (a `.dist-info` with `entry_points.txt`, on
`PYTHONPATH`):

```
$ T14_CALLS=…/calls.txt PYTHONPATH=…/site:…/outside \
    uv run publishable dry-run …/proj/configs/t14/config.yaml
  warning W-APPARATUS-UNANSWERED apparatus
          condition `00_model=m1`'s fact `reagent_lot` came back `null` on 1 of 1 probes
  warning W-APPARATUS-UNANSWERED apparatus
          condition `01_model=m2`'s fact `reagent_lot` came back `null` on 1 of 1 probes
2 problems (0 errors, 2 warnings)
sweep: 2 conditions (grid) × 1 repeats = 2 executions
…
and 9 fixed files in that directory:
  apparatus/probes.jsonl
…
creates nothing
EXIT=0
$ cat calls.txt
m1
m2
$ ls -A …/results      # empty
```

Two calls, one per resolved condition, **each under that condition's own cfg** (`m1`, `m2` — not
`m1`, `m1`, which is what the wide cfg would have given); the declared-but-unanswered fact warns for
both conditions; `output_dir` is empty. **Then pinned by mutation** — a probe is a moment, a test is
tomorrow.

**What was built.** `cli._dry_run_probe(prepared) -> int | None`, sited after `_prepare_run` and
before any printing, assembled from the shipped pure pieces (`observe_once` → `check_facts` →
`Observations.record` → `warn_unanswered`). No `Observer` is constructed (Decision 6). `check_changed`
is not called, and the code carries the **measured** ground rather than "there is no baseline":
`Observations.record` fills `_first_answered` from the facts it is handed and `changed` compares the
*next* facts against that entry, so with one round per condition the value the gate would compare
against is the value it was just given. `apparatus.py` is untouched except for docstrings (task 13).
No code is minted.

**Decision 14's containment was copied with its `try` AND with both return branches.** A dispatch
failure is `EXIT_WRONG`; at the call site `E-APPARATUS-RAISED` earns `EXIT_EXTERNAL` and the other
four `APPARATUS_CODES` keep `EXIT_WRONG` — the split `command_run`'s own containment makes. Lifting
only the `except BaseException` shape would have been the partial copy Decision 14 exists to prevent.

### Task 10's mutations — each with its two branches checked, and one reported blind

| Mutation | Result | Two branches differ? |
|---|---|---|
| Remove the `try` around `observe_once`/`check_facts` | **2 failed** (`fixture_v_an_unreachable_apparatus_exits_five`, `fixture_w_a_credential…`) — and stderr printed `instrument rejected token sk-h9a-w-do-not-print` **verbatim** | Yes — the positive control leaked the declared credential, which is the whole of W |
| **Prescribed:** hoist the probe call above `_prepare_run` | **BLIND — reported, not claimed as passed.** `prepared` is unbound at that point, so the mutant raises `UnboundLocalError` before reaching any behaviour; `ruff` catches only the unused variable (F841), not the use-before-assignment | **No** — the mutant does not run, so the two branches cannot differ on the property X tests |
| **Substitute for it:** probe first, from a template resolved independently of `_prepare_run` (a plausible alternative implementation of the same feature) | **1 failed, on exactly the discriminating assertion** — `assert not entered.exists(), "the probe ran before validation refused the config"` — with the exit code still `1`, so an exit-code-only assertion would have passed | Yes |
| Also tried and rejected as a substitute: drop `c.has_errors` from `_prepare_run`'s validate gate | Fails X **on the exit code** (`assert 0 == 1`), never reaching the entry-file assertion — so it does not demonstrate the ordering | It differs, but on the wrong axis |

**Every count above is the number pytest printed**, from a run scoped to the named `-k` selection; no
count is offered from a single test file.

### Fixtures V, W, X — how each literal is obtained

- **V arm 1** asserts the ordered **list** of `instrument.model` values the probe saw
  (`["m1", "m2"]`), not a count: a count of 2 is also what two calls under the wide cfg would give.
  The tally is written **outside `output_dir`**, from an environment variable, so it is evidence *and*
  task 11's arm stays true.
- **V arm 2** asserts `W-APPARATUS-UNANSWERED` twice with both condition keys named, so a build that
  warned once for the whole command fails. `00_model=m1` / `01_model=m2` were read off the run, not
  guessed — my first draft asserted `00_m1` and failed.
- **V arm 3** asserts exit **5** *and* that `creates nothing` is **absent** from stdout, which is what
  pins the round's siting before the printing.
- **W**'s credential is declared through `Param(requires_env=)`, total over `choices`, and actually
  set in the environment, so `declared_credential_names` finds it and `credential_values` reads a real
  value. Both halves asserted: the secret absent **and** `<redacted:` present, because a command that
  printed nothing would satisfy the absence alone.
- **X** asserts the probe's entry file does **not** exist, plus a **positive control** in the same test
  that the same probe *does* write it when the config validates — so the absence is the ordering
  rather than an inert probe.

**No project-local probe exists, and that is forced rather than chosen**: `apparatus._probe_for`
resolves a name through `scan_group(PROBE_GROUP)` — package metadata — so the probe must come from an
installed distribution while the *template* can be project-local. Fixture U's own arrangement, cited
rather than re-invented.

---

## Task 11 — the finding: the design's prescribed Fixture Y mutation was BLIND on every shipped arm

**Measured, not reasoned.** The three shipped *creates nothing* arms
(`..._creates_nothing_under_output_dir_on_a_never_run_project`,
`..._leaves_an_existing_output_dir_byte_identical`, `..._against_a_live_lock_completes_and_takes_none`)
all drive `_h6a_t5_project`, whose `experiment_type: generic` resolves to
`GenericTemplate.apparatus_probe = None`. So `_dry_run_probe` returns at its first guard and the design's
mutation — *"add `append_observation` to `dry-run`'s round"* — has no round to add to.

Spliced in for real (`append_observation(prepared.output_dir, phase=PHASE_DRY_RUN, …)` inside the loop):

```
1 failed, 3 passed
FAILED …::test_h9a_fixture_y_dry_run_creates_nothing_while_the_probe_round_runs
E  Left contains 2 more items:
E  {'apparatus': None,
E   'apparatus/probes.jsonl': (276, '4c6ab047…')}
```

**The three shipped arms all pass; only the new one fails.** That is the proof they were blind rather
than merely quiet — the distinction `CLAUDE.md` draws under *reading a mutation's silence as
confirmation*.

**The new arm** is Y over a **probe-declaring** project whose `output_dir` already holds a completed
run, so `apparatus/` is inside the snapshot as an existing path rather than as an absence, paired with
two positives: the probe's tally gains exactly one entry per resolved condition (so the round really
ran) and the transcript printed.

**`_h9a_snapshot`** is the recursive `{relpath: (size, sha256)}` map the design names, with `None` for
a directory so a created-but-empty directory is a difference; **size AND digest** because a digest
alone cannot see an equal-content rename and a size alone cannot see a length-preserving edit.
`test_h9a_the_snapshot_helper_can_fail` proves it sees all three shapes **separately** — a helper that
saw one would pass a test asserting their disjunction.

**Second mutation:** `command_dry_run` creates `output_dir / "scratch"` → **3 failed, 1 passed**. The
one that passes is the live-lock arm, which asserts the lock file's bytes rather than the tree; named
here rather than left as a puzzle.

**Scope stays `output_dir`, and the docstring says why that IS the promise** rather than a weakening
of it: `dry-run` imports the entrypoint and runs `discover_local`, which writes `__pycache__` under
`src/**` and `templates/**` exactly as `validate` already does (§ Templates' *"goes dirty at
`validate`"*, measured live by H6b batch 4). A repo-wide assertion would fail and invite whoever met
it to weaken it.

---

## Task 12 — the sweep, the 20, and fifteen rows narrower than their code

### The sweep, run before any edit, files named individually, output never filtered

```
$ grep -n "<pat>" README.md docs/design-principles.md docs/experimental-designs.md \
      docs/reference.md CLAUDE.md docs/feasibility-llm-growth-studies.md
```

| Pattern | Homes | Attributed individually |
|---|---|---|
| `step directories` | **4**, all `reference.md` | `:368` (§ Operation commands prose, task 9's, outside its own section per its Concern 1) · `:3673` (§ CLI reference row, task 9's) · `:3756` (§ What `demo` walks you through, stop 4, task 9's) · `:3882` (§ Validation's plan-resolution prose, task 9's) |
| `would write` | **4**, all `reference.md` | the same `:368`, `:3673`, `:3756` — **plus `:3094`**, task 12's own `would write 64 artifacts` line |
| `64 artifacts` | **1** | `:3094` |
| `every artifact path` | **0** | the amendment's own claim, confirmed |

Zero hits in `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md` and `CLAUDE.md`
for all four patterns. **Re-run newline-insensitively** (whitespace collapsed to single spaces, per
file): identical counts 4 / 4 / 1 / 0.

**Can-fail proof:** the same newline-insensitive counter over `docs/reference.md` returns **4** for
`would write` and **0** for `zzz-not-present-zzz`, so it distinguishes present from absent.
**A sweep that silently did not run**, worth recording because a transcript cannot tell it from zero
hits: my first attempt used `grep -rn … --include=*.md`, which zsh rejected with *"no matches found"*
before `grep` ever ran. Recovered by naming the files, which the rules require anyway.

### FINDING (Minor) — the plan's *amended* sweep count is itself one short

§ Task 12's amendment, written in the batch 3-5 fix round **because the old target had zero homes**,
re-measured `would write` at **three** homes (`:3094`, `:3673`, `:3756`). It has **four**. The missed
one is `:368` — and `git show 574eba7:docs/reference.md | grep -c "would write"` → **4** confirms it
was four at the exact commit the amendment says it measured against ("`HEAD` at the start of this fix
round"), so this is a miscount rather than drift. `:368` is a line **that same fix round's own report
quotes verbatim** (`task-b4-report.md:468`). This is the shape the amendment was written to prevent,
one level up: *a hit in a file already accounted for reads as noise.* Caught by attributing every hit
individually rather than reconciling against the amendment's table. **The plan is a dated record and
was not retro-edited**; this report is the correction.

### The 20 — verified by running, and the arithmetic held

A 4-step project with the worked example's four **scopes** (`run` → `condition` → `repeat` →
`summary`), 3 conditions (`baseline` + a 2-value grid) and 5 seed repeats, built and `dry-run` outside
this repository:

```
would create 20 step directories under …/results/run_.../
  shared/step01_load_cohort
  conditions/00_baseline/step02_fit_model
  conditions/00_baseline/seed01/step03_analyze          (…5 per condition)
  …
  summary/step04_compare_methods
and 8 fixed files in that directory:
```

**20**, and the four components are 1 + 3 + 15 + 1 exactly as the plan derived them, so **the
arithmetic was right and the run is what says so.** The scope mix is load-bearing: four
*repeat*-scoped steps over 3 × 5 would have printed 60, and correcting the document toward that number
would have been the trap.

**What the document now carries.** The counting rule sits beside the number (one directory per planned
(step, condition, repeat) triple, `runner.step_dir_for`'s answer), the transcript's own last lines name
what is omitted, and the prose beside it cites `design-principles.md` § Greenfield only and names the
two run-time conditionals (`units.parquet`, `measurements.parquet`) that make the old promise
unsatisfiable rather than merely expensive. The transcript's seed labels are the worked example's own
(`seed17`, `seed42`, `seed137`, `seed1009`, `seed2027`) — see the filing below, which is why.

### § Exit codes and diagnostics — NO edit, and that is the answer

Its cost-ordering paragraph already states validate → input manifest → apparatus probe, exit `1`
without reaching the probe, `5` only for a config that validates — **true of the build as of task 10**,
so the paragraph gained a reader rather than a correction. The `3` and `4` rows already read
*"`run`, `draft`, `resume` only"*. Nothing was edited, on H6a's batch-6 restraint precedent.

### The per-code emit-site check — fifteen rows were narrower than their code

**§ Errors / § Warnings carry one row per code covering EVERY emit site, and each table's own scope
sentence limits no command** — checked, not assumed: § Warnings core reports says *"some fire at
`validate` time … others at `run` time … the table names which, in each row's condition"*; § Errors
`validate` reports scopes itself to what `validate` collects; § Errors core raises scopes itself to
raises plus two `Collector` refusals. None restricts which commands a row covers.

Every code `_dry_run_probe` can emit, and every code the extraction plus two new commands newly
routes, was read one at a time:

| Code | Row | Verdict |
|---|---|---|
| `E-APPARATUS-RAISED` | *"called at run start and before every execution"*; *"one of **three** outcomes"*; *"**A third surface**: `freeze`"* | **narrower — widened.** Called at `dry-run` too; three outcomes → four; a fourth surface added, with its own exit-5 reading |
| `E-APPARATUS-RETURN` | *"escaping `_execute_prepared`"* | **narrower — widened** to name the round that called it at each surface |
| `E-PROBE-UNKNOWN` | *"reached whenever `command_run` resolves the declared probe"* | **narrower — widened** to `run`/`draft` and `dry-run` |
| `E-PLUGIN-DECORATOR` | *"but **only at `run`**"* | **narrower — widened**; the `validate`-never-dispatches half kept |
| `E-PLUGIN-LOAD` | *"met only at `run`"* | **narrower — widened** |
| `W-APPARATUS-UNANSWERED` | *"at run end"*; *"**A second surface**: `freeze`"* | **narrower — widened**; a third surface, over the round's own counts, printed before the transcript |
| `E-APPARATUS-FACT-CREDENTIAL`, `-FACT-TYPE`, `-FACT-MISSING` | each *"Raised in `apparatus.check_facts`"* | **no edit needed** — none claims a command surface |
| `E-APPARATUS-CHANGED` | *"Raised in `apparatus.check_changed`"*; *"A second surface: `freeze`"* | **no edit** — `dry-run` does not call `check_changed`, so it is not an emit site and inventing a clause would be a claim nothing needs |
| `E-PLUGIN-COLLISION` | decided at registration / inside the import `E-PLUGIN-LOAD` contains | **no edit** — names no command surface for a probe |
| `E-TEMPLATE-COLLISION`, `E-TEMPLATE-LOAD` | *"every command that resolves a template meets it at load"* | **no edit** — already general, and `dry-run` is such a command |
| `E-RESOLVER-SWEPT-PARAM`, `E-RESOLVER-RAISED`, `E-UNITS-ATTR-MISSING`, `E-UNITS-EMPTY`, `E-UNITS-KEY-DUPLICATE`, `E-UNITS-SOURCE-UNREADABLE` | all *"`command_run` … at `run`"* | **narrower — widened** to *"every command that enters phases 1-5 — `run`, `draft` and `dry-run` — through `cli._prepare_run`"* |
| `E-UNITS-ATTR-COLUMN` | *"what `command_run` checks through `validate_config` … so `run` meets this refusal"* | **narrower — widened** the same way; its *"One emit path, not two surfaces"* claim still holds |
| `E-GIT-NO-REPO`, `-NO-COMMIT`, `E-CODE-DIRTY`, `-EMPTY`, `-FILE-LIST` | already `cli._prepare_run` | **no edit** — task 2 fixed these five |

**Disclosed as a fourth edit class rather than folded in silently.** Task 12's brief names three
edits; these are a fourth, and they are in scope because the narrowing is **this slice's own doing**
(two new commands and one extraction) and because a normative § Errors row narrower than its code is
the exact Major shape this family keeps finding. `cli.command_run` at § The one config file's
`null_test` clause was narrowed to `cli.py`, matching its four sibling clauses **verbatim** — a
deletion, not a rewrite.

**What was NOT touched:** § Operation commands' rows (tasks 4 and 9), § Draft runs (task 6), § The
apparatus files (task 13, done there), and the worked example's statistics — `r = 0.581 / 0.607 /
0.412` and every interval around them are byte-unchanged (`git diff main...HEAD -- docs/reference.md`
contains no `0.581`, `0.607`, `0.412`, `0.488`, `0.661` or `−0.169` line).

---

## Task 13 — the records

**§ The apparatus files.** *"at `dry-run`, at run start, before each execution, and at `freeze`"* →
`dry-run` deleted, and one paragraph added: `dry_run` is a **reserved** phase name no build appends,
because the ledger lives inside a run directory `dry-run` never creates, and naming it keeps the
vocabulary total over § The apparatus core can only observe's four places a probe runs.

**§ Mistakes core prevents (`experimental-designs.md`) — the second home the scoping does not name.**
*"its facts are recorded per condition at `dry-run`, …"* → *"it is called per condition at `dry-run`,
… and its facts are recorded from run start onward — `dry-run` probes but records nothing, having no
run directory to record into."* The mistake the row describes is still structurally prevented (the
gate fails the run), so the § Mistakes core prevents contract holds.

### The `dry-run` sweep over the four documents, every hit attributed

```
$ grep -n "dry-run" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md
```
Counted **now**, not carried: `README.md` **3**, `docs/design-principles.md` **2 lines / 3
occurrences**, `docs/experimental-designs.md` **1**, `docs/reference.md` **33 lines** (the plan's
figure of 20 predates tasks 9 and 12). Can-fail control: the same grep for `zzz-absent-zzz` returns 0
in each of the four.

- **README's 3** — a walkthrough pointer, an invocation line, a table row naming the command. None
  claims recording.
- **`design-principles.md`'s 2 lines** — checked rather than assumed, as the brief instructs: `:87` is
  *"There is no `--dry-run` … those modes are separate commands with their own names — `dry-run`,
  `resume`, `draft`"* (two occurrences on that line, both about flags-versus-names, both correct) and
  `:157` is the lifecycle-command list. Correct.
- **`experimental-designs.md`'s 1** — `:375`, the one fixed above.
- **`reference.md`'s 33** — thirteen are task 12's own § Errors rows; five are § Before you spend it
  and its neighbours; `:1025` is task 13's new paragraph; `:368`, `:3708`, `:3753`, `:3791`, `:3805`,
  `:3917`, `:1096`, `:1399`, `:347`, `:872`, `:972`, `:2046`, `:4155` were each read individually.
  **`:347`** (*"whether the apparatus is reachable is checked by `dry-run`"*) and **`:1399`** (*"It
  runs at `validate` and `dry-run`"*) are now true. **`:872`** and **`:972`** were already correct
  (`dry-run` takes no lock; it *builds* the manifest without writing it).

**FINDING the sweep caught, and fixed in the same commit — a third false build claim.** § Secrets &
credentials `:4084` read *"In this build the executing site is `run`; `draft`, `resume` and `dry-run`
inherit it when each is built."* False for two of the three as of this branch: `load_env` is in
`cli._prepare_run`, which all three of `run`, `draft` and `dry-run` enter. Corrected to name the three
executing sites and leave `resume` as the one still owed.

**`apparatus.py`.** The `PHASES` docstring's *"called by NOTHING at this commit … the filing, owner
H9"* paragraph would have gone false under its own slice's change — the most frequent single defect in
this family. Rewritten to say the constant is **reserved**, why, and citing **Decision 7** rather than
the struck filing. **Two neighbouring sentences that would have gone stale with it were corrected in
the same commit rather than left**: `append_observation`'s *"the other two are named so H8's and H9's
callers do not mint a fifth spelling"* (H9 now provably supplies no caller) and `replay_ledger`'s
*"nothing appends one **yet**"*. Every claim I put in the new paragraph was checked by grep first:
`tests/test_apparatus.py:1315` enumerates all four literals, and the two exclusion fixtures are
`tests/test_apparatus.py:1137` and `tests/test_freeze.py:357`.

### `spec-defects.md`

**STRUCK** — *"no build appends a `PHASE_DRY_RUN` ledger line…"*, with the resolution named and **both**
questions it left its owner answered: (a) no line is appended, (b) `replay_ledger`'s filter does **not**
widen. Reproduced before striking, and the count is the one the command printed:
`grep -rn "PHASE_DRY_RUN" src/` prints **six** lines, two of them code (the definition and its `PHASES`
membership) and four prose — **no call site passes it.** (My first draft of that sentence said "two
hits", which the command contradicted; corrected before commit.)

**AMENDED, not struck** — the S4c-task-9 `resolve_contrasts` precondition. H9a discharges **two** of its
three commands: `dry-run` by construction (`resolve_contrasts`' two call sites are
`_baseline_comparisons`/`_declared_comparisons`, called only from
`_compute_vs_baseline`/`_compute_declared_contrasts`, called only from `_execute_prepared` (2570-4120),
which `command_dry_run` (4427-4572) does not call — walked with `ast`, not with a grep), and `draft`
because it delegates to `_execute_prepared` and so *is* `run`'s sequence. It still binds `resume` (H9b)
and `reproduce` (H9c), so striking it would leave two live obligations unowned.

**RECORDED WITHOUT TAKING** — the file holds **eight** H9-owned entries, not the scoping's six, with a
table naming each and the part it belongs to. **The shape is the finding**: both missed entries name
their owner **in prose inside an appended amendment**, not in a heading's `— **Owner: H9**` suffix, and
every re-owning in this file is an appended paragraph because a dated record is appended to rather than
retro-edited. **A scoping that counts owners by heading under-counts by exactly the entries that were
re-owned after filing.**

**TWO NEW FILINGS, each reproduced, each with an owner that is a fact and a reason:**

1. **The worked example's seed *labels* cannot be produced by the seed *values* printed beside them.**
   `reference.md` shows `labels: [seed17, seed42, seed137, seed1009, seed2027]` beside
   `seeds: [17, 42, 137, 1009, 2027]`, and `replication._seed_members`' rule is `f"seed{s % 100:02d}"`
   with the full-value form used **only** as a collision fallback.
   **Reproduce:** `uv run python -c "print([f'seed{s % 100:02d}' for s in [17,42,137,1009,2027]])"` →
   `['seed17', 'seed42', 'seed37', 'seed09', 'seed27']` — all five distinct, so the fallback never
   fires and **three of the five documented labels are unreachable.** Three homes, all `reference.md`
   (`:905`, `:923`, and § Before you spend it's transcript); `README.md` shows only `seed17`/`seed42`,
   both reachable. **Found while deriving the transcript** — a real `dry-run` printed `seed01`,
   `seed96`, `seed06`, `seed78`, `seed39`, every one two digits. The transcript H9a landed uses the
   documents' own labels, so this filing is the only place the disagreement is recorded rather than
   propagated. **Owner: unassigned, with the reason** — no remaining slice has `replication.py`'s label
   rule or that worked example as its surface, and the fix is a choice between two documents' numbers
   with a shipped path component inside it.
2. **Correction 22's residue, at its measured size.** **Reproduce:**
   `grep -rn "command_run" src/ tests/ | wc -l` → **195**, across 22 files
   (`grep -rc … | grep -v ':0$'`), **101 in `tests/` against `src/`'s 94**. The plan's *"roughly
   forty-five"* was a lower bound over a narrower pattern.
   **The signpost check the dispatch asked for, done rather than assumed:** a reader who greps
   `command_run` in `cli.py` lands **inside** `command_run`, whose docstring carries the phase split —
   the signpost works for those 34 hits. A reader who greps `reference.md` lands on § Errors core
   raises' *"since H9a, in `cli._prepare_run`, which `command_run` calls"* — it works there too, and
   `reference.md` now has exactly that **one** `command_run` mention, on purpose. **A reader who greps
   `tests/` — the majority — lands on neither**, and that is what is filed. **Owner: unassigned, with
   the reason**, and the entry notes H9b and H9c will each add a *third and fourth* caller of
   `_prepare_run`, so the residue grows rather than shrinks.

**Not touched:** the H7d Part B `max_failed_fraction` filing.

**`CLAUDE.md`** gains H9a's paragraph in the established form — what it built, **retires nothing**,
**unblocks zero configs with the structural reason**, four things worth carrying (Ruling R's
document-is-wrong argument and the run-verified 20; the blind Fixture Y mutation; the fifteen narrow
§ Errors rows; the amended sweep that itself under-counted), pointing at § Executability's table rather
than restating it. The order line now reads **H9b, H9c, H9d, then H3c-3's remaining 14**. The
`Prepared` field count quoted in it (**thirty-six**) was checked with
`len(dataclasses.fields(Prepared))` → 36, not read off the docstring.

---

## Task 14 — both passes, and § Executability re-derived

### Mechanical pass

One throwaway script over the seven `*.md` files the passes govern: `README.md`,
`docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`,
`docs/feasibility-llm-growth-studies.md`, `CLAUDE.md`, `docs/superpowers/spec-defects.md`. **The
development record is exempt and was not run through it and not retro-edited.** Checks: every relative
link and `#anchor` resolves (including cross-file `file.md#frag`), no two headings in a file produce
the same anchor, every table row matches its header's column count, no all-blank table row, no trailing
whitespace, no tab, no invisible unicode. **Fenced blocks skipped.**

**Result: `--- 0 problems over 7 files`.**

**The first run printed 11, and all 11 were the checker's own bugs** — which is why *prove the checker
can fail* comes before trusting it:

- it stripped `_` along with `*` as markdown emphasis, where GitHub's slugger **keeps** `_`, so two
  live headings (`…derive_seed is where it comes from`, `` `reuse_from` addresses an artifact…``) made
  **7** real links read as dead;
- it split table cells on `|` without honouring `\|`, so **4** rows carrying escaped pipes inside cells
  (`sobol \| latin_hypercube \| random`, and `CLAUDE.md`'s own enum-comment row) read as column
  mismatches.

**Can-fail proof, run after the fixes**, on a purpose-built bad file with a fenced block at the end —
all seven classes fire and the fenced content is correctly ignored:

```
bad.md: DUPLICATE ANCHOR #dup at lines [3, 5]
bad.md:7: TRAILING WHITESPACE
bad.md:9: TAB
bad.md:11: INVISIBLE U+200B
bad.md:15: TABLE COLS 1 != header 2
bad.md:16: EMPTY TABLE ROW
bad.md:18: DEAD ANCHOR #nope
bad.md:20: DEAD LINK ./no-such.md
bad.md:22: DEAD CROSS-ANCHOR ./other.md#nope
```

### Cross-document pass, over the four documents

| Class | How it was checked | Result |
|---|---|---|
| **The shared worked example** | `grep -n "64 artifact\|artifacts under"` over the four named → **0**; `grep -n "step directories"` → 5 lines, one carrying the figure `20`; can-fail control `grep -c cohort-pilot` → 15 / 6 / 0 / 23 (the 0 is `experimental-designs.md`, which uses varied domain examples by design) | **20 has one home and no contradicting one.** § What `demo` walks you through's stop-4 row states no count, so it does not contradict. The `r`/interval literals are untouched |
| **Config completeness** | branch diff of `reference.md` filtered to added/removed config-field lines (`^[-+]\s{2,}[a-z_]+:`) → **empty**, against a 387-line control | No field added or removed |
| **Enum comments** | branch diff filtered to `# a \| b \| c`-shaped comments → **empty**; 21 such comments exist in `reference.md` | None moved |
| **`apparatus.PHASES` vs § The apparatus files** | `PHASES` → `['dry_run','freeze','pre_execution','run_start']` (4); § The apparatus core can only observe names four places; § The apparatus files names three ledger phases **plus** the reserved-name paragraph; *"the four places a probe runs"* has 2 homes, both consistent | Consistent |
| **Declared vs derived** | nothing in the branch diff turns a derived value into an input | Unchanged |
| **Versions** | `CITATION.cff` `version: 0.1.0` vs `reference.md`'s `publishable_version: "0.1.0"` | Agree |
| **Prevented mistakes** | the one `experimental-designs.md` § Mistakes core prevents row this slice edited still describes a structurally-prevented mistake (the gate fails the run) | Holds |
| **The `Status` column** (moved twice by this slice) | `NOT_BUILT_COMMANDS` → `{demo, docs, list-templates, reproduce, resume}` (5); `reference.md`'s § CLI reference `NOT BUILT` rows → the same 5; `OPERATION_COMMANDS` → `{draft, dry-run, freeze, report, run, validate}` (6) | Exact agreement |
| **House style** | added heading lines containing an en dash → **0** (can-fail: the grep finds 9 en dashes in the feasibility analysis and 7 in `CLAUDE.md`, both prose, both allowed); added lines using ASCII `x` between digits → **0** | Clean |

### § Executability — re-derived, and the table byte-identical

One entry, *"Measured on 2026-08-23 against commit `c925416` — after H9a"*, which is also the branch's
last commit touching `src/` or `tests/` (`git log -1 --format=%h -- src tests` → `c925416`), so the sha
names the tree the figures were derived against.

**H9a is NOT additive and the entry says so before deriving anything**, then checks the design's four
enumerated behaviour changes against the nine configs **one at a time**: two shipped invocations'
exit code and output, `NOT_BUILT_COMMANDS`/`OPERATION_COMMANDS` losing and gaining keys, the two-token
arm's answer for `publishable draft new`, and the extraction. **None reads a `data` or `statistics`
block**, which is what a row of this table is derived from.

Row by row, measured rather than repeated:

- **Row 1 (8 of 8 validating with zero errors)** — three measurements: `git diff --name-only
  main...HEAD -- src` prints **two** files (`apparatus.py`, `cli.py`), so `validate.py`, `units.py`,
  `sweep.py`, `stats.py` and `correction.py` are untouched; `apparatus.py`'s whole diff is **three
  docstring paragraphs and zero statements**; and `cli.command_validate`'s source segment is
  **byte-identical** between `main` and the tip — 261 characters, compared with
  `ast.get_source_segment` on both sides rather than read off the diff's hunk headers, which name it
  only as the enclosing context of an insertion below it.
- **Row 2 (0, `io.reuse_from`)** — a step-level call; this slice adds no reader of a run directory, and
  `_prepare_run` carries the same `UpstreamLedger`/`UpstreamResolver` in the same statement order.
- **Row 3 (7, the `report_by`-under-`resample` gap)** — chosen inside `stats.summarize_step`, reached
  from **phase 8 inside `_execute_prepared`**, which `dry-run` never enters and which `draft` enters
  identically to `run`. `stats.py` is not in the two-file diff.
- **Row 4 (1, free of every core-side dependency)** — `draft`'s precondition is a **dirty working
  tree**, a property of the operator's checkout and not of a config; `dry-run`'s probe round is
  unexercised because `GenericTemplate.apparatus_probe` **is `None`** (read at this commit, beside
  `apparatus_facts == []`), so `_dry_run_probe` returns at its first guard for all nine. Named
  explicitly because it cuts the other way: `draft` **does** give E4 and C3 a route past the dirty-tree
  obstacle § Three repositories records — but that was never one of the core-side dependencies row 4
  counts, so the row does not move.

**H9a unblocks ZERO configs**, and the reason is structural: both commands are second entries into a
sequence these configs already reach or do not.

**The four-row table is byte-identical and extracted, never retyped.** The preceding (H6b) entry's
table was extracted **two independent ways** — `sed -n '1946,1951p'` and a programmatic walk finding
the last `| Figure | Count | Visible to` header and reading forward while the line starts with `|` —
and `diff`-ed: **empty**, six lines each. The pasted block was then `difflib`-compared against the
preceding one in the finished file: **`BYTE-IDENTICAL: True`, 6 lines each.** Each cell still names
**H8a** in its own prose, because that is what character for character means. **No fifth number is
minted and no ordinal is asserted** — the entry says so and derives nothing from a count of previous
entries.

**Three live claims corrected, none of them inside a dated entry, each by deleting the undated build
claim rather than restating it**: `draft` *"does not dispatch in this build"* (§ Three repositories, and
what decides the seams), `resume` *"prints **the same** specified but not built diagnostic"* (same
table — and its *"the same"* referent was the first, so removing one and leaving the other would have
left a dangling comparison), and — Ruling R's third home, and a **specification** claim rather than a
build one — `dry-run` printing *"where every artifact will land"* (§ Cost and execution summary), now
step directories and fixed files with the omission named, since `reference.md` no longer promises the
artifact files. `grep -c "where every artifact will land\|does not dispatch in this build"` → **0**.

---

## Concerns

1. **A Minor against the plan, not against the code: § Task 12's amended sweep count is one short.**
   `would write` has four homes and the amendment says three; the missed one is `:368`, a line the
   fix round's own report quotes. Recorded here rather than by retro-editing the plan. Nothing built on
   the wrong number, because the sweep was re-run before any edit.
2. **A fourth edit class in task 12, disclosed rather than folded in.** Fifteen § Errors / § Warnings
   rows were widened. I judged this in scope because the narrowing is this slice's own doing and a
   normative row narrower than its code is the Major shape this family keeps finding — but it is more
   than the brief's three edits and a reviewer should check the widenings for over-claiming. Each is
   listed above with the phrase it replaced.
3. **`E-APPARATUS-CHANGED` has no `dry-run` clause, deliberately.** `dry-run` does not call
   `check_changed` (Decision 6's measured ground), so it is not an emit site and I added nothing. A
   reader who wonders *why* `dry-run` does not gate finds the answer in `_dry_run_probe`'s docstring
   and in Decision 7's struck filing — **not** in the § Errors row. If the gate should say so, that is
   a row edit I chose not to invent.
4. **The seed-label filing touches the shared worked example and I did not fix it.** Three of five
   documented labels are unreachable from the documented seeds. The § Before you spend it transcript
   H9a landed uses the documents' labels, which keeps the example self-consistent and leaves the
   code-vs-document disagreement in one filing rather than in the transcript. If the reviewer prefers
   the transcript show reachable labels, that changes the worked example and needs a ruling.
5. **The mechanical checker is a throwaway and is not in the repo** (this repo ships no such tooling by
   rule). Its two bugs are recorded above so the next person writing one does not repeat them:
   **keep `_` in slugs, and split table cells on unescaped `|` only.**
6. **Fixture X's prescribed mutation is not constructible** and the substitute is a six-line
   alternative implementation rather than a one-line edit. Reported as blind with the reason rather
   than reported as passed; the design's own precedent for that shape is its two mutations *"named
   blind in advance."*
