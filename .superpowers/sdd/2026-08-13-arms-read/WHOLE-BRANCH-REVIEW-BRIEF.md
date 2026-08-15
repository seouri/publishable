# H3c-1 whole-branch review — what this branch is, and where its defects have lived

The branch is `h3c1-arms-read`, forked from `cb96c7d` (H3b Clustered units and partitions).

**Goal:** a `sweep.groups` axis expands into conditions whose rosters **differ**, each holding the arm
named by an attribute — `allocation: between` with `assign.method: by_attribute` — recorded in
`allocation.json` under `provenance.allocation_hash`. Retires three build refusals; refuses `random`
and `blocked` as *method values* and a cross-arm contrast as a *combination*.

## The acceptance bar

> A `groups` axis that expanded conditions while handing each the same roster would report **two
> identical measurements as two arms**.

Two conditions' rosters must differ, and handing them the same roster must be **structurally
impossible** rather than merely avoided. An arm is a **subset view** of the one roster resolved per run —
never a re-resolution, because `Unit` is frozen and hashable by key precisely so one roster can be
shared, and `units_hash` and every provenance claim rest on that.

## Where this branch's defects actually lived — hunt these first

Twenty-one numbered tasks plus 16b, added mid-slice — and the same classes recurred throughout:

**1. A check that could not fail.** Ten-plus instances across the preceding slices and at least four
here. The forms seen on this branch specifically:

- an assertion **arithmetically implied** by another in the same test (arms' `resolved` summing to a
  roster whose arm sizes are already pinned)
- a control asserting only **absences**, which passes identically if nothing ran
- a **headline mutation applied to a proxy** — the extracted helper's body rather than the call site —
  where reverting the real call sites left the whole suite green
- a `units_hash` assertion written to prove an arm is a view rather than a re-resolution, which **cannot
  detect a re-resolution**, because a re-resolution with equal keys and attributes hashes identically
- fixtures where two quantities coincide, so two behaviours are indistinguishable

**2. A defect living in a combination no single task owns.** Three found, one of them Critical:

- two derivations of "which group axes exist" disagreeing — `sweep.selector_paths` accepting a `levels`
  list of any element type while a `cli` helper required strings — so `levels: [1, 2]` expanded into two
  conditions and narrowed neither, **defeating the acceptance bar from inside the task that set it**
- the unpaired contrast, owned by nothing until a pre-flight audit found it: `paired: True` is hard-coded
  and justified by naming the two codes the retirement task removes
- `report_by`'s strata computed over the whole roster inside the per-condition loop

**3. A comment or document claiming a guarantee the branch does not provide.** Five instances, including
a docstring promising a `KeyError` the code did not raise, and a hash docstring claiming coverage of
"exactly the bytes written" when it covers the canonical form (measurably different digests).

**4. A phrase locating a table row by position.** Five written, two wrong — once in a row **no diff
touched**, falsified by an insertion that moved it. Counts of table rows are the worst form.

## The single-authority pattern

`units.arms_of` is the one authority for arm membership, `units.arm_members` the per-condition view.
Both `validate` and the runner read them, which is what makes "a config that validates cannot crash the
runner" true. **A second derivation of membership anywhere is a defect**, and the branch already caught
one at a level above where it was looking for it.

## Known and deliberately left

- `E-SWEEP-ABLATE-CROSSED` sorts before `E-SWEEP-ABLATE-BASELINE-GROUP` in § Errors `validate` reports —
  pre-existing, owned by task 20
- `cli.command_run`'s per-condition aggregation loop has no direct entry point; the end-to-end tests
  reach it by monkeypatching **only** `validate._check_unimplemented`
- `docs/superpowers/` is gitignored, so nothing recorded only there survives the merge

## What to check that no per-task review could

Each task was reviewed against its own brief. What no task-scoped review could see:

- whether the **twenty-one commits together** leave the acceptance bar structurally impossible to defeat
- whether the three retirements left any claim, comment, test or document stale
- whether `n`'s four parts reconcile on every path a group axis creates
- whether any two of the new refusals overlap, or leave a gap between them
- whether the worked example `cohort-pilot` moved anywhere: 240/228/12; r = 0.581 / 0.607 / 0.412;
  delta 0.026 ci95 [−0.007, 0.059]; kendall −0.169 [−0.213, −0.125]; `repeat_spread` std 0.014; hashes
  `8e21`/`1a2b`/`3d8a`/`6b1f`; README demo `2f5c8d0`

## The last defect found, and what it says about how to review this branch

Task 20 — the consistency-pass task, whose whole job was to prove the acceptance bar — ran **19
adversary configs**, thirteen of them shapes nobody had named, each driven through `expand`,
`validate_config` and `main(["run", …])` to a real `run.yaml`. Careful work, independently confirmed.

It still missed the bar's own failure, and the reason is the most useful thing on this page:

> **All 19 ran against a single 8-control/3-treatment roster.** The set was enumerated over config
> *shape*; the exit criterion is a property of *roster content*. Every set-equality refusal in its
> results table was therefore **roster-incidental rather than structural** — one of its cases refused
> only because that particular roster carried units naming no declared level.

The missed defect: `levels: [control, treatment, control]` — a plausible typo — produces three
conditions where two are **byte-identical at every file**, sha256s matching across all five seed
repeats, with `validate` exiting 0 and no warning. That is `experimental-designs.md`'s *Two identical
measurements reported as two arms* verbatim.

**So when you check the acceptance bar, vary what the config is *about*, not only how it is spelled.**
Roster content, attribute values, level lists, and the relationship between them. A suite of nineteen
shapes over one roster proved less than three shapes over three rosters would have.

## The tally

Six checks in this branch turned out unable to fail — the sixth being that adversary suite. The other
five are listed above. Every one was caught by a mutation and none by reading, which is the other thing
worth carrying into this review: **do not conclude a check works because you understand what it says.**
