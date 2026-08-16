# Task 17 review — `allocation.json` gains its fourth key

**Reviewed:** `3436b56..5eaaddb` (`feat: allocation.json records the realized holdout split`).

## Verdicts

1. **Spec compliance: ✅** — the document shape, the three-way `seed`/`strata` distinction, the widened
   gate, the key order, the hash coverage and the `provenance` pairing all match `reference.md`
   § `allocation.json` and § The other files a run writes. No `holdout_hash` was added.
2. **Task quality: ❌** — two docstrings in the two functions this task edited now claim guarantees the
   code does not provide, and neither is owned by task 19's enumerated thirteen. Both are one-paragraph
   fixes; nothing else blocks.

---

## Findings

### Important #1 — `build_allocation_document`'s return-condition paragraph is false as of this commit

`src/publishable/artifacts.py:180-183`:

```
    Returns `None` when `group_axes` is empty — no arm assignment resolved,
    matching § The other files a run writes' "present when either is
    declared": the caller writes nothing in that case rather than an empty
    file.
```

The function returns `None` only when `group_axes` is empty **and** `holdout is None`. With an empty
`group_axes` and a holdout it returns a document — which is the whole point of this task.

**Verified by:** reading the shipped gate (`if not group_axes and holdout is None:`) and by running
`build_allocation_document({}, HoldoutPlan(("P1",), ("P2",), 7, ()))`, which returns a document; the
task's own `test_the_document_is_written_when_either_partition_is_declared` asserts exactly that.

Two aggravating factors, both named in CLAUDE.md:

- It **cites the very sentence that falsifies it**. "Present when either is declared" is the contract
  this task widened the gate to honour, and the paragraph quotes it in support of the narrower rule —
  CLAUDE.md's *"citing a sentence whose job is to contrast as if it supported the claim."*
- It sits in the function the task edited, three paragraphs above the guard it changed —
  CLAUDE.md's *"when you change a guard, re-read its justification."*

**Not owned elsewhere.** Task 19's thirteen enumerated sites list `artifacts.py` once (site #5,
"**`holdout` is never written here**"), which this task correctly replaced. This paragraph is a
different sentence, is not in that table, and is not among the eight protected forward references.

**Fix:** rewrite to "Returns `None` only when neither partition resolved — `group_axes` empty and no
holdout", keeping the "writes nothing rather than an empty file" clause, which is still true.

### Important #2 — `allocation_hash`'s docstring enumerates the insertion order and is now short by one

`src/publishable/artifacts.py:315-317`:

```
    `allocation.json` is written as (that call uses `indent=2` and insertion
    order — `seed`, `arms`, `strata` — for a human reader).
```

The realized insertion order is `seed`, `arms`, `holdout`, `strata`.

**Verified by:** `list(build_allocation_document(arms, holdout).keys())` →
`['seed', 'arms', 'holdout', 'strata']`.

The surrounding argument (canonical vs. written encoding hashing differently) is untouched and remains
correct. **Confine the fix to the three-element list** — the same docstring's `holdout_hash` rule-out is
one of task 19's eight protected forward references, is still true (no `holdout_hash` exists anywhere),
and must not be converted to present tense.

### Minor #3 — the call-site wiring in `cli.py` is a live seam with no fixture, owned by task 18

**Verified by mutation:** replaced `build_allocation_document(group_axes, holdout_plan)` with
`build_allocation_document(group_axes)` in `src/publishable/cli.py:1641` and ran the full suite —
**1950 passed, 2 xfailed, all green.** Every new test in this task calls
`build_allocation_document` directly; nothing exercises the argument being passed. Reverted by copying
the pre-mutation backup back in place (never `git checkout --`), `__pycache__` cleared, revert verified
by re-running (`301 passed` across `test_artifacts.py`/`test_cli.py`).

**Owned, and not fixable here.** `E-DATA-HOLDOUT-UNSUPPORTED` is still live at this commit
(`src/publishable/validate.py:3589`), so no config can carry a holdout as far as `command_run`; tasks
13–17 had no config that could reach it. The plan's task 18 half-two names this pin verbatim: *"5. Task
17, `allocation.json`: the file exists, `provenance.allocation` and `allocation_hash` are non-`None`,
and re-canonicalizing the parsed file reproduces the hash."* Recorded here so task 18's reviewer can
confirm that pin lands and actually fails against the one-argument call.

### Minor #4 — this task's records are untracked and the workspace `.gitignore` was re-clobbered

`git ls-files` showed `task-16-{brief,report,review}.md` tracked but **no `task-17-*` file tracked**, and
`.superpowers/sdd/.gitignore` sitting at a bare `*` in the working tree — the known
`scripts/sdd-workspace`/`task-brief` clobber, which the report says it restored but which did not
survive to the commit. Under the clobbered file this review would have landed ignored too.
CLAUDE.md: *"a ledger line saying 'filed' is not a filing."*

**Action taken by this review:** restored `.superpowers/sdd/.gitignore` from `HEAD`. The task-17 report
and this review still need `git add -f` when the ledger for this task is committed.

