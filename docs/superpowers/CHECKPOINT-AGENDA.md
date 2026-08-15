# S5 checkpoint agenda — audit of `spec-defects.md`

All 98 `##` entries in `docs/superpowers/spec-defects.md` (2491 lines) were read and classified,
and every entry making a factual claim about current code was checked against `HEAD`. The file is
**less open than its headings suggest and more stale than it admits**: 31 entries are pure records
of a minted identifier, 20 are answered, 6 are historical duplicates preserved beside their
revisions, and 41 still owe something — but of those 41, the large majority owe *one* document
change (a registry line), not a code decision. Eleven distinct stale claims were found. Five are
open-looking entries whose defect was fixed by a later entry that never amended the earlier
heading; three are records that understate a divergence which has since grown; two are claims that
are simply false at `HEAD`; one is a miscount. Two entries the task flagged for verification turned
out **still true** (`rank_family`, `SystemExit`), one turned out **not reachable but only
incidentally so** (`float()` on an `aggregate` return), and one names an owner slice — S5b — that
merged without doing the work. The single largest owed document change is not recorded as an entry
at all: **105 of the 130 identifiers `src/` emits appear in none of the four documents.** That
number splits three ways and only one part is genuinely owed — see item 1. Separately, one
identifier the documents *do* name, `E-UNIT-IMMUTABLE`, is implemented nowhere in `src/` or
`tests/`.

## Genuinely open items, ranked by consequence

