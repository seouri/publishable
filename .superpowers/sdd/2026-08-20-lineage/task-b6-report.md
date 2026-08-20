# Batch 6 report — tasks 8, 9, 10 (H8a closes)

Commits: `d2fcfa4` (task 8), `254aabe` (task 9), `c2fd70e` (task 10).

## Status

All three tasks complete. Gates clean throughout: `uv run ruff check .`, `uv run ruff format --check .`
(84 files), `uv run mypy` (47 source files), `uv run pytest -q` — **2512 passed, 1 skipped, 2 xfailed**
(2510 baseline + the 2 tests task 8 added; no other count moved).

## Task 8 — scopes

Fixture P: a real downstream run with four generated steps, one at each scope (`run`, `condition`,
`repeat`, `summary`), each calling `io.reuse_from` against one upstream run that published four
distinct names — all four succeed, and `provenance.upstream` carries one entry whose `used` list
holds all four `step/name` pairs, sorted. Built by scaffolding directly with `generate_experiment`/
`generate_step` rather than `run_a_project`'s `extra_step_source`, because that parameter applies one
source to every entry in `extra_steps` and cannot give four different scopes to four different
generated steps in one run.

The control: a fifth, `run`-scoped step calls `io.read_upstream` on the condition-scoped step —
ordinary same-run direction checking still fires (`E-STEP-READ-DIRECTION`), read from that
execution's own `executions.jsonl` line rather than from an absence. A second test pins
`not hasattr(ResolverIO, "reuse_from")` paired with `hasattr(StepIO, "reuse_from")`.

**Mutation run:** added `self._summary_only("reuse_from")` at the top of `reuse_from` in
`artifacts.py`. Result: **FAIL** — the run-, condition- and repeat-scoped arms all fail with
`E-STEP-SCOPE-ONLY` (confirmed against the actual pytest failure, not inferred), because three of the
four executions are not `summary`-scoped. Reverted by editing the line back out; re-ran the two new
tests green, then the full suite green. No other mutation was prescribed for this task (Decision 9
states there is nothing else to check); no `src/` change was needed or made.

## Task 9 — documents

`docs/reference.md`:
- § Lineage between runs gains the two locator forms' refusals (`E-UPSTREAM-LOCATOR`,
  `E-UPSTREAM-REPO-CONTAINED`, `E-UPSTREAM-RUNID-MISMATCH`), the record refusals
  (`E-UPSTREAM-RECORD-MISSING`/`-UNREADABLE`/`-VERSION`), the run-/summary-only scope rule and its
  three refusals, the `reuse_from`-specific containment pair (`E-UPSTREAM-NAME`,
  `E-UPSTREAM-ARTIFACT-MISSING`), and the `upstream: []` no-upstream shape — each stated as derived
  from the section's own existing no-selector argument rather than restated from scratch.
