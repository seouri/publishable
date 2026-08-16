# Task 13 review: `cli._resolved_holdout` — realize the holdout once

Reviewed `review-c01cf3e..6c328a6.diff` against `task-13-brief.md`, `task-13-report.md`,
`CLAUDE.md`, and the code at this commit.

## Verdicts

1. **Spec compliance — ✅**
2. **Task quality — ✅**

No Critical findings. One Important, four Minor.

---

## The four required checks

### 1. The digest is `design_digest(doc)`, verified independently

**Verified by reading, not by trusting the report.** `grep -n "^\s*digest\s*=" src/publishable/cli.py`
returns exactly one assignment inside `command_run`: `cli.py:1246`,
`digest = design_digest(doc)  # phase 5: pin hashes`. The only other `digest` occurrences in the
file are the two helper *parameters* (`cli.py:317`, `cli.py:458`) and keyword passes
(`digest=digest` at 1588). Nothing rebinds the local between 1246 and the holdout call at 1463 —
no reassignment, no `for digest in ...`, no nested-scope shadow. The same local is consumed by
`resolve_repeats` (1350), `partition_units` (1426) and `_resolved_group_axes` (1458). Task 12's
reviewer's question is settled: **the digest passed is `design_digest(doc)`, not a neighbour.**

### 2. Sited once, outside every loop — settled by reading

`command_run` begins at `cli.py:1220`; the realization is at `cli.py:1463`, at **indent 4**, i.e.
the function body's own statement level. Its neighbours at the same indent are
`conditions = expand(doc)` (1430), `group_axes = _resolved_group_axes(...)` (1458) and
`arm_members_map = ...` (1466). `grep -n "^    for \|^    while " src/publishable/cli.py` over
lines 1220–1750 returns **nothing**, and any enclosing `if` would have put the statement at indent
8 — so the call is inside no loop over conditions, arms, repeats or metrics, and inside no
conditional. Ordering also matches the brief: `build_allocation_document` is called at 1576 and
`execute_plan` at 1582, both after it.

Production call sites, greped: `_resolved_holdout` is defined once (455) and called once (1463);
`holdout_for`/`holdout_seed_for` appear in production at exactly one place, inside
`_resolved_holdout` (494–495). **One realization, one composition.**

### 3. No raise is swallowed

`_resolved_holdout`'s body is five lines and contains **no `try`, no `except`, no
`contextlib.suppress`, no defensive `getattr`/`.get` around the call**. The two early returns are
shape gates on the *declaration* (`roster is None`; non-dict or empty `block`), not fault
absorbers. `holdout_for`'s `ContractError`/`E-DATA-HOLDOUT-EMPTY` and its final
`NotImplementedError` (`units.py:1498`) propagate to `command_run`'s caller unchanged — verified
empirically by mutation (a) below, where the `NotImplementedError` surfaced through
`_resolved_holdout` untouched.

### 4. Gate agreement with `validate`

`_resolved_holdout`'s gate is `if not isinstance(block, dict) or not block: return None`. That is
**character-for-character `_check_holdout`'s own gate** (`validate.py:2740-2741`), the check that
owns every holdout finding. The two bare-truthiness sites diverge only on one shape: a **truthy
non-dict** `holdout` (`holdout: random`, `holdout: [ ... ]`, `holdout: 1`) — declared to
`_check_unimplemented` (`validate.py:3583`) and `_check_evaluation_split_cells`
(`validate.py:3072`), undeclared to `_check_holdout` and to this function.

That shape **cannot reach a run**: `envelope.py:90` declares `"data.units.holdout": dict`, so a
non-mapping value becomes an `E-CONFIG-TYPE` finding (`envelope.py:337-343`). **The routing was
checked, not assumed** — `validate.py:458-459` consumes `check_envelope`'s findings as
`c.error(code, field, message)`. The surrounding comment's "leaf faults are deliberately NOT
fatal" means only that `ok` is left untouched so later checks still run; the finding is still an
**error**, so `validate` exits nonzero and `command_run` returns before the holdout is realized. So the divergence is inert both today and after task 18
retires `E-DATA-HOLDOUT-UNSUPPORTED`. `holdout: {}` and `holdout: null` are falsy under **all
three** predicates, so the empty-block reading is unanimous. **No shape is drawn-on by one gate
and validated-as-absent by the other.**

---

## Findings

### Important

**I1 — The docstring and call-site comment state present-tense wiring that does not exist at this
commit.** `_resolved_holdout`'s docstring: *"The one object handed to the runner's narrowing, to
the denominators, and to `build_allocation_document`."* The call-site comment: *"the runner's
narrowing, the denominators and `allocation.json` are all handed this one object."* **Verified**
by grepping the tree: `holdout_plan` has exactly one occurrence in `src/` — its own assignment,
carrying `# noqa: F841 -- consumed starting task 14`. Nothing is handed it. This is the repo's
most-repeated habit (CLAUDE.md § Habits that cost real work: *a comment claiming a guarantee the
code does not provide*), and the two sentences are the strongest form of it: they name three
consumers, none of which exists.

**This finding does NOT block task 13.** Reason stated rather than implied: the wording is
verbatim from the brief, the horizon is named three tokens away by the `noqa`, and tasks 14–17
make every clause true inside this slice. It converts into one obligation on task 17's reviewer,
written below.

