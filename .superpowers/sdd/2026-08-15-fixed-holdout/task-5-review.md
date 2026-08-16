# Task 5 review: `_check_holdout`, declaration half A

**Reviewed:** `b477297..5e3d965` (one commit, `src/publishable/validate.py` +168, `tests/test_validate.py` +97).

**Verdict 1 — Spec compliance: ✅.** `HOLDOUT_METHODS`, `_check_holdout` with the five findings in
declaration order, the empty/non-mapping gate, the wiring after `_check_fold_stratify_by`, and all
21 parametrized test rows are the brief's code. The one deviation the report declares (merging the
two-line f-string) is verified below as text-identical. Two of the findings below are inherited from
the brief rather than introduced by the implementer, and are marked as such.

**Verdict 2 — Task quality: ❌.** One test does not exercise the case its name and the brief both
demand (F1); two METHOD branches are individually deletable with a green suite because no test in
the diff asserts a message (F3); three § Errors rows disagree with emit sites and no document was
changed (F2); two comments claim what the code does not do (F4, F6); and one behaviour diverges from
the sibling convention its own comment invokes (F5).

## Verification baseline

- `uv run pytest` → **1846 passed, 2 xfailed** (matches the report). `uv run pytest
  tests/test_validate.py -k holdout` → 24 passed.
- Every mutation below was applied by rewriting the file's text in place (never `git checkout --`),
  with `__pycache__` deleted before each run, and each revert verified by **re-running** the suite
  (final revert: `24 passed`). Working tree confirmed at `5e3d965` afterwards.

### Every parametrized row is discriminated (mutations I ran)

| Rows | Mutation that makes them FAIL | Result |
|---|---|---|
| malformed 2 (`"stratified"`) | `elif method not in HOLDOUT_METHODS:` → `elif False:` | 1 failed |
| malformed 3 | FRAC-absent branch → `if False:` | 1 failed |
| malformed 4, 6 (`frac: 0`, `-0.5`) | `0.0 <` → `-1.0 <` | 2 failed |
| malformed 5, 7 (`frac: 1`, `1.5`) | brief's mutation (a), re-run by implementer | — |
| malformed 8 | FROM-absent branch → `if False:` | 1 failed |
| malformed 9 (`from: ""`) | `elif isinstance(declared_from, str) and not declared_from:` → `elif False:` | 1 failed |
| malformed 10 | by_attribute `declared_frac is not None` → `is None` | 1 failed |
| malformed 11 | random `declared_from is not None` → `is None` | 1 failed |
| malformed 12 (`stratify_by`) | `if holdout.get("stratify_by") is not None:` → `if False:` | 1 failed |
| malformed 13, 14 (seed) | `if not pinned and seed != "auto":` → `if False:` | 2 failed |
| well-formed 0–3 | random `declared_from is not None` → `is None` | 4 failed |
| well-formed 1 (`seed: "auto"`) | `seed != "auto"` → `seed != "AUTO"` | 1 failed |
| well-formed 2, 5 (`seed: 1234`) | `pinned = …` → `pinned = False` | 2 failed |
| well-formed 3 (`frac: 0.999`) | `< 1.0` → `< 0.9` | 1 failed |
| well-formed 4, 5 | by_attribute `declared_frac is not None` → `is None`; and `elif isinstance(declared_from, str) and not declared_from:` → `elif …str):` | 2 failed each |
| **malformed 0 (`method` absent)** | **none found — see F3** | see F3 |
| **malformed 1 (`method: ["random"]`)** | **none found — see F3** | see F3 |

Attribution is settled: with `_check_holdout`'s body replaced by an immediate `return`, all 15
malformed rows and `test_an_empty_or_null_holdout_validates_clean` fail (16 failed / 24), so no
expected code is arriving from `check_envelope` or `_check_unimplemented`. Note the same run left
**all 6 well-formed rows green** — see F10.

---

## Important

### F1 — `test_an_empty_or_null_holdout_validates_clean` never writes `holdout: null`

The helper omits the key rather than setting it to `None`:

```python
    if block is not None:
        units["holdout"] = block
```

**Verified by probe** (temporary test, printed and removed): `_holdout(None)` produces
`{'data.units': {'from': 'index.csv', 'key': 'patient_id'}}` — no `holdout` key at all. The second
assertion therefore pins key-absence, not the `null` case. The brief was explicit — "`holdout: {}`
and `holdout: null` therefore validate clean … **Pin it with a test**, because an implementer will
otherwise try to refuse it" — and the test's *name* and docstring both claim the `null` case. This
is CLAUDE.md's "a test whose **name** claims the guarantee", with the aggravating clause: tasks 6
and 7 extend this same function, and a reader greps for exactly this name and stops looking.

The behaviour is correct today — I probed an explicit `data.units.holdout: None` and it reports no
`E-DATA-HOLDOUT-*` code. Only the pin is missing. Fix: a sentinel for "omit" in `_holdout`, so
`None` means `null`. (Inherited from the brief's helper, which cannot express the case the brief
demanded.)

