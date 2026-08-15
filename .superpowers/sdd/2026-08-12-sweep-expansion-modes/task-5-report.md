# Task 5 report — `ablate`'s three composition checks

**Commit:** `e0ee322` — *feat: refuse the three ablate compositions reference.md names*
**Suite:** `1054 passed, 0 xfailed` (was 1043 passed, 2 xfailed). `ruff check` clean, `mypy` clean.
`ruff format` was not run.

## The three rows, as stated, and the check built from each

All three live in `_check_sweep` (`src/publishable/validate.py`), which is where the template's
`parameter_spec` and the expanded `sweep` block are both already in hand.

### Row 226/216 — Ablation targets → `E-SWEEP-ABLATE-TARGET`

> ``sweep.ablate.remove[0]`` is `analysis.min_samples` (int); `remove` needs a boolean or nullable
> parameter — use `override`

One identifier, two branches, per the coupling decision below.

- **Branch 1 (the row's own words).** For each `remove` path the template declares, if
  `not (param.type_ is bool or param.nullable)` — the parameter can hold neither `false` nor
  `null` — refuse and say "use `override`". A fact about the `Param` alone, so it is **ungated by
  the baseline**.
- **Branch 2 (the produced value).** Otherwise, ask `sweep.removal_value(baseline, path)` what the
  entry actually produces and `param.check` whether the parameter may hold it. Because branch 1
  already passed, this fires only for a **boolean the baseline leaves free**: `removal_value`
  reads the baseline, finds nothing, takes the `null` reading, and plants `null` at a
  non-nullable bool. Gated on a declared baseline.

Both are gated on `_path_resolves` (an unknown path is `E-SWEEP-PATH-UNKNOWN` and has no `Param`
to ask), and the baseline reading applies to `remove` only — an `override` states its own value,
and refusing one on a path the baseline leaves free would reject a legal config (the line
`sweep.ablated_paths` already draws for `E-SWEEP-BASELINE-PARTIAL`).

### Row 227/217 — Ablation needs a baseline → `E-SWEEP-ABLATE-BASELINE-MISSING`

> `sweep.ablate` is declared but `sweep.baseline` is not — there is nothing to ablate from

`if ablate and not baseline` — truthiness on both sides, since `init` writes `ablate: null` and a
null block is not a declared ablation. Fires once per config, not once per `remove` entry, which is
why branch 2 above is gated on a declared baseline.

### Row 228/218 — Doesn't compose with a parameter axis → `E-SWEEP-ABLATE-CROSSED`

> `sweep.ablate` cannot be combined with `grid`, `paired`, or `sample` … `groups` is the exception

The modes are **not** enumerated at the check. `sweep.py` now names them once:

```python
AXIS_MODES = ("grid", "paired", "sample")
def axis_modes_present(sweep) -> list[str]: ...   # truthy members, in AXIS_MODES order
```

`_axes` builds its product from exactly these and `_swept_paths` collects exactly their paths, so
a fourth axis mode joins this refusal the day it joins `_axes` — the rule names no mode ("a second
parameter axis") and neither does its enforcement. `groups` is deliberately outside the tuple: it
varies units, not parameters. Empty/`null` modes are not counted (an empty `grid` has
`E-SWEEP-AXIS-EMPTY`; it is not a second axis).

`tests/test_sweep.py::test_axis_modes_is_every_mode_that_contributes_an_axis` pins the tuple from
both ends: every member makes `_axes` non-empty, and `AXIS_MODES ∪ {baseline, ablate, groups}` is
the six-mode vocabulary exactly.

## The row-216 coupling decision

**Both readings implemented, under one identifier.** The reason they are one identifier and not
two: they are the same question ("can `remove` act on this target?") asked of the two things that
answer it — the parameter, and the baseline that `sweep.ablation_changes` consults in the
parameter's place.

The coupling is real and forced branch 2. `ablation_changes` picks `false` versus `null` from
`baseline.get(path)` because `sweep.py` is pure and has no `parameter_spec`. So:

| Config | Branch 1 (declaration) | What executes | Caught by |
|---|---|---|---|
| `remove: [analysis.min_samples]`, baseline fixes it | fails — `int`, not nullable | `null` at an int | branch 1 |
| `remove: [analysis.drop_missing]`, baseline fixes it | passes — bool | `false` | nothing, correctly |
| `remove: [analysis.drop_missing]`, baseline fixes something else | **passes — it is a bool** | `null` at a non-nullable bool | **branch 2 only** |
| `remove: [analysis.tag]` (nullable str), baseline fixes it | passes | `null` | nothing, correctly |

Row three is the plan's "must be one the baseline fixes" reading, and the type check alone lets it
through. Rather than restate the plan's paraphrase as a second rule, branch 2 checks **what the
entry produces** — `removal_value`, shared with `ablation_changes` rather than reimplemented, so
the check and the expansion cannot disagree — against the parameter's own `Param`. That is the
"a declaration is not what it produces" lesson applied where the brief said it would bite, and it
fires exactly on the coupled case and nowhere else (a nullable target passes `check(None)` and is
never reported).

## Identifiers: grep before minting

Two greps, both before minting — the commands as actually run:

```
$ grep -rn "ABLATE" docs/*.md README.md src/ tests/     # → no matches at all
$ grep -n "ablat" docs/superpowers/spec-defects.md      # → E-SWEEP-ABLATE-UNSUPPORTED, prose only
                                                        #   (task 4 retired it; recorded, not live)
```

Re-run afterwards over the whole tracked tree as `git grep -n "ABLATE"`, which returns only the
three new codes plus that one historical mention. No other `E-SWEEP-ABLATE-*` existed anywhere in
the four documents, `src/`, `tests/`, `docs/superpowers/**` or `.superpowers/**`. Reuse considered and rejected:
`E-SWEEP-BASELINE-PARTIAL` (its condition is a baseline leaving an *axis* free — `ablate` is not an
axis), `E-SWEEP-PATH-DUPLICATE` (two axis-shaped modes writing one path; ablated paths deliberately
do not join that set), `E-PARAM-VALUE` (would report a value the user never wrote, with no way to
say "use `override`"). Three minted:

| Code | Row |
|---|---|
| `E-SWEEP-ABLATE-BASELINE-MISSING` | 227/217 |
| `E-SWEEP-ABLATE-CROSSED` | 228/218 |
| `E-SWEEP-ABLATE-TARGET` | 226/216 |

Each has a row in `docs/reference.md` § Errors `validate` reports, alphabetical within the sweep
family (all three sort above `E-SWEEP-AXIS-EMPTY`), condition written from the emit site with every
gate disclosed: truthiness for 217/218, the `groups` exception for 218, and for `-TARGET` both
branches, the `_path_resolves` gate, the declared-baseline gate, and the `remove`-only scope.

`-BASELINE-MISSING` rather than `-BASELINE`: row 219 ("ablation baseline isn't a group level") is
also about the ablate baseline and will want a name in this family — `E-SWEEP-ABLATE-BASELINE-…`
is left free for it.

## Fail-then-pass evidence

Checked out task 4's `src/publishable/{validate,sweep}.py` (`b93a559`) under the new tests:

```
7 failed, 20 passed
  test_ablate_without_a_baseline_is_refused
  test_ablate_crossed_with_a_parameter_axis_is_refused
  test_ablate_is_refused_against_every_axis_shaped_mode[grid|paired|sample]
  test_removing_a_parameter_that_is_neither_boolean_nor_nullable_is_refused
  test_removing_a_boolean_the_baseline_leaves_free_is_refused
```

The two legal-case tests (`test_a_plain_ablation_validates_clean`,
`test_ablate_composes_with_a_group_axis`) passed on the old code, as they must — they assert
absence, not presence. With the checks in place: `1054 passed`.

## Mutation table

Run against the committed tree (`e0ee322`), restored with `git checkout -- .` after each.

| # | Mutation | Test(s) that failed |
|---|---|---|
| M1 | 217 removed (`if False`) | `test_ablate_without_a_baseline_is_refused` |
| M2 | 217 fires on any `ablate` (legal case) | that test's 3 legal-case siblings + 2 more, 5 total |
| M3 | 218 removed (`crossed_modes = []`) | crossed test + all 3 axis-mode parametrizations |
| M4 | `groups` added to `AXIS_MODES` (legal case) | `test_ablate_composes_with_a_group_axis`, `test_axis_modes_is_every_mode_that_contributes_an_axis` |
| M5 | 216 branch 1 removed | `test_removing_a_parameter_that_is_neither_boolean_nor_nullable_is_refused` |
| M6 | `or param.nullable` dropped from branch 1 | `test_removing_a_nullable_parameter_is_accepted` |
| M7 | 216 branch 2 removed | `test_removing_a_boolean_the_baseline_leaves_free_is_refused` |
| M8 | branch 2 fires on every `remove` (legal case) | 8 tests, incl. both legal-case ones |
| M9 | `removal_value` always returns `False` | 2 validate tests + `test_remove_sets_false_for_a_boolean_and_null_for_anything_else` |

Every check dies when removed and dies when inverted; the two branches of `-TARGET` die
separately (M5 vs M7), which is why the assertions check a message fragment as well as the code.
M6 is the branch the advisor flagged as uncoverable with `generic`'s spec (it declares no nullable
parameter): `test_removing_a_nullable_parameter_is_accepted` patches
`GenericTemplate.parameter_spec` with a `Param(str, nullable=True)` for its duration, following
the existing precedent at `tests/test_validate.py:4467`.

## The xfail markers, and the tightened assertions

Both `@pytest.mark.xfail(strict=True)` markers and the `_NO_IDENTIFIER_YET` reason string are
gone; `git grep xfail tests/` returns nothing, and the suite reports **0 xfailed**.

Both tests now assert an **exact error-code set**, via a new `_error_codes` helper that filters to
`level == "error"`:

- `test_ablate_without_a_baseline_is_refused` → `== {"E-SWEEP-ABLATE-BASELINE-MISSING"}`
- `test_ablate_crossed_with_a_parameter_axis_is_refused` → `== {"E-SWEEP-ABLATE-CROSSED"}`

An exact set is the direct answer to the near-miss the brief describes: `E-SWEEP-BASELINE-PARTIAL`
(or anything else) appearing alongside now fails the test rather than satisfying it, so the code
firing is demonstrably the one under test. The same exact-set form is used for the two legal-case
tests, where the set is `set()` and `{"E-SWEEP-GROUPS-UNSUPPORTED"}` respectively.

## Rows 219 and 257, and `groups`

Neither implemented. `E-SWEEP-GROUPS-UNSUPPORTED` still fires, and
`test_ablate_composes_with_a_group_axis` asserts it is the **only** error a legal
`ablate × groups` config carries — which both confirms the refusal is intact and pins row 218's
stated `groups` exception (M4 above is its mutation).

## Documentation touched

- `docs/reference.md` § Errors `validate` reports — three new rows.
- `docs/superpowers/spec-defects.md` — the retirement-window entry and the "Row 216 has two
  readings" entry are marked closed/resolved with what closed them; the "three value-level shapes"
  entry's stale "the next task's to mint" rationale is corrected (it is still open, and none of
  its three shapes is one of rows 216–218).
