## Task 7 review — `E-STATS-RESAMPLE-UNITS`

Reviewed `c0c9dbd..01b2b97` against `.../task-7-brief.md`, `.../task-7-report.md`, and
`docs/superpowers/specs/2026-08-15-resample-honoured-design.md`.

**Spec compliance: ✅**
**Task quality: approved with findings** — 2 Important, 3 Minor. No Critical.

Tree at `01b2b97`: `uv run pytest` 1721 passed, 2 xfailed; `ruff check` clean; `mypy` clean (42 files).
`reference.md` mechanical pass clean — no duplicate anchors, no broken same-file anchors, no trailing
whitespace/tab/invisible unicode, and the three ragged-looking table rows and two "broken" anchors my
checker flagged are all present at `c0c9dbd` and are false positives (escaped `\|` inside cells;
underscores in anchors, which GitHub keeps). No count phrase sits near either inserted row.

---

## The judgment call: made correctly, and the reason is stronger than the one recorded

The brief left open whether to gate on the **declaration** or on `roster is None`. The implementer chose
the declaration. That is right, and it is right for a reason neither the brief nor the report found —
see Important 1.

I probed every shape rather than reasoning about them (`codes()` over `write_config`, roster-bearing
`statistics.resample: {method: bootstrap, n: 2000}` throughout):

| `data.units` | codes reported |
|---|---|
| absent | `E-STATS-RESAMPLE-UNITS`, `E-STATS-RESAMPLE-UNSUPPORTED` |
| `null` | `E-STATS-RESAMPLE-UNITS`, `E-STATS-RESAMPLE-UNSUPPORTED` |
| `{}` | `E-STATS-RESAMPLE-UNITS`, `E-STATS-RESAMPLE-UNSUPPORTED` |
| `5` / `"index.csv"` (not a mapping) | `E-CONFIG-SHAPE` — fatal, `_check_resample` never runs, no `AttributeError` |
| `data: 5` (parent not a mapping) | `E-CONFIG-SHAPE` |
| `{from: index.csv, key: patient_id}` | `E-STATS-RESAMPLE-UNSUPPORTED` only |
| `{from: nope.csv, …}` | `E-UNITS-SOURCE-MISSING`, `-UNSUPPORTED` |
| `{key: no_such_col}` | `E-UNITS-KEY-MISSING`, `-UNSUPPORTED` |
| `{attributes: [nope]}` | `E-UNITS-ATTR-MISSING`, `-UNSUPPORTED` |

Answering the three questions asked:

1. **Declared-but-unresolvable is genuinely covered elsewhere, with an actionable finding.** All three
   unresolvable shapes report a specific, self-explaining `E-UNITS-*` code from `_check_units`. Staying
   silent here is correct, not a gap.
2. **Missing `data.units` is genuinely covered by nothing else.** The absent/`null`/`{}` rows carry
   exactly two codes, one of which is the new one and the other of which retires at task 12. Remove the
   new check (I did — see below) and those configs report `-UNSUPPORTED` alone. The hole would be open
   after task 12. The task is not busywork.
3. **The between-poles shapes are handled.** `null` and `{}` fire (the `or {}` coercion). A non-mapping
   `data.units` — or a non-mapping `data` — is caught upstream by `E-CONFIG-SHAPE` as fatal, so the
   `(doc.get("data") or {}).get("units")` walk cannot raise. This was the one crash risk in the
   expression and it is closed.

## The tests are not vacuous on `E-STATS-RESAMPLE-UNSUPPORTED`

The named risk — an acceptance test passing on the old wholesale refusal, as three earlier tasks in this
slice did — does not apply. Mutation, `__pycache__` cleared, reverted by editing in place:

- **Deleted the `_check_resample` call site** (line 637 → `pass  # MUTANT`):
  `test_a_resample_with_no_unit_roster_is_refused` **FAILS** —
  `assert 'E-STATS-RESAMPLE-UNITS' in {'E-STATS-RESAMPLE-UNSUPPORTED'}`. The assertion names the new code
  specifically, so the surviving `-UNSUPPORTED` finding cannot carry it.
  `test_an_unresolvable_roster_does_not_earn_a_second_resample_finding` passes — correct, it is the control.
