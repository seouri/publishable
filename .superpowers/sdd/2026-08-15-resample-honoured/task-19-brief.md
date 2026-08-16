## Task 19: The `init`-materializes-optional-blocks residual

**Files:** Modify `docs/superpowers/spec-defects.md`. Possibly `src/publishable/materialize.py` and `docs/reference.md` — see the ruling below.

**Interfaces:**
- Consumes: the open entry in `docs/superpowers/spec-defects.md` under *"The generated config calls itself 'the complete parameter set' before it is one"*, whose **Open residual, routed** paragraph reads: "whether `init` should materialize the optional `statistics` sub-blocks at all is a design decision, not a reconciliation, and is left open. **Owner: H4 Statistics** (it owns `resample` and `null_test`, the last two that are refused; whatever it decides for those settles the shape for `contrasts` and `report_by` too)."
- Produces: a **closed** entry — a ruling with its grounds, so the residue is a decision rather than a silence.

**The ruling this plan makes, and the argument for it.** `init` should **not** materialize `statistics.resample`. Grounds, in the order they bind:

1. **`parameter_spec` is the single source of truth for what `init` writes**, and `resample` is not a parameter — it is a `statistics` block, and `materialize.py` writes exactly two `statistics`-adjacent keys today (`correction: holm` and a top-level `hypotheses: []`).
2. **The two documents already disagree in this direction and `reference.md` resolves it**: § The one config file says its fenced example is "the complete config *schema*, which is a wider thing than the literal output of `init`; a materialized file that does not carry them is not an incomplete config", and that for `contrasts` and `report_by` "declaring one by hand is how a run asks for it, and `validate` accepts the key whether or not `init` wrote it". `resample` inherits that sentence.
3. **Writing it would change behaviour, not just text.** A materialized `resample: {method: bootstrap, n: 2000}` is a **declared** resample under Task 13's `declared` flag, so every generated project would turn every recorded column into a percentile interval by default — reversing § Statistical reporting's stated asymmetry ("a column metric has a t-interval available, so resampling it is a *choice*, and `resample` is what makes it"). A materialized `resample: null` would be inert but would then need its own inline comment and would tempt the `.get("resample", DEFAULT)` reading Task 13 forbids.

So: **no `materialize.py` change, no `reference.md` change**, and the entry closes on the third argument, which is the one only this slice could make.

- [ ] **Step 1: Write the failing test** — the check is a grep and an existing test, run in Step 2:

```bash
cd /Users/joon/src/tries/publishable
grep -n 'resample\|null_test' src/publishable/materialize.py   # must print nothing
uv run pytest tests/test_materialize.py -q
```

- [ ] **Step 2: Run it, confirm it fails** — the grep prints nothing today, which is the state the ruling preserves; `tests/test_materialize.py` passes. **This task's deliverable is the written ruling, not a behaviour change** — so "confirm it fails" here means confirming that the `spec-defects.md` entry is still open and still says "left open. Owner: H4 Statistics": `grep -n 'Owner: H4 Statistics' docs/superpowers/spec-defects.md`.

- [ ] **Step 3: Implement** — in `docs/superpowers/spec-defects.md`, replace the **Open residual, routed** paragraph under *"The generated config calls itself 'the complete parameter set' before it is one"* with:

```markdown
**Residual — CLOSED by H4a (2026-08-15).** Whether `init` should materialize the optional
`statistics` sub-blocks: **no.** Three grounds, in the order they bind.

1. `parameter_spec` is the single source of truth for what `init` writes, and none of these is a
   parameter. `materialize.py` writes `statistics.correction` and a top-level `hypotheses: []`
   and nothing else under `statistics`.
2. `reference.md` § The one config file already resolves it for `contrasts` and `report_by` —
   its fenced example is "the complete config *schema*, which is a wider thing than the literal
   output of `init`; a materialized file that does not carry them is not an incomplete config" —
   and `resample` and `null_test` inherit that sentence rather than needing their own.
3. **The argument only this slice could make:** now that `resample` is honored, a materialized
   `resample: {method: bootstrap, n: 2000}` would be a *declared* resample, so every generated
   project would give every recorded column a percentile interval by default — reversing
   § Statistical reporting's asymmetry, which is that a column has a t-interval available so
   resampling it is a **choice** and `resample` is what makes it. A materialized `resample: null`
   would be inert but would need its own inline comment and would invite the
   `.get("resample", DEFAULT)` reading that separates the absent key from the explicit null.

No `materialize.py` change and no `reference.md` change. Recorded so the absence is a decision.
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest`, then re-run both greps from Step 1 and confirm `grep -n 'left open' docs/superpowers/spec-defects.md` no longer matches this entry. Then the mechanical pass on `spec-defects.md`: no trailing whitespace, no tab, table rows intact, every `#anchor` resolvable.

- [ ] **Step 5: Mutate** — add `"  resample: {method: bootstrap, n: 2000}",` to `materialize.py`'s `statistics:` block. Run `uv run pytest tests/test_cli.py -k undeclared_resample_shape`. **Both of Task 1's pins must FAIL** — every generated project now declares a resample, so `column["method"]` becomes `percentile_over_units` and `"resample_draws" not in column` breaks. That is the empirical demonstration of ground 3, and it is why this task's ruling is a behaviour argument rather than a stylistic one. Note the failure in the commit message. Delete `__pycache__`, remove the line in place, re-run.

