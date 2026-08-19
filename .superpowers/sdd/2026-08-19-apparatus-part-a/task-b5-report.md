# Batch 5 — tasks 14, 16, 17 — the residue that closes H7d Part A

Commits `5fc26fa` (task 14: `validate` calls no probe), `80c2b2c` (task 16: one row per code),
`e15c474` (task 17: the filings). This report: `task-b5-report.md`.

## Status

All three tasks complete, in order 14 → 16 → 17, each committed separately. Suite: **2417 → 2418**
(task 14's one new test; tasks 16 and 17 are documents-only, `previous + 0` each, as their briefs
require).

## Task 14 — the guard: no `validate` path calls a probe

`tests/test_validate.py::test_no_validate_path_calls_a_declared_probe` (installed, registries,
git_repo, write_config, tmp_path). A real installed distribution registers `loud_probe`, whose
module writes a flag file and then raises `RuntimeError`. A project-local template
`loud_probing` declares `apparatus_probe = "loud_probe"`. `validate_config` on a config naming
that template resolves the probe's *name* cleanly (`_check_probe`'s metadata scan) and calls it
**never**: the flag is absent and the findings set is exactly `set()` — the same empty set the
`generic` golden config produces, which is the control that the check reached and passed
`_check_probe` rather than never getting that far.

**Mutation, applied where the behaviour lives** (`validate.validate_config`, inside
`_check_probe`'s success branch): added a call `apparatus._probe_for(declared)(None)` right after
`if declared in known: return`. Result: **FAIL** — the test raised `RuntimeError: a validate path
called the probe`, propagating out of `codes()`, and the flag file existed on disk. Reverted by
deleting the two added lines; re-ran and confirmed **PASS**, with `diff` against a saved copy of
`validate.py` showing **byte-identical** to the pre-mutation file. This is a pin of behaviour, not
of a string or a crash: the mutation's two branches differ in exactly the property the guard
exists to catch (a call happened, and left evidence).

Gates clean (ruff check, ruff format --check, mypy — 46 files). Full suite: **2418 passed, 1
skipped, 2 xfailed** (previous 2417 + 1).

## Task 16 — one row per code

**How the codes were enumerated:** by reading `src/publishable/apparatus.py`'s raise sites
directly — `observe_once`'s `E-APPARATUS-RAISED`, `check_facts`'s four raises (`E-APPARATUS-RETURN`
×3 sites/1 code, `E-APPARATUS-FACT-CREDENTIAL`, `E-APPARATUS-FACT-TYPE`, `E-APPARATUS-FACT-MISSING`,
in that execution order), `Observations.warn_unanswered`'s `W-APPARATUS-UNANSWERED` — and
`src/publishable/cli.py`'s probe-dispatch wrapper (`apparatus._probe_for` call, `E-PROBE-UNKNOWN` /
`E-PLUGIN-LOAD` / `E-PLUGIN-DECORATOR`), never from the brief's prose first. Confirmed after, by a
sweep over `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`,
`docs/reference.md`, `CLAUDE.md` and `docs/feasibility-llm-growth-studies.md` for each of the six
new identifiers: each appears exactly once, in its own new row. Can-fail control: the same sweep for
`register_probe` returns 7 hits across that file list, proving the sweep isn't vacuously empty.

**Placement:** § Errors core raises is topically ordered (not alphabetical — confirmed by reading
its existing sequence), so the five `E-APPARATUS-*` rows were inserted as a block immediately after
the existing `E-RESOLVER-YIELD` row, the nearest thematic sibling (a returned-value check at core's
boundary). § Warnings core reports and § Errors validate reports are alphabetically ordered by code
(confirmed by reading), so `W-APPARATUS-UNANSWERED` was inserted first (before `W-DATA-CLUSTER-
UNDECLARED`), and `E-PROBE-UNKNOWN`'s existing row (already correctly positioned) was rewritten in
place to state dual-surface — `apparatus._probe_for` raises the identical code, from the identical
metadata scan, at dispatch.

**A defect found and fixed beyond the brief's explicit six-row list:** the existing
`E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD` rows described their reach as *"a resolver source's
dispatch, at `validate` as well as at `run`"* — accurate before this slice, and now under-describing
what the code does, since `apparatus._probe_for` dispatches through the identical
`check_registration`/`load_entry_point` functions (confirmed by reading `plugins.py` and
`apparatus.py`, and by reading `cli.py`'s dispatch-wrapper comment, which states this explicitly).
Both rows were extended to name the probe case, with its asymmetry stated: unlike a resolver, a
probe is dispatched only at `run`, never at `validate`, because `validate` calls no probe at all
(task 14's own guard). This is the shape `CLAUDE.md`'s own misreading table names — *"scoping a
diagnostic by the helper it calls"* — so it was corrected rather than left.

**§ Validation's "Probe is installed" row**: read, confirmed unchanged (it is `validate`'s own row,
and every check this slice added needs a call, which is exactly what that row is not), and left
untouched, as the brief instructs.

**§ Artifact layout's run tree**, **§ The apparatus core can only observe**, **§ The apparatus
files**, and `experimental-designs.md`'s apparatus row: all read against Decision 1's `dry-run`-
siting fix and task 8's ledger-path insertion. All four already reflect the current code — fixed by
earlier batches in this slice (task 1's commit `0113fce`, task 8's commit `f1be329`) — and needed no
further change here.

**`CLAUDE.md`'s misreading-table row**: the `apparatus_facts` clause was deleted (not rewritten
around) now that task 5's `check_facts` gives it a reader — `field_convention` is now named as the
sole remaining example.

