# Task 4 report: `ablate` emits one change at a time

**Commits:** `e2f85e7` (feature + retirement), `9e07dd4` (a test a mutation proved missing).
**Suite:** 1019 → **1042 passing**; `uv run ruff check .`, `uv run mypy` green. `ruff format` not run.

---

## What was built

`sweep.ablation_changes(sweep)` produces one `{path: value}` change per `remove`/`override` entry,
in the order the `ablate` mapping declares its keys. `expand` applies them **after** the product,
not as an axis: each ablate row's `values` is `dict(baseline) | change`, so it runs as the baseline
with exactly one thing different, and the declared baseline is appended once, above, as condition
`00` — **read**, never re-emitted.

A row now carries a third element, the values its **label** is rendered from: the whole cell for a
product row, the one change alone for an ablate row. That is what makes `01_labs=false` — the label
§ Expansion modes shows in its `groups` example — rather than a label restating every inherited
baseline value.

**What `remove` sets is decided by the baseline's value for that path.** § Expansion modes says
`remove` sets "a boolean parameter to `false` or a nullable one to `null`", which is a fact about
the parameter's `Param` — and `sweep.py` is pure, with no template and so no `parameter_spec` to
consult. The baseline is the one thing an ablation is defined against (§ Validation row 216: every
removed path is one the baseline fixes), so a boolean *there* selects `false`; anything else takes
the nullable reading. A path the baseline does not fix takes the `null` reading and is `validate`'s
to refuse (task 5), not `expand`'s to guess at.

---

## Operation-by-operation enumeration, and the guard for each

