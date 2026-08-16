## Task 11: Refuse a weighted contrast, and retire `E-DATA-WEIGHT-UNSUPPORTED`

### First, and it gates the retirement: contrasts are still unweighted

`reference.md` § Weighted samples: *"a [contrast](#contrasts-claims-that-arent-condition-vs-baseline) between two weighted conditions uses **the same weights on both sides**, which is automatic under `allocation: within` and worth checking when it isn't."*

**No weighted contrast construction exists.** `paired_t_over_units(diffs, confidence)` takes only differences; `paired_delta_of_derived` and `paired_percentile_of_derived` likewise. Task 10 wired the *single-condition* estimators — value, interval and `n.effective` — but a `vs_baseline` delta is still computed unweighted. Retiring the refusal without addressing that turns every weighted run's delta into a wrong number, which is the same forbidden move task 10 was widened to prevent one level up.

**Ruling: mint a narrow, temporary refusal rather than building the estimator family here.** Building it is a second slice's worth of work — three constructions plus their wiring — and H4 Statistics already owns the contrast and correction family. The precedent is exact: H2 retired `E-SWEEP-BASELINE-PARTIAL` and minted `E-SWEEP-SAMPLE-BASELINE` for the combination it had just made reachable but could not yet compute.

So `data.units.weight_by` becomes legal, **except** in combination with a contrast:

| Config | Outcome |
|---|---|
| `weight_by`, no contrast | works — weighted mean, weighted interval, `n.effective`, `weighted_by` |
| `weight_by` + `sweep.baseline` | refused |
| `weight_by` + `statistics.contrasts` | refused |

Follow `E-SWEEP-SAMPLE-BASELINE`'s shape when writing it: the message says what is wrong, what to do instead, and that the combination will be honoured once the contrast estimators weight. **Measure the blast radius before writing the guard** — refuse only the combinations that actually produce a wrong delta, and pin each edge. A refusal wider than the harm strands designs that are fine, which is the failure H2 checked for explicitly.

The identifier needs a registry row, and § The one config file's `NOT BUILT` list still has to go **ten → nine** for `weight_by` itself. Say in your report whether the new code belongs in that list too — it refuses a *combination*, not a declaration, and H2 ruled that such a code carries a registry row and does **not** join the `NOT BUILT` count.

### Then: the retirement

Mirrors task 6. Remove `("weight_by", "E-DATA-WEIGHT-UNSUPPORTED")` from the five-field loop; `materialize.py`'s comment loses `NOT BUILT`; `reference.md`'s prose count goes **ten → nine**. `weight_by` is already a typed `str` leaf in `envelope.py`, so there is no whole-leaf block to close here — **verify that rather than assuming it**.

- [ ] **Step 1: Write the failing test**

```python
def test_a_declared_weight_by_is_no_longer_refused(write_config):
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id",
        "attributes": ["sampling_weight"],
        "weight_by": "sampling_weight",
    }}})
    assert "E-DATA-WEIGHT-UNSUPPORTED" not in codes(path)
```

- [ ] **Step 2: Run it and confirm it fails.**

- [ ] **Step 3: Remove the tuple from the five-field loop; update `materialize.py`.**

- [ ] **Step 4: `reference.md` § The one config file — drop the `NOT BUILT` marker on `weight_by:` and take the prose count ten → nine.**

- [ ] **Step 5: Full suite, then grep every tracked `*.md` for `E-DATA-WEIGHT-UNSUPPORTED` — it must appear nowhere. Prove the grep can fail against a code that does exist.**

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: data.units.weight_by is a declaration core honors"
```

---

