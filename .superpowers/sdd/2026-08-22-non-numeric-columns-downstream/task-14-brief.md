## Task 14: `report` and `study` pinned as readers of `aggregated`, and three shipped docstrings re-derived

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: two real commands.** The scoping's task 14 and the design's Fixture J. `report.py` and
`study.py` both walk `aggregated` — the key this slice changes — and the scoping's own instruction was
that this **must be pinned rather than assumed**, because it is precisely the additive-only claim the
ruling requires.

**Files:** `tests/test_report.py`, `tests/test_study.py`, `tests/test_cli.py` (docstrings)

- [ ] **Step 1: Fixture J — `report` over Fixture A's run.** Render the run's `run.yaml` through
      `publishable report` and assert the condition table holds rows for `n_valid`, `n_rows`,
      `mean_score` and `score` and **no row for `valid`**. **Assert on the rendered text**, and say what
      else in that output could produce the substring you assert — the scoping measured `report`
      rendering a non-numeric `value` **without complaint** when one reached `aggregated`, so a bare
      `assert "valid" not in out` would be satisfied by the absence of the *word*, not of the row.

- [ ] **Step 2: `study`'s thin-metric floor sees the same four entries.** A two-member bundle through
      `report study.yaml`. `study.py`'s `_floor_metric_entries` walks every entry carrying `basis`,
      **structurally**, so a string wearing a metric block's shape would enter the floor check. Assert the
      four entries and no fifth. **Grep `_floor_metric_entries` and read the walk before asserting what it
      sees**; report the grep.

- [ ] **Step 3: re-derive the three shipped test docstrings the scoping measured, and grep each claim.**
      **All three exist at the names the scoping gave** — confirmed at `ee8085e`,
      `grep -c` over `tests/test_cli.py` returns hits for all three; **run it and report it.**
      - `test_a_run_without_a_holdout_pins_its_denominators_and_artifacts` says *"`stats.summarize_step`
        drops a bool column outright"*. **False in the wrong function**: `summarize_step` never sees the
        column; it receives `{}` from the collapse. Re-derive it to what the test actually pins.
      - `test_a_baseline_sweep_reports_a_delta` says the scaffold's step *"records only a bool …
        filtered by `_is_numeric`"*, which names the right predicate in the wrong function. Re-derive.
      - `test_an_unclustered_resampled_contrast_draws_what_it_always_drew` says the default step *"grows
        no `basis: units` column"*, which **is true and stays.** Say so; do not edit it.
      **Both false docstrings become true after this slice in a different way than they were false**, so
      **delete the wrong clause and state what the test pins**, rather than relocating the claim. *Prefer
      deleting a claim to rewriting it.*

- [ ] **Step 4: the mutations — two.**
      (i) Empty `summarize_step`'s `_is_numeric` gate in the column loop, so a `valid` metric block is
      published. **Step 1's no-`valid`-row assertion and step 2's four-entry assertion must both FAIL.**
      *Why the branches differ:* the block reaches `aggregated`, both readers walk it structurally, and
      neither refuses it — measured by the scoping.
      (ii) Point `study.py`'s floor walk at a shallower path. **Step 2 must FAIL.** *Why the branches
      differ:* the shipped walk is the deep one, and a shallower walk was **dead on every real record** on
      a preceding slice — this is the fixture that would have caught it.
      **Named blind in advance:** the three docstring edits. Their replacement is the B4 review reading
      each against the code, and **the greps this task must report.**

- [ ] **Step 5: run** the four commands. **Delta:** Fixture J's two arms; three docstrings edited, one left
      alone. **Commit:** `H5b task 14: report and study pinned as readers of aggregated, and three shipped
      docstrings re-derived`.

---