- `validate._check_unimplemented`'s docstring said the three rules "are the next slice's checks" —
  now names the three codes and says the one remaining open row is 219.
- `sweep.ablation_changes`'s closing paragraph now names `E-SWEEP-ABLATE-TARGET` as the refusal it
  defers to.

## Questionable / worth a second look

1. **One identifier for two conditions.** `E-SWEEP-ABLATE-TARGET` covers both branches. Precedent
   exists (`E-SWEEP-SAMPLE-INVALID` covers six), the doc row discloses both, and the messages are
   distinct — but a reviewer who wants one code per condition would split it.
2. **Branch 2 is gated on a declared baseline**, so a config with no baseline at all reports only
   `E-SWEEP-ABLATE-BASELINE-MISSING` even when a `remove` also targets an `int`. Branch 1 still
   fires there (it is ungated), so the int case is never silent; only the boolean-leaves-free case
   is folded into the baseline refusal, which is the same fault said once.
3. **`AXIS_MODES` is not yet consumed by `_axes` itself** — `_axes` and `_swept_paths` still read
   each mode by name, because each has a different shape and unifying them would be a refactor
   beyond this task. The tuple is pinned against `_axes` by test instead of by construction.
4. **Cross-document pass on the `reference.md` edit**, beyond the mechanical one: the `groups`
   exception is now stated in three places (§ Expansion modes, § Validation row 228, and the new
   `-CROSSED` registry row) and all three agree — `groups` composes with `ablate` and is refused
   only on its own `-UNSUPPORTED` code. `git grep -n "next slice\|later slice\|not yet\|will be
   honored" docs/reference.md` returns nothing about `ablate`, so no passage still describes rows
   216–218 as pending. The line-181 `NOT BUILT` list is unaffected — the three new codes are not
   `-UNSUPPORTED` and do belong in the validate-time registry.
