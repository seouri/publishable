# Task 10 review: `units.holdout_for` — the unclustered draw and the column read

Reviewed: `4a44a26..30a9338` (`a6c6945` + a docs commit). Files in scope:
`src/publishable/units.py`, `tests/test_units.py`.

## Verdicts

1. **Spec compliance: ❌** — every prescribed behaviour is present and correct, but
   the plan-level Global Constraint *"every new error site is pinned by its MESSAGE,
   not only its code"* is met at **zero of six** new error sites. The one message
   assertion written is vacuous (Finding 1, proved by mutation).
2. **Task quality: ❌** — two checks that cannot fail (Findings 1 and 2), and one
   docstring guarantee the code does not provide (Finding 3). The construction
   itself is right: verified bit-identical to `assignment_for`'s `random` branch.

---

## Positive verification (parent concerns 1 and 2, both closed affirmatively)

**The pinned literals are correct, and independently so.** Rather than trusting the
literals derived by running the implementation, I checked the construction against
its sibling directly. `holdout_for(roster, {"method": "random", "frac": 0.2},
seed=1234)` over a 10-unit roster and `assignment_for(roster, "ax", {"method":
"random", "seed": 1234, "ratio": {"train": 0.8, "test": 0.2}}, ["train", "test"],
"d")` return **byte-identical membership in both sides**:

```
holdout  ('u2','u8','u3','u5','u6','u4','u9','u0')  ('u1','u7')
assign   ('u2','u8','u3','u5','u6','u4','u9','u0')  ('u1','u7')
IDENTICAL: True
```

Verified by running both in one process. This is the direct evidence for the
docstring's *"That is `assignment_for`'s `random` branch exactly"*: same
`_apportion` (through `holdout_sizes`, which is `_apportion(n, [1-frac, frac])`),
one fresh `random.Random(seed)` used for exactly one whole-roster shuffle of keys in
roster order, then consecutive slices, first side first. Read at
`src/publishable/units.py` — `assignment_for`'s unclustered branch and `holdout_for`'s
`random` branch. Both also check the zero-size refusal *before* shuffling, so the
generator is consumed identically. **No bit-stability reconciliation is owed to
task 11.**

**No helper shadowing remains.** `grep -n "^def _roster\|^def _holdout_roster"
tests/test_units.py` returns exactly two definitions at distinct names. The three
pre-existing pinned-literal tests (`test_partitions_cover_the_roster`, which pins
`u{i:03d}` at 240 units, and `test_the_unclustered_draw_is_unmoved_by_the_clustered_rewrite`,
which pins `"u018"`/`"u036"`/… at 50 units) were run by name and pass. The
implementer's disagreement with the brief was correct and correctly resolved.

**Gates, re-run clean after all my mutations were reverted:** `uv run pytest` — 1902
passed, 2 xfailed. `uv run ruff check .` — All checks passed. `uv run mypy` — Success,
42 files. `uv run ruff format --check --diff` on both touched files: I extracted every
hunk's start line and confirmed **none** falls in the new `HoldoutPlan`/`holdout_for`
region (units.py ~1274–1424) or the new test region (test_units.py ~3154–3245). The
report's unverified formatting claim is confirmed.

---

## Findings

### Critical

**None.** No incorrect output on any input `validate` admits.

### Important

**Finding 1 — the only message assertion in the task cannot fail; the
`E-DATA-HOLDOUT-EMPTY` message names the wrong side and the suite stays green.**

`test_a_holdout_that_leaves_a_side_empty_raises` asserts `empty_side in
str(exc.value)`. The message's invariant tail reads *"the trai**n**ing side has
nothing to fit on, or the **test** side has nothing to report over"* — so both
`"train"` and `"test"` are substrings of **every** instance of this message,
regardless of what `side` computed.

*Verified by mutation.* I inverted the side-naming line to
`side = "test" if train_size == 0 else "train"` (a message that names the wrong side
in both parametrizations), deleted `__pycache__`, and ran the **full** suite:
`1902 passed, 2 xfailed`. Both parametrizations of the test passed. Reverted in place
by editing the line back; revert verified by `diff` against a pre-mutation copy
(clean) **and** by re-running the function and reading the two real messages back
(`apportions the test side` / `apportions the train side`).

Fix: `assert f"apportions the {empty_side} side zero" in str(exc.value)`. That is the
smallest string carrying the discriminating word in a position the invariant tail
cannot supply.

**Finding 2 — the `E-DATA-HOLDOUT-VALUES` raise pins nothing, defeating the
three-line comment directly above it.**

