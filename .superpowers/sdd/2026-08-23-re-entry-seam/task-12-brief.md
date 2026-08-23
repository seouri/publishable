## Task 12

Three document edits, all in `reference.md`, and one sweep that must be run before any of them.

1. **§ Before you spend it's transcript.** Replace `would write 64 artifacts under
   /secure/results/cohort-pilot/run_.../` with the narrowed lines Ruling R licenses, and **state the
   counting rule beside the number** so the next reader re-derives instead of carrying: one step
   directory per planned (step, condition, repeat) triple, which is what `runner.step_dir_for` returns.
   For the worked example that is **20** — `shared/step01_load_cohort` (1) + `conditions/<c>/step02_fit_model`
   × 3 (3) + `conditions/<c>/<seed>/step03_analyze` × 3 × 5 (15) + `summary/step04_compare_methods`
   (1). **Verify the 20 by running a dry-run of a 4-step, 3-condition, 5-seed project** rather than by
   trusting this arithmetic; if it disagrees, the arithmetic is the thing that is wrong and you report
   which.
2. **The omission sentence.** The transcript and the row must both say what is *not* listed and why,
   citing `design-principles.md` § Greenfield only.
3. **§ Exit codes and diagnostics.** `dry-run`'s cost-ordering paragraph and the `3`/`4` rows now have
   readers. **Change no code and no row's meaning** — if a row needs no edit, edit nothing and say so.
   H6a's batch 6 restraint is the precedent: a Minor named rather than a self-authorized out-of-scope
   edit.

**The sweep, before any edit — AMENDED 2026-08-23, batch 3–5 fix round (Major 2 of
[`task-b4-review.md`](../2026-08-23-re-entry-seam/task-b4-review.md)). This replaces the paragraph
below it, which is left struck rather than deleted so the reason for the replacement stays legible:
task 9's three unowned `reference.md` edits (its own report's Concern 1) already narrowed `:368`,
`:3756` and `:3882` away from `every artifact path` before task 12 was dispatched, so a sweep for that
phrase finds zero homes across all six files and "Measured already" below is stale — not because the
edits were wrong (the review adjudicated their content correct) but because the plan was never
amended to say what replaced what it swept for, which is exactly the omission
`CLAUDE.md` § The development record warns against.**

Sweep for `step directories` and `would write` instead — the phrasing task 9 actually landed — over
the same six files, **named individually, never `*.md`**, and **never filter the output of a sweep
whose job is to find a string; filter the file list.** Re-measured 2026-08-23 against `HEAD` at the
start of this fix round: `step directories` has **four** homes, all in `reference.md`
(`:368`, `:3673`, `:3756`, `:3882` — the last three task 9's, the first also task 9's but outside its
own section, per its Concern 1); `would write` has **three**, all in `reference.md`
(`:3094` — task 12's own, unedited; `:3673`, `:3756` — task 9's). `64 artifacts` keeps its one home,
`:3094`. Zero hits in `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, and
`CLAUDE.md`. `docs/feasibility-llm-growth-studies.md` carries its own home of the artifact-path
promise (plan correction 9), owned by task 14, not this sweep. **Attribute every hit individually** —
a hit in a file already accounted for reads as noise, and that is how one claim's fifth and sixth
homes were missed in one slice. Editing `:3094`'s `64 artifacts`/`would write` line per item 1 above
will change its own count in a re-sweep; that is expected, not a discrepancy to chase.

~~**The sweep, before any edit.** `64 artifacts`, `would write`, and `every artifact path` over
`README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`,
`CLAUDE.md` and `docs/feasibility-llm-growth-studies.md` — **named individually, never `*.md`**, and
**never filter the output of a sweep whose job is to find a string; filter the file list.** Measured
already: `64 artifacts` and `would write` have **one home each**, both in `reference.md`; a third home
of the artifact-path promise is in the feasibility analysis (task 14). **Attribute every hit
individually** — a hit in a file already accounted for reads as noise, and that is how one claim's
fifth and sixth homes were missed in one slice.~~

**`×` not `x`, including inside fenced blocks. Hyphens, never en dashes, in anything that becomes an
anchor. No positional row locators** — name what a sibling row *does*.

**Must not touch:** § Operation commands' rows (tasks 4 and 9), § Draft runs (task 6), § The apparatus
files (task 13), and the worked example's statistics — `r = 0.581/0.607/0.412` and every interval
around them **may not move**.

---

