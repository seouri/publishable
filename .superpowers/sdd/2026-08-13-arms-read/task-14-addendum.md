# Task 14 — controller additions

These are requirements, with the same force as the brief file they accompany.

## The shape is given exactly — do not design it

`reference.md` § `allocation.json` — who went where prints the file in full:

```json
{
  "seed": {"arm": 774512301},
  "arms": {"arm": {"control": ["P0007", "P0011"], "treatment": ["P0002", "P0019"]}},
  "holdout": {"train": ["P0002", "P0007"], "test": ["P0011", "P0019"]},
  "strata": {"arm": ["site", "severity"]}
}
```

Four top-level keys, `arms` and `seed` and `strata` **keyed by axis name**. Write what the document
shows. Where the document and your instinct differ, the document leads and you record the gap rather
than improving the shape.

**H3d adds `holdout` to this same file**, and the section says why they share one: *"Both are partitions
of one roster drawn once."* So decide now, and say in the docstring, what your writer does with the keys
this build cannot fill. Two readings are available and they are not equally good:

- omit `holdout` entirely when no holdout is declared — consistent with § The other files a run writes'
  own habit of *absent rather than null, so "not hashed" can't be misread as "hashed to nothing"*
- write `"holdout": null`

The `manifest/input.json` precedent quoted above argues for omission. **Pick one, name the precedent,
and make the test assert the key's presence or absence explicitly** — a test that only checks `arms` is
one an H3d implementer can silently contradict.

## `seed` under `by_attribute`

This build refuses `random` and `blocked` (`E-DATA-ASSIGN-DRAWN`, task 9), so the only method that
reaches your writer is `by_attribute` — **and nothing was drawn**. A `seed` recording a draw that did
not happen is a false record, which is the same fault § Allocation names when it says *"Under
`method: by_attribute` a `ratio` describes a draw that didn't happen, so `validate` rejects a non-empty
one"*. Omit the axis from `seed` rather than writing a number, and **assert that in a test** — this is
the assertion most likely to be missing, because a writer that emits a seed anyway looks correct against
a fixture nobody checked the seed of.

Same question for `strata`: `assign.stratify_by` describes how a draw was balanced. Under
`by_attribute` there is no draw. Say what you do and why.

## Present when declared, absent when not — and the absent half is the weak test

The brief asks for both. The **absent** half is the one that passes vacuously: a test asserting
`not (run_dir / "allocation.json").exists()` passes for a run that failed before writing anything, for a
wrong `run_dir`, for a typo in the filename. **Pair it with a positive assertion on the same run** —
that `run.yaml` exists and the run completed — and state in the docstring what makes it discriminate.
Four verification probes in this project have already reported nothing for *every* input.

## Keys, never row numbers

The mutation the brief names — write row indices rather than keys — must fail on the **exact keys**, not
on a type or a length. `["P0007", "P0011"]` and `[0, 1]` have the same length, and a test asserting
`len(arms["arm"]["control"]) == 2` dies to neither. Assert the key strings.

Use `units.arms_of` — task 10's single authority for arm membership, read by `validate` and by the runner
after task 12. **A fourth derivation of membership here is the defect that pattern exists to prevent**,
and it is especially bad in this file: `allocation.json` is the record that answers "which patients were
in the treatment arm", so a membership derived separately from the one the run executed would be a
record of something that did not happen.

Roster order within each level, per § The resolved list order, which says the resolved list keeps the
order it was resolved in and that `assign.method: blocked` reads that order as data. `arms_of` already
promises roster order and has a test that would catch a sort — do not re-sort.

## Documentation

**Never write a phrase locating a table row by position.** Tasks 9, 10 and 11 did it five times and were
wrong twice. Name what a sibling row *does*; when you insert a row, check every row your insertion
**moved**.

§ The other files a run writes' tree diagram already carries the `allocation.json` line with the comment
*"realized arm assignment and holdout split; present when either is declared"* — check it still matches
what you wrote, and that § Allocation's and § A fixed holdout split's two references to the file agree
with each other after your change.
