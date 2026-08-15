# Task 3 report: `sample` draws its conditions

**Commits:** `2e0e270` (feature), `cabdc5a` (mutation-driven test strengthening + spec-defect
entry), `2907ebb` (the run-scope swept-path fix found while checking call sites).
**Suite:** 970 → 1016 passing. `uv run ruff check .` and `uv run mypy` green. `ruff format` not run.

## What landed

- `sweep.py`: `sample_fault` (the shared gate), `_sample_seed`/`sample_seed_for` (the derivation),
  `_scaled` (the three range forms), `_sample_cells` (`n` realized draws), `sample` joining `_axes`
  and `_swept_paths`, and `sample_seed` on `sweep_document`.
- `validate.py`: `E-SWEEP-SAMPLE-UNSUPPORTED` retired; `_check_shape` gains the whole `sample`
  shape family; `_check_sweep` gains `E-SWEEP-SAMPLE-INVALID`, the sampled paths through
  `E-SWEEP-PATH-UNKNOWN`, the bounds through `E-PARAM-VALUE` (the "sample ranges" check), and a
  widened `E-SWEEP-PATH-DUPLICATE` over all three axis-shaped modes.
- `cli.py`: `sweep.yaml` records `sample_seed`.
- `reference.md`: `NOT BUILT` dropped from `sample`, Thirteen → Twelve, the `seed:` comment widened
  to name the pin, `sample_seed` named in § `sweep.yaml`, one § Validation row, one new registry
  row, and the `E-SWEEP-PATH-DUPLICATE`/`E-SWEEP-PATH-UNKNOWN` rows widened.

## Note 3: every operation on `sample`-derived data, and its guard

`_sample_cells` and everything downstream of it, enumerated as operations rather than as inputs.
Each row names the YAML-expressible type that makes that operation raise, and the guard. Every
shape row is guarded **twice**: `validate._check_shape` (`E-CONFIG-SHAPE`, fatal, matching the
`grid`/`paired` guards) reports it to the user, and `sweep.sample_fault` refuses it from inside
`expand` so a config that reaches expansion without passing validate raises a coded
`ContractError` rather than a bare exception.

