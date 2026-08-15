# Task 5 report: `E-STATS-RESAMPLE-STRATIFY-UNKNOWN`

**Status:** Complete. Commits `1253763` (initial) + `92ad457` (review
follow-up).

**Tests:** `uv run pytest` → 1711 passed, 2 xfailed (baseline 1704 + 7 new:
the brief's 4, 2 added before first review — a wrong-typed container test and
a non-string-entry test — plus 1 more added addressing Important 1 below).
`uv run mypy` clean (42 files). `uv run ruff check .` clean.

## What was built

- `src/publishable/validate.py`: `_check_resample` now also checks
  `statistics.resample.stratify_by` against `data.units.attributes` (the
  declared set, read the same way `_check_report_by` reads it), normalized
  through `units.stratum_names` — the same normalization the eventual draw
  balances on. One finding per offending name. A wrong-typed **container**
  (`stratify_by: 5`) is guarded off before the loop, because unlike
  `assign.<axis>.stratify_by`, this field **is** an `envelope.py` `LEAF_TYPES`
  leaf (`(str, list)`) — an unguarded read would double-report the same
  wrong-typed leaf under both `E-CONFIG-TYPE` and this code.
- `docs/reference.md` § Errors `validate` reports: new row for
  `E-STATS-RESAMPLE-STRATIFY-UNKNOWN`, giving § Validation's *Resample strata
  exist* row (unchanged, two-column table with no Code column) its identifier.
- `tests/test_validate.py`: 6 new tests, plus a fix to the shared
  `_RESAMPLE_UNITS` fixture constant (dropped `attributes: ["cohort"]` — see
  disagreement 2) and a new `_resample_stratum_table` helper for tests that
  need a real resolved roster.

## Two disagreements with the brief, both resolved and verified

**1. The brief's own Step 3 code and Step 1 test contradict each other.** The
suggested error message ended with
`` f"`data.units.attributes` declares {', '.join(sorted(declared)) or 'none'}" ``.
The brief's own first test declares `attributes: ["cohort"]` and then asserts
`"cohort" not in named` over the *other* offenders' messages — but "cohort" is
the declared attribute, so it always appears in that trailing clause,
regardless of which names are refused. Ran it as written first: confirmed the
test fails with `'cohort' is contained here: ... declares cohort'`. Resolved
by dropping the trailing "declares ..." clause entirely, matching
`_check_report_by`'s shorter message shape — which the brief itself said to
reuse, and no doc commits to the message enumerating the declared set.

**2. The brief's stated mechanism for the fixture defect is wrong, though the
prescribed fix was still correct.** The brief said a `None` roster would take
"the early-return path" in `_check_resample`, making the check vacuous. In
fact `_check_resample` never reads its `roster` parameter at all (confirmed by
reading the function body), and `validate_config` calls `_check_resample`
unconditionally regardless of whether the roster resolved — there is no gate
on roster in this function. So the specific failure mode described didn't
apply. The fixture fix was still necessary for two other reasons that do
matter: (a) `data.units.attributes: ["cohort"]` against the default
`index.csv` (`patient_id` only) produces a stray `E-UNITS-ATTR-MISSING` on
every config that declares it, which is noise a reviewer would have to
explain away; and (b) task 4's `_RESAMPLE_UNITS` constant carried the same
roster-broken shape forward as a trap for tasks 6-8, which will need a
resolved roster. Fixed both: added `_resample_stratum_table(tmp_path)` (writes
`patient_id,cohort` real columns) for the four tests that need `cohort` to
resolve, and dropped `attributes: ["cohort"]` from `_RESAMPLE_UNITS` itself
(none of task 4's existing method/`n` tests read the roster, so this costs
nothing and removes the stray finding for every test using that constant).

**Roster-resolution proof:** ran the new tests pre-implementation; `codes()`
returned exactly `{'E-STATS-RESAMPLE-UNSUPPORTED'}` — no
`E-UNITS-ATTR-MISSING` — confirming the roster resolved cleanly against the
fixed CSV before any code under test existed to produce a false negative.
Post-implementation, the same config additionally reports
`E-STATS-RESAMPLE-STRATIFY-UNKNOWN` naming the undeclared name. The new
type-fault test also asserts `E-UNITS-ATTR-MISSING` absent directly.

