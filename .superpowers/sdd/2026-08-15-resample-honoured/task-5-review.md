# Task 5 review: `E-STATS-RESAMPLE-STRATIFY-UNKNOWN`

**Spec compliance: ✅**
**Task quality: findings** — 3 Important, 5 Minor. No Critical.
**I1 and I2 should be closed before task 6 starts.** Both are inherited rather than local:
I1 leaves the declaration-vs-columns axis unpinned exactly as task 8 gives `_check_resample`
a reason to read the roster, and I2's docstring is the helper tasks 6-8 consume. "No Critical"
is not permission to proceed past them.

Reviewed at `1253763`. Baseline reproduced: `uv run pytest` → **1710 passed, 2 xfailed**;
`ruff check .` and `mypy` (42 files) clean. Every mutation below was applied in place,
`__pycache__` deleted between runs, reverted by editing in place, and the tree confirmed
byte-identical to `1253763` afterwards (`diff` against a saved copy, never `git status`).

---

## Spec compliance

- Design spec item 5 ("`resample.stratify_by` names declared attributes; mints the identifier
  § Validation's *Resample strata exist* row has never had") is delivered as written.
- § Validation's *Resample strata exist* row (`reference.md:321`) correctly left unchanged —
  that table has no Code column.
- Registry row inserted in § Errors `validate` reports in correct alphabetical position
  (`RESAMPLE-N` → `RESAMPLE-STRATIFY-UNKNOWN` → `SWEEP-ABLATE-*`).
- **Mechanical pass clean:** row has 2 columns matching the header; `(#expansion-modes)`
  resolves to `### Expansion modes`; no trailing whitespace, tab or invisible unicode
  anywhere in `reference.md` outside fences; no count phrase near the insertion (the table is
  unbroken by prose, and no sentence counts registry rows).
- **Config completeness holds:** § The one config file already shows
  `{method: bootstrap, n: 2000, stratify_by: []}` in the `resample:` comment
  (`reference.md:147-149`), so the accepted `[]` default is the documented one.
- **Nothing implies resample is honoured.** `_check_resample`'s docstring still opens by
  restating that `E-STATS-RESAMPLE-UNSUPPORTED` refuses the block wholesale.

## The two corrections, verified

**1. Message vs. test contradiction — real, and the correction is sound.** Confirmed the
brief's message (`… declares {', '.join(sorted(declared))}`) is incompatible with its own
`assert "cohort" not in named`, because `cohort` is the declared attribute and appears in
every offender's message. The shipped message matches `_check_report_by`'s shorter shape
exactly. See Minor 1 for the cost.

**2. Fixture change verified on its own merits, not the dispatcher's rationale.**
- `_check_resample` indeed never reads `roster`; confirmed by reading the body.
- `_resample_stratum_table` produces a **genuinely resolved** roster. Pinned by mutation:
  deleting the `_resample_stratum_table(tmp_path)` call from
  `test_a_wrong_typed_resample_stratify_by_…` fails on
  `assert "E-UNITS-ATTR-MISSING" not in found`. The `tmp_path` the helper writes to is the
  one `write_config` points `data.input_dir` at, and the fixture's own `index.csv` is written
  at setup, before the test body overwrites it — ordering is correct.
- **Dropping `attributes: ["cohort"]` from `_RESAMPLE_UNITS` weakens nothing from tasks 3-4.**
  All 11 uses assert code *membership* (`in` / `not in`); none asserts a set equality, reads
  the roster, or depends on `E-UNITS-ATTR-MISSING`. Checked each of the 8 tests individually.
- It strictly **helps task 8**: `units._from_table` *raises* `ContractError(E-UNITS-ATTR-MISSING)`
  for an attribute with no column, so under the old constant the roster was `None` for every
  task-3/4 test. It now resolves. Nothing in this diff makes a resolved roster harder to
  obtain. Caveat in Important 2: the helper writes **one** unit row, which will not satisfy
  task 8's `limits.min_clusters` count work as-is.

## Mutation results

| Mutation | Result |
|---|---|
| `break` after the `c.error` in the loop | Only `…earns_one_finding_per_offending_stratum` fails (`1 == 2`); the single-offender test still passes. Reported behaviour reproduced exactly |
| `stratum_names(stratify_by)` → `stratify_by or []` | `…bare_string…is_read_as_one_name` fails with 4 offenders (`s`,`i`,`t`,`e`) |
| Container guard removed | `…wrong_typed…is_a_type_fault_not_a_second_finding` fails: the code appears alongside `E-CONFIG-TYPE` |
| **`declared` ← the roster's realized attribute keys** | **Full suite still green — see Important 1** |

Additional probes (written, run, removed):
- An **undeclared but real CSV column** (`stratify_by: [cohort]` with no `attributes`) *is*
  refused — the documented behaviour is correct, only untested.
- `attributes: "cohort"` (non-list) never reaches this code: `E-CONFIG-SHAPE` is fatal first.
  So the `isinstance(attrs, list)` guard `_check_assign` carries is unreachable here — **not**
  a defect, and matching `_check_report_by` was right.
- `stratify_by: [{a: 1}]` does not raise; exactly 1 finding. The `not isinstance(name, str) or`
  short-circuit keeps the unhashable item off the `in` test.

---

## Important

**I1. The task's defining guarantee is a check that cannot fail.** Replacing

```python
declared = {a for a in (…)["attributes"] or [] if isinstance(a, str)}
```

with `declared = {a for u in (roster or []) for a in u.attributes}` — i.e. reading the
**roster's realized columns** instead of the **declaration** — leaves all six new tests green
*and the entire suite green (1710 passed, 2 xfailed)*. Every stratify test writes a CSV whose
columns and whose `attributes` declaration are the same set, so no assertion can see the
difference. That is precisely the *"a fixture whose numbers agree with the bug"* shape, on the
one axis the brief spent two paragraphs on ("The reference set is `data.units.attributes`")
and the registry row states as a promise ("`data.units.attributes`, **not the source's
columns**"). The fix is one test: `data.units` declaring **no** `attributes` against a CSV
that has a real `cohort` column, `stratify_by: ["cohort"]`, asserting the code fires. The code
already behaves correctly (probed); only the pin is missing. This gets worse in task 8, which
gives `_check_resample` a genuine reason to read the roster and so makes a column-based
reading a live way to regress.

**I2. `_resample_stratum_table`'s docstring ships the mechanism the report itself refuted.**
It reads "Write the roster `resample.stratify_by`'s checks read … fails roster resolution
(`E-UNITS-ATTR-MISSING`) **before this check ever sees a resolved roster**". `_check_resample`
never receives a resolved roster in any sense — it reads declarations only, which the report's
own disagreement 2 states. This is interface documentation on the shared helper tasks 6, 7 and
8 inherit, and it tells them the stratify check is roster-dependent. It also loses the two
*correct* reasons the report gives (stray-finding noise; a trap disarmed for later tasks) and
says nothing about what the helper actually provides — **one** unit row, `p1,a`, which is not
enough for task 8's cluster-count work. Rewrite it to say: the config's `attributes`
declaration resolves against this table, so no stray `E-UNITS-ATTR-MISSING` is emitted; the
stratify check reads the declaration, not the roster; one row, extend it if you need counts.

**I3. A comment attributes a diagnostic code to a function that raises an uncoded exception.**

> `# NOT units._stratum_groups, which is assign-specific: it admits a sweep.groups axis name`
> `# as a legal target and raises E-DATA-ASSIGN-STRATIFY-UNKNOWN`

`_stratum_groups` raises a bare `NotImplementedError`. Its own docstring exists partly to
explain why: *"It stays a bare `NotImplementedError` rather than a coded `ContractError` for
that reason: a code here would have to name one of the two faults and would be wrong for the
other."* The code is emitted by `validate._check_assign`. Inherited from the brief, but this is
the repo's most-repeated defect class and the comment is in the function tasks 6-8 extend.
(The *second* mention of that code — "one finding per offending name, the same rule
`E-DATA-ASSIGN-STRATIFY-UNKNOWN` already follows" — **is** accurate; verified against the
per-name loop in `_check_assign`.)

## Minor

**M1. The dropped clause costs the typo affordance.** The two *closest* siblings both end with
the declared set: `E-DATA-ASSIGN-STRATIFY-UNKNOWN` ("`data.units.attributes` declares …, and
`sweep.groups` declares …") and `E-DATA-WEIGHT-UNKNOWN` ("`data.units.attributes` declares
…"). Only `_check_report_by` omits it. A user who typed `cohot` now learns the name is wrong
but not what the near-miss candidates are. The brief's contradiction was real, but the cheaper
resolution was to keep the clause and narrow the assertion to the `names \`…\`` prefix.
The requirement that the test assert *the code and the offending name* is met at suite level
(`dx_status`, `count_stratum`, `site`, `3` are each asserted in a message), though
`test_a_resample_stratum_must_be_a_declared_attribute` itself now asserts code membership only.

**M2.** `_check_resample`'s docstring still enumerates the wrong-typed children as
"(`method`, `n`)". There are three now, and `stratify_by`'s guard has a different shape
(coerce-to-`None` rather than skip).

**M3.** `units.stratum_names`' docstring still calls itself "`assign.<axis>.stratify_by`'s
declared names" and "**imported by `validate._check_assign`**". Task 5 adds the second caller
and is the whole reason the *"two independent readings"* contract in that docstring now
spans two fields. It should name both.

**M4. Two tests survive `_check_resample` being deleted outright.** Mutation: `return` as the
first statement of the function. Ten of the seventeen `-k resample` tests fail; these two pass —

- `test_an_empty_resample_stratify_by_is_not_refused` — absence-only, no companion. The brief
  acknowledged it as a control.
- `test_a_wrong_typed_resample_stratify_by_is_a_type_fault_not_a_second_finding` — its only
  must-report assertion, `E-CONFIG-TYPE`, is produced by `check_envelope`, **not by the
  function under test**. That is the exact shape the brief named from task 4 (an acceptance
  paired with a refusal from a different function). It is not fully vacuous — the guard-removal
  mutation does fail it — but it cannot tell "the guard works" from "the function is gone".

One line each fixes both: set `n: 50` in the config so `E-STATS-RESAMPLE-N` fires from
`_check_resample` itself and assert it, proving the function ran.

**M5.** A bare `stratify_by: ""` is silently accepted (`stratum_names` returns `()` for any
falsy value), while the closest documented sibling `E-REPL-FOLD-STRATIFY-UNKNOWN` explicitly
refuses "a non-string, an empty string, or an empty list". The consequence here is nil — it is
identical to the documented `[]` default — so this is a documentation asymmetry, not a defect;
worth a clause in the registry row rather than a code change.

## Cleared, for the record

- No comment or docstring in this diff claims the comparison family is in hand (spec decision
  5 requires task 6 to recompute it locally).
- The registry row's claims about the `LEAF_TYPES` leaf and the wrong-typed *declaration* vs.
  wrong-typed *entry* split are both true and both pinned by tests.
- `envelope.py` has `"statistics.resample.stratify_by": (str, list)` and no entry for
  `assign.<axis>.stratify_by`, so the comment's contrast between the two is accurate.
- The registry row's normative cross-reference — "for the same reason `E-DATA-CLUSTER-UNKNOWN`
  reads that set" — is **true**: `_check_cluster_by`'s docstring states "`data.units.attributes`
  is the reference set for the name", and its emit site reads `units.get("cluster_by")` against
  the declared set, not the table's columns. The `E-REPL-FOLD-STRATIFY-UNKNOWN` row makes the
  same citation and inherits nothing wrong.