| Operation on `sample`-derived data | Input type that makes it raise | Guard |
|---|---|---|
| `sample.get("n")`, `sample["ranges"]` — attribute/item access on the block | `sweep.sample: "x"` / `[...]` → `AttributeError`/`TypeError` | `_check_shape` `sweep.sample` mapping; `sample_fault` non-dict |
| `range(n)` / `engine.random(n)` | `n: "8"`, `n: 1.5`, `n: null` → `TypeError` | `_check_shape` `sweep.sample.n` integer; `sample_fault` |
| `n` used as a count | `n: 0`, `n: -3` → no crash, silently zero conditions (worse) | `sample_fault` → `E-SWEEP-SAMPLE-INVALID` |
| `n` as an integer, semantically | `n: true` (a `bool` **is** an `int` to Python) → one condition from a declaration a reader reads as a flag | both, `bool` excluded explicitly |
| `method == "sobol"` dispatch | `method: ["sobol"]` → no crash, silently falls through to `random` | `_check_shape` string; `sample_fault` |
| `method` outside the enum | `method: gaussian` → silently `random` | `sample_fault` → `E-SWEEP-SAMPLE-INVALID` |
| the seed, pinned or derived | `seed: [1]`, `seed: "17"` → a string seed is not a seed | `_check_shape` string-or-int; `sample_fault` |
| `ranges.items()` | `ranges: []`, `ranges: "x"` → `AttributeError` | `_check_shape` mapping; `sample_fault` |
| `ranges` as the axis's width | `ranges: {}` → `qmc.Sobol(d=0)` raises; `random` yields `n` empty cells | `sample_fault` (empty `ranges` refused before any sampler is constructed) |
| a range key used as a dict key and split in `_keys_for(...).split(".")` | `ranges: {123: ...}` → `AttributeError: 'int' object has no attribute 'split'` — the exact crash task 2 closed for `paired` and `grid` | `_check_shape` string key; `sample_fault`; `_swept_paths` also skips non-strings |
| `next(iter(declared_range.items()))` | `ranges: {a.b: "uniform"}` → `AttributeError` | `_check_shape` mapping; `sample_fault` |
| the single form key | `{}` (no form) → `StopIteration`; two forms → one silently ignored | `sample_fault` (`len(spec) != 1`) |
| `form == "int_uniform"` dispatch | `{123: [0,1]}` → non-string form, silently scaled as `uniform` | `_check_shape` string; `sample_fault` |
| unknown form | `{gaussian: [0,1]}` → silently scaled as `uniform` | `sample_fault` |
| `bounds[0]`, `bounds[1]` | `uniform: 0.5` → `TypeError`; `[0,1,2]` → third bound silently dropped | `_check_shape` list; `sample_fault` (list of exactly two) |
| arithmetic on a bound (`float(low)`, `math.log`) | `["0","1"]` → `TypeError`; `[true,false]` → arithmetic on booleans | `_check_shape` number, `bool` excluded; `sample_fault` |
| `high - low` as a width | `[1, 0]`, `[1, 1]` → draws outside the declared interval, or a degenerate axis | `sample_fault` |
| `math.log(low)` | `log_uniform: [0, 1]` → `ValueError: math domain error`; a negative low → same | `sample_fault` |
| `int(low)`, `int(high)` | `int_uniform: [1.5, 3.5]` → silently truncated to a different range | `sample_fault` |
| `design_digest(config)` — `json.dumps` over `data.units` | a YAML date (`enrolled: 2026-08-12` → `datetime.date`) → `TypeError: not JSON serializable`, which `validate` swallows | `sample_seed_for` catches and re-raises as `E-SWEEP-SAMPLE-INVALID`; computed **only** when `sample` is declared and only on the `auto` path, so no other config is exposed |
| the drawn value written by `yaml.safe_dump` | a NumPy scalar → `RepresenterError` at run time, after the compute | `_scaled` returns plain `int`/`float`; pinned by `test_the_drawn_values_are_plain_python_scalars` and the end-to-end cli test |
| `_axes` receiving no seed | (internal) a fallback seed would draw a real-looking sample from a seed no config derived, while `sweep.yaml` recorded another | raises `E-SWEEP-SAMPLE-INVALID` rather than defaulting |

`E-CONFIG-SHAPE` covers the *types*; `E-SWEEP-SAMPLE-INVALID` covers the legal-shape/illegal-value
residue. That is the same division `grid` already draws between its `list` guard in `_check_shape`
and `E-SWEEP-AXIS-EMPTY` in `_check_sweep`.

Pinned by `test_a_malformed_sample_raises_a_coded_error_rather_than_crashing` (26 inputs, asserting
`ContractError` with the code — never a bare exception), `test_a_misshapen_sample_is_refused_as_a_shape_fault`
(13 inputs, `E-CONFIG-SHAPE`) and `test_a_sample_that_cannot_be_drawn_from_is_refused` (10 inputs,
`E-SWEEP-SAMPLE-INVALID`).

## Tests: fail-then-pass evidence

The determinism test was written first, per step 2, and run before any implementation:

```
$ uv run pytest tests/test_sweep.py -x -q
tests/test_sweep.py:411: AssertionError
FAILED tests/test_sweep.py::test_sample_draws_are_deterministic_given_the_config
1 failed, 29 passed in 0.08s
```

After `sweep.py`:

```
$ uv run pytest tests/test_sweep.py -q
42 passed in 0.76s
```

The validate-side tests likewise failed first — two of them for a real reason rather than a missing
feature, which is worth recording: `test_sample_is_accepted_and_expands_for_real` reported
`E-SWEEP-PATH-UNKNOWN` for `analysis.confidence`, a parameter the template plainly declares. Cause:
my loop variable `for path, spec in sample["ranges"].items()` shadowed `_check_sweep`'s own
`spec = template.parameter_spec`, which `_path_resolves` and `_value_checks` both close over — so
every path resolution in the sample branch was checked against the *range* dict. Renamed to
`declared_range`, with a comment naming the hazard.

