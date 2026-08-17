# Task 27–29 review — attribute projection, `E-RESOLVER-MEASUREMENT-FIELD`, condition-independence

Reviewed `d5c1acb..cf92b70` (commits `4e47f50`, `5b14a61`, `86d87f9`) against
`docs/superpowers/specs/2026-08-17-resolvers-design.md` and its appended corrections, the three task
briefs, the report, and the ledger's two inherited obligations.

**Gates, re-run in the foreground at `cf92b70`:** `uv run pytest` → **2089 passed, 1 skipped, 2
xfailed** (112s), `ruff check` clean, `ruff format --check` → 80 files already formatted, `mypy` → no
issues in 45 source files. The report's numbers reproduce exactly.

Every mutation below was applied by editing the file, `__pycache__` deleted, the suite re-run, and the
file restored from a pre-mutation copy in the scratchpad — never `git checkout --`. The revert is
verified by behaviour (full suite back to 2089 passed), not by `git status`.

## Verdicts

| Task | Axis | Verdict |
|---|---|---|
| 27 | Build | **FAIL** — the new attribute loop lets a bare `TypeError` escape `validate` for a user-writable config; only the resolver path has no guard (C1) |
| 27 | Pinning | **PASS** — all four tests discriminate; the union-vs-intersection fixture is genuinely discriminating, and the reserved-before-missing order is pinned |
| 28 | Build | **PASS with findings** — ungated is the right reading and is correctly implemented, but ungated *too far*: it fires on a resolver whose roster never resolved, and the file's own prose says it cannot (I1) |
| 28 | Pinning | **PASS** — the gate mutation, the code-string mutation, and the table arm's own gate each redden exactly one test |
| 29 | Build | **PASS** — the refusal answers the direct question; only the sentinel read is re-coded |
| 29 | Pinning | **FAIL** — the ledger's `cfg` obligation is closed only for the direct-call path; the `validate`-threaded half was pinnable at this commit and was deferred on an expired spec claim (I2) |

---

## Findings

### C1 — Critical, task 27: a non-string `attributes` item under a resolver crashes `validate`

`_from_resolver`'s new loop (`src/publishable/units.py`, the `for attribute in attrs:` block) checks
`attribute in RESERVED_FIELDS` (a tuple — tolerates an unhashable name) and then
`attribute not in yielded`, where `yielded` is a `set`. An unhashable declared attribute raises
`TypeError: unhashable type` out of `resolve_units`, past `_check_units`'s `except ContractError`, and
out of `validate` — which `E-RESOLVER-YIELD`'s own § Errors row states in words is contracted never to
raise.

**Verified by probe**, not by reading: a throwaway test appended to `tests/test_validate.py` (run,
then the file restored from a pre-edit copy) validated a config with
`data.units.from: {resolver: plate_wells}` and `attributes: [{"operator": 1}]` against an installed
resolver. Result:

```
E   TypeError: unhashable type: 'dict'
src/publishable/units.py:391: TypeError
```

No finding, no `ContractError` — a traceback out of `validate`.

The other two sources are immune, which is what makes this task 27's and not pre-existing:
`_check_units`'s guard is `if isinstance(source, str) and isinstance(attrs, list)` (validate.py ~1331)
and reports `E-UNITS-ATTR-MISSING` for each non-string item, and its own comment at 1315–1329 records
that `check_envelope` reports **nothing** for a non-string list *element*, so skipping silently "would
be a real gap"; `_from_glob` raises `ContractError` unconditionally for any attribute name and never
hashes it. Before this commit no attribute loop existed on the resolver path at all.

Minimal fix: an `isinstance(attribute, str)` check before the set membership in `_from_resolver`
(reported as `E-UNITS-ATTR-MISSING`, the identifier the table path already uses for the type-shaped
version of the same question), or extend validate.py:1331's guard to a resolver source. Not a wider
change.

### I1 — Important, task 28: the ungated arm fires where no roster resolved, and two prose claims say it cannot