| # | Line | Item | What closes it | Owner named |
|---|---|---|---|---|
| 1 | — | 105 live identifiers appear in no document, but only part of that is owed: **14** are `-UNSUPPORTED` codes deliberately left out (entries 1416, 1515 state this as policy — they retire with their slice); **13** are warnings blocked on item 2; the remaining **78** are errors, of which **12 are raise-time `ContractError`s that belong in § Errors core raises by that table's own framing** — `E-REPL-SEED-COLLISION`, `E-STEP-NAME-COLLISION`, `E-STEP-EXISTS`, `E-STEP-SCOPE-UNKNOWN`, `E-STEP-SCOPE-ONLY`, `E-STEP-UNIT-UNKNOWN`, `E-STEP-UNIT-SETTLED`, `E-STEP-UNITS-CONTRACT`, `E-STEP-READ-CONDITION-UNKNOWN`, `E-STEP-READ-REPEAT-REQUIRED`, `E-STEP-ESTIMATE-CI95`, `E-STEP-ESTIMATE-VALUE` | Add those 12 rows; leave the `-UNSUPPORTED` family out on the existing policy | Nobody — implicit in ~25 entries |
| 1b | — | `E-UNIT-IMMUTABLE` is named in `reference.md` § Errors core raises ("a write through a frozen `Unit`") and exists in neither `src/` nor `tests/` | `units.py:24` is `@dataclass(frozen=True, eq=False)`, so a write raises `dataclasses.FrozenInstanceError` — no `.code`, and not a `PublishableError` for `main` to catch. Either implement the coded refusal or drop the promise | **Not recorded in `spec-defects.md` at all** — found by this audit |
| 2 | 823 | No warning registry exists to hold 23 `W-` codes; entry declines to "close it badly" | A document design decision: a diagnostics registry, or § Validation's table as the home | S5 checkpoint |
| 3 | 462 | `validate` crashes on wrong scalar leaf types (`metadata.name: [a,b]` → bare `TypeError`) | A config-envelope type schema; entry argues it needs its own task | "its own task and its own reviewer" — never assigned |
| 4 | 1619 | `rank_family` tie-breaks lexicographically where `reference.md` says declaration order; `where` omitted entirely | Thread a declaration index onto `Member`, or change the document | "next slice touching `correction.py`" — **S5b touched it and did not** |
| 5 | 2430 | `supported: null` is a third verdict state; no document states either rule producing it | § Pre-registration gains three states + both routes; `run.yaml` example shows one | S5b review → checkpoint |
| 6 | 150 | § Package layout omits **six** built modules | Add `runner`, `coercion`, `contrasts`, `correction`, `estimate`, `strata` | S5 checkpoint (spine design says so) |
| 7 | 1016 | `SystemExit` at module scope escapes `validate`'s `except Exception` — no diagnostic, user-chosen exit code | Add `except SystemExit` beside line 219 of `validate.py`, report `E-ENTRYPOINT-IMPORT` | "whichever slice next touches validate's import path" — four have |
| 8 | 2054 | § The importable surface names 7 names `__init__.py` does not export | Export `Unit`; decide whether unbuilt names stay in the table | S5a → checkpoint |
| 9 | 2472 | `float()` on an `aggregate` return — **not reachable, but only incidentally** | Pin the containment with a test, or refuse at the boundary | S5 checkpoint |
| 10 | 337 | `run.yaml`'s `layout` and `provenance.input_manifest_changed` appear in no `reference.md` example | Two lines in § The two files | Unassigned since S1 |
| 11 | 2297 | A comparison's `observed` block carries `method`; the document's example shows three keys | One key in § Pre-registration's example + a docstring line | S5 checkpoint |
| 12 | 2 | `Config.raw` shadows a top-level key named `raw`; § The importable surface admits no exception | State that the root carries one accessor and nested nodes carry none | Unassigned since S1 |
| 13 | 1521 | The table `aggregate` receives still omits declared unit attributes and non-numeric columns | Thread the roster into `cli.py`'s `UnitTable`; needs a collapse rule for strings | **S4c — S4c/S4d/S5a/S5b all merged without it** |
| 14 | 29 | The generated config still calls itself "the complete parameter set"; `materialize.py` emits none of `statistics.contrasts`/`.resample`/`.null_test`/`.report_by` | Those four blocks land, or the phrase narrows | S4 → not done |
| 15 | 227 / 246 | A `run`- or `condition`-scoped step's return has nowhere to land and is silently discarded | A document decision: not recorded, or a new `results` block | Unassigned since S1 |
| 16 | 1928 | `by` is a spent metric name and `reference.md` documents no reserved names | A sentence in § Reporting strata or § Steps and artifacts | S4d → checkpoint |
| 17 | 1968 | § Validation's table lists two run-time warnings as validate-time checks | Split the rows, or say which are run-time | S4d → checkpoint |
| 18 | 2311 | § `Estimate` states four rules and should state six (`ci95` element type, numeric `value`) | Two lines in § `Estimate` + two identifiers in § Errors core raises | S5b → checkpoint |
| 19 | 1794 | `contrasts.resolve_contrasts` is still unguarded against an unhashable side; only `validate.py`'s copy refuses | Safe while every path validates first; a `dry-run`-style caller reopens it | "a later slice" |
| 20 | 1326 | Two `repeat_spread` figures declined: a nested `fold` omits the block entirely; a derived metric gets none — both shown in `reference.md` | Thread a per-slice `aggregate` recompute through `cli.py` | "a future slice" |
| 21 | 325 | `validate` findings are not ordered by config position, which § Exit codes and diagnostics promises | Track document position, or amend the sentence | Unassigned since S1 |
| 22 | 191 | Whether a missing `uv.lock` refuses or warns is unresolved | Belongs to the `reproduce` slice — not yet built | `reproduce` (hardening) |
| 23 | 89 / 99 | `code_hash` is not `.gitignore`-aware; `parameters_hash` does not normalize | Pass an `is_ignored` predicate; give `parameters_hash` the spec, or name the caller | "hardening" |
| 24 | 236 / 259 | A single repeat's dispersion, and `per_repeat`'s `""` key when nothing repeats | Answered for `basis: units` at line 525; the repeats case and the `""` key are not | S4 → not done |
| 25 | 558 | `reference.md` still admits `__` in a swept value while the label separator forbids it; only `sweep.py` refuses | One sentence in § How artifacts are organized | Unassigned since S2 |
| ~~26~~ | 683 | `E-SWEEP-BASELINE-PARTIAL` refuses per-cell baseline expansion, which the document specifies | Implement per-cell expansion, then retire the code | **CLOSED 2026-08-12** by H2 Sweep expansion modes, tasks 6 and 7 |
| 27 | 1874 / 2009 | Two residue tables (10 rows) from the S4c and S4d whole-branch reviews | Each row is safe today; row-by-row triage at the checkpoint | S4c/S4d; one row names **S4e, which the spine does not define** |
| 28 | 132 | `E-IO-FAILED` is undocumented; § Exit codes should say a local `OSError` exits `1` | Two additions to `reference.md` | Unassigned since S1 |
| 29 | 208 | `W-ENV-UNLOCKED` fires on every scaffolded run until `publishable` is published | Publish a release | Bootstrapping, not a defect |
| 30 | 12 | `default_repeats` reads as a materialized value where S1 implements a floor | Rename the column to "Repeat floor", or state the distinction | Unassigned since S1 |
| 31 | 2370 | Two narrow holes left open by choice: `_check_contrasts` calls `expand` unguarded; `compare: {condition: X}` with no `to` and no baseline fires neither check | Either widen the guard or record the choice in a document | S5b → checkpoint |
| 32 | 373 | Seven `E-DATA-*-UNSUPPORTED` refusals still live, all undocumented | Each retires with its own hardening slice | Hardening |

