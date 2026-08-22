# Task 12 report: filings and both consistency passes

**Status: complete.** All six steps of the brief done; both gates for the branch's own edits
(`docs/experimental-designs.md`, `docs/reference.md`) plus the mechanical/cross-document sweeps over
the four documents ran and are clean. `spec-defects.md` (the one exception to "never retro-edit the
development record") was amended, never retro-edited — every change is an appended note dated
2026-08-22, and nothing was deleted from a prior entry's own text.

## The five carry-forwards

1. **`units.parquet` type unification, live half CLOSED / dead half STRUCK.** Verified against
   `docs/reference.md` § The per-unit tables (lines ~991–998): task 1 states the promote/refuse rule
   and the `.parquet`-only scope, closing the live half. Struck the S5 prediction that the same slice
   "also lands non-numeric recorded columns" — that is a different question (a column non-numeric
   throughout, not one disagreeing on type within itself) and belongs to H5b, per H5a's own plan
   ("What H5a refuses to do, with the route").

2. **`np.str_`/`np.bytes_` row, CLOSED with grounds split.** Measured directly against
   `src/publishable/coercion.py`'s `_coerce_one`: `coerce_scalars({"v": np.str_("hello")}, "test")`
   returns `{'v': 'hello'}` (type `str`, admitted before the `__len__` guard — a `str` by
   inheritance); `coerce_scalars({"v": np.bytes_(b"hello")}, "test")` raises `ContractError`
   (`bytes` is not one of the four scalar types, and it has `__len__`). The entry's own pairing
   ("the two share a slice") bound one ground that closes a refusal to a different ground that
   confirms one was never a bug — both are now named, in the S4a residue table's `AMENDED` row.

3. **`Estimate.method` coercion gap.** Reproduced: `_coerce_estimate` in `coercion.py` returns
   `method=value.method` verbatim — no call to `_coerce_one` — while `value` and each `ci95` bound
   are coerced. `coerce_scalars({"v": Estimate(value=1.0, ci95=[0.5, 1.5],
   method=np.str_("t_over_units"))}, "test", scope="summary")` returns an `Estimate` whose `.method`
   is still `numpy.str_`, and `yaml.safe_dump` on it raises the bare `RepresenterError` this module
   exists to prevent. Corrected the "CLOSED by S5a, as the row already records" line — appended a
   note rather than rewriting it — and filed the gap (below), unassigned: no config-reachable
   trigger is known (a template's `aggregate` chooses `method` as a Python literal), and no
   remaining slice has `coercion.py`'s `Estimate` exemption as its surface.

4. **`experimental-designs.md` added to the sweep list, and swept.** It was already touched by this
   branch (one row added to § Mistakes core prevents, verified present — `E-UNITS-ATTR-COLUMN`'s
   fourth home). All sweeps below name it explicitly alongside the other three documents, `CLAUDE.md`,
   and the feasibility analysis.

5. **`finalize`'s `unit`-shadow entry: value hijack CLOSED for every config, list dedupe CLOSED,
   severity bound widened before being struck, wrong prediction struck, residual filed separately.**
   - Value hijack: closed by task 5's `E-UNITS-ATTR-COLUMN` (`RESERVED_COLUMNS = ("unit",
     "measurement", "by")`, one reader across `_from_table`/`_from_glob`/`_from_resolver`). Verified
     `run` meets the same refusal through `validate`'s gate (one emit path, confirmed by grep: three
     raise sites, all reached from the same roster-resolution call `command_run` makes through
     `validate_config` before its own `resolve_units`).
   - List dedupe: closed by task 8's `_finalize_columns`, whose own docstring already states the
     residual (verified by reading `src/publishable/artifacts.py`).
   - Severity bound: "confined to the published `units.parquet`" was too narrow — `read_condition`
     lets a `summary` step read another condition's `units.parquet` back, so the same shadow would
     also have corrupted what a step computes from, not only what an outside reader trusts. Widened,
     then struck along with the closed entry.
   - Wrong prediction struck: measured `E-UNITS-ATTR-COLUMN` lives in § Errors `validate` reports and
     § Validation, and not in § Errors core raises (`validate` is what reports it) — same ground the
     H5a plan's correction 11 gives for the sibling `E-UNITS-ATTR-RESERVED` filing's identical wrong
     prediction. Struck rather than rewritten.
   - Residual filed as its own entry: a directly constructed `Unit` carrying an attribute named
     `unit` still hijacks the value, unreachable from any config `validate` can see. Unassigned —
     no remaining slice charters direct-`Unit`-construction guards, and building one would be a fifth
     stoppage nobody has argued for (H5a plan correction 5).

## Filings (step 2), each unassigned with a reason

- **Three writers (`.yaml`, `.json`, `.jsonl`) raise a bare traceback for a nested NumPy scalar.**
  Measured: `io.write("x.yaml", {"v": np.float64(1.0)})` → bare `yaml.RepresenterError`;
  `.json`/`.jsonl` → bare `TypeError` for `np.int64`/`np.bool_` (np.float64/np.str_ survive because
  `json` accepts a `float`/`str` subclass on sight). Unassigned: no remaining slice (H5b, H6, H9,
  H3c-3's remaining 14) has nested-structure encoding as its surface.
- **A non-`str` column key.** Measured: `_encode_csv([{1: "a"}])` writes `b'1\na\n'` silently;
  `_encode_parquet([{1: "a"}])` raises a bare `TypeError`. H5a's contract sentence speaks to values,
  not column names. Unassigned, same reason.
- **A directly constructed `Unit` with an attribute named `unit`.** Covered above (carry-forward 5's
  residual).

## Mechanical pass (step 3), over what the branch edited

Ran over the four documents (`README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`), fenced code blocks skipped in every check.

- **Trailing whitespace / tabs**: `grep -nP '[ \t]+$|\t' <file>` per document — zero hits in all
  four. Can-fail proof: injected `"trailing space here \n"` into a scratch file and the same grep
  caught it at line 1.
- **Invisible unicode**: `grep -nP '[\x{200B}\x{200C}\x{200D}\x{FEFF}\x{00A0}]' <file>` — zero hits.
  Can-fail proof: injected a U+200B zero-width space into a scratch file; caught.
- **`×` vs `x`**: `grep -nP '(?<![a-zA-Z0-9])\d+\s?x\s?\d+(?![a-zA-Z0-9])' <file>` — zero hits in all
  four. Can-fail proof: `"3 x 5 conditions"` in a scratch file was caught.
- **En dash in a heading (anchor-forming text)**: `grep -n '^#.*–'` — zero hits. Can-fail proof: `"#
  Dose–response"` in a scratch file was caught.
- **Anchors and links**: wrote a slugger matching GitHub's algorithm (lowercase, drop non-alnum/
  underscore/hyphen/space characters with no replacement, spaces to hyphens, no collapsing) over all
  four documents' headings (skipping fenced blocks), checked every `[text](target)` — same-doc `#anchor`
  and cross-doc `file.md#anchor` — resolves, and checked for duplicate anchors within a document.
  Result: **0 duplicate anchors, 0 broken links** across 15 (README) + 11 (design-principles) + 24
  (experimental-designs) + 84 (reference) headings. Can-fail proof: appended a link to a nonexistent
  anchor to a scratch copy and it was caught (`'anchor not found in same doc'`); an earlier, cruder
  version of the slugger produced 26 false positives on real `&`/`.`/`,`/backtick-underscore
  headings, which is itself the proof the checker was sensitive to its own slugging rule — fixed
  before trusting the clean result.