Ungated is correct — spec correction 4 and the row are right, and the implementation honours them (see
the mutation table). But the arm is gated on nothing at all, including on the roster having resolved.
`_check_units` returns `frozenset()` for `columns` on **every** failure path — an unregistered
resolver name, `E-RESOLVER-YIELD`, `E-UNITS-EMPTY`, a missing or non-absolute `input_dir` — so `by`
is compared against an empty column set and the code fires.

**Verified by probe** through `validate_config`, config `data.units.from: {resolver: "nope"}` with
`measurements: {by: read_id, collapse: first}`:

```
PROBE-A ['E-RESOLVER-MEASUREMENT-FIELD', 'E-RESOLVER-UNKNOWN']
```

The message asserts a fact about what the resolver yielded — *"resolver `nope` yields no unit carrying
an attribute of that name"* — for a resolver that was never imported. The table arm is immune by
accident of its gate (`technical_n is None` whenever resolution fails), so this fail-open is specific
to the new arm.

Two prose claims in the same file are falsified by it, which is finding (b) with evidence rather than a
reading:

- `_check_measurements`'s docstring: *"When the roster does not resolve, the type half is skipped, but
  the shape half still runs below it"* — the new arm is neither: a roster-derived check that runs when
  the roster did not resolve.
- the arm's own comment: *"The columns here are what the resolver yielded, before the projection"* —
  false when `columns` is `frozenset()` because nothing yielded anything.

Fix: add `roster is not None` to the arm's condition (or read `columns` only when it is). Note **all
three of task 28's tests stay green under that fix** — they pass a real `UnitList` — which is exactly
why the task's own suite could not see this.

### I2 — Important, task 29: the `cfg` obligation's load-bearing half was pinnable here and was deferred on an expired claim

**The report's attribution to task 33 is wrong.** The ledger's obligation (progress.md, "Minor (`cfg`
fixture gap, M2)") names two production-threaded `cfg`s and says the gap should "not be assumed closed
already". Task 29 closed the direct-call half (`_READS_A_PARAM` reading
`cfg.parameters.analysis.method`, called through `resolve_units` directly) and left the
`validate.py` half attributed to task 33, on the spec's correction that *"tasks 25, 27, 28 and 29
cannot test through `validate_config` at their own commits, because the resolver skip is only deleted
at 26."*

**That claim expired before task 29 was written.** Task 26 landed at `884076a`, ahead of `4e47f50`;
`E-DATA-RESOLVER-UNSUPPORTED` is absent from `src/` at this commit, and
`test_a_resolver_source_is_no_longer_refused_wholesale` (tests/test_validate.py:2616) already resolves
a real installed resolver through `validate_config` with the `installed` / `registries` /
`write_config` fixtures.

**Verified by probe:** a `validate_config`-level test using exactly those fixtures, with a resolver
reading `cfg.parameters.analysis.method` and a `sweep.grid` over that path, reports
`['E-RESOLVER-SWEPT-PARAM']` at HEAD and `[]` under the mutation
`resolve_wide_cfg(doc, wide_swept_paths(...))` → `resolve_wide_cfg(doc, set())` in `_check_units`. The
mutation the report calls "task 33's catch" is caught by a test task 29 could have written, using
machinery already in the file it was editing. This is `CLAUDE.md`'s "a scoping expires; the code
outranks both" — a stale spec claim carried instead of re-checked.

**The `cli.py` half is genuinely still open and is not task 29's.** Mutating `cli.py:1318`'s
`resolve_wide_cfg(doc, wide_swept_paths(...))` to `resolve_wide_cfg(doc, set())` leaves the **whole**
suite green (2089 passed) — the run path has no resolver-through-`main` test at all, which task 33
already owns per the task 25–26 review. Recorded so the two halves stay honestly split rather than
looking closed.

### M1 — Minor, task 27: `E-UNITS-ATTR-MISSING`'s row now enumerates three sources and still says "either source"

