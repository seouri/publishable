# H5a batch 5 (tasks 5–6) — review

Commits reviewed: `828f42b` (task 5), `cf3789c` (task 6), `d0ff8d2` (report), diffed against
`87affb6`.

Gates re-run here, foreground, caches cleared: `ruff check` clean, `ruff format --check` 93 files
already formatted, `mypy` clean on 52 source files, `uv run pytest` **2875 passed, 1 skipped,
2 xfailed** — the count the dispatch expected. Tree left clean (`git status --porcelain` empty);
every mutation was reverted by restoring a pre-mutation copy and re-running the affected tests, no
`git checkout --` anywhere.

## Verdicts

- **Spec compliance: PASS, with two Majors to close before this branch merges.** Decisions 3, 4 and
  6 are built as written, correction 1 is honoured in the direction the second controller ruling
  demanded, and controller requirement 3's ordering pin is real — I made its directory assertion
  fire under a constructed mutation the exit code cannot catch. Both `E-RESOLVER-YIELD` rows cover
  both emit sites, and the document's past-tense claim about what ran before is true, verified by a
  real run. Neither Major is a defect in shipped behaviour; both are pins that do not pin — the
  enforcement obligation the batch-4 ledger routed to Fixture R **by name** is not discharged, and
  Fixture A's message assertion is satisfied by its own error message's enumeration.
- **Task quality: PASS.** Two mutations I re-ran reproduce exactly as reported, and the batch is
  better than its brief in two places: it disclosed a broader mutation (iv) rather than narrowing it
  to the brief's wording, and it split the two `by`-survival arms so each uniquely catches a
  different guard — a separation the brief did not ask for and the report understates. The
  deductions are the two Majors above and **three brief clauses dropped without disclosure**
  (Minors 1–3), two of which are assertions the brief named explicitly. Three undisclosed drops in
  one batch is the pattern worth naming: each is individually small, and the report's Concerns
  section discloses two nuances while carrying none of these.

---

## Findings

### Major 1 — Fixture R does not close correction 6's enforcement gap; the report says it does

**File:** `tests/test_units.py:4089` (`test_a_resolver_yielding_a_numpy_scalar_attribute_coerces_to_exact_python_float`),
`tests/test_cli.py:12075` (`_YIELDS_TEN_WITH_A_NUMPY_SCALAR_ATTRIBUTE`);
report § *Confirming Fixture R closes correction 6's enforcement gap*.

The batch-4 ledger (`progress.md:176`) states the obligation precisely: *"correction 6's ordering
rule is enforced only at the shared function — displacing the branch fails five tests, but **nothing
pins the resolver surface** … Task 6's Fixture R inherits an enforcement obligation."* Correction 6's
ordering rule is specifically about **`np.str_`**: task 10's `str`-by-inheritance branch must land
before task 6, or a resolver yielding an `np.str_` attribute — which works today — starts refusing.
`coercion.py:216`'s own comment says the same and hands the remaining gap to *"the coercion call
site's own job, once one exists."* Task 6 is that call site.

**Verified by running.** I deleted the `isinstance(value, str) → str.__str__(value)` branch from
`coercion._coerce_one` — the exact displacement correction 6 forbids — and ran the full suite:
**6 failures, none of them at the resolver surface.** Five are `tests/test_coercion.py` (the shared
function, already enforced before this batch) and one is
`tests/test_apparatus.py::test_an_np_str_fact_value_resolves_instead_of_being_refused` (task 10's own
retirement pin at a different call site). Every new resolver fixture in this batch uses `np.float64`,
which reaches the coercion through the `item()` unwrap and never touches the `str` branch;
`grep -rn 'np.str_' tests/` shows no resolver-surface use at all.

The report's narrower claim — that the control *"would fail if `units.py`'s coercion call site were
ever removed or reverted"* — is true (mutation (i) confirms it, and I reproduced that). But that is
not the gap the ledger named, and the section heading asserts the gap is closed. This is the
project's recorded shape *a carried finding is in the brief, measured, named — and still not built,
while the report claims it was*.

**Fix is one line:** add `np.str_("north")` as a second attribute to Fixture R's positive-control
resolver and assert `type(...) is str`.

### Major 2 — Fixture A's "the message names the offending attribute" assertion is vacuous

**File:** `tests/test_units.py:202` (`assert reserved in str(e.value)`), `tests/test_units.py:259`,
`tests/test_units.py:271`, `tests/test_validate.py:4802` (`assert reserved in message`);
message built at `src/publishable/units.py:248`, `:281`, `:467`.

The message interpolates the offender **and** `', '.join(RESERVED_COLUMNS)` — literally
`"unit, measurement, by"` — into one string. So `reserved in str(e.value)` is satisfied by the
enumeration regardless of which name the refusal actually reports. This is CLAUDE.md § Writing
checks that can fail's *an assertion satisfied by neighbouring output*, and it is what the decoy
apparatus was built to make load-bearing: task 5 brief step 5 requires each arm to assert
`E-UNITS-ATTR-COLUMN` **and** that the message names the offending attribute.