- **Gate → `if roster is None:`**: `test_an_unresolvable_roster_…` **FAILS**
  (`E-STATS-RESAMPLE-UNITS` joins `E-UNITS-SOURCE-MISSING`) while
  `test_a_resample_with_no_unit_roster_is_refused` stays green. The pair genuinely discriminates the two
  gates, exactly as the report claims. Report's mutation account verified.

---

## Findings

### Important 1 — the comment miscites its precedent, and the real precedent (12 lines from the one it cites) contradicts the `return`

The added comment says: *"The precedent is `_check_replication`'s fold-without-basis check
(`E-REPL-FOLD-K`), for the same reason."* That is the wrong code, and the right one is a near-exact twin
that was missed.

`E-REPL-FOLD-NO-UNITS` already exists in `_check_replication` and is the direct analogue — *"a `fold`
level partitions units, and `data.units` is not declared; there is nothing to partition"* — registered at
`docs/reference.md` § Errors. Probed:

| config | codes |
|---|---|
| `fold, k: 3`, no `data.units` | `E-REPL-FOLD-NO-UNITS` |
| `fold, k: all`, no `data.units` | `E-REPL-FOLD-K`, `E-REPL-FOLD-NO-UNITS` |
| `fold, k: 3`, `data.units: {from: nope.csv}` | `E-UNITS-SOURCE-MISSING` only |

So `E-REPL-FOLD-K` is the *`k: all` basis-unknowable* fault, a different one; the no-units fault has its
own code. Three consequences:

- **The judgment call is more strongly supported than recorded.** The twin gates on the identical
  expression — `not (doc.get("data") or {}).get("units")` — and stays silent for the unresolvable roster
  (third row above). This is not a novel call at all; it is the house pattern, and the review is
  therefore confident in it.
- **The twin does not `return`.** It reports and lets the remaining replication checks run. The new check
  returns. See Important 2.
- **The report's precedent audit did not happen as described.** It states the implementer "re-read …
  `_check_replication`'s `E-REPL-FOLD-K` site" and found the precedent "a clean fit with no adaptation
  required". The twin sits in the same function; reading that site and not finding it is what makes the
  claim doubtful. (The brief and the spec's trap table carry the same imprecise phrase
  "fold-without-basis shape is the precedent", so the miscitation originates upstream — but auditing an
  inherited comment against the code is exactly the standing obligation here.)

**Fix:** cite `E-REPL-FOLD-NO-UNITS`, and consider the naming divergence (`-NO-UNITS` vs `-UNITS`) while
the code is one commit old and unreferenced by any other task.

**Fix upstream too, or it regenerates.** The spec's own trap table (§ The traps, and where each lives,
the *Retiring a refusal opens a silent no-op* row) says "`_check_replication`'s fold-without-basis shape
is the precedent". Fold-without-*basis* is `E-REPL-FOLD-K`; the precedent here is fold-without-*units*,
`E-REPL-FOLD-NO-UNITS`. Left as written, the next brief drawing on that row reproduces the miscitation.
This is a spec-side correction and **not** a compliance failure — the spec required the check
(§ Task decomposition item 7) and was silent on both the code name and the gate, which is why the spec
verdict stays ✅.

### Important 2 — the comment claims a guarantee the code does not provide, and it is the sentence task 8 will read as an instruction

*"Every later check in this function returns after this one, since each of them presupposes a roster it
would have nothing to read."* Both halves are false:

- **`roster` is never read anywhere in `_check_resample`.** It is an unused parameter. Receipt: the
  function spans lines 4989–5194 (`awk 'NR>4989 && /^def |^class /{print NR; exit}'` gives 5195,
  `_check_report_by`); `grep roster` over 4989–5194 returns the signature and four comment lines and no
  use. No check in the function presupposes a roster.
- The `method` enum check reads `resample.get("method")`; the `n` floor reads `resample.get("n")`. Both
  are entirely roster-independent. Only `stratify_by` reads `data.units.attributes` — the *declaration*,
  not the roster.

Measured consequence of the `return`:

```
resample: {method: bootstap, n: 50}, no data.units  → E-STATS-RESAMPLE-UNITS, E-STATS-RESAMPLE-UNSUPPORTED
resample: {method: bootstap, n: 50}, with a roster  → E-STATS-RESAMPLE-METHOD, E-STATS-RESAMPLE-N, -UNSUPPORTED
```

Two independently-fixable shape faults are swallowed, with a false justification for swallowing them.

Why this is more than a wording nit:

