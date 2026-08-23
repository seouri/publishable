# H6b batch 4 review — tasks 6 and 7

Commits reviewed: `596985a` (task 6), `1bd9483` (task 7). Branch `h6b-environment-record`.

**Verdicts: task 6 PASS. task 7 PASS**, both with findings (Minor/process only — no code or
behavioral defect found in either commit's actual content).

## Process fact established before anything else: neither task has a report file

`.superpowers/sdd/2026-08-23-environment-record/task-b4-report.md` does not exist, and neither does
`task-6-report.md` under any name — checked with `find .superpowers/sdd/2026-08-23-environment-record
-type f` and `git log --all --diff-filter=A --name-only` for the slice directory: only `task-b1..b3
-report.md` were ever committed. **The assignment's premise that "task 6's report exists" is false.**
Both tasks in this batch are unreported work, and every claim below about either commit was verified
from scratch — by behavior where a behavior existed to run, by reading otherwise — never by trusting a
report, because there is none to trust.

## Task 6 — Ruling P confirmed, Decision 12 declined and re-owned

**What I verified by behavior (not by reading the commit message).** Built a hand-assembled project
outside the repo (`publishable new` into scratch, `.gitignore`'s `__pycache__/`/`*.py[cod]` lines
removed, a real project-local template added under `templates/`, a fully valid `config.yaml` built so
`validate` could reach exit 0 rather than stopping on an unrelated error):

```
BEFORE: git status --porcelain          -> (clean)
publishable validate configs/probe-exp/config.yaml
  -> "✓ config valid", exit 0
AFTER:  git status --porcelain
  -> ?? src/probe_exp/__pycache__/
     ?? src/probe_exp/steps/__pycache__/
     ?? templates/__pycache__/
publishable run configs/probe-exp/config.yaml
  -> error E-CODE-DIRTY  src/** or templates/**  uncommitted changes; commit them first
     exit 1
```

This is an exact behavioral match for the commit's claim and for § Templates' *"goes dirty at
`validate`"* sentence: it is **TRUE as measured**, not merely as read. (First attempt at this probe
was contaminated by my own `git add -A` picking up already-generated `__pycache__/` into the initial
commit, which masked the effect — redone cleanly by untracking those paths before the clean-baseline
commit; noted here because it is exactly the kind of self-inflicted false negative this section's
checks exist to catch.)

**Clause-by-clause re-read of the whole § Templates paragraph (`docs/reference.md` line ~1715)
against code at HEAD** — the step the brief required and report:
- "editing a local `aggregate` moves the hash exactly as editing a step does, and `run` refuses a
  dirty `templates/` for the same reason it refuses a dirty `src/`" — TRUE: `cli.py:2031`'s
  `E-CODE-DIRTY` row names `"src/** or templates/**"` as one pathspec.
- "Discovery importing every file to find its registration writes `templates/__pycache__/`" — TRUE,
  confirmed above.
- "`code_hash` skips `__pycache__` directories and compiled `.pyc`/`.pyo` files unconditionally …
  applied before git is asked anything, so no ignore file could have done that for it" — TRUE, read
  `hashes.py::hashed_files`: `_SKIP_DIRS`/`_SKIP_SUFFIXES` are applied in the `rglob` loop itself,
  strictly before the `include` callable (the one that asks git via `-c core.excludesFile=`) is ever
  invoked.
- "dirty gate is what the scaffolded `.gitignore` is for … `validate` and `run` see a clean tree" —
  TRUE, `scaffold.py`'s `GITIGNORE` constant includes both lines.
- The clause the brief expected to be false — *"it reads the working tree rather than git, so no
  ignore file could have done that for it"* — **was already fixed before H6b's branch point**: `git
  log -S "it reads the working tree rather than git" -- docs/reference.md` shows it was rewritten by
  H6a task 1 (`c863e3e`), not by this batch. So there was nothing left for task 6 to delete, and the
  commit correctly makes no edit to `reference.md`. The paragraph is fully true at HEAD, verified
  clause by clause, and task 6's silence on `reference.md` is the right outcome rather than a missed
  step — though, absent a report, there is no direct evidence the implementer performed this specific
  re-read rather than arriving at the no-op by luck. I performed it myself above and it holds.

**Decision 12 (the OPEN root-`.gitignore` filing).** Re-read the amendment in `spec-defects.md`: it
is recorded as **DECLINED**, in writing, with a reason (widening `E-CODE-DIRTY`'s pathspec is a
behaviour change to a shipped command, costing every uncommitted root file a false-positive risk;
H6b is chartered additive), it is **re-owned unassigned** with a stated reason (no remaining
chartered slice owns `E-CODE-DIRTY`'s pathspec — H9 touches `reproduce`/`dry-run`/`draft`/`resume`/
`demo`/`docs`, none of which is the gate's definition; H3c-3's 14 are folds/holdouts inside cells),
and the closer's own cost accounting is named (what an uncommitted root file that is *not* a
`.gitignore` should do at the gate). It is an amendment, not a strike — the original entry's `##`
heading and body are untouched; only text is appended below it. **This matches the brief's checklist
item for item.**