- § The two files: the existing non-empty `upstream` example (present since the initial commit,
  predating H8a's code) is **confirmed** against `UpstreamLedger.entries()` — same four keys, same
  order — rather than rewritten, and gains one sentence that `upstream: []` is the ordinary case.
- § Errors core raises gains one row per new code (11 codes total, read out of `lineage.py` and
  `artifacts.py` by grep, grouped into 4 rows by mechanism/Decision-5 exception class), and repairs
  the `E-ARTIFACT-NAME` row, which read as write-side-only and now states its two new read-side emit
  sites (`read_upstream`, `read_condition`, added by task 12).
- The `ArtifactError` gloss ("core will not write this") is false in both places it appears — fixed
  in **both** `errors.py` and `reference.md`'s exception tree, to "an artifact-shaped fault — on a
  write, or on a read."
- § Steps and artifacts: the `io.reuse_from` table row confirmed unchanged (no repair needed); the
  "resolved against the step's directory" clause repaired to name the actual target directory per
  reader (the caller's own for writes, the *named* step's for `read_upstream`/`read_condition`/
  `reuse_from`).
- § Package layout: `lineage.py`'s "not yet built" marker removed; `artifacts.py`'s gloss gains
  `reuse_from`.

**How the `E-UPSTREAM-*` codes were enumerated:** read `lineage.py` and `artifacts.py`'s `reuse_from`
end to end first, listed every `code="E-UPSTREAM-*"` site by eye, then confirmed with
`grep -rn "E-UPSTREAM" src/publishable/` (11 codes, matching) — read-then-grep, the order `CLAUDE.md`
requires. Confirmed each new row's wording covers every site the grep found (no site left uncovered,
no row claiming a site that doesn't exist).

**Sweeps** (reuse_from / upstream / lineage / lineage.py / E-ARTIFACT-NAME / "not yet built" /
every `provenance` key list), each run by naming README.md, design-principles.md,
experimental-designs.md, reference.md, feasibility-llm-growth-studies.md and CLAUDE.md individually
(never filtered on output) and each proven capable of failing first, against "not yet built" as the
control string (present 8/1/3 times respectively in reference.md/feasibility/CLAUDE.md, absent in
design-principles.md/experimental-designs.md). No document besides reference.md needed a change:
README, design-principles.md, experimental-designs.md name none of these strings; the feasibility
analysis's and CLAUDE.md's many `io.reuse_from` mentions are dated development-record claims and are
correctly left untouched (task 10 adds the new dated entry rather than editing old ones).

**Disposition, not a fix:** the design doc's own body (§ task table, § Corrections) still attributes
the read-side containment fix and `E-ARTIFACT-NAME`'s two new emit sites to "task 5." Measured
against the actual git history: `e21d795` (task 5) built `reuse_from`'s *own* new containment;
`406a86a` ("H8a task 12: wire the shared `_contained` helper into `read_upstream` and
`read_condition`") is what actually touched the two shipped readers. This is already corrected in
the **plan's** own appended "Corrections against the code" (correction 3: "task 5 splits into tasks
5 and 12"). The design's body is development record per `CLAUDE.md` and is not retro-edited to match
— recorded here as a disposition rather than an edit.

## Task 10 — re-measurement and filings

`docs/feasibility-llm-growth-studies.md` § Executability on this build gains
"Measured on 2026-08-20 against commit `254aabe` — after H8a" (the last commit carrying source
changes; task 10 itself makes none, so this is the correct commit to cite — the same pattern the
existing "after H7d Part B" entry uses, citing a commit that precedes the entry's own). Quotes the
2026-08-20 correction-to-the-correction's four-row table with **exactly one row moved**:

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes |
| Blocked on `io.reuse_from` | **0** | no |
| Meet the `report_by`-under-`resample` gap | **7** | no |
| Free of every core-side dependency this analysis can name | **1** | no |

Mints no fifth number and does not resurrect the "3", "6", or "8-of-8-projected" readings the
2026-08-20 corrections ruled inconsistent (the plan's own correction 1 rules the design's third
payoff figure out on the same grounds). States what may be claimed by probe (both locator forms
resolve; the read dispatches through the registered reader; `provenance.upstream` carries the
upstream's own two hashes) versus what may not (E3/E4/E6 executing; anything from `validate`, since
the locator is a parameter, the read is a step-level call, and the record key is written at run
end). States E2's plugin obligation (a `summary` step must republish the compiled programs, since
`growth_screen`'s compile step is `condition`-scoped and only `run`-/`summary`-scoped steps are
addressable under Decision 4) as the plugin's task, changing no core-side count.

`docs/superpowers/spec-defects.md`:
- Struck "`io.reuse_from` is unbuilt and unowned by any H7 sub-slice" as **CLOSED by H8a**, noting in
  the strike that the entry's own citation — "`reference.md` § Steps that consume an earlier run's
  artifacts" — named a heading that was never in `reference.md` (confirmed by grep: the phrase is a
  table cell in `experimental-designs.md`); the specification lives under § Lineage between runs.
- Re-scoped the `report_by`-under-`resample` entry (already `CONVERTED` to a documented limitation by
  H4d task 24, so this is an appended amendment, not a re-open): attributed to E1, E2, E4, E6, C1, C2,
  C3 rather than C1–C3 alone, citing the design doc's own measurement (`summarize_step` over one
  12-row table moving both `prob` and `latency_ms` with/without `resample_columns`). Owner unchanged
  (H4 Statistics; H4d is terminal for the family).
- Confirmed (not re-done) that the six-`run.yaml`-keys entry already had `provenance.upstream` struck
  by task 7's own 2026-08-20 amendment.
- Confirmed by grep that the `..`/absolute escape in `read_upstream`/`read_condition` was **never
  filed** in this document — it went straight from gap to fix in task 12, so there is nothing to
  strike; recorded here for the record only.
- Left `BaseTemplate.field_convention` and `max_failed_fraction`'s truncation status untouched.

## Where a brief, the design, or the plan disagreed with the code

Grepped each brief's assertions against the code before repeating them, per `CLAUDE.md`'s rule that
five "no disagreements" reports were previously wrong because each hid one in prose the brief
supplied.

- **Task 9 brief / design doc vs. actual commit history:** the one substantive disagreement, above —
  "task 5" attributed for work `406a86a` (task 12) did. Already corrected by the plan; recorded as a
  disposition, not an edit, per the development-record rule.
- **Task 8 brief:** matched the code exactly — `ResolverIO` has `read_input` only, `StepIO` has
  `reuse_from`, and `scope.py`'s `SCOPE_ORDER` confirms no direction check applies to `reuse_from`
  (Decision 9 as written).
- **Task 10 brief:** the four-figure table it prescribes matches the plan's own correction 1 exactly;
  no disagreement found between the brief, the plan, and the design's § The payoff once the plan's
  correction is applied (the design's own third payoff row is the one correction 1 already flags as
  a fifth number, and I did not carry it).

## Concerns