**Verified by running.** I replaced `{name!r}` / `{attribute!r}` with a hard-coded `'aaa_site'` (a
decoy) at all three emit sites, so every refusal names a name that is not the offender. **All 14
Fixture A arms across `test_units.py` and `test_validate.py` still passed.** The code assertions are
sound; the message half pins nothing, and with it the decoys buy nothing they were meant to buy.

**Fix:** assert the offender's own clause — `f"names {reserved!r}"` — rather than the bare name.

### Minor 1 — arm O1 drops the brief's `E-RESOLVER-YIELD` assertion, undisclosed

**File:** `tests/test_cli.py:12088` (`test_arm_o1_a_structural_resolved_attribute_pays_for_nothing_before_it_refuses`).

Task 6 brief step 6 says of arm O1: *"Assert the diagnostic names `E-RESOLVER-YIELD`, **and** that
`output_dir` holds no `run_*` directory at all."* The shipped test takes no `capsys` and asserts only
`run_dir is None`, the `run_*` glob, and the two `latest` pointers — **no assertion about the
diagnostic's identifier anywhere.** Verified by reading the whole test body: neither `capsys` nor
`E-RESOLVER-YIELD` appears in it. Not disclosed in the report's Concerns.

Consequence: O1 passes if the roster refuses under *any* code that lands before directory creation,
and O2 attributes the refusal to the fixture's shape rather than to the identifier. The batch knew
the pattern — task 5's `test_a_reserved_column_name_meets_the_same_refusal_at_run`
(`tests/test_validate.py:4827`) takes `capsys` and asserts its code in stdout, twelve hours earlier
in the same branch. Held at Minor because `tests/test_units.py:4049` pins the code at the direct-call
surface, so the identifier is not unpinned outright — only unpinned at the `run` surface this arm
exists for.

### Minor 2 — brief step 6(a)'s second clause was dropped, and the report's grep claim describes a citation that does not exist

**File:** `tests/test_artifacts.py:663` (`test_a_plain_recorded_by_column_survives_into_units_parquet`);
report § *Zero-disagreements check*.

