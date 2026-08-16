## Task 6: Carry `technical_n`, and retire `E-DATA-MEASUREMENTS-UNSUPPORTED`

### Precondition: `measurements.by` is never checked against the declared attributes

**Close this before retiring the refusal.** Measured at task 3's HEAD, over a table with two rows per patient:

```
measurements: {by: nonexistent, collapse: {depth: mean}}
  -> units: [('p1', 15.0), ('p2', 35.0)]
  -> technical_n: {'min': 2, 'max': 2, 'median': 2.0}
```

A typo'd `by` silently averages rows that **nothing declared to be measurements of one unit**, and reports a `technical_n` claiming the collapse was intentional. Today `E-DATA-MEASUREMENTS-UNSUPPORTED` masks it — the config never gets that far. Retiring the refusal makes a wrong-answer path reachable, which is worse than the missing-diagnostic gaps elsewhere in this task.

`validate` already refuses an unknown attribute elsewhere (`E-UNITS-ATTR-MISSING`), and `data.units.attributes` is the declared set. Refuse a `by` that names nothing in it, and pin it. Task 3's implementer disclosed this in `spec-defects.md`; it is not a task 3 defect, but it **is** this task's gate.

### Sequencing constraint

**Task 6 must not land its `technical_n` route before task 9 has made its `counts` shape decision** — or the two tasks invent two routes for the same problem. Task 9 is explicitly scoped to decide how a sibling-of-`n` travels through `runner`'s attrition counts and `stats.summarize_step`; `technical_n` is the same question asked first. Either make the shape decision here and have task 9 follow it, or agree the route with task 9's brief before implementing. Say which you did.


### First: `technical_n` must actually be reported

Task 3 computes `technical_n` and returns it beside the roster, and **nothing carries it anywhere**. `reference.md` § What isn't a repeat says it "is reported for transparency — as `{min, max, median}` rather than a single number, because real files are uneven and a bare `technical_n: 3` would be a claim of balance nobody checked."

**Retiring the refusal is exactly the wrong moment to leave that undone.** Retiring it declares the declaration honoured; a feature that collapses replicates and never reports how many it collapsed is a declaration accepted whose effect is half-delivered — the risk this slice's spec names first.

Task 3's implementer investigated the route and did **not** guess, which was right. Its findings, to start from rather than redo:
- The shape `reference.md` shows puts it beside a *metric's* `n`, whose route is `runner`'s attrition counts → `stats.summarize_step`. That plumbing is task 9's, and task 9 is in the other half of the slice.
- `provenance.units` is documented as exactly `{n, key}`, so parking it there would invent an undocumented `run.yaml` field.

**Decide and justify.** It lands here rather than in task 9 so that the `measurements` half stays self-contained and the slice keeps its documented split seam at the 6/7 boundary. If you conclude the only correct home genuinely requires task 9's plumbing, say so and report `DONE_WITH_CONCERNS` rather than inventing a field — but say which document sentence forces that, not which is more convenient.

Whatever you choose, **pin it with a test that reads it back from a real run's artifacts**, not from a return value.

### Then: the retirement

**Files:**
- Modify: `src/publishable/validate.py`, `src/publishable/envelope.py`, `src/publishable/materialize.py`, `docs/reference.md`
- Test: `tests/test_validate.py`

- [ ] **Step 1: Write the failing test**

```python
def test_a_declared_measurements_block_is_no_longer_refused(write_config):
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id",
        "attributes": ["depth", "read_id"],
        "measurements": {"by": "read_id", "collapse": {"depth": "mean"}},
    }}})
    assert "E-DATA-MEASUREMENTS-UNSUPPORTED" not in codes(path)
```

- [ ] **Step 2: Run and confirm it fails**

- [ ] **Step 2b: Three stale `reference.md` bits, routed here by task 3 because this task rewrites these sections.** **Amended after task 5: `finalize` is now a *second* raise surface** — a step recording a non-numeric value under a numeric rule raises `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` at collapse time, so the execution fails on a *value the step recorded* rather than on anything the step did, and the user sees a code with no lookup. The row you write must cover **both** `resolve_units` and `finalize`, or it ships incomplete. `resolve_units` raises `E-DATA-MEASUREMENTS-INVALID` and `E-DATA-MEASUREMENTS-COLLAPSE-TYPE`, but (i) both rows sit only in § Errors `validate` reports, (ii) neither carries the dual-listing clause `E-UNITS-COLLAPSE-RULE` has, and neither has a counterpart in § Errors core raises, and (iii) `E-DATA-MEASUREMENTS-COLLAPSE-TYPE`'s row says `is_measurement_numeric` is "the single authority this check and **a future run-time coercion** both read" — that coercion is no longer future, and a row edit that only adds the dual-listing clause would leave this one false. Fix all three.

- [ ] **Step 3: Remove `("measurements", "E-DATA-MEASUREMENTS-UNSUPPORTED")` from the five-field loop.** Close the whole-leaf `envelope.py` block: replace the bare `dict` for `data.units.measurements` with typed leaves for `.by` (`str`) and `.collapse` (`str` or `dict`), so an unknown key inside it is reached by a check. Update `materialize.py`'s inline comment to drop `NOT BUILT`.

- [ ] **Step 4: Documents.** In `reference.md` § The one config file: the `NOT BUILT` marker on `measurements:` goes, and the prose count **eleven → ten**.

**Do not edit the "latent rather than live" passage** — it is about **`holdout`**, not `measurements`, and `holdout` stays refused until H3d. I checked this rather than inferring it, because editing a passage about a neighbouring block while believing it is about yours is precisely the document-defect class this project keeps shipping.

The relevant enumeration is `reference.md`'s closed-schema paragraph, which names **four** whole-leaf blocks the claim excepts: a `hypotheses` entry, a `statistics.contrasts` entry, a `replication.repeats` entry of kind `seed` or `fold`, and the mapping form of `data.units.from`. **`measurements` is not among them** — it is typed as a bare `dict` in `envelope.py` but excluded from that list because the whole block is refused.

So there are exactly two honest outcomes, and step 3 decides which:
- **If you fully type `.by` and `.collapse` as leaves** (the plan's intent), `measurements` never becomes a whole-leaf block and **neither passage needs an edit**. Verify by pinning that a typo *inside* the block — `{by: read_id, colapse: mean}` — now reports `E-CONFIG-KEY-UNKNOWN`.
- **If you cannot fully type it**, then `measurements` becomes a fifth live whole-leaf block and you **must add it to that enumeration**, with the slice that closes it named, exactly as the other four are.

Say which outcome you landed in and show the evidence. Silently leaving it typed `dict` while retiring the refusal is the one thing that must not happen: that turns a latent gap live without recording it anywhere.

- [ ] **Step 5: Run the full suite.** Then grep every tracked `*.md` for `E-DATA-MEASUREMENTS-UNSUPPORTED`; it must appear nowhere. **Prove the grep can fail** by running it against a code that does exist.

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: data.units.measurements is a declaration core honors"
```

---