The widened row reads "…the source table has no column for, or names any value at all under a
`{glob: ...}` source, …, or a value no unit a resolver yielded carries — reported for the first such
name, and after `E-UNITS-ATTR-RESERVED` under either source". The insertion made "either" a count
phrase over three sources. `CLAUDE.md` flags exactly this ("check every count phrase near it"). The
ordering claim itself is true and pinned on all three paths.

### M2 — Minor, task 28: the positive test carries an unasserted co-firing finding

`test_a_resolver_yielding_no_measurement_field_is_refused_under_its_own_code` keeps
`"collapse": "mean"` over a non-numeric attribute, so its `findings` also contain
`E-DATA-MEASUREMENTS-COLLAPSE-TYPE`. Harmless — its assertions are membership plus one negative
(`E-UNITS-ATTR-MISSING not in found`) paired with a positive, so both still discriminate — but the
docstring does not mention the co-firing, and a reader diffing this fixture against the two controls
(now `"first"`) will wonder why they differ.

---

## The three collapse-rule decisions (the implementer's reported disagreement)

All three verdicts are correct, and the third was checked for the "passing for the unrelated reason"
trap rather than assumed:

| Test | Decision | Verified |
|---|---|---|
| `..._refused_under_its_own_code` | left at `"mean"` | Correct — asserts membership, not exhaustiveness. Confirmed the extra `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` finding is present and irrelevant to all four assertions (M2) |
| `..._does_yield_the_measurement_field_reports_nothing` | `"mean"` → `"first"` | Correct — asserts `== []`; under `"mean"` it fails for the unrelated type rule. Still discriminating: an unconditionally-reporting arm reddens it |
| `..._table_source_keeps_its_collapse_gated_reading` | `"mean"` → `"first"` | Correct **and still discriminating** — verified by mutation: removing the table arm's `technical_n is not None and technical_n["max"] > 1` gate reddens exactly this test (plus 9 others across the file). The gate is on `technical_n`, not on the collapse rule, so the `"first"` change cannot blind it |

The pre-existing `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` behaviour is unchanged by these commits — the
per-column type loop runs unconditionally, below both arms.

## Task 29's refusal is not a proxy

Condition-independence is answered by the **direct** question. `_check_units` builds the resolver's
`cfg` with `resolve_wide_cfg(doc, wide_swept_paths(doc.get("sweep") or {}))` — the same substitution
the step path uses — and `wide_swept_paths` derives its set from the sweep declaration itself: every
axis-shaped mode's paths (`_swept_paths`, so `grid`, `paired`, `sample`), plus `baseline`-fixed and
`ablated` paths, minus `selector_paths`. The refusal then fires on an actual **read** of a
`SweptAway` marker, so it is neither a name shape nor a presence test, and a parameter the sweep leaves
alone stays readable (the control test asserts the roster resolves from it).

The re-code seam is `exc.code != "E-STEP-SWEPT-PARAM"`, and the third test pins that only the sentinel
read is re-coded (a resolver raising `E-UNITS-EMPTY` keeps its own identifier). Verified by mutation:
`if False: raise` reddens exactly that test and the pre-existing `E-RESOLVER-YIELD` test.

## § Errors rows

Every code these three tasks emit has exactly one row, and each row covers every emit site:

| Code | Rows | Emit sites covered |
|---|---|---|
| `E-UNITS-ATTR-MISSING` | 1 (widened, task 27) | table (`_from_table`), glob (`_from_glob`), resolver (`_from_resolver`), non-string item (`_check_units`), `measurements.by` table arm — the resolver clause was added; see M1 for the stale count phrase |
| `E-UNITS-ATTR-RESERVED` | 1 | source-agnostic wording ("names a field of `Unit` itself"), so the new `_from_resolver` site needs no change |
| `E-RESOLVER-MEASUREMENT-FIELD` | 1 | `Not yet emitted:` clause struck; wording ("the resolver the roster came from yields no attribute of that name") presupposes a resolved roster, which I1 is the code violating |
| `E-RESOLVER-SWEPT-PARAM` | 1 | `Not yet emitted:` clause struck; the row's mechanism description matches the implementation |

## Every new test, and the single-line mutation that reddens it