## Staleness findings

Each was verified against `HEAD`. Priority order: a false entry misleads the checkpoint.

### S1. `percentile_over_units is unguarded` (line 1557) — **FALSE at `HEAD`**

The floor landed. `src/publishable/stats.py:183-186`:

```python
    if len(values) < 2:
        return None
    if draws < min_honest_draws(confidence):
        return None
```

Closed by the entry at line 1779, whose account is accurate. The heading at 1557 was never amended.
Its second claim — "nothing in production calls it" — is **still true**: `statistics.resample` is
refused by `E-STATS-RESAMPLE-UNSUPPORTED`, which is still in `src/`.

### S2. `limits.max_ineligible_fraction moves from S4b to S4c` (line 1637) — **FALSE at `HEAD`**

It is read. `src/publishable/cli.py:869-881` reads
`(doc.get("limits") or {}).get("max_ineligible_fraction")` and warns `W-DATA-INELIGIBLE`. Closed by
line 1752, accurately. The entry's *other* two claims survive: `grep -rn min_clusters
min_units_per_cell src/` returns nothing, so both remain unread behind refused features.

### S3. `statistics.contrasts is absent from _check_shape's nested pass` (line 1664) — **FALSE at `HEAD`**

`src/publishable/validate.py` now carries, inside `_check_shape`'s nested pass, a `statistics`
branch refusing a non-list `contrasts` **and** a non-list `report_by` as `E-CONFIG-SHAPE`. Closed by
line 1794. That later entry carries its own live residue — `resolve_contrasts` itself is still
unguarded — which is item 19 above and is **invisible to a reader scanning headings**, because the
heading reads `RESOLVED`.

### S4. `W-STATS-FAMILY counts a baseline comparison per condition even with no baseline` (line 1646) — **FALSE at `HEAD`**

`src/publishable/validate.py:992` computes `comparisons = len(resolve_contrasts(doc, conditions))`,
not `len(conditions) - 1`, and line 995 fires only for `correction: none` over a non-empty family.
Closed by line 1678, which says so explicitly. The 1646 heading still reads as an open false
positive.

### S5. `io.read_upstream can only reach run-scoped steps — MARKED FOR THE NEXT SLICE` (line 715) — **FALSE at `HEAD`**

