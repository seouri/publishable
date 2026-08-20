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

## Whole-branch fix round

Read `.superpowers/sdd/2026-08-19-apparatus-part-a/whole-branch-review.md` in full. Verdict: merge
with items owed, no Critical, three Majors, four Minors — merge held on Major 2. Fixed Major 1,
Major 2 and Major 3; closed Minors 1 and 2; recorded Minor 3 as a fact rather than a fix (there is
nothing to change — see below). Commits `06bc38d`, `0f29b8a`, `eafb222`, `69c7ced`.

### Major 2 — a fact value containing a declared credential was published verbatim

**Changed:** `apparatus.check_facts`'s credential check (step 2) matched only by exact equality
(`value == cred_value`); `secrets.redact`, over the identical value set
(`credential_values(declared_credential_names(...))`), matches by substring. Changed to
`cred_value and cred_value in value` — the same matching `redact` already uses, guarded against an
unset credential the same way `redact` guards one. The refusal message still names the fact's key
and the credential's name, never the value (unchanged from before, verified still true).
`docs/reference.md`'s `E-APPARATUS-FACT-CREDENTIAL` row rewritten to say "exact value or substring
containment."

**Verified by:**
- Wrote `test_a_fact_value_containing_a_declared_credential_is_refused` and
  `test_the_containment_refusal_also_names_the_variable_and_never_the_value` in
  `tests/test_apparatus.py` (direct call to `check_facts`). Ran against the pre-fix code first:
  the first passed (mistakenly — see below) but the message test failed with `DID NOT RAISE`,
  confirming the containment case slipped through.
- Wrote `test_a_fact_value_containing_a_declared_credential_fails_the_command_end_to_end` in
  `tests/test_cli.py`, driving a probe module returning
  `{"endpoint": "https://api.example.com/v1?key=" + token}` through the real
  `main(["run", ...])`. **Reverted the fix and re-ran**: the test failed, reproducing the review's
  exact finding by a slightly different path — exit 1 but under `E-APPARATUS-FACT-MISSING` rather
  than a clean exit 0, because this fixture's probe returns `endpoint` while the template declares
  `apparatus_facts = ["model_revision"]`, so the missing-key check fires before the credential
  check would have run at all either way. This confirms the fixture reaches the credential-check
  code path in the fixed version, and that the reproduction is real rather than a fixture accident.
  Restored the fix, re-ran: exit 1, `E-APPARATUS-FACT-CREDENTIAL`, no `run.yaml`, `lab7` absent from
  every byte of every artifact under the results directory.
- `diff` against a saved pre-fix copy of `apparatus.py` after restoring: byte-identical.

### Major 1 — a non-`str` `apparatus_probe` silently read as "no apparatus" at both surfaces

**Changed:** `validate._check_probe` (the sole place both surfaces route through, since
`command_run` calls `validate_config` before ever inspecting `apparatus_probe` itself and returns
on `c.has_errors`) now reports `E-PROBE-UNKNOWN` for any `apparatus_probe` that is not `None` and
not a usable non-empty `str`. `None` stays the one documented spelling of "no probe declared" and
draws nothing. `cli.py:2402`'s own `isinstance` guard is untouched — the review's own words, "which
also makes `cli.py`'s isinstance the belt-and-braces it reads as," describe exactly why: with
`validate` now refusing the malformed declaration and `command_run` returning before that line is
ever reached, the guard there stops being reachable with bad data in the one built command that
constructs an `Observer`. `docs/reference.md`'s `E-PROBE-UNKNOWN` row updated to state the type
case.

**Verified by:**
- Wrote `test_a_non_str_apparatus_probe_is_reported_rather_than_silently_skipped` in
  `tests/test_validate.py`, with a project-local template declaring `apparatus_probe =
  ["wbr_probe"]`. Ran against the pre-fix code: `KeyError: 'E-PROBE-UNKNOWN'` — confirmed silent.
