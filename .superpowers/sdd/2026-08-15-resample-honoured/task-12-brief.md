## Task 12: Retire `E-STATS-RESAMPLE-UNSUPPORTED`

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`, `docs/feasibility-llm-growth-studies.md`. Test `tests/test_validate.py`.

**Interfaces:**
- Consumes: `validate._check_unimplemented(doc, c)` at `src/publishable/validate.py:2931`, whose two-entry loop over `("resample", …)` / `("null_test", …)` sits at `:3138–3158`.
- Produces: a config declaring `statistics.resample` that reaches `command_run` at all. **Every later task's end-to-end test depends on this**, because `cli` always validates before running and an error exits before a run directory exists.

**Why it lands here and not later.** Tasks 4–11 built the validate-time refusals and the constructions; nothing yet honours the declaration, so retiring the blanket refusal opens a **two-task window** (this task through Task 14) in which a declared `resample` validates clean and changes only the derived draw count. That window is closed by Task 14 and is the smallest one available: retiring any earlier would make the window five tasks wide, and retiring any later would make Tasks 13–14 untestable end to end. `E-STATS-RESAMPLE-UNITS`, `E-STATS-RESAMPLE-METHOD`, `E-STATS-RESAMPLE-N`, `E-STATS-RESAMPLE-STRATIFY-UNKNOWN`, `E-STATS-RESAMPLE-STRATIFY-VARIES`, `W-STATS-RESAMPLE-FAMILY` and `W-STATS-RESAMPLE-CLUSTERS` are all already in place, so the shape is checked before it is honoured.

**`E-STATS-NULLTEST-UNSUPPORTED` stays.** It is an independent key in the same loop, owned by H4d, and `p_value` appears nowhere in `src/`.

**A `-UNSUPPORTED` code is retired wholesale and is absent from the registry.** Do not add a "retired" row to § Errors `validate` reports — that family is deliberately outside that table, and § The one config file's `NOT BUILT` list is where a refused block is named. Retiring means the name disappears from `src/` and from `docs/` except where a historical record deliberately keeps it.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
def test_a_declared_resample_is_no_longer_refused_wholesale(write_config):
    """H4a implements it, so the blanket refusal retires with the slice — the
    same way `E-STATS-CONTRASTS-UNSUPPORTED` and `E-STATS-REPORTBY-UNSUPPORTED`
    retired with theirs."""
    found = codes(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id"},
                "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
            }
        )
    )
    assert "E-STATS-RESAMPLE-UNSUPPORTED" not in found
    # The positive companion, in the same test: the config is now CLEAN of every
    # resample finding, so this cannot pass by the refusal having been renamed.
    assert not [code for code in found if code.startswith("E-STATS-RESAMPLE")]


def test_a_declared_null_test_is_still_refused(write_config):
    """The sibling entry in the same loop is H4d's and does not retire here. A
    single-key retirement that deleted the loop would pass the test above and
    fail this one."""
    assert "E-STATS-NULLTEST-UNSUPPORTED" in codes(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id"},
                "statistics": {"null_test": {"method": "permutation", "n": 5000,
                                             "shuffle": "cohort"}},
            }
        )
    )


def test_the_retired_resample_code_appears_nowhere_in_src():
    """A retired `-UNSUPPORTED` code is retired wholesale. Filtering the FILE
    LIST rather than the sweep's output, because a matching line can itself
    contain whatever you would have excluded."""
    import pathlib

    hits = [
        path
        for path in pathlib.Path("src").rglob("*.py")
        if "E-STATS-RESAMPLE-UNSUPPORTED" in path.read_text()
    ]
    assert hits == []
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k no_longer_refused_wholesale or retired_resample_code -x`. Both fail; `test_a_declared_null_test_is_still_refused` passes and is the control that keeps the sibling alive.

