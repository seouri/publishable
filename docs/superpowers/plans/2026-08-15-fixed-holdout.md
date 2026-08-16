# H3d — a fixed holdout split — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `data.units.holdout` partitions the roster once, a step sees the test units as `io.units` and the train units as `io.units.train`, every denominator that should narrow does, and the realized split lands in `allocation.json` — retiring `E-DATA-HOLDOUT-UNSUPPORTED`, and refusing the roster-wide evaluation split beside a cell structure that `fold` performs wrongly today.

**Architecture:** `validate` gains `_check_holdout`, which closes the block's key set in `envelope.py` and refuses a bad `method`, a `frac` outside (0, 1), a missing `from`, a field meaning nothing under the declared method, a malformed seed pin, an unknown or cluster-splitting `stratify_by`, `holdout` beside a `fold` level, a `by_attribute` column that is not exactly `{train, test}`, and a `random` split that apportions the test side zero units — all of it landing while `E-DATA-HOLDOUT-UNSUPPORTED` is still alive. A shared check site refuses **either** evaluation split beside `allocation: between` / a non-empty `sweep.groups` (`E-DATA-HOLDOUT-CELLS`, `E-REPL-FOLD-CELLS`), which is H3c-3's own 3-task refusal merged into this slice. `units.holdout_for` is the single producer of a `HoldoutPlan`, in two constructions — `_apportion` + one shuffle + consecutive slices when unclustered, `_assign_whole_clusters_by_ratio` at `[1-frac, frac]` when clustered — with `_stratum_groups` wrapped around either, and `units.holdout_seed_for` as the single producer of its seed. `cli.command_run` realizes that plan once, hands it to `runner.execute_plan` as `holdout_train=` beside a test-narrowed `units=`, threads the test-narrowed roster into the six denominator sites, and hands the same object to `build_allocation_document` for its fourth key.

**Spec:** docs/superpowers/specs/2026-08-15-fixed-holdout-design.md

**Task count: 20, not the spec's 19.** One amendment, made by the dispatcher: the spec's task 19 held two unrelated halves. Its **regression pin moves to task 1** — a no-holdout run must be byte-identical to today, and once the runner narrowing lands at task 14 there is nothing left to compare against. H4a's plan made this exact mistake; its task-1 pin then caught real bugs at its tasks 13 and 14 that nothing else would have. The spec's tasks 1–18 shift to 2–19, and the **reader-facing** half of the old 19 — the feasibility re-count and `experimental-designs.md` — becomes task 20, where it belongs.

**Sequencing, and a consequence that shapes five briefs.** Tasks 2–9 refuse and declare with `E-DATA-HOLDOUT-UNSUPPORTED` alive throughout; 10–17 draw, narrow and record; 18 retires the refusal; 19–20 sweep and pin. **No config validates while the wholesale refusal stands**, so tasks 13–17 have no end-to-end path at all: each tests its seam by direct call, and **task 18 carries five enumerated end-to-end pins**, one per wiring task. That is what makes task 18's size honest rather than discovered.

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced because an implementer sees only its own task brief.

**Commands.** Tests `uv run pytest`. Lint `uv run ruff check .`. Format `uv run ruff format --check .`. Types `uv run mypy`. All four must pass before a commit.

**Baseline.** `uv run pytest -q` at `78bb794` is **1801 passed, 2 xfailed**, ~96 s. A task that leaves the count below its own additions has broken something.

**Identifiers this slice mints.** Every one is new; `grep -rn` for each over `src/` and `docs/` returns nothing at `78bb794`.

| Code | Fault | Minted in task |
|---|---|---|
| `E-DATA-HOLDOUT-METHOD` | `holdout.method` absent, non-string, or outside `("random", "by_attribute")` | 5 |
| `E-DATA-HOLDOUT-FRAC` | Under `random`: `frac` absent, not a real number, or outside the open interval (0, 1) | 5 |
| `E-DATA-HOLDOUT-FROM` | Under `by_attribute`: `from` absent, not a string, or empty | 5 |
| `E-DATA-HOLDOUT-NO-DRAW` | A field meaning nothing under the declared method — `frac` under `by_attribute`, `from` under `random` | 5 |
| `E-DATA-HOLDOUT-SEED` | `seed` present and neither `auto` nor a plain `int` | 5 |
| `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` | `holdout.stratify_by` names something `data.units.attributes` does not declare, names `data.units.measurements.by`, or is not the name of an attribute at all | 6 |
| `E-DATA-HOLDOUT-FOLD` | `data.units.holdout` and a `{kind: fold}` repeat level are both declared | 6 |
| `E-DATA-HOLDOUT-VALUES` | Under `by_attribute`: the named column does not resolve to exactly `train` and `test` | 7 |
| `E-DATA-HOLDOUT-STRATIFY-VARIES` | `holdout.stratify_by` names an attribute that varies within a `data.units.cluster_by` cluster | 7 |
| `E-DATA-HOLDOUT-EMPTY` | Under `random`, unstratified and unclustered: `frac` apportions the test side zero units | 7 |
| `E-DATA-HOLDOUT-CELLS` | `data.units.holdout` beside `allocation: between` or a non-empty `sweep.groups` | 8 |
| `E-REPL-FOLD-CELLS` | A `{kind: fold}` repeat level beside `allocation: between` or a non-empty `sweep.groups` | 8 |
| `E-DATA-HOLDOUT-VARIES` | Under `data.units.measurements`, the column `holdout.from` names is not constant across the rows collapsing into one unit | 9 |

**Retired by this slice:** `E-DATA-HOLDOUT-UNSUPPORTED`, at task 18 and not before. `E-DATA-RESOLVER-UNSUPPORTED` and `E-STATS-NULLTEST-UNSUPPORTED` stay.

**Exact values used across this slice.**

- `holdout.method`'s enum is exactly `("random", "by_attribute")` — `reference.md` § A fixed holdout split's own inline comment.
- `by_attribute`'s two column values are exactly `train` and `test`, fixed literals. Settled in task 2; every later task reads them as literals, never as "the two values sorted".
- `frac` is the **test** fraction, so the apportionment weights are `[1 - frac, frac]` in that order — train first, test second.
- The holdout seed derivation is `sha256(f"{digest}|holdout|{units_hash(roster)}")[:4]` read big-endian, matching `units.assign_seed_for`'s construction with `assign|{axis}` replaced by `holdout`. **Not** `units._seed_from`'s `f"{digest}|folds"`.
- A `by_attribute` holdout records **no** seed (`HoldoutPlan.seed is None`) and **no** strata, exactly as `ArmPlan` does for `by_attribute`: recording a seed would be a false record of a draw that never happened.

**Boundaries this slice does not cross.**

- **Folds or holdouts drawn inside cells.** Task 8 refuses the combination and names **H3c-3** as the owner of that refusal's retirement. No task here draws within a cell.
- **`io.reuse_from`.** Unbuilt, and out of scope.
- **`E-DATA-RESOLVER-UNSUPPORTED`.** H7b's.
- **A `holdout_hash`.** Ruled out by `artifacts.allocation_hash`'s own docstring. `allocation_hash` canonicalizes whatever document it is handed and needs no change.
- **`sweep.yaml`.** `reference.md` § `sweep.yaml` gives `partitions` to a **`fold`** level; § A fixed holdout split sends a holdout's realized membership to `allocation.json` and nowhere else. A holdout writes no `sweep.yaml` key. Do not re-derive this.
- **`limits.min_units_per_cell`.** Specified, unbuilt, owned by an open `spec-defects.md` entry. A thin test partition is refused outright by task 7 instead.
- **`resume`.** No reader exists; build none.
- **`partition_units`.** Untouched, at all.
- **`technical_n` under a holdout.** A whole-roster `{min, max, median}` sitting beside a test-partition `n` is a real honesty gap. It is **filed as a `spec-defects.md` entry in task 2 and not fixed here** — it needs `data.units.measurements` *and* `holdout` together, which no feasibility config declares. Do not "complete" task 15 by adding it.

**Test-fixture facts that bite. Read before writing any `validate` test.**

- **`tests/test_validate.py`'s `base_config` has no `data.units` key at all** — `data` holds only `input_dir`, `output_dir`, `input_manifest_policy`. `write_config`'s dotted overrides walk existing nodes and **do not create intermediates**, so `write_config({"data.units.holdout": {...}})` raises `KeyError`. The canonical form, used at 103 sites in that file already, overrides the **whole block**:

```python
write_config({"data.units": {"from": "index.csv", "key": "patient_id",
                             "holdout": {"method": "random", "frac": 0.2}}})
```

- `write_config` writes one row of `index.csv` (`patient_id\np1\n`) by default. A test needing a real roster writes its own first: `(tmp_path / "input" / "index.csv").write_text(...)`.
- `codes(path)` returns the **set** of every finding's code; `_error_codes(path)` returns the errors only. Both are already defined in `tests/test_validate.py`.
- `tests/test_cli.py`'s `run_a_project` takes `units_overrides`, which **merges into `data.units`** (`doc["data"]["units"].update(...)`), plus `units`, `roster_csv`, `unit_attributes`, `_starter_step`, `extra_step_source` and `expect_exit`.

**The alongside-not-instead rule, and it is not optional.** Every check tasks 5–9 add is exercised against configs that *also* earn `E-DATA-HOLDOUT-UNSUPPORTED`, and **task 18 retires that code**. Each such test must assert **membership on its own line**, both the new finding *and* the surviving wholesale refusal:

```python
found = codes(write_config({...}))
assert "E-DATA-HOLDOUT-FRAC" in found
# Alongside, never instead of: the wholesale refusal is still live at this
# commit, and task 18 retires it. Asserting membership on its own line makes
# that retirement a one-line deletion rather than a rewrite of this test.
assert "E-DATA-HOLDOUT-UNSUPPORTED" in found
```

**`assert codes(...) == {...}` and `assert set(...) == {...}` are banned in tasks 5–9 for any config declaring a holdout.** An exact-set assertion turns task 18 into a rewrite of the whole of Part A, which is the cost the scoping named and this rule exists to avoid.

**Mutation discipline, every task.** Apply the named mutation to the file it names. Run the named test. Confirm it **FAILS**. Then `find . -name __pycache__ -type d -exec rm -rf {} +`. Then revert **by editing the file back in place** — never `git checkout -- <file>`, which destroys uncommitted work and has been mistaken for a revert twice in this repo. Confirm the test **PASSES** again. Verify the revert by behaviour (the test passes), never by `git status`.

**Test-design rules this repo enforces.** Sixteen checks across the two H3c slices could not fail, and roughly a dozen more in H7a. Before believing any test here:

- A control that asserts only an absence passes identically if nothing ran. Every such assertion needs a positive companion **produced by the code under test**, in the same test.
- Vary the roster's **content** when the property is about roster content. Nineteen adversary configs over one roster made every refusal roster-incidental in an earlier slice.
- Size a fixture so each candidate wrong answer produces a **different** observable. Two elements only ever distinguish two answers.
- **A mutation is a claim too.** Before writing "this mutation must fail test X", check the two branches can actually produce different results.
- **Derive expected values from the fixture**, never from an assumption about it. Where a task says "pin the realized membership", it means: run the implementation, read the actual keys, and write those literals down.
- Never filter the output of a grep whose job is to find a string — filter the file list.

**No present-tense claim about what a later task builds.** Fourteen of H4a's nineteen briefs carried this defect, most of them in a docstring or comment the implementer copied verbatim. If a comment describes behaviour a later task adds, write it as what is true **at that commit** — "not realized at this commit", never "is never realized".

**Documentation rules.** `×` not `x` for multiplication, including inside fenced blocks. Hyphen, never an en dash, in anything that becomes an anchor. Cite by section (`reference.md` § "A fixed holdout split"), never by line number. After any `*.md` edit run the mechanical pass: every relative link and `#anchor` resolves, no two headings in a file share an anchor, every table row matches its header's column count and none is empty, no trailing whitespace, tab, or invisible unicode — skipping fenced code blocks in all of them. Any inline `# a | b | c` enum comment must list every value its table defines. The cross-document pass governs `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md` and `docs/reference.md` **only** — never the development record under `docs/superpowers/`, where a correction is appended rather than retro-edited. `spec-defects.md` is the one exception: a closed gap is struck there rather than left to mislead.

---

## Task 1: The regression pin — a run with no holdout, denominators and artifacts

**Files:** Modify (append) `tests/test_cli.py`. No `src/` change.

**Interfaces:**
- Consumes: `run_a_project(tmp_path, *, capsys=None, units=10, units_overrides=None, _starter_step=None, expect_exit=EXIT_OK, **overrides)` from `tests/test_cli.py`; `EXIT_OK` and `EXIT_PARTIAL` from `publishable.diagnostics`, already imported at the top of that file.
- Produces: `test_a_run_without_a_holdout_pins_its_denominators_and_artifacts` and `test_io_units_train_raises_without_a_fold_or_holdout` — the only baseline tasks 14–18 can be compared against.

**Why this is task 1 and not task 19.** The spec put it last. It moves here because a no-holdout run must stay byte-identical to today, and **once the runner narrowing lands at task 14 there is nothing left to compare against**: the very code that would break the baseline is the code that would have to be written to build the baseline. H4a's plan made this mistake, the dispatcher caught it before dispatch, and H4a's task-1 pin then caught real bugs at its tasks 13 and 14 that nothing else in the suite would have.

