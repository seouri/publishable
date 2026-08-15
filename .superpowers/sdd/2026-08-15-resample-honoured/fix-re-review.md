# H4a fix-round re-review — `statistics.resample` honoured

Scope: the fix diff only (`d59316d..20347d9`, 4 commits), against
`whole-branch-review.md`'s three Important and four Minor findings and
`whole-branch-fix-report.md`'s account of them.

**Verdict: findings.** One Important and one Minor, both unclosed and both newly introduced by this
round, both of the overreaching-claim class the round was fixing. I1's *behaviour* is right and its
pin is real; I1's *stated safety argument is false*, and the widened retry converts a previously
contained fault into a run that exits 1 with no `run.yaml` — demonstrated, not reasoned. I2, I3(a),
I3(b) and all four Minors from the whole-branch review are closed. Tree state at `20347d9` is as
specified.

**Blocking status: blocks merge, trivially.** Both fixes are prose — one comment in `cli.py`
rewritten, one clause in `reference.md` tightened. **No code, no test, and no re-verification of the
acceptance property**; nothing below needs re-reviewing after them.

---

## Important — the retry's non-raise argument is false, and the widening costs the containment property

`cli.command_run`'s new comment states:

> every `ContractError` this `except` can catch is raised from its `if derived:` block, which runs
> AFTER its column loop has completed. The two faults raised inside the column loop —
> `E-STATS-RESAMPLE-STRATIFY-VARIES` … and `E-DATA-WEIGHT-INVALID` … — surface on the FIRST call and
> so never enter this handler at all. Reaching here therefore means that loop already succeeded…

The first call is **inside the `try`**. A `ContractError` raised from the column loop is caught by
exactly this `except`, so "surfaces on the first call" and "never enters this handler" are not the
same statement, and the second is false. Reaching the handler does **not** imply the column loop
succeeded. That is the premise the whole non-raise argument rests on. The same wrong argument is
carried in `whole-branch-fix-report.md` § Important 1 — `d5bfca2` is the commit that aligned the
report to the code's argument, and it aligned it to this one.

**Proved by mutation at the behaviour site**, not by reading. `stats.percentile_over_units_clustered`
monkeypatched to raise `ContractError(code="E-STATS-RESAMPLE-STRATIFY-VARIES")` — a column-loop
fault — under the pin test's own config (`cluster_by`, declared `resample: {bootstrap, n: 500}`,
a deriving template):

| tree | outcome |
|---|---|
| `20347d9` as shipped | `main(["run", …])` returns **1**, `E-STATS-RESAMPLE-STRATIFY-VARIES` on stderr, **no `run.yaml` written, no run directory** — every execution spent, record lost |
| same tree with only `resample_columns=`/`strata=` removed from the **retry** (edited in place, reverted in place, `__pycache__` cleared, suite re-verified) | run **completes**, exit 0 |

So the widening is what changes the outcome, and it changes it in the direction the invariant the
comment cites exists to forbid ("a crash after every execution is already spent").

**How bad, honestly.** The trigger is latent, not live: the only *new* column-loop raise the four
arguments admit is `E-STATS-RESAMPLE-STRATIFY-VARIES`, and I could not reach it past `validate`.
`validate._check_resample` checks each `stratify_by` name over the whole roster with
`stratum_varies_within_cluster`; `cli.resample_strata` hands `stats.py` a `|`-joined cross of the
same names, and a cross of per-name-constant values is constant, over a subset of the same units.
The one divergence the two normalizations allow (`validate` renders `None` → `"no value"`,
`cli.py` renders it → `"<absent>"`, so a literal attribute value `"no value"` beside an absent one
in a cluster passes `validate` and raises at run time) needs an attribute that is genuinely absent
for some unit, and no roster path produces one — `units.py:220` builds CSV attributes from `row[a]`
for every declared name, and the measurement collapse at `units.py:821` merges over names at least
one member carries. `E-DATA-WEIGHT-INVALID` is not a regression from this diff: `weights` was
already on the retry.

That does not make it Minor. The brief asked precisely whether the retry can now raise; the answer
is that it can, that the reason given for why it cannot is wrong, and that what actually holds the
line is `validate` and `attrition` — the two second lines of defence the fix report explicitly says
the argument "does not rest on". A comment stating the wrong invariant is what the next person
widening this retry, or loosening that `validate` row, will read. It is the third instance of the
class I1 and I2 both were, introduced while fixing them, which the brief named as the worst outcome.

**The fix is a rewrite of the comment, not of the code** (the code's behaviour is right, and I would
not revert it): say that the column loop *can* raise into this handler; that the retry replays it;
that the only column-loop `ContractError` the new arguments admit is
`E-STATS-RESAMPLE-STRATIFY-VARIES`, refused by `validate` from the roster before `run` starts, with
`E-DATA-WEIGHT-INVALID` gated by `attrition` outside any `try` and already on the retry before this
change — i.e. the same facts, ordered so that each is true, and with the dependence on `validate`
stated rather than disclaimed. If that dependence is judged too thin, the alternative is to catch
around the retry itself; that is a design call, not this review's.

---

## Closed

