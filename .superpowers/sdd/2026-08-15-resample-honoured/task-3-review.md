# Task 3 review — Close `statistics.resample` one level in

**Range:** `d5a3a19..3c8c941` (+61/−3, `envelope.py` + `tests/test_envelope.py`)

**Spec compliance:** ✅
**Task quality:** findings — 2 Important, 2 Minor

---

## What was verified, by behaviour

The dual role is real and was exercised directly (probe against `check_envelope`, not by reading):

| Document | Result |
|---|---|
| `resample: 5` / `resample: "bootstrap"` / `resample: []` | exactly one `E-CONFIG-TYPE` at `statistics.resample`, "expected a mapping" — the three child paths short-circuit (`node = None`) rather than adding a second finding. Unchanged by this diff |
| `{method, n, stratifyy_by}` | `('E-CONFIG-KEY-UNKNOWN', 'statistics.resample.stratifyy_by', '… — did you mean `stratify_by`?')`, and nothing on the three real keys |
| `resample: null` | clean (leaf loop skips `None`; the closure recurses into `None` and returns) |
| `resample` absent | clean |
| `stratify_by: site` | clean; `stratify_by: ["site"]` clean |
| `stratify_by: 3` | `E-CONFIG-TYPE` — the task-5 backstop exists |
| `n: true` | `E-CONFIG-TYPE` (`_is_type`'s bool special-case holds through the new entry) |
| `methodd: bootstrap` | `E-CONFIG-KEY-UNKNOWN` with a `method` hint |

Spec step 3 of `2026-08-15-resample-honoured-design.md` asked for exactly `statistics.resample.{method,n,stratify_by}` in `LEAF_TYPES`, the `measurements` precedent, and **no** closed key set. That is what landed. `reference.md`'s block expansion (line ~147) documents exactly those three keys, so no legal documented key is newly refused. `stratify_by: (str, list)` agrees with `units.stratum_names`, which reads a bare string as one name.

**No documentation change is required** — checked so the next reviewer need not re-derive it: § Validation's whole-leaf list (`reference.md` line 330) names `hypotheses`/`contrasts` entries, `repeats` entries and the `from` mapping, not `resample`; the `E-CONFIG-KEY-UNKNOWN` row (line 448) names `holdout` and `from` only; line 188's "NOT BUILT" list is still true.

## Mutations run (mine, not the report's)

`__pycache__` cleared between runs; every revert done by editing in place; `git status` clean and `1694 passed, 2 xfailed` restored at the end.

| Mutation | Result |
|---|---|
| Rename `statistics.resample.stratify_by` → `MUTANT.…` | `test_the_three_resample_leaves_are_typed` FAILS (set shrinks to two) **and** `test_a_bare_string_stratify_by_is_accepted_by_the_envelope` FAILS (bare string becomes `E-CONFIG-KEY-UNKNOWN`). Typo test still passes — the closure survives on the other two children, as the task claimed |
| `(str, list)` → `list` | bare-string test FAILS with `E-CONFIG-TYPE … expected a list`. The `(str, list)` choice is pinned |
| Rename all three entries | typo test FAILS (no finding) **and** typed test FAILS — the container derivation is what produces the unknown-key finding, confirmed rather than assumed |

Baseline `1694 passed, 2 xfailed`; `ruff check` and `mypy` clean.

---

## Findings

### Important 1 — the test docstring inverts the house pattern, and task 4 will inherit it

`test_the_three_resample_leaves_are_typed`'s docstring: *"A wrong-typed child now has an `E-CONFIG-TYPE` backstop, **which is what lets `_check_resample` read each value without its own isinstance ladder**."*

The code does not provide that. `validate.py` lines 449-456 state it outright: *"Leaf faults are deliberately NOT fatal — `ok` is untouched here."* `check_envelope`'s findings are collected and validation continues, so task 4's `_check_resample` **will** be reached with `n: "many"` and `method: 3`. `n >= 80` on a `str` raises `TypeError`, which escapes as a bare traceback, not a finding.

The actual house pattern is the opposite of the docstring: every sibling site keeps a *quiet* guard that returns without reporting, with the reason spelled out — `validate.py` line 773 (`data.input_dir`), line 792 (the second `Path(input_dir)` read), line 888 and line 909 (`data.units.key`), each reading "`check_envelope` is what REPORTS this (E-CONFIG-TYPE) — this guard exists because this function may be reached without it having run: a leaf fault is deliberately non-fatal".

So the envelope entries are a *reporting* backstop (one fault, one finding, named path), not a *typing* precondition. Task 4 needs the same silent `isinstance`/`continue` guard those four sites keep. Fix the docstring to say that, since as written it tells the task-4 implementer to omit exactly the guard the codebase requires.

### Important 2 — the new block comment contradicts its sibling eight lines up

`envelope.py` line 93: *"these three names are fixed, **the block is no longer refused wholesale**, and leaving it whole would make a `stratifyy_by` typo unreachable … the moment the wholesale refusal retired"*.

At `3c8c941` the block *is* still refused wholesale: `validate.py` line 3141 fires `E-STATS-RESAMPLE-UNSUPPORTED` on any truthy `statistics.resample`. The clause is false today, and self-contradictory — it gives "no longer refused" as the reason while the same sentence describes the retirement as future. It also conflicts with the `holdout` clause in the module docstring (line 30): *"`holdout` stays whole for now: `E-DATA-HOLDOUT-UNSUPPORTED` still refuses the block, so its gap is latent"* — `resample` is in the identical state at this commit and is closed anyway.

The true statement is the stronger one: the gap is latent today, and the schema is closed **before** the refusal retires later in this slice — the design doc's own validate-before-honour ordering. One-clause fix. (This is the repo's most-repeated defect class and the specific thing the brief asked to audit; the module docstring's *other* edit — dropping `.resample` from the "declared at their own key with the one outer type" list and pointing at `measurements` — is accurate.)

### Minor 1 — the difflib hint is asserted nowhere

`test_a_misspelled_resample_key_is_reported_rather_than_ignored` destructures `for code, path, _ in findings` and drops the message. The report claims the hint; my probe confirms it fires; nothing pins it, so a degradation of `_immediate_children` would be silent here. Add `assert "did you mean \`stratify_by\`?" in message`.

### Minor 2 — the three new tests lack `-> None`

All 13 pre-existing tests in `tests/test_envelope.py` are annotated; the three added ones are not (inherited from the brief's snippet). `mypy` is scoped to `src` so nothing catches it, which is why it survived.

## A plausible task-4 mistake these tests would not catch

Beyond Important 1's crash: `resample: {}` is falsy, so `_check_unimplemented` does not fire and the envelope reports nothing — an empty block validates entirely clean today and will keep doing so unless task 4 decides it. Also unpinned here: `stratify_by: [1, 2]` (a list of non-strings) passes the envelope by design, so task 5's declared-attribute check is the only thing standing between it and a run.