**Registry check.** `grep -n '"W-' src/publishable/*.py` and `git show 596985a --stat` confirm the
only file touched is `docs/superpowers/spec-defects.md` — no `W-` code, no § Warnings/§ Validation
row, no `src/`/`tests/` change of any kind. Matches "add nothing to any registry."

**Mechanical pass on the edited file.** `grep -nP '[ \t]$' docs/superpowers/spec-defects.md` → 0 hits.
One new anchor was added, `[§ Three hashes](../reference.md#three-hashes)`; `grep -n "^## Three
hashes" docs/reference.md` confirms it resolves.

**Gates.** Full suite re-run fresh (stale `__pycache__`/pytest-of-joon cleared first):
`2971 passed, 1 skipped, 2 xfailed` — unmoved. `ruff check .` clean. `ruff format --check .`:
93 files already formatted. `mypy`: success, 52 source files. Delta: 0 tests, as required.

**Finding (Minor/process).** No report file exists for task 6 (see above) — the batch's only written
record of this task's work is the commit message. Every claim in that message was independently
reproduced by behavior or by reading in this review, and all of it held up, but the absence itself is
a process gap: per this repo's own convention (every other batch in this slice has a `task-bN-report.md`),
this one is missing, and nothing in the git history explains why.

## Task 7 — three stale claims (unreported; verified from scratch)