**What it pins, and why each line is here.** The four things tasks 14–17 are most likely to move for a config that declares no holdout at all: `n.resolved` in `executions.jsonl` and in `run.yaml`'s aggregated block (task 15's denominators), `provenance.units.n` and `units_hash` (which must stay whole-roster and are the one pair task 15 must **not** touch), `allocation.json`'s absence together with `provenance.allocation`/`allocation_hash` being `None` (task 17's fourth key and its "both absent" gate), and `io.units.train` raising `E-STEP-UNITS-UNAVAILABLE` (task 14's narrowing, which must not start handing out a train list to a run that declared no partition).

**The generated config writes `holdout: null`**, which `materialize.py` materializes today — so this pin is over the shape a generated project actually produces, and the test asserts that key is `None` rather than absent, because `_check_unimplemented`'s `if units.get(field)` is false for both and they are different documents.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
_TRAIN_TOUCHING_STEP = '''\
# src/{pkg}/steps/step01_touch_train.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        # Reaches for the training partition with no `fold` repeat and no
        # `data.units.holdout` declared. At this commit that raises
        # `E-STEP-UNITS-UNAVAILABLE` from `UnitList.train`, which is the
        # property being pinned: an empty list here would let a fit run on
        # nothing and write a plausible model.
        train = io.units.train
        return {{"n_train": len(train)}}
'''


def test_a_run_without_a_holdout_pins_its_denominators_and_artifacts(tmp_path, capsys):
    """The whole-roster shape a run with no `data.units.holdout` produces.

    Pinned FIRST, before any narrowing exists: tasks 14 and 15 narrow
    `io.units` and four denominators onto a holdout's test partition, and
    after that there is no un-narrowed build left to compare against. Every
    number here is over the full 10-unit roster, and every one of them must
    still be 10 when this slice is done.
    """
    doc = run_a_project(tmp_path, capsys=capsys, units=10)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())

    # `materialize.py` writes the key as an explicit `null`. Asserted rather
    # than assumed: an absent key and an explicit `null` are different
    # documents that must produce one shape, and this is the one a generated
    # project actually has.
    assert run["config"]["data"]["units"]["holdout"] is None

    # The ledger's own denominator, per execution. `attrition` hands out the
    # whole roster today, so `resolved` is the roster size.
    ledger = [
        json.loads(line)
        for line in (doc["run_dir"] / "executions.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert ledger, "no executions were recorded — the pin would be vacuous"
    for record in ledger:
        assert record["n"]["resolved"] == 10, record

    # The same figure as `run.yaml` arranges it, which is the surface a reader
    # actually cites.
    aggregated = run["results"]["conditions"][0]["aggregated"]
    assert aggregated, "nothing aggregated — the pin below would be vacuous"
    for block in aggregated.values():
        for metric in block.values():
            if isinstance(metric, dict) and isinstance(metric.get("n"), dict):
                assert metric["n"]["resolved"] == 10, metric

    # The roster's IDENTITY, which is deliberately NOT a metric's denominator
    # and which task 15 must leave whole. Pinned beside the denominators above
    # precisely so a change that narrows both is distinguishable from one that
    # narrows only what it should.
    provenance = run["provenance"]
    assert provenance["units"]["n"] == 10
    assert provenance["units"]["key"] == "patient_id"
    assert provenance["units_hash"].startswith("sha256:")

    # No arm assignment and no holdout, so no `allocation.json` and no hash —
    # the "both absent" gate task 17 widens.
    assert not (doc["run_dir"] / "allocation.json").exists()
    assert provenance["allocation"] is None
    assert provenance["allocation_hash"] is None


def test_io_units_train_raises_without_a_fold_or_holdout(tmp_path, capsys):
    """`io.units.train` with neither partition declared raises rather than
    handing back an empty list — `reference.md` § Steps and artifacts. Pinned
    here because task 14 teaches `execute_plan` to populate `.train` from a
    holdout plan, and a narrowing written one branch too wide would start
    handing a train list to a run that declared no partition at all.

    The step's failure is CONTAINED: the plan runs to its end and `run_status`
    turns it into `partial`, so the run directory exists and the ledger can be
    read for the code."""
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=10,
        _starter_step=_TRAIN_TOUCHING_STEP,
        expect_exit=EXIT_PARTIAL,
    )
    ledger = [
        json.loads(line)
        for line in (doc["run_dir"] / "executions.jsonl").read_text().splitlines()
        if line.strip()
    ]
    failed = [r for r in ledger if r["status"] == "failed"]
    # A positive companion for the absence below: something must actually have
    # run and failed, or the code assertion would pass over an empty list.
    assert failed, "no execution failed — the step never ran"
    assert all("E-STEP-UNITS-UNAVAILABLE" in (r["error"] or "") for r in failed)
    assert all(r["n"]["resolved"] == 10 for r in ledger)
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k "without_a_holdout or units_train_raises" -x`. **This is a characterization pin, so both tests must PASS immediately.** If either fails, the assertion is wrong and not the code: fix the assertion to what the run actually produces, and record the difference in the commit message. Two things to check before changing anything — that `json` and `yaml` are already imported at the top of `tests/test_cli.py` (they are), and that `_starter_step` exists as a `run_a_project` parameter (it does, added by H4a task 1; its source goes through `STARTER_STEP.format(pkg=pkg)`, which is why every literal `{` in `_TRAIN_TOUCHING_STEP` is doubled).

- [ ] **Step 3: Implement** — nothing. The pin is the deliverable. No `src/` file is touched by this task.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_cli.py -k "without_a_holdout or units_train_raises"`, then the whole suite: `uv run pytest`.

- [ ] **Step 5: Mutate** — two mutations, because each pins a different half.

  (a) In `src/publishable/runner.py`'s `execute_plan`, change the no-fold branch

```python
        if fold_members is None or scoped_units is None:
            step_units = scoped_units
```

  to

```python
        if fold_members is None or scoped_units is None:
            step_units = UnitList(list(scoped_units or []), train=scoped_units)
```

  Run `uv run pytest tests/test_cli.py -k units_train_raises`. It must **FAIL**: no execution fails any more, so `assert failed` trips. Delete `__pycache__`. Edit the two lines back in place. Re-run; it passes.

  (b) In `src/publishable/runner.py`'s `attrition`, change `handed = keys` (the `if fold_members is None:` branch) to `handed = set(sorted(keys)[:3])`. Run `uv run pytest tests/test_cli.py -k without_a_holdout`. It must **FAIL** on `record["n"]["resolved"] == 10`. Delete `__pycache__`. Edit it back in place. Re-run; it passes.

- [ ] **Step 6: Commit** — `test: pin the no-holdout run's denominators, artifacts and train raise`.

---

## Task 2: The documents — three under-specifications, thirteen codes, two rows, and the inference-base ruling

**Files:** Modify `docs/reference.md`, `docs/superpowers/spec-defects.md`. No code, no test file.

**Interfaces:**
- Consumes: nothing.
- Produces: the normative statements every later task enforces — the `train`/`test` literals (tasks 7, 10), the `allocation.json` home for a holdout's `seed`/`strata` (task 17), the `holdout.seed` row in § What `auto` derives from with `E-DATA-HOLDOUT-SEED` (task 5), all twelve § Errors rows (tasks 5–8), the two new § Validation rows (tasks 7, 8), the `resample` × `holdout` sentence (task 16), and decision 5's inference-base ruling (tasks 15, 17).

**Why the documents are first.** `CLAUDE.md`: the four documents are normative and they lead; where the code cannot follow them the document changes first. Five of the things below are things no document currently says, so a later task would otherwise be inventing a rule and implementing it in the same commit.

**Decision 5, settled here so no later task re-derives it.** `CLAUDE.md`'s invariant is that **units are the inference base and `n` counts units**. Under a holdout, the units that produce a result are the **test** partition, so:

- `n.resolved`/`n.completed`/`n.ineligible`/`n.failed` count **test** units. A 20 % holdout over 240 reports `resolved: 48`, which § A fixed holdout split already says.
- Every interval is over that same table, so nothing about the correction family changes: a holdout narrows the denominator and adds no member.
- `provenance.units.n` and `provenance.units_hash` stay **whole-roster**. They are the roster's *identity*, not a metric's denominator — that is what makes `240` there and `48` in a metric's `n` two true numbers rather than a contradiction.
- The training units are **not** `ineligible` and **not** `failed`. They were never handed out, so they appear in no count at all.

- [ ] **Step 1: Write the failing test** — the test here is a set of throwaway greps, run in Step 2 and not kept. Filter the **file list**, never the output:

```bash
cd /Users/joon/src/tries/publishable
# Every code this slice mints must exist in reference.md § Errors after Step 3.
for code in E-DATA-HOLDOUT-METHOD E-DATA-HOLDOUT-FRAC E-DATA-HOLDOUT-FROM \
            E-DATA-HOLDOUT-NO-DRAW E-DATA-HOLDOUT-SEED \
            E-DATA-HOLDOUT-STRATIFY-UNKNOWN E-DATA-HOLDOUT-FOLD \
            E-DATA-HOLDOUT-VALUES E-DATA-HOLDOUT-STRATIFY-VARIES \
            E-DATA-HOLDOUT-EMPTY E-DATA-HOLDOUT-CELLS E-REPL-FOLD-CELLS \
            E-DATA-HOLDOUT-VARIES; do
  printf '%s %s\n' "$code" "$(grep -c -- "$code" docs/reference.md)"
done
# The three under-specifications.
grep -n 'holdout.*train.*test' docs/reference.md | head
grep -n '"holdout":' docs/reference.md
grep -n "holdout.seed" docs/reference.md
```

- [ ] **Step 2: Run it, confirm it fails** — every code prints `0`; `grep -n '"holdout":'` returns only the one `allocation.json` example line with no `seed` in it; `holdout.seed` appears only in § What `auto` derives from's *prose*, with no row in the table beneath it and no refusal code. That is the confirmation.

- [ ] **Step 3: Implement** — six edits to `docs/reference.md` and one to `docs/superpowers/spec-defects.md`.

  **(a) § A fixed holdout split — settle the `by_attribute` literals, and mark the cells prose honestly.** Replace the sentence beginning "`by_attribute` covers a split that already exists" with:

```markdown
`by_attribute` covers a split that already exists, which benchmark datasets usually ship: name the column (`from: split`) and core partitions rather than draws. **The column's values must be exactly `train` and `test`** — two fixed literals, not "whichever two values are there". A holdout declares no `levels` for core to read an order out of, and inferring one from the data would make which side is evaluated depend on a lexical accident of the input; a column holding `{A, B}`, or `{train, test, dev}`, is refused as `E-DATA-HOLDOUT-VALUES`. Rename the column's values, or map them in the step that produces the roster.
```

  Then replace the **fourth** interaction bullet (the one beginning "**Under `allocation: between`, the split happens within each cell**") with:

```markdown
- **A roster-wide split beside a cell structure is refused, not drawn.** Under `allocation: between`, or under a non-empty `sweep.groups`, a single split of the whole roster would leave cells with unequal test sizes and, at worst, a cell with no test units at all — so core refuses the combination outright (`E-DATA-HOLDOUT-CELLS`), rather than recording a partition whose imbalance a reader would have to cross against the arms list by hand to see. A `fold` repeat beside the same cell structure is refused for the identical reason and under its own code, `E-REPL-FOLD-CELLS`. Drawing *within* each cell is the design that lifts both refusals, and it is not built.
```

  Then append one paragraph to that section, immediately before "The realized membership is written to `allocation.json`":

```markdown
**A holdout narrows a denominator and adds nothing to the correction family.** `statistics.resample` draws over the per-unit table, which under a holdout holds only the units that recorded — the test partition — so a percentile interval rests on that many units, and on that many [clusters](#clustered-units) when `cluster_by` is declared. `limits.min_clusters` is checked against the **test** partition's cluster count for that reason: a roster of 50 clusters under a `frac: 0.2` holdout resamples roughly 10, and warning against the wider number would be warning against a denominator no interval used. The units held back for training produced no result, so they are counted nowhere: not `completed`, not `ineligible`, not `failed`. `provenance.units.n` and `units_hash` stay whole-roster regardless — they are the roster's identity, not a metric's denominator, which is why `240` there and `48` in a metric's `n` are two true numbers rather than a contradiction.
```

  **(b) § Validation — two new rows.** Insert them immediately after the existing *Holdout strata survive clustering* row:

```markdown
| One split, not one cell each | `data.units.holdout` or a `{kind: fold}` level is declared beside `allocation: between` or a non-empty `sweep.groups` — one roster-wide evaluation split would give the cells unequal test sizes, and a cell none at all once the split is fine enough |
| Holdout leaves a test partition | `holdout.method: random` with `frac: 0.01` over 40 units apportions the test side zero units, so every metric would be over nothing |
```

  **(c) § Errors `validate` reports — thirteen rows.** Add them in the `data.units` block, after the existing `E-DATA-ASSIGN-*` rows, each with the code in the right-hand column, in the order the Global Constraints table lists them. Write each row's left-hand cell as the fault, with the sentence of reasoning the surrounding rows carry — the thirteenth (`E-DATA-HOLDOUT-VARIES`) belongs beside its `E-DATA-CLUSTER-VARIES` / `E-DATA-WEIGHT-VARIES` / `E-DATA-ASSIGN-VARIES` siblings rather than with the rest, since it is raised by `resolve_units` at run time and not by `validate` — check which table those three live in and put it there. For example:

```markdown
| `data.units.holdout.method` is absent, is not a string, or is not one of `random`, `by_attribute`. An allowlist, not a denylist: a method named here and realized nowhere would validate clean and then partition on something core never drew | `E-DATA-HOLDOUT-METHOD` |
| Under `method: random`, `data.units.holdout.frac` is absent, is not a real number, or is outside the open interval (0, 1). Both endpoints are excluded: `0` holds nothing out and `1` holds everything out, and each leaves one side of the split empty | `E-DATA-HOLDOUT-FRAC` |
| Under `method: by_attribute`, `data.units.holdout.from` is absent, is not a string, or is empty — there is no column to read the partition out of, and unlike [`assign.<axis>.from`](#allocation-within-subjects-or-between-subjects) a holdout has no axis name to default to | `E-DATA-HOLDOUT-FROM` |
| A `data.units.holdout` field that means nothing under the declared method: `frac` under `by_attribute`, which reads a partition rather than drawing one, or `from` under `random`, which draws one rather than reading one. The same fault [`E-DATA-ASSIGN-NO-DRAW`](#errors-validate-reports) names one declaration over | `E-DATA-HOLDOUT-NO-DRAW` |
| `data.units.holdout.seed` is present and is neither `auto` nor a plain integer — a quoted `"1234"`, a `1.5`, or a `true` is a pin nothing can honour, and honouring it as far as the derivation would record a derived seed under a key the config wrote deliberately | `E-DATA-HOLDOUT-SEED` |
| `data.units.holdout.stratify_by` names a value `data.units.attributes` does not declare, names the column `data.units.measurements.by` names — consumed when a unit's rows collapse, so no resolved unit carries it — or is not the name of an attribute at all: a non-string, an empty string, or an empty list. Checked from the declaration alone, so it reports whether or not a roster resolved | `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` |
| `data.units.holdout` and a `{kind: fold}` repeat level are both declared. Two answers to one question — how the data is divided for evaluation — leaving "which units is this metric over?" with none | `E-DATA-HOLDOUT-FOLD` |
| Under `method: by_attribute`, the column `data.units.holdout.from` names does not resolve to exactly `train` and `test`: a unit carries some other value, carries none, or one of the two literals names no unit at all. Read through `units.arms_of`, the single authority for a column-read partition, so the same set equality an arm assignment requires is the one a holdout requires | `E-DATA-HOLDOUT-VALUES` |
| `data.units.holdout.stratify_by` names an attribute that varies within a `data.units.cluster_by` cluster, checked through `units.stratum_varies_within_cluster` — the single authority *Fold strata survive clustering* and *Resample strata survive clustering* also read. Whole clusters go to one side of a holdout, so a cluster carrying two stratum values can be dealt to neither | `E-DATA-HOLDOUT-STRATIFY-VARIES` |
| Under `method: random`, unstratified and unclustered, `frac` apportions the test side zero units over the resolved roster — every metric would be over nothing. Reported for the unstratified, unclustered draw only, mirroring *Every arm draws units*: a stratified or clustered split is checked where the run performs it, because a cluster is the smallest thing that can move and only the draw knows what it moved | `E-DATA-HOLDOUT-EMPTY` |
| `data.units.holdout` is declared beside `data.units.allocation: between` or a non-empty `sweep.groups`. One roster-wide split across a cell structure gives the cells unequal test sizes and, at worst, a cell with no test units — refused rather than recorded, because the imbalance is only visible to a reader who crosses `allocation.json`'s membership against the arms list by hand | `E-DATA-HOLDOUT-CELLS` |
| A `{kind: fold}` repeat level is declared beside `data.units.allocation: between` or a non-empty `sweep.groups`, refused for the identical reason and at the identical check site as `E-DATA-HOLDOUT-CELLS`. `k` is bounded by the whole roster's [fold basis](#validation), so a roster-wide partition can leave a small arm with folds holding none of its units | `E-REPL-FOLD-CELLS` |
| Under [`data.units.measurements`](#what-isnt-a-repeat), the column `data.units.holdout.from` names is not constant across the rows collapsing into one unit — the unit would be filed on whichever side the row the collapse happened to keep says, making a train/test membership an accident of row order. The fourth member of the family `E-DATA-CLUSTER-VARIES`, `E-DATA-WEIGHT-VARIES` and `E-DATA-ASSIGN-VARIES` already form, and raised where they are raised: at run time, by `resolve_units`, which is the one place holding the pre-collapse rows that prove it | `E-DATA-HOLDOUT-VARIES` |
```

  **(d) § `allocation.json` — the holdout's `seed` and `strata` home.** Replace the JSON example's `"holdout"` line with:

```json
  "holdout": {"train": ["P0002", "P0007"], "test": ["P0011", "P0019"],
              "seed": 3310985422, "strata": ["label"]},
```

  and add this paragraph immediately after the existing "**`seed` and `strata` are keyed by axis…**" paragraph:

```markdown
**A holdout carries its own `seed` and `strata`, inside its own block.** The top-level `seed` and `strata` are keyed by *axis name*, and a holdout is not an axis — hanging it off a fabricated key would invite a reader to index it as one. So the `holdout` block is self-contained: `train` and `test` always, `seed` only when the split was **drawn** (`method: random`), and `strata` only when it declared a non-empty `stratify_by`. A `by_attribute` holdout carries neither, for the reason a `by_attribute` axis is left out of both above: it reads a partition the data already holds, so a seed would record a draw that never happened and a `stratify_by` would describe how a draw was balanced when none was. There is no `holdout_hash`; `provenance.allocation_hash` covers this file whole, both partitions being of one roster drawn once.
```

  **(e) § What `auto` derives from — the missing row and the missing refusal.** Add to the four-row table:

```markdown
| `data.units.holdout.seed` | digest + the resolved roster | the roster changes, or the unit declaration does — see below |
```

  and extend the "**A seed that is *present* must be one or the other**" paragraph's last sentence to read:

```markdown
`sweep.sample.seed` is refused as `E-SWEEP-SAMPLE-INVALID`, `assign.<axis>.seed` as `E-DATA-ASSIGN-SEED`, and `holdout.seed` as `E-DATA-HOLDOUT-SEED`. A pinned `holdout.seed` is excluded from the design digest the same way a pinned `assign.<axis>.seed` is, and for the same reason: a seed that is itself inside the digest it is mixed with would make the derivation self-referential, and would move every *other* derived draw in the run.
```

  **(f) § Weighted samples — the `resample` × `holdout` sentence.** Extend the sentence beginning "`fold`, `holdout`, and `assign` all take a `stratify_by` already" with:

```markdown
A `holdout` also decides what a draw is *over*: `resample` draws from the per-unit table, which under a holdout holds the test partition alone — see [A fixed holdout split](#a-fixed-holdout-split).
```

  **(g) `docs/superpowers/spec-defects.md` — file the `technical_n` gap.** Append a new entry at the end of the open section:

```markdown
## OPEN — `technical_n` is a whole-roster figure beside a test-partition `n`

`cli._cond_beside_n` withholds `technical_n` from a condition whose roster was narrowed to
an arm, on the stated grounds that "copying a whole-roster figure onto a subset states a
spread nobody computed over that subset". A `data.units.holdout` narrows the same way and
the same withholding is not applied: `technical_n` is `{min, max, median}` over the whole
roster's measurement counts, and under a holdout it would sit beside an `n` counting the
test partition alone.

**Deliberately not closed by H3d.** It needs `data.units.measurements` *and*
`data.units.holdout` declared together, which no config in
`docs/feasibility-llm-growth-studies.md` does, and closing it inside H3d's task 15 would
add an unbudgeted behaviour change to the task the scoping already names as the one most
likely to ship wrong. The mechanism is cheap when it is wanted: `_cond_beside_n` already
takes the un-narrowed roster as its third argument and decides by identity.

**Found by:** H3d, Task 2 (documents-only). **Owner:** whichever slice next changes
`_cond_beside_n`, or H3c-3 if it retrofits the holdout to cells first — re-owner this entry
when that slice finishes rather than leaving it pointing at a closed one.
**Severity:** Minor. Both numbers are individually true and separately labelled; the fault
is that a reader must know which roster each was computed over.
```

- [ ] **Step 4: Run, confirm it passes** — re-run every grep from Step 1: each code now prints a non-zero count, the `allocation.json` example carries `seed` and `strata` inside its `holdout` block, and `holdout.seed` appears in the `auto` table. Then the **mechanical pass** over `docs/reference.md` and `docs/superpowers/spec-defects.md`: `grep -n ' $' docs/reference.md docs/superpowers/spec-defects.md` returns nothing; `grep -nP '\t' docs/reference.md` returns nothing; every new table row has the same column count as its header (`E-` rows are 2 columns, § Validation rows are 2, the `auto` table is 3); every `#anchor` added above resolves against a heading that exists (`grep -n '^#' docs/reference.md`); no heading was added, so no anchor can collide; `×` was not needed and no `x` was used for multiplication. Then the **cross-document pass**: `grep -rn "holdout" docs/design-principles.md README.md` — confirm nothing there states a rule these edits contradict, and in particular that no passage shows `holdout` as producing a derived value these edits now declare settable, or the reverse. Then `uv run pytest` — `tests/test_materialize.py` pins the generated config's comment text; these edits touch no `materialize.py` line, so it must still pass untouched.

- [ ] **Step 5: Mutate** — a documents-only task has no code mutation, so mutate the **sweep** instead, which is the thing that can silently be wrong here. Temporarily change one occurrence of `E-DATA-HOLDOUT-VALUES` in `docs/reference.md` to `E-DATA-HOLDOUT-VALUE` and re-run the Step 1 loop: it must print `E-DATA-HOLDOUT-VALUES 0`. That proves the loop can fail. Edit it back in place and re-run; it prints a non-zero count.

- [ ] **Step 6: Commit** — `docs: settle the holdout's three under-specifications, its thirteen codes, and the inference base`. Use `git add -f docs/superpowers/spec-defects.md` if `scripts/sdd-workspace` has clobbered `.superpowers/sdd/.gitignore` in the meantime.

---

## Task 3: Close `data.units.holdout` one level in

**Files:** Modify `src/publishable/envelope.py`. Modify (append) `tests/test_envelope.py`.

**Interfaces:**
- Consumes: `LEAF_TYPES: dict[str, type | tuple[type, ...]]` and `check_envelope(doc) -> list[tuple[str, str, str]]` in `src/publishable/envelope.py`.
- Produces: five new `LEAF_TYPES` entries — `data.units.holdout.method` (`str`), `.frac` (`float`), `.from` (`str`), `.stratify_by` (`(str, list)`), `.seed` — so a `methodd` inside the block is `E-CONFIG-KEY-UNKNOWN` and a wrong-typed child is `E-CONFIG-TYPE`.

**The precedent, and it is exact.** `data.units.measurements` is typed `dict` *and* closed one level in at `.by`/`.collapse`; `statistics.resample` is typed `dict` and closed at `.method`/`.n`/`.stratify_by`. `envelope.py`'s own comment argues that `resample` was closed **before** its wholesale refusal retired, deliberately — "the slice that honours a block needs the shape checked before it can read the values." A holdout's children have fixed names, so the same closure applies, and it closes the `holdout: {}` truthiness hole's sibling as a by-product: a `{methodd: random}` is reported by no check at `78bb794`.

**Two rulings this task must not get wrong.**

- **`frac` is typed `float`, and `_is_type` special-cases `bool`.** A `frac: 1` (a plain `int`) is a legal YAML spelling of a fraction the range check then refuses as outside (0, 1); typing it `(int, float)` would let `frac: 1` reach the range check rather than `E-CONFIG-TYPE`, which is the right division of labour — a `1` is a well-typed number outside the interval, not a type fault. So type it `(int, float)`, not `float`. State this in the entry's comment.
- **`seed` is typed `(str, int)`**, matching what § What `auto` derives from permits: the string `auto` or a plain integer. `bool` is excluded by `_is_type`'s special case, which is exactly why `seed: true` must reach `E-CONFIG-TYPE` rather than being read as `1`.
- **`stratify_by` is `(str, list)`**, not `list` alone — `units.stratum_names` reads a bare `stratify_by: label` as one name exactly as `[label]` is, and typing it `list` would make the envelope and the draw disagree about the same declaration. `statistics.resample.stratify_by`'s entry states this verbatim; copy the reasoning.

- [ ] **Step 1: Write the failing test** — append to `tests/test_envelope.py`:

```python
def test_a_misspelled_holdout_child_is_reported():
    """`data.units.holdout` is closed one level in, the arrangement
    `measurements` and `resample` already have: its children have fixed names,
    so a typo among them is reachable by a check rather than silently ignored.

    The positive companion is in the same test on purpose — a well-spelled
    sibling in the SAME block must produce no finding, so this cannot pass by
    reporting every key in the block."""
    findings = check_envelope(
        {"data": {"units": {"holdout": {"methodd": "random", "frac": 0.2}}}}
    )
    assert ("E-CONFIG-KEY-UNKNOWN", "data.units.holdout.methodd") in [
        (code, path) for code, path, _ in findings
    ]
    assert not [f for f in findings if f[1] == "data.units.holdout.frac"]


@pytest.mark.parametrize(
    "block,path,expect_type_error",
    [
        ({"method": ["random"]}, "data.units.holdout.method", True),
        ({"method": "random"}, "data.units.holdout.method", False),
        # A plain `int` is a legal YAML spelling of a fraction; the OPEN-interval
        # refusal is `E-DATA-HOLDOUT-FRAC`'s, not the envelope's, so `1` must be
        # well-typed here. `True` is not: `_is_type` excludes `bool` from every
        # numeric entry, since `True` is not a fraction.
        ({"frac": 0.2}, "data.units.holdout.frac", False),
        ({"frac": 1}, "data.units.holdout.frac", False),
        ({"frac": True}, "data.units.holdout.frac", True),
        ({"frac": "0.2"}, "data.units.holdout.frac", True),
        ({"from": "split"}, "data.units.holdout.from", False),
        ({"from": 3}, "data.units.holdout.from", True),
        # A bare string names one stratum exactly as a one-element list does —
        # `units.stratum_names`, the single authority the draw balances on.
        ({"stratify_by": "label"}, "data.units.holdout.stratify_by", False),
        ({"stratify_by": ["label"]}, "data.units.holdout.stratify_by", False),
        ({"stratify_by": 7}, "data.units.holdout.stratify_by", True),
        ({"seed": "auto"}, "data.units.holdout.seed", False),
        ({"seed": 1234}, "data.units.holdout.seed", False),
        ({"seed": True}, "data.units.holdout.seed", True),
        ({"seed": 1.5}, "data.units.holdout.seed", True),
    ],
)
def test_each_holdout_child_is_typed(block, path, expect_type_error):
    """Each of the five children, at its own type, with a legal value beside
    every illegal one. Both arms are asserted because a parametrization that
    only ever asserts a FAILURE proves nothing about the success path — the
    shape that left `blocked`'s stratified draw fully threaded and never
    exercised."""
    findings = check_envelope({"data": {"units": {"holdout": block}}})
    typed = [f for f in findings if f[0] == "E-CONFIG-TYPE" and f[1] == path]
    assert bool(typed) is expect_type_error, findings
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_envelope.py -k holdout -x`. Both fail: the closure test reports no `E-CONFIG-KEY-UNKNOWN` at all (the walk never descends into a known leaf), and every `expect_type_error=True` row reports nothing.

- [ ] **Step 3: Implement** — in `src/publishable/envelope.py`, replace the entry

```python
    "data.units.holdout": dict,
```

with

```python
    "data.units.holdout": dict,
    # Closed one level in, the arrangement `data.units.measurements` above and
    # `statistics.resample` below both have, and for their reason: these five
    # names are fixed, so leaving the block whole would make a `methodd` typo
    # unreachable by any check. Closed *before* the block's own wholesale
    # refusal retires, which is `resample`'s ordering rather than
    # `measurements`': the slice that honours a block needs the shape checked
    # before it can read the values.
    "data.units.holdout.method": str,
    # `(int, float)`, not `float`: a `frac: 1` is a well-typed number that
    # happens to fall outside the open interval (0, 1), which is a different
    # fault with a different code (`E-DATA-HOLDOUT-FRAC`) and a different fix.
    # `bool` is excluded by `_is_type`'s special case, since `True` is not a
    # fraction however well `bool` subclasses `int`.
    "data.units.holdout.frac": (int, float),
    "data.units.holdout.from": str,
    # `(str, list)` for `statistics.resample.stratify_by`'s reason, one
    # declaration over: `units.stratum_names` — the single authority a draw
    # balances on — reads a bare `stratify_by: label` as one name exactly as
    # `[label]` is, so typing this `list` alone would make the envelope and the
    # draw disagree about the same declaration.
    "data.units.holdout.seed": (str, int),
    "data.units.holdout.stratify_by": (str, list),
```

  Then rewrite the module docstring's two `holdout`-stays-whole claims. Replace

```python
# `holdout` stays whole for now: `E-DATA-HOLDOUT-UNSUPPORTED` still refuses the
# block, so its gap is latent, and H3d closes it.
```

with

```python
# `holdout` is closed one level in too, at its own five keys, for the reason
# `resample` is: `E-DATA-HOLDOUT-UNSUPPORTED` still refuses the block at this
# commit, and the shape is checked ahead of that refusal lifting rather than
# after it, so the slice that honours the block reads values whose shape a
# check already approved.
```

  and in the paragraph beginning "The table stopping at a key is the end of the line", replace

```python
# misspelled `resolverr` in a `data.units.from` mapping or `methodd` in
# `holdout` is reported by no check in this build. That is the documented
# cost of a whole leaf (`reference.md` § Validation names the blocks it
# applies to and the slice that closes each), not a claim that such a key
# could never be named: `holdout`'s children have fixed names. The keys that
```

with

```python
# misspelled `resolverr` in a `data.units.from` mapping is reported by no
# check in this build. That is the documented cost of a whole leaf
# (`reference.md` § Validation names the blocks it applies to and the slice
# that closes each), not a claim that such a key could never be named — a
# `methodd` in `holdout` was in exactly that position and is now reported,
# its children's names being fixed. The keys that
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_envelope.py -k holdout`, then `uv run pytest`. Then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — in `src/publishable/envelope.py`, change `"data.units.holdout.frac": (int, float),` to `"data.units.holdout.frac": (int, float, str),`. Run `uv run pytest tests/test_envelope.py -k each_holdout_child_is_typed`. The `{"frac": "0.2"}` row must **FAIL**. Delete `__pycache__`, edit the entry back in place, re-run; it passes. Then a second mutation, because the first only proves the type table is read: delete the `"data.units.holdout.method": str,` line entirely. `test_a_misspelled_holdout_child_is_reported` must **FAIL** — with no path beneath `holdout` in the table, `_known_containers` stops treating `holdout` as a container and the walk never descends. Restore the line in place and re-run.

- [ ] **Step 6: Commit** — `feat: close data.units.holdout one level in, ahead of its refusal lifting`.

---

## Task 4: `design_digest` excludes `holdout.seed`

**Files:** Modify `src/publishable/hashes.py`, `docs/superpowers/spec-defects.md`. Modify (append) `tests/test_hashes.py`.

**Interfaces:**
- Consumes: `hashes._units_excluding_assign_seed(units: Any) -> Any` and `hashes.design_digest(config: dict[str, Any]) -> str`.
- Produces: `hashes._units_excluding_drawn_seeds(units: Any) -> Any` — the same function, renamed, now dropping `holdout.seed` as well as every `assign.<axis>.seed`. `design_digest` calls it in place of the old name.

**Why this lands before any pin is reachable.** `spec-defects.md` carries this as the explicitly **open** half of a closed entry, whose owner it names as "the slice that builds `data.units.holdout`". The defect is that `design_digest` canonicalizes `data.units` wholesale, so a **pinned** `holdout.seed` would move the digest that every *other* derived draw in the run reads — the `seed` repeat stream, the sample draw, each `assign.<axis>.seed`. Pinning one seed to cite it would silently redraw everything else, which is the confounding the digest's own section exists to prevent. It must land before task 5 makes a pinned seed reachable at all.

**The rename is the point, not decoration.** A function named `_units_excluding_assign_seed` that also drops a holdout's seed is a false name of exactly the class `CLAUDE.md` records a dozen instances of. `grep -rn _units_excluding_assign_seed src/ tests/ docs/` before and after; every site moves.

- [ ] **Step 1: Write the failing test** — append to `tests/test_hashes.py`:

```python
def test_a_pinned_holdout_seed_does_not_move_the_design_digest():
    """A seed that is itself inside the digest it is mixed with makes the
    derivation self-referential — and worse, moves every OTHER derived draw in
    the run. `assign.<axis>.seed` is already excluded for that reason; this is
    the same exclusion one field over.

    The positive companion is in the same test: changing a NON-seed holdout
    field MUST move the digest, or an implementation that dropped the whole
    `holdout` block would pass the first assertion alone."""
    base = {"data": {"units": {"from": "index.csv", "key": "patient_id",
                               "holdout": {"method": "random", "frac": 0.2}}}}
    pinned = {"data": {"units": {"from": "index.csv", "key": "patient_id",
                                 "holdout": {"method": "random", "frac": 0.2,
                                             "seed": 1234}}}}
    other_pin = {"data": {"units": {"from": "index.csv", "key": "patient_id",
                                    "holdout": {"method": "random", "frac": 0.2,
                                                "seed": 9999}}}}
    assert design_digest(base) == design_digest(pinned)
    assert design_digest(pinned) == design_digest(other_pin)

    widened = {"data": {"units": {"from": "index.csv", "key": "patient_id",
                                  "holdout": {"method": "random", "frac": 0.3}}}}
    assert design_digest(base) != design_digest(widened)


def test_the_seed_exclusion_covers_assign_and_holdout_together():
    """One config carrying both pins. Asserted together because the two
    exclusions are one function: an implementation that returned early after
    rewriting `assign` would leave `holdout.seed` in, and a config with only
    one pin cannot tell that apart from a correct one."""
    def cfg(assign_seed, holdout_seed):
        return {"data": {"units": {
            "from": "index.csv", "key": "patient_id",
            "assign": {"arm": {"method": "random", "seed": assign_seed}},
            "holdout": {"method": "random", "frac": 0.2, "seed": holdout_seed},
        }}}

    assert design_digest(cfg(7, 11)) == design_digest(cfg(8, 12))
    # A non-seed edit inside the SAME two blocks still moves it, so the
    # exclusion is per-field rather than per-block.
    moved = {"data": {"units": {
        "from": "index.csv", "key": "patient_id",
        "assign": {"arm": {"method": "blocked", "seed": 7}},
        "holdout": {"method": "random", "frac": 0.2, "seed": 11},
    }}}
    assert design_digest(cfg(7, 11)) != design_digest(moved)


def test_the_seed_exclusion_never_raises_on_a_shape_it_did_not_expect():
    """`validate` reaches `design_digest` before a config is known-good, so a
    non-mapping `holdout` must be left exactly as given rather than unpacked.
    Each of these must return a digest instead of raising."""
    for holdout in ("nonsense", ["a", "list"], 3, None):
        assert design_digest(
            {"data": {"units": {"holdout": holdout}}}
        ).startswith("sha256:")
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_hashes.py -k "holdout_seed or exclusion" -x`. The first two fail on the equality assertions; the third passes already (the current function returns `units` untouched when `assign` is not a mapping — which is a **coincidence of the current shape**, not a guarantee, and is why it is pinned before the rewrite rather than after).

- [ ] **Step 3: Implement** — in `src/publishable/hashes.py`, rename and widen:

```python
def _units_excluding_drawn_seeds(units: Any) -> Any:
    """`data.units` with every drawn partition's own `seed` dropped —
    `assign.<axis>.seed` from each axis block, and `holdout.seed`.

    `assign` is a mapping of axis name -> block, so its exclusion is per-axis:
    an axis's own `seed` is dropped from its own block only, never the whole
    `assign` subtree and never a sibling axis's `seed`. `holdout` is a single
    block, so its exclusion is one key. See docs/reference.md § What `auto`
    derives from: each of these seeds mixes the digest with the roster, and a
    seed that is itself inside the digest it is mixed with would make the
    derivation self-referential.

    **The wider harm is the reason this is not merely tidy.** `design_digest`
    canonicalizes `data.units` wholesale, and every other derived draw in the
    run reads the digest — the `seed` repeat stream, `sweep.sample`, each
    axis's assignment. Leaving a pinned seed in would mean that pinning one
    partition to cite it silently redrew all the others, which is the exact
    confounding § What `auto` derives from exists to prevent.

    Every other field of both blocks still moves the digest, which is the
    point: widening `frac`, restratifying, or changing an axis's `method` is a
    different design and must not be reproducible under the same digest.

    `design_digest` runs at run time on a validated config, but `validate`
    reaches it too (indirectly, via `expand` -> the `sample` seed derivation),
    so a malformed config can arrive here first. This function never raises: a
    non-mapping `units`, a non-mapping `assign`, a non-mapping axis block, or a
    non-mapping `holdout` is left exactly as given rather than unpacked, so the
    caller's canonical JSON encoding still runs over *something* instead of
    crashing on a shape it did not expect.
    """
    if not isinstance(units, dict):
        return units
    out = units
    assign = out.get("assign")
    if isinstance(assign, dict):
        new_assign = {}
        changed = False
        for axis, block in assign.items():
            if isinstance(block, dict) and "seed" in block:
                new_assign[axis] = {k: v for k, v in block.items() if k != "seed"}
                changed = True
            else:
                new_assign[axis] = block
        if changed:
            out = {**out, "assign": new_assign}
    holdout = out.get("holdout")
    if isinstance(holdout, dict) and "seed" in holdout:
        out = {**out, "holdout": {k: v for k, v in holdout.items() if k != "seed"}}
    return out
```

  and in `design_digest`, replace the call and widen its docstring's first line:

```python
def design_digest(config: dict[str, Any]) -> str:
    """`data.units` (every field except a drawn partition's own `seed`) and `sweep.groups`.

    A parameter edit redraws nothing, and neither does pinning or changing an
    axis's `assign.seed` or `data.units.holdout.seed` — see
    `_units_excluding_drawn_seeds`.
    """
    units = _units_excluding_drawn_seeds((config.get("data") or {}).get("units"))
```

  Then sweep for the old name — **by claim, not by the file this task happens to name**: `grep -rn _units_excluding_assign_seed src/ tests/ docs/`. Every hit moves, including the `spec-defects.md` entry, whose *closed* half names the old function.

  Then in `docs/superpowers/spec-defects.md`, strike the open half. Replace the paragraph beginning "**One field over, the same defect is latent.**" with:

```markdown
**~~One field over, the same defect is latent.~~ Closed by H3d, task 4.**
`hashes._units_excluding_assign_seed` was renamed `_units_excluding_drawn_seeds` and now
drops `data.units.holdout.seed` as well as each `assign.<axis>.seed`, so a pinned holdout
seed no longer perturbs any other derived draw. `reference.md` § What `auto` derives from
gained the matching row and named `E-DATA-HOLDOUT-SEED` in the same slice.
```

  and change the entry's trailing "The `holdout.seed` half above remains open" sentence to say it is closed by H3d task 4.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_hashes.py -k "holdout_seed or exclusion"`, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Then re-run `grep -rn _units_excluding_assign_seed src/ tests/ docs/` — it must return **nothing**. Prove the sweep can fail by running it against `_units_excluding_drawn_seeds`, which must return hits.

- [ ] **Step 5: Mutate** — in `src/publishable/hashes.py`, change the holdout branch's condition from `if isinstance(holdout, dict) and "seed" in holdout:` to `if False and isinstance(holdout, dict) and "seed" in holdout:`. Run `uv run pytest tests/test_hashes.py -k "holdout_seed or exclusion"`. Both `test_a_pinned_holdout_seed_does_not_move_the_design_digest` and `test_the_seed_exclusion_covers_assign_and_holdout_together` must **FAIL**. Delete `__pycache__`, edit the condition back in place, re-run; both pass. Then a second mutation proving the *positive* companion is not vacuous: change the exclusion to drop the whole block — `out = {**out, "holdout": None}` in place of the dict comprehension. `test_a_pinned_holdout_seed_does_not_move_the_design_digest` must **FAIL** on `design_digest(base) != design_digest(widened)`. Revert in place.

- [ ] **Step 6: Commit** — `fix: exclude data.units.holdout.seed from the design digest`.

---

## Task 5: `_check_holdout`, declaration half A — method, `frac`, `from`, the dead fields, the seed pin

**Files:** Modify `src/publishable/validate.py`. Modify (append) `tests/test_validate.py`.

**Interfaces:**
- Consumes: `Collector.error(code, path, message)` from `publishable.diagnostics`; `validate_config`'s locals `doc`, `units_decl`, `roster`, `usable_cluster`.
- Produces:

```python
HOLDOUT_METHODS = ("random", "by_attribute")


def _check_holdout(
    doc: dict[str, Any],
    units: dict[str, Any],
    roster: UnitList | None,
    cluster_by: str | None,
    c: Collector,
) -> None:
```

  called from `validate_config` immediately after `_check_fold_stratify_by(doc, units_decl, roster, usable_cluster, c)`:

```python
    _check_holdout(doc, units_decl, roster, usable_cluster, c)
```

  Tasks 6 and 7 extend this same function. The `roster` and `cluster_by` parameters are unread at this commit and are in the signature anyway, for `units.assignment_for`'s stated reason: a caller that already has to hold both must not be told the signature changed under it two tasks later.

**The five findings this task adds**, in declaration order: `E-DATA-HOLDOUT-METHOD`, `E-DATA-HOLDOUT-FRAC`, `E-DATA-HOLDOUT-FROM`, `E-DATA-HOLDOUT-NO-DRAW`, `E-DATA-HOLDOUT-SEED`. `_check_resample`'s docstring is the model: it **enumerates its findings and says an eighth belongs in the list**, so this one enumerates its five and says the same.

**The `holdout: {}` ruling, settled here and not re-derived later.** An empty or non-mapping `holdout` **returns immediately and reports nothing**, mirroring `_check_resample`'s own `if not isinstance(resample, dict) or not resample: return`. `holdout: {}` and `holdout: null` therefore validate clean, exactly as they do at `78bb794` — the scoping calls this "the truthiness hole", and it is not a hole: `_check_unimplemented`'s `units.get(field)` is false for both, `envelope.py` (task 3) reports any misspelled child, and a block declaring nothing partitions nothing. **Pin it with a test**, because an implementer will otherwise try to refuse it.

**Every value read here is `isinstance`-guarded and quietly skipped when it is not a leaf `envelope.py` types.** A leaf type fault is deliberately non-fatal in this module — reported as `E-CONFIG-TYPE` and validation continues — which is the same division `_check_report_by` and `_check_resample` keep.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
def _holdout(block, **extra) -> dict:
    """`write_config`'s whole-block override for a config declaring a holdout.

    `base_config` has no `data.units` key at all, so a dotted
    `{"data.units.holdout": ...}` override raises `KeyError` walking `units` —
    the whole block is what every other `data.units` test in this file writes.
    """
    units = {"from": "index.csv", "key": "patient_id", **extra}
    if block is not None:
        units["holdout"] = block
    return {"data.units": units}


def test_an_empty_or_null_holdout_validates_clean(write_config):
    """`holdout: {}` and `holdout: null` declare nothing and partition nothing,
    so neither is refused — `_check_resample`'s own `not isinstance(...) or not
    ...: return` gate, one block over. Pinned because the shape looks like a
    hole and is not: a misspelled child inside a NON-empty block is reported by
    `check_envelope`, and `_check_unimplemented`'s truthiness test is false for
    both of these.

    The positive companion is the third assertion: a real declaration in the
    same position DOES report, so this cannot pass by the check being dead."""
    assert "E-DATA-HOLDOUT-METHOD" not in codes(write_config(_holdout({})))
    assert "E-DATA-HOLDOUT-METHOD" not in codes(write_config(_holdout(None)))
    assert "E-DATA-HOLDOUT-METHOD" in codes(write_config(_holdout({"frac": 0.2})))


@pytest.mark.parametrize(
    "block,expected",
    [
        # `method` — absent, wrong type, out of enum. An allowlist: a method
        # named here and realized nowhere would validate clean and then
        # partition on something core never drew.
        ({"frac": 0.2}, "E-DATA-HOLDOUT-METHOD"),
        ({"method": ["random"], "frac": 0.2}, "E-DATA-HOLDOUT-METHOD"),
        ({"method": "stratified", "frac": 0.2}, "E-DATA-HOLDOUT-METHOD"),
        # `frac` under `random` — absent, and each end of the OPEN interval.
        ({"method": "random"}, "E-DATA-HOLDOUT-FRAC"),
        ({"method": "random", "frac": 0}, "E-DATA-HOLDOUT-FRAC"),
        ({"method": "random", "frac": 1}, "E-DATA-HOLDOUT-FRAC"),
        ({"method": "random", "frac": -0.5}, "E-DATA-HOLDOUT-FRAC"),
        ({"method": "random", "frac": 1.5}, "E-DATA-HOLDOUT-FRAC"),
        # `from` under `by_attribute` — absent and empty. There is no axis name
        # to default to, unlike `assign.<axis>.from`.
        ({"method": "by_attribute"}, "E-DATA-HOLDOUT-FROM"),
        ({"method": "by_attribute", "from": ""}, "E-DATA-HOLDOUT-FROM"),
        # A field meaning nothing under the declared method, both directions.
        ({"method": "by_attribute", "from": "split", "frac": 0.2},
         "E-DATA-HOLDOUT-NO-DRAW"),
        ({"method": "random", "frac": 0.2, "from": "split"},
         "E-DATA-HOLDOUT-NO-DRAW"),
        ({"method": "by_attribute", "from": "split", "stratify_by": ["label"]},
         "E-DATA-HOLDOUT-NO-DRAW"),
        # The seed pin — present and neither `auto` nor a plain int.
        ({"method": "random", "frac": 0.2, "seed": "1234"}, "E-DATA-HOLDOUT-SEED"),
        ({"method": "random", "frac": 0.2, "seed": 1.5}, "E-DATA-HOLDOUT-SEED"),
    ],
)
def test_a_malformed_holdout_declaration_is_refused(write_config, block, expected):
    found = codes(write_config(_holdout(block)))
    assert expected in found
    # Alongside, never instead of: `E-DATA-HOLDOUT-UNSUPPORTED` is still live
    # at this commit and task 18 retires it. Membership on its own line makes
    # that retirement a one-line deletion rather than a rewrite of this test.
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


@pytest.mark.parametrize(
    "block",
    [
        {"method": "random", "frac": 0.2},
        {"method": "random", "frac": 0.2, "seed": "auto"},
        {"method": "random", "frac": 0.2, "seed": 1234},
        {"method": "random", "frac": 0.999},
        {"method": "by_attribute", "from": "split"},
        {"method": "by_attribute", "from": "split", "seed": 1234},
    ],
)
def test_a_well_formed_holdout_declaration_earns_none_of_the_five(write_config, block):
    """The success path for every arm above. A parametrization asserting only
    failures proves nothing about either method's accepted shape — the shape
    that left `blocked`'s stratified draw fully threaded and never exercised.

    A pinned `seed` is legal under BOTH methods on purpose: `by_attribute`
    records no seed, but a config carrying one is not malformed, and refusing
    it here would put the `NO-DRAW` rule somewhere this test would not see."""
    found = codes(write_config(_holdout(block)))
    for code in ("E-DATA-HOLDOUT-METHOD", "E-DATA-HOLDOUT-FRAC",
                 "E-DATA-HOLDOUT-FROM", "E-DATA-HOLDOUT-NO-DRAW",
                 "E-DATA-HOLDOUT-SEED"):
        assert code not in found
    # The positive companion: this config is not silently escaping the check
    # entirely — the wholesale refusal still fires on the same declaration.
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k holdout -x`. `test_a_malformed_holdout_declaration_is_refused` fails on every row; `test_an_empty_or_null_holdout_validates_clean` fails on its third assertion; the well-formed test passes already (nothing reports), which is why its **positive companion** — the surviving wholesale refusal — is what keeps it from being vacuous.

- [ ] **Step 3: Implement** — in `src/publishable/validate.py`, add the enum beside `ASSIGN_METHODS` (which sits at module level with its own explanatory docstring):

```python
HOLDOUT_METHODS = ("random", "by_attribute")
"""`data.units.holdout.method`'s enum — `reference.md` § A fixed holdout split.

Two values and no more, and stated as a closed enum for `ASSIGN_METHODS`'s
reason: a third named here and realized nowhere would validate clean and then
reach `units.holdout_for`, which refuses what it cannot draw. Which of the two
reads a partition and which draws one is what decides every other field's
meaning, so a malformed `method` is reported before any of them is read.
"""
```

  and the check itself, placed immediately after `_check_fold_stratify_by`'s definition:

```python
def _check_holdout(
    doc: dict[str, Any],
    units: dict[str, Any],
    roster: UnitList | None,
    cluster_by: str | None,
    c: Collector,
) -> None:
    """Every check `data.units.holdout` gets — five findings at this commit, in
    declaration order, and the enumeration is the list rather than a sample of
    it:

    - `E-DATA-HOLDOUT-METHOD` — the `method` enum.
    - `E-DATA-HOLDOUT-FRAC` — `frac` in the open interval (0, 1), under `random`.
    - `E-DATA-HOLDOUT-FROM` — `from` required, under `by_attribute`.
    - `E-DATA-HOLDOUT-NO-DRAW` — a field meaning nothing under the declared
      method.
    - `E-DATA-HOLDOUT-SEED` — the seed pin.

    **None of the five reads `roster` or `cluster_by`**, and both are in the
    signature anyway, `units.assignment_for`'s reason: the caller already holds
    both, and a caller told the signature changed under it is what a stable one
    avoids. A check added here must state which side of that line it is on —
    this list is what the next reader counts against, so a sixth finding
    belongs in it, and a roster-reading one carries its own
    `roster is not None` guard rather than leaning on a caller.

    **An empty or non-mapping declaration returns reporting nothing**,
    `_check_resample`'s own gate one block over. `holdout: {}` and
    `holdout: null` declare nothing and partition nothing;
    `_check_unimplemented`'s truthiness test is false for both, and a
    misspelled child inside a non-empty block is `check_envelope`'s
    `E-CONFIG-KEY-UNKNOWN` rather than this function's.

    Every value read here is `isinstance`-guarded and quietly skipped when it
    is not the leaf `envelope.LEAF_TYPES` types, the same division
    `_check_report_by` keeps: a leaf type fault is `E-CONFIG-TYPE`, reported
    already and deliberately non-fatal, and reporting a second, derived fault
    on top of the one the reader has to fix anyway is what
    `validate_config`'s own `usable_cluster` guard avoids.

    **`frac`'s interval is open at both ends.** `0` holds nothing out and `1`
    holds everything out; each leaves one side of the split empty, and a split
    with an empty side is not a split. A `frac` small enough to apportion the
    test side zero units over *this* roster is a different fault with a
    different fix — widen it, or resolve more units — and is not this check's.
    """
    holdout = units.get("holdout")
    if not isinstance(holdout, dict) or not holdout:
        return

    method = holdout.get("method")
    if method is None:
        c.error(
            "E-DATA-HOLDOUT-METHOD",
            "data.units.holdout.method",
            f"is not declared; the methods are {', '.join(HOLDOUT_METHODS)}, and which "
            "one is declared decides what every other field of the block means — "
            "`random` draws a split and `by_attribute` reads one already in the data",
        )
    elif not isinstance(method, str):
        # Absorbed here rather than left to `E-CONFIG-TYPE` alone: the reader's
        # question is which method they meant, and a bare type finding does not
        # enumerate the two.
        c.error(
            "E-DATA-HOLDOUT-METHOD",
            "data.units.holdout.method",
            f"is {method!r}, which names no method; the methods are "
            f"{', '.join(HOLDOUT_METHODS)}",
        )
    elif method not in HOLDOUT_METHODS:
        c.error(
            "E-DATA-HOLDOUT-METHOD",
            "data.units.holdout.method",
            f"is {method!r}, which is not one of {', '.join(HOLDOUT_METHODS)}. A method "
            "named here and realized nowhere would validate clean and then partition "
            "on something core never drew",
        )

    declared_frac = holdout.get("frac")
    declared_from = holdout.get("from")
    if method == "random":
        if declared_frac is None:
            c.error(
                "E-DATA-HOLDOUT-FRAC",
                "data.units.holdout.frac",
                "is not declared, and `method: random` draws the test side by "
                "fraction — there is nothing to draw without one",
            )
        elif isinstance(declared_frac, (int, float)) and not isinstance(declared_frac, bool):
            if not 0.0 < float(declared_frac) < 1.0:
                c.error(
                    "E-DATA-HOLDOUT-FRAC",
                    "data.units.holdout.frac",
                    f"is {declared_frac}, and a test fraction is strictly between 0 and "
                    "1 — `0` holds nothing out and `1` holds everything out, and each "
                    "leaves one side of the split empty",
                )
        if declared_from is not None:
            c.error(
                "E-DATA-HOLDOUT-NO-DRAW",
                "data.units.holdout.from",
                "means nothing under `method: random`, which draws the split rather "
                "than reading one out of a column — declare `method: by_attribute` to "
                "read the column, or drop `from`",
            )
    elif method == "by_attribute":
        if declared_from is None:
            c.error(
                "E-DATA-HOLDOUT-FROM",
                "data.units.holdout.from",
                "is not declared, and `method: by_attribute` reads the split out of a "
                "column — unlike an assignment axis there is no axis name to default "
                "to, so the column has to be named",
            )
        elif isinstance(declared_from, str) and not declared_from:
            c.error(
                "E-DATA-HOLDOUT-FROM",
                "data.units.holdout.from",
                "is empty, which names no column to read the split out of",
            )
        if declared_frac is not None:
            c.error(
                "E-DATA-HOLDOUT-NO-DRAW",
                "data.units.holdout.frac",
                "means nothing under `method: by_attribute`, which reads a split the "
                "data already holds rather than drawing one to a size — the realized "
                "proportion is whatever the column says it is",
            )
        if holdout.get("stratify_by") is not None:
            c.error(
                "E-DATA-HOLDOUT-NO-DRAW",
                "data.units.holdout.stratify_by",
                "means nothing under `method: by_attribute`: `stratify_by` names how a "
                "draw is BALANCED, and a split read out of a column was not drawn. The "
                "same absorption `E-DATA-ASSIGN-NO-DRAW` performs for the same field "
                "one declaration over",
            )

    if "seed" in holdout:
        seed = holdout["seed"]
        pinned = isinstance(seed, int) and not isinstance(seed, bool)
        if not pinned and seed != "auto":
            c.error(
                "E-DATA-HOLDOUT-SEED",
                "data.units.holdout.seed",
                f"is {seed!r}, and a seed is `auto` or a plain integer. A quoted "
                "number, a float, or a boolean is a pin nothing can honour, and "
                "deriving one anyway would record a derived seed under a key the "
                "config wrote deliberately",
            )
```

  and wire it in `validate_config`, immediately after the `_check_fold_stratify_by` call:

```python
    _check_fold_stratify_by(doc, units_decl, roster, usable_cluster, c)
    # Sited here for `_check_fold_stratify_by`'s reason and beside it: both read
    # the resolved roster and the usable cluster name, and both check a
    # partition's declaration rather than a repeat's. `usable_cluster` is
    # already narrowed to a non-empty string or `None` above, so this call needs
    # no guard of its own.
    _check_holdout(doc, units_decl, roster, usable_cluster, c)
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k holdout`, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — three, because three independent things could be dead.

  (a) In `src/publishable/validate.py`, change `if not 0.0 < float(declared_frac) < 1.0:` to `if not 0.0 <= float(declared_frac) <= 1.0:`. Run `uv run pytest tests/test_validate.py -k malformed_holdout_declaration`. The `frac: 0` and `frac: 1` rows must **FAIL**. Revert in place; re-run.

  (b) Change the wiring line `_check_holdout(doc, units_decl, roster, usable_cluster, c)` to pass `{}` in place of `units_decl`. **Every** row of `test_a_malformed_holdout_declaration_is_refused` must **FAIL**, and `test_an_empty_or_null_holdout_validates_clean`'s third assertion too. This is the mutation that proves the check is *wired*, not merely written — the seam H4a's `_condition_counts` extraction exists to make visible. Revert in place; re-run.

  (c) Change the empty-block gate from `if not isinstance(holdout, dict) or not holdout:` to `if not isinstance(holdout, dict):`. `test_an_empty_or_null_holdout_validates_clean`'s **first** assertion must **FAIL** (`holdout: {}` now reports `E-DATA-HOLDOUT-METHOD`). Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: refuse a malformed data.units.holdout declaration`.

---

## Task 6: `_check_holdout`, declaration half B — `stratify_by` existence, and `holdout` × `fold`

**Files:** Modify `src/publishable/validate.py`. Modify (append) `tests/test_validate.py`.

**Interfaces:**
- Consumes: `_check_holdout(doc, units, roster, cluster_by, c)` from task 5; `units.stratum_names(stratify_by: Any) -> tuple[str, ...]`, already imported in `validate.py`.
- Produces: two more findings inside the same function — `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` and `E-DATA-HOLDOUT-FOLD` — and the docstring's enumeration grown from five to seven.

**Why these two are one task and not two halves of task 5.** Different failure reason: the first discharges the `holdout` half of § Validation's shared *Stratification attribute exists* row, which `validate.py`'s `_check_fold_stratify_by` docstring explicitly says "belongs to the slice that builds that block"; the second reads a **different block** (`replication`) and is the only check in `_check_holdout` that does.

**Read through `units.stratum_names`, not with a hand-rolled `isinstance` chain.** It is the single authority the draw balances on, and it reads a bare `stratify_by: label` as one name exactly as `[label]` is. Two independent readings of one declaration pinned in agreement by nothing is the validate-clean-then-disagree shape this repo refuses; `_check_resample` reads it the same way and its own comment says why.

**One finding per offending name.** A `stratify_by: [site, sex]` naming two undeclared attributes earns two findings, not one naming only the first — `E-DATA-ASSIGN-STRATIFY-UNKNOWN`'s stated rule, and the reason the fixture below declares two.

**Where the exclusion is sited, and why not in `resolve_repeats`.** In `_check_holdout`, reading `replication.repeats` from the doc. `replication.REPL_DECLARATION_CODES` stays exactly as it is: a fold level is a perfectly well-formed *repeat*, and what is refused is the **combination** with a declaration in another block, which `resolve_repeats` cannot see. Siting it here is also what lets task 18 retire the wholesale refusal without touching `replication.py`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
_HOLDOUT_STRATA_ROSTER = "patient_id,label,site\n" + "".join(
    f"p{i},{'x' if i % 2 else 'y'},s{i % 3}\n" for i in range(12)
)


def test_a_holdout_stratum_naming_no_declared_attribute_is_refused(write_config, tmp_path):
    """§ Validation *Stratification attribute exists*, the `holdout` half —
    `_check_fold_stratify_by`'s docstring names this as belonging to the slice
    that builds the block, and this is that slice.

    TWO undeclared names, because the rule is one finding per offending name
    and a one-element fixture cannot tell that from one finding per
    declaration."""
    (tmp_path / "input" / "index.csv").write_text(_HOLDOUT_STRATA_ROSTER)
    c = Collector()
    validate_config(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.25, "stratify_by": ["sex", "cohort"]},
                attributes=["label", "site"],
            )
        ),
        c,
    )
    unknown = [f for f in c.findings if f.code == "E-DATA-HOLDOUT-STRATIFY-UNKNOWN"]
    assert len(unknown) == 2, [f.message for f in unknown]
    # Both names, not the same name twice: a loop reporting `strata[0]` each
    # time would give a count of 2 and be wrong about which attributes failed.
    joined = " ".join(f.message for f in unknown)
    assert "'sex'" in joined and "'cohort'" in joined, joined
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in {f.code for f in c.findings}