- **Table column counts / empty cells**: a small parser (skips fenced blocks and separator rows,
  respects backtick spans so a `|` inside inline code isn't miscounted as a cell boundary) over all
  four documents — **0 issues**. Can-fail proof: a 3-column table with a 2-column data row was
  caught.

## Cross-document pass (step 4)

- **`E-UNITS-ATTR-COLUMN`'s four homes**, confirmed present and none narrower than the code:
  § Validation (line 272), § Errors `validate` reports (lines 628–629), § Steps and artifacts
  (line 1249), `experimental-designs.md` § Mistakes core prevents (line 384). Grep:
  `grep -n "E-UNITS-ATTR-COLUMN" docs/reference.md docs/experimental-designs.md` → 4 hits across the
  two files as listed.
- **Reserved-metric "set of one" sentence**: `grep -n "set of one" docs/reference.md` → exactly one
  hit, at § Steps and artifacts' `by`-reservation paragraph, unedited by this branch and still
  correctly describing the return-name set (`RESERVED_COLUMNS`, H5a's different set with a different
  subject, was never folded into it).
- **§ Templates' "whatever the step recorded plus every declared unit attribute"**: confirmed by
  `git diff 804271c..HEAD -- docs/reference.md | grep "plus every declared"` → no hit; the sentence
  is untouched on this branch (verified by `git diff`, not by reading alone).
- **§ Steps and artifacts' writer/reader table and the `E-ARTIFACT-UNWRITABLE`/coercion split**: read
  the `.csv`/`.parquet` rows (lines 1220–1227) against the code and the design's second controller
  ruling — `.parquet` keeps accepting a structural/`bytes` cell byte-faithfully, `.csv` refuses one;
  cross-row type disagreement is stated only for `.parquet`. Consistent with
  `src/publishable/artifacts.py`'s `keep_structural` branch in `_check_column_types`.
- **`E-STEP-RETURN-TYPE` row against the finished code**: confirmed the row states both the
  int/float promotion boundary and the bool/int, str/int refusal, matching § The per-unit tables.
- **Config completeness, enum comments, versions**: confirmed no-ops by `git diff` — no
  `config.yaml`/`run.yaml` example touched, no `# a | b | c` enum comment line added, no version
  string touched.
- **§ Executability's four-row table**: `git diff 804271c..HEAD -- docs/feasibility-llm-growth-
  studies.md` → empty diff, file untouched. Swept the whole branch diff for a fifth number:
  `git diff 804271c..HEAD -- README.md docs/design-principles.md docs/experimental-designs.md
  docs/reference.md CLAUDE.md docs/feasibility-llm-growth-studies.md | grep -nE '^\+.*[0-9]+ of
  [0-9]+|^\+.*now execute'` → no hits.
- **A sweep for every string the branch removed**: `git diff 804271c..HEAD -- src/ tests/ docs/
  CLAUDE.md` for removed identifier-shaped tokens surfaced `RESERVED_FIELDS` (renamed to
  `UNIT_FIELDS`/`RESERVED_COLUMNS`) among others. `grep -n "RESERVED_FIELDS" README.md docs/design-
  principles.md docs/experimental-designs.md docs/reference.md CLAUDE.md docs/feasibility-llm-growth-
  studies.md` → **zero hits** (filtering the file list to those six names explicitly, not the grep
  output). Positive control that the grep mechanism itself works: the same pattern style against
  `E-UNITS-ATTR-COLUMN`, known present, returns hits in `docs/reference.md` (3) and
  `docs/experimental-designs.md` (1). `RESERVED_FIELDS` still appears, correctly, in the dated
  development record (`spec-defects.md`, `H5-SCOPING.md`, the plans and design spec) describing the
  pre-rename name historically — left alone, per "never retro-edit the development record."

## `§ Errors` per-code emit-site check for tasks 5, 7, 9

- **Task 5 — `E-UNITS-ATTR-COLUMN` / `E-UNITS-ATTR-RESERVED`.** `grep -rn` in `src/publishable/
  units.py` finds three raise sites for each code (`_from_table`, `_from_glob`, `_from_resolver`),
  and `docs/reference.md`'s § Errors row (lines 628–629) states the rule generically ("`data.units.
  attributes` names ...") rather than by source, so it already covers all three without narrowing.
  `run`'s path is covered by the same row's "one emit path, not two surfaces" sentence, verified
  against `command_run`'s validate-first order.
- **Task 7 — widened `E-STEP-KEY-COLLISION`.** `grep -rn "E-STEP-KEY-COLLISION" src/publishable/` →
  six raise sites across `artifacts.py` and `stats.py`. `docs/reference.md` line 1116's § Errors row
  states the rule as a property of the recorded column ("a recorded column named `unit`, or one
  named `measurement`"), not by which `io.record` branch raised it, so task 7's new plain-branch site
  is already covered by the existing row's wording rather than needing a new one.
  § Steps and artifacts line 1002 independently states the same rule for both branches.
- **Task 9 — `E-ARTIFACT-UNWRITABLE` split, `E-STEP-RETURN-TYPE` widened.** `grep -rn
  "E-ARTIFACT-UNWRITABLE" src/publishable/artifacts.py` → two raise sites (`_check_column_types`'s
  non-mapping-row check, and `write`'s unregistered-suffix-and-non-bytes/str check); reference.md's
  two rows (line 1102's containment-escape row and line 1225's writer-contract row) between them
  cover both, and the writer-contract paragraph (lines 1225–1227) documents the split precisely —
  `.csv` refuses a structural/`bytes` cell with `E-STEP-RETURN-TYPE`, `.parquet` accepts one and no
  longer raises `E-STEP-RETURN-TYPE` for that shape, and a non-mapping row is refused by both formats
  with `E-ARTIFACT-UNWRITABLE`.

## Gates

- `uv run ruff check .` — all checks passed.
- `uv run ruff format --check .` — 93 files already formatted.
- `uv run mypy` — success, no issues found in 52 source files.
- `uv run pytest` — **2891 passed, 1 skipped, 2 xfailed in 192.07s**, matching the baseline exactly.
  This task touched only `docs/superpowers/spec-defects.md` and this report, so the count was
  expected to be unchanged, and it is.

## Concerns

- None found that block this task. The three newly filed gaps are all pre-existing behaviour (not
  introduced by H5a), reproduced directly rather than inferred, and each carries a stated reason for
  being unassigned rather than orphaned.