**I2 — docstring undercount and misattribution. Closed, counted rather than read.** `_check_resample`
spans `validate.py:4995–5309`; its `c.error(`/`c.warn(` sites are exactly **seven**, at 5075, 5091,
5102, 5153, 5203, 5229, 5297, and their identifiers appear in the docstring's list in that same
declaration order. Both roster readers are named (`W-STATS-RESAMPLE-CLUSTERS`,
`E-STATS-RESAMPLE-STRATIFY-VARIES`) and each does carry its own `roster is not None` guard (5179,
5217); no other line in the function body reads `roster`. The perishable errand ("Check
`cli.command_run`'s `derived_metric_draws` directly…") is gone, and its replacement — "`command_run`
now resolves the block once and threads it into the column and derived constructions alike" — is
true of the code as shipped. The inline no-`return` comment now points at the list instead of naming
"the one exception", and keeps its hedge.

**I3(a) — non-finite gap re-ownered. Closed.** `spec-defects.md:5164` names H4b, "weights and
clusters through the contrast family", cites `docs/superpowers/H4-SCOPING.md` § Decomposition —
which **exists and contains a row of exactly that title** (checked, since a deferral pointing at a
phantom section would be the same defect one level over) — records that the previous owner was H4a,
that both tasks landed, and that task 14's decline was deliberate, with the two disclosure sites
named. Live owner, true statement.

**I3(b) — contrast-echo gap filed. Closed.** `spec-defects.md:5449`, Finding 3 on the task-16 entry,
where `CLAUDE.md` sends a reader. It states the gap correctly (`_comparison_step_blocks` takes no
`beside_n`; `resample_beside` reaches only `summarize_step`), says plainly that the ledger claimed a
registration never made, and shares Findings 1–2's owner.

**M1** — the scope paragraph is on the task-16 entry and matches what I re-probed via the review's
table (unstratified constant pool still publishes `Interval(5, 5)`; not a regression). **M2** — both
owners now read H4b with the file to look it up in; the only two surviving mentions of "H4's
contrast-side hardening" (5397, 5452) are historical narration, not owners. **M3** — retired.
**M4** — the paragraph's counts re-checked independently against the fenced block: `NOT BUILT`
markers = **3** (`from: {resolver}`, `holdout`, `null_test`) ✓; optional `statistics` sub-blocks =
**4** (`contrasts`, `resample`, `null_test`, `report_by`) ✓; `measurements`' two sub-fields ✓; the
six-key axis set matches `envelope.ASSIGN_AXIS_KEYS` ✓. The `#statistical-reporting` anchor resolves.

**Task 1's pin and the undeclared path.** `-k "undeclared_resample or contained_aggregate_fault or
clustered_derived_metric_is_refused"` → 6 passed. The retry path with `resample` **undeclared**
(`cluster_by` + deriving template, i.e. `E-DATA-CLUSTER-DERIVED` fires and this exact retry runs) was
run end to end at `20347d9`: the column's block is
`{basis, ci95, correction, method, n, repeat_spread, value}` — **no `resample_draws`, no `resample`
echo**, `method: t_over_units_clustered`, the `eaf3605` shape. Structurally guaranteed too: every new
argument is read behind `resample_columns=resample_spec["declared"]`, false when undeclared.

**Quoted guarantees spot-checked.** The cli comment's and the new test's quotation of
`reference.md` § Statistical reporting ("absent entirely — not `null` — when no `resample` is
declared") is verbatim at `reference.md`:2376. The phantom-section filing is honest and its count
holds: `grep -rl` (file list filtered, output never) finds the string in **0** places in
`reference.md`, 4 sites in `stats.py` + 1 in `validate.py`, both scoping docs, 4 plans, 4 specs, 5
non-diff development-record files, and `spec-defects.md` — the entry's eighteen, with the `.diff`
copies reasonably excluded. Both readings stated, owner unassigned, not a blocker. Not re-litigated:
the `CLAUDE.md` gitignore point, per the brief.

## Minor — a second overreaching rationale, this one in `reference.md`

Same class as the Important above, also introduced by this round, also inside a fix's own rationale —
which is why it is filed rather than left as polish. `reference.md` is normative, so the bar is the
brief's third bullet, and that bullet carves out nothing for prose.

`reference.md` § The one config file's new clause reads "`init` writes no `resample` key at all …
so a materialized one would silently make that the default for every generated project." A
materialized `resample: **null**` would *not* — `_resolved_resample` treats an explicit null as
undeclared, which `test_the_undeclared_resample_shape_is_pinned_explicit_null` pins, and `null` is
precisely how `init` materializes the sibling `measurements`. The sentence is true only under
"materialized at its default expansion". A clause's worth of imprecision in a paragraph whose whole
subject is that distinction. The fix is a clause — say "materialized at its default expansion", or
say that `init` writes it neither way — not a rewrite.

## Tree state at `20347d9`

`uv run pytest` → **1801 passed, 2 xfailed**. `uv run ruff check .` clean. `uv run mypy` clean, 42
files. Working tree clean apart from the caller's own `progress.md` edit and this file. Every
mutation above was applied at the behaviour site, reverted **by editing in place** (a `cli.py` copy
kept in scratch, `diff`-verified), `__pycache__` cleared between runs, and the revert verified by
behaviour — the full suite green afterwards, not `git status`.