def test_a_bare_string_holdout_stratum_is_read_as_one_name(write_config, tmp_path):
    """`units.stratum_names` reads `stratify_by: label` as one name exactly as
    `[label]` is. Read as a sequence of characters instead, an undeclared bare
    string would report one finding per LETTER — five for `sexes` — so the
    count is what distinguishes the two readings, and the fixture's name is
    five letters long for exactly that reason."""
    (tmp_path / "input" / "index.csv").write_text(_HOLDOUT_STRATA_ROSTER)
    c = Collector()
    validate_config(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.25, "stratify_by": "sexes"},
                attributes=["label", "site"],
            )
        ),
        c,
    )
    assert len([f for f in c.findings if f.code == "E-DATA-HOLDOUT-STRATIFY-UNKNOWN"]) == 1


@pytest.mark.parametrize("declared", ["", [], 7, [3]])
def test_a_holdout_stratum_that_names_no_attribute_at_all_is_refused(
    write_config, tmp_path, declared
):
    """A non-string, an empty string, and an empty list each name no attribute.
    `data.units.holdout.stratify_by` IS an `envelope.LEAF_TYPES` leaf as of task
    3, so `7` also earns `E-CONFIG-TYPE` — absorbed here as well because a bare
    type finding does not say what a stratum has to be."""
    (tmp_path / "input" / "index.csv").write_text(_HOLDOUT_STRATA_ROSTER)
    found = codes(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.25, "stratify_by": declared},
                attributes=["label", "site"],
            )
        )
    )
    assert "E-DATA-HOLDOUT-STRATIFY-UNKNOWN" in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_a_holdout_stratum_naming_the_measurement_axis_is_refused(write_config, tmp_path):
    """The measurement axis is consumed when a unit's rows collapse, so no
    resolved unit carries it — the same fault and the same code as an
    undeclared name, for `_check_fold_stratify_by`'s stated reason one
    declaration over."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,read_id,label\n" + "".join(f"p{i // 2},r{i},x\n" for i in range(12))
    )
    found = codes(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.25, "stratify_by": ["read_id"]},
                attributes=["read_id", "label"],
                measurements={"by": "read_id", "collapse": "mean"},
            )
        )
    )
    assert "E-DATA-HOLDOUT-STRATIFY-UNKNOWN" in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_a_declared_holdout_stratum_is_accepted(write_config, tmp_path):
    """The positive companion, produced by the code under test: the same
    declaration over a name `data.units.attributes` DOES declare reports
    nothing, so the check reads the declaration rather than refusing every
    `stratify_by`."""
    (tmp_path / "input" / "index.csv").write_text(_HOLDOUT_STRATA_ROSTER)
    found = codes(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.25, "stratify_by": ["label", "site"]},
                attributes=["label", "site"],
            )
        )
    )
    assert "E-DATA-HOLDOUT-STRATIFY-UNKNOWN" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_a_holdout_beside_a_fold_repeat_is_refused(write_config):
    """§ A fixed holdout split: two answers to one question — how the data is
    divided for evaluation — leaving "which units is this metric over?" with
    none. Probed at `78bb794`: this config reports ONLY
    `E-DATA-HOLDOUT-UNSUPPORTED` today, with no exclusion check at all."""
    overrides = _holdout({"method": "random", "frac": 0.2})
    overrides["replication"] = {
        "repeats": [{"kind": "fold", "k": 5}], "order": "as_declared"
    }
    found = codes(write_config(overrides))
    assert "E-DATA-HOLDOUT-FOLD" in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_a_holdout_beside_a_seed_repeat_is_not_refused(write_config):
    """The control, and it must report something: a `seed` repeat divides
    nothing, so the exclusion is about `fold` specifically rather than about
    `replication` being declared at all. Without the second assertion this
    passes identically if the check is dead."""
    found = codes(write_config(_holdout({"method": "random", "frac": 0.2})))
    assert "E-DATA-HOLDOUT-FOLD" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k "holdout_stratum or holdout_beside" -x`. Every test asserting a new code fails; the two controls pass already, which is why each carries the wholesale-refusal companion. `Collector` and `validate_config` are already imported at the top of `tests/test_validate.py`.

- [ ] **Step 3: Implement** — extend `_check_holdout` in `src/publishable/validate.py`. First grow the docstring's enumeration to seven, inserting after the `E-DATA-HOLDOUT-SEED` bullet:

```python
    - `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` — a `stratify_by` name that is not a
      declared unit attribute, names `data.units.measurements.by`, or is not
      the name of an attribute at all.
    - `E-DATA-HOLDOUT-FOLD` — a `{kind: fold}` repeat declared beside this
      block. The only check here that reads a block other than `data.units`.
```

  Then append to the function body, after the seed pin:

```python
    # `stratify_by`, through `units.stratum_names` — the single authority the
    # draw balances on, which reads a bare `stratify_by: label` as one name
    # exactly as `[label]` is. Re-deriving that reading here with an
    # `isinstance` chain would pin two independent readings of one declaration
    # in agreement by nothing, which is what `_check_resample` reads it this
    # way to avoid.
    #
    # **`data.units.attributes` is the reference set**, not the source's
    # columns, the side of the line `_check_cluster_by`, `_check_weight_by` and
    # `_check_fold_stratify_by` all read: a stratum is read per unit when the
    # split is drawn, so it has to survive resolution as an attribute rather
    # than merely be a column of the source. Checked from the declaration
    # alone, so it reports whether or not a roster resolved.
    #
    # One finding per offending name, `E-DATA-ASSIGN-STRATIFY-UNKNOWN`'s rule:
    # a declaration naming two undeclared attributes earns two, rather than one
    # naming only the first.
    attrs = units.get("attributes") or []
    declared_names = (
        sorted({a for a in attrs if isinstance(a, str)}) if isinstance(attrs, list) else []
    )
    measurements = units.get("measurements")
    measurement_axis = measurements.get("by") if isinstance(measurements, dict) else None
    raw_strata = holdout.get("stratify_by")
    strata = stratum_names(raw_strata)
    if raw_strata is not None and not strata:
        # An empty string or an empty list: present, and naming nothing. Left
        # silent it would be a declaration that changes no behaviour, which is
        # exactly what a truthy read of it hides.
        c.error(
            "E-DATA-HOLDOUT-STRATIFY-UNKNOWN",
            "data.units.holdout.stratify_by",
            "is empty, which names no attribute to balance the split on and changes "
            "no behavior. Name the attribute, or remove the key",
        )
    for name in strata:
        if not isinstance(name, str) or not name:
            c.error(
                "E-DATA-HOLDOUT-STRATIFY-UNKNOWN",
                "data.units.holdout.stratify_by",
                f"names {name!r}, which is not the name of a unit attribute — a split "
                "is balanced on attributes named as strings",
            )
            continue
        if name not in declared_names:
            c.error(
                "E-DATA-HOLDOUT-STRATIFY-UNKNOWN",
                "data.units.holdout.stratify_by",
                f"names {name!r}, which is not a unit attribute — a stratum is read "
                "per unit when the split is drawn, so it has to be one. "
                f"`data.units.attributes` declares "
                f"{', '.join(declared_names) or 'none'}",
            )
            continue
        if isinstance(measurement_axis, str) and measurement_axis == name:
            c.error(
                "E-DATA-HOLDOUT-STRATIFY-UNKNOWN",
                "data.units.holdout.stratify_by",
                f"names {name!r}, which `data.units.measurements.by` also names — the "
                "measurement axis is consumed when a unit's rows collapse and is not "
                "an attribute of the resolved unit, so there is nothing left to "
                "balance the split on. Stratify on an attribute that survives the "
                "collapse",
            )

    # The one check here that reads a block other than `data.units`. Sited in
    # `validate` rather than in `resolve_repeats` because a `fold` level is a
    # perfectly well-formed *repeat*: what is refused is the COMBINATION with a
    # declaration in another block, which `resolve_repeats` never sees. That is
    # also why `replication.REPL_DECLARATION_CODES` is unchanged by this.
    repeats = (doc.get("replication") or {}).get("repeats")
    if isinstance(repeats, list) and any(
        isinstance(level, dict) and level.get("kind") == "fold" for level in repeats
    ):
        c.error(
            "E-DATA-HOLDOUT-FOLD",
            "data.units.holdout",
            "is declared beside a `{kind: fold}` repeat level, and the two are "
            "mutually exclusive — each divides the units for evaluation, so together "
            "they leave `which units is this metric over?` with no single answer. To "
            "hold out a final test set AND cross-validate for model selection, declare "
            "the holdout and do the inner search inside the step over `io.units.train`",
        )
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k "holdout_stratum or holdout_beside"`, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — two.

  (a) In `src/publishable/validate.py`, change `strata = stratum_names(raw_strata)` to `strata = (raw_strata,) if isinstance(raw_strata, str) else tuple(raw_strata or ())` — a re-derivation that agrees with `stratum_names` on every shape this fixture set covers except none, so **check the two branches can differ before trusting it**: they cannot, and this mutation is therefore *rejected*. Use this one instead: change it to `strata = tuple(raw_strata) if isinstance(raw_strata, list) else ()`. Run `uv run pytest tests/test_validate.py -k bare_string_holdout_stratum`. It must **FAIL** — a bare `"sexes"` now yields zero names, so no finding is reported. Revert in place; re-run.

  (b) Change the fold exclusion's `level.get("kind") == "fold"` to `level.get("kind") == "batch"`. `test_a_holdout_beside_a_fold_repeat_is_refused` must **FAIL**. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: refuse an unknown holdout stratum and a holdout beside a fold`.

---

## Task 7: `_check_holdout`, roster half — the two literals, the clustered stratum, the empty test side

**Files:** Modify `src/publishable/validate.py`, `src/publishable/units.py`. Modify (append) `tests/test_validate.py`, `tests/test_units.py`.

**Interfaces:**
- Consumes: `units.arms_of(roster, column, levels) -> dict[str, list[Unit]]`, `units.stratum_varies_within_cluster(roster, cluster_by, stratify_by) -> tuple[str, list[str]] | None`, `units._apportion(n, weights) -> list[int]`.
- Produces:

```python
# src/publishable/units.py
HOLDOUT_LEVELS = ("train", "test")


def holdout_sizes(n: int, frac: float) -> tuple[int, int]:
    """`(train, test)` — `n` apportioned across `[1 - frac, frac]`."""


def holdout_values_fault(roster: UnitList, column: str) -> str | None:
    """The message describing how `column` fails to be exactly `{train, test}`
    over this roster, or `None` when it does not fail."""
```

  plus three more findings inside `_check_holdout` — `E-DATA-HOLDOUT-VALUES`, `E-DATA-HOLDOUT-STRATIFY-VARIES`, `E-DATA-HOLDOUT-EMPTY` — and `arms_of` added to `validate.py`'s `publishable.units` import list.

**Why `holdout_values_fault` exists rather than `validate` and the draw each wrapping `arms_of`.** Both `_check_holdout` (here) and `units.holdout_for` (task 10) have to answer "does this column resolve to exactly the two literals", and both have to say so in a holdout's vocabulary rather than `arms_of`'s, whose message names an arm and an axis's declared levels. Two independent wrappings of one raise is precisely how two messages come to drift — `stratum_varies_within_cluster` is the pattern that already solves this in this repo: **one function computes the fault and returns it, and each caller decides whether to collect it or raise it.** So the verdict and the wording live here, once, and task 10's `holdout_for` raises the string this returns.

**Why `holdout_sizes` exists rather than `validate` computing `int(n * frac)`.** `_apportion` is private, and a second arithmetic for the same split is exactly the validate-clean-then-disagree gap: `validate` would approve a `frac` whose realized test side the draw then sized differently. One public function, two callers — this check and task 10's `holdout_for`. `_apportion`'s largest-remainder rule is what `assignment_for`'s `random` branch already uses, so the holdout inherits it rather than inventing one.

**Each of the three carries its own `roster is not None` guard** rather than leaning on a caller — `_check_resample`'s stated convention, and the reason its docstring separates the roster-reading findings from the rest.

**The siting rule for the empty-test-partition refusal, and it is trap 5's.** Mirror *Every arm draws units* exactly: **reported for the unstratified, unclustered `random` draw only.** A stratified or clustered split is checked where the run performs it, because a cluster is the smallest thing that can move and only the draw knows what it moved. And `by_attribute` needs no refusal here at all — `arms_of` already refuses a level no unit's value names, which is a zero-size side by another name, so adding one would double-refuse the same fault under two codes.

**`stratum_varies_within_cluster`'s docstring is stale and this task fixes it.** It claims *"rows Fold strata survive clustering and Holdout strata survive clustering"* — two rows — while having **three** call sites at `78bb794` (`validate.py`'s `E-DATA-ASSIGN-STRATIFY-VARIES`, `E-REPL-FOLD-STRATIFY-VARIES` and `E-STATS-RESAMPLE-STRATIFY-VARIES`). This task adds the **fourth**, so the docstring must name four rows. **Before editing it, run `grep -rn "Fold strata survive clustering" tests/ src/`** — a test pinning that wording is the "sweep stopped one file short" shape, and it must move with the docstring.

- [ ] **Step 1: Write the failing test** — append to `tests/test_units.py`:

```python
def test_holdout_sizes_is_the_single_authority_for_the_split_sizes():
    """One arithmetic for the split, shared by `validate`'s refusal and the
    draw. `_apportion`'s largest-remainder rule, which `assignment_for`'s
    `random` branch already uses — so a `frac` `validate` approves is a `frac`
    the draw realizes at the same sizes.

    Each row is chosen so a DIFFERENT wrong rule gives a different answer:
    truncation, rounding, and largest-remainder disagree on at least one."""
    assert holdout_sizes(10, 0.2) == (8, 2)
    assert holdout_sizes(240, 0.2) == (192, 48)
    # 7 × 0.2 = 1.4: truncation gives 1, rounding gives 1, largest-remainder
    # gives 1 — and the train side is what separates a rule that apportions
    # from one that subtracts a rounded test size.
    assert holdout_sizes(7, 0.2) == (6, 1)
    # 4 × 0.2 = 0.8: the floor is 0 and the remainder goes to the LARGEST
    # fractional part, which is the test side's 0.8 against the train side's
    # 3.2 — so largest-remainder gives 1 here where truncation gives 0.
    assert holdout_sizes(4, 0.2) == (3, 1)
    # The case the refusal exists for: no rule can give the test side a unit.
    assert holdout_sizes(2, 0.2) == (2, 0)
    assert sum(holdout_sizes(13, 0.3)) == 13
```

  and append to `tests/test_validate.py`:

```python
_SPLIT_ROSTER_OK = "patient_id,split\n" + "".join(
    f"p{i},{'test' if i % 5 == 0 else 'train'}\n" for i in range(20)
)
_SPLIT_ROSTER_THREE = "patient_id,split\n" + "".join(
    f"p{i},{['train', 'test', 'dev'][i % 3]}\n" for i in range(20)
)
_SPLIT_ROSTER_AB = "patient_id,split\n" + "".join(
    f"p{i},{'A' if i % 2 else 'B'}\n" for i in range(20)
)
_SPLIT_ROSTER_ONE_SIDED = "patient_id,split\n" + "".join(
    f"p{i},train\n" for i in range(20)
)


@pytest.mark.parametrize(
    "roster_csv",
    [_SPLIT_ROSTER_THREE, _SPLIT_ROSTER_AB, _SPLIT_ROSTER_ONE_SIDED],
    ids=["a third value", "neither literal", "one literal unused"],
)
def test_a_by_attribute_holdout_column_must_hold_exactly_train_and_test(
    write_config, tmp_path, roster_csv
):
    """The two literals are fixed, settled in task 2: a holdout declares no
    `levels`, and inferring an order from the data would make which side is
    evaluated depend on a lexical accident of the input.

    Three ROSTERS against one config shape, deliberately: the property is about
    roster CONTENT, and varying config shape over one roster is what made
    nineteen adversary configs roster-incidental in an earlier slice. Each
    roster fails a different way — a third value, neither literal present, and
    both literals declared but one naming no unit."""
    (tmp_path / "input" / "index.csv").write_text(roster_csv)
    found = codes(
        write_config(
            _holdout(
                {"method": "by_attribute", "from": "split"}, attributes=["split"]
            )
        )
    )
    assert "E-DATA-HOLDOUT-VALUES" in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_a_by_attribute_holdout_column_holding_exactly_the_two_literals_is_accepted(
    write_config, tmp_path
):
    """The positive companion, produced by the code under test: the same
    declaration over a column that IS exactly `{train, test}` reports nothing,
    so the refusal reads the roster rather than refusing `by_attribute`."""
    (tmp_path / "input" / "index.csv").write_text(_SPLIT_ROSTER_OK)
    found = codes(
        write_config(
            _holdout(
                {"method": "by_attribute", "from": "split"}, attributes=["split"]
            )
        )
    )
    assert "E-DATA-HOLDOUT-VALUES" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


_VARYING_HOLDOUT_STRATUM = "patient_id,animal_id,label\n" + "".join(
    f"p{i},a{i // 2},{'x' if i % 2 else 'y'}\n" for i in range(28)
)
_CONSTANT_HOLDOUT_STRATUM = "patient_id,animal_id,label\n" + "".join(
    f"p{i},a{i // 2},{'x' if (i // 2) % 2 else 'y'}\n" for i in range(28)
)


@pytest.mark.parametrize(
    "roster_csv,expected",
    [(_VARYING_HOLDOUT_STRATUM, True), (_CONSTANT_HOLDOUT_STRATUM, False)],
    ids=["varies within the animal", "constant within the animal"],
)
def test_a_holdout_stratum_must_be_constant_within_a_cluster(
    write_config, tmp_path, roster_csv, expected
):
    """§ Validation *Holdout strata survive clustering* — whole clusters go to
    one side of a holdout, so a cluster carrying two stratum values can be
    dealt to neither. The fourth `stratum_varies_within_cluster` call site.

    Two ROSTERS with the SAME config: `label` alternates per unit in one and
    per animal in the other, so a check that ignored the roster gives the same
    answer for both and this pair separates them."""
    (tmp_path / "input" / "index.csv").write_text(roster_csv)
    found = codes(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.25, "stratify_by": ["label"]},
                attributes=["animal_id", "label"],
                cluster_by="animal_id",
            )
        )
    )
    assert ("E-DATA-HOLDOUT-STRATIFY-VARIES" in found) is expected
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_a_holdout_that_apportions_the_test_side_no_units_is_refused(
    write_config, tmp_path
):
    """§ Validation *Holdout leaves a test partition*. 4 units at `frac: 0.1`
    apportions `[4, 0]` — every metric would be over nothing.

    The fixture is 4 units and not 40 because the roster size is what decides
    the answer: at 40 the same `frac` apportions `[36, 4]` and reports
    nothing, which is the second row below."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id\n" + "".join(f"p{i}\n" for i in range(4))
    )
    found = codes(write_config(_holdout({"method": "random", "frac": 0.1})))
    assert "E-DATA-HOLDOUT-EMPTY" in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_the_same_frac_over_a_larger_roster_is_accepted(write_config, tmp_path):
    """The positive companion for the row above, produced by the code under
    test and differing ONLY in roster size — so the refusal is the
    apportionment's answer rather than a refusal of small `frac` values."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id\n" + "".join(f"p{i}\n" for i in range(40))
    )
    found = codes(write_config(_holdout({"method": "random", "frac": 0.1})))
    assert "E-DATA-HOLDOUT-EMPTY" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_the_empty_test_partition_refusal_is_not_reported_for_a_clustered_split(
    write_config, tmp_path
):
    """Trap 5's siting rule, mirroring *Every arm draws units*: a clustered or
    stratified split is checked where the RUN performs it, because a cluster is
    the smallest thing that can move and only the draw knows what it moved.
    The same 4-unit roster that reports above must not report here.

    The wholesale refusal is the positive companion — without it this passes
    identically if `_check_holdout` never ran at all."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,animal_id\n" + "".join(f"p{i},a{i // 2}\n" for i in range(4))
    )
    found = codes(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.1},
                attributes=["animal_id"],
                cluster_by="animal_id",
            )
        )
    )
    assert "E-DATA-HOLDOUT-EMPTY" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_units.py -k holdout_sizes tests/test_validate.py -k "by_attribute_holdout or holdout_stratum_must or apportions_the_test or larger_roster or clustered_split" -x`. `holdout_sizes` fails on `ImportError`; every `validate` test asserting a new code fails; the three controls pass, each carrying its wholesale-refusal companion.

- [ ] **Step 3: Implement** —

  (a) In `src/publishable/units.py`, add beside `_apportion`:

```python
HOLDOUT_LEVELS = ("train", "test")
"""`data.units.holdout`'s two sides, in apportionment order — train first.

Fixed literals rather than "the two values the column happens to hold", because
a holdout declares no `levels` for core to read an order out of, and inferring
one from the data would make which side is *evaluated* depend on a lexical
accident of the input. `reference.md` § A fixed holdout split states the rule
and § Errors names the refusal, `E-DATA-HOLDOUT-VALUES`.

Order is load-bearing twice: it is the order `holdout_sizes` apportions in, so
`frac` is the SECOND weight, and it is the order `arms_of` is handed for a
`by_attribute` read.
"""


