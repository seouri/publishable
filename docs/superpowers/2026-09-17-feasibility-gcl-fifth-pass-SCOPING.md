# Scoping: fifth pass of `feasibility-growth-chart-literacy.md`

**Measured 2026-09-17 against `publishable@af0d3d5`.** Every claim below was read off the code,
the git history, or a command's output — not off the documents. This scoping exists because the
analysis' fourth pass is dated 2026-09-13 and **all three of its pins have since moved**, one of
them in the tree `code_hash` covers, which the document's own argument said had not moved.

Per `CLAUDE.md`, a scoping expires and every charter re-scoped in this project was stale **in the
same direction — under-counted and missing surface**. That is the finding again, and this pass
does not rewrite the analysis: 3,784 lines of it are unaffected, three sections are not.

## The four gates, at this commit

Run in the order `CLAUDE.md` fixes, quoted as printed rather than summarised:

| gate | command | result |
|---|---|---|
| tests | `uv run pytest` | **3622 passed, 1 skipped, 2 xfailed** in 121.96s |
| lint | `uv run ruff check .` | `All checks passed!` |
| format | `uv run ruff format --check .` | `102 files already formatted` |
| types | `uv run mypy` | `Success: no issues found in 56 source files` |

## Every pin has moved, and one of them breaks a standing argument

| pin | analysis says | actual, 2026-09-17 | drift |
|---|---|---|---|
| `publishable` (executability) | `549dcb3` | `af0d3d5` | 3 commits, **`src/**` among them** |
| the plan | `d346683` (header), `e69489b` (executability) | `728ba69` | 73 commits, 10 touching the plan document, 7 of those after `e69489b` |
| `2026-08-28-gcl-measurement` | `087e071` | `c7db460` | 12 commits |

**The standing argument that is now false.** § Executability reads: *"the same fourteen validate
rows … **fourteen** commits: `git diff 9a7844c..549dcb3 -- src templates` is **empty**, and all
fourteen are re-measurements of this very document or repairs to its own guards."* That sentence is
the reason the document could claim its figures survived fourteen commits. Measured now:

    git diff 549dcb3..af0d3d5 -- src templates
    => 3 files changed, 194 insertions(+), 6 deletions(-)

`src/publishable/{cli,run_record,runner}.py`. **Core has moved for the first time since this
analysis was written**, so the argument has to be re-derived rather than have its number patched.

## The central finding: core gained a feature because of this study, and the analysis is silent on it

`456a3db` and `af0d3d5` exist because of **E3 of the project this document analyses**, and the
document does not mention either. The chain, each link measured:

1. The analysis specifies `max_failed_fraction: 0.2` in **all fourteen** configs, and E3's plan as
   **27,000 metered calls = 9 × 5 × 600** (§ The fourteen configs, line 425; § Cost and execution
   summary).
2. `docs/superpowers/2026-09-14-resuming-a-truncated-run-SCOPING.md` names the failure by record:
   `2026-08-28-gcl-measurement-data/.../run_2026-09-13T20-04-32Z_c1a577a` — the study's own tree.
   `step03_screen` raised `RemoteDisconnected` on one execution of 45, **19,800 calls into the
   27,000**.
3. `_units_failed_anywhere` charged **every unit of that raised execution** — 300 of a 600-unit
   roster — so `0.5 > 0.2` and the plan broke with **11 of 45 executions never attempted**.
4. `run.yaml` was written, and `E-RESUME-RUN-ENDED` then refused every resume. **One dropped socket
   cost 19 hours of metered work with no route back at any price.**
5. Core changed twice in response: `af0d3d5` made a *raised* execution contribute no unit failures,
   and `456a3db` made `resume` continue a truncated run into a fresh `run_<id>/`.

A feasibility analysis whose own recommended threshold produced a core defect, and which does not
yet carry the fix, is stale in the way that matters most: the next person to run E3 would read the
document, set `0.2`, and not know what it used to mean or that recovery now exists.

## What changed in core, and which section each lands in

**1. `max_failed_fraction` produces `partial`, not `failed`.** `reference.md` listed it among "four
things" that produce `failed`; the code never agreed — the reason is threaded to `run_status` and
deliberately left out of its mapping. Corrected in the document, not the code, because the code is
right: a run whose guard fires with 33 executions recorded has a great deal to report. **The
analysis makes no prose claim either way, so it carries no stale sentence — but it now owes the
consequence**, because a `partial` E3 is resumable and a `failed` one is not.

**2. A raised execution contributes no unit failures.** The arithmetic for E3's own shape:

