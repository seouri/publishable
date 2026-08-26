# The development record

This directory and `.superpowers/sdd/` hold how `publishable` was built. They are
**tracked deliberately**, and this file exists to say why, because 727 files of task
reports and rulings is not what a visitor expects to find in a repository.

The short version: this project's claim is that a run should be publishable by
default — that the record of what happened should be the thing you hand a reviewer,
rather than something reconstructed afterwards from a shell history. Applying that to
the tool's own construction is the cheapest test of whether the claim is worth
anything. So the design of every slice, the plan it was executed from, what was
measured against the code before each was written, and every ruling made along the
way are all here, dated, with the reason attached.

## What is normative and what is not

**Nothing in here is normative.** The specification is four documents and only four:
[`README.md`](../../README.md), [`docs/design-principles.md`](../design-principles.md),
[`docs/experimental-designs.md`](../experimental-designs.md) and
[`docs/reference.md`](../reference.md). Those say what `publishable` **is**. The record
says how it got there. Where the two disagree, the four documents win — and where the
four documents disagree with the code, the code wins and the document changes first.

## What is here

The slices run from 2026-08-08 to 2026-08-25 and are represented across two trees.
`.superpowers/sdd/` holds a directory per slice — 31 of them, plus a `final/` holding
one critical-fixes report — and the first two slices predate that workspace, so their
rulings are in the two decision ledgers below instead.

| Where | What it is |
|---|---|
| [`specs/`](specs) | A slice's design: its decisions, each with grounds, and what it refuses (43 files) |
| [`plans/`](plans) | The same slice as numbered tasks, with code and a per-task mutation (42 files) |
| `*-SCOPING.md` | What was **measured against the code**, dated and pinned to a commit (27 files) |
| [`spec-defects.md`](spec-defects.md) | Gaps found and deliberately not closed, each with an owner |
| [`s1-decision-ledger.md`](s1-decision-ledger.md), [`s2-decision-ledger.md`](s2-decision-ledger.md) | The first two slices' rulings, before the ledger moved into the workspace |
| [`CHECKPOINT-AGENDA.md`](CHECKPOINT-AGENDA.md) | An audit of `spec-defects.md` against `HEAD` |
| [`2026-08-26-whole-project-review.md`](2026-08-26-whole-project-review.md) | The review that closed the charter |
| `.superpowers/sdd/<slice>/` | Per-slice: the ledger of every ruling and its cost if wrong, plus a report and a review for each task (610 files) |

`CLAUDE.md` § The development record is the table to read if you are working in the
repository rather than reading it; it says which of these to open when.

## Two rules that govern it

**A scoping expires; a spec does not.** Every charter re-scoped in this project was
stale in the same direction — under-counted and missing surface — which is why a
scoping is dated and pinned to a commit. A claim carried from one without re-checking
is worse than a claim omitted.

**The record is append-only.** A spec records what was decided when it was written and
a scoping what was measured on its date; retro-editing either destroys the evidence
they exist to hold. A published claim that turns out wrong is corrected the way this
repository corrects any published claim: append the correction and say what it
replaces. `spec-defects.md` is the one exception, being a live list, where a closed gap
is struck rather than left to mislead.

## How it was written

The slices were built with an agentic workflow — a design, a plan of numbered tasks, an
implementer per task, a reviewer per task, and a whole-branch review before merge. The
reports and reviews in `.superpowers/sdd/` are that workflow's output, which is why they
argue with each other and why several record a task leaving the branch red rather than
self-authorizing an edit. Those are the interesting ones.

The record is unusually candid about its own mistakes, and that is deliberate: the
recurring failure here was never a wrong answer, it was a **right-looking answer derived
from a proxy** — a grep for one spelling standing in for "where can this happen", a count
standing in for a membership test, a passing suite standing in for a check that could
fail. `CLAUDE.md` § Misreadings this repo has made more than once is the distilled form,
and every row of it was paid for by something in this directory.
