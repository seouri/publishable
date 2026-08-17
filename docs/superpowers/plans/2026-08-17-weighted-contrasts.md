# H4b-1 — weights through contrasts, and retiring `E-DATA-WEIGHT-CONTRAST` — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a `data.units.weight_by` declared beside a comparison stops being refused. A weighted
contrast's delta, its interval, its effect size and its effective size are all weighted, its
interval is its own construction over the paired intersection, and the record says it was weighted.
`E-DATA-WEIGHT-CONTRAST` is retired. The payoff, in the form the spec's decision 6 fixes:
**the count of feasibility experiments with no remaining core-side blocker goes three → six** —
C1, C2, C3 join E1, E2, E5 — and **the executable count stays at three**, because C1–C3 also depend
on `io.reuse_from`, which is unbuilt and unowned.

**Architecture.** Three constructions and one closure, on two paths that must not be confused.

- **The payoff path** is a *recorded column* contrast under a declared `statistics.resample`. All
  three C configs declare `resample`, so `resample_columns` is `True`, so `_comparison_step_blocks`
  routes a column through `stats.paired_percentile_of_derived` with the local `_column_mean`
  closure. **The weighting happens inside that closure** — it looks each weight up by the `unit`
  key the construction preserves in every draw — and the construction itself gains no `weights`
  parameter. This is tasks 5–9.
- **The general path** is a column contrast with **no** `resample` declared. There
  `paired_t_over_units` is called, and it needs a weighted sibling,
  `stats.weighted_paired_t_over_units`. **`paired_t_over_units` is never called on C1–C3, raw or
  corrected**, so this path is *off* the payoff. This is tasks 9–10.
- **A derived metric is not weighted by core at all.** Its resample closures already re-attribute
  the roster (`cli._make_resample_fn` closes over `_attributed(units, attrs)`), so the weight column
  reaches `aggregate` as a unit attribute and the template decides. `paired_delta_of_derived` and
  `paired_percentile_of_derived` therefore take no `weights`, and a derived contrast keeps the
  unweighted `method` spelling while still recording `weighted_by` and its effective size — the
  declaration is true of the run either way. This is task 1's filing, pinned in task 7.

Beside the arithmetic, two absences close: `resample.stratify_by` is honoured on a contrast draw for
the first time (`paired_percentile_of_derived` was the only percentile construction in `stats.py`
with no `strata` parameter, and all three payoff configs declare one), and the corrected bound stops
diverging — `correction.Member` gains a `weights` field so `_corrected_bounds`' `diffs` branch
rebuilds a *weighted* t interval rather than an unweighted counterpart of a weighted raw one.

**Tech stack:** Python ≥ 3.11, `pytest`, `ruff`, `mypy`. No new dependency. No new module: the
changes land in `src/publishable/stats.py`, `src/publishable/cli.py`,
`src/publishable/correction.py`, `src/publishable/validate.py`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `docs/feasibility-llm-growth-studies.md`.

**Spec:** docs/superpowers/specs/2026-08-17-weighted-contrasts-design.md

