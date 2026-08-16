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