Mitigating, and why this is Important rather than Critical: the `noqa` comment on the very next
token names the horizon (`consumed starting task 14`), the claims become true within this same
slice at tasks 14–17, and the wording was prescribed verbatim by the brief — the implementer
followed instructions rather than inventing a claim. **The obligation this creates:** if any of
tasks 14–17 is cut or descoped, these two passages become false claims nobody owns. A reviewer of
task 17 should re-read both and confirm each of the three named consumers exists.

### Minor

**M1 — "`_check_units` has already reported why" describes a case that cannot occur.** The
docstring justifies the `roster is None` guard with *"there is nothing to partition, and
`_check_units` has already reported why."* **Verified:** `cli.py:1257-1259` resolves the roster as
`resolve_units(units_decl, input_dir) if units_decl else (None, None, frozenset())`, and
`resolve_units` (`units.py:266-268`) returns a `UnitList`, never `None`. So `roster is None`
implies `units_decl` is falsy, which implies `(units_decl or {}).get("holdout")` is `None` — and
in that shape `_check_units` reported **nothing**, because nothing was wrong. The guard is
correct and defensive (the same posture `command_run`'s fold guard takes at 1365), but its stated
reason attributes a diagnostic to a shape that emits none. A truthful version would say the branch
is unreachable with a declared holdout and exists so a future caller cannot get it wrong.

**M2 — mutation (a) fails by a raise, not by the assertion; judged acceptable, no stronger form
exists.** I re-ran it myself (edit in place, `uv run pytest -k holdout_is_realized_once`): FAILED
with `NotImplementedError: data.units.holdout.method: None is not realized here`, exactly as
reported. Reverted by editing the file back, `__pycache__` deleted, revert verified by **re-running**
(`5 passed`) and by `diff` against a pre-mutation copy (`IDENTICAL`) — never `git checkout --`.
Judgement: the crash **is** the behavioural difference the guard prevents, because there is no
input for which an empty block yields a *plan* rather than a raise. Asking the test to distinguish
"wrong return value" from "crash" would be asking it to distinguish two readings only one of which
can exist. Same judgement for mutation (d): with the `roster is None` guard gone, `holdout_seed_for`
iterates `None` inside `units_hash` before any plan could be built, so `TypeError` is the only
possible alternative to `None`. Both tests discriminate; neither should be rewritten.

**M3 — the new test code is not `ruff format`-clean, adding to the file's pre-existing drift.**
`uv run ruff format --diff tests/test_cli.py` reports the new `_cli_roster` body and the
`_resolved_holdout(...)` multi-line call among its hunks. The brief supplied that text verbatim and
the file already drifts, so this changes nothing about the baseline verdict — but the added lines
are new drift, not inherited drift. `uv run ruff check .` is clean, and `uv run mypy` per the
report.

**M4 — the report cites `cli.py` line 1199 for the digest; the assignment is at line 1246.** A
line-number citation is what CLAUDE.md § Documentation conventions asks records to avoid for
exactly this reason. The substantive claim is right; only the coordinate is stale.

---

## Every test, with the single-line mutation that kills it

| Test | Killing mutation | Status |
|---|---|---|
| `test_the_holdout_is_realized_once_and_returns_none_when_undeclared` | `if not isinstance(block, dict) or not block:` → `if not isinstance(block, dict):` | **Run by me** — FAILS (see M2) |
| same, roster arm | delete `if roster is None: return None` | reported (d) — FAILS via `TypeError` in `units_hash` |
| `test_the_realized_holdout_uses_the_derived_seed_and_the_cluster_map` | drop `clusters=clusters` from the `holdout_for` call | reported (b) — FAILS on the clustered equality **and** on the `set(clustered.test) != set(plan.test)` companion |
| `test_a_pinned_holdout_seed_reaches_the_realization` | strip `seed` from the block handed to `holdout_seed_for` | reported (c) — FAILS `plan.seed == 4321` |

The two brief-mandated mutations plus two of the implementer's own were run; the implementer also
checked mutation (c)'s **blindness claim** by re-running the other two tests under it (both passed),
which is the right way to substantiate a docstring that says "would pass every other assertion".

**What no test in this slice can catch, and I settled by reading instead:** that the realization is
sited once and outside every loop (check 2 above). A realization inside a per-condition loop would
be behaviourally invisible — same seed, same roster, same partition — so task 18's pin would pass
over a defect. Read and confirmed clean.

**Not a finding:** the absence of an end-to-end test. `E-DATA-HOLDOUT-UNSUPPORTED` is still live
(`validate.py:3580`), so no config reaches `command_run` with a holdout; task 18 carries the pin
that `allocation.json`'s `holdout.train ∪ holdout.test` is the roster and its `seed` equals
`holdout_seed_for` over the run's own digest. Nothing in this diff would make that pin fail:
the seed reaching the plan is `holdout_seed_for(block, digest, roster)` with `digest =
design_digest(doc)`, and `holdout_for` partitions the whole roster.

## Verification of the report's own claims

- Digest provenance: **independently confirmed** (check 1).
- Single call site: **confirmed** by grep over `src/`.
- Gate parity with `_check_holdout`: **confirmed** by reading `validate.py:2740-2741`.
- Mutation (a): **re-run by me**, same failure mode.
- `uv run pytest tests/test_cli.py -k holdout` → 5 passed after revert; `uv run ruff check .` → clean.
- Process note in the report: `git checkout -- .superpowers/sdd/.gitignore` was used, which
  CLAUDE.md flags as destructive in general. Here it restored the `sdd-workspace` clobber of a
  tracked file with no uncommitted content of its own, which is the documented remedy. No finding.
