# G1 scoping — the gaps the growth-chart feasibility analysis found

Read-only measurement against `main` at `84e6802`, on 2026-08-28. Every probe and grep below was
run against that tree, never remembered. Spec claims and build facts are labelled separately
throughout.

Chartered by [`feasibility-growth-chart-literacy.md`](../feasibility-growth-chart-literacy.md)
§ Gaps this analysis found in the specification, whose seven entries are the whole of the charter,
and by the three of them filed in [`spec-defects.md`](spec-defects.md) on the same date. **This is
the first slice chartered from a feasibility analysis rather than from the hardening spine**, which
is what `CLAUDE.md` says a gap found after the charter completes becomes.

**The goal, in the requester's words: every config validates and every gap closes.** The first half
is **already true at `84e6802`** and this slice does not change it — measured below. So the slice
is the second half, and its size is decided by how many of the seven survive contact with the code.

**Verdict: seven filed, four real, two documentation-only, one retraction. 11 tasks in four
batches.** Gap 2 is the only one that needs a mechanism that does not exist; gaps 1, 3 and 7 are
each a bounded change to a file that already owns the question; gaps 5 and 6 are sentences; gap 4 is
**not a defect** and its filing is what needs correcting.

**Baseline at `84e6802`:** `uv run pytest -q` → **3485 passed, 1 skipped, 2 xfailed**, 423 s.

---

## 0. What "fully" already is, measured before anything is proposed

The charter's phrase is *every config validates*. It does, today:

```
15 of 15 accepted by `publishable validate` at 84e6802
  13 clean
   2 carrying one `W-DATA-CLUSTER-UNDECLARED` each, and no error
```

Re-measured in `2026-08-28-gcl-measurement/` after that tree was copied out of the session
scratchpad, against `84e6802` rather than the `b0a6c9e` the analysis names —
`git diff b0a6c9e..84e6802 -- src/ templates/` is **empty**, so the two measurements are of the same
code.

**So no task in this slice exists to make a config validate.** Two consequences worth stating before
the decomposition, because both invert the shape a reader expects from a hardening slice:

- **The two warnings are not defects to remove.** They are gap 4, and gap 4 is retracted below.
- **A gap closing can make a config stop validating**, which is the honest direction for gap 3: a
  config core accepts today and should not is the finding, so closing it turns a silent acceptance
  into a refusal. Nothing in the fifteen is written that way — every one of them already uses the
  spelling gap 3 recommends — so the fifteen stay green either way. That is a property of the
  fifteen, not evidence about the change, and the slice must not read it as one.

---

## 1. The seven, measured one at a time

| # | As filed | Measured at `84e6802` | Verdict |
|---|---|---|---|
| 1 | `parameter_spec` path must be exactly two segments; the third case crashes | `materialize.py:73` — `if path.count(".") != 1: raise ValueError(...)`, reached from the single call site at `:146`. The docstring states the constraint and its reason (*"would emit broken YAML, so we fail loudly instead of guessing at general nesting"*). No `E-` code, no row in § Errors, no sentence in § Templates. Core's own `generic` declares no such path (`[p for p in GenericTemplate.parameter_spec if p.count('.') != 1]` → `none`) | **Real.** Undocumented constraint, unhandled exit |
| 2 | A correction family cannot span runs | `correction.family_shape` builds from one run's members; `study.py` has 12 functions, none of which corrects — `study_add` redacts and copies. No key anywhere carries a cross-run family | **Real, and the only missing mechanism** |
| 3 | A `sweep.baseline` duplicating a `grid` cell is accepted silently | Measured by calling `expand` and `resolve_contrasts` directly rather than reading labels: six conditions for a four-cell design, `duplicate pairs: [(0, 2), (1, 3)]`, family `[(2, 0), (3, 1), (4, 0), (5, 1)]` — two of four comparisons compare a condition against one holding identical `values`. `validate` reports no error and no warning | **Real** |
| 4 | `W-DATA-CLUSTER-UNDECLARED` fires on a declared reporting stratum | `validate.py:3651` states it outright: *"`statistics.report_by` is deliberately **not** among them: a run that reports by `site` while `site` really is a cluster wants both declarations, not silence."* `reference.md` § Warnings core reports enumerates the four exclusions and `report_by` is not one of them | **NOT a defect.** A documented decision with its reason attached |
| 5 | A `fold` level's `stratify_by` is a string; every other `stratify_by` is a list | `replication.py:49` — `stratify_by: str \| None = None`, read at `:300`. The type is deliberate and singular. `reference.md` § Repeat kinds says *"plus optional `stratify_by`"* and gives no type; § The one config file's `replication` block shows only `{kind: seed, n: 5}`, so a kind's fields are documented in § Repeat kinds and the type is documented nowhere | **Real, and documentation-only** |
| 6 | `measurements` is out of reach of a resolver roster, and `collapse` is not per-column by default | Both halves are **built and diagnosed**: `E-RESOLVER-MEASUREMENT-FIELD` (`validate.py:1545`) names the fault and the remedy in its own message, and the per-column map exists — `units.py:863` — with § Validation rows at `reference.md:540` covering it. What is absent is one sentence: the config schema's inline comment `{by: read_id, collapse: mean}` does not say `collapse` applies to **every** carried column | **Real, and documentation-only** |
| 7 | There is no absolute-threshold hypothesis | `validate.py:5883` — `scope == "summary" and has_compare` → `E-HYPOTHESIS-FORM`; `scope != "summary" and not has_compare` → the same code inverted. So a non-summary metric **must** carry `compare`, and `compare` names two conditions or a contrast. There is no third form | **Real** |