### Informational #5 — the runner's consumer is a projection of the plan, not the plan object

`cli.py:1657-1662` hands `execute_plan` a `UnitList([u for u in roster if u.key in set(holdout_plan.train)])`
rather than the plan itself. Membership is identical and derived solely from `holdout_plan.train`, so
there is **no second draw** and task 13's `_resolved_holdout` docstring claim holds as written — it is a
claim about the partition, not about object identity. Worth stating precisely: the runner sees **roster
order**, while `allocation.json` records the **plan's** order (the shuffle's). That is task 14's code,
not this task's, and it does not affect any claim either file makes.

---

## Answers to the five directed checks

### 1. The document beat the brief — confirmed, and key order is cosmetic

`docs/reference.md` § `allocation.json` prints:

```json
{
  "seed": {"arm": 774512301},
  "arms": {...},
  "holdout": {"train": [...], "test": [...], "seed": 3310985422, "strata": ["label"]},
  "strata": {"arm": ["site", "severity"]}
}
```

— `seed`, `arms`, `holdout`, `strata`. **Verified by:** reconstructing the document's own example values
through the shipped function and printing `json.dumps(doc, indent=2)`; the output matches the fenced
example key-for-key, block-for-block, including the axis-keyed `seed`/`strata` and the holdout's own two.
The brief's literal Step 3 code would indeed have produced `seed, arms, strata, holdout`.

**Nothing load-bearing depends on the order.** `allocation_hash` canonicalizes with `sort_keys=True`, so
no digest moves; `provenance.allocation_hash` is unaffected. The only consumer is a human reading the
written file, and fidelity to the printed example is the whole value. So "the document leads" was the
right call *and* it cost nothing — but the one place the insertion order is recorded **in code** is the
`allocation_hash` docstring, which the change left stale (Important #2). That is the only follow-on.

### 2. Task 13's three consumers — all three exist, all three take the same object

**Verified independently in `src/publishable/cli.py`:**

| Consumer | Site | Takes |
|---|---|---|
| The denominators | `eval_roster = _evaluation_roster(roster, holdout_plan)` — line 1522 | the plan object |
| The runner's narrowing | `holdout_train=(UnitList([...holdout_plan.train...]))` into `execute_plan` — lines 1657-1662 | a projection of the same plan |
| `allocation.json` | `build_allocation_document(group_axes, holdout_plan)` — line 1641 | the plan object |

All three read from the single `holdout_plan = _resolved_holdout(...)` at line 1517. There is **no second
derivation and no re-draw** anywhere: `_resolved_holdout` is the only caller of `holdout_for` in the run
path. Two take the object itself; the third takes a `UnitList` built from `holdout_plan.train`'s keys —
see Informational #5. The docstring's load-bearing claim (one realization, not three answers that happen
to agree) is now true and needed no correction, as the report says.

### 3. Unit keys, never row numbers — pinned

`HoldoutPlan.train`/`.test` are typed `tuple[str, ...]` on a frozen dataclass
(`src/publishable/units.py:1249-1282`), and its own docstring states the rule with the renumbering
argument. `build_allocation_document` does `list(holdout.train)` — a copy of keys, with no roster in
scope to index into (the function takes none, deliberately). Drift to indices would be a `mypy` failure
at the `HoldoutPlan` boundary, and `uv run mypy` is clean. The new
`test_a_drawn_holdout_...` asserts literal `["P2", "P7"]` string keys.

### 4. The three-way distinction — all three arms separated, no conflation

| Arm | `HoldoutPlan` | Recorded | Test |
|---|---|---|---|
| drawn + stratified | `seed=3310985422, strata=("label",)` | `seed` and `strata` | `test_a_drawn_holdout_writes_its_own_seed_and_strata_inside_its_block` |
| drawn + unstratified | `seed=7, strata=()` | `seed`, **no** `strata` | `test_a_drawn_unstratified_holdout_records_its_seed_and_no_strata` |
| read (`by_attribute`) | `seed=None, strata=()` | **neither** | `test_a_read_holdout_records_neither_seed_nor_strata` |

Each is asserted by **exact dict equality**, so a spurious key fails it — which is what makes the middle
arm distinguishable from both neighbours rather than merely from one. `strata` is omitted on the
emptiness test (`if holdout.strata:`) and `seed` on the `is not None` test, which is the documented
split: emptiness for one, method for the other. The implementer's added mutation (d) is the right one
for the middle arm and its absence from the brief was a real gap.

The axis-keyed blocks stay present and empty: `doc["seed"] == {} and doc["strata"] == {} and
doc["arms"] == {}` is asserted on the holdout-only document, and the code still builds `seed`/`strata`
from `group_axes` alone. Nothing was repurposed — the holdout's own two live inside `document["holdout"]`.

### 5. The gate — correct in all four combinations, and nothing else keyed off the old one

`if not group_axes and holdout is None: return None`. The four combinations are asserted by
`test_the_document_is_written_when_either_partition_is_declared`, and neither→`None` is additionally
pinned end-to-end at `tests/test_cli.py:7743` (`assert not (doc["run_dir"] / "allocation.json").exists()`
plus both `provenance` fields `None`) and at `tests/test_cli.py:1749`.