The comment above the raise argues that `holdout_values_fault` "computes the verdict
AND the wording, so this raise and `validate._check_holdout`'s collected finding are
one answer rather than two wrappings of `arms_of` that drift apart." Nothing tests
the wording half of that claim:
`test_a_by_attribute_holdout_over_a_column_that_is_not_the_two_literals_raises`
asserts only `exc.value.code`.

*Verified by mutation.* I replaced `raise ContractError(fault,
code="E-DATA-HOLDOUT-VALUES")` with `raise ContractError("nonsense",
code="E-DATA-HOLDOUT-VALUES")` — discarding `fault` entirely, which is exactly the
drift the comment says is prevented — and ran the **full** suite: `1902 passed, 2
xfailed`. Reverted in place; revert verified by `diff` (clean) and by re-running the
column read and reading the real message back (`the holdout column 'split' has values
A, B over this roster …`).

Fix that cannot go stale: `assert str(exc.value) == holdout_values_fault(roster,
"split")`. That asserts the agreement the comment claims, rather than a hard-coded
literal — the `test_..._message_matches_validates` shape CLAUDE.md names, where two
messages were each compared against their own literal and nothing compared them to
each other.

**Finding 3 — the docstring's bolded "Both sides are refused empty" is false; an
out-of-range `frac` fails open and returns a plan with an empty side.**

The `random` branch guards `frac` for *type* only (`isinstance(frac, (int, float))`
and not `bool`) and cites `E-DATA-HOLDOUT-FRAC` in its refusal message — but
`validate._check_holdout` refuses **two** things under that one code: a non-numeric
`frac`, and a numeric one outside the open interval (0, 1)
(`src/publishable/validate.py`, `if not 0.0 < float(declared_frac) < 1.0`). The
draw implements only the first half. `_apportion` over a negative weight yields
negative or over-large sizes, neither of which is `== 0`, so the empty-side refusal
is bypassed.

*Verified by running* `holdout_for` over a 10-unit roster:

| `frac` | result |
|---|---|
| `-0.5` | returns a plan; `train` = 10 keys, **`test` = `()`** |
| `2.0` | returns a plan; **`train` = `()`**, `test` = 10 keys |
| `1.5` | returns a plan; 5/5 split, an arithmetic accident of `shuffled[:-5]` |
| `0.0`, `1.0` | correctly `E-DATA-HOLDOUT-EMPTY` |

This is precisely the shape the task's own reasoning exists to close: the docstring
argues the draw refuses an empty side because it "holds the realized sizes and is the
last place that can see them", and the allowlist paragraph argues fail-closed "costs
nothing" *because* `validate` refuses first — an argument that applies verbatim to
`frac`'s range and was not applied. One-line fix: widen the guard to
`or not 0.0 < float(frac) < 1.0`.

Scoped precisely, not inflated: `HoldoutPlan`'s *other* documented guarantee —
"Every key of the roster appears in exactly one of them" — **survives** at every `n`,
because `shuffled[:k] ∪ shuffled[k:]` partitions the list for any integer `k`,
including a negative or over-large one. Only the empty-side claim breaks.

**Finding 4 — `HOLDOUT_METHODS_REALIZED` and the branches it describes are pinned in
agreement by nothing.**

The tuple is read at exactly one place: the final `NotImplementedError`'s message,
which claims "the methods this build draws are …". Adding `"stratified"` to the
tuple makes that message assert this build draws a method that still raises. Verified
by `grep -n "HOLDOUT_METHODS_REALIZED" tests/*.py src/publishable/*.py` — **no test
references it at all**, and it is imported by nothing.

Note the asymmetry with its stated model: `DRAWN_ASSIGN_METHODS` *is* imported by
`validate` and *is* pinned by a test (`tests/test_units.py:1253`, `assert "adaptive"
not in DRAWN_ASSIGN_METHODS`). The cheap equivalent here is a test asserting every
member of `HOLDOUT_METHODS_REALIZED` returns a `HoldoutPlan` over a suitable roster —
which also converts the tuple from decorative into load-bearing.

**Finding 5 — four of the six new error sites have no test at all.**