- Wrote `test_a_non_str_apparatus_probe_fails_the_command_before_any_run_directory_exists` in
  `tests/test_cli.py`, driving the same shape through `main(["run", ...])`. **Reverted the fix and
  re-ran**: `assert main(...) == expect_exit` failed with `0 == 1` — the run completed, wrote
  `run.yaml`, and (confirmed by the harness's own stdout capture) recorded nothing about the
  malformed declaration. Restored the fix, re-ran: exit 1, `E-PROBE-UNKNOWN` in the output, no run
  directory created at all (`doc["run_dir"] is None`, `not list(doc["results_dir"].glob("run_*"))`).
- `diff` against a saved pre-fix copy of `validate.py` after restoring: byte-identical.

### Major 3 — a sentence pointing at § Executability for an answer it did not contain

**Changed:** added `### Measured on 2026-08-19 against commit `06bc38d` — after H7d Part A` to
`docs/feasibility-llm-growth-studies.md` § Executability on this build, the section batch 1's
rewrite (line 825, and the identical rewrite at line 937) pointed a reader at. States what the
apparatus mechanism now does, the zero/six/three figures (cited from the whole-branch review's own
re-measurement through `validate_config` on E1 and C1, rather than re-run a third time on an
identical fixture — worded honestly as a citation, not as a fresh run I did not perform), and the
honest statement of what changed: a probe-declaring run would now record five real sub-keys and
could newly earn one of five codes or a warning, none of it exercised by these nine configs since
none declares a probe a real plugin backs.

**Verified by:** reading the section before and after (confirmed no other apparatus mention existed
at any date, confirmed the new entry is the last one and precedes `## Cost and execution summary`
correctly), and by the anchor-resolution script (24 links, 0 missing) run against this file after
the edit.

### Minor 1 — the no-sweep condition key `"00"`

Added one sentence to § The apparatus files: a run declaring no `sweep` has one condition, keyed
`"00"` (the `<nn>_<label>` scheme with an empty label) rather than `"None"` or a literal `null`,
citing the canonical-JSON sort-keys reason already stated for the code's own choice.

### Minor 2 — a three-place enumeration where reference.md now names four

`docs/experimental-designs.md`'s apparatus row named `dry-run`, run start, and before every
execution; added `freeze` as the fourth, matching `reference.md` and `condition_key`'s vocabulary.
Confirmed by an **unfiltered** sweep of `dry-run` across all six documents (`README.md`,
`design-principles.md`, `experimental-designs.md`, `reference.md`, `CLAUDE.md`,
`feasibility-llm-growth-studies.md`) that no other three-place enumeration remains outside the
feasibility analysis's own (exempt from the cross-document pass, as the review itself notes).

### Minor 3 — noted, not fixed, because there is nothing to fix

Task 16's report was correct: § Validation's "Probe is installed" row needed no change, because
every check this slice adds needs a call and § Validation is the table of checks that don't.
`reference.md`'s existing "Six things deliberately absent from that table" paragraph already states
this. Recorded in `progress.md`'s fix-round entry so a later reader does not re-file "no
`E-APPARATUS-*` § Validation row" as a missing row.

### Minor 4 — batch 5 unreviewed

Closed by the whole-branch review itself, which reviewed tasks 14, 16 and 17 directly and found
them sound.

### Ledger and CLAUDE.md, the other two items the review named as owed at merge

- `progress.md`'s batch-5 entry and the whole-branch review's own findings were already recorded
  (commit `4cb8ed1`, made before this fix round began) — confirmed present, not re-added. This
  round appended its own "Fix round" entry recording what was changed and verified for each finding
  (commit `69c7ced`).
- `CLAUDE.md` gained an "H7d Part A" paragraph (merge date, the zero/six/three figures, the five
  codes and one warning, the two Majors closed the same day) and the H7b Part B paragraph's stale
  clause — *"filed, owned by H7d"*, describing the false `apparatus: null` gap in the present
  tense after H7d Part A closed it — was amended in place with a forward pointer, on this repo's
  own convention (`7fb413d` for H4d) of a separate `docs: CLAUDE.md records <slice>` commit
  (`eafb222`).

### Final state after the fix round

- Commits: `06bc38d` (Major 1, Major 2, Minor 1, Minor 2), `0f29b8a` (Major 3),
  `eafb222` (CLAUDE.md), `69c7ced` (ledger).
- Test summary: **2423 passed, 1 skipped, 2 xfailed** (2418 baseline + 5 new tests: 2 direct-call
  in `test_apparatus.py`, 2 end-to-end in `test_cli.py`, 1 direct-call in `test_validate.py`).
- Gates: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` (46 source files) —
  all clean.
- Every mutation (reverting a fix to reproduce the review's finding) checked against the body of
  the test it reproduces first, run to completion, then reverted by restoring a saved pre-fix copy
  and re-verified by re-running — never by `git checkout -- <file>`.
- Findings not closed: none. All three Majors, both actionable Minors, and both remaining
  "owed at merge" items (ledger, CLAUDE.md) are closed. Minor 3 needed a note, not a fix, and Minor
  4 was closed by the review's own act of reviewing batch 5.