## Mutation testing (all three, each applied/confirmed FAIL/reverted/confirmed PASS)

1. `break` after the first offender in the loop →
   `test_a_resample_declaration_earns_one_finding_per_offending_stratum` FAILED
   (`1 == 2`), companion single-offender test still passed. Reverted.
2. `stratum_names(resample.get("stratify_by"))` → `resample.get("stratify_by")
   or []` → `test_a_bare_string_resample_stratum_is_read_as_one_name` FAILED
   with 4 offenders (`s`,`i`,`t`,`e`). Reverted.
3. (Added after review) Removed the wrong-typed-container guard →
   `test_a_wrong_typed_resample_stratify_by_is_a_type_fault_not_a_second_finding`
   FAILED (`E-STATS-RESAMPLE-STRATIFY-UNKNOWN` appeared alongside
   `E-CONFIG-TYPE`). Reverted.

`__pycache__` cleared between each apply/revert; reverts done by editing in
place, verified by re-running the test to PASS, never by `git status`.

## Concerns

- The § Errors registry row was drafted once with an overclaim ("or is not a
  name at all" implying any wrong type reaches this code) that the
  container-type guard made false; corrected to state the guard explicitly and
  contrast it with `E-DATA-ASSIGN-STRATIFY-UNKNOWN`'s opposite case (no
  envelope backstop there). Flagging in case a later task's docs read still
  assumes the old, broader wording.
- `_RESAMPLE_UNITS` changed shape (no longer declares `attributes`). Tasks 6-8
  should use `_resample_stratum_table` (or their own roster) if they need a
  real attribute against this constant going forward.

## Review response (spec ✅, 3 Important + 5 Minor, no Critical)

All eight addressed. Final suite: **1711 passed, 2 xfailed** (one net new
test added while fixing Important 1). `uv run mypy` and `uv run ruff check .`
both clean.