| Test | Mutation | Run |
|---|---|---|
| `..._roster_is_projected_onto_the_declared_attributes` (27) | `attributes={a: ...}` → `attributes=unit.attributes` | **FAIL** (reproduced; also reddens the sparse test) |
| `..._declared_attribute_no_unit_yields_is_refused_naming_the_resolver` (27) | delete the `if attribute not in yielded:` raise | FAIL by construction — no `ContractError` raised; the `"index.csv" not in message` assertion additionally pins the generalized wording |
| `..._name_only_some_units_yield_is_not_missing` (27) | `if attribute not in yielded:` → `if any(attribute not in u.attributes for u in units):` | **FAIL** (reproduced). **The fixture is discriminating**: `_YIELDS_PARTIAL` gives `scratch` to unit 1 and not unit 2, so union and intersection give different answers, and the assertion is on the projected values (`[{"scratch": "x"}, {}]`) not on a code |
| `..._reserved_attribute_name_is_refused_before_a_missing_one` (27) | swap the two `if` blocks in the loop | **FAIL** (reproduced) — `paths` is reserved *and* unyielded, so the wrong order yields `E-UNITS-ATTR-MISSING` |
| `..._resolver_yielding_no_measurement_field_is_refused_under_its_own_code` (28) | add ` and technical_n is not None and technical_n["max"] > 1` to the resolver arm | **FAIL** (reproduced — the report's claim is true: `technical_n=None` is what instantiates the ungated reading) |
| same (28) | resolver arm's code → `"E-UNITS-ATTR-MISSING"` | FAIL on the paired negative assertion (positive assertion in the same test, so it is not a bare absence) |
| `..._resolver_that_does_yield_the_measurement_field_reports_nothing` (28) | drop `if valid_by not in columns:` from the resolver arm | FAIL — reports unconditionally |
| `..._table_source_keeps_its_collapse_gated_reading_of_the_same_field` (28) | remove the table arm's `technical_n` gate | **FAIL** (reproduced) |
| `..._resolver_reading_a_swept_parameter_is_refused_under_its_own_code` (29) | delete the `except ContractError` re-code arm | FAIL — `E-STEP-SWEPT-PARAM` escapes |
| `..._resolver_reading_a_parameter_the_sweep_leaves_alone_resolves` (29) | re-code on any `ContractError`, or mark every path swept | FAIL — the control instantiates the "fair game" half of § Where units come from |
| `..._resolvers_own_coded_refusal_keeps_its_own_identifier` (29) | `if exc.code != "E-STEP-SWEPT-PARAM": raise` → `if False: raise` | **FAIL** (reproduced) |

Six mutations were run for real (bolded); the remainder are deletions of the sole code path each test's
assertion depends on, and are named rather than run.

## Docstrings and comments touched

- **`_from_resolver`'s docstring** — re-read whole, as the ledger asked. The false claim named one round
  ago ("Task 28 … as of this commit no such check exists") is gone and replaced with a true one
  (`validate._check_measurements` checks `by` against the returned columns — verified, that is exactly
  what the new arm does). The added projection paragraph is accurate: the union reading, the drop of an
  undeclared attribute, and the list of downstream readers (`cluster_by`, `weight_by`,
  `assign.<axis>.from`, `holdout.from`, `stratify_by`) all match the code and § Where units come from.
- **`_check_measurements`'s docstring and the new arm's comment** — falsified by I1; see above.
- **The `except ContractError` comment in `_from_resolver`** — accurate: the `discover_local` precedent
  it cites is real, and the claim "the mechanism is shared and the fault is not" matches
  `wide_swept_paths`.

## Housekeeping

`.superpowers/sdd/.gitignore` was clobbered to a bare `*` again and was in that state at review time —
the report's "restored before any commit" claim does not describe the tree it left. Restored from
`HEAD` during this review (`git show HEAD:… > …`, not `git checkout --`). No tracked record was lost:
14 of the 18 files in the plan directory are tracked, and the 4 that are not are the three task briefs
and the `.diff`, which the restored `.gitignore` ignores by policy.