| | old accounting | new accounting |
|---|---|---|
| one raised execution of 45 | charges 300/600 = **0.50 > 0.2** → plan stops | charges **0** |
| units needed to trip 0.2 | — | **121 of 600**, genuinely unsettleable |

So `0.2` does not change as a *recommendation* and changes completely in *meaning*: it guarded
outages by accident and now guards attrition on purpose, which is what it was declared for. What
the change deliberately leaves uncovered, and the analysis should say: a step that raises part-way
through its units on **every** execution trips no threshold and runs the plan to its end.

**3. A truncated plan is continuable, and the surface is entirely absent here.** `continues` and
`E-RESUME-RUN-ENDED` have **0 hits** in 3,784 lines. What exists now: a `truncated` block carrying
`reason`, `planned`, `attempted` and the `outstanding` triples, absent rather than null when the
plan ended; `resume` on such a directory allocating a fresh `run_<id>/` beside it, copying
everything but `run.yaml` and `lock`; `identity.json` carrying `continues` so a continuation cannot
claim inherited work. **Two stop reasons are continuable and one is not** — `max_failed_fraction`
and an unreachable apparatus recover, a *changed* apparatus fact cannot, and `E-RESUME-RUN-ENDED`
says so by name.

**A structural question, checked and answered No.** § One repository, fourteen configs works out how
fourteen runs share one directory, and a continuation allocating a second `run_<id>/` looked like it
might break that. It does not: each config declares its own `data.output_dir`
(`/secure/results/gcl/e03-serialization` and thirteen siblings), so a continuation lands inside that
config's own output directory. The consequence worth stating is narrower — **one logical attempt can
now span two run directories linked by `continues`**, so anything that reads "the run" for E3 must
follow the chain rather than assume one directory per config.

## What this pass did NOT re-measure, and the dependency by name

`CLAUDE.md` allows an executability claim to **quote its table or name the dependency**, and this is
the second:

**`62 conditions, 450 executions, 106,260 unit-executions` and the "sixteen byte-identical blocks"
were not re-measured.** Reproducing them needs the fourteen-config scaffold the fourth pass built —
a git repo, `publishable new`, a `src/growth_chart` package carrying both template classes and the
step classes, the plugin, and a `uv.lock` — and that scaffold is not in this repository.

**Evidence that the number cannot have moved, offered instead of the number being carried
silently:** the sole `runner.py` change in the interval is inside the failure-fraction accounting,
gated on `if r.status != "completed": continue`. Plan enumeration — conditions, executions and
unit-executions — is untouched, and the suite that covers it passes (3622). That is an argument, not
a measurement, and it is labelled as one. **Re-running it is the first item in the next-steps list.**

> **Corrected the same day, and this scoping was wrong in the direction it warns about.** The
> scaffold was not missing: `2026-08-28-gcl-measurement` carries all fourteen configs,
> `src/growth_chart/`, both templates, and `publishable` as an **editable path install pointing at
> this checkout**. Nothing needed building. Re-measured at `af0d3d5`: `validate` accepts **14 of
> 14** and `dry-run` sums to **62 / 450 / 106,260**, all three matching. The dependency named above
> was real in form and false in fact — the apparatus was one directory away — which is this
> project's *under-counted and missing surface* failure applied to a scoping's own inventory of what
> it cannot reach. The **sixteen byte-identical blocks** remain unchecked and that dependency is
> genuine.
>
> A **fourth pin** also moved and the table above omitted it: `publishable-growth-chart`, pinned by
> the analysis at `368e520`, is at `f06bfbb`.

## Gaps this pass found

| # | gap | where |
|---|---|---|
| A | The analysis' "`src templates` is empty for fourteen commits" argument is false at `af0d3d5` | § Executability |
| B | The continuation surface (`resume` on truncated, `truncated` block, `continues`, `E-RESUME-RUN-ENDED`) is absent | § What core refuses; § Executability |
| C | `max_failed_fraction: 0.2` in fourteen configs carries no note of what it now means, or that it once stopped E3 | § The fourteen configs |
| D | One logical run can span two directories; the directory-sharing section assumes one per config | § One repository, fourteen configs |
| E | E3's own 19-hour loss is absent from § Cost and execution summary, which is where a reader budgets | § Cost and execution summary |
| F | **Not a gap in this document — a defect in the plan.** `growth-chart-literacy.md` still describes the generator as `93/102` (at `7b41f43`, 2026-09-15). The generator is at **34 of 35 criteria** pooled over 36 seeds (`growth-chart-literacy@728ba69`), and `93/102` is a **per-pool row count**, which that project twice established is noise on the fall family | the plan, not here |
