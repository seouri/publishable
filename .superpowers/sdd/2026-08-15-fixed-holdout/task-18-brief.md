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