Enumerated from the operations `ablation_changes` and `expand` perform, not from inputs imagined.
All guards are in `validate._check_shape`, fatal, under `E-CONFIG-SHAPE` — the class `paired` and
`sample` already sit in, and the class that matters because `validate` swallows expansion crashes
by design (`_check_sweep`'s `try: expand(doc) except Exception`).

| Operation | Input type that makes it raise | Guard |
|---|---|---|
| `ablate.items()` | **none** — `ablation_changes` early-returns `[]` on its `isinstance` check, so `ablate: "x"` expands to the baseline row alone. Corrected after review: the earlier claim of an `AttributeError` here was wrong. The guard still belongs, because *silently ignoring a declared block* is its own fault class — the same one `E-SWEEP-EXPANDS-EMPTY` exists for | `sweep.ablate` must be a mapping |
| `for path in remove` | non-list, non-iterable (`{…}` iterates keys; an int → `TypeError`) | `sweep.ablate.remove` must be a list |
| `for path in remove` where `remove` is a **string** | does not raise — iterates character by character into one condition per letter | same list guard; this is the quiet failure `grid`'s axis guard already closed, and is asserted directly in `test_every_misshapen_ablate_really_does_break_expand` |
| `{path: …}` dict literal | an unhashable path (a list/dict entry) → `TypeError` | `sweep.ablate.remove[i]` must be a string |
| `_keys_for` → `path.split(".")`, and `label_for`'s `path.rsplit` | a hashable non-string (`123`) survives the dict literal and raises later, in `_keys_for` | same string guard — which is why it is at the *path* level, not only the list level |
| `for entry in override` | non-list; a string raises at `dict(entry)` below | `sweep.ablate.override` must be a list |
| `dict(entry)` | `None` → `TypeError`; a string/`[…]` → `ValueError` | each `sweep.ablate.override[i]` must be a mapping |
| each override key, into `_keys_for` | non-string key (`{123: "x"}` parses fine off YAML) | override keys must be strings |
| `dict(baseline or {})` — a **new** consumer of an existing guard | non-mapping baseline → `TypeError` | `sweep.baseline`'s mapping guard, unchanged (validate.py, `_check_shape`) |
| `baseline.get(path)` | needs `baseline` to be a mapping and `path` hashable | the two guards above, jointly |

**`from` is deliberately unguarded.** `expand` reads `sweep.baseline` directly and performs *no*
operation on `from` at all, so there is no type that makes anything raise; a guard there would be
enumerating inputs rather than closing a crash. That a `from` naming something other than
`baseline` is silently ignored is a *value* fault — recorded in `spec-defects.md`, see below.

`test_a_misshapen_ablate_is_refused_as_a_shape_fault` covers all eleven shapes;
`test_every_misshapen_ablate_really_does_break_expand` asserts the other half of the claim — that
each of them really does break `expand` unguarded (five raise, the string case mis-expands) — so
the guard is provably closing a crash rather than refusing a shape someone imagined.

---

## The `_swept_paths` decision

**Ablated paths are NOT in `_swept_paths`.** It stays the axis-shaped modes' set, as its docstring
already says, and a new `ablated_paths(sweep)` carries `ablate`'s.

The discriminator is `_swept_paths`'s consumer in `validate._check_unimplemented`:
`E-SWEEP-BASELINE-PARTIAL` reads it to ask *which axis a baseline leaves free*, and its message and
whole comment block reason about a baseline expanding to one condition per cell of the unfixed
axes. `ablate` is not an axis, has no cells, and (per § Expansion modes) cannot compose with one.
An ablated path in that set would refuse a legal config — `override: [{analysis.min_samples: 10}]`
with a baseline that does not fix `analysis.min_samples` — with a message about cells that do not
exist. Putting them in and subtracting them there is the same amount of code with worse semantics.

Both consumers that *do* need the whole set take the union explicitly and say why:

1. **`expand`'s labelling.** `_keys_for` shortens a path to a suffix unique among the paths it is
   shown; an ablated path missing there falls back to `label_for`'s last-segment rule, so
   `features.notes` and `clinical.notes` both render `notes=false` — one label for two conditions,
   and a label is a selector and a directory name. Pinned by
   `test_an_ablated_path_is_disambiguated_against_every_other_ablated_path`.
2. **`cli.command_run`'s run-scope unreadability.** An ablated path varies across conditions, so a
   `run`/`summary`-scoped step reading it would get the base config's value. The `baseline` term of
   that union already covers every `remove` path (a removed path is one the baseline fixes); the
   residue is an `override` path the baseline leaves alone. This is the third widening of that one
   line (`baseline`, then `paired`/`sample`, now `ablate`), and its comment says so.

`test_ablated_paths_are_not_axis_shaped_paths` asserts the split itself, so the decision is a test
rather than a comment.

---

## Are ablated values checked against `Param`?

**`override` values: now yes.** `_check_sweep` runs each `override` entry through `_path_resolves`
then `_value_checks(..., nameable=True)` — the same `E-PARAM-VALUE` and `E-SWEEP-VALUE-UNNAMEABLE`
pair a `grid` value gets, no new identifiers. An override value is structurally a `grid` value:
user-written at a dotted path, planted into a condition's config, and rendered into its label. Left
unchecked it was exactly task 3's escape reopened — `override: [{analysis.method: pearsonn}]` would
have validated clean and run a value § Validation's "Choices" row promises to refuse, and a value
containing `__` would have produced a label that cannot be parsed back into axes. The
`_path_resolves` gate is load-bearing: `_value_checks` indexes `spec[path]` unguarded, so an
unknown override path would otherwise be a `KeyError` inside a function contracted never to raise
(`test_an_ablate_override_path_the_template_does_not_declare_is_refused`).

**What `remove` produces: not checked, and it should be — by task 5.** `false`/`null` on a
parameter that is neither boolean nor nullable is § Validation row 226 verbatim
("`remove` needs a boolean or nullable parameter — use `override`"), which the plan assigns to task
5 alongside row 217 and 218. Verdict: it must be checked, on that row's identifier, in that task —
implementing a second reading of it here would either duplicate the finding or pre-empt an
identifier task 5 is told to grep for first. **Live gap until then:** `remove: [analysis.min_samples]`
validates clean today and plants `null` into an `int` parameter.

---

## Fail-then-pass evidence

Implementation stashed, tests run against the committed pre-task tree, then restored:

```
$ git stash push src/publishable/sweep.py src/publishable/validate.py src/publishable/cli.py
$ uv run pytest tests/test_sweep.py -q -k "ablat or override or remove_sets"
7 failed, 1 passed, 44 deselected
  FAILED test_ablate_emits_one_baseline_and_one_condition_per_removal
  FAILED test_an_ablation_is_labelled_by_its_one_change_not_by_what_it_inherited
  FAILED test_an_ablated_path_is_disambiguated_against_every_other_ablated_path
  FAILED test_ablated_paths_are_not_axis_shaped_paths
  FAILED test_override_is_the_non_boolean_one_at_a_time_form
  FAILED test_remove_sets_false_for_a_boolean_and_null_for_anything_else
  FAILED test_ablate_declares_its_conditions_in_the_order_it_writes_them

$ uv run pytest tests/test_validate.py -q -k "ablate"
16 failed, 299 deselected
  FAILED test_ablate_is_accepted_and_expands_for_real          (E-SWEEP-ABLATE-UNSUPPORTED still fired)
  FAILED test_an_ablate_override_value_is_checked_against_its_own_param
  FAILED test_an_ablate_override_path_the_template_does_not_declare_is_refused
  FAILED test_an_ablate_override_value_carrying_the_axis_separator_is_refused
  FAILED test_a_misshapen_ablate_is_refused_as_a_shape_fault[…11 cases…]
  FAILED test_every_misshapen_ablate_really_does_break_expand

$ git stash pop && uv run pytest -q
1042 passed
```

`test_an_ablate_override_path_is_unreadable_at_run_scope` (tests/test_cli.py) was written *after*
the feature commit, because mutation M8 proved it missing; its fail-then-pass is M8 below.

---

## Mutation table

Every mutation applied to the **committed** tree, reverted with `git checkout --`, with
`git status --porcelain` confirmed empty after each (lesson 3).

| # | Mutation | Test run | Observed |
|---|---|---|---|
| M1 | `ablate` **multiplies** — the changes crossed into a product (`itertools.product(*[[c, {}] for c in ablation_changes(sweep)])`) | `-k ablate_emits` | **FAILED** — 9 conditions, `assert len(conditions) == 4` |
| M2 | the baseline **re-emitted** as its own ablate row (`[{}] + ablation_changes(sweep)`) | `-k "ablate_emits or labelled_by_its_one_change"` | **FAILED** ×2 — 5 conditions, and an extra empty-bodied label before `labs=false` |
| M3 | `remove` sets **`true`** instead of `false` | `-k "ablate or remove_sets"` | **FAILED** ×4, including `values["features.demographics"] is False` |
| M4 | an ablate row labelled from its **full values** rather than its change | `-k "ablat or override_is"` | **FAILED** ×4 — `labs=false__notes=true` for `labs=false` |
| M5 | ablated paths **dropped from the labelling union** in `expand` | `-k "ablat or override_is"` | **FAILED** — `features.notes` and `clinical.notes` both label `notes=false` |
| M6 | the `override` `Param`/nameability check **deleted** | `tests/test_validate.py -k ablate` | **FAILED** ×3 |
| M7 | the `ablate.remove` **path-string** shape guard deleted | `-k misshapen_ablate` | **FAILED** ×2 (`[123]`, `[["…"]]`) |
| M8 | `ablated_paths` dropped from **cli**'s swept-path union | full suite | **PASSED (1041) — mutation survived** |

M8 is the one finding of the exercise: the cli half of the `_swept_paths` decision was untested, so
the union could be deleted with the suite green. `test_an_ablate_override_path_is_unreadable_at_run_scope`
was added (mirroring `test_a_sampled_path_is_unreadable_at_run_scope`, a real run whose `summary`
step reads an `override` path the baseline does not fix); re-applying M8 then **FAILS** it, and the
test passes on the unmutated tree. Committed separately as `9e07dd4`.

---

## What the refusal retirement touched

Mirrored task 2's `paired` retirement (`git log -S E-SWEEP-PAIRED-UNSUPPORTED` → `268f37c`), which
settles the scope question: the four documents plus code and tests; `docs/superpowers/**` are
historical records and keep their references.

- **`src/publishable/validate.py`** — the `ablate` row removed from `_check_unimplemented`'s
  refusal loop (the loop is kept, one row, for `groups`); its shared message now reads "expands
  `baseline`, `grid`, `paired`, `sample` and `ablate` only; `groups` will be honored in a later
  slice"; `E-SWEEP-KEY-UNKNOWN`'s message likewise; `_check_unimplemented`'s docstring rewritten to
  say what `ablate` now does and which of its checks are the next slice's; the
  `E-SWEEP-BASELINE-PARTIAL` comment extended with why an ablated path is deliberately absent.
- **`docs/reference.md`** — the `NOT BUILT` marker dropped from `sweep.ablate` in § The one config
  file's example, and the count sentence taken from **Twelve** to **Eleven** with `sweep.ablate`
  removed from its enumerated list. Verified by grep, not by hand-count: exactly eleven `NOT BUILT`
  markers remain in the config example (lines 79–146).
- **No § Validation registry row existed to remove** — per reference.md § The one config file, the
  `-UNSUPPORTED` family is deliberately absent from that table; confirmed by
  `grep -rn "ABLATE-UNSUPPORTED" README.md docs/*.md src/ tests/`, which now matches only the
  retirement test's own docstring and assertion.
- **`tests/test_validate.py`** — the `ablate` rows removed from
  `test_each_unimplemented_mode_is_refused_on_its_own` and
  `test_every_sweep_refusal_message_defers_rather_than_scolds`;
  `test_an_empty_or_null_mode_is_not_a_declaration` keeps `ablate: None` and still passes (a null
  mode is not a declaration).
- **`groups` stays refused.** `E-SWEEP-GROUPS-UNSUPPORTED` still fires
  (`test_each_unimplemented_mode_is_refused_on_its_own[groups]`, green).

---

## Anything questionable

1. **Retiring the refusal opened a window that only task 5 closes — the largest item here.**
   `E-SWEEP-ABLATE-UNSUPPORTED` fired on *any* truthy `ablate`, so it was also the only thing
   refusing two compositions § Expansion modes rules out. Both validate clean and expand on this
   branch now:
   - **`ablate` with no `sweep.baseline`** (§ Expansion modes: "It therefore **requires**
     `sweep.baseline`") →
     `expand({'sweep': {'ablate': {'remove': ['features.labs']}}})` gives one condition,
     `labs=None`, with no baseline row at all. `dict(baseline or {})` keeps `expand` total, which is
     right, but total here means it executes a design the spec says cannot exist.
   - **`ablate` × `grid`/`paired`/`sample`** ("no defensible reading of what it would mean") →
     baseline + the product's rows + the ablate rows. `E-SWEEP-PATH-DUPLICATE` does not catch it
     either: ablated paths deliberately do not join `named_by`, for the same reason they do not
     join `_swept_paths`.
   This is a **regression window**, not a pre-existing gap, and it is why task 5 (which owns
   § Validation rows 217 and 218) is the close of a refusal this task removed rather than optional
   cleanup. Not implemented here because minting those identifiers is task 5's step 1. Recorded in
   `spec-defects.md` § "RETIRING `E-SWEEP-ABLATE-UNSUPPORTED` OPENED A WINDOW UNTIL TASK 5 LANDS".
2. **`ablate × groups` is untestable in this slice.** § Expansion modes describes it at `(1 + n)`
   conditions per level with per-cell baselines (`00_cohort=derivation__baseline`); it needs a group
   axis and per-cell baseline expansion, which are H3's and task 6's. `groups` remains refused, so
   nothing here composes with it, and nothing here was written for it.
3. **Three value-level `ablate` faults survive both guards** — a `from` naming anything but
   `baseline` (silently ignored), an unrecognised key inside `ablate` (`removes:` → a truthy block
   yielding zero changes, so the run executes the baseline alone and reports success), and a
   **multi-key `override` entry** (one condition *two* changes from the baseline, in the mode whose
   whole contract is one change). None is a shape fault, so lesson 1 does not reach them; each needs
   an identifier or a widening of `E-SWEEP-KEY-UNKNOWN`'s documented "one of the six recognized
   sweep modes" condition, which is registry work task 5 already owns the procedure for. Recorded in
   `docs/superpowers/spec-defects.md` § "`sweep.ablate` has three value-level shapes nothing
   refuses", which the `_check_shape` comment cites.
4. **Duplicate `remove` entries produce two conditions with identical labels.** Same block, recorded
   in the same spec-defects entry. Not fixed: it is the same "a label is also a selector" class as
   the `E-SWEEP-PATH-DUPLICATE` gap, and it wants one identifier covering both.
5. **`render_value(None)` renders `None`, not `null`.** A nullable removal therefore labels
   `cutoff=None`. It matches `SWEPT_VALUE_PATTERN`, is unique, and is pre-existing behaviour shared
   with a `null` grid value — but "as written in the config" (the function's own docstring) argues
   for `null`. Left alone as out-of-scope; it touches every mode's labels, not `ablate`'s.
6. **`_check_unimplemented`'s refusal loop now has exactly one row.** Kept as a loop rather than
   collapsed to a branch, so retiring `groups` in H3 is a row deletion like this one was.


---

## Review round (spec ❌ — two Importants, two Minors), commit `<see below>`

**Important 1 — `remove` paths now get the same path check `override` paths get.** Upheld, and
fixed. `remove: [analysis.methdo]` validated with zero findings and expanded a condition planting
`null` at a path template `generic` never declared; `expand` plants a `remove` path through
`resolve_condition_cfg`'s `setdefault` walk exactly as it plants an `override` one, so my own
argument for checking `override` applied to it word for word. `_check_sweep` now runs each `remove`
entry through `_path_resolves` (`E-SWEEP-PATH-UNKNOWN`, `sweep.ablate.remove[i]`, no new
identifier), pinned by `test_an_ablate_remove_path_the_template_does_not_declare_is_refused`.
Only the **path** is checked there — what `remove` *produces* stays § Validation row 216's
question, and the comment says so.

**Important 2 — the window now has a mechanical handle in a tracked file.** Both durable records of
it (`docs/superpowers/spec-defects.md` and the SDD ledger) are gitignored, which is how this slice
already lost task 2's `paired` finding. `tests/test_validate.py` now carries
`test_ablate_without_a_baseline_is_refused` and
`test_ablate_crossed_with_a_parameter_axis_is_refused`, both
`@pytest.mark.xfail(strict=True, reason=…)`, both asserting only that `validate` reports *some*
error — no identifier, because task 5 is instructed to grep before minting one. `strict=True` makes
them fail loudly if the gap is closed without the marker being removed, so closure is watched
rather than trusted. The `ablate × grid` case fixes the grid axis in its baseline deliberately, or
`E-SWEEP-BASELINE-PARTIAL` would have made it pass for a reason unrelated to `ablate` — it did, on
the first draft, and `xfail(strict=True)` caught that as an XPASS.

**Minor 1 — the guard table's first row was wrong.** A non-mapping `ablate` does not raise:
`ablation_changes` early-returns on its `isinstance` check. The row is corrected above; the tests
were already honest about this (`test_every_misshapen_ablate_really_does_break_expand` never
claimed `"notamapping"` raises), and the validate guard still belongs, because silently ignoring a
declared block is its own fault class.

**Minor 2 — row 216's two readings, recorded for task 5.** The plan glosses row 216 as "every
`remove`/`override` path must be one the baseline fixes"; `reference.md`'s row says "`remove` needs
a boolean or nullable parameter — use `override`". Two different checks, and `ablation_changes` has
now **coupled** them by deciding `false` versus `null` from `baseline.get(path)` — so a `remove`
path the baseline does not fix silently takes the `null` reading, and skipping the
baseline-fixes-it check means a non-nullable `int` gets `null` with nothing reporting either fault.
Recorded in `spec-defects.md` § "Row 216 has two readings, and `expand` has now coupled them" so
task 5's brief inherits it. Not fixed here: both readings need that row's identifier.

**Verification.** `uv run pytest` → **1043 passed, 2 xfailed**; `uv run ruff check .` and
`uv run mypy` green; `ruff format` not run. `E-SWEEP-GROUPS-UNSUPPORTED` still fires
(`test_each_unimplemented_mode_is_refused_on_its_own[groups]`, green).

**Mutation (against the committed tree, `git status --porcelain` empty after each):**

| # | Mutation | Test run | Observed |
|---|---|---|---|
| M9 | the `remove` `_path_resolves` loop deleted | `-k "remove_path_the_template"` | **FAILED** — `StopIteration`, no `E-SWEEP-PATH-UNKNOWN` raised |
| M10 | `_path_resolves` called on `override` paths only, with `remove` gated on `isinstance(path, str) and False` | `-k "remove_path_the_template"` | **FAILED** — same |
| M11 | a stub check added that refuses `ablate` without a baseline (the gap closed, marker left behind) | `-k "ablate_without_a_baseline"` | **FAILED — `[XPASS(strict)]`**, which is the handle working: closure is caught, not silently absorbed |
| M11b | the same stub, with `strict=True` → `strict=False` | same | **xpassed, suite green** — so `strict` is the load-bearing half, not the `xfail` marker alone |
