# Task 25–26 review — resolver dispatch and the retirement of `E-DATA-RESOLVER-UNSUPPORTED`

Reviewed `54a994f..4c09532` (commits `c563d30`, `519c090`) against
`docs/superpowers/specs/2026-08-17-resolvers-design.md` and its appended corrections, the two task
briefs, and the ledger's four inherited obligations.

**Gates, re-run in the foreground at `4c09532`:** `uv run pytest` → **2077 passed, 1 skipped, 2
xfailed** (107s), `ruff check` clean, `ruff format --check` → 80 files already formatted, `mypy` →
no issues in 45 source files. The report's arithmetic is the honest one; the briefs' numbers were
stale, as disclosed.

## Verdicts

| Task | Axis | Verdict |
|---|---|---|
| 25 | Build | **PASS with findings** — dispatch is correct, order-preserving, acyclic; one garbled user-facing message and one missing § Errors row |
| 25 | Pinning | **PASS** — every new test discriminates; three mutations each redden exactly one test |
| 26 | Build | **PASS** — the retirement is complete and behaviourally pinned |
| 26 | Pinning | **FAIL** — two of the four inherited obligations unmet, the slice's central invariant still half-pinned, and one guard's sole coverage dropped |

---

## Does anything surviving pin resolver → roster → run → `run.yaml`?

**No.** Nothing in the suite exercises a resolver source through `main(["run", ...])`.

**The report's claim is true, and I reproduced it.** A throwaway test (written, run, deleted;
tree verified clean afterwards) built an installed distribution registering `plate_wells` under
`publishable.resolvers`, pointed `data.units.from` at it through `tests/test_cli.py`'s
`run_a_project` helper, and ran `main(["run", ...])`:

```
run.yaml → .../results/run_2026-08-17T12-33-31Z_436cab2/run.yaml
STATUS: completed
PROV UNITS: {'n': 10, 'key': 'patient_id'}
```

Exit `EXIT_OK`, one warning (`W-ENV-UNLOCKED`, incidental to the fixture), `status: "completed"`,
and the roster resolved through the plugin's `Unit`-yielding generator. The milestone is real.

**But it is pinned by nothing that survives.** This is a deferral the spec makes explicitly — its
corrections' final paragraph: *"tasks 25, 27, 28 and 29 cannot test through `validate_config` at
their own commits ... each tests its own function directly and task 33 re-asserts end to end."*
Task 33 owns it. Recorded here so the obligation is not lost: **task 33 must add an end-to-end
resolver run**, and it is the only place the first executable path in the project's history gets a
regression.

---

## Findings

### Critical

**C1 (task 26) — obligations (b) and (c) unmet: the narrowed no-import invariant is still pinned
half, and the docstring that says so is now false in every clause.**