`src/publishable/artifacts.py:460-478` resolves per target scope: `run`/unknown → `run_dir/shared`,
`summary` → `run_dir/summary`, otherwise the caller's own condition directory via
`condition_dir_name`, then `_nest_repeat`. The hard-coded `shared/` path the entry describes is
gone. Fixed by S3b task 7, recorded at line 901 — which never amends this heading, and this heading
still carries the most urgent-looking marker in the file.

### S6. `runner.py is missing from § Package layout` (line 150) — **true, but now understates the divergence by 6×**

The entry closes with "No other module built in S1 diverges from the layout table". At `HEAD` the
tree in `docs/reference.md` § Package layout omits **six** shipped modules: `runner.py`,
`coercion.py`, `contrasts.py`, `correction.py`, `estimate.py`, `strata.py`. It also still lists
eleven modules that do not exist (`plugin_scaffold`, `docs`, `lineage`, `study`, `apparatus`,
`secrets`, `reproduce`, `report`), which is expected — those are unbuilt features — but the
checkpoint should not read this entry as "one line to add".

### S7. `The importable surface names five things __init__.py does not export` (line 2054) — **miscounted, and one claim is false**

`src/publishable/__init__.py`'s `__all__` holds nine names. The table in `docs/reference.md`
§ The importable surface names **seven** that are absent, not five: `Unit`, `Apparatus`,
`BaseReport`, `register_template`, `register_resolver`, `register_probe`, `register_writer`. The
reverse direction is clean — nothing is exported that the table does not name.

The entry's parenthetical "`register_template` is the only one of the four core actually ships
today" is **false**: `grep -rn "def register_" src/publishable/` returns nothing. The template
registry is `get_template`/`template_names` in `src/publishable/templates/registry.py`; there is no
`register_template` decorator at all. **Zero** of the four registries exist.

### S8. `A non-numeric aggregate return may reach float() uncontained` (line 2472) — **not reachable, but the containment is incidental and unpinned**

The entry asks two questions and this answers both. The closure *does* route through
`coerce_scalars` (`src/publishable/cli.py:930-940`), and `coerce_scalars` *does* accept `str`
(`coercion.py:36`, `_SCALARS = (bool, int, float, str)`), so the entry's suspicion that a `str` is
refused upstream is wrong. But every call site of the closure sits inside an `except Exception`
that exists for degenerate bootstrap draws: `stats.py:277-282` (`percentile_of_derived`),
`stats.py:325-332` (`paired_delta_of_derived` — the function the entry names), `stats.py:380-386`
(`paired_percentile_of_derived`), and `cli.py:1184-1197` for the strata path. A template returning
`{"m": "high"}` therefore yields `ci95: null`, `W-STATS-AGGREGATE-FAILED`, and a `str` in the
metric's `value` — not a traceback.

Two things the checkpoint should record rather than drop: the containment is justified in those
docstrings **only** as degenerate-draw handling, so a plausible future narrowing reopens the path
with no test failing; and **no test pins this case** (`tests/test_stats.py:1388-1407` pins a
compute that *raises*, not one that returns a `str`).

### S9. `E-RUN-SEED-MISSING` / `E-RUN-CFG-MISSING` "not in the registry" (lines 279, 598) — **now false**

Both, plus `E-RUN-ORDER-MISMATCH`, `E-REPL-ORDER-UNRESOLVED` and `E-RUN-FOLD-UNRESOLVED`, are in
`docs/reference.md` § Errors core raises' last row. Closed at lines 927 and 1094. The two earlier
headings still read as open registry gaps.

### S10. `E-STEP-COLUMN-UNKNOWN` "not yet done in this pass" (line 1206) — **now false**

Landed; the entry at line 1515 records it, and the identifier appears in `docs/reference.md`.

### S11. `S4e` (line 2016) names a slice the spine does not define

The S4d residue table defers a test to "**S4e**, when non-numeric recorded columns land".
`docs/superpowers/specs/2026-08-08-implementation-spine-design.md` § The slices runs S1–S5 and then
"hardening slices"; there is no S4e. The deferral has no owner.

### Owner slices that merged without the work

