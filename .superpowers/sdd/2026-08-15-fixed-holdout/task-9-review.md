# Task 9 review — `units._holdout_constant_column`

Reviewed `review-8cbba42..08351ff.diff` (commits `bf27897`, `08351ff`) against `task-9-brief.md`,
`task-9-report.md`, `CLAUDE.md`, and `task-8-review.md`.

Every mutation was reverted by copying back a scratchpad backup of `src/publishable/units.py` — **no
`git checkout --` on any source file** — `__pycache__` deleted before each run, and each revert
verified by **re-running** `tests/test_units.py` (176 passed) plus `git diff --stat`, not by
`git status` alone. Measured myself at `08351ff`: `uv run pytest` → **1891 passed, 2 xfailed**;
`uv run ruff check .` clean; `uv run mypy` clean (42 source files). Working tree clean afterwards.

`.superpowers/sdd/.gitignore` was found clobbered to a bare `*` **again** (after task 9's own commit)
and restored from `HEAD`.

## Verdicts

1. **Spec compliance: ✅** — Steps 1–5 are present, and every prescribed edit is the brief's text.
   The accessor, the `"holdout"` registry entry, the `resolve_units` insertion point and comment, the
   two rewritten "not reachable" passages, and the `validate.py` sentence all match the brief
   verbatim or near-verbatim. Step 5(a) reproduces. Step 5(b)'s prescribed mutation is genuinely dead
   and the implementer's replacement test is genuinely live — **I reproduced both** (finding 0).
2. **Task quality: ❌** — one narrow, fixable defect, but it is exactly the class this task was
   dispatched to be careful about. Adding `"holdout"` as a key of `CONSTANT_COLUMN_RULES` opened a
   **second** route into the registry — `resolve_units`' flat comprehension, which iterates
   `for declaration in CONSTANT_COLUMN_RULES` and admits a **string-valued** `data.units.holdout`.
   That route emits `E-DATA-HOLDOUT-VARIES` with a message spelling (`data.units.holdout`, no
   `.from`) that no § Errors row covers and no test pins, and it falsifies three sentences this diff
   itself wrote (finding 1). Three further document/comment claims added or left by this diff are
   false or stale (findings 2, 3, 4). The core behaviour — the accessor, the gate, the ordering — is
   correct and now properly attributed by mutation. **To be clear about what finding 1 is and is
   not**: the runtime behaviour is not broken — a string `holdout` over a varying column is still
   refused, the config still fails, no user gets a wrong answer. The defect is that three sentences
   this diff wrote describe a route they deny exists, and that the message the second route emits is
   covered by no § Errors row and pinned by no test.

---

## 0. Verified: the brief's mutation (b) is dead, and the replacement is live

**Run by me.** Moved `constant.update(_holdout_constant_column(units_decl.get("holdout")))` to after
the flat-pair `constant.update({...})` block, deleted `__pycache__`, ran
`uv run pytest tests/test_units.py -k "holdout_rule or resolve_units_checks_holdout"`:

```
FAILED tests/test_units.py::test_resolve_units_checks_holdout_after_assign_and_before_cluster
E  AssertionError: assert 'E-DATA-CLUSTER-VARIES' == 'E-DATA-HOLDOUT-VARIES'   (second assertion)
1 failed, 1 passed, 174 deselected
```

The `1 passed` is `test_the_holdout_rule_is_checked_after_assign_and_before_the_flat_pair` — the
brief's own test, unaffected, exactly as the report says. Reverted from the backup; re-ran
`tests/test_units.py` → 176 passed; `git diff --stat src/publishable/units.py` empty.

So the report's disagreement is **correct and correctly diagnosed**: the brief's test builds its
`constant` dict in the test body and never calls `resolve_units`, so it can only prove
`collapse_measurements` stops at the first key of whatever dict it is handed. The implementer found
this by running the mutation rather than by trusting the brief, closed the gap with a real
`resolve_units` test placed beside the existing precedent
(`test_one_column_named_by_both_cluster_and_arm_reports_exactly_one_code`), and verified the
replacement discriminates. That is the behaviour this repo asks for; it is the best part of the task.

---

## Findings

### 1. Important — `"holdout"` in the registry opens a second, undocumented route: a bare-string `data.units.holdout`

`resolve_units`' flat comprehension is `for declaration in CONSTANT_COLUMN_RULES if
isinstance(units_decl.get(declaration), str) and units_decl[declaration]`. Before this diff the
registry had no `holdout` key, so that loop never looked at `units_decl["holdout"]`. It does now, and
the `isinstance(..., str)` filter — which correctly drops the *mapping* form — **admits the string
form**.

**Verified by probe, twice.**

Direct `resolve_units` call with `data.units.holdout: "split"` over a `split` column that varies
within `p1`'s two measurement rows:

```
CODE: E-DATA-HOLDOUT-VARIES
MSG:  `data.units.holdout` names 'split', which unit 'p1' declares more than one value for across
      its measurement rows (train, test) — …
```

And reachable through `validate_config` (throwaway test using `test_validate.write_config` /
`messages_by_code`, since deleted): codes `['E-CONFIG-TYPE', 'E-DATA-HOLDOUT-UNSUPPORTED',
'E-DATA-HOLDOUT-VARIES']` — so validation does continue past `E-CONFIG-TYPE` (task 8's review
established the same) and a user sees this message.

There is no crash risk — `any(v != values[0] for v in values)` never evaluates `values[0]` on an
empty list, so a string naming a nonexistent column is inert. The defect is what it says, and what
this diff says about it:

- **A message spelling no § Errors row covers.** `reference.md` § Errors (Errors core raises) reads
  "the column `data.units.holdout.**from**` names is not constant …". The emitted path here is
  `data.units.holdout`. CLAUDE.md: § Errors carries one row per code covering **every emit site**;
  the plan-level Global Constraint is that a new error site is pinned **by its message**. Nothing in
  the 1891 tests asserts this message or this path.
- **The registry docstring this diff wrote is falsified by it.** "**`holdout.from` reaches this
  registry through its own accessor**, `_holdout_constant_column` below … it could not be a flat
  entry either: `resolve_units`' comprehension filters on `isinstance(..., str)` and drops a mapping
  before the registry is consulted." It *is* also a flat entry, for the non-mapping value.
- **`validate.py`'s new sentence is falsified by it** — in the file this task was specifically told
  to sweep because it falsified the old one: "the three that ARE read — `cluster_by`, `weight_by`,
  and (**under `by_attribute`**) `holdout.from`". A bare-string `holdout` is neither `by_attribute`
  nor `holdout.from`, and is read.
- **The accessor's docstring** ("An absent block, a **non-mapping block**, … are shapes … this
  function is silent on") is true of the function and misleading about the declaration: the
  declaration is not silent, the registry entry answers for it.

This also differs from the divergence task 8's review accepted. There the second finding was about a
**different declaration pair**; here it is a second substantive verdict about **the same value**
`E-CONFIG-TYPE` has already refused, computed by treating a mis-typed scalar as a column name — the
shape task 7's review objected to for `E-DATA-HOLDOUT-EMPTY`.

**Remedy, one of two, both one line plus a sentence.** Either exclude `holdout` from the flat
comprehension (`if declaration != "holdout"`, with the reason: `holdout` reaches the registry only
through its accessor, so a mis-typed scalar stays `E-CONFIG-TYPE`'s alone) and pin it with a test
asserting `E-DATA-HOLDOUT-VARIES` is **not** raised for a string `holdout`; or accept the second
route deliberately — in which case the § Errors row, the registry docstring and `validate.py`'s
sentence must all say so, and the message must be pinned by a test.

### 2. Important — § Errors does not record that `validate` reports `E-DATA-HOLDOUT-VARIES`, while its three siblings are explicitly dual-listed

**Verified by probe** (mapping form, the intended path — `holdout: {method: by_attribute, from:
split}` over a varying `split`, through `validate_config`):

```
CODES: ['E-DATA-HOLDOUT-UNSUPPORTED', 'E-DATA-HOLDOUT-VARIES']
MSG:   `data.units.holdout.from` names 'split', which unit 'p1' declares more than one value for …
```

So `validate` reports this code today, through the resolution it already performs. **Verified by
grep** (`grep -rn "HOLDOUT-VARIES" docs/*.md`): the code appears in `reference.md` **once**, in
§ Errors *Errors core raises*. Its row says only "raised where they are raised: at run time, by
`resolve_units`". The sibling row directly above it — the one covering `E-DATA-CLUSTER-VARIES`,
`E-DATA-WEIGHT-VARIES`, `E-DATA-ASSIGN-VARIES` — ends "all three are also
[reported by `validate`](#errors-validate-reports) under the same codes, reaching it through the
resolution it performs", and each of those three additionally carries a row in *Errors `validate`
reports*. `E-DATA-HOLDOUT-VARIES` carries neither.

The row was minted by task 1, before there was an emit site; this task is the one that made the
validate surface real, so it is this task's row to complete. One clause on the existing row, or the
sibling row's dual listing.

### 3. Important — the "Four codes" docstring cites a section that does not state the rule

The rewritten `CONSTANT_COLUMN_RULES` docstring asserts: "`reference.md` § Clustered units,
§ Weighted samples, § Allocation **and § A fixed holdout split** state the same rule about four
different columns".

**Verified by reading the whole section** (`sed -n '/^### A fixed holdout split/,/^### /p'` then
grepping it for `measurement rows`, `VARIES`, `constant`): the only constancy sentence there is
"**Whole clusters go to one side** … and `stratify_by` must be constant **within a cluster**" — a
different rule about a different field. § Clustered units, § Weighted samples and § Allocation each
*do* carry the measurement-row constancy paragraph the docstring describes (`reference.md`
§ Clustered units "A cluster must not vary within a unit's measurement rows", § Weighted samples "a
weight must not vary…", § Allocation "Under `method: by_attribute`, `assign.<axis>.from` must not
vary…"). The fourth section carries no such paragraph — only § Errors does.

The honest fix is either to add the parallel paragraph to § A fixed holdout split (which is what the
other three have, and would make the docstring true as written) or to cite § Errors for the fourth.
The rest of the rewrite is sound: **verified by reading both registry messages**, `cluster_by`'s says
"it decides which side of a train/test split the unit lands on" and `holdout`'s says "decides which
side of a train/test split the unit lands on" — the carve-out's claim that the two say the *same*
thing about the damage is accurate, and the other three still each say a different thing.

### 4. Important — `collapse_measurements`' docstring enumerates the `constant` key shapes and was not updated

Its second paragraph: "A key is either a bare entry of `CONSTANT_COLUMN_RULES` (`cluster_by`,
`weight_by`) or a dotted `assign.<axis>.from` — one per declared axis, built by
`_assign_constant_columns`". **Verified by reading** — this diff adds a third shape,
`holdout.from` built by `_holdout_constant_column`, and the enumeration in the very function that
consumes it still says "either … or". This is the docstring-enumeration-goes-stale class CLAUDE.md
records twice for this file (`stratum_names`' call-site count, still filed open in
`docs/superpowers/spec-defects.md`; `stratum_varies_within_cluster`, corrected in task 7). One clause.

### 5. Minor — the brief's own test's name and docstring claim the guarantee finding 0 proves it does not make

`test_the_holdout_rule_is_checked_after_assign_and_before_the_flat_pair` — the name says "is checked
after assign and before the flat pair" and the docstring says "Pinned as an order rather than left to
dict-building accident". Neither is true of what it asserts (finding 0's mutation: it passes with the
order reversed). This is CLAUDE.md's documented defect verbatim — "a test whose **name** claims the
guarantee … a reader greps for exactly that name and stops looking" — and the implementer's companion
explains the distinction only in *its* docstring, which nobody grepping the ordering name will reach.

The property it *does* pin — `collapse_measurements` stops at the first entry of the mapping it is
handed — is real and already covered from the other end by
`test_one_column_named_by_both_cluster_and_arm_reports_exactly_one_code` (`resolve_units`) and
`test_the_three_codes_are_not_one_code_and_none_excludes_another` (per-declaration). **Recommend
rename, not deletion** — e.g.
`test_collapse_stops_at_the_first_entry_of_the_constant_mapping_it_is_given` — with the docstring's
"Pinned as an order" clause replaced by a pointer to
`test_resolve_units_checks_holdout_after_assign_and_before_cluster`, which is where the ordering
guarantee actually lives.

### 6. Minor — three of the eight parametrize rows are killed by no mutation

Kill table, **every row verified by a mutation I ran** (`-k holdout_accessor`, reverted from backup
and re-run each time):

| Row | Single-line mutation that kills it | Result |
|---|---|---|
| `absent` (`None`), `not a mapping` (`"nonsense"`) | delete `if not isinstance(holdout_decl, dict): return {}` | **2 failed**, 6 passed |
| `random with a stray from` | delete the `method != "by_attribute"` gate (brief's 5(a)) | **1 failed** (`…[random with a stray from]`), 7 passed — run by me, not taken from the report |
| `non-string from` (`7`) | `if isinstance(declared_from, str) and declared_from:` → `if declared_from:` | **1 failed**, 7 passed |
| `empty from` (`""`) | same line → `if isinstance(declared_from, str):` | **1 failed**, 7 passed |
| `empty` (`{}`), `by_attribute with no from`, `random` | **none found** | survive all four mutations |

The last three all lack a `from`, so they return `{}` under every mutation of every guard — they are
documentation rows, not checks. Minor rather than Important because the positive path *is* pinned:
`test_a_holdout_from_column_varying_within_a_unit_is_refused` asserts
`constant == {"holdout.from": "split"}` and `test_a_constant_holdout_from_column_collapses_cleanly`
asserts the clean collapse, so "a function returning `{}` unconditionally" cannot satisfy this file.
Recorded so it is not re-derived.

### 7. Minor — `resolve_units`' pre-existing comment still says "the worst of the three"

Two lines above the new comment: "`assign` is documented as the worst of the three (§ Allocation: …
where **cluster/weight only** decide which side of a split it lands on or what it stands for)". The
registry docstring three hundred lines away was updated from "Three codes" to "Four codes" in this
same diff; this enumeration was not. Not false about `assign` (it is worse than all three others),
but the count and the "cluster/weight" list now exclude a member of the family the very next comment
adds. **Verified by reading** `src/publishable/units.py` § `resolve_units`' `measurements` block.

### 8. Minor — the `E-DATA-ASSIGN-VARIES` row's precedence enumeration now under-enumerates, and the holdout↔cluster order is stated in code only

**Verified by grep** of `docs/reference.md`: the `E-DATA-ASSIGN-VARIES` row says "a single unit
violating more than one gets exactly one code, from whichever declaration's entry is checked first —
`assign`, ahead of `cluster_by`/`weight_by`, matching the severity this row states". `assign` is now
also ahead of `holdout`; the sentence is not false, but it is the enumeration a reader consults for
the precedence and it omits the member this task added. Correspondingly, the holdout-before-cluster
order is asserted **only** in the new code comment — no document states it — which is the same
"precedence rule nothing in the documents states" the registry docstring warns against, one
declaration over. The comment is careful to say it is a determinism choice and not a severity claim,
so this is a documentation completeness note rather than a contradiction; a clause on the
`E-DATA-HOLDOUT-VARIES` row would settle it alongside finding 2.

### 9. Note, no finding — Step 4's sweep, re-run by me

- `grep -rn "not read by" src/publishable/*.py` → one hit, the corrected `validate.py` sentence
  (which finding 1 shows is now wrong for a different reason).
- `grep -rn "holdout.from" src/publishable/*.py | grep -i "not reach\|unreachable\|still is not"` →
  **no hits**: every present-tense unreachability claim is gone from `src/`.
- Sweep-can-fail check: `grep -rln "_holdout_constant_column" src/publishable/*.py` returns
  `units.py`, so the pattern does match when the string is present.
- The historical quotes surviving in `docs/superpowers/` are the tracked development record, which
  CLAUDE.md forbids retro-editing. Correctly left alone.

### 10. Note, no finding — report accuracy

Every claim in `task-9-report.md` that I checked holds: mutation (a)'s and (b)'s outcomes, the
reverts, the suite counts (1891 passed / 2 xfailed at `08351ff`, measured myself), `ruff check` and
`mypy` clean, and the § Errors row for `E-DATA-HOLDOUT-VARIES` pre-existing from task 1. The one
thing the report's last line understates is that the § Errors row "already described exactly what
this task's emit site does" — it describes the `holdout.from` site (findings 1 and 2 are the two
halves it does not describe). `git checkout` was used on `.superpowers/sdd/.gitignore` only, which is
restoring a tracked file rather than reverting a mutation, and is what CLAUDE.md asks for.

---

## Mutation ledger

| Mutation | File | Result |
|---|---|---|
| move `constant.update(_holdout_constant_column(...))` after the flat pair | `units.py` | `test_resolve_units_checks_holdout_after_assign_and_before_cluster` **FAILED** on its second assertion; the brief's `..._before_the_flat_pair` test **passed** → finding 0, finding 5 |
| delete `if not isinstance(holdout_decl, dict): return {}` | `units.py` | rows `absent`, `not a mapping` **failed** |
| `if isinstance(declared_from, str) and declared_from:` → `if declared_from:` | `units.py` | row `non-string from` **failed** |
| same line → `if isinstance(declared_from, str):` | `units.py` | row `empty from` **failed** |

| Probe | Result |
|---|---|
| `resolve_units` with `holdout: "split"` (bare string) | `E-DATA-HOLDOUT-VARIES`, message path `data.units.holdout` → finding 1 |
| `validate_config` with `holdout: "split"` | `['E-CONFIG-TYPE', 'E-DATA-HOLDOUT-UNSUPPORTED', 'E-DATA-HOLDOUT-VARIES']` → finding 1 |
| `validate_config` with `holdout: {method: by_attribute, from: split}` | `['E-DATA-HOLDOUT-UNSUPPORTED', 'E-DATA-HOLDOUT-VARIES']`, path `data.units.holdout.from` → finding 2 |

Every mutation reverted by copying back the scratchpad backup and verified by re-running
`tests/test_units.py` (176 passed) and `git diff --stat`. Probe test files deleted. Final state:
`uv run pytest` 1891 passed / 2 xfailed, `ruff check` clean, `mypy` clean, `git status` clean.