Beyond Findings 1 and 2 (which have tests that under-assert), these three branches
plus the final one are reached by no test in the diff, verified by reading all six new
tests: the clustered/stratified `NotImplementedError`, the missing-`from`
`NotImplementedError`, and the unusable-`frac` `NotImplementedError`. The final
unknown-method raise is reached by
`test_an_unknown_holdout_method_raises_rather_than_falling_back` but asserts only the
exception *type*, so its message — the one that interpolates
`HOLDOUT_METHODS_REALIZED` — is unpinned (this is Finding 4's other end).

I confirmed the three untested branches behave as documented by running them
(`stratify_by: ["x"]` and `clusters={}` both raise the clustered/stratified message;
`block=None` and `block={}` both fall to the final raise). They are correct — they are
simply unpinned, and the clustered/stratified message is the one task 11 will delete,
so nothing will notice if it is deleted a task early.

The brief is what under-specified this; the implementer followed it faithfully. The
finding is still owed here, because the Global Constraint binds the task rather than
the brief.

### Minor

**Finding 6 — `plan.strata == ()` is a placeholder, not a check.** Both `return`
statements hard-code `strata=()`, and any non-empty `stratify_by` raises before
either is reached, so no non-artificial mutation can make the assertion fail. Stated
plainly for task 11's reviewer: this assertion currently proves nothing. Its sibling
`plan.seed == 1234` **is** breakable (`seed=None` or `seed + 1` in the `random`
return), and the `by_attribute` path's `assert plan.seed is None` is positively
pinned — a construction that recorded a seed there would fail
`test_a_by_attribute_holdout_reads_the_column_and_records_no_draw`. So the parent's
"is the no-seed record pinned positively?" question is **yes**; the strata question
is **no**.

**Finding 7 — `block: Mapping[str, Any] | None` is accepted and undocumented.**
`holdout_for(roster, None, seed=…)` raises `NotImplementedError` reporting
`method: None`. `assignment_for`, whose signature this copies, documents the
absent-block case explicitly ("an absent, non-mapping, or method-less block, which
`validate._check_assign` falls back to the same way" → `by_attribute`).
`holdout_for`'s docstring says nothing about it. Either the `| None` is dead weight
or it is a trap for task 13's wiring, which will hold an optional `data.units.holdout`
block and may reasonably expect the `None` case to mean "no holdout" rather than "an
unknown method". Verified by running both `None` and `{}`.

**Finding 8 — the docstring names two symbols that do not exist at this commit.**
"The derivation is `holdout_seed_for`'s, and composing them is `cli.command_run`'s"
is written in the present possessive; `grep -rn "holdout_seed_for" src/` returns only
this docstring line. It is true of the plan (tasks 12 and 13) but not of the build,
where every other forward-looking statement in this same function is marked "not
realized at this commit". This is the call-site-enumeration shape CLAUDE.md flags as
having gone stale twice in this file. Low cost to fix, low cost if left — but it
should not be left *silently*, since task 12/13 renaming `holdout_seed_for` would
leave this sentence pointing at nothing.

---

## Seam for task 11 (parent concern 3)

**The seam is sound; nothing is hard-coded that task 11 must undo, beyond one
literal.** Verified by reading the signature, the returned type, and
`assignment_for`'s realized clustered and stratified branches as the model:

- The signature already carries everything construction 2 needs: `clusters` is a
  parameter, and `strata` is derived inside from `block["stratify_by"]` through
  `stratum_names`, the same normalization `assignment_for` uses. No signature change
  is owed.
- `HoldoutPlan.strata` exists as a field and is documented for the non-empty case.
  Task 11 changes the `random` branch's `strata=()` literal to `strata=strata` and
  deletes the up-front `NotImplementedError`. That is the whole undo.
- One thing task 11 must *not* inherit: the empty-side refusal currently reads
  `holdout_sizes`' declared sizes. A clustered draw's realized sizes are not those —
  a cluster is the smallest thing that can move — so the refusal has to be restated
  per branch, exactly as `assignment_for` restates `E-DATA-ASSIGN-LEVELS` separately
  in each of its three branches. Flagged here so it is not read as already handled.
- `HOLDOUT_METHODS_REALIZED` needs no change in task 11 (the *methods* are unchanged;
  only the constructions behind them grow), which is worth saying because the tuple's
  name invites the opposite reading.

## Mutation hygiene

Two mutations run, both to `src/publishable/units.py`. A copy was taken to the
scratchpad before the first. Both were reverted **by editing the file back**, never by
`git checkout --`. Each revert was verified twice: by `diff` against the pre-mutation
copy (exit 0), and by re-running the code path and reading the restored behaviour
back. `__pycache__` was deleted before every run. The final gate run
(`pytest`/`ruff`/`mypy`, all clean) was performed after both reverts, not inherited
from the report.