**Measurement this plan argues from:** `docs/superpowers/H4b-SCOPING.md`, taken 2026-08-17 against
`main` at `b65ab91`. Every signature, attribute, error code, config key and file path below was read
from the source named beside it, at `d11f40a` (this branch's head). **Nothing is cited by line
number**; the prior H4 scoping's moved by ≈ 50 in one slice.

**Task count: 15**, the spec's § Task decomposition in its order and grain.

---

## Sequencing, and the three constraints the spec fixes

**5 → 7.** A stratified draw lives *inside* the weighted closure. Building the closure first bakes
the answer in by omission, which is exactly how `resample.stratify_by` came to be dropped on this
path.

**2 and 3 → 7–10.** An emitted `method` string and a record key must exist in a document before code
writes them. The four documents currently give a weighted contrast **no `method` string at all** —
no `weighted_paired_*` spelling exists anywhere in them.

**13 last among the code tasks.** A refusal is deleted only after everything it stood in for exists.

Full order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15.

### Two deviations from the spec's grain, each argued

**(a) `stats.weighted_paired_t_over_units` is built in task 9, not task 10.** The spec puts the
construction in task 10 and the corrected path in task 9 — but `_corrected_bounds`' `diffs` branch
*is* the first caller, so task 9 cannot be written without it. Task 9 therefore builds the
construction and wires the corrected bound; **task 10 wires the same construction into the raw
interval** in `_comparison_step_blocks`' non-`resample` branch and sets `Member.weights` there.
Nothing is dropped and nothing is added; one function moves one task earlier.

**(b) The § Validation row *Weighted deltas aren't computed* is struck in task 13, not task 11.**
The spec's task 11 pairs that strike with the two sibling re-words. A § Validation row and its
§ Errors row are **the same check seen from two ends**, and striking one while the emit still fires
would leave the document claiming a live refusal does not exist — for the two commits between 11 and
13. Task 11 therefore does the two sibling re-words and § Weighted samples' contrast sentence; task
13 strikes the § Validation row, the § Errors row and the emit **in one commit**.

### Where each task's tests can live, stated once because it decides seven task briefs

**`command_run` validates before it runs**, and returns `EXIT_WRONG` on any error
(`cli.command_run`: `if doc is None or c.has_errors: return EXIT_WRONG`). `E-DATA-WEIGHT-CONTRAST`
is an error. **So no weighted contrast reaches `_comparison_step_blocks` through `run` until task
13.**

Tasks 6, 7, 8, 10 and 12 therefore test by calling `cli._comparison_step_blocks`,
`cli._compute_vs_baseline` and `cli._compute_declared_contrasts` **directly**, which
`tests/test_cli.py` already does at
`test_a_comparison_reads_its_own_condition_not_condition_zero`,
`test_compute_declared_contrasts_within_is_narrowed_by_the_test_partition` and
`test_compute_vs_baseline_roster_argument_never_affects_the_auto_generated_family`. Tasks 5 and 9
test `stats`/`correction` directly, which their test modules already do throughout. **Task 13 is
where the same behaviour is asserted end to end through `command_run` and `validate_config`**, after
the refusal is gone.

This is not a weakening: each task's mutation is applied at the site the behaviour lives, which is
what this repo's discipline asks for. It *is* a deviation from the spec's task 12 wording ("the three
C configs exercised end to end"), and it is reported as one — task 12 exercises the three C *shapes*
through the three functions, and task 13 adds the `validate`-clean and `run`-through halves.

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced because an
implementer sees only its own task brief.

**Commands.** Tests `uv run pytest` — takes about two minutes; **run it in the foreground** and wait
for it. Lint `uv run ruff check .`. Format `uv run ruff format .`. Types `uv run mypy`. All four
must pass before a commit.

**Verify format with `uv run ruff format --check .`, never the bare form.** A previous brief in this
repo wrote the bare form where it meant `--check` and rewrote 67 files. **The repo is format-clean:
`ruff format --check .` reports 80 files, 0 to reformat. Keep it that way.**

**Baseline.** `uv run pytest -q` is **2118 passed, 1 skipped, 2 xfailed** (measured 2026-08-17 at
`d11f40a`). A task that leaves the count below its own additions has broken something. Every task
states its expected count.

**`E-DATA-WEIGHT-CONTRAST` stays alive until task 13.** Every test written before task 13 asserts
its own finding **alongside** that code, never instead of it, and **never on a total code set** — so
task 13 is a one-line deletion per test rather than a rewrite. The tests task 13 edits are named
there by test name.

**CLAUDE.md's contrast invariant, verbatim, because four tasks turn on it:** a contrast is computed
over the **intersection of both sides' completed units**, recorded as `n_paired`, and **its interval
is its own construction over that intersection** — never a difference of the two sides' intervals.
`data.units.weight_by` **weights an enriched sample's estimates and records `weighted_by`**.

**`validate` collects rather than aborting.** A refusal elsewhere never makes a later check
unreachable. Three readers across two slices got this wrong. Do not infer unreachability from a
refusal; build the config and look.

**Every new error site is pinned by its MESSAGE, not only its code.** Use the `fragment` +
`messages_by_code(path)[code]` pattern already in `tests/test_validate.py`; both helpers are defined
at the top of that file. **A message assertion is not automatically a discriminating one**: assert a
fragment only one branch can produce. **`messages_by_code` collapses duplicate-code findings
last-wins**, so a code emitted more than once per config needs a counted assertion, not
`messages_by_code`.

**Mutation discipline, every task.** Apply the named mutation to the file it names. Run the named
test. Confirm it **FAILS**. Then `find . -name __pycache__ -type d -exec rm -rf {} +`. Then revert
**by editing the file back in place** — **never `git checkout -- <file>`**, which destroys
uncommitted work and has been mistaken for a revert twice in this repo. Confirm the test **PASSES**
again, and verify the revert by *behaviour*, never by `git status`.

**A mutation is a claim too.** Before believing "this mutation must fail test X", read the *body* of
test X and check the two branches can actually produce different results. Thirteen prescribed
mutations across six slices were blind. Where this plan concludes a mutation cannot discriminate, it
says so and prescribes a different one; do the same for any mutation you add. **And a mutation's
silence is evidence about the TESTS, not the code.**

**Statistics is where this repo has found the most checks that could not fail — sixteen in two
slices. The shape to watch here: a weighted interval whose weights are uniform *is* the unweighted
one.** Every fixture in this plan is sized so a wrong weighting gives a different answer, and every
task states the two answers. Do not simplify a fixture's weights.

**Documentation rules.** `×` not `x` for multiplication, including inside fenced blocks. Hyphen,
never an en dash, in anything that becomes a filename or an anchor. **Cite by section**
(`reference.md` § "Contrasts: claims that aren't condition-vs-baseline"), **never by line number**.
**No positional locators** ("the row above", "further up"): name what a sibling row *does*. **No
counts in prose or comments** and **no call-site enumerations**: state what a set *is*. **A build
fact is dated and pinned to a commit where it is true.** **Prefer deleting a claim to rewriting
it.** After any `*.md` edit run the mechanical pass: every relative link and `#anchor` resolves, no
two headings in a file share an anchor, every table row matches its header's column count and none
is empty, no trailing whitespace, tab or invisible unicode — skipping fenced code blocks in all of
them. Any inline `# a | b | c` enum comment must list every value its table defines. **Never filter
the output of a sweep whose job is to find a string — filter the file list**, and name the four
documents explicitly, since the development record is tracked and `*.md` no longer means what it
used to.

**The four normative documents LEAD; `src/` follows.** `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`. Where they and the code disagree, **the
document changes first** and the gap is recorded in `docs/superpowers/spec-defects.md`. The
cross-document pass governs those four **only** — never the development record under
`docs/superpowers/`, where a correction is appended rather than retro-edited. `spec-defects.md` is
the one exception: a closed gap is struck there rather than left to mislead.
**§ Errors carries one row per code covering every emit site**, not one row per site.

**`tests/conftest.py` already has** an autouse `os.environ` restore, an opt-in `registries` fixture
and an opt-in `installed` distribution fixture. **Do not add duplicates, and do not add a second
autouse fixture of any kind.** No task in this slice needs `registries` or `installed`.

**Do not touch the worked example.** `cohort-pilot` declares no `weight_by`, so no weighted key
belongs in § The two files' `run.yaml`, in § Statistical reporting's fenced `results:` block, or in
any of the worked example's intervals — which `CLAUDE.md` § The worked example says were checked
numerically and **must not be narrowed back**. The weighted record shapes get their own fenced
examples in § Contrasts and § Weighted samples.

**§ The one config file's declaration count must not move.** It reads *"**One** declaration above is
not yet built"* — `statistics.null_test`, H4d's. Retiring a *combination* refusal is not retiring a
declaration, and `_check_sweep`'s own comment makes that placement argument for both of its codes.
Likewise **no row moves in any `Status`-carrying table**: `tests/test_cli.py` asserts set equality
between the document's `NOT BUILT` command rows and `cli.NOT_BUILT_COMMANDS`.

---

## The fixture every arithmetic task shares, and the numbers it produces

Written once here because seven tasks use it and a weakened copy is how this repo has produced
sixteen checks that could not fail.

**Six units, one recorded column `m`, one baseline side at zero, two strata, two weight levels.**

| unit | `of.m` | `against.m` | diff | weight | stratum |
|---|---|---|---|---|---|
| `u0` | 1.0 | 0.0 | 1.0 | 1 | `A` |
| `u1` | 2.0 | 0.0 | 2.0 | 1 | `A` |
| `u2` | 3.0 | 0.0 | 3.0 | 1 | `A` |
| `u3` | 9.0 | 0.0 | 9.0 | 3 | `B` |
| `u4` | 10.0 | 0.0 | 10.0 | 3 | `B` |
| `u5` | 11.0 | 0.0 | 11.0 | 3 | `B` |

Every number below is exact arithmetic, not an observation:

| Quantity | Unweighted | Weighted |
|---|---|---|
| `delta` (mean of diffs vs Σwd/Σw) | **6.0** = 36/6 | **8.0** = 96/12 |
| `cohens_d` (dz) | **1.3416407864998738** = 6/√20 | **2.0** = 8/4 |
| effective size over the intersection | 6 (`n_paired`) | **4.8** = 12²/30 (Kish) |
| forced floor of a **stratified** draw pool | **5.0** = (3·1 + 3·9)/6 | **7.0** = (3·1·1 + 3·3·9)/12 |
| centre of the paired *t* interval | 6.0 | 8.0 |

**Why the weighted variance is 16.0 and the *dz* exactly 2.0.** The weighted variance uses
`weighted_t_over_units`' own denominator, `Σw − Σw²/Σw` — which is what makes equal weights
reproduce the unweighted construction digit for digit. Here Σw = 12, Σw² = 30, so the denominator is
12 − 2.5 = 9.5, and Σw(d − 8)² = 49 + 36 + 25 + 3 + 12 + 27 = 152. 152/9.5 = 16.0, sd = 4.0,
dz = 8.0/4.0 = 2.0.

**Why the stratified floor is a *forced* bound and not an observation.** A stratified draw preserves
each stratum's own key count, so every draw is three `A` keys and three `B` keys. The smallest
possible mean is three copies of `u0` (1.0) and three of `u3` (9.0). Unweighted that is 5.0;
weighted, with `A` at 1 and `B` at 3, it is (3·1·1 + 3·3·9)/12 = 84/12 = 7.0. An **unstratified**
draw can go far below both — five copies of `u0` and one of `u3` gives 4.33 unweighted — so
`min(pool)` separates the two readings with a bound neither RNG nor draw count can move.

**Per-draw domination is provable, so the pools are comparable.** Within any drawn multiset the
weight is monotone in the value (1.0–3.0 carry weight 1, 9.0–11.0 carry weight 3), so the weighted
mean of that multiset is ≥ its unweighted mean, with equality only for a single-stratum draw.
Sorting preserves elementwise domination, so `all(w >= u for w, u in zip(weighted_pool,
unweighted_pool))` holds at a shared seed, and `sum(weighted_pool) > sum(unweighted_pool)` holds as
soon as one draw is heterogeneous.

**The Kish fixture is a second one, and it has to be.** Kish over the *intersection* versus over the
*whole weight mapping* cannot be separated by the table above, because the mapping and the
intersection coincide there. Task 8 uses eight units with a four-unit collapsed table:

| units | weights | Kish |
|---|---|---|
| `u0`–`u7` (the whole mapping) | 1, 1, 1, 3, 1, 1, 1, 3 | **6.0** = 12²/24 |
| `u4`–`u7` (the collapsed table alone) | 1, 1, 1, 3 | **3.0** = 6²/12 |

`n_paired` is 4, and 3.0 ≠ 4 ≠ 6.0 — three distinct answers, so the fixture separates "over the
intersection" from "over the mapping" from "just use the count". In production the seam arises under
a declared `holdout`: `cli` builds `weights` from the whole `roster` while `_comparison_step_blocks`
is called with `eval_roster` and a collapsed table over the test partition alone. **C1–C3 all
declare `holdout: null`, so no payoff config separates the readings** — which is why the fixture
instantiates the seam directly.

---

## Identifiers and record keys this slice touches

| Name | What it is | State at `d11f40a` | Task |
|---|---|---|---|
| `weighted_paired_t_over_units` | `method` string and `stats` function | **absent from all four documents and from `src/`** | 2 (documented), 9 (built) |
| `weighted_paired_percentile_over_units` | `method` string | **absent from all four documents and from `src/`** | 2 (documented), 7 (emitted) |
| `weighted_by` on a contrast entry | record key | per condition only (`cli`'s `weighted_beside`/`beside_n`) | 3 (documented), 8 (emitted) |
| `n_paired_effective` | record key — Kish over the paired intersection | **minted here** | 3 (documented), 8 (emitted) |
| `stats.weighted_cohens_dz` | function | documented rule, no code | 3 (documented), 8 (built) |
| `paired_percentile_of_derived(..., strata=)` | parameter | **the only percentile construction without one** | 5 |
| `correction.Member.weights` | field | absent | 4 (field), 9 (read) |
| `E-DATA-WEIGHT-CONTRAST` | refusal | 1 emit + 1 § Errors row + 1 § Validation row + 2 sibling rows citing it + 4 `validate.py` comments + 5 tests | 1 (message narrowed), 13 (retired) |

Confirm `weighted_paired_t_over_units` and `weighted_paired_percentile_over_units` are free before
task 2, by sweeping the **file list** rather than filtering output:

```
grep -rn "weighted_paired" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md src/ tests/
```

→ must be empty. **Can-fail control on the identical file list:**

```
grep -rno "weighted_t_over_units[a-z_]*" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md src/ | wc -l
```

→ non-zero, so the sweep can find a `weighted_` spelling when one is there.

---

## Task 1: settle and file the derived/column split, and narrow the published refusal's claim

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `tests/test_validate.py`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: `validate._check_sweep`'s `E-DATA-WEIGHT-CONTRAST` emit, guarded by
  `comparisons > 0 and isinstance(weight_by, str) and weight_by` — read in
  `src/publishable/validate.py`, `_check_sweep`; `cli._make_resample_fn`, whose returned closure is
  `tmpl.aggregate(_attributed(units, attrs), cfg)` — read in `src/publishable/cli.py`;
  `stats.paired_delta_of_derived` and `stats.paired_percentile_of_derived`, neither of which takes a
  `weights` parameter — read in `src/publishable/stats.py`.
- Produces: the refusal message and its § Errors row with the over-broad estimator claim **deleted**;
  one new `spec-defects.md` entry recording that the derived half is settled by the code.

**This task is a filing, not a note, and it is not on the payoff path.** `H4-SCOPING` asked that the
derived half be *settled and filed*. The code settles it: a derived metric's resample closures
re-attribute the roster inside every draw, so the weight column reaches `aggregate` as a unit
attribute and the template weights whatever its own metric needs weighting by. So
`paired_delta_of_derived` and `paired_percentile_of_derived` need **no** `weights` parameter — and
two of the three estimators the published refusal names are never touched by this slice. A refusal
that promises three constructions will take weights, when two of them will not, is a claim the
document has to stop making before the code makes it false.

**Prefer deleting the claim to rewriting it.** The § Errors row's final clause enumerates the three
functions; replacing that enumeration with a narrower one converts a wrong claim into a maintenance
obligation. Delete the enumeration and let the row say the refusal lifts once a weighted contrast
construction exists — which is self-maintaining, because the row itself is deleted in task 13.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_validate.py`, immediately after
      `test_a_weighted_declared_contrast_is_refused`:

```python
def test_the_weight_refusal_does_not_promise_the_derived_estimators_will_weight(
    write_config, tmp_path
):
    """The derived half is settled by the code, not by this slice: a derived
    metric's resample closures re-attribute the roster inside every draw
    (`cli._make_resample_fn`), so the weight column reaches `aggregate` as a unit
    attribute and the template weights its own metric. `paired_delta_of_derived`
    and `paired_percentile_of_derived` therefore take no weights, and a refusal
    promising they will is a claim the document must stop making before the code
    makes it false.

    The absence is asserted beside a presence that must report — the `Estimate`
    remedy — because a control asserting only absences passes identically if
    nothing ran."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n")
    path = write_config(
        {
            "data.units": _weighted_units(),
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman"]},
            },
        }
    )
    assert "E-DATA-WEIGHT-CONTRAST" in codes(path)
    message = messages_by_code(path)["E-DATA-WEIGHT-CONTRAST"]
    assert "`summary` step" in message
    assert "paired_delta_of_derived" not in message
    assert "paired_percentile_of_derived" not in message
```

- [ ] **Step 2: Run and see it fail.** `uv run pytest
      tests/test_validate.py::test_the_weight_refusal_does_not_promise_the_derived_estimators_will_weight`
      → fails on `"paired_delta_of_derived" not in message`? **No — check first.** Read the emit's
      message in `validate._check_sweep`: it ends *"The combination will be honored once the paired
      estimators take weights"*, which names no function. The **§ Errors row** is where the three
      are enumerated. So this test as written passes today, which makes it a **blind test**.
      **Replace it** with the discriminating pair below before proceeding — this is recorded rather
      than silently fixed, because "the message names the three functions" was the plan author's own
      assumption and reading the emit falsified it.

```python
def test_the_weight_refusal_does_not_promise_the_derived_estimators_will_weight(
    write_config, tmp_path
):
    """The derived half is settled by the code, not by this slice: a derived
    metric's resample closures re-attribute the roster inside every draw
    (`cli._make_resample_fn`), so the weight column reaches `aggregate` as a unit
    attribute and the template weights its own metric. `paired_delta_of_derived`
    and `paired_percentile_of_derived` therefore take no weights.

    The message's own over-broad half is *"the paired estimators"*, plural and
    total. Narrowed to name the construction that is actually missing, and pinned
    beside the `Estimate` remedy — a presence that must report, since a control
    asserting only absences passes identically if nothing ran."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n")
    path = write_config(
        {
            "data.units": _weighted_units(),
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman"]},
            },
        }
    )
    assert "E-DATA-WEIGHT-CONTRAST" in codes(path)
    message = messages_by_code(path)["E-DATA-WEIGHT-CONTRAST"]
    assert "`summary` step" in message
    assert "once a weighted contrast construction exists" in message
    assert "once the paired estimators take weights" not in message


def test_the_weight_refusals_errors_row_names_no_estimator():
    """The row and the message are one claim seen from two ends, and the row is
    where the three functions were actually enumerated. Parsed from the document
    rather than compared against a second literal: a test comparing each of two
    spellings to its own hard-coded string is how this repo shipped a name that
    claimed an agreement no assertion made."""
    row = next(
        line
        for line in REFERENCE_MD.read_text().split("\n")
        if line.rstrip().endswith("| `E-DATA-WEIGHT-CONTRAST` |")
    )
    assert "weight_by" in row  # the control: the right row was located
    assert "paired_delta_of_derived" not in row
    assert "paired_percentile_of_derived" not in row
```

      `REFERENCE_MD` is defined in `tests/test_cli.py`; the second test therefore lives in
      **`tests/test_cli.py`**, beside `_status_tables`, not in `tests/test_validate.py`. Import
      nothing new for it.

- [ ] **Step 3: Run and see them fail.** The first fails on `"once a weighted contrast construction
      exists" in message`; the second on `"paired_delta_of_derived" not in row`.

- [ ] **Step 4: Implement.** In `src/publishable/validate.py`, `_check_sweep`, replace the emit
      message's closing sentence:

```python
            "returned by a `summary` step, which core records as reported rather than "
            "recomputing. The combination will be honored once a weighted contrast "
            "construction exists",
```

      and delete the paragraph of the preceding comment block that enumerates the three estimators,
      replacing it with the settled fact:

```python
    # A weighted design that publishes a contrast. `reference.md` § Weighted
    # samples: core computes weighted means for `basis: units` metrics and a
    # weighted `t_over_units` interval whose df comes from Kish's effective size,
    # and "a contrast between two weighted conditions uses the same weights on
    # both sides". Nothing in this build weights a contrast at all — no weighted
    # paired construction exists, and the closure a column contrast's resample
    # runs through takes the plain collapsed row — so a weighted run's
    # `vs_baseline` delta and its interval would be unweighted numbers sitting
    # beside weighted per-condition values, each side answering a different
    # question with nothing in the record distinguishing them. That is the same
    # defect the per-condition wiring was widened to prevent one level up, one
    # level down.
    #
    # **A DERIVED metric is not core's to weight, and that is settled rather than
    # pending.** Its resample closures re-attribute the roster inside every draw
    # (`cli._make_resample_fn`), so the weight column reaches `aggregate` as a
    # unit attribute and the template weights its own metric; the paired derived
    # estimators take no weights and will not. What is missing is the weighted
    # form of a recorded COLUMN's contrast, raw and corrected.
```

      In `docs/reference.md`, in `E-DATA-WEIGHT-CONTRAST`'s § Errors row, delete the estimator
      enumeration from the final clause so it reads *"Temporary: the refusal lifts with the slice
      that builds a weighted contrast construction for a recorded column — a derived metric's weight
      reaches `aggregate` as a unit attribute, so core does not weight one"*.

      Append to `docs/superpowers/spec-defects.md`:

```markdown
## CLOSED by H4b-1 task 1 — the paired derived estimators were owed a weights decision, and the code had already made it

`docs/superpowers/H4-SCOPING.md` § 4.3 recorded "H4b's first task, not an observation": whether
`paired_delta_of_derived` and `paired_percentile_of_derived` take weights, or whether a weighted
derived contrast is record-only. `docs/superpowers/H4b-SCOPING.md` § 2.1 re-measured it at `b65ab91`
and found the code had settled it — a derived metric's resample closure is
`tmpl.aggregate(_attributed(units, attrs), cfg)`, so the weight column reaches `aggregate` as a unit
attribute on the contrast path exactly as it does per condition, and there is no per-unit vector for
core to weight.

**Settled: they take no weights, and `weighted_by` and the effective size still travel beside a
derived contrast** — the declaration is true of the run either way. `method` stays the unweighted
spelling, because core did not do the weighting.

What was actually owed was the *filing*, because the settlement narrows a published refusal message
and a normative § Errors row that both promised three constructions would take weights. Both were
narrowed by deletion in this task; both are deleted outright in H4b-1 task 13.

**Found by:** H4b-SCOPING § 2.1. **Closed by:** H4b-1, task 1.
```

- [ ] **Step 5: Run and see them pass.** `uv run pytest` → **2118 + 2 = 2120 passed**, 1 skipped,
      2 xfailed. Then `ruff check`, `ruff format --check`, `mypy`.

- [ ] **Step 6: Mutate.** In `src/publishable/validate.py`, restore the old closing clause — change
      `"once a weighted contrast construction exists"` back to `"once the paired estimators take
      weights"`. `tests/test_validate.py::test_the_weight_refusal_does_not_promise_the_derived_estimators_will_weight`
      must **FAIL** on both of its narrowing assertions. **Checked against the test body:** the test
      asserts one substring present and the other absent, and the mutation swaps exactly those two
      substrings, so the branches cannot agree.

      Second mutation, for the document half: in `docs/reference.md`, re-insert
      `` `paired_delta_of_derived` `` into `E-DATA-WEIGHT-CONTRAST`'s row.
      `tests/test_cli.py::test_the_weight_refusals_errors_row_names_no_estimator` must **FAIL**.
      **Checked against the test body:** the row is located by its final cell, which the mutation
      does not touch, so the control assertion still passes and the failure is the inserted name.

      **No mutation reaches** the `spec-defects.md` entry — a filing is prose in an untested file.
      Nothing in this repo tests that file, and adding a test for it would be a second source of
      truth for build state.

- [ ] **Step 7: Commit.** `validate: the weight refusal stops promising the derived estimators will weight`

---

## Task 2: mint the weighted-contrast `method` vocabulary in § Statistical reporting

**Files:** Modify `docs/reference.md`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: § Statistical reporting's two construction tables, both with the header
  `| The interval | Is |` — read in `docs/reference.md`; `REFERENCE_MD` and the table-parsing idiom
  in `tests/test_cli.py`'s `_status_tables`.
- Produces: two new rows in the contrast construction table; the derived-metric exception stated;
  `tests/test_cli.py::_interval_method_names()`, a helper tasks 7 and 10 use to pin code against the
  document rather than against a second literal.

**The document gives weights on a contrast nothing.** § Statistical reporting handles the three other
axes three ways — explicit rows for clustering per condition, explicit rows for weighting per
condition, a stated `_clustered` suffix rule for clustering on a contrast — and for weighting on a
contrast there is no row, no suffix rule and no sentence. The precedent for closing that is already
in the record: `spec-defects.md` carries two **RESOLVED (H3b task 13)** entries for the missing
clustered-percentile and weighted-clustered rows. Rows, not a suffix rule, for the same reason those
two got rows: a suffix rule that composed with the `_clustered` one would name four constructions
this build does not have.

**The helper parses both tables into one set, deliberately.** Keying the two `| The interval | Is |`
tables apart would need a positional or heading-relative locator, which this repo forbids. The
agreement tasks 7 and 10 need is *"an emitted contrast `method` is a string one of the construction
tables defines"*, which one set answers, and which cannot go stale when a row moves.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_cli.py`, beside `_status_tables`:

```python
def _interval_method_names() -> set[str]:
    """Every `method` string § Statistical reporting's construction tables define.

    Both `| The interval | Is |` tables, as one set: keying them apart would need a
    positional locator, and what the code-agreement pins below need is whether an
    emitted string is one the document defines at all. The name is the first
    backticked token of the first cell, the same shape `_status_tables` reads.
    """
    names: set[str] = set()
    lines = REFERENCE_MD.read_text().split("\n")
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[:2] != ["The interval", "Is"] or not lines[i + 1].startswith("|---"):
            continue
        for row in lines[i + 2 :]:
            if not row.startswith("|"):
                break
            match = re.match(r"`([^`]+)`", row.strip().strip("|").split("|")[0].strip())
            assert match, row
            names.add(match.group(1))
    return names


def test_the_interval_construction_tables_are_parsed_at_all():
    """The control for every agreement pin that reads this set: a parser finding
    nothing makes all of them pass vacuously, which is the shape of the bug they
    exist to catch. Both tables must be found — one per-condition name and one
    contrast name that predate this slice."""
    names = _interval_method_names()
    assert "t_over_units" in names
    assert "weighted_t_over_units" in names
    assert "paired_t_over_units" in names
    assert "paired_percentile_over_units" in names


def test_a_weighted_contrast_has_a_documented_method_string():
    """Decision 3: the four documents gave a weighted contrast no `method` string
    at all. Both weighted paired forms are defined before any code emits one — a
    record key code writes and no document names is the pair `CLAUDE.md` says to
    grep for."""
    names = _interval_method_names()
    assert "weighted_paired_t_over_units" in names
    assert "weighted_paired_percentile_over_units" in names
```

- [ ] **Step 2: Run and see it fail.** The control passes; `test_a_weighted_contrast_has_a_documented_method_string`
      fails on the first assertion.

- [ ] **Step 3: Implement.** In `docs/reference.md` § Statistical reporting, add two rows to the
      contrast construction table — the one whose `paired_t_over_units` row says *"A column metric,
      when no `resample` is declared"* — placed after `unpaired_percentile_over_units`:

```markdown
| `weighted_paired_t_over_units` | Student's *t* on the [weighted](#weighted-samples) per-unit differences over the [`n_paired`](#contrasts-claims-that-arent-condition-vs-baseline) intersection: the weighted mean of the differences, the weighted variance, and df from Kish's effective size over that intersection rather than `n_paired` − 1. A column metric under `weight_by`, when no `resample` is declared |
| `weighted_paired_percentile_over_units` | The same single joint draw as `paired_percentile_over_units`, with the [weighted](#weighted-samples) column mean recomputed on each draw, so the weights are in the estimate rather than in the drawing. A column metric under `weight_by` and a declared `resample` |
```

      Then, immediately after the paragraph that states the `_clustered` suffix rule, add:

```markdown
**A weighted contrast weights a recorded column and not a derived metric.** A column has a per-unit
value to weight, so `weight_by` moves its delta, its interval and its `cohens_d` onto the two
weighted forms above. A derived metric has none — [`aggregate`](#templates-where-parameters-are-defined)
returned one number for the whole table — so core hands it the weight column as a unit attribute and
the template weights whatever its own metric needs weighting by, exactly as it does per condition.
Its `method` therefore stays `paired_percentile_over_units`, because core did not do the weighting,
while `weighted_by` and the effective size travel beside it regardless: the declaration is true of
the run either way. The `_clustered` suffix does not compose with either weighted form in this build
— [`E-DATA-CLUSTER-CONTRAST`](#errors-validate-reports) refuses a clustered contrast outright.
```

      In the same section, in the sentence that says which method strings core emits, **delete the
      inline enumeration** so it reads: *"The method strings in the two construction tables above are
      what core **emits** into `run.yaml`, not values a config may name here."* A rewritten
      enumeration would be a second source of truth for what the tables hold; the sentence already
      derives its claim from them.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2120 + 3 = 2123 passed**, 1 skipped,
      2 xfailed. Then the other three commands. Then the mechanical `*.md` pass: both new rows have
      exactly two cells, every `#anchor` in them resolves, no trailing whitespace, no en dash.

- [ ] **Step 5: Mutate.** In `docs/reference.md`, change the new
      `` `weighted_paired_percentile_over_units` `` row's first cell to
      `` `weighted_paired_percentile_of_derived` ``.
      `tests/test_cli.py::test_a_weighted_contrast_has_a_documented_method_string` must **FAIL** on
      its second assertion. **Checked against the test body:** the helper reads the first backticked
      token of the first cell, which is exactly what the mutation changes, and the control test's
      four assertions are all on rows the mutation does not touch — so the control still passes and
      the failure is attributable to the renamed row rather than to a broken parser.

      Second mutation, for the parser itself: change `_interval_method_names`' guard from
      `cells[:2] != ["The interval", "Is"]` to `cells[:2] != ["The interval", "IS"]`, so it matches
      no table. `test_the_interval_construction_tables_are_parsed_at_all` must **FAIL**. This is what
      makes the control a control rather than a comment.

- [ ] **Step 6: Commit.** `docs: a weighted contrast gets a method vocabulary, and the derived exception`

---

## Task 3: design and document the contrast record shape under a weight

**Files:** Modify `docs/reference.md`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: § Contrasts' fenced `results: contrasts:` example, whose metric block is
  `{delta, basis, paired, method, n_paired, ci95, ci95_corrected, correction, correction_level,
  family_size, family}` — read in `docs/reference.md`; `cli._comparison_step_blocks`' literal metric
  block, `{delta, basis, paired, method, n_paired, ci95, cohens_d, correction}` — read in
  `src/publishable/cli.py`; § Weighted samples' `effective` and § Clustered units' `clusters`, both
  of which "join the three-part `n`".
- Produces: `weighted_by` and `n_paired_effective` documented on a contrast entry, with the argument
  for a scalar sibling rather than a mapping; `tests/test_cli.py::_section_text()`.

**`n_paired` is a scalar and the shape is forced.** § Weighted samples says Kish's size "joins the
three-part `n` as `effective`" and § Clustered units says the same of `clusters` — but a contrast
entry has **no `n` mapping at all**, and § Contrasts argues *why*: "the condition-level `n` can't
carry this, because it belongs to one condition and the contrast spans two". So
`H4-SCOPING`'s *"`effective`/`clusters` beside `n_paired`"* is an undocumented invention, and the
shape has to be designed here.

**Ruling: a scalar sibling key, `n_paired_effective`.** Promoting `n_paired` to a mapping is closed —
`tests/test_cli.py` asserts it as an integer at several call sites (`== 10`, `== 0`, `== 40`, `== 4`,
`== 30`, `== 20`, `== 5`), so the change would be a rewrite of pinned regressions with no
behavioural content, which is precisely the shape that has broken two pinned regressions in this
repo before. A sibling key also reads correctly: it is a fact *about* `n_paired`, computed over the
same intersection, and its name says so. `clusters` gets no sibling here — H4b-2 owns that, and it
should follow this shape.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_cli.py`:

```python
def _section_text(heading: str) -> str:
    """`reference.md` from `heading` to the next heading of the same depth or shallower.

    Named rather than positional: the caller passes what the section *is*, so an
    inserted sibling section cannot silently move the slice.
    """
    lines = REFERENCE_MD.read_text().split("\n")
    start = next(i for i, line in enumerate(lines) if line.strip() == heading)
    depth = len(heading) - len(heading.lstrip("#"))
    for j in range(start + 1, len(lines)):
        match = re.match(r"(#{1,6}) ", lines[j])
        if match and len(match.group(1)) <= depth:
            return "\n".join(lines[start:j])
    return "\n".join(lines[start:])


def test_the_weighted_contrast_record_keys_are_documented():
    """Task 3's ruling, in the document before any code writes it. `n_paired` is a
    scalar and § Contrasts argues why a contrast has no `n` mapping to join, so
    Kish's size over the intersection takes a scalar sibling rather than the shape
    § Weighted samples uses per condition.

    The control asserts the section was really located: a slicer that returned the
    empty string would fail every `in` and pass every `not in`."""
    section = _section_text("#### Contrasts: claims that aren't condition-vs-baseline")
    assert "n_paired" in section  # the control
    assert "weighted_by" in section
    assert "n_paired_effective" in section
```

- [ ] **Step 2: Run and see it fail.** Fails on `"weighted_by" in section`.

- [ ] **Step 3: Implement.** In `docs/reference.md` § Contrasts, after the `n_paired` paragraph, add:

````markdown
**Under [`weight_by`](#weighted-samples) a contrast entry carries two more keys**, and they are the
same two facts a weighted per-condition block carries, arranged for a record that has no `n` mapping
to join. `weighted_by` names the attribute, beside `method`, exactly as it sits beside a condition's
own value. Kish's effective size takes a **scalar sibling of `n_paired`**, `n_paired_effective`,
rather than joining an `n` block: this record deliberately has no `n`, on the same argument that
makes `n_paired` carry its own count, and the
effective size is a fact about the intersection `n_paired` counts. It is computed over **that
intersection's** weights and not over the roster's — under a [holdout](#a-fixed-holdout-split) or
unequal completion those are different multisets, and the size reported beside an interval has to be
the size the interval was computed at.

```yaml
results:
  contrasts:
    - id: sensitivity
      of: 02_arm=abnormal
      against: 01_arm=normal
      step03_screen:
        prob: {delta: 0.041, basis: units, paired: true,
               method: weighted_paired_percentile_over_units,
               weighted_by: sampling_weight,
               n_paired: 330, n_paired_effective: 214.7,
               ci95: [0.018, 0.063], cohens_d: 0.36,
               correction: holm, correction_level: 0.0125,
               family_size: 4, family: {comparisons: 2, metrics: 2}}
```

All four move together or none of them does: a weighted delta beside an unweighted interval, an
unweighted `cohens_d`, or an `n_paired` with no effective size beside it, is a declaration accepted
whose effect is half delivered — the same three-way obligation a weighted per-condition block
carries, with one more part because a contrast reports an effect size a condition does not.
````

      **Note for the implementer:** the block above is quoted with four backticks so its inner
      `yaml` fence survives; write the inner one into `reference.md` as an ordinary three-backtick
      block, and re-run the mechanical fence check after.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2123 + 1 = 2124 passed**, 1 skipped,
      2 xfailed. Then the other three. Then the mechanical `*.md` pass, and confirm nothing was added
      to § The two files' `run.yaml` or to § Statistical reporting's `results:` block — the worked
      example declares no `weight_by`.

- [ ] **Step 5: Mutate.** In `docs/reference.md`, rename `n_paired_effective` to `effective` in both
      places (prose and the fenced example).
      `tests/test_cli.py::test_the_weighted_contrast_record_keys_are_documented` must **FAIL** on its
      third assertion. **Checked against the test body:** `"n_paired_effective" in section` is a
      substring test and `effective` is a substring of neither `n_paired` nor `weighted_by`, so the
      two branches genuinely differ. Note that the *reverse* substring relation does hold —
      `n_paired` is a substring of `n_paired_effective` — which is why the control asserts
      `n_paired`, present under both readings, rather than being asked to discriminate.

      Second mutation, for the slicer: change `_section_text`'s `heading` comparison from
      `line.strip() == heading` to `line.strip() == heading + "!"`. The test must **FAIL** with
      `StopIteration`, which is what says the section is really being read rather than the whole
      file. If it instead passed, the assertions would be over the whole document and every one of
      them vacuous — that is the failure this second mutation exists to rule out.

- [ ] **Step 6: Commit.** `docs: a contrast entry's shape under a weight — weighted_by and n_paired_effective`

---

## Task 4: decide the corrected bound — `Member.weights`, argued against the exactly-one invariant

**Files:** Modify `src/publishable/correction.py`, `tests/test_correction.py`.

**Interfaces:**
- Consumes: `correction.Member`, fields `where, step, metric, delta, ci95, pool, diffs,
  declaration_index`, and `__post_init__`'s "exactly one of `pool`/`diffs` whenever there is a
  `ci95`" rule — read in `src/publishable/correction.py`; `correction._corrected_bounds`, which
  tests `diffs` first and falls through to `pool` — same file.
- Produces: `Member.weights: tuple[Any, ...] | None = None`, and a second, separate
  `__post_init__` rule. **`_corrected_bounds` is not touched here** — task 9 reads the field.

**The decision, and why it is a task.** `_corrected_bounds` calls
`paired_t_over_units(member.diffs, confidence=1.0 - level)` and `Member` has no weights field. So a
weighted raw interval would ship beside an **unweighted** corrected one on the same row, and **every
existing test would pass** — `Member`s are constructed at exactly one site, and no test compares a
raw to a corrected construction under a weight, because the combination is refused today. That is the
fault `__post_init__`'s own docstring names for the pool/diffs mix, one axis over.

**Ruling: add `weights` to `Member`, do not force the pool.** Forcing a weighted column contrast to
carry `pool` would make **weighting imply resampling**, which contradicts § Statistical reporting's
stated asymmetry — "a column metric has a t-interval available, so resampling it is a choice, and
`resample` is what makes it" — and would silently change the `method` string of a config that
declared no `resample`. A declaration must not switch a second, unrelated declaration on.

**The exactly-one invariant is not reopened, and that is the load-bearing half of the ruling.**
`weights` is not *evidence*; it is a modifier on one particular kind of evidence. So
`__post_init__` keeps its `(pool is None) == (diffs is None)` rule untouched and gains a second,
independent one: `weights` may be set **only** alongside `diffs`, and must be the same length. Set
beside `pool` it is a bookkeeping error — a percentile pool is already built from weighted draws, so
weights there would be applied twice — and that is exactly the class `__post_init__` exists to catch.

**Off the payoff path, and say so.** `cli`'s `corrected_from_pool = is_derived or resample_columns`
is `True` for all three C configs, so their corrected bound reads `interval_at(member.pool)` and the
pool is already weighted by task 7's closure. **`Member.weights` matters only for the non-`resample`
column path**, which needs a `resample_columns=False` fixture to be reachable at all.

**A field written and read by nothing exists between this task and task 9.** That is a two-commit
window inside one slice, not a shipped "declarable and unread" gap. It is stated here so nobody
closes it as one.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_correction.py`:

```python
def test_a_member_may_carry_weights_alongside_its_differences():
    """Decision 4. A weighted column contrast with no `resample` declared has a
    weighted raw *t* interval, and `_corrected_bounds` rebuilds the corrected one
    from the same evidence — so the weights have to travel with the differences
    they weighted. Anything else publishes a weighted raw beside an unweighted
    corrected, which is the fault `__post_init__`'s docstring names for the
    pool/diffs mix one axis over."""
    member = Member(
        where="cond:1",
        step="s",
        metric="m",
        delta=8.0,
        ci95=(4.0, 12.0),
        pool=None,
        diffs=(1.0, 2.0, 3.0, 9.0, 10.0, 11.0),
        weights=(1, 1, 1, 3, 3, 3),
        declaration_index=0,
    )
    assert member.weights == (1, 1, 1, 3, 3, 3)


def test_weights_beside_a_pool_is_refused():
    """A percentile pool is already built from weighted draws, so weights there
    would be applied twice. The exactly-one-of `pool`/`diffs` invariant is
    untouched: this is a second, separate rule about which evidence `weights` can
    modify, which is why it names `pool` in its own message."""
    with pytest.raises(ValueError) as excinfo:
        Member(
            where="cond:1",
            step="s",
            metric="m",
            delta=8.0,
            ci95=(4.0, 12.0),
            pool=(1.0, 2.0, 3.0),
            diffs=None,
            weights=(1, 1, 1),
            declaration_index=0,
        )
    assert "pool" in str(excinfo.value)


def test_weights_of_a_different_length_than_the_differences_is_refused():
    """A misaligned weight vector is the whole failure class this wiring guards
    against — it produces a plausible number rather than an error, which is what
    `stats._weighted_mean`'s `strict=True` zip refuses one level down. Caught at
    construction so the fault names the bookkeeping rather than surfacing as a
    `zip` error inside a corrected bound."""
    with pytest.raises(ValueError) as excinfo:
        Member(
            where="cond:1",
            step="s",
            metric="m",
            delta=8.0,
            ci95=(4.0, 12.0),
            pool=None,
            diffs=(1.0, 2.0, 3.0),
            weights=(1, 1),
            declaration_index=0,
        )
    assert "length" in str(excinfo.value)


def test_a_member_with_no_weights_is_unchanged():
    """The neighbouring shape, and the reason the field is defaulted: every
    existing construction site and every existing test builds a `Member` without
    it, and none of them moved."""
    member = Member(
        where="cond:1",
        step="s",
        metric="m",
        delta=1.0,
        ci95=(0.5, 1.5),
        pool=None,
        diffs=(1.0, 2.0),
        declaration_index=0,
    )
    assert member.weights is None
```

- [ ] **Step 2: Run and see them fail.** The first, second and third fail with `TypeError:
      Member.__init__() got an unexpected keyword argument 'weights'`; the fourth fails on
      `member.weights is None` with `AttributeError`.

- [ ] **Step 3: Implement.** In `src/publishable/correction.py`, add the field **after**
      `declaration_index` is *not* an option — it must be defaulted, and `declaration_index` is not,
      so `weights` goes last:

```python
    where: str
    step: str
    metric: str
    delta: float
    ci95: tuple[float, float] | None
    pool: tuple[float, ...] | None
    diffs: tuple[float, ...] | None
    declaration_index: int
    weights: tuple[Any, ...] | None = None
```

      Extend the class docstring with the field's argument, and extend `__post_init__`:

```python
    def __post_init__(self) -> None:
        """Exactly one of `pool`/`diffs` is set whenever there is a `ci95` to
        correct — never both, never neither. A member with no interval at all
        (`ci95=None`, excluded by `family_members` before either field is ever
        read) is exempt: it carries neither.

        ... (existing paragraphs unchanged) ...

        **`weights` is a modifier on `diffs`, not a third kind of evidence**, so
        it does not enter the exactly-one rule and is checked separately. A
        weighted column contrast's raw interval is `weighted_paired_t_over_units`
        over those differences, and the corrected bound has to be the same
        construction at a smaller α or it is a counterpart in name only. Beside
        `pool` it would be applied twice — a percentile pool is already built
        from weighted draws — and at a different length it is a misaligned vector,
        the failure class that produces a plausible number rather than an error.
        Both are `cli`'s bookkeeping to get right, so both raise `ValueError` for
        the reason the rule above does.
        """
        if self.weights is not None:
            if self.pool is not None:
                raise ValueError(
                    "Member weights modify diffs, not a pool; a percentile pool is "
                    "already drawn from weighted values"
                )
            if self.diffs is None or len(self.weights) != len(self.diffs):
                raise ValueError(
                    "Member weights must be the same length as diffs, not "
                    f"{len(self.weights)} against "
                    f"{'no diffs' if self.diffs is None else len(self.diffs)}"
                )
        if self.ci95 is None:
            return
        if (self.pool is None) == (self.diffs is None):
            raise ValueError(
                "Member requires exactly one of pool/diffs, not "
                f"{'both' if self.pool is not None else 'neither'}"
            )
```

      **The weights checks run before the `ci95 is None` early return, deliberately.** A misaligned
      weight vector on an interval-less member is still a bookkeeping error, and the existing rule's
      exemption is about *evidence being absent*, not about alignment being optional.

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2124 + 4 = 2128 passed**, 1 skipped,
      2 xfailed. Then the other three. `Any` is already imported in `correction.py`.

- [ ] **Step 5: Mutate.** In `src/publishable/correction.py`, move the whole `if self.weights is not
      None:` block to **after** the `if self.ci95 is None: return` line.
      `tests/test_correction.py::test_weights_of_a_different_length_than_the_differences_is_refused`
      must **still pass** — its member carries a `ci95`. **This mutation is blind, and it is recorded
      rather than prescribed.** The discriminating one is below.

      **The mutation to run:** delete the `if self.diffs is None or len(self.weights) !=
      len(self.diffs):` branch entirely.
      `test_weights_of_a_different_length_than_the_differences_is_refused` must **FAIL** — no
      `ValueError` is raised at all. **Checked against the test body:** it passes a 2-long weights
      against a 3-long diffs and asserts on the message, and with the branch gone nothing raises, so
      `pytest.raises` fails outright rather than on the message.

      **Second mutation, for the pool rule:** change `if self.pool is not None:` to `if False:`.
      `test_weights_beside_a_pool_is_refused` must **FAIL** — but read its body first: with the pool
      branch gone, the *length* branch is reached, `self.diffs is None` is true, and a `ValueError`
      **is** raised — whose message says "length", not "pool". The test asserts `"pool" in
      str(excinfo.value)`, so it fails on the message rather than on the absence. **That is why the
      two messages must not share a word**: had both said "weights are wrong", this mutation would
      have been silent.

      **A third, for the interval-less case:** add `weights=(1, 1)` to any existing `Member(...)`
      construction in `tests/test_correction.py` that passes `ci95=None` and `diffs=None` — if none
      exists, this is a seam no fixture instantiates and the brief says so rather than claiming
      coverage. Check `tests/test_correction.py` for a `ci95=None` member; if one exists, the
      early-return ordering above becomes pinnable and a test for it should be added here.

      **No mutation reaches** `_corrected_bounds`' use of the field — nothing reads it until task 9,
      which is where that mutation is prescribed.

- [ ] **Step 6: Commit.** `correction: a Member may carry the weights its differences were weighted by`

---

## Task 5: `resample.stratify_by` on a contrast — decided, built, and the residue filed

**Files:** Modify `src/publishable/stats.py`, `docs/superpowers/spec-defects.md`,
`tests/test_stats.py`.

**Interfaces:**
- Consumes: `stats.paired_percentile_of_derived(of, against, keys, compute_of, compute_against, seed,
  draws=2000, confidence=0.95) -> PairedResample` — read in `src/publishable/stats.py`;
  `stats.percentile_of_derived`'s own `strata: dict[str, str] | None = None` branch, which builds one
  pool per stratum by walking the already-sorted keys, orders the pools by their own sorted contents,
  and indexes `strata` by key rather than `.get`-ing it — same file; `stats.paired_keys`, which
  returns the intersection **sorted** — same file.
- Produces: `paired_percentile_of_derived(..., strata: dict[str, str] | None = None)`, honoured in
  the draw; one `spec-defects.md` entry filing the newly-reachable degenerate case with a named owner.

**This task must precede task 7.** A stratified draw lives *inside* the weighted closure's caller, so
building the closure before deciding whether a contrast's draw stratifies bakes the answer in by
omission — which is exactly how `resample.stratify_by` came to be silently dropped on this path.

**Ruling: honour it.** `percentile_over_units`, `percentile_over_units_clustered` and
`percentile_of_derived` all take `strata`; `paired_percentile_of_derived` is the only percentile
construction in `stats.py` that does not, and no contrast call site passes one. So a declared
stratification is honoured per condition and **silently dropped on every contrast** — and all three
payoff configs declare `stratify_by: [consensus_label, count_stratum]`. Filing it instead would ship
"C1–C3 have no remaining core-side blocker" while their contrast intervals quietly ignored a
declaration they made.

**The pairing survives, and that is the property to keep.** One drawn key list feeds **both** sides'
tables, exactly as the unstratified branch does — stratifying changes *which* keys are drawn, never
that both sides see the same ones. Drawing each side's strata independently would resample the two
conditions apart and destroy the pairing, which is the failure this construction's docstring already
argues about the unstratified draw.

**What is deliberately not built here.** `percentile_of_derived` carries a **content-based degenerate
refusal**: if every key in every stratum carries the identical recorded row, every draw is the same
multiset and the interval has zero width, so it refuses before drawing. `paired_percentile_of_derived`
carries none of its siblings' degenerate refusals — `spec-defects.md` already records that as a
deferred finding — and adding `strata` here makes a near-unique `stratify_by` newly able to produce a
zero-width *contrast* interval. That is filed with a named owner rather than built: it is a third
construction's worth of work and the 15-task budget does not hold it.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_stats.py`:

```python
_PAIRED_OF = {
    "u0": {"m": 1.0},
    "u1": {"m": 2.0},
    "u2": {"m": 3.0},
    "u3": {"m": 9.0},
    "u4": {"m": 10.0},
    "u5": {"m": 11.0},
}
_PAIRED_AGAINST = {k: {"m": 0.0} for k in _PAIRED_OF}
_PAIRED_KEYS = ["u0", "u1", "u2", "u3", "u4", "u5"]
_PAIRED_STRATA = {"u0": "A", "u1": "A", "u2": "A", "u3": "B", "u4": "B", "u5": "B"}


def _mean_of_m(table):
    column = getattr(table, "m")
    return float(sum(column) / len(column))


def test_a_stratified_paired_draw_preserves_each_stratums_key_count():
    """`reference.md` § Weighted samples: `resample.stratify_by` says what an
    independent draw is, "resampling within each stratum so a bootstrap can't
    return a replicate whose stratum composition the design ruled out".

    The assertion is a FORCED BOUND, not an observation. A stratified draw is
    always three `A` keys and three `B` keys, so the smallest mean it can produce
    is three copies of `u0` (1.0) and three of `u3` (9.0) — exactly 5.0. An
    unstratified draw can go to 4.33 with five `A` keys and one `B`, and does at
    this seed and draw count. Neither the RNG nor the draw count can move the
    bound, which is what makes this test discriminating rather than lucky."""
    from publishable.stats import paired_percentile_of_derived

    stratified = paired_percentile_of_derived(
        _PAIRED_OF,
        _PAIRED_AGAINST,
        _PAIRED_KEYS,
        _mean_of_m,
        _mean_of_m,
        seed=7,
        draws=200,
        strata=_PAIRED_STRATA,
    )
    plain = paired_percentile_of_derived(
        _PAIRED_OF,
        _PAIRED_AGAINST,
        _PAIRED_KEYS,
        _mean_of_m,
        _mean_of_m,
        seed=7,
        draws=200,
    )
    assert min(stratified.pool) >= 5.0 - 1e-9
    # The control that must report: the same seed and draw count without strata
    # reaches below the forced floor, so the bound above is the stratification and
    # not a pool that happens to start high.
    assert min(plain.pool) < 5.0
    assert stratified.draws_used == 200
    assert plain.draws_used == 200


def test_a_stratified_paired_draw_still_draws_once_for_both_sides():
    """The property stratification must not cost. One drawn key list feeds both
    tables, so what is resampled is the difference — drawing each side's strata
    independently would resample the two conditions apart, the failure this
    construction's docstring argues about the unstratified draw.

    Pinned by an oracle rather than by inspection: with `against` holding the same
    column as `of`, a single shared draw cancels to exactly zero on every draw, so
    a zero-width pool at zero is proof the two tables saw the same keys. Two
    independent draws could not produce it."""
    from publishable.stats import paired_percentile_of_derived

    got = paired_percentile_of_derived(
        _PAIRED_OF,
        _PAIRED_OF,
        _PAIRED_KEYS,
        _mean_of_m,
        _mean_of_m,
        seed=7,
        draws=200,
        strata=_PAIRED_STRATA,
    )
    assert set(got.pool) == {0.0}


def test_a_stratum_mapping_missing_a_drawn_key_is_a_core_defect():
    """Indexed, not `.get`-ed — the discipline `percentile_of_derived`'s own
    `strata` branch states: a caller whose roster and mapping have come to
    disagree about which units exist is a core defect, not a silent extra
    stratum."""
    from publishable.stats import paired_percentile_of_derived

    with pytest.raises(KeyError):
        paired_percentile_of_derived(
            _PAIRED_OF,
            _PAIRED_AGAINST,
            _PAIRED_KEYS,
            _mean_of_m,
            _mean_of_m,
            seed=7,
            draws=10,
            strata={"u0": "A"},
        )


def test_a_relabelled_stratum_draws_the_identical_sequence():
    """The invariance `percentile_over_units` and `percentile_of_derived` both
    keep, and for the identical reason: pools are ordered by their own sorted
    contents rather than by label, so renaming a stratum cannot change the
    interval. Two labels is enough here because the two orderings this must rule
    out are exactly two — insertion order and label order — and swapping the two
    labels reverses one and not the other."""
    from publishable.stats import paired_percentile_of_derived

    swapped = {k: ("B" if v == "A" else "A") for k, v in _PAIRED_STRATA.items()}
    first = paired_percentile_of_derived(
        _PAIRED_OF, _PAIRED_AGAINST, _PAIRED_KEYS, _mean_of_m, _mean_of_m,
        seed=7, draws=200, strata=_PAIRED_STRATA,
    )
    second = paired_percentile_of_derived(
        _PAIRED_OF, _PAIRED_AGAINST, _PAIRED_KEYS, _mean_of_m, _mean_of_m,
        seed=7, draws=200, strata=swapped,
    )
    assert first.pool == second.pool
```

- [ ] **Step 2: Run and see them fail.** All four fail with `TypeError:
      paired_percentile_of_derived() got an unexpected keyword argument 'strata'`.

- [ ] **Step 3: Implement.** In `src/publishable/stats.py`, add the parameter and the branch:

```python
def paired_percentile_of_derived(
    of: dict[str, dict[str, float]],
    against: dict[str, dict[str, float]],
    keys: list[str],
    compute_of: "Callable[[UnitTable], float | None]",
    compute_against: "Callable[[UnitTable], float | None]",
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
    strata: dict[str, str] | None = None,
) -> PairedResample:
```

      and, inside, replace the draw with the two-branch form:

```python
    if len(keys) < 2:
        return PairedResample(interval=None, draws_used=0, pool=[])
    rng = random.Random(seed)
    n = len(keys)
    # One pool per stratum, built by walking `keys` — which `paired_keys` returns
    # sorted — so each pool's own contents come out sorted, and the pools are then
    # ordered by those contents rather than by label. That is the same
    # relabelling-invariance `percentile_over_units` and `percentile_of_derived`
    # keep for the same reason: a renamed stratum must draw the identical sequence
    # of tables. `strata` is indexed, not `.get`-ed, the discipline `weights` and
    # `clusters` follow elsewhere here — a caller whose roster and mapping have
    # come to disagree about which units exist is a core defect, not a silent
    # extra stratum. It need not be exactly `keys`' set: a caller passing a
    # roster-wide mapping simply never has the extra entries looked up.
    pools: list[list[str]] | None = None
    if strata is not None:
        grouped: dict[str, list[str]] = {}
        for key in keys:
            grouped.setdefault(strata[key], []).append(key)
        pools = sorted(sorted(group) for group in grouped.values())
    values: list[float] = []
    for _ in range(draws):
        # ONE drawn key list, feeding BOTH sides — under strata exactly as
        # without. Stratifying changes which keys are drawn and never that the two
        # sides see the same ones; drawing each side's strata independently would
        # resample the two conditions apart and destroy the pairing, which is the
        # failure this function's docstring argues about the unstratified draw.
        if pools is None:
            drawn = [keys[rng.randrange(n)] for _ in range(n)]
        else:
            drawn = [
                group[rng.randrange(len(group))] for group in pools for _ in range(len(group))
            ]
        table_a = unit_table_from_rows([{"unit": k, **of[k]} for k in drawn])
        table_b = unit_table_from_rows([{"unit": k, **against[k]} for k in drawn])
```

      The rest of the loop and the tail are unchanged. Extend the docstring with a paragraph naming
      the stratified branch, the pairing property it preserves, and — explicitly — that the
      content-based degenerate refusal its three siblings carry is **not** here and is filed.

      Append to `docs/superpowers/spec-defects.md`:

```markdown
## OPEN — a stratified paired draw can publish a zero-width contrast interval — **Owner: H4b-2**

H4b-1 task 5 gave `stats.paired_percentile_of_derived` a `strata` parameter, so
`statistics.resample.stratify_by` is honoured on a contrast for the first time. Its three sibling
percentile constructions each carry a **content-based degenerate refusal** —
`percentile_over_units`'s strata branch, `percentile_over_units_clustered`'s cluster-content branch,
and `percentile_of_derived`'s identical-row branch, which refuses before drawing when every key in
every stratum carries the same recorded row. `paired_percentile_of_derived` carries none of them,
which `docs/superpowers/spec-defects.md`'s entry on the contrast path's disclosure gaps already
records as deferred.

**What task 5 changed is the reachability.** A near-unique `stratify_by` now makes every stratified
contrast draw pick from an identical multiset of rows, so `compute_of`/`compute_against` return the
same difference every time and the entry publishes `ci95: [x, x]` — a zero-width 95 % interval, which
§ Statistical reporting refuses in those terms — indistinguishable from a genuine interval. Before
task 5 the same config's contrast draw was unstratified and could not reach it.

Not built in H4b-1: it is a third construction's worth of work (the paired form has two collapsed
tables to compare rows across, not one) and the slice's task budget does not hold it.

**Owner: H4b-2 — clusters through contrasts**, by name and not "whichever slice ships next": H4b-2 is
the half that adds the remaining paired percentile construction, so it is where the degenerate sweep
belongs for all of them at once. It should be built together with the zero-width sweep the contrast
disclosure entry already defers to H4b.

**Found by:** H4b-1, task 5. **Severity:** Minor — reachable only from a `stratify_by` whose strata
are near-unique, which `validate` does not refuse.
```

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2128 + 4 = 2132 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/stats.py`, change `pools = sorted(sorted(group) for
      group in grouped.values())` to `pools = None`, so a declared stratification is accepted and
      dropped — the exact defect this task closes.
      `tests/test_stats.py::test_a_stratified_paired_draw_preserves_each_stratums_key_count` must
      **FAIL** on `min(stratified.pool) >= 5.0 - 1e-9`. **Checked against the test body:** with
      `pools = None` the stratified call becomes byte-identical to the `plain` call at the same seed,
      and the test's own control asserts `min(plain.pool) < 5.0` — so the two assertions become
      contradictory and the first is the one that fails. A test asserting only that the two calls
      *differ* would have caught this too, but a test asserting only the floor without the control
      would not have caught a pool that started high for an unrelated reason.

      **Second mutation, for the pairing:** in the stratified branch, build `table_b` from a second,
      independent draw — `[{"unit": k, **against[k]} for k in [keys[rng.randrange(n)] for _ in
      range(n)]]`. `test_a_stratified_paired_draw_still_draws_once_for_both_sides` must **FAIL**:
      its oracle passes the same collapsed table as both sides, so a shared draw cancels to exactly
      `{0.0}` and two independent draws cannot. **Checked against the test body:** the assertion is
      set equality against `{0.0}`, which no independent-draw pool over these six values can produce.

      **Third mutation, for the ordering invariance:** change `pools = sorted(sorted(group) ...)` to
      `pools = [sorted(group) for group in grouped.values()]` — insertion order rather than content
      order. `test_a_relabelled_stratum_draws_the_identical_sequence` must **FAIL**. **Checked
      against the test body:** with two labels, swapping them reverses insertion order, and the two
      pools have different contents (`A` holds 1–3, `B` holds 9–11), so the drawn sequences differ
      and the pools cannot compare equal. **Two labels is exactly enough here because the candidate
      orderings are exactly two**; a fixture whose two strata held the same values could not have
      distinguished them.

      **No mutation reaches** the `spec-defects.md` filing.

- [ ] **Step 6: Commit.** `stats: a paired percentile draw honours resample.stratify_by`

---

## Task 6: thread `weights` and `strata` into the three comparison functions

**Files:** Modify `src/publishable/cli.py`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: `cli._comparison_step_blocks(comp, *, roster, aggregated, collapsed_by_key,
  derived_by_key, resample_fns_by_key, seed, draws, min_reported_n, findings, where, where_id,
  conditions_by_index, resample_columns)`; `cli._compute_vs_baseline(*, doc, conditions, roster,
  aggregated, collapsed_by_key, derived_by_key, resample_fns_by_key, seed, draws, findings,
  resample_columns)`; `cli._compute_declared_contrasts(...)` with the same keywords —
  all read in `src/publishable/cli.py`. `cli.command_run`'s `weights: dict[str, Any] | None` built
  from `roster` where `weight_by` is a non-empty string, and its `resample_strata: dict[str, str] |
  None` built where `resample_spec["declared"] and resample_spec["stratify_by"]` — same file.
- Produces: `weights: dict[str, Any] | None = None` and `strata: dict[str, str] | None = None` on all
  three, passed down from `command_run`'s two call sites, with `strata` reaching
  `paired_percentile_of_derived` in **both** branches.

**Defaulted keywords, not required parameters.** `tests/test_cli.py` calls all three directly at
several sites, and a required parameter would be an edit with no behavioural content at every one of
them — the shape that has broken pinned regressions in this repo before. Defaulting to `None` also
makes "no weight declared" and "this call site has not been taught about weights" the same thing,
which is what they are.

**At this commit `strata` is observable and `weights` is not.** The stratified draw changes the pool,
which a test can see. `weights` is accepted and reaches nothing until task 7's closure reads it. That
is stated rather than glossed: **the mutation for `weights`' threading is task 7's**, and this task
prescribes only the `strata` one.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_cli.py`:

```python
_W_OF = {
    "u0": {"m": 1.0}, "u1": {"m": 2.0}, "u2": {"m": 3.0},
    "u3": {"m": 9.0}, "u4": {"m": 10.0}, "u5": {"m": 11.0},
}
_W_AGAINST = {k: {"m": 0.0} for k in _W_OF}
_W_WEIGHTS = {"u0": 1, "u1": 1, "u2": 1, "u3": 3, "u4": 3, "u5": 3}
_W_STRATA = {"u0": "A", "u1": "A", "u2": "A", "u3": "B", "u4": "B", "u5": "B"}


def _weighted_contrast_block(**extra):
    """One column contrast over the six-unit weighted fixture, called directly.

    Direct because `command_run` validates first and `E-DATA-WEIGHT-CONTRAST` is
    an error until task 13, so no weighted contrast reaches this function through
    `run` yet. Returns `(metric_block, members)`.
    """
    from publishable.cli import _comparison_step_blocks
    from publishable.contrasts import Comparison
    from publishable.sweep import Condition

    block, members = _comparison_step_blocks(
        Comparison(id="c", of=1, against=0),
        roster=_cli_roster(6),
        aggregated={1: {"s": {"m": 6.0}}, 0: {"s": {"m": 0.0}}},
        collapsed_by_key={(1, "s"): _W_OF, (0, "s"): _W_AGAINST},
        derived_by_key={},
        resample_fns_by_key={},
        seed=7,
        draws=200,
        min_reported_n=None,
        findings=Collector(),
        where="condition 1",
        where_id="cond:1",
        conditions_by_index={
            0: Condition(index=0, label="baseline", is_baseline=True),
            1: Condition(index=1, label="arm", values={"analysis.method": "spearman"}),
        },
        **extra,
    )
    return block["s"]["m"], members


def test_a_contrasts_column_draw_honours_resample_stratify_by():
    """Task 5's `strata` reaching the contrast call site. The forced bound is the
    assertion: a stratified draw is three `A` keys and three `B` keys, so its
    smallest possible mean is (3·1 + 3·9)/6 = 5.0, while an unstratified draw over
    the same six units reaches 4.33. Nothing about RNG or draw count can move
    that bound."""
    stratified, _ = _weighted_contrast_block(resample_columns=True, strata=_W_STRATA)
    plain, _ = _weighted_contrast_block(resample_columns=True)
    assert stratified["ci95"][0] >= 5.0 - 1e-9
    # The control that must report: without strata the same seed and draw count
    # produce a lower bound below the forced floor.
    assert plain["ci95"][0] < 5.0


def test_the_three_comparison_functions_accept_weights_and_strata():
    """The threading itself, at all three signatures — `_comparison_step_blocks`
    above plus the two callers. `weights` reaches no arithmetic at this commit
    (task 7's closure is what reads it), so this pins acceptance and the
    unchanged-answer property: a weight passed today must not silently move a
    number, because nothing has been built to move it correctly yet."""
    from publishable.cli import _compute_declared_contrasts, _compute_vs_baseline
    from publishable.sweep import Condition

    conditions = [
        Condition(index=0, label="baseline", is_baseline=True),
        Condition(index=1, label="arm"),
    ]
    common = dict(
        conditions=conditions,
        roster=_cli_roster(6),
        aggregated={1: {"s": {"m": 6.0}}, 0: {"s": {"m": 0.0}}},
        collapsed_by_key={(1, "s"): _W_OF, (0, "s"): _W_AGAINST},
        derived_by_key={},
        resample_fns_by_key={},
        seed=7,
        draws=200,
        findings=Collector(),
        resample_columns=False,
    )
    plain, _ = _compute_vs_baseline(doc={}, **common)
    threaded, _ = _compute_vs_baseline(doc={}, weights=_W_WEIGHTS, strata=_W_STRATA, **common)
    assert plain is not None and threaded is not None
    assert plain[1]["s"]["m"]["delta"] == pytest.approx(6.0)
    assert threaded[1]["s"]["m"]["delta"] == pytest.approx(6.0)

    doc = {"statistics": {"contrasts": [{"id": "c1", "of": "arm", "against": "baseline"}]}}
    out, _ = _compute_declared_contrasts(
        doc=doc, weights=_W_WEIGHTS, strata=_W_STRATA, **common
    )
    assert out is not None
    assert out[0]["s"]["m"]["n_paired"] == 6
```

- [ ] **Step 2: Run and see them fail.** Both fail with `TypeError: ... got an unexpected keyword
      argument 'strata'`.

- [ ] **Step 3: Implement.** In `src/publishable/cli.py`, add two keywords to each of the three
      signatures, after `resample_columns`:

```python
    resample_columns: bool,
    weights: dict[str, Any] | None = None,
    strata: dict[str, str] | None = None,
```

      In `_comparison_step_blocks`, pass `strata=strata` to **both**
      `paired_percentile_of_derived` calls — the derived branch's and the `_column_mean` branch's.
      `weights` is not read yet. Add to the docstring:

```python
    `weights` is `command_run`'s roster-wide `{unit key: weight}` mapping, or
    `None` when `data.units.weight_by` is undeclared, and `strata` its resolved
    `statistics.resample.stratify_by` mapping. Both are defaulted rather than
    required: the direct call sites in the test suite would otherwise take an edit
    with no behavioural content, and "no weight declared" and "this caller has not
    been taught about weights" are the same fact. `strata` reaches both percentile
    branches, because a declaration honoured for a derived metric and dropped for
    a recorded column would be the asymmetry § Weighted samples' pairing of
    `weight_by` with `resample.stratify_by` exists to rule out.
```

      In `command_run`, at both `_compute_vs_baseline(...)` and
      `_compute_declared_contrasts(...)` calls, add `weights=weights,
      strata=resample_strata,` beside the existing `resample_columns=resample_spec["declared"],`.

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2132 + 2 = 2134 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/cli.py`, in `_comparison_step_blocks`' `_column_mean`
      branch, change `strata=strata` to `strata=None`.
      `tests/test_cli.py::test_a_contrasts_column_draw_honours_resample_stratify_by` must **FAIL** on
      `stratified["ci95"][0] >= 5.0 - 1e-9`. **Checked against the test body:** the mutated call
      becomes identical to the test's own `plain` control, whose asserted lower bound is *below* the
      floor, so the two assertions become contradictory.

      **Second mutation:** in `command_run`, change `strata=resample_strata` to `strata=None` at both
      call sites. **This fails no test in this task** — all three tests call the functions directly.
      It is task 13's end-to-end run that catches it, and task 13's brief says so. Recorded rather
      than left silent: **a mutation's silence is evidence about the tests**, and the test that would
      catch this one is scheduled rather than missing.

      **The derived branch's `strata=strata` is reached by no mutation in this task either** — no
      fixture here supplies `resample_fns_by_key`, so the derived branch is never entered. Task 12's
      C-shaped fixture is where a derived contrast under a declared `stratify_by` is exercised, and
      its brief carries the mutation.

- [ ] **Step 6: Commit.** `cli: weights and resample strata reach the three comparison functions`

---

## Task 7: the weighted `_column_mean` closure — the payoff

**Files:** Modify `src/publishable/cli.py`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: `cli._comparison_step_blocks`' local `_column_mean(table, _name=metric_key) -> float`,
  which reads `getattr(table, _name)` and returns `sum(column) / len(column)` — read in
  `src/publishable/cli.py`; `stats.paired_percentile_of_derived`, whose every draw builds each row as
  `{"unit": k, **of[k]}` so the **unit key survives inside the draw** — read in
  `src/publishable/stats.py`; `stats.UnitTable.__getattr__`, which serves any column present in some
  row, and whose refusal is keyed on "this name appears in no row" so that `unit` — deliberately
  omitted from `columns` — is readable; `stats.weighted_mean_of(values, weights) -> float | None`,
  the single copy of the weighted mean, which gates through `stats.checked_weights` — same file.
- Produces: a weighted `_column_mean`; `mean_of(diffs)` replaced by the weighted mean of the
  differences under a weight; `method="weighted_paired_percentile_over_units"` passed through a new
  `method` keyword on `paired_percentile_of_derived`.

**This is the task C1–C3 actually need.** Their column contrasts route through
`paired_percentile_of_derived` because they declare `resample`; `paired_t_over_units` is never called
on them, raw or corrected. **A mutation on `paired_t_over_units` proves nothing about this task.**

**The construction gains a `method` keyword, not a `weights` one.** `paired_percentile_of_derived` is
shared by the derived branch — which decision 1 settles as *not* weighted by core — and the
`_column_mean` branch, which is. One construction therefore has to be able to produce two `method`
strings, and the arithmetic stays in the closure where the derived/column distinction already lives.
Nothing in `src/` reads `Interval.method` for control flow: every reader records it
(`cli`'s two metric blocks, `stats.summarize_step`'s two, `run_record`'s `Estimate` path, and
`coercion`'s `Estimate` check), so a defaulted keyword cannot change any existing behaviour.

**The weights are looked up by `unit`, per draw.** A bootstrap draw duplicates units on purpose, so
the weight vector must be built from the *drawn* keys and not from the roster — a vector filtered or
ordered differently weights the wrong unit, which is `summarize_step`'s own discipline one level over.

**The point estimate moves too.** `delta` is `mean_of(diffs)` today. Under a weight it is
Σwd/Σw over the same `col_keys` — which is identical to the difference of the two sides' weighted
column means over that set, so the point estimate and the pool cannot drift onto different rosters,
the property the existing comment claims for the unweighted case.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_cli.py`:

```python
def test_a_weighted_column_contrast_weights_its_delta_and_its_draws():
    """The payoff path. All three C configs declare `statistics.resample`, so a
    recorded column's contrast goes through `paired_percentile_of_derived` with the
    `_column_mean` closure — `paired_t_over_units` is never called on them.

    The two answers are exact arithmetic, not observations: unweighted
    (1+2+3+9+10+11)/6 = 6.0, weighted (1+2+3+27+30+33)/12 = 8.0. A weighting that
    did nothing, or that weighted only the point estimate, lands on 6.0 for one of
    the two assertions."""
    weighted, _ = _weighted_contrast_block(resample_columns=True, weights=_W_WEIGHTS)
    plain, _ = _weighted_contrast_block(resample_columns=True)
    assert plain["delta"] == pytest.approx(6.0)
    assert weighted["delta"] == pytest.approx(8.0)
    # The interval moved with it, drawn from the same seed: per-draw the weight is
    # monotone in the value here (1.0-3.0 carry 1, 9.0-11.0 carry 3), so every
    # drawn multiset's weighted mean is at least its unweighted mean, and sorting
    # preserves that elementwise. So the pool DOMINATES rather than merely
    # differing, which a wrong weighting would break in a detectable direction.
    assert weighted["ci95"][0] > plain["ci95"][0]
    assert weighted["ci95"][1] > plain["ci95"][1]


def test_a_weighted_column_contrast_records_the_documented_method_string():
    """The agreement pin, against the document rather than against a second
    literal: a test comparing each of two spellings to its own hard-coded string
    is how this repo shipped a name claiming an agreement no assertion made.
    `_interval_method_names` parses § Statistical reporting's construction
    tables."""
    weighted, _ = _weighted_contrast_block(resample_columns=True, weights=_W_WEIGHTS)
    plain, _ = _weighted_contrast_block(resample_columns=True)
    assert weighted["method"] == "weighted_paired_percentile_over_units"
    assert plain["method"] == "paired_percentile_over_units"
    assert weighted["method"] in _interval_method_names()
    assert plain["method"] in _interval_method_names()


def test_a_weighted_derived_contrast_keeps_the_unweighted_method_string():
    """Decision 1, pinned. Core does not weight a derived metric: its resample
    closure re-attributes the roster inside every draw, so the weight column
    reaches `aggregate` as a unit attribute and the template weights its own
    metric. So `method` stays `paired_percentile_over_units` even under a declared
    weight — the split this slice's whole payoff argument rests on, and the one no
    other test in this file can see."""
    from publishable.cli import _comparison_step_blocks
    from publishable.contrasts import Comparison
    from publishable.sweep import Condition

    def _derived(table):
        column = getattr(table, "m")
        return float(sum(column) / len(column))

    block, _members = _comparison_step_blocks(
        Comparison(id="c", of=1, against=0),
        roster=_cli_roster(6),
        aggregated={1: {"s": {"d": 6.0}}, 0: {"s": {"d": 0.0}}},
        collapsed_by_key={(1, "s"): _W_OF, (0, "s"): _W_AGAINST},
        derived_by_key={(1, "s"): {"d": 6.0}, (0, "s"): {"d": 0.0}},
        resample_fns_by_key={(1, "s"): {"d": _derived}, (0, "s"): {"d": _derived}},
        seed=7,
        draws=200,
        min_reported_n=None,
        findings=Collector(),
        where="condition 1",
        where_id="cond:1",
        conditions_by_index={
            0: Condition(index=0, label="baseline", is_baseline=True),
            1: Condition(index=1, label="arm", values={"analysis.method": "spearman"}),
        },
        resample_columns=True,
        weights=_W_WEIGHTS,
    )
    assert block["s"]["d"]["method"] == "paired_percentile_over_units"
    # And the unweighted arithmetic: core handed the closure the plain collapsed
    # rows, so the derived delta is 6.0 and not 8.0.
    assert block["s"]["d"]["delta"] == pytest.approx(6.0)


def test_a_weighted_stratified_column_contrast_weights_inside_the_strata():
    """The ordering constraint task 5 exists for, made observable. A weighted
    stratified draw is three `A` keys and three `B` keys with `B` carrying weight
    3, so its forced floor is (3·1·1 + 3·3·9)/12 = 7.0 — above the unweighted
    stratified floor of 5.0 and far above the unweighted unstratified 4.33. A
    closure built before the strata decision would weight over the wrong pool and
    miss this bound."""
    both, _ = _weighted_contrast_block(
        resample_columns=True, weights=_W_WEIGHTS, strata=_W_STRATA
    )
    stratified_only, _ = _weighted_contrast_block(resample_columns=True, strata=_W_STRATA)
    assert both["ci95"][0] >= 7.0 - 1e-9
    assert stratified_only["ci95"][0] >= 5.0 - 1e-9
    assert stratified_only["ci95"][0] < 7.0
```

- [ ] **Step 2: Run and see them fail.** The first fails on `weighted["delta"] ==
      pytest.approx(8.0)` (it is 6.0); the second on the `method` string; the fourth on
      `both["ci95"][0] >= 7.0`. The third — the derived control — **passes today**, and that is
      correct: it is a regression pin for a split task 7 must not break, so it goes green on arrival
      and stays green. Record that in the report rather than treating it as a broken test.

- [ ] **Step 3: Implement.** In `src/publishable/stats.py`, add the `method` keyword to
      `paired_percentile_of_derived` (after `strata`) and use it in the returned `Interval`:

```python
    strata: dict[str, str] | None = None,
    method: str = "paired_percentile_over_units",
) -> PairedResample:
```

```python
    return PairedResample(
        interval=Interval(low=values[lo], high=values[hi], method=method),
        draws_used=len(values),
        pool=values,
    )
```

      with the docstring paragraph explaining it: **the construction is shared by a derived contrast,
      which core does not weight, and a recorded column's contrast, which it does — so the caller
      names the string rather than this function deriving it from a `weights` parameter it
      deliberately does not take.**

      In `src/publishable/cli.py`, `_comparison_step_blocks`' column branch:

```python
                col_keys = [
                    k
                    for k in base_keys
                    if metric_key in of_collapsed[k] and metric_key in against_collapsed[k]
                ]
                diffs = [
                    of_collapsed[k][metric_key] - against_collapsed[k][metric_key] for k in col_keys
                ]
                n_paired = len(col_keys)
                # The intersection's OWN weights, in `col_keys` order, so nothing
                # downstream can weight a unit the difference beside it did not
                # come from. `None` when no weight is declared, which is what
                # keeps every unweighted construction on exactly the arithmetic it
                # had.
                col_weights = None if weights is None else [weights[k] for k in col_keys]
                resampled = None
                if resample_columns and n_paired >= 2:
                    # ... existing comment block unchanged ...
                    #
                    # **The weights live in the CLOSURE, not in the
                    # construction.** `paired_percentile_of_derived` is shared
                    # with the derived branch, which core does not weight
                    # (§ Weighted samples hands that weight column to `aggregate`
                    # as a unit attribute), so a `weights` parameter there would
                    # weight the wrong half. The closure can reach them because
                    # the construction keeps the real unit key inside every draw:
                    # each row is `{"unit": k, **of[k]}`, and a bootstrap draw
                    # duplicates units on purpose, so the vector is built from the
                    # DRAWN keys rather than from the roster — a vector filtered
                    # or ordered differently weights the wrong unit, which is
                    # `summarize_step`'s own discipline one level over.
                    def _column_mean(
                        table: UnitTable,
                        _name: str = metric_key,
                        _weights: dict[str, Any] | None = weights,
                    ) -> float:
                        column: list[float] = getattr(table, _name)
                        if _weights is None:
                            return float(sum(column) / len(column))
                        drawn = [_weights[k] for k in table.unit]
                        got = weighted_mean_of([float(v) for v in column], drawn)
                        if got is None:
                            # An empty column — the identical input on which the
                            # unweighted branch above raises `ZeroDivisionError`,
                            # and which `paired_percentile_of_derived` catches as a
                            # degenerate draw either way. Raised rather than
                            # coerced to a number, so the two branches refuse the
                            # same input; a fabricated 0.0 here would enter the
                            # pool as a real draw.
                            raise ValueError("a weighted column contrast drew an empty table")
                        return got

                    resampled = paired_percentile_of_derived(
                        of_collapsed,
                        against_collapsed,
                        col_keys,
                        _column_mean,
                        _column_mean,
                        seed,
                        draws=draws,
                        strata=strata,
                        method=(
                            "paired_percentile_over_units"
                            if weights is None
                            else "weighted_paired_percentile_over_units"
                        ),
                    )
                    interval = resampled.interval
                else:
                    interval = paired_t_over_units(diffs)
```

      and the metric block's `delta`:

```python
                    "delta": (
                        mean_of(diffs)
                        if col_weights is None
                        else weighted_mean_of(diffs, col_weights)
                    ),
```

      Add `weighted_mean_of` to the `from publishable.stats import (...)` list in `cli.py`.

      **No new error code, deliberately.** The empty-column branch raises a bare `ValueError`, which
      is what the unweighted branch's own arithmetic raises on the same input and what
      `paired_percentile_of_derived` already contains as a degenerate draw. Minting a code for it
      would put a § Errors row behind a condition the `n_paired >= 2` gate makes unreachable, and
      `reference.md` § Errors carries rows for conditions a reader can meet.

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2134 + 4 = 2138 passed**, 1 skipped,
      2 xfailed. Then the other three commands, and the mechanical `*.md` pass over the edited row.

- [ ] **Step 5: Mutate.** In `src/publishable/cli.py`, in `_column_mean`, change `drawn =
      [_weights[k] for k in table.unit]` to `drawn = [1 for _ in column]` — a uniform weighting,
      which is the shape this repo's statistics fixtures keep failing to detect.
      `tests/test_cli.py::test_a_weighted_column_contrast_weights_its_delta_and_its_draws` must
      **FAIL** on `weighted["ci95"][0] > plain["ci95"][0]`. **Checked against the test body:** with
      uniform weights the weighted call's *pool* becomes byte-identical to `plain`'s at the same
      seed, so the two `ci95` comparisons become `>` on equal numbers and fail — while
      `weighted["delta"] == 8.0` would still pass, because the delta is weighted outside the closure.
      **That is exactly why this test asserts both the delta and the interval**: either assertion
      alone leaves half the weighting unpinned, which is § 8's "a weighted interval beside an
      unweighted point estimate" one direction and the other.

      **Second mutation, for the delta:** change the metric block's `delta` back to bare
      `mean_of(diffs)`. The same test must **FAIL** on `weighted["delta"] ==
      pytest.approx(8.0)` — it becomes 6.0. **Checked against the test body:** 6.0 and 8.0 are
      distinct exact values, and `plain["delta"] == 6.0` in the same test is what says the mutation
      collapsed the two readings rather than breaking both.

      **Third mutation, for the derived split:** pass `weights` into
      `paired_percentile_of_derived`'s derived-branch call — i.e. give the derived closure the
      weighted arithmetic by passing `method="weighted_paired_percentile_over_units"` there too.
      `test_a_weighted_derived_contrast_keeps_the_unweighted_method_string` must **FAIL** on the
      `method` assertion. **Checked against the test body:** it asserts the exact unweighted spelling
      and the unweighted delta, and the mutation changes only the first, so the failure is
      attributable to the method string rather than to arithmetic.

      **No mutation reaches** the empty-column `ValueError` — the `n_paired >= 2` gate above makes it
      unreachable from any config, and a test that reached it would have to break that gate. It is a
      symmetry guard against the unweighted branch's own failure on the same input, not a behaviour
      with a caller.

      **And no mutation in this task reaches `strata` in the derived branch** — no fixture here
      supplies both a derived closure and a stratification. Task 12's C-shaped fixture does, and its
      brief carries the mutation.

- [ ] **Step 6: Commit.** `cli: a weighted column contrast weights its delta and every draw`

---

## Task 8: the record under a weight — `weighted_by`, `n_paired_effective`, and a weighted `cohens_d`

**Files:** Modify `src/publishable/stats.py`, `src/publishable/cli.py`, `tests/test_stats.py`,
`tests/test_cli.py`.

**Interfaces:**
- Consumes: `stats.kish_effective_n(weights) -> float`, which gates through `checked_weights` and
  answers `0.0` for an empty sequence — read in `src/publishable/stats.py`; `stats.cohens_dz(diffs) ->
  float | None`, `None` below two values and `None` at zero sd — same file;
  `stats._weighted_mean(checked, values)` and `stats.checked_weights(weights)`, the single copies —
  same file; `stats.weighted_t_over_units`' variance denominator `Σw − Σw²/Σw`, which is what makes
  equal weights reproduce the unweighted construction digit for digit — same file;
  `cli._comparison_step_blocks`' two metric blocks — read in `src/publishable/cli.py`;
  `run_record.assemble_run_yaml`, which attaches a comparison block **verbatim** and filters no keys
  — read in `src/publishable/run_record.py`.
- Produces: `stats.weighted_cohens_dz(diffs, weights) -> float | None`; three keys on every affected
  contrast entry — `weighted_by`, `n_paired_effective`, and a weighted `cohens_d`.

**Three record obligations, one task, because they move together or the feature is half delivered.**
The per-condition case makes exactly this argument: `value`, interval and `n.effective` move together
because "a weighted interval beside an unweighted point estimate would be a declaration accepted whose
effect is half delivered". A contrast has the same obligation and one more part — it reports an effect
size a condition does not.

**`n_paired_effective` is Kish over the paired intersection, and that is the trap.** `cli` builds
`weights` from **the whole roster**, and `_comparison_step_blocks` is called with `eval_roster` and a
collapsed table that under a declared holdout holds the test partition alone. Kish over the mapping
answers a different question than Kish over the intersection, and the natural implementation reaches
for the mapping and sums it. **No payoff config separates the readings** — C1–C3 all declare
`holdout: null` — so the fixture instantiates the seam directly: eight weights, a four-unit collapsed
table, three distinct answers (6.0 over the mapping, 3.0 over the intersection, 4 for the count).

**A weighted `cohens_dz` is documented and absent.** § Statistical reporting: "A weighted condition
standardizes by the weighted standard deviation, on the same weights the mean used." `cohens_dz(diffs)`
takes a list, and `cli` computes it from the local `diffs` regardless of the weight. **This is scoping
task 10, absorbed into this task rather than dropped** — the spec's 15 do not name it, and leaving it
out would publish a weighted delta beside an unweighted effect size on the payoff path.

**The variance denominator is `Σw − Σw²/Σw`, not `Σw`.** That is what makes equal weights reproduce
`cohens_dz` exactly rather than approximately — at w ≡ 1 it is n − 1 — and `Σw` would be a different
statistic wearing the same name. `weighted_t_over_units`' docstring makes the argument; do not
re-derive it.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_stats.py`:

```python
def test_a_weighted_dz_standardizes_by_the_weighted_standard_deviation():
    """`reference.md` § Statistical reporting: "A weighted condition standardizes by
    the weighted standard deviation, on the same weights the mean used."

    Exact arithmetic, not an observation. Σw = 12, Σw² = 30, so the denominator is
    12 − 30/12 = 9.5; Σw(d − 8)² = 49 + 36 + 25 + 3 + 12 + 27 = 152; 152/9.5 = 16.0,
    sd = 4.0, dz = 8.0/4.0 = 2.0. The unweighted answer over the same differences
    is 6/√20 = 1.3416..., so a weighting that did nothing lands on a different
    number rather than on this one."""
    from publishable.stats import cohens_dz, weighted_cohens_dz

    diffs = [1.0, 2.0, 3.0, 9.0, 10.0, 11.0]
    assert weighted_cohens_dz(diffs, [1, 1, 1, 3, 3, 3]) == pytest.approx(2.0)
    assert cohens_dz(diffs) == pytest.approx(1.3416407864998738)


def test_a_weighted_dz_at_equal_weights_is_the_unweighted_one():
    """The oracle, and the reason the variance denominator is `Σw − Σw²/Σw` rather
    than `Σw`: at w ≡ 1 it is n − 1, so this is a generalization rather than a
    second statistic wearing the same name. If this ever fails, the formula is
    wrong rather than this test."""
    from publishable.stats import cohens_dz, weighted_cohens_dz

    diffs = [1.0, 2.0, 3.0, 9.0, 10.0, 11.0]
    assert weighted_cohens_dz(diffs, [1] * 6) == pytest.approx(cohens_dz(diffs))
    # Invariant to rescaling, as every weighted construction here is: a weight
    # column summing to a population size gives the same answer as one summing to
    # the row count.
    assert weighted_cohens_dz(diffs, [7] * 6) == pytest.approx(cohens_dz(diffs))


def test_a_weighted_dz_refuses_the_degenerate_shapes_the_unweighted_one_does():
    """`None` below two differences, and `None` at zero dispersion — the two
    refusals `cohens_dz` carries, kept so the pair refuses the same inputs. Plus
    the one the weights add: a denominator of zero, which is all the weight on one
    unit, is the same n − 1 = 0 fact the length guard answers."""
    from publishable.stats import weighted_cohens_dz

    assert weighted_cohens_dz([1.0], [1]) is None
    assert weighted_cohens_dz([2.0, 2.0], [1, 3]) is None
```

      and to `tests/test_cli.py`:

```python
_K_OF = {f"u{i}": {"m": float(i + 1)} for i in range(4, 8)}
_K_AGAINST = {k: {"m": 0.0} for k in _K_OF}
_K_WEIGHTS = {
    "u0": 1, "u1": 1, "u2": 1, "u3": 3,
    "u4": 1, "u5": 1, "u6": 1, "u7": 3,
}


def test_a_weighted_contrast_entry_carries_the_three_documented_keys():
    """§ Contrasts: `weighted_by` beside `method`, `n_paired_effective` as a scalar
    sibling of `n_paired`, and `cohens_d` weighted on the same weights the delta
    used. All four move together or the declaration is half delivered.

    The key names are compared against the document's own § Contrasts text rather
    than against a second literal, which is the agreement a hard-coded pair of
    strings cannot make."""
    weighted, _ = _weighted_contrast_block(resample_columns=True, weights=_W_WEIGHTS)
    plain, _ = _weighted_contrast_block(resample_columns=True)
    section = _section_text("#### Contrasts: claims that aren't condition-vs-baseline")
    assert weighted["weighted_by"] == "sampling_weight"
    assert "weighted_by" in section
    assert "n_paired_effective" in section
    assert weighted["n_paired_effective"] == pytest.approx(4.8)
    assert weighted["n_paired"] == 6
    assert weighted["cohens_d"] == pytest.approx(2.0)
    # The unweighted neighbour: absent keys, not null ones, and the unweighted dz.
    assert "weighted_by" not in plain
    assert "n_paired_effective" not in plain
    assert plain["cohens_d"] == pytest.approx(1.3416407864998738)


def test_kish_is_taken_over_the_paired_intersection_not_the_weight_mapping():
    """The trap `cli`'s own weight-construction site sets up: `weights` is built
    from the WHOLE roster, while a contrast is computed over the intersection —
    under a declared `holdout` the collapsed table is the test partition alone.

    Three distinct answers separate the three readings, which is what makes this
    fixture discriminating: Kish over the whole mapping is 12²/24 = 6.0, over the
    four-unit intersection 6²/12 = 3.0, and `n_paired` is 4. No two coincide, so a
    denominator taken from the mapping and one taken from the count both fail.

    C1-C3 all declare `holdout: null`, so no payoff config separates them — the
    fixture instantiates the seam directly."""
    from publishable.cli import _comparison_step_blocks
    from publishable.contrasts import Comparison
    from publishable.sweep import Condition

    block, _members = _comparison_step_blocks(
        Comparison(id="c", of=1, against=0),
        roster=_cli_roster(8),
        aggregated={1: {"s": {"m": 6.5}}, 0: {"s": {"m": 0.0}}},
        collapsed_by_key={(1, "s"): _K_OF, (0, "s"): _K_AGAINST},
        derived_by_key={},
        resample_fns_by_key={},
        seed=7,
        draws=200,
        min_reported_n=None,
        findings=Collector(),
        where="condition 1",
        where_id="cond:1",
        conditions_by_index={
            0: Condition(index=0, label="baseline", is_baseline=True),
            1: Condition(index=1, label="arm", values={"analysis.method": "spearman"}),
        },
        resample_columns=True,
        weights=_K_WEIGHTS,
    )
    assert block["s"]["m"]["n_paired"] == 4
    assert block["s"]["m"]["n_paired_effective"] == pytest.approx(3.0)


def test_a_weighted_derived_contrast_carries_the_record_keys_without_a_weighted_method():
    """Decision 1's other half. Core does not weight a derived metric, so `method`
    stays the unweighted spelling and `cohens_d` stays `null` — the worked
    example's own rule, a derived metric having no per-unit value to difference.
    But `weighted_by` and `n_paired_effective` still travel beside it: the
    declaration is true of the run either way, which is the same arrangement
    `summarize_step` makes per condition."""
    from publishable.cli import _comparison_step_blocks
    from publishable.contrasts import Comparison
    from publishable.sweep import Condition

    def _derived(table):
        column = getattr(table, "m")
        return float(sum(column) / len(column))

    block, _members = _comparison_step_blocks(
        Comparison(id="c", of=1, against=0),
        roster=_cli_roster(6),
        aggregated={1: {"s": {"d": 6.0}}, 0: {"s": {"d": 0.0}}},
        collapsed_by_key={(1, "s"): _W_OF, (0, "s"): _W_AGAINST},
        derived_by_key={(1, "s"): {"d": 6.0}, (0, "s"): {"d": 0.0}},
        resample_fns_by_key={(1, "s"): {"d": _derived}, (0, "s"): {"d": _derived}},
        seed=7,
        draws=200,
        min_reported_n=None,
        findings=Collector(),
        where="condition 1",
        where_id="cond:1",
        conditions_by_index={
            0: Condition(index=0, label="baseline", is_baseline=True),
            1: Condition(index=1, label="arm", values={"analysis.method": "spearman"}),
        },
        resample_columns=True,
        weights=_W_WEIGHTS,
    )
    entry = block["s"]["d"]
    assert entry["weighted_by"] == "sampling_weight"
    assert entry["n_paired_effective"] == pytest.approx(4.8)
    assert entry["method"] == "paired_percentile_over_units"
    assert entry["cohens_d"] is None
```

      **`weighted_by` needs the attribute *name*, which `_comparison_step_blocks` does not have** —
      it receives the mapping only. So the signature takes one more defaulted keyword,
      `weighted_by: str | None = None`, threaded from `command_run`'s existing `weight_by` local
      through the two callers. The test fixtures above pass it via `_weighted_contrast_block`; update
      that helper to pass `weighted_by="sampling_weight"` whenever `weights` is given. **Write the
      helper's update in this step**, so the tests are self-consistent when they first run:

      Insert exactly two lines into task 6's `_weighted_contrast_block`, immediately before its
      `block, members = _comparison_step_blocks(` call and after its three local imports:

```python
    if "weights" in extra:
        extra.setdefault("weighted_by", "sampling_weight")
```

      Nothing else in that helper changes: the `_comparison_step_blocks(...)` call already ends in
      `**extra`, which is what carries the new keyword through. `setdefault` rather than assignment, so
      a caller naming its own `weighted_by` — task 12's `_c_shape_common` does — keeps it.

- [ ] **Step 2: Run and see them fail.** The two `stats` tests fail with `ImportError`; the three
      `cli` tests fail with `TypeError: ... unexpected keyword argument 'weighted_by'`.

- [ ] **Step 3: Implement.** In `src/publishable/stats.py`, beside `cohens_dz`:

```python
def weighted_cohens_dz(diffs: Sequence[float], weights: Sequence[Any]) -> float | None:
    """The weighted mean of the per-unit differences over their weighted standard
    deviation.

    `reference.md` § Statistical reporting: "A weighted condition standardizes by
    the weighted standard deviation, on the same weights the mean used." So the
    same weights the delta was computed with, and no others — a *d* standardized by
    an unweighted dispersion is a ratio of two different samples' summaries.

    **The variance denominator is `Σw − Σw²/Σw`, not `Σw`**, the same choice
    `weighted_t_over_units` argues at length: at w ≡ 1 it is n − 1, so equal
    weights reproduce `cohens_dz` digit for digit and this is a generalization
    rather than a second statistic wearing the same name. `Σw` would shrink the
    denominator and inflate every *d*.

    Invariant to rescaling the weights, as every weighted construction here is:
    both the mean and the variance divide the scale out.

    `None` below two differences and `None` at zero dispersion, the two refusals
    `cohens_dz` carries, kept so the pair refuses the same inputs — and `None` for
    a zero denominator, which is all the weight concentrated on one unit and the
    same n − 1 = 0 fact the length guard answers.

    `weights` is annotated `Any` for the reason `weighted_t_over_units`' is: a
    weight is a unit attribute, `units._from_table` builds those from
    `csv.DictReader`, and `units.usable_weight` — reached through
    `checked_weights` — is the single gate `validate` approved the config against.
    """
    if len(diffs) < 2:
        return None
    w = checked_weights(weights)
    total = sum(w)
    denominator = total - sum(x * x for x in w) / total
    if denominator <= 0:
        return None
    mean = _weighted_mean(w, diffs)
    variance = sum(a * (d - mean) ** 2 for a, d in zip(w, diffs, strict=True)) / denominator
    sd = math.sqrt(variance)
    return mean / sd if sd > 0 else None
```

      In `src/publishable/cli.py`, add `weighted_by: str | None = None` to all three signatures, pass
      it down from both `command_run` call sites as `weighted_by=weight_by if weights else None`, and
      in `_comparison_step_blocks` add the three keys to both metric blocks after they are built:

```python
            # The three facts a weight adds to a contrast entry, and they move
            # together with the delta and the interval: § Contrasts requires it,
            # and a weighted delta beside an unweighted effect size or an
            # `n_paired` with no effective size beside it is a declaration
            # accepted whose effect is half delivered. Absent — not null — when no
            # weight is declared, the same absent-not-null shape `weighted_by`
            # already has per condition.
            #
            # **Kish is over the PAIRED INTERSECTION**, whose weights are
            # `entry_weights` below, not over the roster-wide mapping `weights`
            # holds: under a declared `holdout` the collapsed table is the test
            # partition alone, and the size reported beside an interval has to be
            # the size the interval was computed at. Summing the mapping is the
            # natural implementation and the wrong one.
            if weights is not None:
                metric_block[metric_key]["weighted_by"] = weighted_by
                metric_block[metric_key]["n_paired_effective"] = kish_effective_n(
                    [weights[k] for k in (base_keys if is_derived else col_keys)]
                )
```

      and, in the column branch's metric block, the effect size:

```python
                    "cohens_d": (
                        cohens_dz(diffs)
                        if col_weights is None
                        else weighted_cohens_dz(diffs, col_weights)
                    ),
```

      Import `kish_effective_n` and `weighted_cohens_dz` from `publishable.stats` in `cli.py`.

      **`col_keys` is not in scope in the derived branch and `base_keys` is not the column's set** —
      that is why the expression above chooses by `is_derived`, and why the block is placed after both
      branches have run rather than duplicated inside each. Read the surrounding code before placing
      it: `is_derived`, `base_keys` and `col_keys` must all be bound at that point, and `col_keys` is
      assigned only in the `else` branch, so the conditional expression is what keeps the placement
      legal.

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2138 + 5 = 2143 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/cli.py`, change the Kish argument to `list(weights.values())`
      — Kish over the whole mapping.
      `tests/test_cli.py::test_kish_is_taken_over_the_paired_intersection_not_the_weight_mapping` must
      **FAIL**: it asserts 3.0 and the mapping gives 6.0. **Checked against the test body:** the
      fixture's eight-unit mapping and four-unit collapsed table give different answers by
      construction, and the same test also asserts `n_paired == 4`, so neither 6.0 nor 4 can pass as
      3.0. **`test_a_weighted_contrast_entry_carries_the_three_documented_keys` would NOT catch this**
      — its mapping and intersection coincide at six units — which is exactly why the second fixture
      exists.

      **Second mutation, for the effect size:** change `cohens_d` back to bare `cohens_dz(diffs)`.
      `test_a_weighted_contrast_entry_carries_the_three_documented_keys` must **FAIL** on
      `weighted["cohens_d"] == pytest.approx(2.0)` — it becomes 1.3416..., which the same test asserts
      as `plain`'s value, so the mutation collapses two readings the test holds apart.

      **Third mutation, for the weighted variance denominator:** in
      `stats.weighted_cohens_dz`, change `denominator = total - sum(x * x for x in w) / total` to
      `denominator = total`. `tests/test_stats.py::test_a_weighted_dz_at_equal_weights_is_the_unweighted_one`
      must **FAIL**. **Checked against the test body:** at w ≡ 1 the correct denominator is n − 1 = 5
      and the mutant's is n = 6, so the two *d*s differ by √(6/5) ≈ 1.095 — a 9.5 % gap, far outside
      `pytest.approx`'s default tolerance. `test_a_weighted_dz_standardizes_by_the_weighted_standard_deviation`
      fails too, on 2.0 versus 152/12 → sd 3.56 → 2.25.

      **No mutation reaches** `weighted_cohens_dz`'s `denominator <= 0` branch through `cli` — reaching
      it needs all the weight on one unit, which `checked_weights` permits (every weight positive
      finite) but which no fixture builds. The unit test
      `test_a_weighted_dz_refuses_the_degenerate_shapes_the_unweighted_one_does` covers the zero-sd
      and short-input branches; the zero-denominator branch is pinned by nothing, and that is stated
      rather than claimed. Add a case if one can be built: `weighted_cohens_dz([1.0, 2.0], [1, 0])` is
      refused by `checked_weights` before the denominator is computed, so the branch may be
      structurally unreachable — **check that before adding a test that cannot fail**.

- [ ] **Step 6: Commit.** `cli: a weighted contrast entry records weighted_by, its effective size and a weighted dz`

---

## Task 9: the corrected bound — `weighted_paired_t_over_units`, and `_corrected_bounds` reading it

**Files:** Modify `src/publishable/stats.py`, `src/publishable/correction.py`,
`tests/test_stats.py`, `tests/test_correction.py`.

**Interfaces:**
- Consumes: `stats.paired_t_over_units(diffs, confidence=0.95) -> Interval | None`, which delegates to
  `t_over_units` and rewraps the `method` string — read in `src/publishable/stats.py`;
  `stats.weighted_t_over_units(values, weights, confidence=0.95) -> Interval | None`, `None` below two
  values and `None` when Kish's size falls below two — same file;
  `correction._corrected_bounds(member, level)`, which tests `diffs` first, then `pool`, and returns
  `None` when neither — read in `src/publishable/correction.py`; `correction.Member.weights` from
  task 4.
- Produces: `stats.weighted_paired_t_over_units(diffs, weights, confidence=0.95) -> Interval | None`;
  `_corrected_bounds` building the weighted construction whenever `member.weights` is set.

**Why the construction is built here rather than in task 10.** `_corrected_bounds` is its **first
caller**, so task 9 cannot be written without it. The spec puts the construction in task 10 and this
is the one place the plan reorders it; task 10 wires the same function into the *raw* interval.

**Delegate, do not hand-roll a second variance.** `paired_t_over_units` wraps `t_over_units` and
rewrites the `method`; the weighted sibling wraps `weighted_t_over_units` the same way. That inherits
the `Σw − Σw²/Σw` denominator, the Kish df, the equal-weights reduction and the rescaling invariance
— four properties `weighted_t_over_units`' docstring already argues and which a second copy would
come to disagree with.

**Off the payoff path, and this is where to say it.** `cli`'s `corrected_from_pool = is_derived or
resample_columns` is `True` for all three C configs, so their corrected bound reads
`interval_at(member.pool)` and the pool is already weighted by task 7's closure — **the payoff path's
corrected bound is consistent for free.** Everything in this task serves the non-`resample` column
path, and its fixtures must set `resample_columns=False` to reach it.

**What the record does when Kish falls below two.** `weighted_t_over_units` returns `None` there, so
the raw `ci95` is `null` and `ci95_corrected` is `null` beside a **present** `weighted_by` and a
present `n_paired_effective` below 2. That is a new combination and it is the honest one: the
weighting happened, the interval had no df to describe it with. `family_members` drops a member whose
`ci95` is `None` before either evidence field is read, so it takes no rank and does not inflate the
family.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_stats.py`:

```python
def test_a_weighted_paired_t_is_the_weighted_construction_under_a_paired_name():
    """The general case's raw interval, and its corrected counterpart. Delegates to
    `weighted_t_over_units` and rewrites the `method`, exactly as
    `paired_t_over_units` delegates to `t_over_units` — so the `Σw − Σw²/Σw`
    denominator, the Kish df and the rescaling invariance are inherited rather than
    re-derived.

    The centre is exact arithmetic: Σwd/Σw = 96/12 = 8.0 weighted against 36/6 =
    6.0 unweighted. A centre is asserted rather than an endpoint because it is
    exact under any df, so this cannot be a test that agrees with a wrong critical
    value."""
    from publishable.stats import paired_t_over_units, weighted_paired_t_over_units

    diffs = [1.0, 2.0, 3.0, 9.0, 10.0, 11.0]
    weighted = weighted_paired_t_over_units(diffs, [1, 1, 1, 3, 3, 3])
    plain = paired_t_over_units(diffs)
    assert weighted is not None and plain is not None
    assert (weighted.low + weighted.high) / 2 == pytest.approx(8.0)
    assert (plain.low + plain.high) / 2 == pytest.approx(6.0)
    assert weighted.method == "weighted_paired_t_over_units"
    assert plain.method == "paired_t_over_units"
    # The df moved too, and it is the part that bites: Kish's size here is
    # 12²/30 = 4.8 against 6 units, so the weighted half-width is wider than the
    # weighted sem alone would give. Pinned as the half-width ratio against the
    # unweighted one, which no equal-weight implementation can reproduce.
    assert (weighted.high - weighted.low) != pytest.approx(plain.high - plain.low)


def test_a_weighted_paired_t_at_equal_weights_is_the_unweighted_one():
    """The oracle. Equal weights must reproduce `paired_t_over_units` digit for
    digit — endpoints, not merely centre — which is what `weighted_t_over_units`'
    variance denominator buys and what a `Σw` denominator would break."""
    from publishable.stats import paired_t_over_units, weighted_paired_t_over_units

    diffs = [1.0, 2.0, 3.0, 9.0, 10.0, 11.0]
    weighted = weighted_paired_t_over_units(diffs, [1] * 6)
    plain = paired_t_over_units(diffs)
    assert weighted is not None and plain is not None
    assert weighted.low == pytest.approx(plain.low)
    assert weighted.high == pytest.approx(plain.high)


def test_a_weighted_paired_t_returns_none_when_kish_falls_below_two():
    """Inherited from `weighted_t_over_units`, and worth its own pin because the
    record shape it produces is new: `ci95: null` beside a present `weighted_by`
    and an `n_paired_effective` below 2. Eight rows concentrated onto 1.7
    effective units have no more dispersion for a df to describe than one row
    does. Weights [1,1,1,9] give 12²/84 = 1.714."""
    from publishable.stats import weighted_paired_t_over_units

    assert weighted_paired_t_over_units([1.0, 2.0, 3.0, 10.0], [1, 1, 1, 9]) is None
```

      and to `tests/test_correction.py`:

```python
def test_a_corrected_bound_over_weighted_differences_is_weighted_too():
    """Decision 4, made observable. `_corrected_bounds` rebuilds the corrected
    interval from the same evidence as the raw one — so weighted differences get a
    weighted construction at the smaller α, not an unweighted counterpart of a
    weighted raw interval.

    Two members, identical but for the weights, at a family size of one so the
    level is α itself and the corrected bound is the raw one's own construction.
    The centres are exact: 8.0 weighted, 6.0 unweighted."""
    diffs = (1.0, 2.0, 3.0, 9.0, 10.0, 11.0)
    common = dict(step="s", metric="m", ci95=(4.0, 12.0), pool=None, declaration_index=0)
    weighted = Member(where="cond:1", delta=8.0, diffs=diffs, weights=(1, 1, 1, 3, 3, 3), **common)
    plain = Member(where="cond:2", delta=6.0, diffs=diffs, **common)
    got_w = corrected_for([weighted], "bonferroni", 1, {"comparisons": 1, "metrics": 1})
    got_p = corrected_for([plain], "bonferroni", 1, {"comparisons": 1, "metrics": 1})
    low_w, high_w = got_w[("cond:1", "s", "m")]["ci95_corrected"]
    low_p, high_p = got_p[("cond:2", "s", "m")]["ci95_corrected"]
    assert (low_w + high_w) / 2 == pytest.approx(8.0)
    assert (low_p + high_p) / 2 == pytest.approx(6.0)


def test_a_pool_carrying_member_is_unaffected_by_the_weights_branch():
    """The payoff path's own corrected bound, pinned as unchanged. A column
    contrast under a declared `resample` carries the POOL, whose draws task 7's
    closure already weighted, so `interval_at` reads a second rank pair off
    weighted evidence and nothing more is needed. `Member` refuses weights beside a
    pool, so this is the shape that must keep working untouched."""
    pool = tuple(float(i) for i in range(200))
    member = Member(
        where="cond:1", step="s", metric="m", delta=100.0, ci95=(5.0, 195.0),
        pool=pool, diffs=None, declaration_index=0,
    )
    got = corrected_for([member], "bonferroni", 1, {"comparisons": 1, "metrics": 1})
    assert got[("cond:1", "s", "m")]["ci95_corrected"] is not None
```

- [ ] **Step 2: Run and see them fail.** The three `stats` tests fail with `ImportError`; the first
      `correction` test fails on the weighted centre (it is 6.0 — the unweighted construction over the
      same differences); the second passes today and is a regression pin.

- [ ] **Step 3: Implement.** In `src/publishable/stats.py`, beside `paired_t_over_units`:

```python
def weighted_paired_t_over_units(
    diffs: Sequence[float], weights: Sequence[Any], confidence: float = 0.95
) -> Interval | None:
    """Student's *t* on the *weighted* per-unit differences, df = Kish's effective n − 1.

    The contrast's interval is its own construction over the paired intersection,
    never a difference of the two sides' intervals — `paired_t_over_units`'
    argument, unchanged by the weighting.

    Delegates to `weighted_t_over_units` and rewrites the `method`, exactly as
    `paired_t_over_units` delegates to `t_over_units`. That is not tidiness: it is
    what makes the `Σw − Σw²/Σw` variance denominator, the Kish df, the exact
    reduction to the unweighted form at equal weights, and the invariance to
    rescaling the weights properties of ONE construction rather than of two that
    can drift apart. A hand-rolled variance here is how a paired interval and a
    per-condition one come to disagree about what a weighted interval is.

    `None` below two differences and `None` when Kish's effective size falls below
    two, both inherited: the record then carries `ci95: null` beside a present
    `weighted_by` and an `n_paired_effective` below 2 — the weighting happened, and
    there was no df to describe it with.
    """
    plain = weighted_t_over_units(diffs, weights, confidence)
    if plain is None:
        return None
    return Interval(low=plain.low, high=plain.high, method="weighted_paired_t_over_units")
```

      In `src/publishable/correction.py`, import it and extend `_corrected_bounds`:

```python
from publishable.stats import interval_at, paired_t_over_units, weighted_paired_t_over_units
```

```python
    if member.diffs is not None:
        # The weights, when the member carries them, decide WHICH t construction
        # rebuilds the bound — the same evidence at a smaller α either way. A
        # weighted raw interval with an unweighted corrected counterpart is
        # narrower or wider than the truth by construction rather than by
        # evidence, which is the fault `__post_init__`'s exactly-one rule refuses
        # one axis over and which no reader of `run.yaml` could detect.
        got = (
            paired_t_over_units(member.diffs, confidence=1.0 - level)
            if member.weights is None
            else weighted_paired_t_over_units(
                member.diffs, member.weights, confidence=1.0 - level
            )
        )
        return None if got is None else (got.low, got.high)
    if member.pool is not None:
        return interval_at(member.pool, 1.0 - level)
    return None
```

      and extend that function's docstring with the sentence, and the module docstring's claim if it
      names the constructions.

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2143 + 5 = 2148 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/correction.py`, change the conditional back to bare
      `paired_t_over_units(member.diffs, confidence=1.0 - level)`.
      `tests/test_correction.py::test_a_corrected_bound_over_weighted_differences_is_weighted_too`
      must **FAIL** on the weighted centre. **Checked against the test body:** the two members carry
      identical `diffs` and differ only in `weights`, so under the mutation both corrected bounds
      centre on 6.0 — and the test asserts 8.0 for one and 6.0 for the other, which the mutation
      makes contradictory. **A test asserting only that the two members' bounds differ would have
      been enough here too, but a test asserting only the weighted centre without the unweighted
      one beside it would not attribute the failure.**

      **Second mutation, for the delegation:** in `stats.weighted_paired_t_over_units`, change
      `weighted_t_over_units(diffs, weights, confidence)` to `t_over_units(diffs, confidence)` — a
      weighted name over an unweighted construction, which is the "comment claiming a guarantee the
      code does not provide" shape as code.
      `tests/test_stats.py::test_a_weighted_paired_t_is_the_weighted_construction_under_a_paired_name`
      must **FAIL** on the weighted centre. **Checked against the test body:** the centre is 8.0
      weighted and 6.0 unweighted, exact under any df, so the mutation cannot pass by landing on a
      similar interval.

      **Third mutation, for the method string:** change the returned `method` to
      `"paired_t_over_units"`. The same test must **FAIL** on `weighted.method ==
      "weighted_paired_t_over_units"`. **Checked:** the same test asserts `plain.method ==
      "paired_t_over_units"`, so the mutation makes the two indistinguishable and the assertion pair
      contradictory.

      **No mutation reaches** the `Kish < 2` route through `correction` — no `Member` fixture here has
      an effective size below two. `tests/test_stats.py::test_a_weighted_paired_t_returns_none_when_kish_falls_below_two`
      pins the construction's own refusal; the record shape it produces (`ci95_corrected: null`
      beside a present `weighted_by`) is pinned by nothing, and that is stated rather than claimed.

- [ ] **Step 6: Commit.** `correction: a weighted raw interval gets a weighted corrected counterpart`

---

## Task 10: the weighted raw interval on the non-`resample` column path — the general case

**Files:** Modify `src/publishable/cli.py`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: `stats.weighted_paired_t_over_units` from task 9; `cli._comparison_step_blocks`' `else:`
  branch, `interval = paired_t_over_units(diffs)` — read in `src/publishable/cli.py`; its
  `corrected_from_pool = is_derived or resample_columns` and the `Member(...)` construction, the one
  site in `src/` where a `Member` is built — same file.
- Produces: the `else:` branch weighted under a weight; `Member(weights=...)` set there and only
  there.

**This task is NOT on the payoff path, and the brief has to say so.** All three C configs declare
`statistics.resample`, so `resample_columns` is `True` and this branch is never taken on them.
`paired_t_over_units` is never called on C1–C3, raw or corrected. **A mutation here proves nothing
about the payoff**; what it makes honest is the general case — a weighted column contrast in a config
that declares no `resample`, which would otherwise publish an unweighted delta's interval beside a
weighted delta.

**`Member.weights` is set only where `diffs` is.** `corrected_from_pool` decides which field the
member carries; `weights` must follow `diffs`, or task 4's second `__post_init__` rule raises. That
rule is the guard against getting this wrong, and it will fire loudly rather than silently — which is
the point of having put it there.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_cli.py`:

```python
def test_a_weighted_column_contrast_with_no_resample_takes_the_weighted_t():
    """The general case, off the payoff path: C1-C3 all declare
    `statistics.resample`, so `resample_columns` is True for them and this branch
    is never taken. What it makes honest is a weighted column contrast in a config
    that declares no `resample`, which would otherwise publish an unweighted
    interval beside a weighted delta.

    The centre is exact — 8.0 weighted against 6.0 unweighted — so this cannot
    pass by landing on a similar interval, and the `method` is checked against the
    document's own construction tables rather than a second literal."""
    weighted, members = _weighted_contrast_block(resample_columns=False, weights=_W_WEIGHTS)
    plain, plain_members = _weighted_contrast_block(resample_columns=False)
    assert weighted["method"] == "weighted_paired_t_over_units"
    assert weighted["method"] in _interval_method_names()
    assert plain["method"] == "paired_t_over_units"
    low, high = weighted["ci95"]
    assert (low + high) / 2 == pytest.approx(8.0)
    low_p, high_p = plain["ci95"]
    assert (low_p + high_p) / 2 == pytest.approx(6.0)
    # The member carries the weights beside the differences, so the corrected
    # bound task 9 built is reachable from a real run rather than from a
    # hand-built `Member` alone.
    assert members[0].weights == (1, 1, 1, 3, 3, 3)
    assert members[0].diffs is not None
    assert plain_members[0].weights is None


def test_a_resampled_column_contrasts_member_carries_no_weights():
    """`corrected_from_pool = is_derived or resample_columns`, so the payoff path's
    member carries the POOL — already drawn from weighted values — and `Member`
    refuses weights beside one. Pinned because setting `weights` unconditionally is
    the natural mistake, and task 4's second `__post_init__` rule is what would
    turn it into a loud `ValueError` rather than a doubled weighting."""
    weighted, members = _weighted_contrast_block(resample_columns=True, weights=_W_WEIGHTS)
    assert members[0].pool is not None
    assert members[0].diffs is None
    assert members[0].weights is None
```

- [ ] **Step 2: Run and see them fail.** The first fails on `weighted["method"] ==
      "weighted_paired_t_over_units"` (it is `paired_t_over_units`); the second passes today and is a
      regression pin for the field task 4 added.

- [ ] **Step 3: Implement.** In `src/publishable/cli.py`, `_comparison_step_blocks`:

```python
                else:
                    # The general case, and it is off the payoff path: a config
                    # declaring `resample` never reaches here. Weighted when a
                    # weight is declared, because the delta above already is —
                    # `weighted_paired_t_over_units` takes its df from Kish's
                    # effective size over this intersection, which is the
                    # `n_paired_effective` recorded beside it.
                    interval = (
                        paired_t_over_units(diffs)
                        if col_weights is None
                        else weighted_paired_t_over_units(diffs, col_weights)
                    )
```

      and, at the `Member` construction:

```python
            corrected_from_pool = is_derived or resample_columns
            members.append(
                Member(
                    where=where_id,
                    step=step_name,
                    metric=metric_key,
                    delta=metric_block[metric_key]["delta"] or 0.0,
                    ci95=(interval.low, interval.high) if interval else None,
                    pool=tuple(resampled.pool) if corrected_from_pool and resampled else None,
                    diffs=None if corrected_from_pool else tuple(diffs),
                    # Only where `diffs` is: a pool is already drawn from weighted
                    # values, so weights beside one would be applied twice, and
                    # `Member.__post_init__` refuses that rather than letting it
                    # through. `corrected_from_pool` is the single decision, read
                    # once for both fields, so the two cannot disagree.
                    weights=(
                        None
                        if corrected_from_pool or col_weights is None
                        else tuple(col_weights)
                    ),
                    declaration_index=0,
                )
            )
```

      Import `weighted_paired_t_over_units` in `cli.py`. **`col_weights` is bound only in the column
      branch** — read the surrounding code: the derived branch does not assign it, so the expression
      above must be reached with it bound, which it is only because `corrected_from_pool` is `True`
      for every derived metric and `or` short-circuits. **That is fragile and must not be relied
      on.** Bind `col_weights = None` beside `is_derived` at the top of the per-metric loop instead,
      before either branch, so the name is always defined and the short-circuit is not load-bearing.

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2148 + 2 = 2150 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/cli.py`, change the `else:` branch back to bare
      `paired_t_over_units(diffs)`.
      `tests/test_cli.py::test_a_weighted_column_contrast_with_no_resample_takes_the_weighted_t` must
      **FAIL** on the `method` assertion and on the weighted centre. **Checked against the test
      body:** the same test asserts the unweighted spelling and the 6.0 centre for `plain`, so the
      mutation makes the two rows indistinguishable and both assertion pairs contradictory.

      **Second mutation, for the member:** change `weights=(...)` to `weights=None` unconditionally.
      The same test must **FAIL** on `members[0].weights == (1, 1, 1, 3, 3, 3)`. **Checked:** the
      test also asserts `plain_members[0].weights is None`, so the mutation collapses two readings
      the test holds apart rather than breaking both.

      **Third mutation, for the pool guard:** change `weights=(None if corrected_from_pool or
      col_weights is None else tuple(col_weights))` to `weights=(None if col_weights is None else
      tuple(col_weights))` — i.e. set weights beside a pool too.
      `test_a_resampled_column_contrasts_member_carries_no_weights` must **FAIL** — and read how:
      `Member.__post_init__` raises `ValueError` at construction, so the test errors rather than
      asserting. That is the intended failure, and it is worth noting that it fails *inside*
      `_comparison_step_blocks` rather than at an assertion — which is what task 4's rule was for.

      **No mutation in this task reaches** `Member.weights`' length check — the vector is built from
      `col_keys` in the same expression the `diffs` are, so no fixture can misalign them. That is the
      guard working, not an untested branch: task 4's own unit test is what pins it.

- [ ] **Step 6: Commit.** `cli: a weighted column contrast with no resample takes the weighted paired t`

---

## Task 11: the two sibling § Errors rows, and § Weighted samples' one sentence about a weighted contrast

**Files:** Modify `docs/reference.md`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: `E-DATA-ALLOCATION-CONTRAST`'s § Errors row, which contrasts its own **per comparison**
  reading against `E-DATA-WEIGHT-CONTRAST`'s and `E-DATA-CLUSTER-CONTRAST`'s whole-family one — read
  in `docs/reference.md` § Errors `validate` reports; `E-DATA-CLUSTER-CONTRAST`'s row, which cites
  *"the same test `E-DATA-WEIGHT-CONTRAST` below applies"* and *"exactly as below"* — same section;
  § Weighted samples' sentence *"a contrast between two weighted conditions uses the same weights on
  both sides, which is automatic under `allocation: within` and worth checking when it isn't"*.
- Produces: both sibling rows stating their own reading rather than citing a row that is about to be
  deleted; § Weighted samples' contrast sentence replaced by what core now does.

**Neither sibling row is deleted, and neither citation may be rewritten into a new one.** Both rows
exist for their own codes and both make a real distinction. What has to go is the *pointer* — a row
citing a row task 13 deletes becomes a dangling reference, and `CLAUDE.md`'s rule is to prefer
deleting a claim to rewriting it. So each row states the property itself.

**The § Validation row is NOT touched here.** See § Two deviations: a § Validation row and its
§ Errors row are one check seen from two ends, and task 13 strikes both with the emit in one commit.

**§ Weighted samples' sentence is now false in one direction and vacuous in the other.** Core builds
**one** roster-wide weight mapping and hands it to both sides of every comparison, so "uses the same
weights on both sides" holds by construction under `between` as well as under `within`, and "worth
checking when it isn't" describes a case core cannot produce. Replace it with what the code does.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_cli.py`:

```python
def test_the_sibling_refusal_rows_state_their_own_reading():
    """Two § Errors rows contrasted their own family-reading against
    `E-DATA-WEIGHT-CONTRAST`'s. That row is deleted in the task after next, so a
    citation of it becomes a dangling reference — and this repo's rule is to delete
    a claim rather than rewrite it into a second one. Each row now states the
    property itself.

    Located by each row's own final cell, which is what tells a row from a
    citation, and asserted with a presence beside each absence so a mislocated row
    cannot pass by matching nothing."""
    lines = REFERENCE_MD.read_text().split("\n")

    def _row(code: str) -> str:
        return next(
            line for line in lines if line.rstrip().endswith(f"| `{code}` |")
        )

    allocation = _row("E-DATA-ALLOCATION-CONTRAST")
    cluster = _row("E-DATA-CLUSTER-CONTRAST")
    assert "per comparison" in allocation  # the control
    assert "cluster_by" in cluster  # the control
    assert "E-DATA-WEIGHT-CONTRAST" not in allocation
    assert "E-DATA-WEIGHT-CONTRAST" not in cluster


def test_weighted_samples_says_what_core_does_with_a_contrasts_weights():
    """§ Weighted samples' only sentence about a weighted contrast named no
    construction, no `method` string and no check, and its "worth checking when it
    isn't" described a case core cannot produce: one roster-wide weight mapping
    reaches both sides of every comparison, so the same-weights property holds by
    construction under `between` too."""
    section = _section_text("### Weighted samples")
    assert "weight_by" in section  # the control
    assert "worth checking when it isn't" not in section
    assert "the same weights reach both sides" in section
```

- [ ] **Step 2: Run and see them fail.** The first on `"E-DATA-WEIGHT-CONTRAST" not in allocation`;
      the second on `"worth checking when it isn't" not in section`.

- [ ] **Step 3: Implement.** In `docs/reference.md` § Errors `validate` reports:

      In `E-DATA-ALLOCATION-CONTRAST`'s row, replace *"Read **per comparison**, not for the whole
      resolved family the way `E-DATA-WEIGHT-CONTRAST` and `E-DATA-CLUSTER-CONTRAST` below are"* with
      *"Read **per comparison**, not once for the whole resolved family"*.

      In `E-DATA-CLUSTER-CONTRAST`'s row, replace *"the same family `W-STATS-FAMILY` counts and the
      same test `E-DATA-WEIGHT-CONTRAST` below applies"* with *"the same family `W-STATS-FAMILY`
      counts"*, and replace *"The *resolved* family is the test rather than the declaration, exactly
      as below:"* with *"The *resolved* family is the test rather than the declaration:"* — the
      sentence that follows already states the rule in full, so the pointer was carrying nothing.

      In § Weighted samples, replace the contrast clause of the four-interactions paragraph with:

```markdown
And a [contrast](#contrasts-claims-that-arent-condition-vs-baseline) between two weighted conditions
uses the same weights on both sides, because **the same weights reach both sides**: core resolves one
weight mapping for the run and hands it to every comparison, so the property holds by construction
rather than by the allocation happening to be `within`. What a contrast weights is a recorded
column — its delta, its interval and its `cohens_d` — while a derived metric's weight arrives at
`aggregate` as a unit attribute exactly as it does per condition; [§ Statistical
reporting](#statistical-reporting) names the two weighted paired constructions and states that split.
```

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2150 + 2 = 2152 passed**, 1 skipped,
      2 xfailed. Then the other three commands, and the mechanical `*.md` pass: both edited rows still
      have their header's cell count, every `#anchor` in the new paragraph resolves.

- [ ] **Step 5: Mutate.** In `docs/reference.md`, re-insert `` `E-DATA-WEIGHT-CONTRAST` `` into
      `E-DATA-CLUSTER-CONTRAST`'s row. `tests/test_cli.py::test_the_sibling_refusal_rows_state_their_own_reading`
      must **FAIL** on the last assertion. **Checked against the test body:** each row is located by
      its own final cell, which the mutation does not touch, so the control assertion still passes and
      the failure is attributable to the re-inserted citation rather than to a mislocated row.

      **Second mutation, for the § Weighted samples half:** delete the phrase *"the same weights reach
      both sides"* from the new paragraph while leaving the rest.
      `test_weighted_samples_says_what_core_does_with_a_contrasts_weights` must **FAIL** on its third
      assertion while its control and its absence assertion both still pass — which is what says the
      test reads the replacement rather than merely the deletion.

      **No mutation reaches** the § Validation row — task 13 owns it, and this task deliberately does
      not touch it.

- [ ] **Step 6: Commit.** `docs: the sibling refusal rows state their own reading, and weights reach both sides`

---

## Task 12: the three C shapes, exercised against a real weighted contrast

**Files:** Modify `tests/test_cli.py`.

**Interfaces:**
- Consumes: `cli._compute_vs_baseline` and `cli._compute_declared_contrasts` with `weights`,
  `weighted_by`, `strata` and `resample_columns` — as built in tasks 6–10; the three shortcut configs'
  shared `data.units` block, `weight_by: sampling_weight`, `cluster_by: null`, `holdout: null`, and
  `statistics.resample: {method: bootstrap, n: 2000, stratify_by: [consensus_label, count_stratum]}`
  with `report_by: [sex, age_band, count_stratum, dx_family, record_source]` — read in
  `docs/feasibility-llm-growth-studies.md` § Shortcut: three runs and § C1/§ C2/§ C3.
- Produces: three tests, one per C shape — C1 a `sweep.baseline` generating `vs_baseline` deltas, C2
  and C3 a declared `statistics.contrasts` entry — each over a weighted, stratified, resampled column
  **and** a derived metric.

**Direct calls, not `command_run`, and the brief has to say why.** `E-DATA-WEIGHT-CONTRAST` is still
alive at this commit and `command_run` returns before running on any error, so a weighted contrast
cannot reach these functions through `run` yet. Task 13 adds the `validate`-clean and `run`-through
halves. **This is a deviation from the spec's task 12 wording** and it is reported as one.

**Every one of these tests asserts `E-DATA-WEIGHT-CONTRAST` alongside its own findings where it
touches `validate` at all — and none of them touches `validate`.** So there is nothing for task 13 to
delete here, which is itself worth stating: the deletions task 13 makes are in
`tests/test_validate.py` only.

**Each C shape's derived metric is the point, not decoration.** C1's headline metric is AUROC, derived
by the template's `aggregate` from the per-unit `prob`/`consensus_label` columns — so the payoff
configs exercise **both** branches of `paired_percentile_of_derived`: the `_column_mean` closure for
`prob` and the template closure for `auroc`. A test covering only the column half would miss the split
decision 1 rests on.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_cli.py`:

```python
_C_STRATA = {
    "u0": "abnormal|low", "u1": "abnormal|low", "u2": "abnormal|low",
    "u3": "normal|high", "u4": "normal|high", "u5": "normal|high",
}


def _c_shape_common():
    """The three shortcut configs' shared shape, as `_comparison_step_blocks`' own
    arguments: `weight_by: sampling_weight`, a `resample` declaring
    `stratify_by: [consensus_label, count_stratum]` (composed into one label the
    way `cli.resample_strata` composes it), `cluster_by: null` and `holdout: null`.

    One recorded column, `prob`, and one derived metric, `auroc` — C1's headline
    metric is derived by the template's `aggregate`, so both branches of
    `paired_percentile_of_derived` are exercised.
    """
    from publishable.sweep import Condition

    def _derived(table):
        column = getattr(table, "prob")
        return float(sum(column) / len(column))

    of = {k: {"prob": v["m"]} for k, v in _W_OF.items()}
    against = {k: {"prob": 0.0} for k in _W_OF}
    return dict(
        conditions=[
            Condition(index=0, label="regime=utilization_only", is_baseline=True),
            Condition(index=1, label="regime=zero_shot", values={"model.regime": "zero_shot"}),
        ],
        roster=_cli_roster(6),
        aggregated={1: {"step03_screen": {"prob": 6.0, "auroc": 6.0}},
                    0: {"step03_screen": {"prob": 0.0, "auroc": 0.0}}},
        collapsed_by_key={(1, "step03_screen"): of, (0, "step03_screen"): against},
        derived_by_key={(1, "step03_screen"): {"auroc": 6.0},
                        (0, "step03_screen"): {"auroc": 0.0}},
        resample_fns_by_key={(1, "step03_screen"): {"auroc": _derived},
                             (0, "step03_screen"): {"auroc": _derived}},
        seed=7,
        draws=200,
        findings=Collector(),
        resample_columns=True,
        weights=_W_WEIGHTS,
        weighted_by="sampling_weight",
        strata=_C_STRATA,
    )


def test_the_c1_shape_publishes_a_weighted_stratified_vs_baseline_delta():
    """C1 — a one-axis `grid` over model regime with the utilization-only
    regression as the declared `baseline`, over a weighted roster with a
    patient-level stratified bootstrap. The last core-side refusal these three
    carry is what task 13 retires; this is the number it was standing in for.

    Exact arithmetic on the column: weighted (1+2+3+27+30+33)/12 = 8.0 against
    unweighted 6.0. Forced bound on the interval: a weighted stratified draw is
    three low-stratum keys at weight 1 and three high at weight 3, so its floor is
    (3·1·1 + 3·3·9)/12 = 7.0."""
    from publishable.cli import _compute_vs_baseline

    out, members = _compute_vs_baseline(doc={}, **_c_shape_common())
    assert out is not None
    column = out[1]["step03_screen"]["prob"]
    derived = out[1]["step03_screen"]["auroc"]
    assert column["delta"] == pytest.approx(8.0)
    assert column["method"] == "weighted_paired_percentile_over_units"
    assert column["ci95"][0] >= 7.0 - 1e-9
    assert column["weighted_by"] == "sampling_weight"
    assert column["n_paired_effective"] == pytest.approx(4.8)
    assert column["cohens_d"] == pytest.approx(2.0)
    # The derived half, on the same run: core did not weight it, so its `method`
    # is the unweighted spelling and its `cohens_d` is null — while `weighted_by`
    # and the effective size travel beside it anyway.
    assert derived["method"] == "paired_percentile_over_units"
    assert derived["cohens_d"] is None
    assert derived["weighted_by"] == "sampling_weight"
    assert derived["n_paired_effective"] == pytest.approx(4.8)
    # The derived draw was stratified too: its own forced floor is the UNWEIGHTED
    # stratified one, 5.0, because core does not weight a derived metric.
    assert derived["ci95"][0] >= 5.0 - 1e-9
    # Both metrics joined the correction family, and the column's member carries
    # the pool rather than the differences.
    assert {(m.step, m.metric) for m in members} == {
        ("step03_screen", "prob"),
        ("step03_screen", "auroc"),
    }
    assert all(m.pool is not None and m.weights is None for m in members)


def test_the_c2_and_c3_shape_publishes_a_weighted_declared_contrast():
    """C2 and C3 — a declared `statistics.contrasts` entry rather than a baseline,
    which is the other route to a comparison and the one `_compute_vs_baseline`
    cannot reach. The same weighted, stratified numbers, on the record shape that
    lands beside the conditions rather than inside one."""
    from publishable.cli import _compute_declared_contrasts

    doc = {
        "statistics": {
            "contrasts": [
                {
                    "id": "sensitivity",
                    "of": "regime=zero_shot",
                    "against": "regime=utilization_only",
                }
            ]
        }
    }
    out, members = _compute_declared_contrasts(doc=doc, **_c_shape_common())
    assert out is not None
    entry = out[0]
    assert entry["id"] == "sensitivity"
    column = entry["step03_screen"]["prob"]
    assert column["delta"] == pytest.approx(8.0)
    assert column["method"] == "weighted_paired_percentile_over_units"
    assert column["n_paired_effective"] == pytest.approx(4.8)
    assert column["ci95"][0] >= 7.0 - 1e-9
    assert [m.where for m in members] == ["contrast:sensitivity"] * 2


def test_a_weighted_report_by_level_mints_no_member_and_no_delta():
    """§ Reporting strata: strata "repeat `aggregated` metrics only, never
    `vs_baseline` or a contrast's delta", and they do not join the correction
    family. All three C configs declare `report_by`, so the boundary is live on
    exactly the shapes this task exercises — and `_comparison_step_blocks` excludes
    the `by` key from its per-metric loop, which is what makes a stratum unable to
    become a comparison.

    Asserted as an absence beside a presence that must report: the two real
    metrics are still there, so a loop that produced nothing at all would fail
    rather than pass."""
    from publishable.cli import _compute_vs_baseline

    common = _c_shape_common()
    common["aggregated"][1]["step03_screen"]["by"] = {"sex": {"f": {"prob": 5.0}}}
    common["aggregated"][0]["step03_screen"]["by"] = {"sex": {"f": {"prob": 0.0}}}
    out, members = _compute_vs_baseline(doc={}, **common)
    assert out is not None
    assert set(out[1]["step03_screen"]) == {"prob", "auroc"}
    assert len(members) == 2
```

- [ ] **Step 2: Run and see them fail.** If tasks 6–10 are complete, all three **pass on arrival**.
      That is the correct outcome for an integration task and it is stated rather than dressed up as a
      red-green cycle: what these tests add is the C shapes' own combination — weight × stratify ×
      resample × derived × `report_by` — which no earlier fixture holds together, and the mutations in
      step 4 are what establish they can fail. **If any of them fails, stop**: an earlier task is
      incomplete and this task is not the place to fix it.

- [ ] **Step 3: Run the whole suite.** `uv run pytest` → **2152 + 3 = 2155 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 4: Mutate.** In `src/publishable/cli.py`, in `_comparison_step_blocks`' **derived**
      branch, change `strata=strata` to `strata=None`.
      `tests/test_cli.py::test_the_c1_shape_publishes_a_weighted_stratified_vs_baseline_delta` must
      **FAIL** on `derived["ci95"][0] >= 5.0 - 1e-9`. **Checked against the test body:** the derived
      draw's forced stratified floor is 5.0 and an unstratified draw over the same six values reaches
      4.33 at this seed and draw count — and this is the **only** test in the suite that exercises a
      derived contrast under a declared `stratify_by`, which is why task 6's brief recorded the
      mutation as scheduled rather than available.

      **Second mutation, for the `by` exclusion:** in `_comparison_step_blocks`, change
      `sorted((set(of_summary) & set(against_summary)) - {"by"})` to
      `sorted(set(of_summary) & set(against_summary))`.
      `test_a_weighted_report_by_level_mints_no_member_and_no_delta` must **FAIL** on the set equality
      and on `len(members) == 2` — the stratum block becomes a third "metric" and mints a third
      `Member`. **Checked against the test body:** the fixture actually installs a `by` key on both
      sides, which is the seam a fixture without one could not instantiate.

      **Third mutation, for `weighted_by`'s threading:** in `command_run`, change
      `weighted_by=weight_by if weights else None` to `weighted_by=None`. **This fails no test in
      this task** — all three call the functions directly with their own `weighted_by`. Task 13's
      end-to-end run is what catches it, and task 13's brief says so.

- [ ] **Step 5: Commit.** `cli: the three shortcut shapes publish a weighted, stratified contrast`

---

## Task 13: retire `E-DATA-WEIGHT-CONTRAST` — the emit, both rows, the comments, and the five tests

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`, `tests/test_validate.py`,
`tests/test_cli.py`.

**Interfaces:**
- Consumes: `validate._check_sweep`'s single emit, guarded by `comparisons > 0 and
  isinstance(weight_by, str) and weight_by`, and its comment block — read in
  `src/publishable/validate.py`; the same file's three other mentions — `_check_unimplemented`'s
  docstring listing it in the combination-refusal family, a comment citing it as a placement
  precedent, and the two sibling guards' comments citing it as their precedent; its § Errors row,
  identified by being the one line whose final cell is the code itself; its § Validation row,
  *Weighted deltas aren't computed*, which names no identifier and is found by reading the table;
  the five tests in `tests/test_validate.py` and the two comment blocks near them.
- Produces: the code gone from `src/` and from `docs/reference.md`; the five tests rewritten to assert
  the design now validates clean; two new end-to-end tests through `validate_config` and `command_run`.

**Last among the code tasks, and the reason is the discipline H7b Part A bought.** The refusal is what
keeps a weighted contrast from publishing a number nobody can interpret. Every construction, record
key and disclosure it stood in for now exists: the weighted closure (7), the record keys (8), the
corrected bound (9), the general case (10), and the strata the payoff configs declare (5).

**Enumerate by reading, then confirm by grep — in that order.** The scoping's own § 1 was reached that
way and its brief's `grep -c` count was wrong. Read `_check_sweep` in full first. Then confirm:

```
grep -rn "E-DATA-WEIGHT-CONTRAST" src/ docs/reference.md tests/
```

→ must be empty at the end of this task. **Can-fail control on the identical file list:**

```
grep -rn "E-DATA-CLUSTER-CONTRAST" src/ docs/reference.md tests/ | wc -l
```

→ non-zero, a different number from the same shape of sweep.

**The five tests are edits, not deletions, and each one asserts something afterwards.** `validate`
collects, so a test asserting a finding *set* that contained the refusal is a **deletion from a
list**; a test asserting `codes(path) == {"E-DATA-WEIGHT-CONTRAST"}` becomes
`codes(path) == set()`, which is a stronger claim than "the code is gone" — it says the design is one
core runs today.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_validate.py`:

```python
def test_a_weighted_generated_comparison_validates_clean(write_config, tmp_path):
    """The retirement. A weighted roster with a baseline over an enumerated axis
    generates `vs_baseline` deltas, and every construction they need now exists —
    the weighted column closure, the weighted paired *t*, the weighted corrected
    bound, the record keys, and the stratified draw. Free of every finding rather
    than merely of the old code, which is what says the design is one core runs."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n")
    path = write_config(
        {
            "data.units": _weighted_units(),
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman", "kendall"]},
            },
        }
    )
    assert codes(path) == set()


def test_a_weighted_declared_contrast_validates_clean(write_config, tmp_path):
    """The other route to a comparison — named rather than generated, so no
    baseline is involved at all. It reached the same refusal and it reaches the
    same weighted constructions now."""
    _weighted_table(tmp_path, "p1,2.0\np2,3.0\n")
    path = write_config(
        {
            "data.units": _weighted_units(),
            "sweep": {"grid": {"analysis.method": ["pearson", "spearman"]}},
            "statistics": {
                "contrasts": [
                    {
                        "id": "spearman_vs_pearson",
                        "of": "method=spearman",
                        "against": "method=pearson",
                    }
                ]
            },
        }
    )
    assert codes(path) == set()
```

      and to `tests/test_cli.py`:

```python
def test_a_weighted_run_publishes_a_weighted_delta_end_to_end(tmp_path, capsys, monkeypatch):
    """The first weighted contrast to reach `run.yaml`. Until this task
    `command_run` returned before running on `E-DATA-WEIGHT-CONTRAST`, so every
    weighted-contrast test called `_comparison_step_blocks` directly — this is the
    pin that the whole path is wired, including the three things `command_run`
    threads and no direct call can see: `weights`, `weighted_by` and
    `resample_strata`.

    `_METHOD_VARYING_STEP` is the starter step for the reason
    `test_a_baseline_sweep_reports_a_delta` uses it: its per-unit values differ
    both by condition and per unit between conditions, so the per-unit differences
    themselves vary. A step recording the same numbers under two labels gives a
    zero-width interval and a `cohens_d` of `None` whatever the weighting does,
    which is the trap this file's own comment records.

    Six units weighted 1/1/1/3/3/3, so Kish's size is 12²/30 = 4.8 against six
    completed — the two figures differ, which is what makes the `n_paired_effective`
    assertion say something."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        replication={"repeats": [{"kind": "seed", "n": 1}], "order": "as_declared"},
        roster_csv=(
            "patient_id,sampling_weight,band\n"
            "p1,1,low\np2,1,low\np3,1,low\np4,3,high\np5,3,high\np6,3,high\n"
        ),
        units_overrides={
            "attributes": ["sampling_weight", "band"],
            "weight_by": "sampling_weight",
        },
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
        statistics={
            "correction": "holm",
            "resample": {"method": "bootstrap", "n": 2000, "stratify_by": ["band"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _first_contrast(run, "method=spearman")
    assert entry is not None
    assert entry["method"] == "weighted_paired_percentile_over_units"
    assert entry["weighted_by"] == "sampling_weight"
    assert entry["n_paired"] == 6
    assert entry["n_paired_effective"] == pytest.approx(4.8)
    assert entry["cohens_d"] is not None
    # The corrected bound came off the same weighted pool rather than from a
    # re-run unweighted construction: `corrected_from_pool` is True under a
    # declared `resample`, so this is the payoff path's own corrected interval.
    assert entry["ci95_corrected"] is not None
```

- [ ] **Step 2: Run and see them fail.** The two `validate` tests fail on `codes(path) == set()` —
      `E-DATA-WEIGHT-CONTRAST` is reported. The end-to-end test fails at `command_run`'s exit code.

- [ ] **Step 3: Implement.**

      In `src/publishable/validate.py`, `_check_sweep`: delete the whole `if comparisons > 0 and
      isinstance(weight_by, str) and weight_by:` block **and its comment block**, and the
      `weight_by = units_here.get("weight_by")` line that feeds only it. **`units_here` stays** — the
      cluster guard reads it, and the "one call, read twice" comment above it explains why there is
      one call; re-read that comment and keep whichever half still applies.

      Delete `E-DATA-WEIGHT-CONTRAST` from `_check_unimplemented`'s docstring list, from the comment
      citing it as a placement precedent, and from both sibling guards' comments. **In each sibling
      comment, delete the citation rather than repointing it** — `E-DATA-CLUSTER-CONTRAST`'s comment
      should state its own placement argument, which it already does in the sentence beside the
      citation.

      In `docs/reference.md`: delete `E-DATA-WEIGHT-CONTRAST`'s § Errors row whole, and the
      § Validation row *Weighted deltas aren't computed* whole. **Check every count phrase and every
      row-relative reference near both** — an insertion or deletion moves rows, and locating a row by
      position is wrong twice in this repo's history.

      In `tests/test_validate.py`, five edits:

      | Test | Edit |
      |---|---|
      | `test_a_weighted_generated_comparison_is_refused` | **Replaced** by `test_a_weighted_generated_comparison_validates_clean` above; delete the old one and its docstring |
      | `test_a_weighted_declared_contrast_is_refused` | **Replaced** by `test_a_weighted_declared_contrast_validates_clean` above |
      | `test_a_weighted_baseline_that_generates_no_comparison_stays_legal` | Its `crossed` control asserted the refusal; that control is now `codes(...) == set()` too, which makes the test's own claim vacuous — **delete the control and rename nothing**, then check whether the remaining assertion still says something. If it does not, delete the test: the shape it distinguished no longer has two sides |
      | `test_an_unweighted_comparison_is_untouched` | Asserts `"E-DATA-WEIGHT-CONTRAST" not in codes(path)`, which is now trivially true — **strengthen to `codes(path) == set()`** rather than deleting, since the unweighted neighbour is still worth pinning |
      | `test_the_weight_refusal_does_not_promise_the_derived_estimators_will_weight` (task 1's) | The refusal is gone, so **delete it**; its claim was about a message that no longer exists, and task 1's `spec-defects.md` entry carries the settled fact |
      | `test_a_weighted_report_by_is_not_a_contrast` | Already asserts `codes(path) == set()` — **unchanged**, and it now says something different and still true: a weighted `report_by` publishes no delta and joins no family |

      And the two comment blocks in `tests/test_validate.py` that cite the code as a precedent for a
      narrow combination refusal: **delete the citation, keep the argument**. One is beside
      `E-SWEEP-SAMPLE-BASELINE`'s tests and one beside the cluster tests.

      In `tests/test_cli.py`, also delete `test_the_weight_refusals_errors_row_names_no_estimator`
      (task 1's) — the row it parses is gone, so `next(...)` would raise `StopIteration`.

      Then write the end-to-end test's body against `run_a_project`'s real signature, which this file
      already uses throughout — read one existing caller before writing it.

- [ ] **Step 4: Run and see them pass.** `uv run pytest` → **2155 + 2 (new) − 3 (deleted) = 2154
      passed**, 1 skipped, 2 xfailed, **assuming
      `test_a_weighted_baseline_that_generates_no_comparison_stays_legal` survives**. State the number
      you actually get and account for every difference; do not adjust the expectation silently.
      Then the other three commands, and the mechanical `*.md` pass. Then the two sweeps above.

      **Confirm § The one config file still reads "One declaration above is not yet built"** and that
      `tests/test_cli.py`'s `NOT_BUILT_COMMANDS` set equality still passes — retiring a combination
      refusal moves neither.

- [ ] **Step 5: Mutate.** In `src/publishable/cli.py`, change `command_run`'s
      `weights=weights` to `weights=None` at both comparison call sites.
      `tests/test_cli.py::test_a_weighted_run_publishes_a_weighted_delta_end_to_end` must **FAIL** on
      the `method` assertion. **Checked against the test body:** with `weights=None` the closure takes
      the unweighted branch and the method is `paired_percentile_over_units`, and the test also
      asserts `weighted_by` and `n_paired_effective`, both of which disappear — so three assertions
      fail rather than one. **This is the mutation tasks 6 and 12 deferred to here**, and it is the
      only one in the slice that can catch `command_run`'s threading.

      **Second mutation:** change `strata=resample_strata` to `strata=None` at both call sites. **Read
      the test body before believing this fails:** the end-to-end test asserts no forced bound, only
      the record shape, so it does **not** discriminate. **Prescribe instead:** extend
      `test_a_weighted_run_publishes_a_weighted_delta_end_to_end` with an assertion the strata force —
      the resolved `resample` echo on the *condition's* own metric block already records
      `stratify_by`, and `summarize_step` honours it per condition, so the contrast's own draw is the
      only place a dropped strata is visible. Build the roster so a stratum's composition forces a
      floor the unstratified draw crosses, exactly as task 7's fixture does, and assert
      `entry["ci95"][0]` against it. **If that cannot be arranged inside `run_a_project`'s roster
      shape, say so and leave the mutation recorded as blind at this site** — the direct-call test
      `test_a_contrasts_column_draw_honours_resample_stratify_by` already pins the honouring, and what
      would remain unpinned is only `command_run`'s threading of it.

      **Third mutation, for the retirement itself:** restore the deleted guard in `validate.py`.
      Both new `validate` tests must **FAIL** on `codes(path) == set()`.

- [ ] **Step 6: Commit.** `validate: retire E-DATA-WEIGHT-CONTRAST — a weighted contrast is computed`

---

## Task 14: the owned prose sweep — by claim, over named files — and the re-ownering

**Files:** Modify `docs/reference.md`, `docs/experimental-designs.md`, `docs/design-principles.md`,
`README.md` (only where a sweep finds something), `src/publishable/*.py` comments and docstrings,
`docs/superpowers/spec-defects.md`.

**Interfaces:**
- Consumes: every claim this slice falsified, enumerated by **reading** the surfaces it changed and
  then confirmed by grep — the order `CLAUDE.md` § Answering a question with a proxy requires, and the
  order whose reverse shipped a credential leak.
- Produces: no claim in the repo saying a contrast is unweighted; every `spec-defects.md` entry owned
  by "H4b" re-ownered to **H4b-2** by name.

**Sweep by claim, not by file.** Three sweeps in one slice have stopped one file short — one covered
`src/` and `docs/` but not `tests/`, one fixed a sentence in one function and missed the same sentence
in the function that falsified it, one stopped at the file its brief happened to name. So each sweep
below names its **file list** and its **can-fail control**, and none of them filters output.

- [ ] **Step 1: Enumerate the claims by reading, then confirm each by grep.** For each claim, read the
      surface it lives on first and write down where it appears; only then run the sweep. The claims
      this slice falsified:

      1. *"no contrast construction in this build weights at all"* and its paraphrases.
      2. *"`paired_t_over_units` takes a list of per-unit differences and nothing else"* — still true
         of that function, and now **misleading** wherever it is offered as the reason a weighted
         contrast is impossible. It appears in `E-DATA-ALLOCATION-CONTRAST`'s and
         `E-DATA-CLUSTER-CONTRAST`'s rows, where it is doing correct work for *those* codes; read each
         occurrence and change only the ones that argue about weights.
      3. *"`paired_percentile_of_derived` is the only percentile construction with no `strata`
         parameter"* — false as of task 5. Likely in `stats.py` docstrings and in the development
         record; **the development record is never retro-edited**, so only `src/`, `tests/` and the
         four documents are in scope.
      4. *"a weighted `cohens_dz` is documented and absent"* — false as of task 8.
      5. *"`Member` has no weights field"* — false as of task 4. Check `correction.py`'s own module
         docstring and `Member.__post_init__`'s.
      6. *"§ Weighted samples' only sentence about a weighted contrast names no construction"* — false
         as of task 11.

      The sweeps, each over a **named file list**:

```
grep -rn "no contrast construction\|contrast construction in this build" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md src/ tests/
grep -rn "and nothing else" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md src/ tests/
grep -rn "only percentile construction" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md src/ tests/
grep -rn "weighted contrast\|weights a contrast\|weight a contrast" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md src/ tests/
```

      **Prove each sweep can fail** by running it against a string known to be present on the same
      file list — for instance `grep -rn "paired_t_over_units" README.md docs/design-principles.md
      docs/experimental-designs.md docs/reference.md src/ tests/`, which must return many lines.

      Also check `docs/experimental-designs.md` § Mistakes core prevents and § What core will not do
      for you: neither is expected to move — a weighted contrast is now *computed*, not refused, and
      nothing there listed it as a refusal — but the cross-document pass covers them and no other task
      opens them. **Read both sections and record that they were read**, rather than concluding from a
      grep's silence.

- [ ] **Step 2: Re-owner the filings.** `grep -n "H4b" docs/superpowers/spec-defects.md` — every entry
      whose owner is "H4b" points at a **closed slice** the moment this branch merges, which reads as
      live work nobody holds. Re-owner each to **H4b-2 — clusters through contrasts** by name, or, for
      any entry this slice actually discharged, strike it as CLOSED with the task that closed it.
      **Read each entry before editing it**: a filing's claims about the code go stale like any other
      comment, and this slice changed code three of them describe.

      The entries to read, by what each *is* rather than by position:

      | Entry | What this slice did to it |
      |---|---|
      | The contrast path's resample disclosure gaps — thin finding, zero-width sweep, resolved-`resample` echo | **Untouched**, and its three findings are still owed. Re-owner to H4b-2 and note that task 5 made the zero-width half *newly reachable* through a stratified draw, which task 5's own entry records |
      | A column resample is only ever defined given finite inputs | **Untouched.** Re-owner; its two `*_is_a_known_unfixed_gap` tests must move **with** the entry, not silently |
      | A column metric's `resample_draws` records the requested `n` | Bookkeeping only — the pointer must not outlive the entry it points at |
      | `percentile_of_derived`'s zero-width interval, and the `report_by` asymmetry deferred beside it | **Live on C1–C3** and untouched: a `report_by` level's recorded-column interval stays `t_over_units` under a declared `resample`. Re-owner, and state that this slice's payoff figure is qualified by it |
      | `paired_percentile_of_derived`'s sorted-pool precondition unasserted | **Task 5 added a second unsorted-input route** (a `strata` mapping whose pools are sorted independently). Read the entry, extend its condition, re-owner |
      | § *How a metric becomes a number* is cited across the repo and does not exist | **Explicitly declined**, in writing: this slice cites it (task 9's docstring inherits a citation from `paired_t_over_units`) and did not write it. Record the decline and name H4b-2 as next to touch the material, or leave it unassigned and say so — silence is how it goes stale |

- [ ] **Step 3: Apply the edits, preferring deletion.** For each claim, delete the falsified sentence
      rather than rewriting it wherever the surrounding text still says what it needs to. A rewrite
      invents; a deletion cannot. Where a claim must be replaced, replace it with a statement that
      **derives** from something already maintained — the construction tables, the `Status` column —
      rather than with a new enumeration.

- [ ] **Step 4: Run everything.** `uv run pytest` → the count task 13 established, unchanged: this
      task adds no test. Then `ruff check`, `ruff format --check`, `mypy`. Then the mechanical `*.md`
      pass over every file edited.

- [ ] **Step 5: Mutate.** There is no code in this task, so the mutation is on the **sweep**, not on
      behaviour: pick one claim you deleted, re-insert it, and confirm the sweep that was supposed to
      find it does. **A sweep that cannot fail is the defect this step exists to rule out**, and this
      repo has lost a true hit to a filtered sweep before.

      **No mutation reaches** any of it through the test suite. That is stated rather than papered
      over: prose is not pinned by tests here, and the four documents' consistency rests on the
      mechanical and cross-document passes.

- [ ] **Step 6: Commit.** `docs: no claim left saying a contrast is unweighted, and every H4b filing re-ownered`

---

## Task 15: the dated count, in its own section

**Files:** Modify `docs/feasibility-llm-growth-studies.md`.

**Interfaces:**
- Consumes: § Executability on this build, whose shape is one dated subsection per measurement —
  *"Measured on \<date\> against commit \<sha\>"* — each naming every refusal by its code, and whose
  most recent entry is dated 2026-08-17 against the H7b Part B commit — read in
  `docs/feasibility-llm-growth-studies.md`; § Shortcut: three runs, whose prose says the combination is
  refused as `E-DATA-WEIGHT-CONTRAST` and that the refusal is temporary; the two prose sites in
  § Three repositories and § What core refuses that cite the code.
- Produces: a **new** dated subsection; the three prose citations updated; **no earlier subsection
  edited**.

**Append, never retro-edit.** A measurement records what was true on its date. The 2026-08-17 Part B
entry's "Six stay blocked … `E-DATA-WEIGHT-CONTRAST` (H4b) for C1, C2 and C3" was true when written
and stays. This slice adds its own entry below it.

**The two figures must not be collapsed in either direction.** Decision 6, and `CLAUDE.md`'s
feasibility step 10:

- **Do not write "unblocks 3 of the nine"** — that is the refusal-gated count the charter states, and
  it reads as an executable count a month later.
- **Do not write "six of nine execute"** — that promotes a blocker count to an execution count across
  an unsettled dependency.

**And the cell's second clause is false for C1–C3 either way, on two counts that bite exactly them.**
"Every field they declare is honoured" — `resample.stratify_by` on a contrast is honoured as of task 5,
so that half is now true; but a `report_by` level's recorded-column interval stays `t_over_units` under
a declared `resample`, which all three declare. Say so.

- [ ] **Step 1: Re-measure, do not carry.** Write the nine configs' `data`/`statistics` blocks through
      `validate_config` the way the 2026-08-17 entry did — a throwaway probe file, run, then deleted;
      no tracked file touched. Record the actual per-config finding lists. **The measurement is the
      deliverable**; a claim carried from the previous entry without re-checking is worse than one
      omitted.

      **Prove the probe can fail**, exactly as the previous entry proved its own: set
      `data.units.holdout.frac` to `0` on an otherwise-clean block and confirm `E-DATA-HOLDOUT-FRAC`
      appears, then revert the field and confirm the zero-error result returns. A block that could not
      fail this way is not a measurement.

- [ ] **Step 2: Write the subsection.** Append to § Executability on this build, after the Part B
      entry:

```markdown
### Measured on <date> against commit <sha> — after H4b-1

H4b-1 retires `E-DATA-WEIGHT-CONTRAST`; this measurement was taken against the commit above, on its
branch. Every one of the nine configs' `data`/`statistics` blocks was run through `validate_config`
again rather than re-derived from the previous entry.

**H4b-1 retires one refusal that 3 of 9 configs hit** (`E-DATA-WEIGHT-CONTRAST`) — the last core-side
refusal C1, C2 and C3 carry — and takes the *no-remaining-core-side-blocker* count from **three to
six**: E1, E2, E5 unchanged, C1, C2, C3 newly. **The executable count stays at three.** C1–C3's
`io.reuse_from` dependency is unsettled, this analysis says so in its own words, and this measurement
does not settle it either — it is a step-level call invisible to any config, and `growth-shortcut`'s
steps do not exist.

**What H4b-1 changed for these three beyond the refusal.** `statistics.resample.stratify_by` is now
honoured on a contrast's draw, not only per condition — all three declare
`stratify_by: [consensus_label, count_stratum]`, and before this slice that declaration was silently
dropped on every delta. Their weighted contrasts record `weighted_by`, an `n_paired_effective` from
Kish over the paired intersection, a weighted `cohens_d`, and a corrected bound built from the same
weighted evidence as the raw one.

**One declaration all three carry is still not honoured**: a `report_by` level's recorded-column
interval stays `t_over_units` under a declared `resample`, which `docs/superpowers/spec-defects.md`
records with a named owner. So "every field they declare is honoured" — the second clause of the
no-remaining-core-side-blocker standard — is true of their `data.units` and `statistics.resample`
blocks and not of their `statistics.report_by`.

| Config | `validate` reports on the transplanted `data`/`statistics` blocks | Would execute? |
|---|---|---|
| E1 | *(none)* | **Yes** — no remaining core-side blocker |
| E2 | *(none)* | **Yes** — no remaining core-side blocker |
| E3 | *(none)* | No — blocked on `io.reuse_from` (invisible to `validate`; a step-level call) |
| E4 | *(none)* | No — blocked on `io.reuse_from` |
| E5 | *(none)* | **Yes** — no remaining core-side blocker |
| E6 | *(none)* | No — blocked on `io.reuse_from` |
| C1 | *(none)* | No — blocked on `io.reuse_from` |
| C2 | *(none)* | No — blocked on `io.reuse_from` |
| C3 | *(none)* | No — blocked on `io.reuse_from` |

<record the warnings every config reports, as the previous entries do, and say why each is an artifact
of the synthetic roster rather than of a real one>

**The mutation this table rests on, re-run rather than carried.** <record the probe above>

Full local `pytest`/`ruff`/`mypy` gates at this commit: <counts>, ruff and mypy both clean.
```

      **`<date>`, `<sha>` and every angle-bracketed slot is filled from the actual measurement.** Do
      not commit an unfilled slot; an undated build claim reads as a spec claim a month later, which is
      the failure this whole section exists to prevent.

- [ ] **Step 3: Update the three prose citations.** Each says the combination is refused. Read each
      before editing, and prefer deletion:

      | Where | What it says now | What it becomes |
      |---|---|---|
      | § Three repositories' table row about a dirty `src/**` | cites § Executability for `draft` not dispatching — **untouched**, it is about a different claim | — |
      | § Shortcut: three runs' paragraph beginning *"That is the declaration read on its own"* | the whole paragraph is the refusal and its remedies | Replaced by what core now computes for these three, with the pointer to the new dated subsection kept |
      | § What core refuses' class-ratio row | *"`weight_by` beside any published comparison is refused as `E-DATA-WEIGHT-CONTRAST`"* | Delete that clause; the row's own point — a ratio change is a different roster — stands without it, and `study` still does not dispatch |

      Then sweep the file for the code, over the **file list**:
      `grep -n "E-DATA-WEIGHT-CONTRAST" docs/feasibility-llm-growth-studies.md` → the only hits left
      must be inside earlier dated subsections, which are never retro-edited, and the new entry's own
      sentence saying it is retired. **Can-fail control:** `grep -c "E-DATA-CLUSTER-CONTRAST"
      docs/feasibility-llm-growth-studies.md`.

- [ ] **Step 4: Run everything.** `uv run pytest` → the count task 13 established. Then the other
      three commands. Then the **mechanical** pass over this file in full — it is exempt from the
      cross-document pass and subject to the mechanical one entirely: `×` not `x`, hyphens not en
      dashes in anchors, every table row matching its header, every `#anchor` resolving.

- [ ] **Step 5: Mutate.** There is no code. The mutation is on the measurement: change one config's
      recorded finding list in the new table to `*(none)*` where the probe reported something, and
      confirm the probe re-run contradicts it. **A table nobody can re-derive is decoration**, and the
      previous two entries each carry their own re-run for exactly this reason.

      **No mutation reaches** this file through the test suite.

- [ ] **Step 6: Commit.** `docs: H4b-1's dated count — three to six with no core-side blocker, three executable`

---

## Self-review

Run before handing the plan on. Every finding below was fixed inline rather than left as a note.

**Spec coverage — one task per decision and per spec decomposition item.**

| Spec item | Task |
|---|---|
| Decomposition 1 — settle and file the derived/column split; narrow the refusal's claim | 1 |
| Decomposition 2 / **Decision 3** — mint the `method` vocabulary | 2 |
| Decomposition 3 — design and document the contrast record shape | 3 |
| Decomposition 4 / **Decision 4** — the corrected bound against the exactly-one invariant | 4 (field), 9 (read) |
| Decomposition 5 / **Decision 5** — `resample.stratify_by` on a contrast | 5 |
| Decomposition 6 — thread `weights` into the three functions | 6 |
| Decomposition 7 / **Decision 2** — the weighted closure in the paired percentile path | 7 |
| Decomposition 8 — `weighted_by` on the contrast entry | 8 |
| Decomposition 9 — the corrected path | 9 |
| Decomposition 10 — weighted `paired_t_over_units`, the general case | 9 (built), 10 (wired) |
| Decomposition 11 — the § Validation row and the two siblings | 11 (siblings), 13 (§ Validation row) |
| Decomposition 12 — the three C configs end to end | 12 (direct), 13 (through `run`) |
| Decomposition 13 — retire `E-DATA-WEIGHT-CONTRAST` | 13 |
| Decomposition 14 — the owned prose sweep | 14 |
| Decomposition 15 / **Decision 6** — the dated count | 15 |
| **Decision 1** — two slices, seamed at weights/clusters | The slice's own scope; H4b-2 named as owner in tasks 5 and 14 |

**Scoping items the spec's 15 do not name, and where each landed.** The scoping's task 9 (Kish over
the paired intersection) and task 10 (a weighted `cohens_dz`) are both absorbed into **task 8**, which
is the record-under-a-weight task; leaving either out would publish a weighted delta beside an
unweighted effect size or an `n_paired` with no effective size. Both are named in task 8's brief as
absorbed rather than added. The scoping's tasks 19–22 (the regression pin, the three filed disclosure
gaps, `report_by` under a weight, the remaining filings) are the **residue group**, which the spec
assigns outside H4b-1's fifteen; tasks 14 and 15 discharge the parts that would otherwise re-owner to
nobody, and the rest are re-ownered to H4b-2 by name in task 14.

**Placeholder scan.** No `TODO` and no unnamed stand-in anywhere. Three code blocks carry an explicit
`... (unchanged)` elision — `Member.__post_init__`'s existing docstring paragraphs, `_column_mean`'s
existing comment block, and `_comparison_step_blocks`' unchanged `col_keys`/`diffs` lines — and each
one names exactly which existing text it stands for and is an **edit instruction against code the
implementer is told to read first**, not a gap to invent. Every line an implementer must *write* is
written out. The angle-bracketed slots
in task 15's subsection template are the one exception and are deliberate: they are a **measurement**
that does not exist until the task runs, and the step says explicitly that an unfilled slot must not be
committed. Task 13's end-to-end test carries real code against `run_a_project`'s real signature,
`_METHOD_VARYING_STEP` and `_first_contrast`, all read from `tests/test_cli.py`.

**Type consistency.** `weights` is `dict[str, Any] | None` at `cli`'s three signatures, matching
`command_run`'s local, whose values come from `Unit.attributes` and are `str` for a table-sourced
roster — which is why every `stats` function annotates weights `Sequence[Any]` and gates through
`checked_weights`/`usable_weight`, the single authority `validate` approved the config against. A
`float` annotation anywhere in this slice would be a call site lying to the type checker.
`Member.weights` is `tuple[Any, ...] | None` for the same reason and because `Member`'s other evidence
fields are tuples so a member cannot be mutated into the record. `strata` is `dict[str, str] | None`,
matching `cli.resample_strata` and `stats.percentile_of_derived`'s existing parameter.
`n_paired_effective` is a `float` — Kish's size is fractional for any uneven weighting, which is why
`kish_effective_n` returns `float` and why the record cannot type it `int`.

**One place the plan corrects itself rather than a task.** Task 1's step 1 prescribes a test, step 2
shows it is **blind against the actual emit message**, and step 2 replaces it with a discriminating
pair. That is left visible on purpose: the false assumption was the plan author's, reading the emit
falsified it, and a plan that silently showed only the fixed version would teach nothing about the
check it nearly shipped.
