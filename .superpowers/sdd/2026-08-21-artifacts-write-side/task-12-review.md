# Task 12 review: filings and both consistency passes

**Verdict: FAIL** — one Critical (an entire carried finding never filed, contradicting the report's
"complete" claim), one Major (a miscounted grep the report itself quotes as its evidence).

## Findings

### Critical — Batch 8's "Fixture E is false of `.csv`" finding is not filed and not mentioned in the report

`progress.md` (batch 8, line 303) states in the development record itself: *"The design's own
Fixture E wording is false of `.csv`. … It is **filed for task 12** rather than edited into the
spec."* Reproduced directly against the code:

```
$ uv run python -c "
from publishable.artifacts import _encode_csv
print(repr(_encode_csv([{'v': None}])))
"
b'v\n""\n'
```

A `None` cell writes through `.csv` as an empty string, not as `None` and not as the literal text
`"None"` — exactly the false-of-`.csv` reading batch 8 measured. `grep -n "Fixture E\|empty
string\|None column" .superpowers/sdd/2026-08-21-artifacts-write-side/task-12-brief.md` returns
nothing: the brief handed to this task never names it, and `grep -n "empty string\|None column"
docs/superpowers/spec-defects.md` (post-commit) also returns nothing — it was never filed. The
task-12 report's own five-carry-forward and three-filings sections do not mention it either. This
is precisely the failure mode `CLAUDE.md` names by hand — *"A ledger line saying 'filed' is not a
filing"* and *"a finding routed to a task fell out of the chain between the review that raised it
and the brief written from it"* — and the report's "Status: complete. All six steps of the brief
done" claim is false while this reproducible, previously-recorded defect sits unfiled.

Verified by behaviour (ran the exact writer function against the exact fixture shape batch 8 used),
not by reading alone.

### Major — the report's own `E-STEP-KEY-COLLISION` emit-site count is wrong, by the report's own cited grep

The report says (§ `§ Errors` per-code emit-site check, task 7): *"`grep -rn
"E-STEP-KEY-COLLISION" src/publishable/` → six raise sites across `artifacts.py` and `stats.py`."*
Reran the identical command:

```
$ grep -rn "E-STEP-KEY-COLLISION" src/publishable/
```

Actual `code="E-STEP-KEY-COLLISION"` raise sites: **6** in `artifacts.py` (lines 746, 752, 760, 778,
797, 805 — the measured/plain `record` branches' `unit`/`measurement`/attribute-shadow checks, three
per branch) **plus 2** in `stats.py` (lines 3115, 3123 — the derived-key-vs-reserved-metric-name and
derived-key-vs-recorded-column checks), for a total of **8**, not 6. Confirmed each is a distinct
`raise ContractError(...)` statement, not a stray comment (comments referencing the code separately
appear at `cli.py:749,3003,3066` and `stats.py:2785`, correctly excluded from the count either way).

This does not change the report's substantive conclusion — `reference.md` line 1002's § Errors row
states the rule generically ("a derived key against a recorded column, a derived key taking the
reserved metric name `by`, a recorded column against a unit attribute, a recorded column named
`unit`, or one named `measurement`"), which does cover all eight sites without narrowing — but the
number itself, offered as the report's own verification evidence for an "every emit site" audit, is
wrong on the grep it quotes. `CLAUDE.md` names this exact shape as a recurring failure ("the second
miscount in two batches, in a column whose own framing is *counts read, not estimated*").

Verified by behaviour (reran the report's own command).

## What passed

- **np.str_/np.bytes_ row**: reproduced — `np.str_` is admitted (`str` subclass, admitted before the
  `__len__` guard), `np.bytes_` still raises `ContractError`. Row correctly closed with grounds split.
- **`Estimate.method` coercion gap**: reproduced — `_coerce_estimate` passes `method` through
  verbatim; a `np.str_` method survives coercion and `yaml.safe_dump` raises a bare
  `RepresenterError`. The stale "CLOSED by S5a" line is correctly amended (appended, not rewritten)
  and the new filing is accurate.
- **`docs/experimental-designs.md` added to sweep and swept**: confirmed present in all sweep
  command lists in the report; the file's own `E-UNITS-ATTR-COLUMN` row (line 384) is one of its
  four confirmed homes.
- **`finalize`'s `unit`-shadow value hijack**: reproduced by reading `finalize`'s attribute-merge
  loop (`merged["unit"] = owner.attributes.get(name)` unconditionally overwrites the identity when
  `name == "unit"`) and `_finalize_columns`'s own docstring, which states the residual verbatim. The
  filing's grounds (roster-resolution refusal at `validate` doesn't reach a directly-built `Unit`)
  are accurate.
- **Three newly filed gaps** (nesting writers' bare tracebacks for `.yaml`/`.json`/`.jsonl`; a
  non-`str` column key writing silently through `.csv` and raising bare `TypeError` through
  `.parquet`; the direct-`Unit` residual) — all three reproduced exactly as described.
- **Re-owning to H5b**: `H5b` is a real, chartered, unstarted sub-slice (`docs/superpowers/
  H5-SCOPING.md` § H5b, `docs/superpowers/specs/2026-08-21-artifacts-write-side-design.md` §11 and
  its corrections table). The two re-owned rows' citations to "H5b tasks 11–13" and "H5b task 15"
  match the H5a plan's own routing table verbatim.
- **§ Errors homes for `E-UNITS-ATTR-COLUMN`**: confirmed exactly 4 (reference.md ×3, experimental-
  designs.md ×1), matching the report.
- **Tasks 5 and 9 emit-site claims**: confirmed by grep — `E-UNITS-ATTR-COLUMN`/`-RESERVED` each 3
  raise sites in `units.py`; `E-ARTIFACT-UNWRITABLE` 2 raise sites in `artifacts.py`, both covered by
  the two named rows.
- **Mechanical pass**: reran trailing-whitespace/tab, en-dash-heading sweeps over the four documents
  myself — 0 hits, and proved each sweep can fail with an injected positive control.
- **`RESERVED_FIELDS` sweep**: reran the report's exact command (file list named explicitly, not
  globbed, not filtered) — 0 hits; positive control (`E-UNITS-ATTR-COLUMN`) returns hits as expected.
- **Development-record integrity**: `git show c52ea38 -- docs/superpowers/spec-defects.md` shows
  only table-row in-place replacements (the existing convention for this table's status column, not
  a deletion of prose elsewhere) and appended dated notes; no other tracked spec/plan file was
  touched. `docs/feasibility-llm-growth-studies.md` is untouched (`git diff main --
  docs/feasibility-llm-growth-studies.md` is empty) — the four-row § Executability table is
  unmoved, no fifth number introduced.
- **Diff scope**: `git diff 478639a..c52ea38 --name-only` touches only `docs/superpowers/
  spec-defects.md` and the task-12 report — the four documents, `CLAUDE.md`, and the feasibility
  analysis are untouched, so config completeness / enum comments / versions / worked-example checks
  are no-ops by construction, as the report claims.

## Gates

- `uv run ruff check .` → All checks passed.
- `uv run ruff format --check .` → 93 files already formatted.
- `uv run mypy` → Success, no issues found in 52 source files.
- `uv run pytest` → **2891 passed, 1 skipped, 2 xfailed in 189.64s** — matches baseline exactly.

## Note on method

Fixture-E finding and the collision-site recount were both established by running code directly
(behaviour), not by reading the report's prose and trusting it. Every other carry-forward and filing
was independently reproduced against the code before being credited as passing.