**Important 1 — the check's central guarantee ("`data.units.attributes`, not
the source's columns") had no test that could fail it.** Verified the
reviewer's claim first: swapped `declared` to `{a for u in (roster or [])
for a in u.attributes}` and all 17 then-existing resample tests, and the full
suite, stayed green. Investigated why rather than taking it at face value:
`Unit.attributes` is built in `units._from_table` as `{a: row[a] for a in
attrs}` where `attrs` is literally `data.units.attributes`'s own declared
list — so `roster[i].attributes.keys()` and the doc's declared set are
*identical by construction* whenever the roster resolves at all. No fixture
using `Unit.attributes` as the alternate reference set could ever distinguish
them; that specific swap is a mathematical no-op, not a live bug. The real
risk the docs prose is guarding against is a wrong implementation reading
**the source's raw columns** (available at resolve time, not stored on
`Unit`) instead of the declaration. Added
`test_a_resample_stratum_naming_a_real_but_undeclared_column_is_refused`:
`index.csv` carries `patient_id,cohort,extra_col`, `data.units.attributes`
declares only `["cohort"]`, and `stratify_by: ["extra_col"]` must still be
refused even though `extra_col` is a real column. Confirmed the fixture is
the discriminating one by temporarily rewiring `declared` to read the
source's own CSV header (opening `data.input_dir/data.units.from` and
splitting its first line) — the new test FAILED as expected (found only
`E-STATS-RESAMPLE-UNSUPPORTED`, no stratify code), then reverted in place and
confirmed PASS. The `Unit.attributes`-based swap is noted above as
empirically indistinguishable and not treated as a live gap — the raw-column
reading is the one the test now pins.

**Important 2 — `_resample_stratum_table`'s docstring shipped the mechanism
I had already refuted.** Rewrote it: `_check_resample` reads `data.units
.attributes` from the declaration alone and never touches `roster`; the table
exists only for (a) avoiding a stray `E-UNITS-ATTR-MISSING` on every test
using it and (b) not leaving `_RESAMPLE_UNITS`'s roster-broken shape as a
trap for later tasks. Also documented explicitly that it writes **one** unit
row — enough for every check in this task, not enough for task 8's cluster
counts, which needs more than one row to have more than one cluster.

**Important 3 — a comment attributed `E-DATA-ASSIGN-STRATIFY-UNKNOWN` to a
raise site that doesn't produce it.** Read `units._stratum_groups`: its
"everything else" branch raises a bare `NotImplementedError`, and its own
docstring says why — the raise can't tell which of two `validate`-time faults
it is, so it deliberately isn't coded. Fixed the comment in
`_check_resample` to say that instead. Confirmed the *other* mention of that
code in the same function (the one-finding-per-name rule, attributed to
`_check_assign`'s own `validate`-time check rather than to the raise) was
accurate and left it alone, per the reviewer's own note.

**Minor 1 — restored the candidate list; fixed the test, not the message.**
Both closest siblings (`E-DATA-ASSIGN-STRATIFY-UNKNOWN`, `E-DATA-WEIGHT
-UNKNOWN`) enumerate the declared set in their message; put that back
(`` `data.units.attributes` declares {sorted(declared)} ``). Rewrote
`test_a_resample_declaration_earns_one_finding_per_offending_stratum` to
extract each offender's own name from its message (`f.message.split("\`")[1]`)
and assert the *set* of offending names is exactly `{"dx_status",
"count_stratum"}`, then assert `"cohort"` **is** present in each message (as
the candidate list), replacing the old absence assertion that the enumeration
necessarily violates.

**Minor 2 — fixed.** `_check_resample`'s docstring now lists `(`method`, `n`,
`stratify_by`)`.

**Minor 3 — fixed.** `units.stratum_names`'s docstring no longer calls itself
`assign`'s alone or names only `_check_assign` as importer; it now states it
is shared with `statistics.resample.stratify_by` and imported by
`_check_resample` too, and is careful not to claim a resample draw exists yet
in this build (`E-STATS-RESAMPLE-UNSUPPORTED` still refuses the block
wholesale) — only that a future one has to read it the same way.

**Minor 4 — fixed both vacuous companions.** Both
`test_an_empty_resample_stratify_by_is_not_refused` and
`test_a_wrong_typed_resample_stratify_by_is_a_type_fault_not_a_second_finding`
now also declare `n: 50` and assert `E-STATS-RESAMPLE-N in found` — a finding
`_check_resample` itself produces, unlike `E-CONFIG-TYPE` (from
`check_envelope`) or a bare absence.

**Minor 5 — ruled: documentation clause, no code change.** A bare
`stratify_by: ""` is silently accepted (`stratum_names` treats an empty
string as falsy, same as absent). Consequence is nil — it just means no
stratum — so added a clause to the `E-STATS-RESAMPLE-STRATIFY-UNKNOWN`
registry row noting the asymmetry with the `fold` sibling's explicit refusal
of an empty string, rather than adding a refusal with nothing behind it.

**Mutation re-verification after all the above edits** (each applied,
confirmed FAIL, `__pycache__` cleared, reverted in place, confirmed PASS):
- Removed the declared-set enumeration from the message → the restored
  candidate-list assertion FAILED as expected.
- Changed the `n` floor comparison to `n < 0` → both Minor 4 companions'
  new `E-STATS-RESAMPLE-N` assertions FAILED as expected.
- Removed the wrong-typed-container guard again (post Minor-4 edit) →
  the wrong-typed test FAILED on the `E-STATS-RESAMPLE-STRATIFY-UNKNOWN`
  absence assertion, with `E-STATS-RESAMPLE-N` correctly still present.
- Re-ran the original `break` and `stratum_names`-bypass mutations against
  the updated assertions (offending-name set, candidate-list presence) —
  both still FAIL as expected.
- The raw-CSV-header mutation for Important 1, described above.

No `git checkout` used for any revert; every revert verified by re-running
the affected test to PASS, not by `git status`.