Step 6(a) asks the plain arm to show the recorded `by` column reaching `units.parquet` *"(and, at
`run`, draws `W-STATS-STRATUM-SHADOWED`, which is already shipped — grep before claiming anything
about it)"*. The shipped arm builds a bare `StepIO` and asserts nothing about the warning; the
omission is not disclosed. The report says it *"grepped … `W-STATS-STRATUM-SHADOWED` confirmed it is
already shipped before citing it in a docstring"* — `git diff 87affb6..HEAD -- tests/ | grep -c
W-STATS-STRATUM-SHADOWED` returns **0**, so no new docstring cites it and the grep guarded nothing.

Load-bearing half is fine and the missing half is covered elsewhere: I ran
`tests/test_cli.py::test_a_recorded_column_named_by_keeps_its_metric_and_warns` (pre-existing,
`test_cli.py:6903`) — a real `run` recording `by`, asserting the warning and the metric's own value
and interval. So "a step recording `by` stays legal" **is** pinned end to end; it is just not pinned
by this batch.

### Minor 3 — arm O1's `run_dir is None` assertion is subsumed and reads stronger than it is

**File:** `tests/test_cli.py:12116`.

`run_a_project` returns `run_dir: None` both when no `run_*` directory exists **and** when one exists
without `executions.jsonl` (`tests/test_cli.py:273`, the H7d correction-3 branch). So `assert
o1["run_dir"] is None` passes in a world where a run directory was created and every environment and
manifest artifact written. The glob assertion two lines below is the one doing the work, and its
docstring is correct about that. Cosmetic, but a reader grepping for the pin could stop at the wrong
line.

---

## Adjudications the dispatch asked for

**Attack 1 — `RESERVED_COLUMNS` has exactly one reader, and a legally recorded `by` survives both
`record` branches. Confirmed.** Counted myself: `grep -rn 'RESERVED_COLUMNS' src/ tests/` gives one
definition (`units.py:33`) and three call sites (`units.py:246`, `:279`, `:465`) — the same
attribute-name check under the three sources, and nothing else in `src/`. `artifacts.py`'s three
literals are byte-untouched (`:645`/`:651`, `:753`, `:794`). Both survival arms pass at baseline, and
I ran each of the two dangerous re-points separately:

- `finalize`'s `key != "unit"` → `("unit","measurement","by")`: **both** arms fail, each on the
  column's absence from the read-back parquet (`{'unit': 'p1', 'score': 10}` vs the expected row).
- `_collapse_measurements`' `("unit","measurement")` → same tuple plus `by`: **only arm (b)** fails,
  same assertion.

So the two arms are not redundant — one uniquely catches `finalize`, the other uniquely catches the
collapse. That is better than the brief specified and better than the report claims.

**Attack 2 — one producer removed, not the possibility. Both halves verified by running.** The
refusal fires for a declared attribute named `by` at `resolve_units`, at `validate_config`, and at a
real `run` (three shipped arms, all green). A step recording `by` stays legal — verified through the
pre-existing end-to-end run above, and through both new `units.parquet` arms. The reasoning survives
into the code: `units.py:33-55`'s docstring names the three sites it must not be pointed at, names
correction 1 and Decision 4, and closes with *"is not license to identify a stratum by the name `by`
anywhere … this comment is what stops it being relearned here."* **Nothing reintroduces a name
test**: `git diff 87affb6..HEAD -- src/ | grep '"by"'` returns the constant definition and nothing
else.

**Attacks 3 and 4 — the ordering pin is real; mutation (i) merely fails for a neighbouring reason.**
Reproduced the report's disclosure exactly: with the coercion removed, O1 dies at
`run_a_project`'s own `assert main(...) == expect_exit` (`assert 0 == 1`), with captured stdout
showing `run.yaml → …/run_2026-08-22T06-39-52Z_436cab2/run.yaml`. The report is honest about this.

The question that decides it is whether the directory assertion can fire at all. **It can, and I made
it.** I removed the coercion and relocated an equivalent structural-attribute refusal to immediately
after `allocate_run_dir` (`cli.py:2329`), returning `EXIT_WRONG` — the shape a later slice would
produce by moving the check to any of the three post-allocation `EXIT_WRONG` returns
(`cli.py:2446`, `:2548`, `:2590`). The helper's exit-code check **passed**, and O1 failed on
`assert next(output_dir.glob("run_*"), None) is None` with the real run directory in the message.
So the helper's check does not mask the property: it catches a *stronger* mutation first, and the
directory assertion is the only thing standing between a relocated refusal and a paid-for run.
**Not a finding.** O2 was verified as a genuine positive control: it passes at baseline and its
`type is float` sibling in `test_units.py` is what fails under mutation (i).

**Attack 6 — `E-RESOLVER-YIELD`'s row scope. Covered.** `grep -rn 'E-RESOLVER-YIELD' src/` gives
exactly two raise sites: `units.py:404` (`_from_resolver`'s non-`Unit` yield) and `units.py:715`
(the re-code at the end of `resolve_units`). Both rows — § Errors `validate` reports
(`reference.md:37` of the diff) and § Errors core raises (`:68`) — now name both shapes and say
where each is raised, including that the second runs over every source while only a resolver can
produce it. No third site, no row narrower than its code.

**Attack 7 — both disclosed nuances verified, neither is catching something else.** Mutation (iv)'s
breadth is explained by `artifacts.py:794`: `finalize` builds `recorded` by one walk over
`self._rows`, into which `_collapse_measurements` also writes, so one filter covers both branches. I
read both failure texts — both are the column's absence from the read-back parquet, the property the
brief names. O1's earlier failure point is adjudicated above.

**Attack 8 — the guard pin. None fired, and none was touched.** `git diff 87affb6..HEAD --
tests/test_artifacts.py` has a single hunk at `@@ -652,6 +652,51 @@`; the guard-pin arms live at
`test_artifacts.py:2439+` (arms B1/B2) and `:2520+` (arms E1/E2) and `test_cli.py:16778+` (arms A/C/D)
— all byte-unmodified. Ran them explicitly: 21 passed. Arm E1 (`.parquet`, no authorized editor) and
arm E2 (`.csv`, task 9's) are intact, and the split's rationale at `test_artifacts.py:2528-2536` still
matches.

## Also checked, not asked for

- **The document's past-tense claim, which is the class of error batch 4's Major was.** § Where units
  come from now says *"Before this, a resolver-yielded list or mapping attribute value wrote a list or
  mapping column straight into `units.parquet`."* **Verified by running**: with the coercion removed,
  a real `run` against a resolver yielding `{"tags": [1, 2]}` produced
  `[{'unit': 'p1', 'tags': [1, 2], 'present': True}, …]` in `units.parquet`. The claim is true, and it
  is the one this batch could most easily have got wrong.
- **Mechanical pass over the four documents** (links, `#anchor` resolution, duplicate anchors, table
  column counts, trailing whitespace, tabs, invisible unicode), fences skipped. Clean — the four
  anchor "misses" and three column-count "misses" my script reported are its own false positives
  (em dashes in headings; escaped `\|` inside cells), each checked by hand.
- **`E-UNITS-ATTR-COLUMN`'s three emit sites** all carry the identical message and the same
  `UNIT_FIELDS` → `RESERVED_COLUMNS` → unsourced order, as brief step 3 requires.

## What I could not check

- **Whether the full *every execution paid for, the record lost* shape is observable.** It is not, on
  this branch: task 9 has not landed, so mutation (i)'s run completes rather than raising inside
  `finalize`. The report says so, and the plan's appended note charters task 11 to re-run the mutation
  on the finished branch. I confirmed the charter exists in the plan; I could not confirm the shape
  itself.
- **Whether `coerce_scalars` over roster attributes can refuse anything a *table* source produces.** I
  reasoned it cannot (`csv.DictReader` gives `str`; `apply_rule`'s numeric rules give `float`; `mode`
  and `first` pass a cell through) and the full suite agrees, but I did not enumerate every
  `collapse` rule's return type against every input shape.
- **`Unit` object identity.** The documented cost (a resolver's own yielded object is replaced) is
  stated in both the code and § Where units come from; I did not look for a consumer that relies on
  identity rather than `key`, beyond the suite being green.
