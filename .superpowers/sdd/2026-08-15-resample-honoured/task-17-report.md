# Task 17 report

Status: COMPLETE.

Commit: (recorded below after `git commit` — supersedes `7160e16`, the pre-review commit).

Tests: `uv run pytest` — 1798 passed + 2 xfailed (baseline 1795 + 3 new tests: the brief's two, plus a
third added during review round 1 for the `report_by` combination). `uv run mypy` and `uv run ruff
check .` clean. All new tests confirmed FAIL before their fix, then PASS after. All mutations (the
brief's original two, plus two more added for the review-round-1 fix) applied, confirmed FAIL,
`__pycache__` cleared, reverted in place, confirmed PASS.

## What changed

- `src/publishable/cli.py`: right after `resample_spec = _resolved_resample(doc)` is resolved (once per
  run), builds `resample_beside` — `{"resample": {"method", "n", "stratify_by": list(...)}}` when
  `resample_spec["declared"]`, else `{}` — and merges it into `weighted_beside` (`.update`, run-wide, so
  the `report_by` level call at the existing `beside_n=weighted_beside` site carries it too) and into
  `cond_beside_n` (`{**_condition_beside_n(...), **resample_beside}`, per condition, feeding both
  `beside_n=cond_beside_n` sites). Both are the exact `beside_n` carriers `summarize_step` copies
  verbatim into every metric block, the same route `weighted_by` already takes — no new mechanism added.
- Updated the stale comment beside `resample_strata`'s sentinel choice, which said "nothing emits a
  stratum LABEL into `run.yaml` today (a future task records the attribute names)". That "future task"
  is this one, but it records the attribute *names* (`resample.stratify_by`), a coarser fact than the
  composed `|`-joined per-unit label the sentinel actually guards — reworded to say so rather than
  leaving it pointing at an already-passed future.
- `docs/reference.md` § Statistical reporting: extended the sentence the whole slice deferred to ("the
  resolved values are recorded in `run.yaml` beside the interval") with what it now means concretely —
  the `resample:` sibling's shape, the absent-not-null rule, and `resample.n` vs. `resample_draws` as two
  different facts. Added a second, clearly-labelled `mean_pred` example carrying a `resample:` sibling,
  placed after the shared worked example's own `r:` block rather than inside it, so that block's numbers
  (`ci95: [0.517, 0.683]`, `repeat_spread: {std: 0.014, ...}`, etc.) are untouched — verified by
  `grep -n '0.517, 0.683|−0.007, 0.059|0.014' docs/reference.md README.md docs/design-principles.md`
  returning the same lines as before the edit.
- `tests/test_cli.py`: the two tests from the brief, appended verbatim.

## The undeclared-case decision

Chose **absent, not null**, for an undeclared `resample` — matching task 1's existing pin exactly.
`resample_spec["declared"]` is `False` for an undeclared config, so `resample_beside` is `{}` and no
`resample` key reaches the record.

**Correction after review round 1.** My original reasoning here was wrong and the coordinator caught it.
I first justified this by claiming task 1's pin "required" the absent shape and that the cost of choosing
absent was "a reader can't tell 2000 was a default from a choice." Neither survives scrutiny. Mutation
confirms task 1's pin passes **with or without** the `declared` guard —
`_assert_undeclared_resample_shape` never asserts `"resample" not in …` — so the pin was never what made
this choice safe, and citing it as the reason was circular. And the "reader can't tell" cost is not real
either: `run.yaml` already embeds the whole config verbatim, so an undeclared run already shows
`statistics.resample` absent from `config:` sitting beside `resample_draws: 2000` in the same file — a
reader who wants to know whether 2000 was a default or a choice already has the answer, from the config
echo, with or without an echo on every metric block. The choice is right; the reason I originally wrote
down was not the reason that makes it right. Recorded here as the corrected justification: **absent is
safe because the config echo already discloses non-declaration, not because of any pin or any information
loss that would otherwise occur.**

## Where the resolved values live

Chose per-metric (`beside_n`/`weighted_beside`, beside every `ci95`), not a run-level block. Reasons:
`summarize_step`'s own carrier rule (a key that sits beside `n` travels in `beside_n`) already covers
this shape, `weighted_by` is the direct precedent for "a key that names a declaration rather than
reporting a figure," and — the deciding argument — the run-level alternative can't distinguish a metric
core actually resampled with the declared method from one it didn't reach at all (a `basis: repeats`
metric, or one dropped by `E-DATA-CLUSTER-DERIVED`). A per-metric echo makes that distinction free: the
key is present exactly where a resample ran under the declaration, and absent everywhere else, so its
presence can never be misread as implying a value varied across metrics when it didn't — it's the same
constant three values repeated, once per metric that used them.

## Review round 1 — addressed

**C1 (Critical) — the echo was emitted as a YAML alias, invisible to both tests.** `resample_beside`'s
inner dict is one Python object, spread by reference into `weighted_beside` and every `cond_beside_n`,
and `summarize_step` copied `beside_n` into every metric block with a bare `**(beside_n or {})`. Object
identity survives the spread, so `yaml.safe_dump` — which aliases by `id()` — wrote the first occurrence
as `resample: &id001 {...}` and every later one as a bare `*id001` pointer. Both new tests called
`yaml.safe_load`, which resolves aliases before any assertion ran, so neither test could see the defect —
the exact class `hypotheses.py`'s `_observed_block` was written to close for a different carrier
(`ci95`), for the identical reason ("the number … is no longer readable where it is written").
`technical_n` has aliased the same way since before this task; the brief's own `beside_n` carrier is what
made it latent, and this task's `resample` made it live enough to catch.

Fixed in `stats.py`: a new `_beside_n_copy(beside_n)` helper (`copy.deepcopy` on any dict-valued entry,
scalar entries like `weighted_by` passed through) replaces both `**(beside_n or {})` spreads. One fix
closes both `technical_n` and `resample` at once, per the brief's instruction. **First attempt was
incomplete** — a shallow `dict(v)` copies the outer `resample` mapping but leaves its nested
`stratify_by` list as the same shared object, which aliases one level down exactly the same way; caught
only by reading the actual emitted `run.yaml` byte for byte, not by reasoning about the dict shape, and
`copy.deepcopy` is what actually closes it.

Both new tests now assert against the **raw `run.yaml` text** (`"&id" not in text`, `"*id" not in text`),
not only the parsed structure, and a third test
(`test_the_resolved_resample_survives_report_by_without_aliasing`) combines a declared `resample` with
`statistics.report_by` — the `report_by` level path routes through `weighted_beside`, which the first two
tests never reach, and three metric blocks sharing one `resample_beside` object is exactly the shape that
produces an anchor and two aliases. It also asserts `by["a"]["pred"]["resample"] is not
step_block["pred"]["resample"]` — after a `safe_load` round-trip, an aliased pair is reconstructed as the
*same* object by PyYAML's loader, so identity survives the round trip and this assertion catches the bug
even through parsed data, independent of the raw-text check.

Mutated twice: reverting `_beside_n_copy` to the shallow `dict(v)` form made both fail on the raw-text
assertion (the nested list still aliased); reverting the call sites to bare `**(beside_n or {})` made both
fail immediately (the whole dict aliased). Both confirmed FAIL, `__pycache__` cleared, reverted in place,
confirmed PASS.

**I1 — a positional and factual double error.** "See the second `r` block below" named no block (it's
`mean_pred`) and pointed the wrong direction (§ What isn't a repeat, which holds it, precedes § Statistical
reporting in the document). Fixed to name the block and its section without a directional word:
"See the `mean_pred` example in § What isn't a repeat for the shape."

**I2 — an over-reaching citation.** "the same absent-not-null rule `resample_draws` follows above" cited
a rule that doesn't exist at that scope — `resample_draws` has two different rules depending on whether
the metric is a column (two-valued: absent or the requested `n`) or derived (three-valued: `null`/`0`/*n*).
What `resample` (the new sibling) actually matches is the *column's* absent-not-null rule specifically,
not "`resample_draws`" as a whole. Reworded to name the recorded-column paragraph specifically and state
that the derived metric's three-valued scheme does not extend to it.

**I3 — see "The undeclared-case decision" above**, rewritten with the corrected justification (config
echo already discloses non-declaration; the pin was never what made this safe).

**I4 — the sweep stopped one file short a third time.** `stats.py`'s own docstring still said `beside_n`
carries "`technical_n` today," unchanged since before `weighted_by` and now wrong by two. Fixed to name
all three current carriers and to state the copy-not-share invariant `_beside_n_copy` now enforces, so the
docstring and the code it describes can't drift apart the same way again without the docstring visibly
lying about the mechanism, not just the key list.

**I5 — the `report_by` path was uncovered.** Addressed by the third new test above, which is also where
C1 was most visible.

**Minors:**
- **§ Weighted samples' `r:` block sitting beside a declared-`resample` snippet with no sibling —
  fixed.** The section's own `weighted_by` example sits right above a `statistics.resample.stratify_by`
  snippet, introduced by "a stratified sample usually needs both," but the `r:` block never showed both
  facts recorded together. Added a second `r:` example directly beneath, carrying both `weighted_by` and
  `resample` (reusing the section's own `stratify_by: [dx_status, count_stratum]` snippet rather than
  inventing new fields), so the composition the prose describes is the composition the example shows.
- **Duplicated prose — tightened.** The `resample`-is-recorded paragraph originally stated the
  absent-not-null rule twice: once correctly scoped and once as the flawed I2 citation appended beside it
  rather than replacing it (a mistake in my first fix pass, caught while re-reading before this report).
  Collapsed to one statement, parenthetical, naming the recorded-column paragraph rather than repeating
  its rule inline.
- **Unattributed second example — fixed.** The `mean_pred` illustration in § What isn't a repeat now says
  outright that its values are illustrative — "a different, unnamed project... not checked against any
  synthetic table the way the worked example's own numbers are" — so a reader doesn't wonder whether 0.183
  is a real, checked figure the way the worked example's are.
- **Key order in the emitted block — documented rather than matched.** The real `run.yaml` places
  `resample`/`weighted_by`/`technical_n` *before* `value`/`basis` (they're spread from `beside_n` first in
  the dict literal `summarize_step` builds), while every compact example in this document orders `value`
  and `basis` first for readability. Rather than rewriting every existing example to match literal
  insertion order — a much larger, unrelated change — added one sentence stating this is a readability
  convention, not a contract, so a reader diffing an example against a real file matches by key name.
- The untested resolved-vs-declared seam is real but out of scope: `resample.n` vs. `resample_draws` when
  a draw is degenerate is exercised by existing derived-metric tests for `resample_draws` itself (not new
  to this task), and no fixture in this task's tests drives a degenerate draw at `n: 500` specifically —
  correct by construction (both keys come from the same `resample_spec`/`draws_used` values already
  tested elsewhere) but not independently pinned here. Flagged rather than added, since constructing a
  degenerate-draw fixture is the kind of thing task 6's suite already owns.
- The two `cli.py` comments citing "task 17" (pre-existing, from an earlier slice's
  `E-SWEEP-GROUPS-UNSUPPORTED` retirement, unrelated to this task) are a real ambiguity now that this task
  is *also* "task 17" in a different slice. Left alone: they're outside this task's files-changed scope
  and belong to `h3b-clustered-units` history, not `h4a-resample-honoured`; renumbering someone else's
  historical comment on a coincidence of task numbers between two different slices' SDD workspaces is a
  separate, larger cleanup and not this task's to do unilaterally. Flagged here rather than silently left.
- Contrast entries (`vs_baseline`, `results.contrasts`) get no `resample` echo. Confirmed deliberate and
  out of scope: registered against **H4's contrast-side hardening**, the same owner as task 16's filed
  M6/M7, not fixed here.
- The dangling `progress.md` fragment referred to by the coordinator was the pre-existing "Task 17:
  dispatched" entry; a "Task 17: COMPLETE" entry was appended rather than editing it in place, so both
  the dispatch note and the completion record are visible in sequence.

Re-ran the full suite after all fixes: `uv run pytest` — 1798 passed + 2 xfailed (1795 baseline + 3 new
tests); `uv run mypy` and `uv run ruff check .` clean. Re-checked the worked-example-numbers grep
(`grep -n '0.517, 0.683|−0.007, 0.059|0.014' docs/reference.md README.md docs/design-principles.md`) —
unchanged set of lines plus the one new, clearly-separate Weighted-samples example reusing the same
numbers deliberately (that section already reused them before this task).

## Concerns

None outstanding beyond the "task 17" comment-number ambiguity noted above, left as a flag rather than a
fix since it belongs to a different slice's history.