- [ ] **Step 3: Implement** —

  (a) `src/publishable/validate.py`, `_check_unimplemented`: delete the `("resample", "E-STATS-RESAMPLE-UNSUPPORTED", "no resampling scheme runs")` tuple from the loop, leaving `null_test` as the only entry. Rewrite the loop as a single guarded check if `ruff` objects to a one-entry loop; keep the message text for `null_test` byte-identical.

  Then edit the docstring paragraph that reads "`statistics.resample` and `.null_test`, and a top-level `hypotheses` block, are refused the same way — a declared 2000-draw bootstrap or a pre-registered hypothesis that runs and reports success while honoring neither is the same silent-no-op class." Replace with:

```
    `statistics.resample` is no longer in this family: `_check_resample` checks
    the declaration for real — the method enum, the 80-draw floor, the strata
    against `data.units.attributes`, the roster's absence, and the cluster count
    — and `cli.command_run` resolves the block and threads it into every
    interval construction, so a declared resample changes the record. That is
    the test this family applies. `.null_test` is still refused the same way: a
    declared 5000-draw permutation that runs and reports nothing is the
    silent-no-op class, and `p_value` exists nowhere in this build.
```

  Also update the comment at `:3134–3138` that reads "`materialize.py` writes only two of these keys into a generated config … so `resample` and `null_test` are simply absent there" — it now names one key.

  (b) `docs/reference.md`:
  - § The one config file's paragraph currently says "**Four declarations above are not yet built**: `data.units.holdout`, the `{resolver: <name>}` form of `data.units.from`, and `statistics.resample` and `statistics.null_test`." Change *Four* to **Three** and drop `statistics.resample` from the list. **Check every count phrase near it** — this repo has been wrong twice on a count near an edited row.
  - Task 2 already removed `NOT BUILT;` from the `resample:` line. Verify with `grep -n 'NOT BUILT' docs/reference.md` that exactly the three remaining declarations carry a marker.
  - § How a metric becomes a number / § Statistical reporting: remove any sentence saying a declared `resample` is refused in this build. Grep for the code: `grep -rln 'E-STATS-RESAMPLE-UNSUPPORTED' docs/` and fix each file the **list** names.

  (c) `docs/feasibility-llm-growth-studies.md` § Executability on this build — **re-date it, do not edit it in place.** It currently opens "Measured on 2026-08-14 against commit `cb96c7d`". A dated build claim is re-measured or it is not changed. Concretely: re-run `uv run publishable validate` against the section's own configs (or, if they are not materialized in the repo, state that the refusal table is re-derived from `validate.py`'s emit sites rather than from a run, and say so in the section), then rewrite the opening as "Measured on <today's date> against commit `<sha of this commit's parent>`", delete the `E-STATS-RESAMPLE-UNSUPPORTED` row from the refusal table, and rewrite the "**Six of the nine are one slice-set away**" paragraph — the remaining blockers are the plugin registry (9 of 9) and `data.units.holdout` (6 of 9), with `E-DATA-WEIGHT-CONTRAST` on C1–C3. **Do not write "unblocks 8 of the nine" anywhere.** The honest statement is: one refusal retired that 8 of 9 configs hit, a regression preserved, and **zero experiments newly executing** — E1–E6 still declare `holdout`, C1–C3 still declare `weight_by` beside a baseline, and all nine declare a resolver.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k resample or null_test`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`. Then: `grep -rln 'E-STATS-RESAMPLE-UNSUPPORTED' src/ docs/ tests/` — the only permitted hits are `docs/superpowers/**` (gitignored) and the new test asserting its absence. Then the doc mechanical pass on `reference.md` **and** `feasibility-llm-growth-studies.md` (the latter is exempt from the cross-document pass, not from the mechanical one).

- [ ] **Step 5: Mutate** — in `validate.py`, re-add the `resample` tuple to `_check_unimplemented`'s loop. Run `uv run pytest tests/test_validate.py -k no_longer_refused_wholesale`. It must FAIL. Delete `__pycache__`, remove the tuple in place, re-run. Second mutation: delete the **whole** loop rather than the one entry; `test_a_declared_null_test_is_still_refused` must FAIL, proving the sibling is genuinely load-bearing here and not incidentally surviving. Revert in place.

- [ ] **Step 6: Commit** — `feat: retire E-STATS-RESAMPLE-UNSUPPORTED; re-date the feasibility build section`.

---