5. **This report is untracked**, because `.superpowers/sdd/.gitignore` ignores everything in that
   directory; every sibling `task-N-report.md` is untracked too, so this follows the convention
   rather than diverging from it.
6. `expand` stays permissive for both refused compositions (it is pure and cannot refuse);
   `tests/test_sweep.py` continues to exercise `ablate × grid` expansion at that level. That
   split is intended — `validate` refuses, `expand` describes.

---

# Task 5 — review follow-up

**Commit:** `1cabc11` — *fix: pin the axis-mode set to the vocabulary's choke point* (plus a
follow-on tidy, see below). Suite **1055 passed, 0 xfailed**; `ruff check` and `mypy` clean;
`ruff format` not run.

## Important — `AXIS_MODES` is now pinned at the choke point, not by a literal test

The reviewer's `ladder` experiment was right and my disclosure understated it: all three
assertions in the old `test_axis_modes_is_every_mode_that_contributes_an_axis` were literals in
the test body, so the dangerous direction (`_axes` grows, `AXIS_MODES` does not) was unpinned and
the test passed while `ablate × ladder` reported nothing.

Fixed by making the vocabulary **derived**, in `sweep.py`:

```python
AXIS_MODES     = ("grid", "paired", "sample")
NON_AXIS_MODES = ("baseline", "ablate", "groups")
SWEEP_MODES    = AXIS_MODES + NON_AXIS_MODES
```