The ledger records this twice, in capitals: *"**Task 26 owes `assert "retire_r26" in
sys.modules`.**"* The report discloses it was not added, and judged the behavioural proof
sufficient. **That judgment is wrong, and I disproved it by mutation.**

Verified by two mutations, run in both directions as the review brief asks:

- **Negative half (unconditional load at the `validate` level).** Added a `for _n in
  scan_group(RESOLVER_GROUP): _resolver_for(_n)` loop at the top of `_check_units_source`.
  `test_validate_imports_no_plugin_for_a_config_that_names_no_resolver` **FAILED** on
  `assert "loadable_units" not in sys.modules`; the retirement test stayed green. This half works.
- **Positive half (inverse: resolve the name, never import).** In `units._resolver_for`, replaced
  `load_entry_point(ep)` / `check_registration(...)` with a fabricated generator yielding
  `Unit(key="p1")`, leaving the `scan_group` name check intact so `E-RESOLVER-UNKNOWN` still fires.
  **All 706 tests in `tests/test_validate.py` passed.** Only `tests/test_units.py` reddened (6
  tests, task 24's and 25's).

So a `validate` that resolves a resolver name from metadata, never imports the plugin, and
fabricates a roster out of thin air is **indistinguishable to the entire validate-level suite**.
Decision 1 — the slice's central decision, *"Yes, `validate` imports a plugin when it runs a
resolver"* — survives at `units.resolve_units` and nowhere at the level the invariant is stated.

Compounding it, and this is obligation (c): `tests/test_validate.py:160-167` still reads

> *"Its positive companion does not exist yet. `_resolver_for` (task 24) has no production caller
> today, so `validate` does not load a resolver for any config — task 26 is where that wiring
> lands, and task 26 owes a test asserting the module IS present for a config that names one (the
> concrete form recorded in the review: `assert "retire_r26" in sys.modules`). Until that lands,
> this test alone would also pass on a `validate` that has no resolver path at all."*

Every factual clause is false at this commit except the last, which is the one the reader is least
likely to act on. `_resolver_for` has a production caller (`units._from_resolver`), `validate` does
load a resolver, and task 26 has landed. This is the *"docstring claiming a guarantee the code does
not provide"* trap with the sign flipped — a docstring claiming a **limit** that no longer exists,
in the file the task edited, and it points a future reader at a task that is closed. Part A shipped
a Critical of exactly this shape in the other direction, which is why the ledger chose the
restore-then-reverse pattern in the first place.

*Fix:* add `assert "retire_r26" in sys.modules` inside
`test_a_resolver_source_is_no_longer_refused_wholesale`'s existing `try`, and rewrite lines 160-167
to state the invariant in the present tense — or delete them, per *prefer deleting a claim to
rewriting it*.

### Important

**I1 (task 25) — `E-UNITS-SOURCE-MISSING`'s widened message renders garbled `{{resolver: ...}}`.**

The clause task 25 was assigned to widen is appended as a **non-f-string** continuation, so its
escaped braces are never unescaped:

```python
f"`data.units.from` is {source!r}; expected a table name, {{glob: ...}}, or "
"{{resolver: ...}}",          # ← not an f-string; braces stay doubled
```

Verified directly:

```
>>> resolve_units({'from': 42, 'key': 'k'}, Path('/tmp'))
'`data.units.from` is 42; expected a table name, {glob: ...}, or {{resolver: ...}}'
```

`{glob: ...}` renders correctly and `{{resolver: ...}}` does not, in one sentence. `docs/reference.md`
line 601 — task 25's own edit — shows the correct form (*"or a `{resolver: ...}` mapping"*), so the
code and the document disagree about the string a user reads. **No test reads this message text**
(`tests/test_units.py:134` asserts the code only), which is why it shipped. Not Minor: this is the
one clause the task existed to widen.

*Fix:* make the continuation an f-string, or single-brace it in the plain string.

**I2 (task 25) — `E-RESOLVER-YIELD` and `E-RUN-RESOLVER-UNCONFIGURED` have emit sites and tests but
no § Errors row, and no stated reason they need none.**

Verified by grep across `src/`, `tests/`, `docs/reference.md`: both codes appear only in
`src/publishable/units.py` and `tests/test_units.py`. The spec's correction 2 mints three codes
"each with an emit site and a test", and task 25's brief is more specific still — that
`E-RUN-RESOLVER-UNCONFIGURED` *"joins § Errors core raises' existing **core's plan disagreeing with
the state core resolved beside it** row."* That row is `docs/reference.md:1050`; the diff does not
touch it. `E-RESOLVER-YIELD` has no row anywhere.

CLAUDE.md's invariant is that **§ Errors carries one row per code**, and reference.md:420-425
exempts only `-UNSUPPORTED` codes from the registry — neither of these is one. The report does not
mention the omission, so it is **unowned as of this commit** rather than deferred to task 33.
(`E-RESOLVER-RAISED`, the third minted code, is task 32's and correctly absent.)

**I3 (task 26) — the seventh deletion dropped the sole pin on `_units_declaration`'s
`E-CONFIG-SHAPE` emit, and the docstring was then rewritten to justify a guard nothing exercises.**

Judgment on the deletion of
`test_check_unimplemented_alone_does_not_raise_on_a_malformed_units_block`:

**The stated premise is true.** `_check_unimplemented` genuinely no longer reads `data.units` —
verified by reading the whole function body and grepping it for `_units_declaration`, `doc.get`,
and `"units"`: zero hits. As a test *of `_check_unimplemented`*, it was moot, and deleting rather
than rewriting was the right instinct.

**But it was doing double duty, and the other duty is now uncovered.** Mutation: deleted the entire
`c.error("E-CONFIG-SHAPE", "data.units", ...)` emit inside `_units_declaration`, reducing the
non-mapping branch to a bare `return None`. **`uv run pytest` → 2077 passed, 1 skipped, 2 xfailed.**
The whole guard can be gutted with the suite green. That test was its only pin.

Worse, task 26 **rewrote** the docstring justifying the guard:

> *"This guard exists for those readers being exercised directly (as several `_check_*` functions
> already are in tests), so none crashes on a non-mapping `data.units` reached on its own."*

`_units_declaration` has four surviving callers (`validate.py:654`, `:1201`, `:1280`, `:4945`), and
a grep of `tests/test_validate.py` for direct calls to any of them returns **nothing**. The
docstring's justification names a use no test makes — a rewrite inventing a claim a deletion could
not have. This is *"prefer deleting a claim to rewriting it"* and *"a mutation's silence is evidence
about the tests"* in one place.

*Fix:* re-site the direct-call test onto a surviving reader — `_check_units_source` is
direct-callable and takes exactly `(doc, c)` — rather than restoring the old test.

**I4 (task 25) — `_from_resolver`'s docstring claims a check that does not exist.**

Paragraph 1, authored by task 25:

> *"they are the only honest reference set for `data.units.measurements.by` ... so the field a CSV
> would simply have carried **is checked against what actually arrived**."*

Probed: a resolver-sourced config declaring `measurements: {by: "nosuchfield", collapse: {x: mean}}`
against a resolver yielding only a `cohort` attribute. `validate` reported **`{}`** — no findings at
all. The config validates clean with `measurements.by` naming a field no unit carries.

That check is `E-RESOLVER-MEASUREMENT-FIELD`, task 28's, and `docs/reference.md`'s own row for it —
corrected by task 26 in this very diff — now reads *"a resolver-produced roster exists, but this
check against it does not."* So the two artifacts of one commit disagree: reference.md marks the
check unemitted while the docstring describes it in the present tense. The columns are returned
*so that* task 28 can make the check; the docstring states the consequence as though it already had.

*Fix:* the honest edit is the future tense or a deletion — the paragraph's real content (why the
columns come back beside the roster) survives without the "is checked" clause.

### Minor

**M1 (task 25) — `ResolverIO(input_dir)` is constructed unconditionally in `command_run`
(`cli.py:1314`), one line above the `if units_decl` guard that decides whether it is used.**
Harmless — construction is `__slots__`-only and touches no filesystem — but it puts an object into
a run with no units block that nothing reads. Task 31 reads `read_paths` off it, so leave it if
that task needs the object unconditionally; otherwise move it inside the branch.

**M2 (tasks 25/26) — nothing pins that the `cfg` threaded to a resolver is the *right* `cfg`.**
Both production call sites do thread it (`validate.py:1350`, `cli.py:1316`), and each is built from
`resolve_wide_cfg(doc, wide_swept_paths(...))` as the brief prescribes. But every resolver fixture
in the suite ignores its `cfg` argument entirely, so replacing the threaded expression with
`Config({})` at either site would go unnoticed. Task 29 (`E-RESOLVER-SWEPT-PARAM`) is where a
fixture that reads `cfg` first becomes necessary; recorded so it is not assumed already covered.

---

## Checks that came back clean

**Obligation (a) — the restore-then-reverse: done, and widened correctly.** `E-RESOLVER-UNKNOWN`'s
*"Not yet emitted"* clause is gone; the *"Not yet reached at `validate`"* qualifiers on
`E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD` are gone and both rows now state the present tense
correctly; the § Errors preamble's own repetition of the claim (reference.md:441-445) is gone — the
third site the report found, which shared no wording with the two rows and would have been the
"grep for one spelling" trap. Two further rows (`E-RESOLVER-MEASUREMENT-FIELD`,
`E-RESOLVER-SWEPT-PARAM`) had their false factual clauses corrected while keeping their **Not yet
emitted** markers, which is the right call — except that one of them now contradicts I4's docstring.

**Obligation (d) — one-line deletions, six of six.** Read each of the six named tests in the diff:
every change removes exactly the line, parametrize case, or whole test naming
`E-DATA-RESOLVER-UNSUPPORTED`. No assertion was rewritten. Two carried docstring corrections
alongside, correctly. The seventh deletion is I3.

**The retirement is behaviourally pinned.** Mutation: restored `_check_units`'s early return for a
resolver source. `test_a_resolver_source_is_no_longer_refused_wholesale` **FAILED** on
`assert "E-RESOLVER-UNKNOWN" in unknown` — `AssertionError: assert 'E-RESOLVER-UNKNOWN' in set()`,
with the first assertion (`found == set()`) still passing, exactly the asymmetry the brief predicted
and the reason the positive control is in the test. `E-DATA-RESOLVER-UNSUPPORTED` appears nowhere in
`src/`; its only remaining occurrence outside the development record and the dated feasibility
analysis is inside the new retirement test's own docstring, which is a statement about its absence.

**Yield order preserved (check 4).** The fixture is built for it: `layout.csv` rows are `B9,h3` then
`A1,c2`, so sorted order and yield order genuinely differ. Mutation: appended
`units = sorted(units, key=lambda u: u.key)` before `_from_resolver`'s return. **Full suite: 1
failed, 2076 passed** — and the one failure is
`test_a_resolver_source_yields_the_roster_in_yield_order`. Exactly one test sees it, which is the
right number, since `provenance.units` records only `{n, key}` and `units_hash` is computed over the
list `resolve_units` returns — a single-producer chain from the pinned point. No separate
`units_hash` fixture is needed; an end-to-end order assertion belongs with task 33's run test.

**Every new test discriminates (check a).** Each mutation reddened exactly one test and left the
rest green:

| Test | Mutation | Result |
|---|---|---|
| `..._yields_the_roster_in_yield_order` | `sorted(units, key=...)` before return | FAIL (1 of 2077) |
| `..._yielding_something_that_is_not_a_unit_is_refused` | `if not isinstance(item, Unit):` → `if False:` | FAIL (`AttributeError` at `units.py:355`) |
| `..._reached_with_no_cfg_refuses_rather_than_crashing` | `if cfg is None:` → `if False:` | FAIL (`FileNotFoundError`, not `ContractError`) |
| `..._is_no_longer_refused_wholesale` | restore `_check_units`' resolver skip | FAIL on the second assertion |
| `test_a_table_source_still_resolves_with_no_cfg` | (control) a `cfg is None` guard one branch higher | reddens by construction |
| `test_the_unsupported_family_is_down_to_null_test` | any re-added `-UNSUPPORTED` finding | equality, not membership |

The `cfg`-guard mutation fails via `FileNotFoundError` rather than the brief's predicted "DID NOT
RAISE", as the report discloses — still a genuine discrimination, since `pytest.raises(ContractError)`
does not admit it.

**Check 5 — `cfg` as a defaulted keyword.** Both production call sites thread it. The two positive
resolver tests pass `cfg=Config({})` explicitly, so the default is not silently doing their work,
and `test_a_table_source_still_resolves_with_no_cfg` is the control proving the default did not turn
every existing caller into a refusal. `E-RUN-RESOLVER-UNCONFIGURED` fires only from a non-production
caller, which is what decision 6's named price means; see M2 for what is still unpinned.

**Check 6 — `_wide_swept_paths` → `sweep.wide_swept_paths`.** Body moved verbatim with one honest
paragraph appended explaining the move. No residue: `grep -rn "_wide_swept_paths" src/ tests/
docs/reference.md` → empty. `tests/test_cli.py`'s import moved in the same commit and all three uses
were renamed. **No monkeypatch is aimed at the old name** — the three `monkeypatch.setattr` calls
against `cli`/`cli_module` target `execute_plan`, `assignment_for`, and `_resolved_resample`, none
of them the moved function. No cycle: an AST scan of runtime imports gives `validate → {plugins,
runner, sweep, units}`, `units → {artifacts, plugins}`, `plugins → artifacts`, `artifacts → sweep`,
and `cli` is the only module importing `validate`; `artifacts`' and `sweep`'s imports of `units` are
both under `TYPE_CHECKING`, so `units → artifacts → sweep → units` is not a runtime cycle. Confirmed
by importing all four modules in a fresh interpreter.

**Check 8 — what the retirement made stale.** Swept by reading rather than by grepping for one
spelling. § The one config file's count goes **two → one**, naming `statistics.null_test` alone, with
the `resample`/`holdout` retirement shape appended; the *"A third refusal in the same family"*
sentence was correctly renumbered to *"A second"* — the count phrase near the edit, which CLAUDE.md
names as the thing an insertion breaks. `materialize.py`'s and reference.md's `from:` enum comments
agree and neither carries `(NOT BUILT)`. § CLI reference's `Status` column is untouched and
correctly so — no command's build state moved. § Where units come from carries no build claim to
strike, which corroborates the report's disagreement about the brief's "second enum comment": I
searched it too and there is nothing there. reference.md:420-425's `-UNSUPPORTED` paragraph is
self-maintaining and needed no edit. `README.md`, `design-principles.md` and
`experimental-designs.md` make no build claim about resolvers at all. `CLAUDE.md`'s two mentions are
dated historical narrative and correctly left for task 33 — the report's reasoning here is right.

**Mutation hygiene.** Every mutation was reverted by restoring a scratchpad copy (never
`git checkout --`), `__pycache__` cleared, and the revert verified by re-running the affected file.
Final `git diff HEAD -- src/ tests/ docs/` is empty; the only working-tree change is the
pre-existing `.superpowers/sdd/.gitignore` clobber.