### F2 — Three § Errors rows disagree with this commit's emit sites, and no document changed

`reference.md` § Errors carries one row per code, and the diff touches no document.

1. **`E-DATA-HOLDOUT-NO-DRAW` has a third emit site the row does not name.** The row enumerates
   "`frac` under `by_attribute` … or `from` under `random`". The code adds
   `data.units.holdout.stratify_by` under `by_attribute` (tested as malformed row 12; mutation Mf
   confirms it is live). The sibling `E-DATA-ASSIGN-NO-DRAW` row names *both* its fields and states
   "One finding per offending field", so enumerating is this repo's convention. **Extend the row.**
2. **`E-DATA-HOLDOUT-FRAC`'s row claims "is not a real number".** Probe: `{"method": "random",
   "frac": "0.2"}` → `E-CONFIG-TYPE` + `E-DATA-HOLDOUT-UNSUPPORTED` only, no `-FRAC`. The code
   deliberately defers wrong types to the envelope.
3. **`E-DATA-HOLDOUT-FROM`'s row claims "is not a string".** Probe: `{"method": "by_attribute",
   "from": 3}` → `E-CONFIG-TYPE` only, no `-FROM`.

Row 477 (`-METHOD`) is *correct*: the code does absorb the non-string case there, and comments why.
Recommended direction: **extend 480, narrow 478 and 479**, since the code's type division matches
`_check_report_by`/`_check_resample` and the METHOD absorption is a reasoned exception. Verified by
`grep -n "E-DATA-HOLDOUT" docs/reference.md` and the two probes above.

### F3 — No test in the diff asserts a message, and two METHOD branches are dead to the suite

Across 11 `c.error` sites the 22 new tests assert only codes. `messages_by_code` already exists in
the same file (`tests/test_validate.py`, defined immediately below `codes`), so this is a habit the
file already has and this diff does not use. Consequence, **verified by two mutations**:

- `if method is None:` → `if False:` → **24 passed.** Row 0 (`{"frac": 0.2}`) falls through to the
  `elif not isinstance(method, str)` branch, which reports the same code at the same path with a
  different message ("is None, which names no method").
- `elif not isinstance(method, str):` → `elif False:` → **24 passed.** Row 1 (`method: ["random"]`)
  falls through to `elif method not in HOLDOUT_METHODS`.

The two branches shadow each other; code and path are identical across all three, so the message is
the only observable, and nothing observes it. Fix is one assertion per row via `messages_by_code`.

### F4 — The `validate_config` call-site comment: one half false, one half true

```python
    # Sited here for `_check_fold_stratify_by`'s reason and beside it: both read
    # the resolved roster and the usable cluster name, and both check a
    # partition's declaration rather than a repeat's. `usable_cluster` is
    # already narrowed to a non-empty string or `None` above, so this call needs
    # no guard of its own.