- [ ] **Step 6: Commit** — `docs: close the init-materializes-optional-blocks residual — no, and here is the behaviour argument`.

---

## Sequencing

Execute in the order above. The order is not free — four constraints bind it, and three of them are not in the spec's own sequencing note.

1. **Task 1 first, absolutely.** It is the only baseline anything later can be compared against. Once Task 14 wires `percentile_over_units` into `summarize_step`'s column branch there is nothing left to compare against, and once Task 13 replaces the literal `2000` there is nothing left to detect a silently changed draw count.
2. **Tasks 4–8 (every `validate` refusal) before Task 12 (the retirement), and Task 12 before Task 13.** Validate-before-honour, inside the slice: the `n >= 80` floor and the no-roster refusal must exist before a declared `resample` can reach a run, or the first `resample: {n: 50}` gets a run whose every interval is `null` with no diagnostic, and a `resample` with no roster validates clean and does nothing.
3. **Task 12 before Tasks 13–18** — a constraint the spec's task list does not state. `cli` always validates before running, and an error exits before a run directory exists, so **every end-to-end test from Task 13 onward is impossible while `E-STATS-RESAMPLE-UNSUPPORTED` still fires.** Placing the retirement at 12 makes the silent-no-op window exactly two tasks wide (12→14, during which a declared resample changes only the derived draw count) — the narrowest available, since retiring earlier widens it to five and retiring later makes Tasks 13–14 untestable.
4. **Tasks 9–11 (the `stats.py` constructions) before Tasks 14–16 (the wiring).** They are pure and unit-testable with no run behind them, so they can land inside the pre-retirement window and shorten it.

Task 3 must precede Tasks 4–8 (they read values whose type the envelope now backstops). Task 2 must precede Task 4 (the enum it enforces is minted there). Task 15 must precede Task 16 only in that both touch `cli.command_run`'s locals; they are otherwise independent. Task 17 must follow Task 13 (it reads `resample_spec`) and Task 15 (it merges into the same `beside_n` locals). Task 18 must be **last but one**, because it pins properties every earlier task could have broken. Task 19 is documentation and may land any time after Task 13, whose `declared` flag its argument rests on.

**After the final task**, re-run the full suite plus every check: `uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run mypy`, then `grep -rln 'E-STATS-RESAMPLE-UNSUPPORTED' src/ docs/ tests/` (only the absence test may match), then `grep -rn p_value src/` (must be empty), then the worked example's numbers: `grep -n '0.488, 0.661\|0.517, 0.683\|0.347, 0.477\|−0.007, 0.059\|−0.213, −0.125\|0.014' docs/reference.md README.md docs/design-principles.md` must return exactly what it returned at `eaf3605`.

## Where this slice will be attacked

**The acceptance property: a config that declares nothing produces byte-identical output to a run at `eaf3605`, and a config that declares `statistics.resample` gets the method, the count and the strata it asked for — on every recorded column, every column contrast, every cluster, and every reporting stratum — with the corrected interval read off the same evidence as the raw one.**

The four places a reviewer will press, in the order they are likely to find something:

1. **The corrected interval of a column contrast under `resample`.** Task 16. `_corrected_bounds` tests `diffs` first; a `Member` that keeps them yields `ci95` from a percentile and `ci95_corrected` from `paired_t_over_units` on the same row, and nothing raises. The defence is the family-of-2 fixture (level 0.025, 160 draws needed, 2000 supplied) with both a containment assertion **and** an assertion the corrected bound is not the *t* bound — because at family size 1 the two coincide and the test could not fail. A reviewer should apply the mutation `corrected_from_pool = is_derived` and confirm the test dies.

2. **The key set a column contrast resamples over.** Task 16. `base_keys` for a ragged column feeds `compute` rows the column is missing from, and `UnitTable.__getattr__` pads with `None` rather than raising, so whether the bug is loud depends on the closure body. The defence is a fixture where a **quarter** of the roster misses the column — at one unit missing, ~720 of 2000 draws survive and the bug produces a plausible interval.

3. **The undeclared path.** Tasks 1 and 13. The absent `resample` key and an explicit `resample: null` are different documents that must resolve to one answer, and `run_a_project`'s `doc.update` makes it easy to pin a baseline the test itself changed by dropping `correction: holm`. The defence is two separate pins, each asserting `correction_level`, `family_size` and `family`.

4. **The stratified draw's arithmetic.** Tasks 9, 10 and 15. Three constructions produce three plausible numbers — the correct within-stratum draw, an unstratified draw, and an equal-weighting of stratum means — and a fixture with two equal strata separates none of them. The defence is the banded fixture (20/8/2 units in `[0,1)`, `[10,11)`, `[100,101)`; clusters 4/3, 3/2, 2/1) sized so that each wrong answer lands in a different place, plus the label-invariance and row-order-invariance pins that catch a draw depending on anything but the multiset.

**Two lower-probability but higher-cost attacks.** `W-STATS-AGGREGATE-FAILED` naming a template's `aggregate` for a recorded column that `aggregate` never touched — prevented by Task 11's invariant and asserted in Task 14. And a `summary`-step `Estimate` acquiring a field from the pass that walks every metric block — prevented structurally (`summary_values`, not `summarize_step`) and asserted in Task 18 with an exact-equality check rather than a set of absences.