and `_check_sweep`'s `E-SWEEP-KEY-UNKNOWN` now tests `key not in SWEEP_MODES` instead of a local
literal set. That is the choke point the reviewer identified: a seventh mode is refused by every
config until it is added to `SWEEP_MODES`, and it can only be added there by being classified as
an axis or not — so `E-SWEEP-ABLATE-CROSSED` gets the right answer either way. This is stronger
than the suggested test assertion, which is also present
(`test_the_mode_vocabulary_is_partitioned_into_axis_and_non_axis`: the union equals `SWEEP_MODES`,
the two tuples are disjoint, the six names are § Expansion modes', every axis mode really makes
`_axes` non-empty and no non-axis mode does).

**The reviewer's experiment, re-run against the committed tree.** `ladder` added to `_axes` only,
`AXIS_MODES`/`SWEEP_MODES` untouched, then an `ablate × ladder` config through `validate`:

```
before: []                                   # zero findings
after : [('error', 'E-SWEEP-KEY-UNKNOWN')]   # the mode is unusable until it is classified
```

The three overstated prose claims are rewritten to describe this mechanism rather than
`AXIS_MODES` alone — `sweep.AXIS_MODES`' docstring now says in bold that the tuple is *not* what
makes it real, `validate`'s `-CROSSED` comment names the `known ← SWEEP_MODES` link, and the
registry row says "joins this refusal by being classified as one … a mode outside it is refused by
`E-SWEEP-KEY-UNKNOWN` before it can be used at all".

## Both Minors

- **Branch 2's message**: now "`sweep.baseline` fixes no ***boolean*** value for … so `remove`
  reads the baseline, finds nothing it can turn off, and sets `null` rather than `false`". New
  test `test_a_non_boolean_baseline_value_is_not_a_boolean_the_remove_can_turn_off` uses
  `baseline: {analysis.drop_missing: "yes"}` — the config where the baseline *does* fix a value
  and the old wording was false. The registry row carries the same correction.
- **`-BASELINE-MISSING` row**: now "Both sides are read for a *truthy* value, so `ablate: null` is
  not a declaration and an empty `baseline: {}` is not one either", matching the emit site.

## Follow-up mutations (committed tree)

| # | Mutation | Test(s) that failed |
|---|---|---|
| M4′ | `groups` moved into `AXIS_MODES` | `test_ablate_composes_with_a_group_axis`, `test_the_mode_vocabulary_is_partitioned_into_axis_and_non_axis` (disjointness) |
| M10 | branch 2's message reverted to "fixes no value" | both `-TARGET` baseline-branch tests |
| M12 | `ladder` added to `_axes` only (the reviewer's experiment) | not a test kill — a **behavior** kill: the config is now refused `E-SWEEP-KEY-UNKNOWN` instead of validating clean |

All earlier mutations (M1–M9) re-checked as still killing after the refactor.
`E-SWEEP-GROUPS-UNSUPPORTED` still fires, and `test_ablate_composes_with_a_group_axis` still
asserts it is the *only* error such a config carries.

## Residual, disclosed rather than claimed away

`SWEEP_MODES` is read by `_check_sweep` inline (`key not in SWEEP_MODES`), but nothing test-pins
*that this check reads it*: rewriting that expression back into a literal set with an extra name
in it passes the whole suite (M11). No test can catch that generically — a behavioral test would
have to guess the extra name — so it is the same class as rewriting any check wrongly, and the
honest statement is that the **partition** is guaranteed by construction while the **link from
the check to the partition** is guaranteed by code review. The local `known` variable was removed
so there is no place for a literal to sit unremarked.

## Two follow-ups from the second advisor pass

- **`E-SWEEP-KEY-UNKNOWN`'s message contradicted its own emit site** (pre-existing, not caused
  here): the branch accepted `groups` from the mode set and then told the user "`expand`
  understands only `baseline`, `grid`, `paired`, `sample` and `ablate`". Fixed rather than
  recorded, since the check is the line I just changed — the message now names the vocabulary from
  `SWEEP_MODES` (sorted), and a mode that is recognized but not built keeps carrying that fact on
  its own `-UNSUPPORTED` code, which is where it belongs. No test asserted the old wording.
- **`docs/reference.md`'s `E-SWEEP-KEY-UNKNOWN` row** ("a key that is not one of the six recognized
  sweep modes (`baseline`, `grid`, `paired`, `ablate`, `sample`, `groups`)") was re-checked against
  the derived constant and still reads true — those six are exactly `SWEEP_MODES`. The
  spec-defects note that widening it to `ablate`'s own keys "is a registry edit rather than a code
  change" is likewise unaffected: that gap is one level down, inside the `ablate` block.