**Mechanical pass**: every link/anchor in `docs/reference.md` resolves (761 checked programmatically,
0 missing); no duplicate-heading anchors introduced; no trailing whitespace or tabs in touched files;
three pre-existing table column-count "mismatches" the naive checker flags (lines 601, 1651, 3480)
are all escaped pipes (`\|`) inside cell prose, none on a line this commit touched.

Suite unchanged: **2418 passed, 1 skipped, 2 xfailed** (previous + 0, documents only).

## Task 17 — the filings

Each entry re-read against the code at this branch's HEAD before touching it, per the brief's step
1. Claims re-verified, not carried:

- **"a run whose template declares an installed probe records a false `apparatus: null`"** (Owner
  H7d): re-checked `cli.py`'s provenance dict directly — the unconditional `"apparatus": None` the
  entry describes is gone, replaced by `observer.block() if observer is not None else None` (task
  11's commit `e833070`). **Struck**, original text kept below the closure note.
- **`PROBES`/`RESOLVERS`, `PROBES` half**: re-checked that `apparatus._probe_for` calls
  `declared_names(PROBE_GROUP, fn)`, which `plugins._registry_for` resolves to the `PROBES` dict
  itself. The entry's own stated reason for being a filing rather than a fix — *"a reader for
  `PROBES` means executing a probe"* — is exactly what task 3 shipped. **Struck the `PROBES` half
  only**; the `RESOLVERS` half was already amended closed by H7b Part B task 30 and is untouched.
- **`BaseTemplate.field_convention`**: re-checked that `cli.command_run` passes `apparatus_facts` to
  `Observer` and `apparatus.check_facts` reads it (raising `E-APPARATUS-FACT-MISSING`). **Amended**
  to name `field_convention` as the sole remaining member of the family — still unassigned; this
  slice does not adopt it, per the brief.
- **`EXIT_EXTERNAL = 5`** (NEW, Owner Part B): re-confirmed by grep at this branch's HEAD — one
  definition in `diagnostics.py`, no reader anywhere in `src/` or `tests/`. **Filed**, narrowed to
  what is actually owed: a reader plus the documented 5-wins-over-3-and-4 precedence (design's §
  Out of scope, task 18 — I initially mis-cited this against the design doc's "Corrections" section
  and against tasks 17/19 alone; corrected in the same edit pass to cite the plan's own Corrections
  correction 13 for the measurement, and the design's Out of scope table's task 18 specifically for
  the reader, naming tasks 17 and 19 as the sibling decisions it depends on rather than restating
  them).
- **Untouched, named so neither is folded in**: the two `required_env` filings and `io.reuse_from`.

**Payoff sentence, written once**: Part A unblocks **zero** configs; **six** with no remaining
core-side blocker and **three** executable, both unmoved — the only direction this slice can move a
config-level count is down. It retires no refusal and mints five error codes and one warning. A
closed filing is not an executable-run count.

Suite unchanged: **2418 passed, 1 skipped, 2 xfailed** (previous + 0).

## Disagreements between a brief/the design/the plan and the code

Two, both self-caught and corrected before this report, in the spirit of this slice's own recurring
finding ("three batches claimed zero and two were wrong"):

1. **Task 17's own first draft mis-cited its `EXIT_EXTERNAL` measurement's source document** — I
   first wrote "`docs/superpowers/specs/2026-08-19-apparatus-part-a-design.md` § Corrections
   against the code, correction 13," but that section lives in the **plan**
   (`docs/superpowers/plans/2026-08-19-apparatus-part-a.md`), not the design doc — confirmed by
   `grep -rn "^## Corrections against the code" docs/superpowers/`. Corrected before committing.
2. **The same draft cited "§ Out of scope, tasks 17 and 19"** for what retiring `EXIT_EXTERNAL`
   needs, omitting task 18 — the design's own Out-of-scope table names task 18 as `EXIT_EXTERNAL`'s
   own reader-and-precedence task, with 17 (`run_status` contract) and 19 (unreachable-vs-moved
   distinction) as sibling dependencies. Confirmed by reading the table directly and corrected
   before committing.

No disagreement found between the design/plan and the shipped code itself in tasks 14, 16 or 17 —
every row and filing written here matches what `apparatus.py`, `cli.py`, `validate.py` and
`plugins.py` actually do, verified by reading and, for task 14, by a mutation.

## Final state

- Commits: `5fc26fa`, `80c2b2c`, `e15c474`.
- Test summary: **2418 passed, 1 skipped, 2 xfailed** throughout (2417 baseline + task 14's 1 new
  test; tasks 16 and 17 are documents-only).
- Gates: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` (46 source files) —
  all clean after every commit.
- Concerns for review: none outstanding. The two self-corrections above are disclosed rather than
  hidden; both were caught before committing, by re-reading the cited section rather than trusting
  the first draft.