None outstanding. `docs/superpowers/spec-defects.md`'s census table (§ "23 entries" table, the H6 row
naming "the six unwritten `run.yaml` keys") still uses that historical count as a stable label for
the filed entry even though two of those six are now closed (allocation since 2026-08-13, upstream
since task 7) — left untouched since it is an index/label for the entry, not a live claim, and no
brief in this batch named it. Worth a controller decision on whether that census table itself should
be re-tallied, but it is outside all three of this batch's briefs.

## Whole-branch fix round (post-MERGE-verdict)

Reviewer's own review is at `.superpowers/sdd/2026-08-20-lineage/whole-branch-review.md`. Verdict
MERGE; one Major already found and fixed by the reviewer (documents only, `E-UPSTREAM-REPO-CONTAINED`
scoped to both emit sites) — nothing owed. Minor 3 (`CLAUDE.md`) is the coordinator's, not touched.
Addressed here: Minors 1, 2, 4.

**Minor 1 — pinned.** Added
`tests/test_artifacts.py::test_reuse_from_a_read_that_raises_inside_read_leaves_the_ledger_untouched`.
It reuses the shipped writer-without-reader fixture (`.fastq` registered in `WRITERS`, absent from
`READERS`) so the artifact genuinely exists on disk (`target.exists()` is `True`) and `_read` itself
is what raises `E-ARTIFACT-UNREADABLE` — the boundary the code comment beside `ledger.record` claims
survives raising, and the boundary batch 5's own fixture (Fixture F's second half, which raises
earlier, at `target.exists()` being `False`) never reaches. Asserts
`io._upstream.ledger.entries() == []` after the raise.

Verified both ways, against the full unfiltered suite: applying the exact mutation named — moving
`self._upstream.ledger.record(...)` to run immediately before `self._read(target)` instead of after
it returns — leaves Fixture F (`tests/test_cli.py::test_fixture_f_a_read_that_raises_contributes_no_entry`)
**green** (2 passed) but fails the new test (`AssertionError: assert [{...}] == []`), confirming the
two branches produce different results and that the new test is what catches the mutation Fixture F
missed. Reverted by copying the file back from a pre-mutation snapshot and re-running; both tests
green again, and the full suite re-run clean at **2513 passed** (2512 baseline + this one new test).

**Minor 2 — ruling: unify, not "state why two copies are right."** `_resolve` (the write-side
containment check, always against `self.step_dir`) and `_contained` (the shared read-side check,
taking `base` as an argument) were the identical predicate written twice. No test pins `_resolve`'s
old exact message text (`grep` confirmed: every test on this path asserts `.code == "E-ARTIFACT-NAME"`
only), so `_resolve` now delegates: `return self._contained(self.step_dir, name, code="E-ARTIFACT-NAME")`.
Also repaired `_contained`'s own docstring, which described itself as "the same symlink-aware
technique `_resolve` already uses ... generalized" — backwards once `_resolve` calls `_contained`
rather than the reverse; restated as `_contained` being the one predicate both a write (via
`_resolve`) and the readers (`read_condition`, `reuse_from`) go through. Verified by running
`tests/test_artifacts.py` in full: **120 passed**, including every existing `E-ARTIFACT-NAME` arm on
both the write side and the read side, plus `mypy` (47 files, clean) and the full suite (unaffected,
still 2513).

**Minor 4 — deleted the stale/temporal claims rather than rewriting them.**
- `lineage.py`'s module docstring: dropped "(from later tasks in this slice)" — the module is
  finished; the sentence now just names what it holds (`resolve_run`, `resolve_step`,
  `UpstreamLedger`, `UpstreamResolver`) rather than describing itself in terms of a schedule that no
  longer exists.
- `read_run_record`'s docstring: "the named step's own recorded status is a later task's check, not
  this one's" → names the actual check, `resolve_step`'s, rather than a temporal placeholder.
- `UpstreamResolver.__init__`'s cache comment: the phrase 'skipping the "must sit under `output_dir`"
  check' named a check that does not exist as its own gate — the relative form's containment check
  is `resolves_inside_repo`, a real one, but there is no separate named check for "sits under
  `output_dir`" (that's a structural consequence of how the relative form is resolved, not a check
  of its own). Rewrote the comment to say what actually goes unrun when the cache-key bug was live:
  `resolve_run` never ran at all for the relative call, so its real containment check never ran
  either, and the relative call was silently answered from whatever directory an earlier absolute
  call happened to resolve to — which need not sit under this config's own `output_dir`.

All three files reformatted with `ruff format` (only the new test's own lines moved — confirmed by
`git diff --stat`, 34 lines added to `tests/test_artifacts.py`, nothing else touched). Gates: `ruff
check .` clean, `ruff format --check .` clean, `mypy` 47 files clean, full suite **2513 passed, 1
skipped, 2 xfailed**. Guard pin re-verified explicitly (`-k h8a_arm`): all three arms still pass,
confirming this round is not what would trip them if it were wrong.

No finding left open.
