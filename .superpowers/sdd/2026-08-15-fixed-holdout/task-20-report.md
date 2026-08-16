# Task 20 report — the reader-facing half

**Status:** complete.
**Commit under measurement:** `d72724bc150ec0d2373ccd71a9784d994215f90a` (HEAD at start of this task).
**Date of measurement:** 2026-08-16.
**Tests:** `uv run pytest` — 1954 passed + 2 xfailed. `uv run ruff check .` clean. `uv run mypy` clean.
`uv run ruff format --check .` — 63 files would reformat, pre-existing and unrelated to the four files
touched here (verified per-file: `CLAUDE.md` and `docs/experimental-designs.md` format clean;
`docs/feasibility-llm-growth-studies.md` and `docs/reference.md` were already in the would-reformat set
before this task, at locations far from any edit made here — `docs/reference.md` untouched by this task
entirely).

## What was measured, and how

Built a scratch project (`publishable new` + `publishable init … --template generic`, outside this repo,
git-initialized, `input_dir`/`output_dir` outside the repo as required) with a 240-row synthetic table
roster standing in for `growth-screen`'s patient index. Materialized all nine configs from the feasibility
analysis (E1–E6, C1–C3) as scratch YAML and ran `publishable validate` against each, at HEAD.

Two substitutions were needed to reach `validate` at all, both disclosed in the appended section:

1. `entrypoint`/`experiment_type` point at this repo's own scaffolded `generic` demo rather than
   `growth_screen`/`growth_shortcut` (neither plugin is installed in any build; an unsubstituted config
   fails at template resolution or entrypoint import before reaching any of the codes in question — the
   same "plugin assumed to exist" stance the original measurement already took, made concrete).
2. For E1, E2, E3, E4, E5, E6: `data.units.from` was additionally tried as `index.csv` beside the
   as-declared `{resolver: patient_trajectory}` — the table-roster substitution the analysis itself does
   not make.

Mutation: `e1-table`'s clean validation was proven discriminating by setting
`data.units.holdout.frac` to `0`, confirming `E-DATA-HOLDOUT-FRAC` fires, then reverting — diff empty
afterward.

## The nine measured results

| Config | `validate` reports (as declared, resolver-based) | Would execute? |
|---|---|---|
| E1 | `E-DATA-RESOLVER-UNSUPPORTED` | No — plugin registry |
| E2 | `E-DATA-RESOLVER-UNSUPPORTED` | No — plugin registry |
| E3 | `E-DATA-RESOLVER-UNSUPPORTED` | No — plugin registry |
| E4 | `E-DATA-RESOLVER-UNSUPPORTED` | No — plugin registry |
| E5 | `E-DATA-RESOLVER-UNSUPPORTED`, `W-REPL-DETERMINISTIC` | No — plugin registry |
| E6 | `E-DATA-RESOLVER-UNSUPPORTED` | No — plugin registry |
| C1 | `E-DATA-RESOLVER-UNSUPPORTED`, `E-DATA-WEIGHT-CONTRAST` | No — two blockers |
| C2 | `E-DATA-RESOLVER-UNSUPPORTED`, `E-DATA-WEIGHT-CONTRAST` | No — two blockers |
| C3 | `E-DATA-RESOLVER-UNSUPPORTED`, `E-DATA-WEIGHT-CONTRAST` | No — two blockers |

`E-DATA-HOLDOUT-UNSUPPORTED` appeared on **none** of the nine, at any substitution — confirmed retired
(also confirmed absent from `src/publishable/*.py` by grep).

Under the table-roster substitution: **E1, E2, E5 validate with zero errors.** E3, E4, E6 *also* validate
with zero errors under the same substitution — but `io.reuse_from`, which their frozen-program reads
depend on, does not exist anywhere in `src/publishable/` (confirmed by grep), so they still cannot run.
The generous "would run under a substitution nobody has written" count is **three (E1, E2, E5), not six**.

## Which of the spec's numbers this confirms, and which it does not

- **Confirms:** `E-DATA-HOLDOUT-UNSUPPORTED` retired; `E-DATA-RESOLVER-UNSUPPORTED` on all nine;
  `E-DATA-WEIGHT-CONTRAST` on exactly C1–C3; zero of nine execute as written.
- **Does not confirm, and corrects:** "H3d unblocks six" / "6 of 9 one slice-set away" as an executable
  count. That figure was always a count of configs that stop hitting one particular refusal. The honest
  generous count, under a substitution the analysis itself never makes, is **three**, because E3/E4/E6's
  remaining blocker (`io.reuse_from`) is invisible to `validate` and only shows up by grepping the source.

## Document edits

- **`docs/feasibility-llm-growth-studies.md`**: appended `### Measured on 2026-08-16 against commit
  d72724b…` under § Executability on this build, per the append-only convention — the 2026-08-15
  measurement is untouched.
- **`docs/experimental-designs.md`**: no edit. § Train-test holdout and § Mistakes core prevents were
  checked against the shipped build and both already state the built behaviour correctly (holdout/fold
  mutual exclusion, `n` as the test partition, the cells refusal is not mentioned here because this
  section is not where it lives — see below).
- **`docs/reference.md`**: no edit. The brief's citation of "§ What core will not do for you" is the
  brief's own defect — that section exists only in `experimental-designs.md`; `reference.md` has no
  section by that name. The cells refusal (`E-DATA-HOLDOUT-CELLS` / `E-REPL-FOLD-CELLS`) is already fully
  documented in `reference.md` § A fixed holdout split's fourth bullet, written by task 2 (not task 8, as
  the brief misattributes — confirmed against `.superpowers/sdd/2026-08-15-fixed-holdout/progress.md`,
  which itself records and corrects the same misattribution). No phantom edit was written.
- **`CLAUDE.md`**: § Repository status's slice-order paragraph rewritten. "H3d (+3) → H4b → H7b → the
  rest" → "H4b → H7b → the rest"; H3d's payoff stated in honest form (one refusal retired that 6 of 9
  hit, one live defect closed — the two cells refusals now named — zero experiments newly executing); a
  pointer to the 2026-08-16 re-measurement added; the existing H3c-3 ownership sentence extended to also
  name retiring the two cells refusals once cells-drawing lands, rather than duplicating the ownership
  statement in a second place. No spine-design reasoning restated, only cited.

## Consistency passes

Mechanical: no trailing whitespace/tabs in edited regions, table rows match headers (3 columns each), no
duplicate anchors, en dashes used only in prose ranges (`C1–C3`, matching pre-existing style in the same
file) never in headings, `×` not needed (no multiplication in new text).

Cross-document: shared worked example (`cohort-pilot`) untouched — grepped for it in both diffs, zero
hits. No config-completeness, enum-comment, or declared-vs-derived changes introduced (no schema fields
touched). The feasibility analysis edit is exempt from the cross-document pass per convention and was
held to the mechanical pass in full.

## Housekeeping

`.superpowers/sdd/.gitignore` was found clobbered to a bare `*` again (by `scripts/sdd-workspace` /
`task-brief`, as CLAUDE.md warns) and was restored via `git checkout --` before this report was written,
verified by diff.

## Concerns

- None blocking. The one thing worth flagging for the whole-branch review: the "generous count is three"
  claim rests on `io.reuse_from` not existing, which is a grep-level fact rather than something
  `validate` can report — a reader who trusts only `validate`'s own output would see E3/E4/E6 as
  indistinguishable from E1/E2/E5 under the table substitution. The appended section says this explicitly
  and points at the grep, but it is worth the reviewer double-checking that grep still returns nothing at
  merge time.
