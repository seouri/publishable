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

