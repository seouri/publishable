# Task 13 review — resolve `statistics.resample` once in `command_run` and thread it

**Spec compliance: ✅**
**Task quality: findings** — 1 Important, 3 Minor. No Critical. Behaviour is correct; every finding is
about prose the next four tasks will read, and one test docstring that claims more than the test proves.

Reviewed at `8b34b19` on branch `h4a-resample-honoured`. Tree left clean; only the pre-existing
uncommitted `progress.md` remains.

## Verification performed

**Baseline, re-run rather than taken from the report:** `uv run pytest` → 1769 passed, 2 xfailed.
`ruff check` and `mypy` clean.

**Mutations, all applied where the behaviour lives, `__pycache__` cleared between runs, reverted by
editing in place, and the file byte-compared against a pre-mutation copy afterwards (`diff` →
identical).**

| # | Mutation | Result |
|---|---|---|
| M1 | `.get("resample") or {}` → `.get("resample", {"n": 500})` | **FAIL** `test_the_undeclared_resample_shape_is_pinned_absent_key`, `test_an_undeclared_resample_still_draws_two_thousand`, `test_the_resample_block_is_resolved_once`; **PASS** `..._pinned_explicit_null`. The asymmetry is exactly right: the absent-key document breaks, the explicit-`null` one does not. The two-document distinction is intact |
| M2 | `"declared": bool(declared)` → `n != 2000` | **FAIL** `test_the_resample_block_is_resolved_once` |
| M2′ | `"declared": bool(declared)` → `bool(declared) and n != 2000` — the *isolating* mutation, which M2 does not perform because M2 also breaks the `{}` case | **FAIL** at the `{"n": 2000}` assertion specifically (line 6920). So a config declaring exactly `n: 2000` genuinely still counts as **declared**, and § Statistical reporting's *"a derived metric is resampled whether or not you declare `statistics.resample`"* is guarded, not merely asserted |
| M3 | `derived_metric_draws = resample_spec["n"]` → `= 2000` (resolver call left in place) — **the threading mutation the implementer did not run** | **FAIL** `test_a_declared_resample_n_changes_the_derived_draw_count` (`assert 2000 == 500`). The resolved value really does reach the six read sites |

**Task 1's pin still reaches the code it guards.** It is not surviving by no longer touching the changed
path: `_assert_undeclared_resample_shape` pins the derived metric's `ci95` numerically at
`(16.025, 23.025)` and `resample_draws == 2000`, both of which are functions of the draw count, and it
fell to M1.

**Resolution happens once — confirmed by code, since no test can confirm it.** `grep -n
'_resolved_resample'` gives exactly one call site, `cli.py:1551`. See Minor 3.

**Scope held.** The diff is a resolver plus two lines; no interval construction call changed. Confirmed
behaviourally: I ran a project declaring `resample: {method: bootstrap, n: 500, stratify_by: cohort}` and
the recorded column is still `method: t_over_units` with no `resample_draws` key. Task 14's work is
untouched.

**Task 11's `resample_draws` ruling is not contradicted.** `stats.summarize_step` still records
`draws_used` from `percentile_of_derived`, `None` when resampling was never attempted; threading `n`
changed only what is requested. (Note: `draws_used` is the *survivor* count, not the requested `n` — the
review brief's paraphrase is loose, but that predates this task and `stats.py`'s own docstring is
correct.)

**The routed `stratify_by` gap — constraint met.** With `stratify_by: cohort` declared, `run.yaml`
contains: the verbatim config echo under `config.statistics.resample`, and beside the interval
`method: percentile_over_units` / `resample_draws: 500`. There is no method string, no resolved-values
echo, and no field name that implies a stratified draw. `RESAMPLE_METHODS = ("bootstrap",)` independently
rules out method-string overstatement. `validate._check_resample` does check `stratify_by` names through
`units.stratum_names` (`E-STATS-RESAMPLE-STRATIFY-UNKNOWN`), so the resolver's docstring claim about
that is accurate, and `units.stratum_names`' own docstring requirement — "whenever it does, it has to
read the same declaration this way too" — is satisfied.

## Findings

### Important — the call-site comment is written from the finished slice's point of view

`cli.py:1545`:

> `statistics.resample` is honored as of H4a: the block is resolved ONCE here and threaded to every read
> site … `reference.md` § Statistical reporting requires the resolved values be recorded beside the
> interval

Two overstatements at the exact line three other modules tell a reader to "check directly"
(`validate.py:5010`, `stats.py:587`, `units.py:1143`):

1. **"is honored"** is unqualified and undated. At this commit only `n` is honored. `declared` is unread,
   `method` is unread, and `stratify_by` is resolved and explicitly not honored. The comment it replaced
   was scrupulous about this — it described its own line and said what was still open — and the
   replacement drops that. This is the slice's four-instance defect class, at the one line tasks 14–17
   will open first.
2. **"requires the resolved values be recorded beside the interval"** is a real quotation of
   `reference.md` line 2340, and the requirement is **not met at this commit**: only `resample_draws`
   (a survivor count) sits beside the interval; the resolved `method` and requested `n` are recorded
   nowhere. Cited as a rationale for resolving once it is defensible; sitting immediately under "is
   honored" it reads as a requirement this commit satisfies.

Suggested: keep the resolve-once rationale, and say plainly that at this commit `n` is the only resolved
field any read site consumes.

### Minor 1 — the resolver docstring promises what Task 14 will do

`cli.py:1037`: "a declared stratification is not yet honored for a derived metric — **only for a column,
once Task 14 wires it in**." The first half is the honest gap statement the brief asked for and is
correct. The second half is a claim about behaviour that does not exist, written in the voice of code
that provides it. If Task 14 lands stratification differently — or does not land it — this docstring is
a false guarantee with nothing pointing at it.

### Minor 2 — `method` is the one field with no type guard, inconsistently with `n`

`declared.get("method") or "bootstrap"` returns whatever non-empty value is there, so
`_resolved_resample({"statistics": {"resample": {"method": 5}}})` returns `5` for a field the task's
produced interface types `str`. Unreachable through `command_run` (`validate_config` at `cli.py:1103`
returns `EXIT_WRONG` before line 1551, and `envelope.py` types `statistics.resample.method` as `str`),
so it is not a live defect — but `n` *is* isinstance-guarded and the non-dict case *is* guarded, so the
defense is inconsistent, and tasks 14–17 consume `method` directly from a spec dict that can hold a
non-`str` when called as a unit.

### Minor 3 — the once-ness test docstring claims a discrimination it does not make

`test_the_resample_block_is_resolved_once`'s docstring: "A unit test on the resolver itself, because the
end-to-end tests above cannot distinguish 'resolved once and threaded' from 'read seven times'." The
unit test does not distinguish them either — it calls `_resolved_resample` directly and would pass
unchanged if seven sites each resolved the block independently. Once-ness is guarded by nothing in the
suite; it holds only because there is exactly one call site today, which tasks 14–17 are about to add
read sites around. The test is a good test of the resolver's *defaults* (it caught M2 and M2′); the
docstring is what overstates. Text was verbatim from the brief, so this is a brief defect the
implementer inherited — worth fixing before Task 14 rather than carried.
