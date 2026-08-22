# H5b — non-numeric columns downstream to `aggregate` — the ledger

Branch `h5b-non-numeric-downstream`, off `main` at `5ee3a0c` + the docs commits above it. 16 tasks in
five batches, every batch reviewed. The slice's central fact, measured before it started: **it is not
additive.** Admitting a unit widens the inference base, so values move in columns holding no non-numeric
data at all — and the numbers it moves are **wrong on the record's own terms today**, one mapping
publishing `completed: 4` while `attrition` over the same executions says `completed: 6`.

## Batch 1 — tasks 1, 2, 3 — the pin captured before anything moves, and the document decisions

Commits `23b79a9` (the pin), `bc4e56e` (§ Templates), `2e9f5e4` (§ The per-unit tables, § Statistical
reporting, `W-STATS-REPEATS-DISAGREE`, one filing), `31a5f31`, review `20289d2` (**task 3 FAIL, one
Critical**), fix round `f0c4f2f`. Suite 2891 → **2895**.

**Arm E reproduces, and the reviewer re-measured it rather than reading the claim.** Plan correction 9
said the two-condition Holm half reproduces at `ee8085e` and moves **two keys the design does not name**;
independently re-measured with a fresh script, every literal matched — `n_paired` 4 → 6, the
`correction_level` swap, both `ci95_corrected` shifts, both unnamed extra keys, and every *must not move*
literal. **A non-reproduction would have been a finding rather than a fixture to repair**, which is why
it was re-measured; it is the one claim in this slice that everything downstream rests on.

**The Critical, and it is a controller defect before it is an implementer one.** Task 3 shipped a
§ Statistical reporting sentence codifying **all-or-nothing**: a column earns a block *"only when every
value carried for it is a real number"*, so one `None` costs the column its block for every unit — the
exact reading controller ruling 1 rejects, and **the silent-drop shape this slice exists to end**, traced
to reachable live code rather than argued.

**The root cause is structural.** The ruling was appended to the plan under a preamble asserting *"a brief
extracted from this plan carries these paragraphs"* — **and that was false**: `task-brief` extracts one
`## Task N` section and nothing else. So the ruling reached the controller and the reviewers and **never
the implementer**, which is this repo's own named failure mode, hit inside the slice whose plan documents
it. Fixed the only way that holds: **every one of the sixteen task sections now opens with a pointer
saying the rulings post-date it and win where they disagree**, and ruling 1 gained an amendment naming the
three mixtures — which is the second finding.

**The all-or-nothing sentence was right about one case and wrong about another**, which is why it read as
plausible and passed its own task:

- **non-numeric for every unit** — no metric block, and correct: there is no mean of strings;
- **a number for some units, `None` for others** — a block over the contributors, with **the contributing
  count reported rather than `completed`**, because an interval over five values published beside a
  `completed` of two hundred is a precision claim no later reader can catch;
- **`str` beside a number** — **cannot occur.** `_check_column_types` refuses it at `finalize`, measured.
  A read rule for it describes an unreachable state, and stating one invites a later reader to build
  against it.

**Two more things worth carrying.** Arms C and D were found to **already exist verbatim**, which is the
claim a reviewer should distrust most — an existing test may pin something *adjacent* — so the reviewer
mutated the production code each arm is said to guard and confirmed both fail; **arm D has no authorized
editor, so its passing is the proof.** And mutation (iv), reversing Holm's rank order, was disclosed as
moving only 2 of 3 correction-level assertions — **the argument is sound** (arm E's `mean_score` sits at
the median rank of a three-member family, and reversing an order cannot move a median) and the reviewer
verified it by running, then found the same mutation **also fails arm A**, an undisclosed side effect
rather than a weakness.