def holdout_sizes(n: int, frac: float) -> tuple[int, int]:
    """`(train, test)` — `n` apportioned across `[1 - frac, frac]`.

    **One arithmetic for the split, and two callers**: `validate._check_holdout`
    refuses a `frac` that apportions the test side zero units, and
    `holdout_for`'s unclustered draw cuts the shuffled roster at exactly these
    sizes. Two derivations of the same number would mean `validate` approving a
    `frac` whose realized test side the draw then sized differently — the
    validate-clean-then-disagree gap `arms_of`'s own docstring is written to
    prevent a third instance of.

    `_apportion`'s largest-remainder rule, which `assignment_for`'s `random`
    branch already uses for `assign.<axis>.ratio`: each side's exact share
    floors and the remainder goes to the larger fractional part. Every size is
    within one of its exact proportional share, which is the strongest claim a
    fraction that doesn't divide `n` supports.

    **A test size of 0 is possible and is the caller's to refuse.** Two units at
    `frac: 0.2` gives `(2, 0)`. Nothing here raises: `validate` holds the
    declared `frac` and the roster a message has to name, so the refusal lives
    there — `_apportion`'s own convention, one construction over.
    """
    train, test = _apportion(n, [1.0 - frac, frac])
    return train, test


def holdout_values_fault(roster: UnitList, column: str) -> str | None:
    """How `column` fails to resolve to exactly `train` and `test` over this
    roster — as a message — or `None` when it does not fail.

    **One authority, two reporting surfaces**, which is
    `stratum_varies_within_cluster`'s own arrangement: `validate._check_holdout`
    collects this as `E-DATA-HOLDOUT-VALUES` and `holdout_for` raises it under
    the same code, so the two cannot come to disagree about either the verdict
    or the wording. Two independent wrappings of one raise is exactly how two
    messages drift apart.

    The **verdict** is `arms_of`'s, unchanged: that function stays the authority
    for a column-read partition and promises set equality in both directions —
    no unit's value outside the pair, and neither literal left holding nothing.
    Only the **wording** is rebuilt here, because `arms_of`'s own message names
    an arm and an axis's declared levels and would send a holdout's reader to
    the wrong section.

    Returns a message rather than raising, so `validate` — contracted never to
    raise — can report it beside every other finding, and so `holdout_for` can
    raise it with the code that belongs to a holdout rather than to an arm.
    """
    try:
        arms_of(roster, column, HOLDOUT_LEVELS)
    except ContractError:
        seen = sorted(
            {str(u.attributes[column]) for u in roster if column in u.attributes}
        )
        missing = [lit for lit in HOLDOUT_LEVELS if lit not in seen]
        return (
            f"the holdout column {column!r} has values {', '.join(seen) or 'none'} over "
            f"this roster — a `by_attribute` holdout needs exactly "
            f"`{HOLDOUT_LEVELS[0]}` and `{HOLDOUT_LEVELS[1]}`"
            + (f", and {', '.join(missing)} names no unit" if missing else "")
            + ". A holdout declares no levels for core to read an order out of, so the "
            "two names are fixed rather than inferred from the data"
        )
    return None
```

  (b) In `src/publishable/units.py`, correct `stratum_varies_within_cluster`'s docstring. Replace

```python
    decides which declaration to name (`reference.md` § Validation, rows *Fold
    strata survive clustering* and *Holdout strata survive clustering*, which is why
    this returns a fault rather than raising one code).
```

  with

```python
    decides which declaration to name — **four callers today, under four codes**:
    `E-DATA-ASSIGN-STRATIFY-VARIES`, `E-REPL-FOLD-STRATIFY-VARIES`,
    `E-STATS-RESAMPLE-STRATIFY-VARIES` and `E-DATA-HOLDOUT-STRATIFY-VARIES`,
    answering to `reference.md` § Validation's *Allocation strata survive
    clustering*, *Fold strata survive clustering*, *Resample strata survive
    clustering* and *Holdout strata survive clustering*. That is why this returns
    a fault rather than raising one code: a code chosen here would be right for
    one caller and wrong for three.
```

  (c) In `src/publishable/validate.py`, add `holdout_sizes` and `holdout_values_fault` to the `publishable.units` import list — **not** `arms_of`, which stays behind `holdout_values_fault` so `validate` has no second way to ask the question — and append to `_check_holdout` — first grow the docstring's enumeration to ten by inserting after the `E-DATA-HOLDOUT-FOLD` bullet:

```python
    - `E-DATA-HOLDOUT-VALUES` — **reads the roster:** under `by_attribute`, the
      named column resolving to exactly `train` and `test`.
    - `E-DATA-HOLDOUT-STRATIFY-VARIES` — **reads the roster:** a stratum that
      varies within a `cluster_by` cluster.
    - `E-DATA-HOLDOUT-EMPTY` — **reads the roster:** a `random`, unstratified,
      unclustered split that apportions the test side zero units.

    **Three of the ten read `roster`**, and each carries its own
    `roster is not None` guard rather than leaning on a caller — `_check_resample`'s
    stated convention.
```

  then append to the body:

```python
    # `by_attribute`'s two literals, through `units.holdout_values_fault` — one
    # authority for both the verdict (`arms_of`'s set equality) and the wording,
    # so this collected finding and the one `holdout_for` raises at run time
    # cannot drift apart. `stratum_varies_within_cluster`'s own arrangement:
    # the function returns a fault and each caller decides whether to collect
    # it or raise it.
    if (
        method == "by_attribute"
        and roster is not None
        and isinstance(declared_from, str)
        and declared_from
    ):
        fault = holdout_values_fault(roster, declared_from)
        if fault is not None:
            c.error("E-DATA-HOLDOUT-VALUES", "data.units.holdout.from", fault)

    # *Holdout strata survive clustering*, through the fourth
    # `stratum_varies_within_cluster` call site. Reusing that function rather
    # than minting a second notion of constancy is the point: whole clusters go
    # to one side of a holdout, exactly as they do to one side of a fold, so
    # the holdout inherits the rule rather than inventing one. Names already
    # refused above are skipped, so a config with one undeclared and one
    # varying stratum gets one finding for each rather than two for one.
    if roster is not None and cluster_by:
        for name in strata:
            if not isinstance(name, str) or name not in declared_names:
                continue  # already refused above
            try:
                offender = stratum_varies_within_cluster(roster, cluster_by, name)
            except ContractError:
                # `clusters_of` refuses a unit carrying no cluster value
                # (`E-DATA-CLUSTER-UNKNOWN`), reported beside this by
                # `_check_cluster_by` or by `_check_units`' own resolution. This
                # module collects rather than raises.
                break
            if offender is not None:
                cluster, values = offender
                c.error(
                    "E-DATA-HOLDOUT-STRATIFY-VARIES",
                    "data.units.holdout.stratify_by",
                    f"names {name!r}, which varies within `{cluster_by}` {cluster} — it "
                    f"carries {', '.join(values)}. A cluster is indivisible and goes "
                    "whole to one side of the split, so a cluster carrying two stratum "
                    "values can be dealt to neither; stratify on an attribute constant "
                    "within a cluster",
                )

    # The zero-size test partition, sited exactly as *Every arm draws units* is:
    # **the unstratified, unclustered `random` draw only**. A stratified or
    # clustered split apportions inside each stratum or moves whole clusters,
    # so the realized test size is not this arithmetic's answer and only the
    # draw knows what it moved — that one is checked where the run performs it.
    # `by_attribute` needs nothing here: `arms_of` above already refuses a
    # literal no unit's value names, which is an empty side by another name,
    # and a second refusal of one fault under two codes is what this omission
    # avoids.
    if (
        method == "random"
        and roster is not None
        and not strata
        and not cluster_by
        and isinstance(declared_frac, (int, float))
        and not isinstance(declared_frac, bool)
        and 0.0 < float(declared_frac) < 1.0
    ):
        _train_size, test_size = holdout_sizes(len(roster), float(declared_frac))
        if test_size == 0:
            c.error(
                "E-DATA-HOLDOUT-EMPTY",
                "data.units.holdout.frac",
                f"is {declared_frac} over {len(roster)} resolved units, which apportions "
                "the test side zero of them — every metric would be over nothing. Widen "
                "`frac`, or resolve a larger roster",
            )
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Then the docstring sweep: `grep -rn "Fold strata survive clustering" src/ tests/ docs/` — every site claiming `stratum_varies_within_cluster` answers to *two* rows must now say four. Prove the sweep can fail by running it against `Holdout strata survive clustering`, which must return hits.

- [ ] **Step 5: Mutate** — three.

  (a) In `src/publishable/units.py`, change `holdout_sizes`'s body to `return _apportion(n, [frac, 1.0 - frac])[0], _apportion(n, [frac, 1.0 - frac])[1]` — the weights reversed. Run `uv run pytest tests/test_units.py -k holdout_sizes tests/test_validate.py -k "apportions_the_test or larger_roster"`. `test_holdout_sizes_...` must **FAIL** on `holdout_sizes(10, 0.2) == (8, 2)`, and `test_a_holdout_that_apportions_the_test_side_no_units_is_refused` must **FAIL** too: 4 units against reversed weights apportions `(0, 4)`, so the *test* side holds everything and the refusal never fires. `test_the_same_frac_over_a_larger_roster_is_accepted` is **not** expected to move — 40 units gives `(4, 36)` either way and neither side is empty — which is why it is named here as the branch that cannot discriminate rather than left for an implementer to puzzle over. Revert in place; re-run.

  (b) In `src/publishable/validate.py`, delete `and not cluster_by` from the empty-test-partition guard. `test_the_empty_test_partition_refusal_is_not_reported_for_a_clustered_split` must **FAIL**. Revert in place; re-run.

  (c) In `src/publishable/units.py`, inside `holdout_values_fault`, change `arms_of(roster, column, HOLDOUT_LEVELS)` to `arms_of(roster, column, sorted({str(u.attributes.get(column)) for u in roster}))` — the "two values sorted" reading task 2 rejected. `test_a_by_attribute_holdout_column_must_hold_exactly_train_and_test` must **FAIL** on the `_SPLIT_ROSTER_AB` and `_SPLIT_ROSTER_THREE` rows, since every observed value is now a declared level — and on `_SPLIT_ROSTER_ONE_SIDED` too, whose sorted set has one member that every unit matches. **All three rows must fail**, which is the check that the mutation reaches the rule rather than one fixture's arithmetic. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: refuse a holdout column, stratum or frac the roster cannot honour`.

---

## Task 8: The shared cells refusal — one check site, two codes, and H3c-3 named as its owner

**Files:** Modify `src/publishable/validate.py`, `docs/experimental-designs.md`, `docs/reference.md`, `docs/superpowers/spec-defects.md`. Modify (append) `tests/test_validate.py`.

**Interfaces:**
- Consumes: `validate_config`'s `doc` and `units_decl`.
- Produces:

```python
def _check_evaluation_split_cells(doc: dict[str, Any], units: dict[str, Any], c: Collector) -> None:
```

  called from `validate_config` immediately after `_check_holdout`. Reports `E-DATA-HOLDOUT-CELLS` and/or `E-REPL-FOLD-CELLS`.

**This is H3c-3's own 3-task refusal and H3d's, merged into one.** The two faults are one fault — *a roster-wide evaluation split beside a cell structure* — both knowable from the declarations alone, both live at `78bb794`. Probed at 15 units split 12/3 by arm: `fold_basis` answers **15** over the whole roster, so `k: 5` is permitted and arm `b` gets **two empty folds**; a roster-wide `frac: 0.2` gives arm `b` **zero test units**. `groups` + `between` + `fold k=5` **validates clean today**.

**Refuse, not disclose.** The disclosure route is `allocation.json` recording a truthful `train`/`test` membership that a reader would have to cross against the arms list by hand to see the imbalance — the silently-wrong class. The repo's precedent is to refuse the *combination* while honouring both *declarations*: `E-DATA-WEIGHT-CONTRAST`, `E-DATA-CLUSTER-CONTRAST`, `E-DATA-ALLOCATION-CONTRAST`, `E-DATA-ASSIGN-BLOCKED-CLUSTER`.

**One check site is not negotiable.** Two codes for the two split kinds is defensible; a second *site* is how the two answers come to disagree.

**Cost against the outside evidence: zero, re-verified.** All nine configs in `docs/feasibility-llm-growth-studies.md` declare one roster, `allocation: within`, no `sweep.groups`, and `seed` or `batch` repeats. And no section of `experimental-designs.md` declares `allocation: between` **and** a `fold` repeat: it declares `between` in three sections and a `fold` in two, with no overlap.