Final state:

```
$ uv run pytest -q
1016 passed in 54.19s
$ uv run ruff check . && uv run mypy
All checks passed!
Success: no issues found in 40 source files
```

## Mutation testing

Each mutant applied to a clean tree, the named test run, then `git checkout --` and
`git status --porcelain src` confirmed empty (shown as `clean:''` in every run).

| # | Mutation | Test | Observed |
|---|---|---|---|
| M1 | `method` ignored — every method draws as `random` | `test_each_method_draws_its_own_points` | **FAILED** as required |
| M2 | seed constant across configs (`f"constant\|sample\|{index}"`) | `test_two_configs_the_digest_can_tell_apart_draw_differently` + `test_sample_draws_are_deterministic_given_the_config` | **1 failed, 1 passed** — exactly the split note 5 asks for: the same-config determinism test cannot see a constant seed, the discriminating test can |
| M3 | pinned integer seed ignored (falls through to the derivation) | `test_a_pinned_integer_seed_overrides_the_derivation` | **FAILED** |
| M4 | `qmc.Sobol(scramble=False)` — the engine ignores its seed | (first run) `-k "sample or method or sobol"` | **SURVIVED, 7 passed** → gap found and closed: the discriminating test is now parametrized over all three methods, after which the same mutant **FAILED** on `[sobol]` |
| M5 | `uniform` returns the raw unit draw | `test_uniform_scales_linearly_into_the_declared_interval` | **FAILED** |
| M6 | `int_uniform` exclusive of its upper endpoint | `test_int_uniform_draws_integers_inclusive_of_both_endpoints` | **FAILED** |
| M7 | `log_uniform` scaled linearly | `test_log_uniform_is_uniform_in_the_log_of_the_interval` | **FAILED** |
| M8 | the sample axis crossed **per path** instead of composed as one axis (`n ** d` conditions) | (first run) whole `test_sweep.py` | **caught only incidentally** by the malformed-input test → gap closed: `test_a_sample_axis_multiplies_with_grid` now declares two sampled paths and asserts 6 conditions, not 18; the same mutant then **FAILED** on it |
| M10 | `command_run`'s `swept_paths` back to `grid \| baseline` | `test_a_sampled_path_is_unreadable_at_run_scope` | **FAILED** (the first, unit-level version of this test survived it — rewritten end to end for that reason) |
| M9 | `_check_shape`'s whole `sample` block deleted | `-k misshapen_sample` | **13 failed** (13 passed before). Note the class stays closed even under this mutant — `sample_fault` still refuses every one from inside `expand` — which is the belt-and-braces the two-sided guard buys |

M4 and M8 are the two the mutation pass earned outright: both were silent-no-op mutants that the
first test set could not see.

## The digest-constancy question (note 2) — verdict: intended, no spec-defect entry

**A project declaring neither `data.units` nor `sweep.groups` does draw the same sample as every
other such project, and that is a pre-existing, documented property of core's randomness rather
than something `sample` introduces.** The evidence is that repeat seeds already have it:

```
$ uv run python -c "... design_digest / resolve_repeats over two unrelated configs ..."
True sha256:62e5db3a6a6f0                  # the two digests are equal
[1862657564, 169278302, 780543318]         # config `alpha`, parameters {x: 1}
[1862657564, 169278302, 780543318]         # config `beta`,  parameters {x: 99}
```

Two configs sharing nothing but the absence of a unit declaration already resolve the *same three
repeat seeds* today, on `main`, with no `sample` involved. `reference.md` § What `auto` derives
from states the rule that produces it and defends it at length: the digest covers "the declarations
describing *what is being randomized over*" and "covers nothing about the parameter values being
swept", because deriving from `parameters_hash` would redraw every fold, reseed every repeat and
reassign every patient whenever a parameter is edited. A config that randomizes over nothing
declared has nothing to distinguish it, and a constant is the honest consequence.