| Entry | Owner named | Status |
|---|---|---|
| 1619 `rank_family` tie-break | "the slice that next touches `correction.py`" | S5b commit `29ab24f` touched `correction.py`; `correction.py:129`'s key is still `(-_evidence_ratio(m), m.condition_index, m.metric)` |
| 1521 row 1, `aggregate`'s table omits unit attributes | **S4c** | `grep -n attributes src/publishable/stats.py` returns nothing; S4c, S4d, S5a and S5b all merged |
| 1016 `SystemExit` | "whichever slice next touches `validate`'s import path" | S4a–S5b all touched `validate.py`; `validate.py:219` is still a bare `except Exception` |
| 1637 / 1646 / 1664 | S4c | **Done** — these three are the file's good news, all closed in S4c task 9 |

### Owed document changes not yet made

Beyond the registry bulk (item 1), these entries state a specific document edit that has not
landed: 2 (§ The importable surface, root accessor), 12 (§ Naming conventions, "Repeat floor"),
132 (§ Exit codes, local `OSError`), 227/246 (§ Steps and artifacts, a wide step's return), 325
(§ Exit codes, finding order), 337 (§ The two files, `layout` + `input_manifest_changed`), 525
(§ Statistical reporting, no interval below two units), 558 (§ How artifacts are organized, `__`),
624 (`io.conditions` yields `(index, label)`), 648 (`E-SWEEP-EXPANDS-EMPTY`), 1928 (reserved metric
names), 1968 (§ Validation's validate-time/run-time blur), 2297 (`method` in the `observed`
example), 2311 (§ `Estimate`'s six rules), 2370 (required `hypotheses` fields + two § Validation
rows), 2430 (§ Pre-registration's three verdict states).

## Appendix — all 98 entries

Kind: **R** record of work done · **O** open · **A** answered/resolved · **H** historical duplicate ·
**R+** record carrying open residue. "Stale" marks a claim shown false above.

| Line | Entry | Kind | Note |
|---|---|---|---|
| 2 | `Config.raw` shadows a `raw` key | O | Verified still true (`config.py:68`, `reference.md`:718) |
| 12 | What `init` writes into `replication.repeats` | O | Doc change owed |
| 23 | S1 omits `data.units` | A | Retired at 553 |
| 29 | "the complete parameter set" before it is one | O | Verified: `materialize.py` emits none of the four `statistics` keys |
| 39 | Registry lacks step-name collisions | O | `E-STEP-NAME-COLLISION` still undocumented |
| 52 | Registry lacks repeat-seed collision | O | `E-REPL-SEED-COLLISION` still undocumented |
| 75 | Two accepted-as-is `BaseStep` behaviors | R | |
| 89 | `code_hash` not `.gitignore`-aware | O | Deferred to hardening |
| 99 | `parameters_hash` does not normalize | O | |
| 110 | Two `git_provenance` environment facts | R | |
| 122 | `code_hash` over zero files | R | Deferred question |
| 132 | Unwritable `output_dir`; `E-IO-FAILED` | R+ | `E-IO-FAILED` absent from `reference.md` (0 hits) |
| 150 | `runner.py` missing from § Package layout | O | **Stale**: six modules, not one |
| 166 | `E-ENTRYPOINT-IMPORT`, `W-ENV-UNLOCKED` | R+ | Both still undocumented |
| 191 | Missing `uv.lock`: refuse or warn | O | Owner: `reproduce`, unbuilt |
| 208 | Scaffold cannot resolve a lockfile | R | Retire on release |
| 227 | A `run`-scoped step's return | O | |
| 236 | A single repeat has no dispersion | O | Answered at 525 for `basis: units` only |
| 246 | `run`- and `condition`-scoped returns | O | Duplicate of 227 |
| 259 | `per_repeat`'s shape with no repeats | O | |
| 270 | Artifacts written before a raise | R | |
| 279 | `E-RUN-SEED-MISSING`, `E-STEP-RETURN-TYPE` | R | **Stale**: now in the registry |
| 292 | `E-STEP-EXISTS` and two siblings | R+ | Three still undocumented |
| 325 | Findings not ordered by config position | O | |
| 337 | `run.yaml` gains `layout`, `input_manifest_changed` | O | Verified: 0 hits in `reference.md` |
| 351 | `E-SWEEP-UNSUPPORTED` + three | R | Two retired; `-REPL-ORDER-` and `-DATA-NOT-ABSOLUTE` live |
| 373 | Seven `E-DATA-*-UNSUPPORTED` | R+ | All seven still live and undocumented |
| 462 | `validate` crashes on wrong scalar leaf types | O | **Verified still true** — reproduced a `TypeError` |
| 490 | `E-STEP-UNIT-UNKNOWN`, `-SETTLED` | R+ | Both undocumented |
| 498 | `units.parquet` type unification | R | |
| 525 | ANSWERED: one unit reports no interval | A | Doc line still owed |
| 534 | ANSWERED: non-numeric column refused | A | |
| 553 | RETIRED: S1 omits `data.units` | A | |
| 558 | Swept-value pattern vs `__` separator | R+ | Doc change owed |
| 590 | The four sweep-mode identifiers | R+ | All four live, undocumented |
| 598 | `E-RUN-CFG-MISSING` belongs in the registry | O | **Stale**: it is in the registry |
| 611 | `E-STEP-SCOPE-ONLY` + two | R+ | Three undocumented |
| 624 | RESOLVED: `read_condition` accepts what `io.conditions` yields | A | One prose line still owed |
| 642 | RETIRED in S3a: `E-SWEEP-UNSUPPORTED` | A | Verified gone from `src/` |
| 648 | A falsy `sweep` expands to zero conditions | A | Fixed; `E-SWEEP-EXPANDS-EMPTY` undocumented |
| 683 | `E-SWEEP-BASELINE-PARTIAL` | R+ | ~~Per-cell expansion unimplemented~~ CLOSED 2026-08-12 (H2 tasks 6, 7) |
| 715 | `read_upstream` reaches only `run` steps | O | **Stale**: fixed in S3b (`artifacts.py:460-478`) |
| 738 | RETIRED in S3b: `E-REPL-KIND-UNSUPPORTED` | A | Verified gone |
| 752 | PARTLY RESOLVED: `validate` imports the entrypoint | A | |
| 764 | …(as originally filed) | H | |
| 799 | NO DOCUMENT CHANGE: `E-ENTRYPOINT-IMPORT` widened | R | A decision, not a debt |
| 810 | …(as originally filed) | H | |
| 823 | PARTLY RESOLVED: `W-REPL-DETERMINISTIC` | R+ | **No warning registry** — item 2 above |
| 837 | …(as originally filed) | H | |
| 857 | RESOLVED: `E-REPL-ORDER-UNRESOLVED` | A | Verified in `reference.md` |
| 867 | …(as originally filed) | H | |
| 894 | RESOLVED: `E-STEP-READ-AMBIGUOUS` | A | Verified in `reference.md` |
| 901 | …(as originally filed) | H | Also closes 715 |
| 927 | RESOLVED: `E-RUN-ORDER-MISMATCH` | A | Verified; closes 279 and 598 |
| 939 | …(as originally filed) | H | |
| 966 | `E-REPL-LEVEL-BATCH-INNER` | R+ | `E-REPL-LEVEL-*` family undocumented |
| 1016 | `SystemExit` escapes `validate`'s catch | O | **Verified still true** (`validate.py:219`) |
| 1039 | RESOLVED: `summary` → `repeat` `read_upstream` | A | |
| 1072 | RESOLVED: `_handed_keys` fallback | A | |
| 1100 | RESOLVED: `fold` with no `data.units` | A | |
| 1134 | RESOLVED: a repeat level's count field | A | |
| 1182 | RESOLVED: two bare `assert`s | A | |
| 1206 | `E-STEP-COLUMN-UNKNOWN` | R | **Stale**: doc row landed (see 1515) |
| 1229 | RETIRED: derived `ci95` resampled | A | |
| 1255 | `W-STATS-AGGREGATE-FAILED` + four fixes | R | |
| 1326 | Two `repeat_spread` figures declined | O | Both still declined |
| 1364 | `resample_draws: null` vs `0` | R | |
| 1416 | Five `-UNSUPPORTED` codes + retirement status | R | Retirement status verified accurate |
| 1457 | S4a whole-branch review | R | |
| 1521 | Carried out of the S4a review (7 rows) | R+ | Row 1 **still open, S4c–S5b merged**; `np.str_` row open |
| 1536 | `E-STATS-CONTRAST-WITHIN` | R+ | Undocumented |
| 1557 | `percentile_over_units` unguarded | O | **Stale**: fixed (`stats.py:185`) |
| 1566 | Three S4b review identifiers | R+ | All three undocumented |
| 1596 | RESOLVED: `confounded: true` | A | |
| 1619 | `rank_family`'s tie-break | O | **Verified still true** (`correction.py:129`); owner merged |
| 1637 | `max_ineligible_fraction` S4b → S4c | O | **Stale**: read at `cli.py:869` |
| 1646 | `W-STATS-FAMILY` counts a phantom baseline | O | **Stale**: fixed at `validate.py:992` |
| 1664 | `contrasts` absent from `_check_shape` | O | **Stale**: present in the nested pass |
| 1678 | `W-STATS-FAMILY` changed condition; two identifiers | R | Closes 1646 |
| 1730 | `W-STATS-CORRECTED-THIN` | R | Residue closed — `test_a_family_too_wide_for_the_draws_reports_no_corrected_interval` (`tests/test_cli.py`) builds the thin case exactly: 2 × 15 = 30 members, `bonferroni` α/30, a 2400-draw floor a 2000-draw pool cannot meet |
| 1752 | RESOLVED: `max_ineligible_fraction` read | A | Closes 1637 |
| 1779 | RESOLVED: `percentile_over_units` floor | A | Closes 1557 |
| 1794 | RESOLVED: `contrasts` in `_check_shape` | R+ | Closes 1664; `resolve_contrasts` residue open |
| 1874 | Residue from the S4c review (6 rows) | R+ | Each row safe today |
| 1888 | `E-STATS-REPORTBY-UNKNOWN` | R+ | Undocumented |
| 1908 | Amendment: an empty stratum gets no block | R | |
| 1928 | New reserved metric name: `by` | R+ | Doc change owed |
| 1968 | `W-STATS-STRATUM-THIN` | R+ | § Validation table blur — doc change owed |
| 2009 | Residue from the S4d review (4 rows) | R+ | One row names **S4e**, an undefined slice |
| 2021 | `E-STEP-ESTIMATE-SCOPE`/`-METHOD`/`W-STEP-ESTIMATE-N` | R+ | § `Estimate` names no identifier |
| 2054 | The importable surface names five unexported things | O | **Stale**: seven, and `register_template` does not exist |
| 2087 | Carried S5a → S5b: `Estimate.ci95` shape | A | Resolved by S5b task 2 |
| 2120 | Nine `E-`/`W-HYPOTHESIS-*` identifiers | R+ | None documented |
| 2297 | `observed` carries `method` | O | Assigned to this checkpoint |
| 2311 | `E-STEP-ESTIMATE-VALUE` + a `ci95` type rule | R+ | § `Estimate` should state six rules |
| 2370 | `E-HYPOTHESIS-KIND`/`-THRESHOLD`/`-CONDITION` | R+ | Two narrow holes left open by choice |
| 2430 | `supported: null` is a third verdict state | O | Doc change owed |
| 2472 | Non-numeric `aggregate` may reach `float()` | O | **Not reachable** — contained incidentally, unpinned |