```

- "**both read the resolved roster and the usable cluster name**" is false at this commit and is
  contradicted by `_check_holdout`'s own docstring five lines of code away: "**None of the five
  reads `roster` or `cluster_by`**". Both parameters are unread (read the function body).
- "**both check a partition's declaration rather than a repeat's**" is false for the sibling:
  `_check_fold_stratify_by` reports `E-REPL-FOLD-STRATIFY-VARIES` under the path
  `replication.repeats`, i.e. a repeat level's declaration — and CLAUDE.md's invariants make `fold`
  one of the three repeat kinds, while `reference.md` § A fixed holdout split says a holdout is
  explicitly *not* one.
- "**`usable_cluster` is already narrowed to a non-empty string or `None` above**" **is true** —
  `validate.py` lines 595–597: `declared_cluster if isinstance(declared_cluster, str) and
  declared_cluster else None`.

The honest form is "sited beside it because tasks 6–7 will read both, and it takes them now so the
signature does not change under this caller" — which is what the docstring already says.

### F5 — `stratify_by: []` under `by_attribute` is refused, and the comment claims the opposite parity

The `stratify_by` NO-DRAW message says "The same absorption `E-DATA-ASSIGN-NO-DRAW` performs for the
same field one declaration over." It is **not** the same. The assign branch tests `stratify_by is
not None and stratify_by != []`, with a comment reading "An empty `ratio: {}` or an empty
`stratify_by: []` — what `init` writes and what most designs carry — changes no behavior and is not
this row's concern", and the § Errors row 469 states that exemption normatively. `_check_holdout`
tests bare `is not None`.

**Verified by probe:** `{"method": "by_attribute", "from": "split", "stratify_by": []}` →
`E-DATA-HOLDOUT-NO-DRAW`. The same asymmetry applies to `frac` (a `frac: 0` under `by_attribute` is
refused, which is fine, but there is no empty-value exemption at all). This is reachable by copying
`reference.md` § A fixed holdout split's own five-key block and setting `method: by_attribute`.
Either match the sibling's `!= []` exemption or drop the sentence claiming parity — and if refusing
an empty list is deliberate, the § Errors row has to say so, since its sibling says the reverse.

### F6 — The docstring's "every value read here is `isinstance`-guarded" is false for three reads

The docstring argues that a wrong-typed leaf is quietly skipped so the reader is not handed "a
second, derived fault on top of the one the reader has to fix anyway". The three presence tests in
the NO-DRAW branches carry no guard. **Verified by probe:**

- `{"method": "by_attribute", "from": "split", "stratify_by": 3}` → `E-CONFIG-TYPE` **and**
  `E-DATA-HOLDOUT-NO-DRAW`.
- `{"method": "by_attribute", "from": "split", "frac": "0.2"}` → `E-CONFIG-TYPE` **and**
  `E-DATA-HOLDOUT-NO-DRAW`.

The behaviour is defensible (a wrong-typed field that means nothing under this method is still
present, and presence is the fault) — it is the universal quantifier in the docstring that is wrong,
and this docstring is what tasks 6 and 7 will read. The `seed` double-report is **not** part of this
finding: `reference.md` row 481 documents `-SEED` firing for `"1234"` / `1.5` / `true` explicitly.

---

## Minor

### F7 — The report's `ruff format --check .` claim is false for the test file (asked about specifically)

The state of `src/` is fine; the report's wording is **not** the only problem.

- `uv run ruff format --check --diff src/publishable/validate.py` → hunks at 339, 1079, 1232, 1915,
  2173, 3655, 4026. **None inside `_check_holdout`** (2653–2820). Inherited baseline, as claimed.
- `uv run ruff format --check --diff tests/test_validate.py` → includes **two hunks at `@@ -11377`
  and `@@ -11417`**, both entirely inside lines authored by this commit (the three multi-line
  NO-DRAW parametrize rows and the `for code in (…)` tuple).

So "none of which originate from lines I authored except one" is inaccurate. Severity is minor —
the repo carries a standing 63-file baseline, so `ruff format` is plainly not enforced — but the
verification the report describes did not hold. (The lines came verbatim from the brief.)

### F8 — `HOLDOUT_METHODS`'s docstring names a function that does not exist

"a third named here and realized nowhere would validate clean and then reach `units.holdout_for`,
which refuses what it cannot draw." **Verified:** `grep -n "holdout_for" src/publishable/units.py`
→ no match at this commit. A shipped docstring asserting a runtime backstop that is not built is the
same shape as CLAUDE.md's "an unbuilt reader of a shipped surface" trap, inverted. Either mark it as
the slice's forward reference or re-check it when the draw lands.

### F9 — `doc` is unread too, and the docstring implies otherwise

"**None of the five reads `roster` or `cluster_by`**" enumerates two of the three unread parameters.
`doc` is never referenced in the body either. One word fixes it.

### F10 — The well-formed test's "positive companion" comment does not attribute to this check

"this config is not silently escaping the check entirely — the wholesale refusal still fires on the
same declaration." `E-DATA-HOLDOUT-UNSUPPORTED` is raised by `_check_unimplemented`, a different
function, and **verified by mutation**: with `_check_holdout`'s body replaced by an immediate
`return`, all six well-formed rows still pass. The assertion proves the config was validated, not
that it reached `_check_holdout`. Mitigated — every one of the six rows is killed by at least one
over-refusal mutation in the table above — so this is a comment-precision finding, not a dead test.
(Inherited from the brief.)

---

## Checked and correct

- **The merged f-string.** `f"is {method!r}, which names no method; the methods are "` +
  `f"{', '.join(HOLDOUT_METHODS)}"` and the single merged literal produce byte-identical text; code,
  path and wording unchanged. ✅
- **Diagnostic completeness.** All five codes emitted here have a `reference.md` § Errors row (477,
  478, 479, 480, 481). No code is emitted without a row. The remaining `E-DATA-HOLDOUT-*` rows
  (482–487) belong to later tasks in this slice. F2 is about row *content*, not row absence.
- **Alongside, never instead of.** Both parametrized tests assert `E-DATA-HOLDOUT-UNSUPPORTED` on
  its own line and neither asserts a total code set, so task 17/18's retirement is a one-line
  deletion. ✅
- **`_holdout`'s docstring claim** that `base_config` has no `data.units` key: verified by reading
  `base_config` — it has `data` with `input_dir`/`output_dir`/`input_manifest_policy` only. ✅
- **`usable_cluster` narrowing** at the call site: true (F4).
- **Message quality.** Every message names its path via the `path` argument and quotes the offending
  value where one exists (`{method!r}`, `{declared_frac}`, `{seed!r}`); the absence cases have no
  value to quote. The three NO-DRAW messages quote no value where the assign sibling does
  (`is {stratify_by!r}, which describes…`) — a small inconsistency, not a defect.