Two further reasons not to file it: nothing in the four documents promises that unrelated
experiments draw differently — the promises are reproducibility and *within*-design independence,
both of which hold — and a user who wants a distinct draw has the documented lever, § What `auto`
derives from's "pinning an integer is the deliberate act", which this task implements (see below).

**What I did file instead** (`docs/superpowers/spec-defects.md`, new entry at the end) is a
different ambiguity found in the same passage — see the last section.

## The `sobol` `n` decision (note 4)

**`n` is drawn exactly, including when it is not a power of two.** `scipy` emits a `UserWarning`
there; it is suppressed with `warnings.catch_warnings()` around that one `.random(n)` call.

The argument, recorded in `_sample_cells`'s docstring: `n` is the **condition count**. It is billed
against `limits.max_executions`, printed by `dry-run`, and recorded in `sweep.yaml` as the design.
Rounding it up or down would execute a different experiment than the one declared, and a run whose
condition count does not match its config is precisely the "a record describing an experiment
nobody performed" failure this project treats as worst. Refusing a documented, reasonable `n` was
the other bad option the brief names. What is actually lost at a non-power-of-two `n` is Sobol's
*balance* property — the sequence is still low-discrepancy, just not perfectly balanced — and no
document promises balance, so no warning code was minted for it (a `W-` code costs a registry row
and a § Warnings row, beyond this task's charter). Pinned by
`test_sobol_accepts_an_n_that_is_not_a_power_of_two`.

## `E-SWEEP-SAMPLE-UNSUPPORTED` and the "sample ranges" check (step 5)

- **Retired.** Removed from `_check_unimplemented`'s refusal tuple; its docstring and the refusal
  message now say this build expands `baseline`, `grid`, `paired` and `sample`. `E-SWEEP-KEY-UNKNOWN`'s
  message, stale since task 2 ("`expand` understands only `baseline` and `grid`"), was corrected in
  the same pass. Two existing tests were updated the way task 2 updated them for `paired`:
  `sample` left the `test_each_unimplemented_mode_is_refused_on_its_own` parametrize list and the
  refusal-message-tone list, and `test_sample_is_accepted_and_expands_for_real` replaces them.
- **The "sample ranges" check is `E-PARAM-VALUE`, not a new code.** § Validation's row states it by
  example — "`sweep.sample.ranges.analysis.confidence` upper bound 1.4 violates the parameter's
  `lt=1`" — which is literally `Param.check` on the bound. Each bound goes through the same
  `_value_checks` a `grid` value does, with `nameable=False` (a bound is never rendered into a
  label; the *drawn* value is, and a drawn float always renders inside `SWEPT_VALUE_PATTERN`).
  Pinned by `test_a_sample_range_bound_outside_its_parameters_constraint_is_refused`, which asserts
  the path `sweep.sample.ranges.analysis.confidence.uniform[1]`.
- Sampled paths also go through `_path_resolves` (`E-SWEEP-PATH-UNKNOWN`), which the registry row
  now names.
- **One code minted:** `E-SWEEP-SAMPLE-INVALID`, one registry row, one § Validation row
  ("Sample is drawable"). All the value-level faults share it with a message naming which fired.
- **`E-SWEEP-GROUPS-UNSUPPORTED` still fires** — `test_each_unimplemented_mode_is_refused_on_its_own`
  covers `ablate` and `groups` and passes.

## Anything questionable

1. **I widened `E-SWEEP-PATH-DUPLICATE` to cover `sample`.** Not in the brief, but leaving it would
   have reopened through a third route exactly what task 2's fix round closed: a path written by
   both `grid` and `sample` lets the later mode's value win on every combination. It is worse here
   than in the enumerated case, because `sweep.yaml` records the *drawn* value as the condition's
   while the run used the `grid` cell's. The check is now a walk over all three modes rather than a
   `grid ∩ paired` intersection, reported at the later mode's location; the registry row follows.
   The pre-existing test asserting the `grid`/`paired` field name still passes unchanged.
2. **A pinned integer `seed` is accepted, contrary to my first implementation.** I initially refused
   anything but `auto`, then found § What `auto` derives from: "`sweep.sample.seed`, `assign.seed`,
   and `holdout.seed` each default to the derivation above … **Pinning an integer is the deliberate
   act**, and the one to take for anything you intend to cite." Refusing it contradicted the
   document, so `sample_seed_for` returns a pinned integer literally (and does not compute the
   digest at all on that path). This is not a re-litigation of the brief's settled decision — the
   brief settled where `auto` derives *from*, not that `auto` is the only legal value. The
   § Expansion modes `seed:` comment was widened to name both values (the enum-comment drift class).
3. **A doc-vs-doc ambiguity is now in `spec-defects.md`.** § Expansion modes says the seed is
   "derived from the design digest"; § What `auto` derives from's table says `sample` draws mix
   "digest + `n`, `method`, `ranges`". I implemented the first, per the brief. The two agree on
   every observable except one: under `random` and `sobol`, raising `n` **extends** the condition
   list rather than redrawing it, which is what the same table explicitly prefers one row up for a
   `seed` level's seeds — and which the "mixes `n`" reading would forbid. Recorded rather than
   silently resolved.
4. **Two sampled conditions can carry identical labels.** Under `int_uniform` over a small range
   (`[10, 12]` with `n: 50`), two draws land on the same integer, so two conditions render the same
   label. Directories stay unique — `condition_dir_name` prefixes the index — but a label is also a
   selector, and `_condition_labels` collects into a `set`, so a hypothesis's `compare.condition`
   naming that label is ambiguous. Not new to this task in kind (it is the label-as-selector
   tension `check_swept_value` already documents), not a crash, and not something § Expansion modes
   speaks to; flagged rather than fixed, since inventing a `sample`-specific label form would move
   artifact paths, which is task D's blast radius rather than this task's.
5. **The `random` method uses `random.Random`, not `numpy.random.default_rng`.** `sweep.py` would
   have been the only module in `src/` importing NumPy, and under `python_version = "3.11"` mypy
   fails inside NumPy's own stubs (`Type statement is only supported in Python 3.12 and greater`) —
   verified as caused by the import, not pre-existing, by stashing. The stdlib generator is
   deterministic given the seed, which is all the property requires, and `stats.py` already seeds
   the same one.
6. **`sample_fault` duplicates `_check_shape`'s type checks.** Deliberate and documented in both
   places: `_check_shape` is what a user sees (fatal, `E-CONFIG-SHAPE`, matching `grid`/`paired`),
   `sample_fault` is what keeps `expand` from crashing when reached without validate. M9 shows the
   second half is load-bearing rather than decorative.

## Four findings from the call-site and reachability sweep (after the first commit)

1. **A real bug, live on `main` for `paired` since task 2, fixed here (`2907ebb`).** `command_run`
   built the set of paths made unreadable at `run`/`summary` scope as
   `set(sweep.grid) | set(sweep.baseline)`. `runner.resolve_wide_cfg` plants a `SweptAway` marker at
   each so a step at those scopes gets `E-STEP-SWEPT-PARAM` rather than "a value that could only be
   wrong for every condition but one". Neither `paired` nor `sample` reached that set, so a
   `summary` step reading a sampled parameter silently got the **base config's** value — one no
   condition in the run used. Now `set(_swept_paths(sweep_block)) | set(baseline)`, the same union
   `label_for` and `E-SWEEP-BASELINE-PARTIAL` already build, so a future mode inherits it. Pinned
   end to end by `test_a_sampled_path_is_unreadable_at_run_scope` (a `summary` step reading a
   sampled parameter must fail the execution); recorded in `spec-defects.md`. Note the first
   version of that test called `resolve_wide_cfg` directly and **survived** the revert — it was
   rewritten as a real run for exactly that reason.
2. **The `sample`-only correction-family exception is reachable now, and holds.** § Validation:
   "Not raised for a `sample`-only sweep, whose draws aren't a family." Dead while `sample` was
   refused. Verified by probe and then pinned: a `sample`-only sweep with `statistics.correction:
   none` produces **no findings at all**. It holds structurally rather than by a special case —
   `contrasts.resolve_contrasts` compares every condition against a *declared* `sweep.baseline`, and
   a `sample`-only sweep declares none, so there are zero comparisons. (With a baseline that pins
   every sampled path, `W-STATS-FAMILY` does fire — but that is not a `sample`-only sweep, so the
   row is satisfied.) Test: `test_a_sample_only_sweep_is_not_a_correction_family`.
3. **`baseline` + `sample` is now refused unless the baseline pins every sampled path**, because
   sample paths joined `_swept_paths`, which `E-SWEEP-BASELINE-PARTIAL` reads. Identical widening to
   the one task 2 made for `paired`, identical reasoning (a baseline leaving an axis free expands to
   one baseline per cell, which this build does not do), and it retires with task D's per-cell
   expansion. Pinned by `test_a_baseline_that_leaves_a_sampled_path_free_is_refused` so task D finds
   it named rather than rediscovering it.
4. **Every `expand()` call site passes the whole doc.** `cli.py:723` is `expand(doc)` and
   `validate.py`'s five call sites are all `expand(doc)` — none narrows or mutates the dict, so no
   caller can redraw a design different from the one `sweep.yaml` records. `resume` is **not
   implemented in this build** (no `command_resume`, no `"resume"` dispatch), so the
   re-expansion-on-resume hazard is not live; whichever slice builds it must read the recorded
   conditions rather than re-expanding, for the same reason § Resuming already gives for
   `execution_order`. Flagged here rather than fixed.

---

# Review round 1 (spec ❌: 1 Critical, 1 Important, 2 Minors)

**Commits:** `c7faf37` (Critical), `c48464a` (Important + Minor 2 + the Minor 1 docstrings + a new
spec-defects entry). **Suite: 1016 → 1019 passing**, `ruff check` and `mypy` green, `ruff format`
not run. `E-SWEEP-GROUPS-UNSUPPORTED` and `E-SWEEP-ABLATE-UNSUPPORTED` both re-confirmed firing
(probed directly: each config reports its own `-UNSUPPORTED` code).

## Critical — `sample`'s *values* were unchecked. Fixed by checking the realized draws.

The reviewer's diagnosis is right and worth restating as the lesson: **my enumeration was over
operations on the declaration, not over what the declaration produces.** `sample_fault` and
`_check_shape` between them close every way a malformed *declaration* reaches the drawing code, and
I wrote a docstring claiming the validates-clean-crashes-at-run class was closed. It was closed over
shapes. The values a `grid` axis contributes go through `_value_checks`; the values a `sample` axis
contributes went through nothing at all, because I checked the two bounds and called that the value
check. Both reported repros confirmed before fixing.

**Route taken: check the realized draws, not the declaration's form.** New
`validate._check_sampled_values`, called once `expand(doc)` has succeeded (the conditions are
already in hand there), running each drawn value through `spec[path].check` — the same `Param.check`
and the same `E-PARAM-VALUE` identifier `grid` and `baseline` values already use.

Why this route rather than "refuse a non-`int_uniform` range on an `int` parameter":

- **Coverage.** The form rule catches the type case and nothing else. It says nothing about the
  second repro (`Param(int, choices=[10, 50])` with `int_uniform: [10, 50]` — right form, right
  type, draws `37`), nor about `pattern`, `ge`/`gt`/`le`/`lt`, or a `log_uniform` range that dips
  under a `gt=0`. The constraint vocabulary is closed but not small, and a form-shaped rule would
  have to re-derive "which forms can satisfy which constraints" — a second, weaker copy of
  `Param.check`.
- **It asks about what executes.** The drawn value is what a step reads, what `sweep.yaml` records,
  and what the condition label renders. Checking the bound is checking something no step sees.
- **It is not flaky.** The draw is deterministic given the config (that is this task's whole
  property), so "this config draws an illegal value" is as stable as any other finding here.

Its one real cost, which the reviewer named and I did not hide: the finding quotes a value the user
did not literally write. Mitigated rather than ignored — the message names the drawn value *and*
the range that produced it (`sweep.sample.ranges.analysis.min_samples.uniform`), adds
"`int_uniform` is the form that draws integers" when the parameter is an `int` and the form is not,
and reports only the **first** offending draw per path, because `n: 50` over a wrong-typed range is
one mistake rather than fifty.

Tests, one per reported shape plus the mirror:

| Test | Pins |
|---|---|
| `test_a_uniform_range_over_an_int_parameter_is_refused_by_what_it_draws` | the type repro; asserts the path, "expected integer", the `int_uniform` hint, and **exactly one** finding for four draws |
| `test_a_sampled_value_outside_the_parameters_choices_is_refused` | the `choices` repro — the case a form-level rule could not catch |
| `test_a_well_typed_sample_draws_no_value_findings` | the mirror: `int_uniform` over an int and `uniform` over a float report nothing |

**Mutation M11**: replacing the `_check_sampled_values(...)` call with `pass` → the first two tests
**FAIL**, the mirror passes. (That run cost me the fix itself: the mutant was applied to an
*uncommitted* tree and `git checkout --` reverted the real change with it. Caught immediately by
re-grepping, restored, and committed **before** re-running the mutant. The lesson is procedural —
never mutate an uncommitted fix — and it is why `c7faf37` landed before this paragraph was written.)

## Important — the `E-SWEEP-SAMPLE-INVALID` row contradicted the code. Fixed.

The row still said "a `seed` other than `auto`" while `sample_fault` accepts a pinned integer. Same
drift class as the two rows I did widen, one row over. Now "a `seed` that is neither `auto` nor a
pinned integer", and while there I widened the same row's closing sentence to "a bound — **or a
drawn value** — that is legal here but violates its own parameter's constraints is `E-PARAM-VALUE`",
which is what the Critical fix changed underneath it, and added the drawn-value case to § Validation's
"Sample ranges" row. Mechanical pass re-run over both `reference.md` and `spec-defects.md`: no
trailing whitespace, no tabs, no duplicate anchors, no broken `#anchor`, every table's rows match
its header.

## Minor 1 — the digest-`TypeError` conversion is defensive, not the user-visible route. Docstrings corrected; the real crash recorded.

Verified the reviewer's claim directly: `cli.command_run` computes `design_digest(doc)` at phase 5
(line ~692), **before** `expand`, and `design_digest` raises `TypeError: Object of type date is not
JSON serializable` for `data.units` holding a bare YAML date. So on the run path my conversion
never fires — and the crash is **pre-existing and independent of `sweep.sample`**: any config with
a date under `data.units` gets a raw traceback today, because `main` catches
`PublishableError`/`OSError` only and `validate` never calls `design_digest` at all.

**Kept the conversion, corrected both docstrings to say exactly what it is for.** It buys `sweep.py`'s
own contract — `expand` is public and documented to raise `PublishableError`, so a caller reaching
it outside `cli` (a test, a future tool) gets a coded error rather than a `TypeError` out of a
hashing helper it never called. Removing it would make `expand` raise an uncoded exception for a
reachable input, which is the thing this slice keeps closing.

**The real crash is now a `spec-defects.md` entry** rather than being papered over: refusing
non-serializable `data.units` leaves belongs where `data.units` is checked (**H3 Units**), and the
choice between refusing at `validate` time and making `design_digest` canonicalize what it hashes is
a real decision rather than a one-line guard.

## Minor 2 — the seed shape message. Fixed.

`_check_shape` reported "expected a string" for `sweep.sample.seed` when an integer is equally
legal. `_KIND_LABEL` gained `string_or_integer` ("a string or an integer") — beside the `integer`
and `number` entries this task added, both of which are in use for `n` and for bounds — and the
guard now names both, with a comment saying why (reporting "expected a string" would send someone
who wrote `seed: [1]` toward quoting a number).

## Concern carried forward

The pre-existing `design_digest` traceback (Minor 1) is a real bare-traceback class reachable
without `sweep.sample`, now filed but not fixed, and it is owned by H3 rather than by any task in
this slice. Worth triaging at the end of the branch alongside the `paired` per-entry value-checking
gap, which is in the same position.