**`secrets.py` module docstring.** The four-key enumeration (`os`, `hostname`, `hardware`, `uv.lock`)
is deleted; the structural claim beside it ("nothing in this module imports `publishable.provenance`
or writes into the document it builds") is kept and stands alone. Verified by reading:
`grep -n "^import\|^from" src/publishable/secrets.py` shows no import of `publishable.provenance`
anywhere in the module, and `grep -n "provenance" src/publishable/secrets.py` shows the word appears
only in this docstring's own prose — never as code. Cross-checked the other direction too:
`grep -n "from .secrets\|from publishable.secrets" src/publishable/*.py` shows `secrets` is imported
BY `cli.py`, `diagnostics.py`, `freeze.py`, `report.py`, `runner.py`, `validate.py` — never the other
way — so the "cannot leak into provenance" claim is structurally sound, matching the design's own
ground for allowing the deletion (Decision 13). Correctly applies "prefer deleting a claim to
rewriting it" to a claim that actually is stale (the block became `{manager, python_version, uv_lock,
uv_lock_hash}` at task 3, so the deleted enumeration named three keys that never existed and omitted
three that did) — not a case of deleting something true.

**`study.py::_redact` docstring.** Correctly identified as the one exception the "prefer deletion"
rule allows, because the sentence's subject *is* this slice's own arrival. The dated `ebf642a`
measurement is kept and explicitly marked superseded ("superseded by H6b task 3, which added it"),
and the sentence is rewritten to state the present fact rather than the prediction. `git diff` shows
this is a pure docstring edit — no line outside the triple-quoted comment moved. Fixture E is named as
the pin, matching Decision 13's requirement.

**`tests/test_study.py::_fixture_y_record` docstring.** The `ebf642a` parenthetical and "which
nothing in this build writes" are removed, as required. **Minor deviation from the brief**: the
brief said "DELETE the parenthetical" and a pure deletion reads grammatically fine on its own
("...its only job is to exercise the `hostname` row of § What `study add` redacts. Every other field
here is..."), but the shipped edit instead substitutes new prose ("...redacts with a value hand-picked
for it, rather than one a real run happened to produce. Every other field..."), which duplicates the
docstring's own next sentence ("but the VALUES are hand-picked to exercise every redacted field at
once"). This is not a false claim — nothing in the substituted text is inaccurate — but it is a
rewrite where the brief and CLAUDE.md's own stated preference ("prefer deleting a claim to rewriting
it — a rewrite invents; a deletion cannot") called for a plain deletion. Flagged as Minor because the
content is true, not structurally load-bearing, and does not touch a pin's assertions.

**Arm S (guard pin), the one thing this docstring edit is authorized to touch.** Confirmed
`_fixture_y_record`'s **docstring only** changed — `git diff 596985a..1bd9483 -- tests/test_study.py`
shows exactly 5 lines changed, all inside the docstring, no assertion or literal moved. Ran the two
named tests directly:

```
tests/test_study.py::test_study_add_redacts_hostname_when_present_on_a_synthesized_record PASSED
tests/test_study.py::test_study_add_leaves_hostname_untouched_when_absent_from_the_source PASSED
```

**Proved arm S can still fail** (the mutation the brief asks every guard pin to survive): mutated
`_redact` to skip the `hostname` replacement (`environment["hostname"] = REDACTED` → `pass`), reran —
`test_study_add_redacts_hostname_when_present_on_a_synthesized_record` **FAILED** with the expected
`AssertionError` (raw hostname `workstation-42.hospital.internal` where `<redacted by study add>` was
expected); the sibling test still passed as its own property is unaffected. Reverted from a saved
copy of `study.py`, reran — both tests **PASSED** again, confirming the revert restored the exact
pre-mutation behavior. The pin is intact.

**Sweep for the claim, not the file it was first noticed in — reproduced independently.** Grepped
newline-insensitively (via `perl -0777`, whitespace-flattened for the third pattern) over every
`.py` file under `src/` and `tests/`, every `.md` under `docs/` (which includes all four normative
documents plus `spec-defects.md`), and `CLAUDE.md`/`README.md` at the repo root, for `never written`,
`ebf642a`, and `manager, python_version`:
- The only source-code hits for `never written`/`ebf642a` are the three sites task 7 edited
  (`secrets.py`'s unrelated *different* "never written anywhere" sentence about the credential
  mapping — read and confirmed it is about a different subject, the per-command credential dict, not
  `provenance.environment` — plus the now-corrected `study.py` sentence itself).
- Every other hit is inside `docs/superpowers/plans/**`, `docs/superpowers/specs/**`, or
  `docs/superpowers/*-SCOPING*.md` — all of which are **tracked records**, explicitly exempt from
  retro-editing per `CLAUDE.md` ("A tracked record is appended to, never retro-edited") and per the
  brief's own "what this task must NOT touch" list. Task 7 correctly left every one of these alone.
- **No hit at all** in `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`,
  `docs/reference.md`, `CLAUDE.md`, or `docs/superpowers/spec-defects.md` — so there is no live,
  mutable fourth home carrying this claim. The sweep can fail (it found the pre-edit versions of all
  three known sites when run against the parent commit as a sanity check), so this is a real negative
  rather than a filter artifact.

**What this task must not touch — confirmed clean.** `git diff 596985a..1bd9483` touches only
`src/publishable/secrets.py`, `src/publishable/study.py`, and `tests/test_study.py` — no other test
assertion, no `study.py`/`secrets.py` code line (both diffs are entirely inside docstrings, confirmed
above), and no `tests/test_cli.py` (where arms P, Q, R, T, U live) at all.

**Gates.** Same fresh run as task 6 above: `2971 passed, 1 skipped, 2 xfailed`; `ruff check` clean;
`ruff format --check` clean; `mypy` clean. Delta: 0 tests, as required.

## Findings

| # | Severity | Task | Finding |
|---|---|---|---|
| 1 | Major (process) | both | No report file exists for this batch at all — not `task-b4-report.md`, not a per-task variant — despite every prior batch in this slice having one and the assignment asserting task 6's report exists. Everything in this review was reconstructed from the diffs and commit messages and independently reverified; nothing here should be read as confirming a report that was never written. |
| 2 | Minor | 7 | `tests/test_study.py::_fixture_y_record`'s docstring edit substitutes new prose for the deleted parenthetical rather than performing a plain deletion, producing a claim that duplicates the docstring's own next sentence. Not false, not a pin risk — a style deviation from the brief's explicit instruction and from CLAUDE.md's stated preference for deletion over rewriting. |

## What I could not verify about task 7 for want of a report

Whether the implementer actually ran the sweep across the five locations the brief specifies, and
whether the choice to rewrite (rather than delete) Fixture Y's parenthetical was a deliberate,
considered substitution or an unexamined default — there is no report to say either way. I ran the
sweep myself and it is clean (see above), and I verified the guard pin still holds by mutation, so
the **outcome** task 7 shipped is sound regardless of what the stalled agent intended; only the
**process disclosure** is missing.

## Suite

`2971 passed, 1 skipped, 2 xfailed` — unmoved from the batch's stated baseline, reproduced fresh after
clearing stale `pytest-of-joon` and `__pycache__` directories.