**Two false present-tense claims this task marks honestly rather than adding a third to.** `experimental-designs.md`'s "folds and holdouts are drawn *within* each cell" is false for `fold` at `78bb794` and would become false for `holdout` the moment this slice lands. `reference.md` § Cross-validation's "Under `allocation: between`, folds are drawn within each cell" is the same sentence one file over. (§ A fixed holdout split's own fourth interaction was already rewritten in task 2 — do not rewrite it again; **read it first** and make these two agree with what it now says.)

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
_CELL_ROSTER = "patient_id,arm\n" + "".join(
    f"p{i},{'b' if i >= 12 else 'a'}\n" for i in range(15)
)
_ARM_GROUP_AXIS = [{"by": "arm", "levels": ["a", "b"]}]


def _cells(units_extra: dict, *, fold: bool) -> dict:
    """A `between` design with an `arm` group axis, plus whichever evaluation
    split the caller asked for. 15 units, 12 in arm `a` and 3 in arm `b` — the
    exact shape both defects were reproduced at."""
    units = {
        "from": "index.csv", "key": "patient_id", "attributes": ["arm"],
        "allocation": "between", "assign": {"arm": {"method": "by_attribute"}},
        **units_extra,
    }
    out: dict = {"data.units": units, "sweep": {"groups": _ARM_GROUP_AXIS}}
    if fold:
        out["replication"] = {
            "repeats": [{"kind": "fold", "k": 5}], "order": "as_declared"
        }
    return out


def test_a_fold_beside_a_cell_structure_is_refused(write_config, tmp_path):
    """A LIVE defect at `78bb794`: this config validates clean, and `k: 5` is
    permitted because `fold_basis` answers 15 over the whole roster while arm
    `b` holds 3 — so arm `b` gets two folds holding none of its units.

    Refused rather than disclosed: `sweep.yaml`'s partitions would record the
    membership truthfully and no reader crosses it against the arms list by
    hand."""
    (tmp_path / "input" / "index.csv").write_text(_CELL_ROSTER)
    found = codes(write_config(_cells({}, fold=True)))
    assert "E-REPL-FOLD-CELLS" in found


def test_a_holdout_beside_a_cell_structure_is_refused(write_config, tmp_path):
    """The same fault, the same check site, the other split kind: a roster-wide
    `frac: 0.2` over 15 units gives arm `b` zero test units."""
    (tmp_path / "input" / "index.csv").write_text(_CELL_ROSTER)
    found = codes(
        write_config(_cells({"holdout": {"method": "random", "frac": 0.2}}, fold=False))
    )
    assert "E-DATA-HOLDOUT-CELLS" in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_both_split_kinds_beside_a_cell_structure_report_both_codes(
    write_config, tmp_path
):
    """One check site, two codes — asserted together because a site that
    returned after the first finding would pass both tests above and still
    hide half the fault. `E-DATA-HOLDOUT-FOLD` rides along, which is correct:
    the two declarations are also mutually exclusive with each other."""
    (tmp_path / "input" / "index.csv").write_text(_CELL_ROSTER)
    found = codes(
        write_config(_cells({"holdout": {"method": "random", "frac": 0.2}}, fold=True))
    )
    assert "E-DATA-HOLDOUT-CELLS" in found
    assert "E-REPL-FOLD-CELLS" in found


def test_allocation_between_alone_triggers_the_refusal_without_a_group_axis(
    write_config, tmp_path
):
    """`allocation: between` and a non-empty `sweep.groups` are two spellings
    of the same cell structure, and EITHER is enough. Without this row a check
    reading only `sweep.groups` passes every test above."""
    (tmp_path / "input" / "index.csv").write_text(_CELL_ROSTER)
    overrides = _cells({"holdout": {"method": "random", "frac": 0.2}}, fold=False)
    overrides["sweep"] = {}
    assert "E-DATA-HOLDOUT-CELLS" in codes(write_config(overrides))


def test_a_group_axis_alone_triggers_the_refusal_without_between(
    write_config, tmp_path
):
    """The other half of the same pair: without this row a check reading only
    `allocation` passes every test above."""
    (tmp_path / "input" / "index.csv").write_text(_CELL_ROSTER)
    overrides = _cells({"holdout": {"method": "random", "frac": 0.2}}, fold=False)
    overrides["data.units"]["allocation"] = "within"
    assert "E-DATA-HOLDOUT-CELLS" in codes(write_config(overrides))


def test_an_evaluation_split_without_a_cell_structure_is_not_refused(
    write_config, tmp_path
):
    """The control, and it must report something. `allocation: within`, no
    `sweep.groups` — the shape all nine feasibility configs declare, and the
    shape this refusal must leave alone."""
    (tmp_path / "input" / "index.csv").write_text(_CELL_ROSTER)
    found = codes(
        write_config(
            _holdout({"method": "random", "frac": 0.2}, attributes=["arm"])
        )
    )
    assert "E-DATA-HOLDOUT-CELLS" not in found
    assert "E-REPL-FOLD-CELLS" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k "cell_structure or triggers_the_refusal or without_a_cell" -x`. Every test asserting a new code fails; the control passes with its companion. **Before implementing, confirm the live defect by hand**: run the fold config through `validate_config` and check it reports no error at all today — that is the defect this task closes, and seeing it is what stops the refusal being written against a fault that was never there.

- [ ] **Step 3: Implement** —

  (a) In `src/publishable/validate.py`, add after `_check_holdout`:

```python
def _check_evaluation_split_cells(
    doc: dict[str, Any], units: dict[str, Any], c: Collector
) -> None:
    """A roster-wide evaluation split beside a cell structure — refused, for
    both split kinds, from one site.

    **The two faults are one fault**, which is why they share a site: a
    `data.units.holdout` and a `{kind: fold}` level each partition the WHOLE
    roster once, and `data.units.allocation: between` or a non-empty
    `sweep.groups` divides that same roster into cells. A partition drawn
    across the cells rather than within them gives them unequal test sizes and,
    once the split is fine enough, a cell holding none of its own units at all
    — a cell-level metric computed from nothing.

    **Two codes, one site.** `E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS`
    send a reader to the declaration they actually wrote; a single code would
    name one of the two and be wrong for the other. A second check *site* is
    what this deliberately does not have — that is how two answers to one
    question come to disagree.

    **Refused rather than disclosed.** The disclosure route would be
    `allocation.json` and `sweep.yaml` recording a truthful membership whose
    imbalance is visible only to a reader who crosses it against the arms list
    by hand — the silently-wrong class. The repo's own precedent is to refuse
    the COMBINATION while honouring both DECLARATIONS, and to route it:
    `E-DATA-WEIGHT-CONTRAST`, `E-DATA-CLUSTER-CONTRAST`,
    `E-DATA-ALLOCATION-CONTRAST`, `E-DATA-ASSIGN-BLOCKED-CLUSTER`.

    **The `fold` half closes a defect that is live at this commit**, not a
    hypothetical: `replication._fold_k` bounds `k` against `units.fold_basis`
    over the WHOLE roster, so 15 units split 12/3 by arm permit `k: 5` and
    leave the 3-unit arm with two empty folds. Nothing else scheduled closes
    it sooner, which is why it ships here rather than with the slice that owns
    cells.

    **The route is a design that draws within each cell**, which this build
    does not have. `docs/superpowers/spec-defects.md` carries the entry and
    names **H3c-3** as the owner of this refusal's retirement.

    Knowable from the declarations alone — no roster, no resolution — so this
    takes neither.
    """
    allocation = units.get("allocation")
    groups = (doc.get("sweep") or {}).get("groups")
    cells = allocation == "between" or bool(isinstance(groups, list) and groups)
    if not cells:
        return
    where = (
        "`data.units.allocation: between`"
        if allocation == "between"
        else "a non-empty `sweep.groups`"
    )
    reason = (
        f"is declared beside {where}, which divides the roster into cells. One "
        "roster-wide split across those cells gives them unequal test sizes and, "
        "once it is fine enough, a cell holding none of its own units — a "
        "cell-level metric computed from nothing. Drawing the split within each "
        "cell is the design that lifts this, and it is not built: declare one or "
        "the other, or run each arm as its own run and join them in a `study`"
    )
    if units.get("holdout"):
        c.error("E-DATA-HOLDOUT-CELLS", "data.units.holdout", reason)
    repeats = (doc.get("replication") or {}).get("repeats")
    if isinstance(repeats, list) and any(
        isinstance(level, dict) and level.get("kind") == "fold" for level in repeats
    ):
        c.error("E-REPL-FOLD-CELLS", "replication.repeats", f"declares a `fold` level, which {reason}")
```

  and wire it in `validate_config`, immediately after the `_check_holdout` call:

```python
    _check_holdout(doc, units_decl, roster, usable_cluster, c)
    # One site for both split kinds, deliberately: see this function's own
    # docstring for why a second site is the thing being avoided rather than a
    # cost being paid.
    _check_evaluation_split_cells(doc, units_decl, c)
```

  (b) In `docs/experimental-designs.md`, replace the clause "**folds and holdouts are drawn *within* each cell**" in the paragraph beginning "Every cell is a condition" with:

```markdown
Every cell is a condition, so cells get their own `values` and their own labels — but **not their own evaluation split**: core refuses a `fold` repeat or a [`data.units.holdout`](reference.md#a-fixed-holdout-split) declared beside a cell structure (`E-REPL-FOLD-CELLS`, `E-DATA-HOLDOUT-CELLS`) rather than drawing one roster-wide partition across the cells, which would give them unequal test sizes and, once the split is fine enough, a cell holding none of its own units. Drawing within each cell is the design that lifts the refusal, and it is not built. `limits.min_units_per_cell` is checked per cell, which is where a 2×2 over a fixed roster starts to bite.
```

  (c) In `docs/reference.md` § Cross-validation, replace the paragraph beginning "**Under `allocation: between`, folds are drawn within each cell**" with:

```markdown
**Under `allocation: between`, a `fold` repeat is refused**, not drawn — `E-REPL-FOLD-CELLS`, the same refusal and the same reason [a holdout](#a-fixed-holdout-split) earns under `E-DATA-HOLDOUT-CELLS`. One roster-wide partition would give the cells unequal test sizes and, once `k` approaches the smallest cell's size, a fold holding none of that cell's units at all, which is a cell-level metric computed from nothing. Drawing within each cell is the design that lifts both refusals: `k` would then be bounded by the *smallest* cell's unit count — or its cluster count, when `cluster_by` is declared — and it is not built. Without a cell structure nothing changes: the boundaries are derived once from the design digest, and every condition sees the same ones, which is exactly what paired contrasts need.
```

  (d) In `docs/superpowers/spec-defects.md`, append:

```markdown
## OPEN — an evaluation split cannot be drawn within a cell

`data.units.holdout` and a `{kind: fold}` repeat both partition the whole roster once, and
`data.units.allocation: between` / a non-empty `sweep.groups` divides that same roster into
cells. `reference.md` § A fixed holdout split and `experimental-designs.md` both prescribe
drawing the split **within** each cell. **No build draws one.**

H3d refuses the combination instead, at one site under two codes — `E-DATA-HOLDOUT-CELLS`
and `E-REPL-FOLD-CELLS` — because the `fold` half was a live defect: `replication._fold_k`
bounds `k` against `units.fold_basis` over the whole roster, so 15 units split 12/3 by arm
permitted `k: 5` and left the 3-unit arm with two empty folds, and the config validated
clean. Refusing rather than disclosing follows `E-DATA-ASSIGN-BLOCKED-CLUSTER`'s precedent:
a truthful record of an imbalance no reader crosses by hand is the silently-wrong class.

**Owner of the retirement: H3c-3**, the slice that builds folds and holdouts inside cells.
Re-owner this entry if that slice's scope changes, rather than leaving it pointing at a
closed one.

**Found by:** H3d, Task 8. **Severity:** Was Major for `fold` while open — a validated
config produced empty folds per arm — and is now closed as a refusal rather than as a
capability.
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Then the **documents sweep, by claim not by file**: `grep -rn "within each cell" docs/reference.md docs/experimental-designs.md docs/design-principles.md README.md` — every remaining hit must be a statement this build actually honours, or must name the refusal. Prove the sweep can fail by running it against `each cell`, which returns more. Then the mechanical pass on both edited documents (trailing whitespace, tabs, anchors resolve, `×` not `x`, table rows match headers) and the cross-document pass: check § Mistakes core prevents in `experimental-designs.md` still lists nothing these edits make merely-discouraged rather than structurally impossible.

- [ ] **Step 5: Mutate** — three.

  (a) In `src/publishable/validate.py`, change `cells = allocation == "between" or bool(...)` to `cells = allocation == "between"`. `test_a_group_axis_alone_triggers_the_refusal_without_between` must **FAIL**. Revert in place; re-run.

  (b) Change it to `cells = bool(isinstance(groups, list) and groups)`. `test_allocation_between_alone_triggers_the_refusal_without_a_group_axis` must **FAIL**. Revert in place; re-run.

  (c) Add `return` immediately after the `E-DATA-HOLDOUT-CELLS` `c.error(...)` call. `test_both_split_kinds_beside_a_cell_structure_report_both_codes` must **FAIL** on `E-REPL-FOLD-CELLS`, and `test_a_fold_beside_a_cell_structure_is_refused` must still pass — which is the point: an early `return` is invisible to every single-declaration test, and only the both-declared fixture separates the two readings. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: refuse a roster-wide evaluation split beside a cell structure`.

---

## Task 9: `holdout.from`'s constant-column accessor

**Files:** Modify `src/publishable/units.py`, `src/publishable/validate.py`. Modify (append) `tests/test_units.py`.

**Interfaces:**
- Consumes: `units.CONSTANT_COLUMN_RULES: dict[str, tuple[str, str]]`; `units.collapse_measurements(units, by, collapse, constant=None)`; `units._assign_constant_columns(assign_decl) -> dict[str, str]`.
- Produces: `units._holdout_constant_column(holdout_decl: Any) -> dict[str, str]`, returning at most one entry keyed `holdout.from`; a `CONSTANT_COLUMN_RULES` entry keyed `holdout` (bare, no dot) carrying `E-DATA-HOLDOUT-VARIES`; and its place in `resolve_units`' documented severity ordering.

**Why this exists at all, in the code's own words.** Two comments in `units.py` say so in the present tense at `78bb794`: *"`holdout.from` still is not [reachable]"* and *"`holdout.from` is not reachable through this registry today… nothing in this task builds one."* `CONSTANT_COLUMN_RULES` is what makes `collapse_measurements` refuse a unit whose declared column is **not constant across the rows collapsing into it**. Under `data.units.measurements`, a `by_attribute` holdout reading a column that disagrees between two rows of one unit would silently take whichever row the collapse kept — **a unit assigned to train or test by an accident of row order.** `design-principles.md` § Core vs. plugin lists `holdout.from` beside `assign.from` as parallel namers of an input field, so this is not an invented requirement.

**Why an accessor and not a flat registry entry.** `resolve_units`' flat comprehension indexes `units_decl` by the registry key and filters on `isinstance(..., str)`, so a mapping is dropped before the registry is consulted — verified by probe in an earlier slice. `holdout` is a mapping with its own `from`, so it needs an accessor, the same shape `_assign_constant_columns` is for `assign` but returning **at most one** entry rather than one per axis.

**Gated on `method == "by_attribute"`**, matching `_assign_constant_columns`' own gate and for its reason: under `random` the split is drawn, no column is read, and a `from` that means nothing there is already `E-DATA-HOLDOUT-NO-DRAW`'s finding — raising a run-time `-VARIES` over a column no draw reads would refuse a config no check approves, in the opposite direction.

**The severity ordering, stated rather than left to dict-building order.** `resolve_units` builds `constant` in a fixed order and `collapse_measurements` stops at the first declaration that raises. `assign` is documented as the worst (it decides which *condition* a unit is measured in). This task inserts `holdout` **after `assign` and before the flat pair**, and the entry's docstring must say what that does and does not claim: `holdout.from` and `cluster_by` say the *same* thing about the damage — which side of a split the unit lands on — so the order between them is fixed deterministically here rather than left to an accident, and is **not** a claim that one is worse than the other. `weight_by` stays last, which is the documented ordering.

**Every key in `CONSTANT_COLUMN_RULES` must contain no `.`** — `collapse_measurements` strips a `constant` key back to the segment before its first `.` before indexing the registry. So the registry key is the bare `holdout`, and the `constant` key is the dotted `holdout.from` that the error message names.

**One consequence to sweep.** `validate.py`'s claim that *"`cluster_by`, `weight_by`, and `holdout` are not read by `resolve_units` at all"* becomes false the moment this lands. It is on task 19's owned-sweep list and is fixed **here**, in the task that falsifies it — `CLAUDE.md`: three sweeps in one slice stopped one file short, and one of them "fixed a sentence in `correction.py` and missed the same sentence in the function that falsified it".

- [ ] **Step 1: Write the failing test** — append to `tests/test_units.py`:

```python
_MEASUREMENT_ROWS = [
    {"patient_id": "p1", "read_id": "r1", "split": "train", "value": "1"},
    {"patient_id": "p1", "read_id": "r2", "split": "test", "value": "2"},
    {"patient_id": "p2", "read_id": "r3", "split": "test", "value": "3"},
]


def _units_from_rows(rows, attributes):
    return [
        Unit(key=r["patient_id"], paths=(), attributes={a: r[a] for a in attributes})
        for r in rows
    ]


def test_a_holdout_from_column_varying_within_a_unit_is_refused():
    """A `by_attribute` holdout reading a column that disagrees between two
    rows of one unit would file that unit on whichever side the row the
    collapse kept says — a train/test membership decided by row order.

    `p1` carries `train` and `test`; `p2` carries one value, so the fixture
    also proves the check is per-unit rather than per-roster."""
    units = _units_from_rows(_MEASUREMENT_ROWS, ["read_id", "split", "value"])
    constant = _holdout_constant_column({"method": "by_attribute", "from": "split"})
    assert constant == {"holdout.from": "split"}
    with pytest.raises(ContractError) as exc:
        collapse_measurements(units, "read_id", "first", constant)
    assert exc.value.code == "E-DATA-HOLDOUT-VARIES"
    assert "split" in str(exc.value)


def test_a_constant_holdout_from_column_collapses_cleanly():
    """The positive companion, produced by the code under test: the same
    declaration over rows that AGREE collapses without raising, and the
    surviving unit keeps the value. Without this the test above passes
    identically if the rule refused every `holdout.from`."""
    rows = [dict(r, split="train") for r in _MEASUREMENT_ROWS]
    units = _units_from_rows(rows, ["read_id", "split", "value"])
    collapsed, counts = collapse_measurements(
        units, "read_id", "first",
        _holdout_constant_column({"method": "by_attribute", "from": "split"}),
    )
    assert [u.key for u in collapsed] == ["p1", "p2"]
    assert [u.attributes["split"] for u in collapsed] == ["train", "train"]
    assert counts == [2, 1]


@pytest.mark.parametrize(
    "decl",
    [
        None,
        {},
        "nonsense",
        {"method": "random", "frac": 0.2},
        {"method": "random", "frac": 0.2, "from": "split"},
        {"method": "by_attribute"},
        {"method": "by_attribute", "from": ""},
        {"method": "by_attribute", "from": 7},
    ],
    ids=["absent", "empty", "not a mapping", "random", "random with a stray from",
         "by_attribute with no from", "empty from", "non-string from"],
)
def test_the_holdout_accessor_resolves_no_column_for_these(decl):
    """It resolves a column or it does not; it never reports a malformed
    declaration. `E-DATA-HOLDOUT-METHOD`, `-FROM` and `-NO-DRAW` are
    `validate`'s findings to raise, not a `ContractError` from a run that
    resolution has no path to report through.

    The `random with a stray from` row is the load-bearing one: the gate is on
    the METHOD, so a drawn split whose declaration happens to carry a `from`
    still reads no column — a run that raised `E-DATA-HOLDOUT-VARIES` there
    would be refusing a config over a column its draw never reads."""
    assert _holdout_constant_column(decl) == {}


def test_the_holdout_rule_is_checked_after_assign_and_before_the_flat_pair():
    """`constant`'s iteration order decides which code a unit violating more
    than one declaration gets, and `collapse_measurements` stops at the first.
    Pinned as an order rather than left to dict-building accident.

    The fixture makes ONE unit violate `assign`, `holdout` and `cluster_by`
    at once — three declarations, so the three candidate orderings each give a
    different answer, which two declarations could not distinguish."""
    rows = [
        {"patient_id": "p1", "read_id": "r1", "split": "train", "arm": "a", "site": "s1"},
        {"patient_id": "p1", "read_id": "r2", "split": "test", "arm": "b", "site": "s2"},
    ]
    units = _units_from_rows(rows, ["read_id", "split", "arm", "site"])
    constant = _assign_constant_columns({"arm": {"method": "by_attribute"}})
    constant.update(_holdout_constant_column({"method": "by_attribute", "from": "split"}))
    constant.update({"cluster_by": "site"})
    with pytest.raises(ContractError) as exc:
        collapse_measurements(units, "read_id", "first", constant)
    assert exc.value.code == "E-DATA-ASSIGN-VARIES"

    # Remove the highest-priority declaration and the NEXT one reports — which
    # is what proves the order rather than merely that `assign` reports.
    without_assign = _holdout_constant_column(
        {"method": "by_attribute", "from": "split"}
    )
    without_assign.update({"cluster_by": "site"})
    with pytest.raises(ContractError) as exc2:
        collapse_measurements(units, "read_id", "first", without_assign)
    assert exc2.value.code == "E-DATA-HOLDOUT-VARIES"
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_units.py -k "holdout_from or holdout_accessor or holdout_rule" -x`. Every test fails on `ImportError` for `_holdout_constant_column`. Add it to `tests/test_units.py`'s `publishable.units` import list along with `_assign_constant_columns`, `collapse_measurements`, `Unit` and `ContractError` if any is missing, then re-run: the accessor tests now fail on the assertion instead.

- [ ] **Step 3: Implement** —

  (a) In `src/publishable/units.py`, add the registry entry. Insert it into `CONSTANT_COLUMN_RULES` **between** `"assign"` and the flat pair is not possible (a dict literal has one order) — insert it after `"assign"`:

```python
    "holdout": (
        "E-DATA-HOLDOUT-VARIES",
        "A holdout decides which side of a train/test split the unit lands on, "
        "so collapsing disagreeing rows would leave that decision to the order "
        "the rows happen to be in — a unit evaluated against a model it was "
        "fitted on, or held back from one it should have been evaluated by. "
        "Which side of a split a unit is on is a fact about the unit, not "
        "about the measurement",
    ),
```

  and extend that registry's docstring, replacing the sentence

```python
**`holdout.from` is not reachable through this registry today** — it is a single key under a fixed mapping, not one per
declared axis, so it needs its own accessor the same shape `_assign_constant_columns`
is for `assign`, and nothing in this task builds one.
```

  with

```python
**`holdout.from` reaches this registry through its own accessor**,
`_holdout_constant_column` below — a single key under a fixed mapping rather
than one per declared axis, so it could not use `_assign_constant_columns`'s
`axis` loop, and it could not be a flat entry either: `resolve_units`'
comprehension filters on `isinstance(..., str)` and drops a mapping before the
registry is consulted. Its `constant` key is the dotted `holdout.from`, for the
message, and the lookup strips it back to the bare `holdout` here, exactly as
it strips `assign.<axis>.from` back to `assign`.
```

  (b) Add the accessor, immediately after `_assign_constant_columns`:

```python
def _holdout_constant_column(holdout_decl: Any) -> dict[str, str]:
    """`holdout.from` when a `by_attribute` holdout declares one — at most one
    entry, keyed by the literal dotted path a reader would look for.

    `_assign_constant_columns`' sibling, one declaration over, and narrower for
    the reason that one is narrow: this function's only job is deciding which
    column, if any, a holdout's constancy has to hold — not reporting a
    malformed declaration. An absent block, a non-mapping block, a missing
    `from`, an empty `from` and a non-`str` `from` are shapes
    `validate._check_holdout` reports (`E-DATA-HOLDOUT-METHOD`,
    `E-DATA-HOLDOUT-FROM`) and this function is silent on, each because it
    resolves to no column to check: those are `validate`'s findings to raise,
    not a `ContractError` from a run that resolution has no path to report
    through.

    **Gated on `method == "by_attribute"`**, matching `_assign_constant_columns`'
    own gate and for its reason: `random` draws the split rather than reading
    one, so no column is read, and a `from` declared beside it means nothing —
    already refused as `E-DATA-HOLDOUT-NO-DRAW`. Without this gate a drawn
    split whose declaration carried a stray `from` naming a column that varies
    within a unit's rows would raise `E-DATA-HOLDOUT-VARIES` over a column its
    draw never reads, which is the validate-clean-then-crash gap in the
    opposite direction: a config no check approves, refused anyway by a rule
    that assumed a read `by_attribute` alone performs.

    **There is no axis-name default**, unlike `assign.<axis>.from`: a holdout
    has no axis name, which is why `validate` requires `from` outright under
    `by_attribute` rather than defaulting it.
    """
    if not isinstance(holdout_decl, dict):
        return {}
    if holdout_decl.get("method") != "by_attribute":
        return {}
    declared_from = holdout_decl.get("from")
    if isinstance(declared_from, str) and declared_from:
        return {"holdout.from": declared_from}
    return {}
```

  (c) In `resolve_units`, insert the accessor's result between `assign`'s and the flat pair's, and rewrite the stale comment. Replace

```python
        constant = _assign_constant_columns(units_decl.get("assign"))
        constant.update(
```

  with

```python
        constant = _assign_constant_columns(units_decl.get("assign"))
        # `holdout.from` next, between `assign` and the flat pair. `assign` is
        # documented as the worst of the family (§ Allocation: a mis-collapsed
        # arm decides which CONDITION a unit is measured in), so it stays
        # first. `holdout.from` and `cluster_by` say the same thing about the
        # damage — which side of a split the unit lands on — so the order
        # BETWEEN those two is fixed here deterministically rather than left to
        # an accident of dict-building, and is **not** a claim that one fault
        # is worse than the other. `weight_by` stays last, which is the
        # documented ordering.
        constant.update(_holdout_constant_column(units_decl.get("holdout")))
        constant.update(
```

  and in the long comment above it, replace

```python
        # now reachable; **`holdout.from` still is not** — its shape is a single
        # key under a fixed mapping, not one-per-declared-axis, and needs its own
        # accessor rather than this one's `axis` loop.
```

  with

```python
        # now reachable; **`holdout.from` reaches it through
        # `_holdout_constant_column`** — its shape is a single key under a
        # fixed mapping, not one-per-declared-axis, so it needed its own
        # accessor rather than this one's `axis` loop.
```

  (d) In `src/publishable/validate.py`, fix the sentence this task falsifies. Replace

```python
    No other `-UNSUPPORTED` field is skipped on: `allocation`, `assign`,
    `cluster_by`, `weight_by`, and `holdout` are not read by
    `resolve_units` at all, so resolving against a real table or glob alongside
    one of those refusals adds a genuine, independent finding
```

  with

```python
    No other `-UNSUPPORTED` field is skipped on: `allocation` and `assign`'s
    method are not read by `resolve_units` at all, and the three that ARE read
    — `cluster_by`, `weight_by`, and (under `by_attribute`) `holdout.from` —
    are read only where a `data.units.measurements` collapse could file a unit
    by row order, which is an independent fault of its own. So resolving
    against a real table or glob alongside one of those refusals adds a
    genuine, independent finding
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Then sweep by claim: `grep -rn "not read by" src/publishable/*.py` and `grep -rn "holdout.from" src/ docs/` — every present-tense claim that `holdout.from` is unreachable must be gone. Prove the sweep can fail by running it against `_holdout_constant_column`, which must return hits.

- [ ] **Step 5: Mutate** — two.

  (a) In `src/publishable/units.py`, delete the `if holdout_decl.get("method") != "by_attribute": return {}` gate. Run `uv run pytest tests/test_units.py -k holdout_accessor`. The `random with a stray from` row must **FAIL**. Revert in place; re-run.

  (b) Move `constant.update(_holdout_constant_column(...))` to **after** the flat-pair `constant.update({...})` block. Run `uv run pytest tests/test_units.py -k holdout_rule`. `test_the_holdout_rule_is_checked_after_assign_and_before_the_flat_pair` must **FAIL** on its second assertion (`E-DATA-CLUSTER-VARIES` now wins over `E-DATA-HOLDOUT-VARIES`). Revert in place; re-run. **Check before trusting this**: the two branches genuinely differ only because the fixture's one unit violates `cluster_by` *and* `holdout.from` at once — a fixture violating only one cannot discriminate, which is why the test builds one that violates three.

- [ ] **Step 6: Commit** — `feat: give holdout.from its own constant-column accessor`.

---

## Task 10: `units.holdout_for`, construction 1 — the unclustered draw and the column read

**Files:** Modify `src/publishable/units.py`. Modify (append) `tests/test_units.py`.

**Interfaces:**
- Consumes: `units.holdout_sizes(n, frac) -> tuple[int, int]`, `units.holdout_values_fault(roster, column) -> str | None` and `units.HOLDOUT_LEVELS` (all task 7); `units.arms_of(roster, column, levels)`; `units.ArmPlan`'s shape as the model.
- Produces:

```python
@dataclass(frozen=True)
class HoldoutPlan:
    train: tuple[str, ...]
    test: tuple[str, ...]
    seed: int | None
    strata: tuple[str, ...]


def holdout_for(
    roster: UnitList,
    block: Mapping[str, Any] | None,
    *,
    seed: int,
    clusters: Mapping[str, str] | None = None,
) -> HoldoutPlan:
```

**`seed` is a required keyword argument and this function never derives one.** Task 12 builds `holdout_seed_for` as the single producer, and task 13 composes the two in `cli.command_run`. A function that both draws and derives is two things to get wrong inside one; `_assign_whole_clusters_by_ratio` taking an `rng` rather than a seed is the same separation one level down.

**The single producer, and the reason it is a pure function.** `validate` has to ask "which units are in the test partition" of the same declaration `cli.command_run` asks it of — task 16's `limits.min_clusters` warning is exactly that question — so the draw cannot live in the runner. `assignment_for`'s own docstring makes this argument verbatim for arms and it transfers.

**Fail-closed on the method: an allowlist, not a denylist.** Any method other than the two raises `NotImplementedError`. `validate` already refuses an out-of-enum method (`E-DATA-HOLDOUT-METHOD`), and the allowlist is what stops a *third* method added to `HOLDOUT_METHODS` and to nothing else from validating clean and then silently partitioning.

**At this commit the clustered and stratified paths raise `NotImplementedError`** and task 11 realizes them. Write that message as what is true at this commit — "not realized at this commit" — not as a permanent refusal.

**`by_attribute` records no seed and no strata**, `ArmPlan`'s own convention: it reads a partition the data already holds, so recording a seed would be a false record of a draw that never happened.

**The zero-size refusal is on BOTH sides.** `validate` (task 7) refuses a zero test side, but it does not refuse a zero *train* side: 2 units at `frac: 0.9` apportions `(0, 2)`. Both are refused here, under `E-DATA-HOLDOUT-EMPTY`, `assignment_for`'s own posture — the draw holds the realized sizes and is the last place that can see them.

- [ ] **Step 1: Write the failing test** — append to `tests/test_units.py`:

```python
def _roster(n, **attrs_by_index):
    """`n` units keyed `u0..u{n-1}`, each carrying whatever the caller maps."""
    return UnitList(
        [
            Unit(key=f"u{i}", paths=(),
                 attributes={k: v(i) for k, v in attrs_by_index.items()})
            for i in range(n)
        ]
    )


def test_an_unclustered_holdout_cuts_the_shuffled_roster_at_the_apportioned_sizes():
    """`_apportion` + one shuffle + consecutive slices — `assignment_for`'s
    `random` branch, one declaration over. The realized membership is pinned as
    a literal derived by RUNNING this, not by predicting it: a predicted
    membership that happened to match a wrong construction is how a 13-unit
    apportionment matched a reverse-order mutant by coincidence in an earlier
    slice.

    Fill these two literals in during Step 3 by printing the actual result."""
    plan = holdout_for(_roster(10), {"method": "random", "frac": 0.2}, seed=1234)
    assert len(plan.train) == 8 and len(plan.test) == 2
    assert set(plan.train) | set(plan.test) == {f"u{i}" for i in range(10)}
    assert not set(plan.train) & set(plan.test)
    assert plan.seed == 1234
    assert plan.strata == ()
    # PINNED LITERALS — replace with what the implementation actually returns.
    assert plan.train == ("REPLACE",)
    assert plan.test == ("REPLACE",)


def test_the_same_seed_and_roster_draw_the_same_holdout_and_a_different_seed_does_not():
    """Determinism, and the positive companion that keeps it from being
    vacuous: a different seed must give a DIFFERENT partition, or a draw that
    ignored the seed entirely would pass the first assertion alone."""
    a = holdout_for(_roster(20), {"method": "random", "frac": 0.25}, seed=7)
    b = holdout_for(_roster(20), {"method": "random", "frac": 0.25}, seed=7)
    c = holdout_for(_roster(20), {"method": "random", "frac": 0.25}, seed=8)
    assert a.test == b.test
    assert a.test != c.test


def test_a_by_attribute_holdout_reads_the_column_and_records_no_draw():
    """Read through `arms_of`, the single authority for a column-read
    partition — so roster order is preserved and set equality is enforced by
    the same function an arm assignment uses. No seed and no strata are
    recorded, `ArmPlan`'s own convention: reading a partition the data holds is
    not drawing one."""
    roster = _roster(10, split=lambda i: "test" if i % 5 == 0 else "train")
    plan = holdout_for(
        roster, {"method": "by_attribute", "from": "split"}, seed=1234
    )
    assert plan.test == ("u0", "u5")
    assert plan.train == ("u1", "u2", "u3", "u4", "u6", "u7", "u8", "u9")
    assert plan.seed is None
    assert plan.strata == ()


def test_a_by_attribute_holdout_over_a_column_that_is_not_the_two_literals_raises():
    """The run-time half of `E-DATA-HOLDOUT-VALUES`, through `arms_of`'s own
    set equality. `validate` refuses this first; the draw refuses it too rather
    than partitioning on whatever it finds."""
    roster = _roster(10, split=lambda i: "A" if i % 2 else "B")
    with pytest.raises(ContractError) as exc:
        holdout_for(roster, {"method": "by_attribute", "from": "split"}, seed=1)
    assert exc.value.code == "E-DATA-HOLDOUT-VALUES"


@pytest.mark.parametrize(
    "n,frac,empty_side",
    [(2, 0.2, "test"), (2, 0.9, "train")],
    ids=["the test side is apportioned none", "the train side is apportioned none"],
)
def test_a_holdout_that_leaves_a_side_empty_raises(n, frac, empty_side):
    """Both sides, because `validate` refuses only the test one: 2 units at
    `frac: 0.9` apportions `(0, 2)` and would fit a model on nothing.
    `assignment_for`'s posture — the draw holds the realized sizes and is the
    last place that can see them."""
    with pytest.raises(ContractError) as exc:
        holdout_for(_roster(n), {"method": "random", "frac": frac}, seed=1)
    assert exc.value.code == "E-DATA-HOLDOUT-EMPTY"
    assert empty_side in str(exc.value)


@pytest.mark.parametrize("method", ["stratified", "", None, "by_attributes"])
def test_an_unknown_holdout_method_raises_rather_than_falling_back(method):
    """An allowlist, not a denylist of the methods that happen to draw today.
    `validate` refuses an out-of-enum method first; this is what stops a THIRD
    method added to `HOLDOUT_METHODS` and to nothing else from validating clean
    and then silently partitioning on a column."""
    with pytest.raises(NotImplementedError):
        holdout_for(_roster(10), {"method": method, "frac": 0.2}, seed=1)
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_units.py -k "holdout_cuts or same_seed_and_roster or by_attribute_holdout or leaves_a_side_empty or unknown_holdout_method" -x`. Every one fails on `ImportError` for `holdout_for`/`HoldoutPlan`; add both to the test module's import list and re-run.

- [ ] **Step 3: Implement** — in `src/publishable/units.py`, add after `ArmPlan`:

```python
@dataclass(frozen=True)
class HoldoutPlan:
    """`data.units.holdout` **realized** — the two sides as unit keys, plus what
    it took to produce them.

    `ArmPlan`'s sibling and deliberately not the same type: an arm plan is
    `level -> keys` over a declared `levels` tuple, where a holdout's two sides
    are fixed and named, and squeezing one into the other would mean either a
    fabricated axis name or a `levels` field with one legal value.

    - `train` and `test` hold unit keys, never row numbers — a roster that
      gains a unit renumbers rows and would silently repoint every membership
      claim. Every key of the roster appears in exactly one of them.
    - Order is **roster order** under `by_attribute`, which `arms_of` promises,
      and the order the shuffle realized under `random` — recorded rather than
      re-sorted, `ArmPlan`'s own rule, because the record of a draw is the
      draw.
    - `seed` is the seed the draw was realized with, and is `None` under
      `by_attribute`: a method that reads a partition the data already holds
      rather than drawing one, so recording a seed would be a false record of a
      draw that never happened.
    - `strata` is the realized `stratify_by`, in declared order, and is empty
      under `by_attribute` for the reason above and empty under a draw that
      declared none.

    `frozen=True` blocks rebinding an attribute; the two tuples are immutable
    outright, so unlike `ArmPlan.members` there is nothing here a determined
    caller can mutate in place.
    """

    train: tuple[str, ...]
    test: tuple[str, ...]
    seed: int | None
    strata: tuple[str, ...]


def holdout_for(
    roster: UnitList,
    block: Mapping[str, Any] | None,
    *,
    seed: int,
    clusters: Mapping[str, str] | None = None,
) -> HoldoutPlan:
    """`data.units.holdout`, realized — **the single producer** of a
    `HoldoutPlan`.

    A **pure function of its arguments**, `assignment_for`'s reason one
    declaration over: `validate` has to ask "which units are in the test
    partition" of the same declaration `cli.command_run` asks it of — the
    `limits.min_clusters` warning is exactly that question — so the draw cannot
    live in the runner. Two callers, one answer, computed the same way from the
    same inputs.

    **`seed` is required and this function never derives one.** The derivation
    is `holdout_seed_for`'s, and composing them is `cli.command_run`'s: a
    function that both draws and derives is two independent things to get wrong
    inside one, and it would put the derivation out of reach of a test that
    wants to pin a draw against a known seed. The value is recorded on the plan
    under `random` and discarded under `by_attribute`, which draws nothing.

    Dispatches on `block["method"]`, `reference.md` § A fixed holdout split's
    own enum:

    - `by_attribute` reads the two sides out of a column, through `arms_of`
      **unchanged** — that function stays the authority for a column-read
      partition and this one does not re-derive it. The levels it is handed are
      `HOLDOUT_LEVELS`, the fixed `train`/`test` literals, so `arms_of`'s set
      equality in both directions is what refuses a third value, a value naming
      neither, and a literal naming no unit. The refusal goes through
      `holdout_values_fault`, which owns both the verdict and the wording, so
      this raise and `validate._check_holdout`'s collected finding are one
      answer rather than two wrappings of the same raise — `arms_of`'s own
      message names an arm and an axis's declared levels and would send a
      holdout's reader to the wrong section.
    - `random`, unclustered and unstratified, draws one: `holdout_sizes` — the
      same apportionment `validate` approved the `frac` against — then one
      `rng.shuffle` of the whole roster's keys, then two consecutive slices,
      train first. That is `assignment_for`'s `random` branch exactly, and
      deliberately so: one construction, described in one place.
    - **Every other value raises `NotImplementedError`** — an allowlist. Fail
      closed costs nothing, because `validate` already refuses an out-of-enum
      method (`E-DATA-HOLDOUT-METHOD`) before a run reaches here, and it is
      what keeps a *third* method added to `validate.HOLDOUT_METHODS` and to
      nothing else from validating clean and then silently partitioning.

    **A `clusters` mapping and a non-empty `stratify_by` are not realized at
    this commit** and raise `NotImplementedError` rather than being silently
    ignored — an ignored `stratify_by` is a split `validate` called stratified
    and the draw balanced on nothing. `clusters` is a parameter anyway, for
    `assignment_for`'s reason: a caller that already has to hold the cluster
    map must not be told the signature changed under it.

    **Both sides are refused empty**, under `E-DATA-HOLDOUT-EMPTY`.
    `validate._check_holdout` refuses a zero *test* side from the declaration
    and the roster size, and does not refuse a zero *train* side — 2 units at
    `frac: 0.9` apportions `(0, 2)`, which would fit a model on nothing. The
    draw holds the realized sizes and is the last place that can see them,
    which is `assignment_for`'s own posture for a zero-size arm.
    """
    block_map: Mapping[str, Any] = block if isinstance(block, Mapping) else {}
    method = block_map.get("method")
    strata = stratum_names(block_map.get("stratify_by"))
    if strata or clusters is not None:
        raise NotImplementedError(
            "a clustered or stratified `data.units.holdout` is not realized at this "
            "commit — the draw that keeps whole clusters on one side, and the one that "
            "balances the split within each stratum, are not built here. Ignoring "
            "either would be a split `validate` called clustered or stratified and the "
            "draw balanced on nothing"
        )
    if method == "by_attribute":
        column = block_map.get("from")
        if not isinstance(column, str) or not column:
            raise NotImplementedError(
                "`data.units.holdout.method: by_attribute` names no column to read the "
                "split out of; `validate` refuses this as `E-DATA-HOLDOUT-FROM`"
            )
        # `holdout_values_fault` computes the verdict AND the wording, so this
        # raise and `validate._check_holdout`'s collected finding are one
        # answer rather than two wrappings of `arms_of` that drift apart.
        fault = holdout_values_fault(roster, column)
        if fault is not None:
            raise ContractError(fault, code="E-DATA-HOLDOUT-VALUES")
        sides = arms_of(roster, column, HOLDOUT_LEVELS)
        return HoldoutPlan(
            train=tuple(u.key for u in sides[HOLDOUT_LEVELS[0]]),
            test=tuple(u.key for u in sides[HOLDOUT_LEVELS[1]]),
            seed=None,
            strata=(),
        )
    if method == "random":
        frac = block_map.get("frac")
        if not isinstance(frac, (int, float)) or isinstance(frac, bool):
            raise NotImplementedError(
                "`data.units.holdout.method: random` declares no usable `frac`; "
                "`validate` refuses this as `E-DATA-HOLDOUT-FRAC`"
            )
        train_size, test_size = holdout_sizes(len(roster), float(frac))
        if train_size == 0 or test_size == 0:
            side = "train" if train_size == 0 else "test"
            raise ContractError(
                f"`data.units.holdout.frac: {frac}` over {len(roster)} resolved units "
                f"apportions the {side} side zero of them. Every split needs both "
                "sides — the training side has nothing to fit on, or the test side has "
                "nothing to report over; widen or narrow `frac`, or resolve a larger "
                "roster",
                code="E-DATA-HOLDOUT-EMPTY",
            )
        shuffled = [unit.key for unit in roster]
        random.Random(seed).shuffle(shuffled)
        return HoldoutPlan(
            train=tuple(shuffled[:train_size]),
            test=tuple(shuffled[train_size:]),
            seed=seed,
            strata=(),
        )
    raise NotImplementedError(
        f"`data.units.holdout.method: {method!r}` is not realized here — the methods "
        f"this build draws are {', '.join(HOLDOUT_METHODS_REALIZED)}. `validate` "
        "refuses an out-of-enum method as `E-DATA-HOLDOUT-METHOD` before a run reaches "
        "this, and an allowlist is what keeps a method added to that enum and to "
        "nothing else from validating clean and then partitioning on something core "
        "never drew"
    )
```

  where `HOLDOUT_METHODS_REALIZED = ("random", "by_attribute")` is declared beside `HoldoutPlan` — **not** imported from `validate`, which imports `units` and not the reverse.

  Then fill in the two `"REPLACE"` literals in `test_an_unclustered_holdout_cuts_the_shuffled_roster_at_the_apportioned_sizes` by running the function and printing `plan.train` and `plan.test`. Paste what it actually returns.

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — three.

  (a) In `src/publishable/units.py`, swap the slices: `train=tuple(shuffled[train_size:]), test=tuple(shuffled[:train_size])`. Run `uv run pytest tests/test_units.py -k holdout_cuts`. It must **FAIL** on the pinned literals *and* on `len(plan.train) == 8`. Revert in place; re-run.

  (b) Delete the `random.Random(seed).shuffle(shuffled)` line entirely. Run `uv run pytest tests/test_units.py -k "holdout_cuts or same_seed_and_roster"`. `test_the_same_seed_and_roster_draw_the_same_holdout_and_a_different_seed_does_not` must **FAIL** on `a.test != c.test`, and `holdout_cuts` must **FAIL** on its pinned literals. **Both must fail** — if only the pinned-literal test fails, the determinism test cannot see the seed and needs a stronger fixture. Revert in place; re-run.

  (c) Change `arms_of(roster, column, HOLDOUT_LEVELS)` to `arms_of(roster, column, tuple(reversed(HOLDOUT_LEVELS)))`. Run `uv run pytest tests/test_units.py -k by_attribute_holdout_reads`. It must **FAIL** — and check the two branches can differ before believing it: `arms_of` returns a mapping keyed by level, and this function indexes it by `HOLDOUT_LEVELS[0]`/`[1]` rather than by position, so reversing the argument alone is a **no-op** and this mutation is *rejected*. Use instead: change the return to `train=tuple(u.key for u in sides[HOLDOUT_LEVELS[1]]), test=tuple(u.key for u in sides[HOLDOUT_LEVELS[0]])`. `test_a_by_attribute_holdout_reads_the_column_and_records_no_draw` must **FAIL**. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: units.holdout_for — the unclustered draw and the column read`.

---

## Task 11: Construction 2 — whole clusters, strata, and the relation between the two constructions

**Files:** Modify `src/publishable/units.py`. Modify (append) `tests/test_units.py`.

**Interfaces:**
- Consumes: `units._assign_whole_clusters_by_ratio(units, weights, rng, clusters) -> list[list[Unit]]`; `units._stratum_groups(units, names, axis, resolved=None) -> dict[tuple[str, ...], list[Unit]]`; `units.holdout_sizes`; `units.holdout_for` from task 10.
- Produces: the clustered and stratified branches of `holdout_for`, `HoldoutPlan.strata` populated, and — the reason this is its own task — a test that **distinguishes the two constructions from each other**. Also changes `_stratum_groups`' third parameter from `axis: str` to `declaration: str`, carrying the full dotted path.

**Why this is a second task and not a branch inside task 10.** `_assign_whole_clusters_by_ratio` takes a **non-optional** `Mapping` and indexes it directly — unlike its sibling `_assign_whole_clusters`, whose docstring argues at length that `clusters is None` is "a cluster of one per unit, not another path". The ratio primitive has no such branch and no such argument, so the unclustered holdout genuinely **cannot** go through it. These are two constructions with a relation between them, not one call with a flag.

**The relation, stated so a fixture can be built to see it.** With one cluster per unit, the two constructions produce the **same sizes** and, in general, **different membership**. The unclustered path shuffles *unit keys* and cuts two consecutive slices. The clustered path shuffles *cluster names*, sorts largest-first (stable, so with equal sizes the shuffled order survives), then deals each cluster to the bucket with the smallest `counts[i] / weights[i]` — which **interleaves** by ratio rather than slicing. So a singleton-cluster draw and an unclustered draw from the same seed over the same roster are **not** bit-identical, and a fixture that cannot tell them apart proves nothing about either. `CLAUDE.md` records exactly this trap: a cluster fixture where correct and buggy cluster counts were both 3.

**The `_stratum_groups` message is wrong for this caller, and the scoping is wrong that it is harmless.** `_stratum_groups` raises `NotImplementedError` interpolating `data.units.assign.{axis}.stratify_by`. A holdout caller passing `axis="holdout"` would print `data.units.assign.holdout.stratify_by` — a path no config can hold. Fix it by changing the parameter to a **full dotted path** and passing `f"data.units.assign.{axis}.stratify_by"` at the three existing sites and `"data.units.holdout.stratify_by"` here. **Before editing, run `grep -rn "stratify_by. names\|E-DATA-ASSIGN-STRATIFY-FORWARD" tests/ src/`** — a test pinning the old wording must move with it.

**`resolved` is not passed by this caller.** A holdout's `stratify_by` admits only a **unit attribute**, never a `sweep.groups` axis — § Validation's *Stratification attribute exists* says so, and task 8 refuses a holdout beside a group axis anyway. So the argument stays at its default and a name that is not an attribute raises, which is correct: `validate` refused it first as `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`.

**Coverage is checked over the MERGED draw, never per stratum** — `assignment_for`'s stated rule for the identical composition: a side a small stratum apportioned nothing is fine while another stratum covered it, and only a side empty across every stratum is refused.

- [ ] **Step 1: Write the failing test** — append to `tests/test_units.py`:

```python
def test_a_clustered_holdout_keeps_every_cluster_whole():
    """`reference.md` § Clustered units: "core computed the partition, so core
    keeps it indivisible." A holdout that trains on one cell of an animal and
    tests on another leaks just as thoroughly for happening only once.

    Twelve units in six clusters of two, so both a correct draw and a
    unit-level one give the same SIZES — the cluster-integrity assertion is the
    only thing that separates them, which is why the fixture is built this way
    rather than with clusters of one."""
    roster = _roster(12, animal=lambda i: f"a{i // 2}")
    clusters = {f"u{i}": f"a{i // 2}" for i in range(12)}
    plan = holdout_for(
        roster, {"method": "random", "frac": 0.5}, seed=99, clusters=clusters
    )
    train, test = set(plan.train), set(plan.test)
    assert train | test == {f"u{i}" for i in range(12)}
    assert not train & test
    for cluster in {f"a{i}" for i in range(6)}:
        members = {k for k, c in clusters.items() if c == cluster}
        assert members <= train or members <= test, (cluster, plan)
    # A positive companion for the integrity assertion above, which a draw
    # putting EVERY unit on one side would also satisfy.
    assert train and test


def test_the_clustered_and_unclustered_constructions_are_not_the_same_draw():
    """The relation between the two constructions, pinned — H3c-2's own
    experience is that a fixture cannot tell them apart unless it is built to.

    With one cluster per unit the two agree on SIZES and differ on MEMBERSHIP:
    the unclustered path shuffles unit keys and cuts two consecutive slices,
    while the clustered path shuffles cluster names, sorts largest-first, and
    deals each to the bucket furthest below its own target share — which
    interleaves by ratio rather than slicing. A fixture asserting only the
    sizes would pass under either construction for either call."""
    roster = _roster(10, animal=lambda i: f"u{i}")
    singleton = {f"u{i}": f"u{i}" for i in range(10)}
    plain = holdout_for(roster, {"method": "random", "frac": 0.4}, seed=5)
    clustered = holdout_for(
        roster, {"method": "random", "frac": 0.4}, seed=5, clusters=singleton
    )
    assert len(plain.test) == len(clustered.test) == 4
    assert set(plain.test) != set(clustered.test)


def test_a_stratified_holdout_splits_within_each_stratum():
    """`stratify_by` balances the split inside each stratum rather than only
    over the roster. Three UNEQUAL strata — 8, 4 and 2 units — so an
    unstratified draw, a correct stratified one, and one that weighted the
    strata equally each produce a different per-stratum test count.

    At `frac: 0.5` the correct per-stratum test counts are 4, 2 and 1; an
    unstratified draw of the same roster gives 7 test units spread by chance,
    which this asserts against directly."""
    sizes = {"big": 8, "mid": 4, "small": 2}
    labels = ["big"] * 8 + ["mid"] * 4 + ["small"] * 2
    roster = _roster(14, band=lambda i: labels[i])
    plan = holdout_for(
        roster, {"method": "random", "frac": 0.5, "stratify_by": ["band"]}, seed=17
    )
    assert plan.strata == ("band",)
    per_stratum = {}
    for name, count in sizes.items():
        members = {f"u{i}" for i, lab in enumerate(labels) if lab == name}
        per_stratum[name] = len(members & set(plan.test))
    assert per_stratum == {"big": 4, "mid": 2, "small": 1}
    # Membership too, not only counts: the counts are FORCED by the
    # apportionment, so no count assertion can see a change in how the
    # generator is carried across strata — the same dimension-no-assertion-
    # can-see shape that let a deleted shuffle pass an earlier slice's suite.
    # PINNED LITERAL — replace with what the implementation actually returns.
    assert set(plan.test) == {"REPLACE"}


def test_a_stratified_clustered_holdout_composes_both_rules():
    """The composition: strata outside, whole clusters inside — the same
    arrangement `assignment_for` uses, and sound only while
    `E-DATA-HOLDOUT-STRATIFY-VARIES` refuses a cluster carrying two stratum
    values, since such a cluster would belong to two groups and be divided.

    Every cluster whole AND every stratum represented on both sides."""
    labels = ["x"] * 8 + ["y"] * 8
    roster = _roster(16, animal=lambda i: f"a{i // 2}", band=lambda i: labels[i])
    clusters = {f"u{i}": f"a{i // 2}" for i in range(16)}
    plan = holdout_for(
        roster,
        {"method": "random", "frac": 0.5, "stratify_by": ["band"]},
        seed=23,
        clusters=clusters,
    )
    train, test = set(plan.train), set(plan.test)
    for cluster in {f"a{i}" for i in range(8)}:
        members = {k for k, c in clusters.items() if c == cluster}
        assert members <= train or members <= test, cluster
    for band in ("x", "y"):
        members = {f"u{i}" for i, lab in enumerate(labels) if lab == band}
        assert members & train and members & test, band


def test_a_stratified_holdout_that_leaves_a_side_empty_across_every_stratum_raises():
    """Coverage over the MERGED draw, `assignment_for`'s rule for the identical
    composition: a side a small stratum apportioned nothing is fine while
    another stratum covered it, and only a side empty everywhere is refused.

    Two strata of one unit each at `frac: 0.2` apportion `(1, 0)` in both, so
    the test side is empty across the whole draw."""
    roster = _roster(2, band=lambda i: f"b{i}")
    with pytest.raises(ContractError) as exc:
        holdout_for(
            roster, {"method": "random", "frac": 0.2, "stratify_by": ["band"]}, seed=1
        )
    assert exc.value.code == "E-DATA-HOLDOUT-EMPTY"


def test_a_thin_stratum_alone_does_not_raise():
    """The positive companion for the rule above, produced by the code under
    test: one stratum apportioning the test side nothing is accepted while
    another covers it. Without this the refusal above is indistinguishable from
    a per-stratum coverage rule."""
    labels = ["big"] * 9 + ["tiny"]
    roster = _roster(10, band=lambda i: labels[i])
    plan = holdout_for(
        roster, {"method": "random", "frac": 0.2, "stratify_by": ["band"]}, seed=3
    )
    assert plan.test and plan.train
    tiny = {"u9"}
    assert tiny <= set(plan.train)
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_units.py -k "clustered_holdout or constructions_are_not or stratified_holdout or stratified_clustered or thin_stratum" -x`. All fail with `NotImplementedError` from task 10's guard. Before implementing, **verify the per-stratum expectations by hand**: `holdout_sizes(8, 0.5) == (4, 4)`, `holdout_sizes(4, 0.5) == (2, 2)`, `holdout_sizes(2, 0.5) == (1, 1)` and `holdout_sizes(1, 0.2) == (1, 0)`. If any differs, fix the test's literals to the arithmetic rather than the other way round.

- [ ] **Step 3: Implement** —

  (a) In `src/publishable/units.py`, change `_stratum_groups`' third parameter from `axis: str` to `declaration: str` and interpolate it whole in the `NotImplementedError`, replacing

```python
            f"`data.units.assign.{axis}.stratify_by` names {name!r}, which no resolved "
```

  with

```python
            f"`{declaration}` names {name!r}, which no resolved "
```

  and adding to that function's docstring:

```python
    **`declaration` is the full dotted path of the declaration being served**,
    not an axis name: this function has more than one caller and the message it
    raises names the config path a reader has to go and fix. An axis name
    interpolated into a fixed `data.units.assign.<...>` template would print
    `data.units.assign.holdout.stratify_by` for a holdout — a path no config
    can hold.
```

  Update the three call sites in `assignment_for` to pass `f"data.units.assign.{axis}.stratify_by"`, and sweep: `grep -rn "assign.*stratify_by. names" src/ tests/` must show every message and every test pinning it agreeing.

  (b) Replace task 10's combined `if strata or clusters is not None: raise NotImplementedError(...)` guard with the two realized branches. Inside the `random` branch, after the `frac` guard and **in place of** the unclustered shuffle-and-slice, put:

```python
        weights = [1.0 - float(frac), float(frac)]
        rng = random.Random(seed)
        train_keys: list[str] = []
        test_keys: list[str] = []
        if strata:
            # One generator across every stratum, `assignment_for`'s own
            # convention: the strata are drawn in roster order from one carried
            # state, so the seed determines the whole split together rather
            # than each stratum in isolation. `_stratum_groups` is handed no
            # `resolved`: a holdout's `stratify_by` admits only a unit
            # attribute, never a `sweep.groups` axis (§ Validation,
            # *Stratification attribute exists*), and a holdout beside a group
            # axis is refused outright as `E-DATA-HOLDOUT-CELLS`.
            groups = _stratum_groups(
                list(roster), strata, "data.units.holdout.stratify_by"
            )
            for stratum_units in groups.values():
                if clusters is not None:
                    # Whole clusters inside each stratum — sound only while
                    # `E-DATA-HOLDOUT-STRATIFY-VARIES` refuses a cluster
                    # carrying two stratum values, which would belong to two of
                    # these groups and be divided here. The identical argument
                    # `assignment_for` makes for the identical composition.
                    train_bucket, test_bucket = _assign_whole_clusters_by_ratio(
                        stratum_units, weights, rng, clusters
                    )
                    train_keys.extend(u.key for u in train_bucket)
                    test_keys.extend(u.key for u in test_bucket)
                else:
                    keys = [u.key for u in stratum_units]
                    rng.shuffle(keys)
                    cut, _rest = holdout_sizes(len(stratum_units), float(frac))
                    train_keys.extend(keys[:cut])
                    test_keys.extend(keys[cut:])
        elif clusters is not None:
            train_bucket, test_bucket = _assign_whole_clusters_by_ratio(
                list(roster), weights, rng, clusters
            )
            train_keys.extend(u.key for u in train_bucket)
            test_keys.extend(u.key for u in test_bucket)
        else:
            train_size, test_size = holdout_sizes(len(roster), float(frac))
            keys = [unit.key for unit in roster]
            rng.shuffle(keys)
            train_keys.extend(keys[:train_size])
            test_keys.extend(keys[train_size:])
        # Coverage over the MERGED draw, never per stratum — `assignment_for`'s
        # rule for the identical composition: a side a small stratum
        # apportioned nothing is fine while another stratum covered it, and
        # only a side empty across the whole draw leaves one half of the split
        # with no units. Also the one refusal the unclustered and clustered
        # paths share: a cluster is the smallest thing that can move, so a
        # clustered draw reaches an empty side more easily rather than being
        # exempt from the refusal.
        if not train_keys or not test_keys:
            side = "train" if not train_keys else "test"
            raise ContractError(
                f"`data.units.holdout.frac: {frac}` over {len(roster)} resolved units "
                f"leaves the {side} side empty"
                + (f", drawn within {len(strata)} stratum declaration(s)" if strata else "")
                + (" over whole clusters" if clusters is not None else "")
                + ". Every split needs both sides — the training side has nothing to fit "
                "on, or the test side has nothing to report over; widen or narrow "
                "`frac`, stratify on fewer attributes, or resolve a larger roster",
                code="E-DATA-HOLDOUT-EMPTY",
            )
        return HoldoutPlan(
            train=tuple(train_keys), test=tuple(test_keys), seed=seed, strata=strata
        )
```

  Delete task 10's separate `train_size == 0 or test_size == 0` pre-check — the merged coverage check above subsumes it, and two refusals of one fault is what the single check avoids. **Keep task 10's tests passing**: re-run them and confirm the message still names the empty side, which both of that task's parametrized rows assert on.

  (c) Update `holdout_for`'s docstring: replace the "not realized at this commit" paragraph with the composition rules — whole clusters through `_assign_whole_clusters_by_ratio` at `[1 - frac, frac]`, strata outside either draw through `_stratum_groups`, one generator across every stratum, and **the relation between the two constructions stated**:

```python
    **The two constructions are deliberately not one, and are not
    bit-identical.** The unclustered draw shuffles unit keys and cuts two
    consecutive slices; the clustered draw shuffles cluster names, sorts
    largest-first and deals each cluster to the bucket furthest below its own
    target share. With one cluster per unit the two agree on the SIZES and
    differ on the MEMBERSHIP — the second interleaves by ratio where the first
    slices — so a fixture that cannot tell them apart proves nothing about
    either. `_assign_whole_clusters_by_ratio` takes a non-optional `Mapping`
    and indexes it, unlike `_assign_whole_clusters`, which is why this is two
    paths rather than one with a `clusters or singletons` default.
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then the task 10 tests (`uv run pytest tests/test_units.py -k holdout`), then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — three.

  (a) In `src/publishable/units.py`, replace the unclustered `else:` branch with a call to `_assign_whole_clusters_by_ratio(list(roster), weights, rng, {u.key: u.key for u in roster})` — the "singleton clusters are the same path" reading this task exists to refuse. Run `uv run pytest tests/test_units.py -k "constructions_are_not or holdout_cuts"`. `test_the_clustered_and_unclustered_constructions_are_not_the_same_draw` must **FAIL** on `set(plain.test) != set(clustered.test)`, and task 10's `holdout_cuts` must **FAIL** on its pinned literals. Revert in place; re-run.

  (b) Move `rng = random.Random(seed)` **inside** the stratum loop. Run `uv run pytest tests/test_units.py -k stratified_holdout`. `test_a_stratified_holdout_splits_within_each_stratum` must **FAIL on its membership assertion and only on that one**: with one generator the strata are drawn from a carried state and with one per stratum each restarts, so the per-stratum *counts* are unchanged — which is exactly why that test carries the pinned `set(plan.test)` literal beside the counts, and why this mutation would be blind without it. Revert in place; re-run.

  (c) In the stratified branch, change `cut, _rest = holdout_sizes(len(stratum_units), float(frac))` to `cut, _rest = holdout_sizes(len(roster), float(frac))` — apportioning the whole roster's sizes inside each stratum. `test_a_stratified_holdout_splits_within_each_stratum` must **FAIL** on `per_stratum == {"big": 4, "mid": 2, "small": 1}`. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: the clustered and stratified holdout draws, and the relation between them`.

---

## Task 12: `units.holdout_seed_for` — the derivation and its own digest suffix

**Files:** Modify `src/publishable/units.py`. Modify (append) `tests/test_units.py`.

**Interfaces:**
- Consumes: `units.units_hash(units: UnitList) -> str`; `units.assign_seed_for(block, axis, digest, roster) -> int` as the model.
- Produces:

```python
def holdout_seed_for(block: Mapping[str, Any], digest: str, roster: UnitList) -> int:
```

**Why it is not `_seed_from`.** `units._seed_from(digest)` hardcodes `sha256(f"{digest}|folds")`. A holdout is not a fold and must not draw the same partition a `fold` level would from the same digest — they are mutually exclusive declarations today (`E-DATA-HOLDOUT-FOLD`), so nothing *observes* the collision, and that is precisely the argument against relying on it: the suffix is what makes the two independent whatever a later slice permits.

**Why it is not `assign_seed_for`.** That one is per-axis and reads `block["seed"]` under an axis name a holdout does not have. The construction is otherwise identical and is copied deliberately: `f"{digest}|holdout|{units_hash(roster)}"`, sha256, first four bytes big-endian.

**The load-bearing half: a pinned integer is returned literally, and the digest is not consulted at all on that path.** `sweep.sample_seed_for`'s own words. "Pinning an integer is the deliberate act, and the one to take for anything you intend to cite" — so a pinned holdout must survive a roster that grows, shrinks, or reorders. Task 4 already stripped `holdout.seed` from `design_digest` for the matching reason.

**`bool` is excluded.** `isinstance(True, int)` is `True`, and `seed: true` is not a pin — `validate` refuses it as `E-DATA-HOLDOUT-SEED`, and this function must not honour it as `1`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_units.py`:

```python
def test_a_pinned_holdout_seed_is_returned_literally_and_ignores_the_digest():
    """`sweep.sample_seed_for`'s load-bearing half, copied: on the pinned path
    the digest is not consulted at all, so a pinned split survives a roster
    that grows, shrinks or reorders.

    Three varying inputs against one pin, because a function that read ANY of
    them would move for at least one of these."""
    block = {"method": "random", "frac": 0.2, "seed": 4321}
    assert holdout_seed_for(block, "sha256:aaa", _roster(10)) == 4321
    assert holdout_seed_for(block, "sha256:bbb", _roster(10)) == 4321
    assert holdout_seed_for(block, "sha256:aaa", _roster(11)) == 4321


def test_a_boolean_seed_is_not_a_pin():
    """`isinstance(True, int)` is `True`, and `seed: true` is not a pin —
    `validate` refuses it as `E-DATA-HOLDOUT-SEED`, and honouring it as `1`
    here would record a derived seed under a key the config wrote
    deliberately."""
    derived = holdout_seed_for({"seed": True}, "sha256:aaa", _roster(10))
    assert derived != 1
    assert derived == holdout_seed_for({}, "sha256:aaa", _roster(10))


def test_the_derived_holdout_seed_mixes_the_digest_and_the_resolved_roster():
    """§ What `auto` derives from's new row. Each assertion changes exactly one
    input, so a derivation that ignored either would fail one of them."""
    base = holdout_seed_for({}, "sha256:aaa", _roster(10))
    assert base == holdout_seed_for({"seed": "auto"}, "sha256:aaa", _roster(10))
    assert base != holdout_seed_for({}, "sha256:bbb", _roster(10))
    assert base != holdout_seed_for({}, "sha256:aaa", _roster(11))
    # `units_hash` covers the roster IN RESOLVED ORDER, so a reordered roster
    # is a different trial and must draw a different split.
    reordered = UnitList(list(_roster(10))[::-1])
    assert base != holdout_seed_for({}, "sha256:aaa", reordered)
    assert 0 <= base < 2**32


def test_the_holdout_seed_is_not_the_fold_seed_for_the_same_digest():
    """`_seed_from` hardcodes `|folds`. The two declarations are mutually
    exclusive today (`E-DATA-HOLDOUT-FOLD`), so nothing observes a collision —
    which is the argument for the suffix rather than against it: the two stay
    independent whatever a later slice permits."""
    assert holdout_seed_for({}, "sha256:aaa", _roster(10)) != _seed_from("sha256:aaa")


def test_the_holdout_seed_is_not_an_assign_axis_seed_for_the_same_digest():
    """The other neighbour, and the one whose construction this copies: same
    digest, same roster, different suffix."""
    roster = _roster(10)
    assert holdout_seed_for({}, "sha256:aaa", roster) != assign_seed_for(
        {}, "holdout", "sha256:aaa", roster
    )
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_units.py -k holdout_seed -x`. All fail on `ImportError`; add `holdout_seed_for`, `_seed_from` and `assign_seed_for` to the test module's import list and re-run.

- [ ] **Step 3: Implement** — in `src/publishable/units.py`, add immediately after `assign_seed_for`:

```python
def holdout_seed_for(block: Mapping[str, Any], digest: str, roster: UnitList) -> int:
    """The seed `data.units.holdout` draws its split with.

    `reference.md` § What `auto` derives from: a holdout's `seed` mixes "digest
    + the resolved roster" — the digest because the split is a property of the
    design, and `units_hash(roster)` because it covers the roster **in resolved
    order**, so two runs that resolved the same units in a different sequence
    did not draw the same trial (§ Where units come from).

    **Its own suffix, `|holdout`, and not `_seed_from`'s `|folds`.** A holdout
    is not a fold, and the two must not draw the same partition from the same
    digest. They are mutually exclusive declarations at this commit
    (`E-DATA-HOLDOUT-FOLD`), so nothing *observes* a collision — which is the
    argument FOR the suffix rather than against it: relying on a refusal
    elsewhere to keep two derivations apart is how they come to agree by
    accident the moment that refusal moves.

    **Not `assign_seed_for` either**, whose payload carries an axis name a
    holdout does not have. The construction is otherwise copied deliberately:
    the same digest, the same `units_hash`, the same four bytes read big-endian
    — one derivation shape for every drawn partition in the config.

    A pinned integer is returned literally, and — the load-bearing half, copied
    from `sweep.sample_seed_for`'s own docstring — **the digest is not consulted
    at all** on that path, only read out of `block`. "Pinning an integer is the
    deliberate act, and the one to take for anything you intend to cite," so a
    pinned split must survive a roster that grows, shrinks, or reorders, and
    `hashes.design_digest` strips `holdout.seed` for the same reason: a pinned
    seed must not move the digest it would otherwise be mixed with.

    `bool` is excluded from the pin: `isinstance(True, int)` is `True`, and
    `seed: true` is not a pin — `validate` refuses it as
    `E-DATA-HOLDOUT-SEED`, and honouring it as `1` would record a derived seed
    under a key the config wrote deliberately.
    """
    seed = block.get("seed", "auto")
    if isinstance(seed, int) and not isinstance(seed, bool):
        return seed
    payload = f"{digest}|holdout|{units_hash(roster)}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_units.py -k holdout_seed`, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — two.

  (a) Change the payload's `|holdout|` to `|assign|holdout|`. `test_the_holdout_seed_is_not_an_assign_axis_seed_for_the_same_digest` must **FAIL** — that is precisely `assign_seed_for({}, "holdout", ...)`'s payload. Revert in place; re-run.

  (b) Change `if isinstance(seed, int) and not isinstance(seed, bool):` to `if isinstance(seed, int):`. `test_a_boolean_seed_is_not_a_pin` must **FAIL** on both of its assertions. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: units.holdout_seed_for, with its own digest suffix`.

---

## Task 13: Realize the holdout once, in `cli.command_run`

**Files:** Modify `src/publishable/cli.py`. Modify (append) `tests/test_cli.py`.

**Interfaces:**
- Consumes: `units.holdout_for(roster, block, *, seed, clusters=None) -> HoldoutPlan`; `units.holdout_seed_for(block, digest, roster) -> int`; `command_run`'s locals `units_decl`, `roster`, `digest`, `clusters`.
- Produces:

```python
def _resolved_holdout(
    units_decl: dict[str, Any] | None,
    roster: "UnitList | None",
    digest: str,
    clusters: dict[str, str] | None,
) -> "HoldoutPlan | None":
```

  and one `holdout_plan = _resolved_holdout(units_decl, roster, digest, clusters)` in `command_run`, placed immediately after `group_axes` is resolved and **before** `build_allocation_document` and `execute_plan`.

**Realized once, and the one object is what everything downstream is handed.** `build_allocation_document`'s own docstring makes this argument for arms and it transfers verbatim: it used to be handed the roster and re-derive the partition through `arms_of`, and *"under a draw that second derivation is a second draw, and 'provably identical' is not something two calls can be made to promise — only not calling twice can."* A holdout under `method: random` is a draw. So the partition the runner runs, the partition the denominators count, and the partition `allocation.json` claims must be **the same object**, not three answers that happen to agree.

**No end-to-end test exists for this task and will not until task 18.** `E-DATA-HOLDOUT-UNSUPPORTED` still refuses every declaration, so no config reaches `command_run`. This task tests `_resolved_holdout` **directly**, which is exactly why the realization is extracted into a named function rather than written inline — the same move `_condition_counts` made when "the fix exists" and "the fix is wired" could not otherwise be told apart. Task 18's end-to-end pins close the remaining gap.

**A holdout beside a group axis is refused at this commit** (`E-DATA-HOLDOUT-CELLS`, task 8), so `clusters` is the only other partition input this function needs and `group_axes` is not one of them.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
def _cli_roster(n, **attrs_by_index):
    from publishable.units import Unit, UnitList

    return UnitList(
        [
            Unit(key=f"u{i}", paths=(),
                 attributes={k: v(i) for k, v in attrs_by_index.items()})
            for i in range(n)
        ]
    )


def test_the_holdout_is_realized_once_and_returns_none_when_undeclared():
    """`None` for every shape that declares no split — the gate
    `build_allocation_document`'s "both absent" rule and the runner's narrowing
    both read. An empty block is undeclared, matching `_check_holdout`'s own
    gate, so a `holdout: {}` partitions nothing rather than drawing an
    unmethodded split."""
    roster = _cli_roster(10)
    for decl in (None, {}, {"holdout": None}, {"holdout": {}}):
        assert _resolved_holdout(decl, roster, "sha256:aaa", None) is None
    # No roster is also `None`: there is nothing to partition.
    assert _resolved_holdout(
        {"holdout": {"method": "random", "frac": 0.2}}, None, "sha256:aaa", None
    ) is None


def test_the_realized_holdout_uses_the_derived_seed_and_the_cluster_map():
    """One realization composing `holdout_seed_for` and `holdout_for` — and it
    must be the SAME answer either helper gives on its own, or the run and the
    record would be two draws.

    The clustered arm is asserted separately because `clusters` reaching
    `holdout_for` is a threading that a composition ignoring the argument would
    pass every unclustered assertion for."""
    from publishable.units import holdout_for, holdout_seed_for

    roster = _cli_roster(12, animal=lambda i: f"a{i // 2}")
    decl = {"holdout": {"method": "random", "frac": 0.5}}
    plan = _resolved_holdout(decl, roster, "sha256:aaa", None)
    seed = holdout_seed_for(decl["holdout"], "sha256:aaa", roster)
    assert plan == holdout_for(roster, decl["holdout"], seed=seed)
    assert plan.seed == seed

    clusters = {f"u{i}": f"a{i // 2}" for i in range(12)}
    clustered = _resolved_holdout(decl, roster, "sha256:aaa", clusters)
    assert clustered == holdout_for(roster, decl["holdout"], seed=seed, clusters=clusters)
    # The positive companion for "the cluster map was threaded": the two
    # realizations differ, so a composition dropping `clusters` is visible.
    assert set(clustered.test) != set(plan.test)


def test_a_pinned_holdout_seed_reaches_the_realization():
    """A pin is the deliberate act, so it has to survive the composition —
    a realization deriving the seed unconditionally would pass every other
    assertion in this file."""
    roster = _cli_roster(10)
    plan = _resolved_holdout(
        {"holdout": {"method": "random", "frac": 0.2, "seed": 4321}},
        roster, "sha256:aaa", None,
    )
    assert plan.seed == 4321
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k "realized_once or realized_holdout_uses or pinned_holdout_seed_reaches" -x`. All fail on `ImportError` for `_resolved_holdout`; add it to `tests/test_cli.py`'s `publishable.cli` import list and re-run.

- [ ] **Step 3: Implement** — in `src/publishable/cli.py`, add `holdout_for`, `holdout_seed_for` and `HoldoutPlan` to the `publishable.units` import list, and add beside `_resolved_group_axes`:

```python
def _resolved_holdout(
    units_decl: dict[str, Any] | None,
    roster: "UnitList | None",
    digest: str,
    clusters: dict[str, str] | None,
) -> "HoldoutPlan | None":
    """`data.units.holdout`, realized **once per run** — or `None` when the
    design declares none.

    The one object handed to the runner's narrowing, to the denominators, and
    to `build_allocation_document`. `build_allocation_document`'s own docstring
    makes the argument for arms and it transfers verbatim: it used to be handed
    the roster and re-derive the partition, and *"under a draw that second
    derivation is a second draw, and 'provably identical' is not something two
    calls can be made to promise — only not calling twice can."* A `method:
    random` holdout is a draw, so the partition the run executes, the
    denominators it reports against, and the membership `allocation.json`
    claims are the same object rather than three answers that happen to agree.

    `None` for four shapes, and they are one shape: an absent `data.units`, an
    absent `holdout`, a `holdout: null`, and a `holdout: {}`. The last is
    `_check_holdout`'s own gate — an empty block declares nothing and
    partitions nothing — so the two readings of "is a holdout declared" agree
    rather than one drawing an unmethodded split the other validated as absent.
    `None` for a roster that did not resolve too: there is nothing to partition,
    and `_check_units` has already reported why.

    `clusters` is `cli.command_run`'s single cluster map, the same one the fold
    partition and the arm draw are handed — not re-derived here, `clusters_of`
    being the single authority. `group_axes` is deliberately not a parameter: a
    holdout beside a group axis is refused at this commit as
    `E-DATA-HOLDOUT-CELLS`, so there is no cell structure for a split to be
    drawn inside of.
    """
    if roster is None:
        return None
    block = (units_decl or {}).get("holdout")
    if not isinstance(block, dict) or not block:
        return None
    return holdout_for(
        roster, block, seed=holdout_seed_for(block, digest, roster), clusters=clusters
    )
```

  and in `command_run`, immediately after the `group_axes = _resolved_group_axes(...)` line:

```python
    # Realized here, once, and before anything reads it — the runner's
    # narrowing, the denominators and `allocation.json` are all handed this one
    # object. See `_resolved_holdout` for why not calling twice is the only
    # thing that can promise the run and the record agree.
    holdout_plan = _resolved_holdout(units_decl, roster, digest, clusters)
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. `holdout_plan` is unused at this commit and `ruff` will say so — that is correct and is what task 14 consumes; if the lint rule is fatal, add the consumption in task 14 and keep this commit's line as the assignment it is, marking it with the narrowest possible suppression and a comment naming what consumes it next.

- [ ] **Step 5: Mutate** — two.

  (a) In `src/publishable/cli.py`, change `if not isinstance(block, dict) or not block:` to `if not isinstance(block, dict):`. `test_the_holdout_is_realized_once_and_returns_none_when_undeclared` must **FAIL** on the `{"holdout": {}}` row — `holdout_for` raises `NotImplementedError` for a methodless block. Revert in place; re-run.

  (b) Drop the `clusters=clusters` argument from the `holdout_for` call. `test_the_realized_holdout_uses_the_derived_seed_and_the_cluster_map` must **FAIL** on its clustered assertion. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: realize the holdout once in command_run`.

---

## Task 14: Runner narrowing — `io.units` is the test partition, `io.units.train` the training one

**Files:** Modify `src/publishable/runner.py`, `src/publishable/cli.py`. Modify (append) `tests/test_runner.py`.

**Interfaces:**
- Consumes: `runner.execute_plan(*, plan, run_dir, input_dir, cfgs, repeats, digest, units=None, max_failed_fraction=None, fold_members=None, arm_members=None, measurements=None)`.
- Produces: one new keyword-only parameter, `holdout_train: "UnitList | None" = None`, and the narrowing that reads it. `cli.command_run` passes `holdout_train=UnitList([u for u in roster if u.key in set(holdout_plan.train)]) if holdout_plan is not None else None`, and `units=` becomes the **test** roster — task 15 names that local.

**The shape, and why it is a `train` list rather than a plan.** `execute_plan` narrows nothing itself and derives nothing: `_cond_roster`'s single-authority argument, which `attrition`'s docstring restates ("does not re-derive that narrowing itself, and must not"). So the runner is handed two rosters and puts one inside the other. Passing the `HoldoutPlan` instead would make the runner a second place that turns keys into units.

**Every scope, not just `repeat`.** § A fixed holdout split: the split is **fixed for the whole run**, so `io.units` is the test partition and `io.units.train` the training one at `run`, `condition`, `repeat` and `summary` scope alike. This is the **inverse** of the fold rule in the same function — `reference.md` says *"A `holdout` does not raise, because its split is fixed for the whole run"*, and `experimental-designs.md` § Cross-validation supplies the other half: *"Condition-scoped fitting is right for a fixed holdout and wrong for cross-validation."* A holdout must therefore **not** take the `elif execution.scope in ("run", "condition"): step_units = None` branch.

**The fold branch is unreachable under a holdout at this commit** — `E-DATA-HOLDOUT-FOLD` (task 6) refuses the pair, and `E-DATA-HOLDOUT-CELLS` (task 8) closes the arm interaction. **Assert it in the code**, and exercise the assertion by calling `execute_plan` directly with both arguments non-`None`. Do **not** write a config-level test for it: no config can instantiate that seam, and a test claiming to would be the "seam named in the brief and instantiated by no fixture" trap. Write the comment as what is true at this commit, naming the code that closes it.

**Arm narrowing needs no interaction.** `arm_members` comes from `sweep.groups`, which task 8 refuses beside a holdout, so `arm_members is None` whenever `holdout_train is not None`. The assertion covers that too.

- [ ] **Step 1: Write the failing test** — append to `tests/test_runner.py`:

```python
_UNITS_RECORDING_STEP_SOURCE = """\
from publishable import BaseStep


class Step(BaseStep):
    scope = "{scope}"

    def run(self, cfg, io):
        io.write("seen.json", {{
            "test": [u.key for u in io.units],
            "train": [u.key for u in io.units.train],
        }})
        return {{"n": len(io.units)}}
"""


@pytest.mark.parametrize("scope", ["run", "condition", "repeat", "summary"])
def test_a_holdout_narrows_io_units_at_every_scope(tmp_path, scope):
    """§ A fixed holdout split: the split is fixed for the whole run, so
    `io.units` is the test partition and `io.units.train` the training one at
    EVERY scope — the inverse of the fold rule in the same function, which
    hands `None` at `run` and `condition`.

    All four scopes are parametrized because the fold branch's `run`/
    `condition` special case sits three lines away, and a narrowing written
    inside it would pass a `repeat`-only test."""
    roster = _runner_roster(10)
    train = UnitList([u for u in roster if u.key in {"u0", "u1", "u2", "u3", "u4",
                                                     "u5", "u6", "u7"}])
    test = UnitList([u for u in roster if u.key in {"u8", "u9"}])
    seen = _run_one_step(
        tmp_path, scope=scope, units=test, holdout_train=train,
        source=_UNITS_RECORDING_STEP_SOURCE,
    )
    assert seen["test"] == ["u8", "u9"]
    assert seen["train"] == ["u0", "u1", "u2", "u3", "u4", "u5", "u6", "u7"]


def test_without_a_holdout_train_still_raises_at_every_scope(tmp_path):
    """The control, and it must produce something: with `holdout_train=None`
    and no fold, `io.units` is the whole roster and `io.units.train` raises —
    the shape task 1 pinned end to end. A narrowing written one branch too wide
    would hand a train list to a run that declared no partition."""
    roster = _runner_roster(10)
    result = _run_one_step_raw(tmp_path, scope="repeat", units=roster, source=
                               _UNITS_RECORDING_STEP_SOURCE)
    assert result.status == "failed"
    assert "E-STEP-UNITS-UNAVAILABLE" in (result.error or "")


def test_a_holdout_beside_a_fold_is_a_core_defect_not_a_silent_choice(tmp_path):
    """No CONFIG can reach this: `E-DATA-HOLDOUT-FOLD` refuses the pair at
    validate time, and `E-DATA-HOLDOUT-CELLS` closes the arm interaction. So
    the seam is exercised by calling `execute_plan` directly with both
    arguments non-`None`, rather than by a fixture that cannot exist — naming a
    seam is not testing it.

    An assertion rather than a silent precedence: two answers to "which units
    is this metric over?" is exactly what the refusal exists to prevent, and if
    it ever stops preventing it, this must be a crash and not a guess."""
    roster = _runner_roster(10)
    with pytest.raises(AssertionError):
        execute_plan(
            plan=_one_step_plan(tmp_path, scope="repeat"),
            run_dir=tmp_path / "run", input_dir=tmp_path / "in",
            cfgs={}, repeats=[], digest="sha256:aaa",
            units=roster,
            holdout_train=UnitList(list(roster)[:5]),
            fold_members={"fold0": frozenset({"u0"})},
        )
```

  `_runner_roster`, `_run_one_step`, `_run_one_step_raw` and `_one_step_plan` are the helpers this file already uses to drive `execute_plan` without a `cli` run — **read `tests/test_runner.py` first and reuse whatever it has** rather than adding four new ones; if a helper does not exist, add the smallest one that does the job and document it beside its siblings.

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_runner.py -k "holdout_narrows or without_a_holdout_train or holdout_beside_a_fold" -x`. The first fails on the unknown `holdout_train` keyword; the control passes already, which is why its own assertion is on a produced failure and not on an absence.

- [ ] **Step 3: Implement** — in `src/publishable/runner.py`, add the parameter to `execute_plan`'s signature after `fold_members`:

```python
    holdout_train: "UnitList | None" = None,
```

  and replace the no-fold branch of the narrowing:

```python
        if fold_members is None or scoped_units is None:
            step_units = scoped_units
```

  with

```python
        if fold_members is None or scoped_units is None:
            # A `data.units.holdout` is fixed for the WHOLE run, so it narrows
            # at every scope — `run`, `condition`, `repeat` and `summary`
            # alike. That is the inverse of the fold rule three lines below,
            # and deliberately: `reference.md` § Step scope says "a `holdout`
            # does not raise, because its split is fixed for the whole run",
            # and `experimental-designs.md` § Cross-validation says
            # "condition-scoped fitting is right for a fixed holdout and wrong
            # for cross-validation". A holdout that took the fold branch's
            # `run`/`condition` hole would hand `None` to exactly the step a
            # holdout exists to let fit.
            #
            # `units` is already the TEST partition when a holdout is declared
            # — `cli.command_run` narrowed it at the call site, `_cond_roster`'s
            # single-authority rule, which `attrition`'s own docstring restates
            # ("does not re-derive that narrowing itself, and must not"). This
            # function turns two rosters into one `UnitList`; it derives
            # neither.
            step_units = scoped_units
            if holdout_train is not None:
                step_units = UnitList(list(scoped_units), train=holdout_train)
```

  and add the assertion at the top of `execute_plan`'s body, before the loop:

```python
    # Two evaluation splits is two answers to "which units is this metric
    # over?", which is exactly what `validate` refuses. **No config can reach
    # this at this commit**: `E-DATA-HOLDOUT-FOLD` refuses `holdout` beside a
    # `{kind: fold}` level, and `E-DATA-HOLDOUT-CELLS` refuses a holdout beside
    # the group axis `arm_members` comes from. So this is an assertion about
    # core's own callers rather than about a config — and it is an assertion
    # rather than a silent precedence because if either refusal ever stops
    # holding, a crash here is what makes that visible instead of a partition
    # chosen by whichever branch happened to be written first.
    assert holdout_train is None or fold_members is None, (
        "a holdout and a fold repeat both narrow the roster; `validate` refuses the "
        "pair as `E-DATA-HOLDOUT-FOLD`"
    )
    assert holdout_train is None or arm_members is None, (
        "a holdout beside a group axis is refused as `E-DATA-HOLDOUT-CELLS`"
    )
```

  and extend `execute_plan`'s docstring with a paragraph naming `holdout_train` and stating that `units` is the test partition when it is given.

  Then in `src/publishable/cli.py`, pass it at the `execute_plan` call:

```python
            holdout_train=(
                UnitList([u for u in roster if u.key in set(holdout_plan.train)])
                if holdout_plan is not None
                else None
            ),
```

  Leave `units=roster` exactly as it is — **task 15 owns that line**, and changing both here would make the denominator fix untestable as a change of its own.

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest` (task 1's two pins must still pass — they are the baseline this task is most likely to move), then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — three.

  (a) In `src/publishable/runner.py`, move the `if holdout_train is not None:` narrowing inside `elif execution.scope == "repeat":`. `test_a_holdout_narrows_io_units_at_every_scope` must **FAIL** for the `run`, `condition` and `summary` rows and pass for `repeat`. Revert in place; re-run.

  (b) Change `step_units = UnitList(list(scoped_units), train=holdout_train)` to `step_units = UnitList(list(holdout_train), train=holdout_train)`. All four rows must **FAIL** on `seen["test"] == ["u8", "u9"]`. Revert in place; re-run.

  (c) In `src/publishable/cli.py`, change the `holdout_train=` expression to `holdout_train=None`. Run `uv run pytest`. Nothing fails, **and that is the honest result at this commit**: no config can declare a holdout, so the `cli` wiring has no test until task 18. Record this in the commit message, and note that task 18's end-to-end pin is what closes it — do not invent a test that reaches `command_run` with a holdout, because `validate` refuses one.

- [ ] **Step 6: Commit** — `feat: a holdout narrows io.units to the test partition at every scope`.

---

## Task 15: The denominators — six sites narrowed, two deliberately not

**Files:** Modify `src/publishable/cli.py`. Modify (append) `tests/test_cli.py`.

**Interfaces:**
- Consumes: `cli._condition_counts`, `cli._condition_report_by_levels`, `cli._condition_beside_n`, `cli._compute_vs_baseline`, `cli._compute_declared_contrasts`, `runner.execute_plan`, all called from `command_run`.
- Produces:

```python
def _evaluation_roster(
    roster: "UnitList | None", holdout: "HoldoutPlan | None"
) -> "UnitList | None":
```

  and one `eval_roster = _evaluation_roster(roster, holdout_plan)` local in `command_run`, passed at **six** call sites.

**This is the item most likely to ship wrong and it gets the sharpest fixture.** `runner.attrition` computes `handed = keys` — the whole roster it was given — when `fold_members is None`, and returns `resolved = len(handed)`, `failed = len(handed) - len(completed) - len(ineligible)`. Under a holdout with no narrowing, **every training unit lands in `failed`**: handed out, recording nothing, neither completed nor skipped.

**The six sites, named.** In `command_run`, replace `roster` with `eval_roster` at exactly these and nowhere else:

1. `execute_plan(..., units=roster, ...)` — which fixes `max_failed_fraction` and `_units_failed_anywhere` **for free**: `execute_plan` computes `resolved = len(units)` on the outer roster, so today a `0.2` holdout over 240 divides at most 48 possible failures by 240 and the guard fires at five times the declared threshold, in the direction of not firing.
2. `_condition_beside_n(beside_n, roster, cond.index, arm_members_map)`.
3. `_condition_counts(results, roster, step_name, cond.index, arm_members_map, ...)`.
4. `_condition_report_by_levels(roster, cond.index, arm_members_map, attribute)`.
5. `_compute_vs_baseline(..., roster=roster, ...)`.
6. `_compute_declared_contrasts(..., roster=roster, ...)`.

Site 5 and 6 are what reach `units_matching(roster, comp.within)`, so a contrast's `within` subgroup is over test units too.

**Two things stay whole-roster, deliberately, and the code must say so.**

- `provenance.units.n` and `provenance.units_hash`. They are the roster's **identity**, not a metric's denominator. A comment at that site must say why `240` there and `48` in a metric's `n` is not a bug — task 2's inference-base ruling written down where a reader meets the number.
- The **key-indexed maps**: `weights` (built `{u.key: ... for u in roster}`), `unit_attributes`, and `resample_strata`. Each is consumed **by key** over the units that completed, so surplus training keys are inert. Narrowing them would be a third answer to which roster is which, for no observable difference. **State this affirmatively in the code**, or an implementer will "complete" the sweep.

**Three figures are holdout-safe by construction and need no change** — verified in the scoping, not assumed: `runner._counts` computes Kish's effective size and the cluster count over the **completed** units (its own docstring: "a df is over the units the interval was computed from"), and `cli`'s `resample_strata`/`clusters` maps are key-indexed. So a whole-roster Kish size never sits beside a test-partition `n`.

**`technical_n` is filed, not fixed.** See Global Constraints. Do not add the withholding.

**No end-to-end test until task 18**, which is why `_evaluation_roster` is a named function: "the fix exists" and "the fix is wired" are otherwise indistinguishable, which is the exact shape of the bug `_condition_counts` was extracted to prevent.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
def test_the_evaluation_roster_is_the_test_partition_and_preserves_roster_order():
    """The denominator every metric counts against. Order preserved because
    the roster's order is part of its identity and `report_by`'s per-level
    tables are built by walking it.

    The `None` arm is the no-holdout case and must return the SAME OBJECT, not
    a copy: `_cond_beside_n` decides whether `technical_n` survives by identity
    (`cond_roster is roster`), so returning a copy here would silently withhold
    it from every unswept run."""
    from publishable.units import HoldoutPlan

    roster = _cli_roster(10)
    assert _evaluation_roster(roster, None) is roster
    assert _evaluation_roster(None, None) is None

    plan = HoldoutPlan(
        train=("u3", "u1", "u0", "u2", "u4", "u6", "u5", "u7"),
        test=("u9", "u8"),
        seed=1234,
        strata=(),
    )
    narrowed = _evaluation_roster(roster, plan)
    assert [u.key for u in narrowed] == ["u8", "u9"]
    assert len(narrowed) == 2


def test_the_narrowed_roster_is_what_attrition_counts_against():
    """The composition this task exists for: `attrition` hands out whatever
    roster it is given, so a training unit that recorded nothing lands in
    `failed` unless the roster it sees is already the test partition.

    Asserted through `_condition_counts` — the one function `command_run`
    calls for a condition's counts — rather than through `attrition` directly,
    because `attrition` counting correctly over a roster nobody narrowed is
    the defect, not the fix."""
    roster = _cli_roster(10)
    eval_roster = _evaluation_roster(roster, _HOLDOUT_PLAN_8_2)
    results = _completed_results_for(["u8", "u9"], step_name="step01", cond_index=0)

    whole = _condition_counts(results, roster, "step01", 0, None)
    narrowed = _condition_counts(results, eval_roster, "step01", 0, None)

    # The defect, stated as a number: 8 training units counted as failures.
    assert whole["resolved"] == 10 and whole["failed"] == 8
    # The fix.
    assert narrowed["resolved"] == 2
    assert narrowed["completed"] == 2
    assert narrowed["failed"] == 0
```

  `_HOLDOUT_PLAN_8_2` is a module-level `HoldoutPlan` with `train=("u0",…,"u7")` and `test=("u8","u9")`. `_completed_results_for` builds the `list[ExecutionResult]` `attrition` reads — **read `tests/test_cli.py` and `tests/test_runner.py` first** and reuse whichever helper already constructs those; only add one if neither does.

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k "evaluation_roster or narrowed_roster_is_what" -x`. Both fail on `ImportError` for `_evaluation_roster`; add it to the import list and re-run. The second then fails on `narrowed["resolved"] == 2`. **Confirm `whole["failed"] == 8` passes before implementing** — that assertion *is* the defect, and seeing it is what stops the fix being written against a fault that was never there.

- [ ] **Step 3: Implement** — in `src/publishable/cli.py`, add:

```python
def _evaluation_roster(
    roster: "UnitList | None", holdout: "HoldoutPlan | None"
) -> "UnitList | None":
    """The units every denominator counts against — the holdout's **test**
    partition when one is declared, and the same roster object otherwise.

    `reference.md` § A fixed holdout split: "`resolved` is the test partition
    — a 20 % holdout over 240 units reports `resolved: 48`, and the interval is
    over those 48. That's the honest denominator: the training units produced
    no result to generalize from."

    **Without this, every training unit lands in `failed`.** `runner.attrition`
    computes `handed = keys` over whatever roster it is given, and a training
    unit is handed out, records nothing, and is neither completed nor skipped —
    so a 0.2 holdout over 240 would report 192 failures and trip
    `max_failed_fraction` on a run in which nothing failed.

    **The same object, not a copy, when no holdout is declared.**
    `_cond_beside_n` decides whether `technical_n` survives by IDENTITY
    (`cond_roster is roster`), so a copy here would silently withhold it from
    every run in the build.

    Roster order is preserved: it is part of the roster's identity, and
    `_report_by_levels` walks it to build each level's table.

    **What this deliberately does NOT narrow**, and the list is the point
    rather than an omission:

    - `provenance.units.n` and `provenance.units_hash` stay whole-roster. They
      are the roster's identity, not a metric's denominator — which is what
      makes `240` there and `48` in a metric's `n` two true numbers rather than
      a contradiction.
    - The key-indexed maps `command_run` builds over the roster — the
      `weight_by` weights, `unit_attributes`, and `resample_strata` — are
      consumed BY KEY over units that completed, so a surplus training key is
      never looked up. Narrowing them would be a third answer to which roster
      is which for no observable difference.
    - `runner._counts`' Kish size and cluster count are computed over the
      COMPLETED units already (its own docstring: "a df is over the units the
      interval was computed from"), so they are holdout-safe by construction
      and need nothing here.
    """
    if roster is None or holdout is None:
        return roster
    test = set(holdout.test)
    return UnitList([u for u in roster if u.key in test])
```

  and in `command_run`, immediately after `holdout_plan` is realized:

```python
    # One narrowing, six readers. `roster` itself stays whole below this line —
    # `provenance.units.n` and `units_hash` are the roster's identity rather
    # than a metric's denominator, and rebinding the name would narrow every
    # future call site silently, including theirs.
    eval_roster = _evaluation_roster(roster, holdout_plan)
```

  Then change **exactly six** call sites from `roster` to `eval_roster`: `execute_plan(units=...)`, `_condition_beside_n`, `_condition_counts`, `_condition_report_by_levels`, `_compute_vs_baseline(roster=...)`, `_compute_declared_contrasts(roster=...)`.

  Then add a comment at the provenance write site, beside `"units": ...`:

```python
            # **Whole-roster, deliberately, and not the same number a metric's
            # `n` reports.** Under a `data.units.holdout` a metric's
            # `n.resolved` counts the TEST partition — 48 where this says 240
            # — and both are true: this is the identity of the roster the run
            # resolved, which is what `units_hash` pins and what `reproduce`
            # checks, where `n` is the denominator of an estimate. Narrowing
            # this would make the hash cover a subset the config never
            # described.
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest` (task 1's pins are the ones to watch: nothing about a no-holdout run may move, and `_evaluation_roster` returning the same object is what guarantees it), then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Then sweep the six sites by claim: `grep -n "roster" src/publishable/cli.py | grep -n "_condition_\|_compute_\|units=roster"` — every remaining `roster` at those functions must be intentional, and `provenance` must still read `roster`.

- [ ] **Step 5: Mutate** — three.

  (a) In `src/publishable/cli.py`, change `_evaluation_roster`'s early return to `return UnitList(list(roster)) if roster is not None else None` — a copy rather than the same object. Run `uv run pytest`. `tests/test_cli.py` carries `technical_n` assertions today, so a `measurements`-declaring run with no group axis should now lose its `technical_n` and fail. **If nothing fails, do not add a test to defend the claim** — that would be building the `technical_n` behaviour Global Constraints files and defers. Instead **weaken the docstring**: replace "would silently withhold it from every run in the build" with a statement that `_cond_beside_n` decides by identity and that returning the same object is what keeps this function out of that decision, with no claim about what any current test observes. Either way, revert the mutation in place and re-run.

  (b) Change the narrowing to `test = set(holdout.train)`. Run `uv run pytest tests/test_cli.py -k "evaluation_roster or narrowed_roster_is_what"`. Both must **FAIL**. Revert in place; re-run.

  (c) Revert the `execute_plan(units=eval_roster)` site back to `units=roster`. Run `uv run pytest`. Nothing fails — **the honest result at this commit**, since no config can declare a holdout. Record it in the commit message and note that task 18's `n.resolved` and `max_failed_fraction` pins are what close it.

- [ ] **Step 6: Commit** — `feat: every denominator counts the holdout's test partition`.

---

## Task 16: `W-STATS-RESAMPLE-CLUSTERS` against the test partition

**Files:** Modify `src/publishable/validate.py`. Modify (append) `tests/test_validate.py`.

**Interfaces:**
- Consumes: `units.holdout_for`, `units.holdout_seed_for`, `units.clusters_of`, `hashes.design_digest`, `units.fold_basis`.
- Produces: `_check_resample(doc, roster, c, holdout_test: UnitList | None = None)` — one new keyword parameter — and a `_holdout_test_roster(doc, units_decl, roster, cluster_by) -> UnitList | None` helper in `validate.py`, called once in `validate_config` and threaded in.

**The defect, in the direction of not firing.** `_check_resample` computes `groups = fold_basis(roster, cluster_by)` over the **whole roster** and compares it to `limits.min_clusters`. Under a `frac: 0.2` holdout the percentile interval actually rests on roughly a fifth of that many clusters: a run with 50 clusters and `min_clusters: 20` passes silently while its intervals rest on ~10 draws. H4a shipped it, and only a task scoped past `holdout` alone would notice.

**Why the fix is the realized draw and not `fold_basis × frac`.** Under `by_attribute` there is **no `frac`** — the realized proportion is whatever the column says. And under `cluster_by` the split moves whole clusters, so the realized cluster count is not any arithmetic on the unit count. `holdout_for` is a pure function precisely so `validate` can ask it, which is `assignment_for`'s own argument.

**Only the clusters warning moves.** `E-STATS-RESAMPLE-STRATIFY-VARIES` keeps reading the **whole** roster: within-cluster constancy over the test partition is implied by constancy over the whole roster, so refusing on the wider set is stricter and correct, and refusing on the narrower one would let a config validate whose *training* half is incoherent. Say this in the code.

**`tests/test_validate.py` does not import `_check_resample`** — verified at `78bb794`, it appears only in docstrings there — so this signature change costs nothing outside `validate.py`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
_FIFTY_CLUSTERS = "patient_id,animal_id,label\n" + "".join(
    f"p{i},a{i // 2},x\n" for i in range(100)
)


def test_the_resample_cluster_warning_counts_the_holdout_s_test_partition(
    write_config, tmp_path
):
    """The warning is about how many INDEPENDENT DRAWS a percentile interval
    rests on, and under a holdout the draw runs over the test partition alone.
    50 clusters × `frac: 0.2` is ~10, so `min_clusters: 20` must warn — and at
    `78bb794` it does not, because the count is taken over the whole roster.

    Two configs differing ONLY in whether a holdout is declared, so the
    warning's presence is attributable to the holdout rather than to the
    roster."""
    (tmp_path / "input" / "index.csv").write_text(_FIFTY_CLUSTERS)
    common = {
        "from": "index.csv", "key": "patient_id",
        "attributes": ["animal_id", "label"], "cluster_by": "animal_id",
    }
    resample = {"resample": {"method": "bootstrap", "n": 2000}}

    without = codes(write_config({
        "data.units": dict(common),
        "limits": {"min_clusters": 20},
        "statistics": resample,
    }))
    # The control, and it must be silent: 50 clusters is above 20.
    assert "W-STATS-RESAMPLE-CLUSTERS" not in without

    with_holdout = codes(write_config({
        "data.units": dict(common, holdout={"method": "random", "frac": 0.2}),
        "limits": {"min_clusters": 20},
        "statistics": resample,
    }))
    assert "W-STATS-RESAMPLE-CLUSTERS" in with_holdout
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in with_holdout


def test_a_holdout_wide_enough_to_keep_the_clusters_does_not_warn(
    write_config, tmp_path
):
    """The positive companion, produced by the code under test: the same
    roster and the same `min_clusters` under a `frac: 0.8` holdout keeps ~40
    clusters on the test side and stays silent. Without it, a fix that warned
    whenever a holdout was declared would pass the test above."""
    (tmp_path / "input" / "index.csv").write_text(_FIFTY_CLUSTERS)
    found = codes(write_config({
        "data.units": {
            "from": "index.csv", "key": "patient_id",
            "attributes": ["animal_id", "label"], "cluster_by": "animal_id",
            "holdout": {"method": "random", "frac": 0.8},
        },
        "limits": {"min_clusters": 20},
        "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
    }))
    assert "W-STATS-RESAMPLE-CLUSTERS" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_the_stratum_constancy_check_still_reads_the_whole_roster(
    write_config, tmp_path
):
    """`E-STATS-RESAMPLE-STRATIFY-VARIES` deliberately does NOT move: a
    stratum varying inside a cluster the holdout put on the TRAINING side is
    still an incoherent declaration, and refusing on the whole roster is the
    stricter, correct reading.

    The fixture makes only the training-side clusters vary — pinned by seed, so
    the assertion is about the check's scope rather than about luck."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,animal_id,label\n"
        + "".join(f"p{i},a{i // 2},{'x' if i % 2 else 'y'}\n" for i in range(40))
    )
    found = codes(write_config({
        "data.units": {
            "from": "index.csv", "key": "patient_id",
            "attributes": ["animal_id", "label"], "cluster_by": "animal_id",
            "holdout": {"method": "random", "frac": 0.2, "seed": 1234},
        },
        "limits": {"min_clusters": 2},
        "statistics": {
            "resample": {"method": "bootstrap", "n": 2000, "stratify_by": ["label"]}
        },
    }))
    assert "E-STATS-RESAMPLE-STRATIFY-VARIES" in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k "resample_cluster_warning or holdout_wide_enough or stratum_constancy_still" -x`. The first fails on `W-STATS-RESAMPLE-CLUSTERS in with_holdout`; the other two pass, which is why each carries a companion.

  **Verify the digest before implementing, because the task's premise rests on it.** `validate`'s realization must use the **same digest** `cli.command_run` derives the seed from, or the warning is aimed at a partition the run does not draw. Confirmed at `78bb794`: `cli.py` line 1199 is `digest = design_digest(doc)  # phase 5: pin hashes`, over the same document `validate_config` holds, and `cli.py` imports it as `from publishable.hashes import code_hash, design_digest, parameters_hash`. **Re-check both** — if `command_run`'s digest has since come from anywhere else (a `run_identity` helper, a pre-narrowed dict), the two realizations diverge and this task must derive it the way `command_run` does rather than the way this brief assumes. Also confirmed: `validate.py` imports nothing from `publishable.hashes` at `78bb794`, so the import is new; `hashes.py` imports only the standard library, so there is no cycle.

  **Verify the arithmetic against the fixture before implementing**: 100 rows in clusters of 2 is 50 clusters; a `frac: 0.2` clustered draw allocates whole clusters, so the test side holds close to 10 — print the realized count from `holdout_for` and confirm it is below 20 rather than assuming it.

- [ ] **Step 3: Implement** — in `src/publishable/validate.py`:

```python
def _holdout_test_roster(
    doc: dict[str, Any],
    units_decl: dict[str, Any],
    roster: UnitList | None,
    cluster_by: str | None,
) -> UnitList | None:
    """The holdout's realized **test** partition, or `None` when the design
    declares none or the draw cannot be performed.

    Realized through `units.holdout_for`, the same pure function
    `cli.command_run` realizes it with — which is the reason that function is
    pure at all, `assignment_for`'s own argument: `validate` has to ask "which
    units will the interval rest on" of the same declaration the run asks it
    of, so a second answer computed here would be a check aimed at a partition
    the run does not use.

    **Never raises.** `validate` collects, and this runs over configs that are
    already known bad — a malformed `frac`, an unresolvable column, an unknown
    stratum, a cluster attribute a unit does not carry. Each of those is
    reported by its own check; here they become `None`, and the check that
    reads this simply does not run rather than reporting a second, derived
    fault on top of the one the reader has to fix anyway.
    """
    if roster is None:
        return None
    block = units_decl.get("holdout")
    if not isinstance(block, dict) or not block:
        return None
    try:
        clusters = clusters_of(roster, cluster_by) if cluster_by else None
        plan = holdout_for(
            roster,
            block,
            seed=holdout_seed_for(block, design_digest(doc), roster),
            clusters=clusters,
        )
    except (ContractError, NotImplementedError, KeyError, TypeError, ValueError):
        return None
    test = set(plan.test)
    return UnitList([u for u in roster if u.key in test])
```

  Add `clusters_of`, `holdout_for` and `holdout_seed_for` to the `publishable.units` import list and `design_digest` from `publishable.hashes`. Then in `validate_config`, immediately after `basis` is resolved:

```python
    # The holdout's realized test partition, resolved once and threaded — the
    # denominator a resample's cluster count is actually over. Resolved here
    # rather than inside `_check_resample` so a future second reader gets the
    # same object rather than realizing a second draw.
    holdout_test = _holdout_test_roster(doc, units_decl, roster, usable_cluster)
```

  and change the call to `_check_resample(doc, roster, c, holdout_test=holdout_test)`.

  Then in `_check_resample`, add the parameter and use it for the cluster count only:

```python
def _check_resample(
    doc: dict[str, Any],
    roster: UnitList | None,
    c: Collector,
    holdout_test: UnitList | None = None,
) -> None:
```

  replacing

```python
            groups = fold_basis(roster, cluster_by)
```

  with

```python
            # **The test partition when a holdout is declared, not the whole
            # roster.** `statistics.resample` draws over the per-unit table,
            # which under a holdout holds only the units that recorded — so a
            # percentile interval rests on the clusters of the TEST side, and
            # counting the wider set warns against a denominator no interval
            # used. Wrong in the direction of NOT firing: 50 clusters at
            # `frac: 0.2` leaves roughly 10, and `min_clusters: 20` passed
            # silently.
            #
            # `holdout_test` is `None` whenever no holdout is declared or the
            # draw could not be performed, so this is `roster` unchanged for
            # every other design — including every config in the build before
            # a holdout existed.
            groups = fold_basis(holdout_test if holdout_test is not None else roster, cluster_by)
```

  and add to `_check_resample`'s docstring, in the `W-STATS-RESAMPLE-CLUSTERS` bullet, that it reads the test partition, plus a sentence on why `E-STATS-RESAMPLE-STRATIFY-VARIES` deliberately does not:

```python
    - `E-STATS-RESAMPLE-STRATIFY-VARIES` — **reads the WHOLE roster, on
      purpose**, even under a `data.units.holdout`. Constancy within a cluster
      over the whole roster implies it over any subset, so the wider read is
      the stricter one; the narrower would let a config validate whose training
      half is incoherent and whose test half happens not to show it.
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — two.

  (a) In `src/publishable/validate.py`, revert the `fold_basis` argument to `roster`. `test_the_resample_cluster_warning_counts_the_holdout_s_test_partition` must **FAIL**, and `test_a_holdout_wide_enough_to_keep_the_clusters_does_not_warn` must still pass. Revert in place; re-run.

  (b) Change `_holdout_test_roster`'s return to `UnitList([u for u in roster if u.key in set(plan.train)])`. `test_a_holdout_wide_enough_to_keep_the_clusters_does_not_warn` must **FAIL** (the train side at `frac: 0.8` is ~10 clusters, below 20) **and** `test_the_resample_cluster_warning_...` must **PASS** — which is exactly why the second test exists: a single-config fixture cannot tell "counts the test side" from "counts the smaller side". Revert in place; re-run.

- [ ] **Step 6: Commit** — `fix: count a resample's clusters over the holdout's test partition`.

---

## Task 17: `allocation.json` gains its fourth key

**Files:** Modify `src/publishable/artifacts.py`, `src/publishable/cli.py`. Modify (append) `tests/test_artifacts.py`.

**Interfaces:**
- Consumes: `artifacts.build_allocation_document(group_axes: Mapping[str, ArmPlan]) -> dict[str, Any] | None`; `artifacts.allocation_hash(document) -> str`.
- Produces:

```python
def build_allocation_document(
    group_axes: Mapping[str, "ArmPlan"], holdout: "HoldoutPlan | None" = None
) -> dict[str, Any] | None:
```

  called from `command_run` as `build_allocation_document(group_axes, holdout_plan)`.

**The document shape, settled in task 2 — read § `allocation.json` before writing code.** The `holdout` block is **self-contained**: `train` and `test` always, `seed` only when the split was drawn, `strata` only when non-empty. The top-level `seed`/`strata` are keyed by *axis name* and a holdout is not an axis, so hanging it off a fabricated key would invite a reader to index it as one.

**The "both absent" gate widens.** `if not group_axes: return None` becomes "neither an assignment nor a holdout" — § The other files a run writes says the file is "present when either is declared", and a holdout-only run must write it.

**It records; it does not recompute.** The function takes **no roster**, and that stays true: with nothing to read membership from, it cannot become a second producer of it. The `HoldoutPlan` arrives realized from `_resolved_holdout`.

**`allocation_hash` needs no change**, and its docstring already rules out a `holdout_hash`: it canonicalizes whatever document it is handed. Do not add one.

**Provenance follows for free**: `provenance.allocation`/`allocation_hash` are already `None` exactly when `alloc_doc` is `None`, so widening the gate makes a holdout-only run record both. The comment at that site naming "`holdout` is never in this build's document at all" is **false the moment this lands** and is fixed here, not left to task 19.

- [ ] **Step 1: Write the failing test** — append to `tests/test_artifacts.py`:

```python
def test_a_drawn_holdout_writes_its_own_seed_and_strata_inside_its_block():
    """§ `allocation.json`: the top-level `seed`/`strata` are keyed by AXIS and
    a holdout is not an axis, so its own two travel inside its block. `train`
    and `test` are unit keys, never row numbers — a roster that gains a unit
    renumbers rows and would silently repoint every membership claim."""
    plan = HoldoutPlan(train=("P2", "P7"), test=("P11", "P19"), seed=3310985422,
                       strata=("label",))
    doc = build_allocation_document({}, plan)
    assert doc["holdout"] == {
        "train": ["P2", "P7"], "test": ["P11", "P19"],
        "seed": 3310985422, "strata": ["label"],
    }
    # The axis-keyed blocks stay present and empty, the shape § `allocation.json`
    # prints for a run whose every axis reads a column.
    assert doc["seed"] == {} and doc["strata"] == {} and doc["arms"] == {}


def test_a_read_holdout_records_neither_seed_nor_strata():
    """`ArmPlan`'s own convention for `by_attribute`, one declaration over:
    reading a partition the data already holds is not drawing one, so a `seed`
    would be a false record of a draw that never happened and a `strata` would
    describe how a draw was balanced when none was.

    Asserted as absent KEYS rather than as `null`, matching
    `manifest/input.json`'s "absent rather than null, so 'not hashed' can't be
    misread as 'hashed to nothing'"."""
    plan = HoldoutPlan(train=("P2",), test=("P11",), seed=None, strata=())
    doc = build_allocation_document({}, plan)
    assert doc["holdout"] == {"train": ["P2"], "test": ["P11"]}


def test_a_drawn_unstratified_holdout_records_its_seed_and_no_strata():
    """The third arm, which the two above cannot distinguish between: a drawn
    split with no `stratify_by` carries a seed and no strata, so `strata` is
    omitted for EMPTINESS rather than for the method."""
    plan = HoldoutPlan(train=("P2",), test=("P11",), seed=7, strata=())
    assert build_allocation_document({}, plan)["holdout"] == {
        "train": ["P2"], "test": ["P11"], "seed": 7,
    }


def test_the_document_is_written_when_either_partition_is_declared():
    """§ The other files a run writes: "present when either is declared". The
    four combinations, because a gate reading only one of the two passes three
    of them."""
    arms = {"arm": ArmPlan(levels=("a", "b"),
                           members={"a": ("P1",), "b": ("P2",)},
                           seed=None, strata=())}
    plan = HoldoutPlan(train=("P1",), test=("P2",), seed=7, strata=())
    assert build_allocation_document({}, None) is None
    assert build_allocation_document(arms, None) is not None
    assert build_allocation_document({}, plan) is not None
    both = build_allocation_document(arms, plan)
    assert both is not None and "arms" in both and "holdout" in both


def test_the_allocation_hash_covers_the_holdout_block():
    """`allocation_hash` canonicalizes whatever document it is handed, so the
    holdout's membership is covered without a `holdout_hash` — which
    `allocation_hash`'s own docstring rules out.

    The positive companion is the inequality: two documents differing only in
    which units were held out must hash differently, or the coverage claim is
    empty."""
    a = build_allocation_document({}, HoldoutPlan(("P1",), ("P2",), 7, ()))
    b = build_allocation_document({}, HoldoutPlan(("P2",), ("P1",), 7, ()))
    assert allocation_hash(a) != allocation_hash(b)
    assert allocation_hash(a) == allocation_hash(
        build_allocation_document({}, HoldoutPlan(("P1",), ("P2",), 7, ()))
    )
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_artifacts.py -k "holdout or either_partition or allocation_hash_covers" -x`. All fail: `build_allocation_document` takes one argument today. Add `HoldoutPlan` to the test module's imports.

- [ ] **Step 3: Implement** — in `src/publishable/artifacts.py`, widen the signature and the gate, and replace the **`holdout` is never written here** paragraph:

```python
def build_allocation_document(
    group_axes: Mapping[str, "ArmPlan"], holdout: "HoldoutPlan | None" = None
) -> dict[str, Any] | None:
```

  Replace

```python
    **`holdout` is never written here.** `E-DATA-HOLDOUT-UNSUPPORTED`
    refuses every `data.units.holdout` declaration in this build, so there
    is never a holdout partition to record; the key is omitted entirely
    rather than written `null`, matching `manifest/input.json`'s own
    "absent rather than null, so 'not hashed' can't be misread as 'hashed
    to nothing'" — here, "no holdout key" rather than "a holdout of
    nothing." H3d adds the key once that refusal lifts.
```

  with

```python
    **`holdout` is the fourth key, and it is self-contained.** `train` and
    `test` hold unit keys, in the plan's own order — roster order under
    `by_attribute`, the shuffle's order under a draw — recorded rather than
    re-sorted, for the reason `arms` is. Its `seed` appears only when the split
    was DRAWN and its `strata` only when non-empty, `arms`' own rule one
    declaration over: a `by_attribute` holdout reads a partition the data
    already holds, so a seed would be a false record of a draw that never
    happened and a `stratify_by` would describe how a draw was balanced when
    none was. Both are omitted rather than written `null`, matching
    `manifest/input.json`'s "absent rather than null, so 'not hashed' can't be
    misread as 'hashed to nothing'".

    **Unlike the axis-keyed `seed` and `strata`, the holdout's own two live
    INSIDE its block.** Those two are keyed by axis name and a holdout has no
    axis name; hanging it off a fabricated key would invite a reader to index
    it as one, and `reference.md` § `allocation.json` prints the shape this
    produces.

    **This function still takes no roster**, and the holdout arrives realized
    for the same reason the arms do: `cli._resolved_holdout` draws it once, and
    a second draw here would be a second allocation.
```

  Then the gate and the payload:

```python
    if not group_axes and holdout is None:
        return None
    arms = {
        axis: {level: list(keys) for level, keys in plan.members.items()}
        for axis, plan in group_axes.items()
    }
    seed = {axis: plan.seed for axis, plan in group_axes.items() if plan.seed is not None}
    strata = {axis: list(plan.strata) for axis, plan in group_axes.items() if plan.strata}
    document: dict[str, Any] = {"seed": seed, "arms": arms, "strata": strata}
    if holdout is not None:
        block: dict[str, Any] = {"train": list(holdout.train), "test": list(holdout.test)}
        if holdout.seed is not None:
            block["seed"] = holdout.seed
        if holdout.strata:
            block["strata"] = list(holdout.strata)
        document["holdout"] = block
    return document
```

  Update the `if not group_axes:` gate comment above it: the silent-skip argument it makes is about `group_axes` only and stays true; add one sentence saying a `holdout` reaches this already realized and carries no such shape hazard.

  Then in `src/publishable/cli.py`, change the call to `build_allocation_document(group_axes, holdout_plan)` and rewrite the comment above it, replacing

```python
        # `None` when
        # `group_axes` is empty — no arm assignment resolved for this run —
        # matching "present when either [an arm assignment or a holdout] is
        # declared"; `holdout` is never in this build's document at all
        # (`E-DATA-HOLDOUT-UNSUPPORTED` refuses every declaration of it).
```

  with

```python
        # `None` only when NEITHER partition resolved — no arm assignment and
        # no `data.units.holdout` — matching "present when either is declared".
        # `holdout_plan` is `_resolved_holdout`'s single realization, the same
        # object the runner narrowed and the denominators counted against, so
        # the membership this file claims is the membership the run used rather
        # than a second draw that happens to agree.
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest` (task 1's `allocation.json` absence pin is the one to watch — a run declaring neither must still write nothing), then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Then check the document against § `allocation.json`'s printed example key by key: `seed`, `arms`, `holdout`, `strata` — the example's insertion order is for a human reader and `json.dumps(..., indent=2)` preserves it, so confirm the written file's key order matches what task 2 printed, or fix one of the two.

- [ ] **Step 5: Mutate** — three.

  (a) In `src/publishable/artifacts.py`, change the gate back to `if not group_axes:`. `test_the_document_is_written_when_either_partition_is_declared` must **FAIL** on the holdout-only row. Revert in place; re-run.

  (b) Change `if holdout.seed is not None:` to `block["seed"] = holdout.seed` unconditionally. `test_a_read_holdout_records_neither_seed_nor_strata` must **FAIL**. Revert in place; re-run.

  (c) Change `block["train"]`/`block["test"]` to `list(holdout.test)`/`list(holdout.train)` — swapped. `test_the_allocation_hash_covers_the_holdout_block`'s **inequality** assertion must still pass (both documents move together), and `test_a_drawn_holdout_writes_its_own_seed_and_strata_inside_its_block` must **FAIL**. Both outcomes are the point: a hash test cannot see a swap that is symmetric across its two inputs, which is why the explicit membership assertion exists.

- [ ] **Step 6: Commit** — `feat: allocation.json records the realized holdout split`.

---

## Task 18: Retire `E-DATA-HOLDOUT-UNSUPPORTED`, and the five end-to-end pins

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`. Modify `tests/test_validate.py` (every Part A test's companion assertion), and append to `tests/test_cli.py`.

**Interfaces:**
- Consumes: `validate._check_unimplemented(doc, c)`.
- Produces: the removal of the tuple loop's last entry — **and the loop itself**, since `holdout` is the only member left at `78bb794`.

**This task is larger than one cell suggests, and the scoping said so.** Two halves:

**Half one — the retirement.** `_check_unimplemented`'s `for field, code in (...)` loop holds exactly one entry, `("holdout", "E-DATA-HOLDOUT-UNSUPPORTED")`. Removing it empties the loop, so the loop goes and the surrounding prose — several paragraphs of accumulated "X left this list" commentary — must be rewritten to describe a function whose `data.units` family is now empty rather than one with a hole in it. **Read the whole function before editing it.**

**Then every Part A test's companion assertion is deleted** — one line each, which is exactly what the alongside-not-instead rule bought. `grep -n 'E-DATA-HOLDOUT-UNSUPPORTED' tests/test_validate.py`, delete each `assert "E-DATA-HOLDOUT-UNSUPPORTED" in found` line and its two-line comment, and **check each remaining test still asserts something**: a test whose only assertion was the companion is now vacuous and needs its real assertion restored, not deleting.

**Expect a finding-order flip and pin it.** H3b task 8's experience: retiring a wholesale refusal changes which finding a `Collector` reports first, and any test asserting on `findings[0]` or on a message's position moves. `grep -n "findings\[0\]" tests/` before and after.

**Re-check the `E-REPL-KIND` route.** `{kind: holdout, n: 1}` reports `E-REPL-KIND` with the message *"`holdout` is not a repeat kind — declare `data.units.holdout` instead"*. That message now points at a **built** field. Assert it still fires and that the config it recommends now validates.

**`replication.REPL_DECLARATION_CODES` stays as it is** — task 6 sited the `fold` exclusion in `validate` rather than in `resolve_repeats`, so nothing there changes.

**Half two — the five end-to-end pins, one per wiring task.** Tasks 13–17 had no config that could reach `command_run`. This is where they get one, and the list is enumerated rather than discovered:

1. **Task 13, realize once:** `allocation.json`'s `holdout.train ∪ holdout.test` is exactly the roster, and its `seed` equals `holdout_seed_for` over the run's own digest.
2. **Task 14, `io.units`/`.train`:** a step at each of two scopes sees the test partition as `io.units` and the training one as `io.units.train`, and their union is the roster.
3. **Task 15, the denominators:** `n.resolved` in `executions.jsonl` and in every metric's `n` equals the **test** size, while `provenance.units.n` equals the whole roster — the two numbers side by side, which is the whole ruling.
4. **Task 15 again, `max_failed_fraction`:** a run whose every test unit fails trips the guard, where an un-narrowed denominator would have divided by five times as many.
5. **Task 17, `allocation.json`:** the file exists, `provenance.allocation` and `allocation_hash` are non-`None`, and re-canonicalizing the parsed file reproduces the hash.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
_HOLDOUT_SEEING_STEP = '''\
# src/{pkg}/steps/step01_split.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        io.write("split.json", {{
            "test": sorted(u.key for u in io.units),
            "train": sorted(u.key for u in io.units.train),
        }})
        for unit in io.units:
            io.record(unit.key, {{"value": 1.0}})
        return {{"n": len(io.units)}}
'''


def test_a_declared_holdout_now_validates_and_runs(tmp_path, capsys):
    """`E-DATA-HOLDOUT-UNSUPPORTED` is retired, so this config reaches
    `command_run` for the first time. Pins tasks 13, 14, 15 and 17 end to end —
    the five wiring tasks had no config that could reach the CLI while the
    wholesale refusal stood, and this is where they get one."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=20,
        units_overrides={"holdout": {"method": "random", "frac": 0.2, "seed": 4321}},
        _starter_step=_HOLDOUT_SEEING_STEP,
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert run["status"] == "completed"

    # Task 17: the file, the provenance pair, and the hash.
    alloc_path = doc["run_dir"] / "allocation.json"
    assert alloc_path.exists()
    alloc = json.loads(alloc_path.read_text())
    assert run["provenance"]["allocation"] == "allocation.json"
    assert run["provenance"]["allocation_hash"] == "sha256:" + hashlib.sha256(
        json.dumps(alloc, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    # Task 13: realized once, over the whole roster, at the pinned seed.
    assert alloc["holdout"]["seed"] == 4321
    assert len(alloc["holdout"]["test"]) == 4
    assert len(alloc["holdout"]["train"]) == 16
    assert set(alloc["holdout"]["train"]) | set(alloc["holdout"]["test"]) == set(
        run_roster_keys(doc)
    )
    assert not set(alloc["holdout"]["train"]) & set(alloc["holdout"]["test"])

    # Task 14: the step saw the same two lists the record claims.
    seen = json.loads(next(doc["run_dir"].rglob("split.json")).read_text())
    assert seen["test"] == sorted(alloc["holdout"]["test"])
    assert seen["train"] == sorted(alloc["holdout"]["train"])

    # Task 15: the denominator is the TEST partition, and the roster's identity
    # is not. The two numbers asserted side by side, which is the ruling.
    ledger = [
        json.loads(line)
        for line in (doc["run_dir"] / "executions.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert ledger
    for record in ledger:
        assert record["n"]["resolved"] == 4, record
        assert record["n"]["completed"] == 4, record
        assert record["n"]["failed"] == 0, record
    assert run["provenance"]["units"]["n"] == 20
    for block in run["results"]["conditions"][0]["aggregated"].values():
        for metric in block.values():
            if isinstance(metric, dict) and isinstance(metric.get("n"), dict):
                assert metric["n"]["resolved"] == 4, metric


def test_max_failed_fraction_is_measured_against_the_test_partition(tmp_path, capsys):
    """Task 15's second pin. A step failing on every test unit is 4 of 4 —
    over the un-narrowed roster it would be 4 of 20, a fifth of the declared
    threshold, and the guard would not fire. The number is what separates the
    two readings, so the fraction is chosen to sit between them."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=20,
        units_overrides={"holdout": {"method": "random", "frac": 0.2, "seed": 4321}},
        limits={"max_failed_fraction": 0.5, "max_executions": 100},
        _starter_step=_ALWAYS_FAILING_STEP,
        expect_exit=EXIT_PARTIAL,
    )
    ledger = [
        json.loads(line)
        for line in (doc["run_dir"] / "executions.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert ledger
    assert all(r["n"]["resolved"] == 4 for r in ledger)
    # The guard fired: the plan stopped short of its full length.
    assert len(ledger) < _planned_execution_count(doc)


def test_a_holdout_repeat_kind_still_routes_to_the_built_field(write_config):
    """`{kind: holdout}` reports `E-REPL-KIND` pointing at
    `data.units.holdout` — and that field is now BUILT, so the message names a
    real destination rather than a refused one. Both halves asserted, because
    the route being correct and the destination existing are two claims."""
    overrides = _holdout(None)
    overrides["replication"] = {
        "repeats": [{"kind": "holdout", "n": 1}], "order": "as_declared"
    }
    by_code = messages_by_code(write_config(overrides))
    assert "E-REPL-KIND" in by_code
    assert "data.units.holdout" in by_code["E-REPL-KIND"]
    assert "E-DATA-HOLDOUT-UNSUPPORTED" not in by_code
```

  `run_roster_keys`, `_ALWAYS_FAILING_STEP` and `_planned_execution_count` are helpers to reuse or add — **read `tests/test_cli.py` first**; a step that raises and a way to count the planned executions both already have precedents there. `hashlib` must be imported in that module.

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k "declared_holdout_now or max_failed_fraction_is_measured or holdout_repeat_kind_still" -x`. The first two fail because `main(["run", ...])` exits `EXIT_WRONG` — `validate` refuses the config, no run directory exists. That failure **is** the confirmation.

- [ ] **Step 3: Implement** —

  (a) In `src/publishable/validate.py`, delete the `("holdout", "E-DATA-HOLDOUT-UNSUPPORTED"),` entry, and with it the now-empty `for field, code in (...)` loop and its `if units.get(field):` body. Rewrite the surrounding commentary — it is several paragraphs of "X left this list" accumulated over many slices — into a statement of what is true after this commit: **no `data.units` sub-field is refused wholesale any more**, each is checked for real by its own function, and the `statistics.null_test` / `{resolver: ...}` refusals that remain live elsewhere in the module are what the family now consists of. Keep the *argument* — a declaration that changes no behaviour is the failure the family exists to prevent — because the next field to be built needs it.

  (b) In `docs/reference.md`, edit § The one config file's "**Three declarations above are not yet built**" sentence: it becomes **two** — `{resolver: <name>}` and `statistics.null_test` — with `data.units.holdout` removed from the list. Remove the `NOT BUILT` marker from the `holdout:` line in the fenced schema and give it the shape comment its `measurements` sibling carries. Fix the trailing clause "`.holdout` inherits the same treatment when its slice lands", which is now discharged by task 3. **Do not enumerate the built names in place of the count** — the sentence derives its claim from the `NOT BUILT` markers, and replacing it with a list converts a self-maintaining statement into a maintenance obligation nobody owns.

  (c) `grep -n 'E-DATA-HOLDOUT-UNSUPPORTED' tests/test_validate.py` and delete each companion assertion and its comment. Then re-read every test you touched: one whose **only** assertion was the companion is now vacuous — restore its real assertion rather than deleting the test.

  (d) `grep -rn 'E-DATA-HOLDOUT-UNSUPPORTED' src/ tests/ docs/` must return **zero hits, everywhere.** Settled rather than left as a question: § The one config file states that the whole `-UNSUPPORTED` family is "deliberately absent from the validate-time registry", so § Errors never carried a row for this code and there is none to retire. The only permissible hits are in `docs/superpowers/` — the development record, which is never retro-edited.

  (e) `grep -n "findings\[0\]" tests/` and re-run the whole suite: pin any finding-order flip where it surfaces rather than reordering checks to preserve an accident.

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest` in full — **this is the run that matters**, because every Part A test changed. Then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Then the mechanical and cross-document passes on `docs/reference.md`.

- [ ] **Step 5: Mutate** — three, each aimed at a different wiring task, because this is the first commit at which any of them is reachable end to end.

  (a) In `src/publishable/cli.py`, change the `execute_plan(units=eval_roster)` site back to `units=roster`. `test_a_declared_holdout_now_validates_and_runs` must **FAIL** on `record["n"]["resolved"] == 4`, and `test_max_failed_fraction_is_measured_against_the_test_partition` must **FAIL** on the guard firing. Revert in place; re-run.

  (b) In `src/publishable/cli.py`, change `holdout_train=` to `holdout_train=None`. `test_a_declared_holdout_now_validates_and_runs` must **FAIL** — the step raises `E-STEP-UNITS-UNAVAILABLE` reaching for `io.units.train`, so the run is `partial` and `run["status"] == "completed"` trips. Revert in place; re-run.

  (c) In `src/publishable/cli.py`, change `build_allocation_document(group_axes, holdout_plan)` to `build_allocation_document(group_axes)`. `test_a_declared_holdout_now_validates_and_runs` must **FAIL** on `alloc_path.exists()`. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: retire E-DATA-HOLDOUT-UNSUPPORTED — a declared holdout now runs`.

---

## Task 19: The owned prose sweep — thirteen sites in `src/`, by claim rather than by file

**Files:** Modify `src/publishable/validate.py`, `src/publishable/cli.py`, `src/publishable/materialize.py`, `docs/reference.md`. Modify `tests/test_materialize.py` if it pins the generated line.

**Interfaces:**
- Consumes: nothing. This task changes comments, docstrings and one generated line.
- Produces: no false present-tense claim about `holdout` anywhere in `src/`.

**The old scoping counted four. There are thirteen.** `CLAUDE.md`: three sweeps in one slice stopped one file short — one covered `src/` and `docs/` but not `tests/`, one fixed a sentence in `correction.py` and missed the same sentence in the function that falsified it, one stopped at the file its brief happened to name. So this sweep is **by claim**, and the thirteen are enumerated below with the task that owns each. Nine were fixed by the task that falsified them; **this task verifies all thirteen and fixes the four nobody owned.**

| # | Site | The claim | Owner |
|---|---|---|---|
| 1 | `validate.py`, `_check_unimplemented`'s tuple-loop entry | The entry itself | Task 18 |
| 2 | `validate.py`, `_check_sweep`'s "two `data.units` sub-fields — `holdout` and a `resolver` source — are still read by nothing" | Becomes **one** | Task 18 |
| 3 | `validate.py`, `_check_fold_stratify_by`'s "`data.units.holdout.stratify_by` halves belong to the slices that build those blocks" | Discharged | **This task** |
| 4 | `validate.py`, `_check_units`' "`cluster_by`, `weight_by`, and `holdout` are not read by `resolve_units` at all" | False | Task 9 |
| 5 | `artifacts.py`, `build_allocation_document`'s "**`holdout` is never written here.**" | False | Task 17 |
| 6 | `cli.py`, the `allocation.json` write site's "`holdout` is never in this build's document at all" | False | Task 17 |
| 7 | `cli.py`, the provenance write site's `None`/`None` pairing comment | The gate changed | **This task** |
| 8 | `cli.py`, the `clusters_of` note's "`holdout` and `assign` **will** each read the same attribute under their own" | Future becomes present | **This task** |
| 9 | `envelope.py`'s "`holdout` stays whole for now… and H3d closes it" | False | Task 3 |
| 10 | `envelope.py`'s "a misspelled… `methodd` in `holdout` is reported by no check in this build" | False | Task 3 |
| 11 | `units.py`, `resolve_units`' "**`holdout.from` still is not** [reachable]" | False | Task 9 |
| 12 | `units.py`, `CONSTANT_COLUMN_RULES`' "**`holdout.from` is not reachable through this registry today**… nothing in this task builds one" | False | Task 9 |
| 13 | `materialize.py`'s generated `holdout: null # optional single fixed train/test split` line | Needs the shape comment its `measurements` sibling carries | **This task** |

**Eight forward references are fine as written and must NOT be touched**: `artifacts.py`'s two `holdout_hash` rule-outs (correct, and in advance), `replication.py`'s `E-REPL-KIND` route (already true), `stats.py`'s two, `validate.py`'s three remaining, and `generators/template.py`'s example prose in a generated file. Changing a correct forward reference to a present-tense claim is the same defect in the other direction.

- [ ] **Step 1: Write the failing test** — a throwaway sweep, run in Step 2 and not kept. **Filter the file list, never the output** — a reviewer checking this exact rule once lost a true hit to `grep -v superpowers`, because the matching line contained that path:

```bash
cd /Users/joon/src/tries/publishable
# Every present-tense absence claim about `holdout`. Read each hit and classify
# it: owned (false now) or forward reference (fine).
grep -rn "holdout" src/publishable/ | grep -in "not yet\|never\|not read\|no check\|still is not\|not reachable\|will \|for now\|NOT BUILT\|this build"
# The four documents, named individually — `*.md` no longer means what it used
# to now that the development record is tracked.
grep -n "holdout" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md | grep -in "NOT BUILT\|not yet\|refused today\|when its slice"
# The generated config line and anything pinning it.
grep -rn "optional single fixed train/test split" src/ tests/ docs/
```

- [ ] **Step 2: Run it, confirm it fails** — the first sweep returns the four unowned sites (3, 7, 8) plus any of the nine an earlier task missed; the second returns § `E-CONFIG-KEY-UNKNOWN`'s "not among them only because the whole block is refused today"; the third returns the `materialize.py` line and its test pin if there is one. **Prove each sweep can fail** by running it against a string known to be present — `grep -rn "holdout" src/publishable/units.py` must return many hits.

- [ ] **Step 3: Implement** — four code sites and one document site, plus whatever the sweep turned up that an earlier task missed.

  (a) `src/publishable/validate.py`, `_check_fold_stratify_by`'s docstring — replace

```python
    particular `stratify_by`, and its `data.units.assign.<axis>.stratify_by` and
    `data.units.holdout.stratify_by` halves belong to the slices that build those
    blocks, so neither is discharged by this.
```

  with

```python
    particular `stratify_by`, and its `data.units.assign.<axis>.stratify_by` and
    `data.units.holdout.stratify_by` halves are `_check_assign`'s and
    `_check_holdout`'s, under their own codes
    (`E-DATA-ASSIGN-STRATIFY-UNKNOWN`, `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`), so
    neither is discharged by this. Three checks answer to one row, and the row
    carries no code for that reason.
```

  (b) `src/publishable/cli.py`, the provenance write site's pairing comment — replace

```python
            # "allocation.json" and its hash, when an arm assignment or a
            # holdout is declared — `None`/`None` together exactly when
            # `alloc_doc` was never written, the same pairing `units`/
            # `units_hash` already use above.
```

  with

```python
            # "allocation.json" and its hash, `None`/`None` together exactly
            # when `alloc_doc` was never written — which is now when NEITHER an
            # arm assignment nor a `data.units.holdout` resolved, the gate
            # `build_allocation_document` widened. The same pairing `units`/
            # `units_hash` already use above, and the same reason: a file named
            # in the record and absent from disk is worse than an honest
            # `None`.
```

  (c) `src/publishable/cli.py`, the `clusters_of` note — replace

```python
        # whose config declares `fold.stratify_by`, and which code a missing value
        # belongs under is a property of the declaration being served — `holdout`
        # and `assign` will each read the same attribute under their own.
```

  with

```python
        # whose config declares `fold.stratify_by`, and which code a missing value
        # belongs under is a property of the declaration being served — `holdout`
        # and `assign` each read the same attribute under their own
        # (`E-DATA-HOLDOUT-STRATIFY-VARIES`, `E-DATA-ASSIGN-STRATIFY-VARIES`),
        # which is why three declarations naming one attribute produce three
        # codes rather than one shared one.
```

  (d) `src/publishable/materialize.py`, the generated line — replace

```python
        "    holdout: null                  # optional single fixed train/test split",
```

  with

```python
        "    holdout: null                  # e.g. {method: random, frac: 0.2}"
        " — one fixed train/test split",
```

  matching the shape its `measurements` sibling carries (`# e.g. {by: read_id, collapse: mean}`), which is the convention for a *built* block materialized as `null`. Keep the column alignment of the surrounding lines — check the generated file by eye, and update `tests/test_materialize.py` if it pins this text.

  (e) `docs/reference.md`, § `E-CONFIG-KEY-UNKNOWN`'s row — replace the parenthetical "and `holdout` is not among them only because the whole block is refused today as `E-DATA-HOLDOUT-UNSUPPORTED`, which makes its gap latent rather than live" with a statement that `data.units.holdout` **is** closed one level in, at its five fixed-name keys, so a typo inside it is reported — leaving `data.units.from`'s mapping as the leaf whose gap the row is actually about.

- [ ] **Step 4: Run, confirm it passes** — re-run all three sweeps: the first returns only the eight forward references, each of which you have read and confirmed is still true; the second returns nothing; the third returns the new line and its test pin. Then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Then the mechanical pass on `docs/reference.md`.

- [ ] **Step 5: Mutate** — the sweep is the thing that can silently be wrong, so mutate it. Temporarily reintroduce the sentence "`holdout` stays whole for now" into `src/publishable/envelope.py`'s module docstring and re-run the first sweep: it must **return that line**. Remove it in place and re-run: gone. Then do the same for the documents sweep by temporarily adding `NOT BUILT` beside a `holdout` mention in `docs/reference.md`.

- [ ] **Step 6: Commit** — `docs: sweep every present-tense claim that a holdout is unbuilt`.

---

## Task 20: The reader-facing half — the honest count, and `experimental-designs.md`

**Files:** Modify `docs/feasibility-llm-growth-studies.md`, `docs/experimental-designs.md`, `docs/reference.md`, `CLAUDE.md`.

**Interfaces:**
- Consumes: nothing.
- Produces: the dated, commit-pinned build claim, and the two normative sections a reader checks against.

**Never state a build fact undated.** `CLAUDE.md`'s feasibility procedure step 10: a claim about what the tool *does today* is perishable in a way a spec claim is not, so it is dated and pinned to a commit and kept in a section of its own. § Executability on this build is the shape — "Measured on \<date\> against commit \<sha\>", every refusal named by its code.

**The honest count, and it is not the charter's.** Write **this**, not "unblocks 6 of 9":

> H3d retires **one refusal that 6 of 9 configs hit** (`E-DATA-HOLDOUT-UNSUPPORTED`, E1–E6; the three shortcut configs declare `holdout: null`), and **zero experiments newly execute.** All nine still declare a resolver and still earn `E-DATA-RESOLVER-UNSUPPORTED`, which is H7b's. C1–C3 keep `E-DATA-WEIGHT-CONTRAST` on top of that.
>
> Under a **table-roster substitution the analysis does not itself make**: E1, E2 and E5 would validate clean and could run. **E3, E4 and E6 would validate clean and still cannot execute** — each reads its frozen compiled program through `io.reuse_from`, which this analysis's own § Executability records as *"no such method exists yet"*. So even the generous count is **three**, not six, and it rests on a substitution nobody has written.

**Re-measure rather than restate.** The scoping measured this on 2026-08-15 against `78bb794`, and this slice has changed the build. **Run the six holdout-declaring configs through `validate` yourself** and write down what they actually report at the merge commit. If any number differs from the scoping's, the measurement wins and the difference goes in the commit message.

- [ ] **Step 1: Write the failing test** — a measurement script, kept only as long as this task, in the scratchpad rather than in the repo:

```bash
cd /Users/joon/src/tries/publishable
# Extract each YAML block from the feasibility analysis into a scratch config,
# point it at a real repo and a table roster, and run `validate`. Record the
# exact code list per config. This is a MEASUREMENT, not a test — its output is
# what gets written into the dated section.
git rev-parse HEAD          # the sha to pin
date -u +%Y-%m-%d           # the date to write
```

- [ ] **Step 2: Run it, confirm it fails** — `grep -n "Measured on" docs/feasibility-llm-growth-studies.md` shows the previous measurement's date and sha, both now stale. That is the confirmation: the section exists and is out of date, which is exactly the state step 10 exists to keep visible.

- [ ] **Step 3: Implement** — four edits.

  (a) `docs/feasibility-llm-growth-studies.md` § Executability on this build: **append** a new dated measurement rather than editing the old one — this is analysis output, and a correction is appended and says what it replaces. New heading line "Measured on \<today\> against commit \<sha\>", then the honest-count block above with every code named, then the per-config table of what each of E1–E6 and C1–C3 now reports. Say explicitly that `E-DATA-HOLDOUT-UNSUPPORTED` no longer appears and that `E-DATA-RESOLVER-UNSUPPORTED` still does.

  (b) `docs/experimental-designs.md` § Train-test holdout: check the section against what this slice built — every claim it makes must now be honoured or refused with a named code — and § Mistakes core prevents: confirm nothing it lists became merely-discouraged rather than structurally impossible. The cells refusal *strengthens* that section rather than weakening it; say so if the section's wording implies folds and holdouts are drawn per cell (task 8 already rewrote the one paragraph that did — **read it first** rather than rewriting it twice).

  (c) `docs/reference.md`: re-check § What core will not do for you against this slice. A holdout inside cells is now a **named refusal with a code**, not an unstated gap, so it belongs there if that list enumerates refusals of that kind.

  (d) `CLAUDE.md`: update the slice-order paragraph. H3d has landed; the remaining order is **H4b → H7b → the rest**, with H3c-3 named as the owner of both the cells retrofit and the cells refusal's retirement. State H3d's payoff in the honest form — one refusal retired that 6 of 9 hit, one live defect closed, zero experiments newly executing — and keep the existing warning that a refusal count read as an executable count is what step 10 exists to prevent.

- [ ] **Step 4: Run, confirm it passes** — `grep -n "Measured on" docs/feasibility-llm-growth-studies.md` shows both the old measurement and the new one, in that order, with the new one naming what it replaces. Then the **mechanical pass** on all four files (the feasibility analysis is exempt from the cross-document pass and subject to this one in full): links and anchors resolve, no duplicate anchors, table rows match headers, no trailing whitespace or tabs, `×` not `x`, hyphens not en dashes in anything that becomes an anchor. Then the **cross-document pass** on the three normative files: the shared worked example is untouched (this slice adds no `cohort-pilot` numbers — confirm it), config completeness holds (§ The one config file's fenced example carries every `holdout` field this slice enforces), every enum comment lists every value its table defines, and nothing shows a derived value as a settable input. Then `uv run pytest` and the three other commands one last time.

- [ ] **Step 5: Mutate** — the claim that can silently be wrong here is the measurement. Take the **one** config the new section says now validates clean under a table-roster substitution, break one field of it deliberately (a `frac: 0` say), and confirm `validate` reports the code the section would have to name. If it reports something else, the section's claim about that config is what is wrong.

- [ ] **Step 6: Commit** — `docs: the honest H3d payoff, dated and pinned`. Use `git add -f` for anything under `.superpowers/sdd/` if the workspace gitignore has been clobbered, and restore that file's content to a bare `*` if `scripts/sdd-workspace` has rewritten it.

---

## Closing checks before the branch is finished

Not a task — the whole-branch review's own list, gathered here so it is not re-derived.

- `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` all clean.
- `grep -rn "E-DATA-HOLDOUT-UNSUPPORTED" src/ tests/ docs/` returns nothing.
- Task 1's two pins still pass, unedited. A no-holdout run is byte-identical to `78bb794`.
- Every one of the thirteen codes in Global Constraints has a § Errors row, a check that emits it, and a test that sees it emitted. `CLAUDE.md`: a row and a code are the same check seen from two ends, and **either end can be missing**.
- Every mutation named in the plan was actually run, actually failed, and was reverted **in place**.