- **The mechanism is task 8**, which extends this same function, and the brief records that three earlier
  comments in `_check_resample` were read as instructions by a later task. This comment tells a task-8
  implementer that adding a check below the gate is safe "since each of them presupposes a roster". Any
  roster-independent check task 8 adds there will silently not run when `data.units` is absent.
- **The house convention documents suppression, and this row does not.** The sibling
  `E-STATS-RESAMPLE-STRATIFY-UNKNOWN` row in § Errors spells out when it "stays silent under this code
  rather than being reported twice", and the function's own docstring records the same discipline for
  wrong-typed leaves. The new § Errors row says nothing about swallowing `-METHOD` and `-N`.

**Fix, either way:** drop the `return` (which is what `E-REPL-FOLD-NO-UNITS` does), or keep it and (a)
replace the justification with the true one — "the remaining checks are worth less than the missing
roster and are suppressed to keep one fixable fault on screen" — and (b) say so in the § Errors row the
way the sibling row does. Not Critical: the check fires and stays silent in all the right places; it is
the justification and the doc that are wrong.

**Due before task 8 begins, not at slice end.** The timing *is* the severity: task 8 extends this
function next, and the comment as written tells its implementer that placing a check below the gate is
safe. Fixed after task 8, the fix lands behind the mistake it exists to prevent.

### Minor 1 — test 1's positive companion asserts only an absence

`assert "E-STATS-RESAMPLE-UNITS" not in codes(<config with a roster>)` is the repo's named "control
asserting only absences" shape. It does discriminate the mutation it is aimed at (a gate that fires
unconditionally), so it is not worthless — but it cannot detect a malformed companion config. Receipt:
substituting `data.units: 5` into that companion (which dies at `E-CONFIG-SHAPE` before
`_check_resample` runs at all) leaves the test **green**. Asserting something the code under test must
produce for that config — `E-STATS-RESAMPLE-UNSUPPORTED` today, a `-METHOD`/`-N` finding after task 12 —
would close it.

### Minor 2 — test 2's positive half is broader than the fault it stands for

`any(code.startswith("E-UNITS-") or code.startswith("E-DATA-"))` passes on any of a large family. It is
**not** vacuous — a clean roster config reports no `E-UNITS-*`/`E-DATA-*` at all, so the assertion has
something to fail on — but naming `E-UNITS-SOURCE-MISSING` would pin the actual claim, which is that the
reader gets *that* actionable finding rather than merely *a* finding in a broad prefix.

### Minor 3 — the report inherits the false claim and carries process noise

Judged as the tracked artifact it now is, for a reader six months out:

- The judgment call itself is explained **well** — the two configs, the empirical `roster is None` /
  `units_declared` truthy asymmetry, the `usable_cluster` argument, and the mutation outcome. That half
  needs no change.
- "**Interface delivered**" says the ordering "only affects whether they run at all when there's no
  roster to check" — implying `-METHOD`/`-N` need a roster, the same falsehood as the comment, and it
  omits the suppression measured above. A reader trusting this paragraph learns something untrue about
  the function.
- The "**No disagreement with the brief found this time** — the six-implementers framing in my
  instructions expected one" paragraph is process noise from a prompt a future reader will not have.
- The § Errors placement claim ("alphabetically last among the `E-STATS-RESAMPLE-*` rows, after
  `-STRATIFY-UNKNOWN`") is correct, and the "no count phrase needed updating" claim is confirmed
  independently.

---

## Out of scope, for the slice record

`reference.md` line 1397 covers `fold`, `statistics.resample` **and** `statistics.null_test` with one
sentence. `fold` now has `E-REPL-FOLD-NO-UNITS` and `resample` has `E-STATS-RESAMPLE-UNITS`;
`null_test` has no equivalent, and `E-STATS-NULLTEST-UNSUPPORTED` covers it wholesale today the same way
`-UNSUPPORTED` covered this shape. Whichever slice retires that refusal inherits this task's hole. Not a
task-7 finding — task 7 is resample-only.

## Method

Mutations run in `src/publishable/validate.py` and `tests/test_validate.py` where the behaviour lives,
`__pycache__` deleted between runs, reverted by restoring a pre-mutation copy taken with `cp` (never
`git checkout`), and verified by re-running the affected tests. Shape probes run as throwaway test
modules under `tests/` (star-importing the `write_config`/`codes` fixtures) and deleted. `git diff` over
`src/` and `tests/` is empty; the tree is clean at `01b2b97`.