**Nothing else keyed off the old gate.** `build_allocation_document` has exactly one production call
site (`cli.py:1641`), found by grepping `src/` and `tests/`. The downstream `provenance` fields follow
`alloc_doc`, not `group_axes` — **verified at `cli.py:1642-1645` and `cli.py:2642-2643`**:

```python
"allocation": "allocation.json" if alloc_doc is not None else None,
"allocation_hash": alloc_hash,          # set only inside `if alloc_doc is not None:`
```

so a holdout-only run records both rather than writing the file and denying it in `run.yaml`. The
brief's "provenance follows for free" claim is true, and the comment at that site already reads "when an
arm assignment **or a holdout** is declared" — as does `reference.md`'s `run.yaml` example comment
(line 621-622). No stale sibling found.

---

## Check (a): every new test, its mutation, and what was verified

Five tests, five single-line mutations, all five demonstrated to fail:

| Test | Single-line mutation that fails it | Run by |
|---|---|---|
| `..._writes_its_own_seed_and_strata_inside_its_block` | swap `block["train"]`/`block["test"]` to `list(holdout.test)`/`list(holdout.train)` | implementer (c); **also by me** via #6 below |
| `..._read_holdout_records_neither_seed_nor_strata` | `block["seed"] = holdout.seed` unconditionally | implementer (b) |
| `..._drawn_unstratified_holdout_records_its_seed_and_no_strata` | `block["strata"] = list(holdout.strata)` unconditionally | implementer (d) |
| `..._document_is_written_when_either_partition_is_declared` | gate back to `if not group_axes:` | implementer (a) |
| `..._allocation_hash_covers_the_holdout_block` | `document["holdout"] = block` → `pass` | **verified by me** |

**Mutation I ran myself:** replacing `document["holdout"] = block` with `pass` in
`src/publishable/artifacts.py`. All **five** new tests failed, including the hash inequality
(`sha256:0aeb83… != sha256:0aeb83…`, both documents reduced to `{'seed': {}, 'arms': {}, 'strata': {}}`).
That is the direct proof the coverage claim is not empty: the holdout block genuinely enters the
canonical JSON that `allocation_hash` digests. Reverted by copying the backup back in place, cache
cleared, revert verified by re-running (`101 passed`).

I also ran the `cli.py` call-site mutation — see Minor #3.

**Mutation (c)'s framing is correct as the brief states it and as the implementer reports it.** A hash
over `{"train": A, "test": B}` versus `{"train": B, "test": A}` cannot see a swap applied to *both*
documents, so the inequality surviving while the membership assertion fails is the intended pair of
outcomes and evidence the explicit assertion is doing work the hash cannot. Not a weakness.

## Check (b): comments and docstrings

Both **replacements** the task made are true and neither overclaims:

- `artifacts.py`'s "**`holdout` is the fourth key, and it is self-contained**" — verified against the
  shipped payload: `train`/`test` always, `seed` gated on `is not None`, `strata` gated on truthiness,
  both inside `document["holdout"]`. The "this function still takes no roster" clause is true (the
  signature has none). No claim about task 18 is made.
- `cli.py`'s replacement — "`None` only when NEITHER partition resolved … `holdout_plan` is
  `_resolved_holdout`'s single realization, the same object the runner narrowed and the denominators
  counted against" — verified against all three consumers (check 2). The "same object" phrasing is
  accurate for the two direct consumers and accurate about *membership* for the third.
- The extended `if not group_axes:` gate comment ("`holdout` carries no such shape hazard: it reaches
  this function already realized … a single call with no per-condition narrowing beside it to compare
  against") is true — `_resolved_holdout` has one call site and there is no per-condition holdout.

Two docstrings the task **did not** revisit are now false: Important #1 and #2.

## Check (c): the documents

- `reference.md` § `allocation.json` already describes the fourth key with the printed example, the
  self-contained-block paragraph, and the `by_attribute`-carries-neither rule — settled in task 2, and
  the implementation now matches it exactly. **No edit was owed and none was made.** Correct.
- **No diagnostic changed.** `E-DATA-HOLDOUT-UNSUPPORTED` is untouched and still live, so § Errors is
  unaffected.
- **No `holdout_hash` was added.** Grepped `src/`, `docs/`, `tests/`: the only occurrences in `src/` are
  `allocation_hash`'s own rule-out (a protected forward reference) and `reference.md`'s "There is no
  `holdout_hash`; `provenance.allocation_hash` covers this file whole." The hash genuinely covers the new
  block — proved by the `document["holdout"] = block` → `pass` mutation above.

## Suite state at review time

`uv run pytest` — **1950 passed, 2 xfailed** on the unmutated tree, and again after every revert. Working
tree returned to the reviewed commit's content (`src/publishable/artifacts.py` and
`src/publishable/cli.py` restored from pre-mutation backups, verified by re-running rather than by
`git status`); `.superpowers/sdd/.gitignore` restored from `HEAD`.