**Four real code gaps (1, 2, 3, 7), two documentation-only (5, 6), one retraction (4).**

---

## 2. Gap 4 is retracted, and the retraction is the finding

The analysis argued that *"the config carries evidence that settles it: an attribute a run declares
as a reporting stratum is being used as a level set, which is precisely the reading the warning says
it ruled out."* That is an argument against a decision, not a discovered defect, and the decision is
recorded in two places with the counter-argument already made: a column can be a reporting stratum
*and* a cluster, and in that case the run wants both declarations rather than one silencing the
other.

**The measured cases do not survive the counter-argument either.** `true_count_band` and
`visit_band` are genuinely not clusters — no unit belongs to a group of correlated units by way of
them — so the warning is a false positive *in those two configs*, which is exactly what its own
message provides for: *"ignore this if the units really are independent."* A false positive a
warning's text anticipates is not a gap in the warning.

**What this costs the slice is one correction, not one task.** The analysis's gap 4 is rewritten to
state the decision and, if it still wants to argue against it, to argue against it as a design
change. Nothing in `src/` moves. This is `CLAUDE.md`'s *citing a sentence whose job is to contrast*
row seen from the far side: the exclusion list's silence about `report_by` is a decision, and
reading a silence as an oversight is the same substitution as reading a documented rule as having
code behind it.

---

## 3. Gap 2 is the whole risk, and it needs a decision before it needs tasks

The other three real gaps are bounded: gap 1 is a refusal that needs a code and a sentence, gap 3 is
a check over a structure `expand` already produces, gap 7 is a third form for a field whose
vocabulary is already closed. **Gap 2 is not bounded**, and the scoping's job is to say why rather
than to pick:

- **It gives a study bundle its first computed field.** Every argument for a bundle being a copy of
  records — `study add` redacts and copies, `report` renders what the record says, a member's
  numbers are never re-derived — applies against it.
- **The family it would carry is not a family core can verify.** Within a run, `family_shape` counts
  members core itself built, which is what makes `family_size` auditable. Across runs, the members
  are whatever a person listed, so the bundle would record an *assertion* about the family and then
  correct at that assertion's size.
- **The alternative is honest and cheap**: state in § Studies that a family does not cross a run,
  and that a cross-run family is corrected by its author and declared in prose. That closes the gap
  as a *documented limitation* rather than as a mechanism — the same disposition
  `reference.md` already uses for the `report_by` interval asymmetry.

**The scoping does not choose.** It records that the two closures differ in kind, and routes the
choice to the design as Decision 1.

---

## 4. What is NOT in this slice

**The refusals stay refused.** Mixed-effects logistic regression, Cochran's Q, conditional logistic
regression, the DeLong test, and the shortcut reliance index are
[what core will not do](../experimental-designs.md#what-core-will-not-do-for-you), with reasons
attached in a normative document. Nine of the analysis's fifteen runs route a number through a
`summary`-step `Estimate` because of them, and that is the design working rather than failing.
Reopening one is an argument against `design-principles.md`, not a task here.

**Nothing about executing a run.** The analysis measured `validate` and `dry-run` only, and this
slice's verification is bounded the same way. A task that needed a real deployment would be
measuring the plugin, not core.

**No new statistics.** Gap 2's mechanism, if Decision 1 takes it, adjusts a *level* and recomputes
no member.

---

## 5. Decomposition — 11 tasks in four batches

| Batch | Task | Gap | Is |
|---|---|---|---|
| **A — the retraction and the sentences** | 1 | 4 | Rewrite the analysis's gap 4 as a documented decision; no code |
| | 2 | 5 | State a `fold` level's `stratify_by` type in § Repeat kinds, beside its `k` |
| | 3 | 6 | Say in § The one config file that `collapse` applies to every carried column, and point at the per-column map |
| **B — gap 1, the crash** | 4 | 1 | Mint the code, raise it as a `ContractError`, and state the constraint in § Templates and in the `Param` table |
| | 5 | 1 | Pin it: a one-segment and a three-segment path, each through the real console script, each mutated |
| **C — gap 3, the duplicate** | 6 | 3 | A check over `expand`'s output for two conditions resolving to the same `values` over the same units |
| | 7 | 3 | The diagnostic names the working spelling § Expansion modes already gives |
| | 8 | 3 | Pin it, including the group-axis form staying on its own existing codes |
| **D — gap 2 and gap 7** | 9 | 7 | The third hypothesis form, whichever Decision 2 takes |
| | 10 | 2 | Whichever closure Decision 1 takes |
| | 11 | — | Whole-branch re-run, the consistency passes, and the `spec-defects.md` entries struck or amended |

**Batch A is where the findings will be**, on this repo's own record: a documents-and-codes batch
looks like the safest to skip and is the one whose output no later batch reads.
