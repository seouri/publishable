### Task 6: `sweep.yaml`

**Files:**
- Modify: `src/publishable/sweep.py`
- Test: `tests/test_sweep.py`

**Interfaces:**
- Consumes: `Condition`; `Repeat` from `replication.py` (fields `kind`, `label`, `seed`).
- Produces: `sweep_document(conditions: list[Condition], repeats: list[Repeat], digest: str, order: list[tuple[int, str]]) -> dict[str, Any]`.

`docs/reference.md` § The other files a run writes: `sweep.yaml` holds "resolved conditions, repeat plan, seeds, fold membership, realized execution order, design digest". Fold membership is S3b and is absent here.

- [ ] **Step 1: Write the failing test**

```python
def test_the_sweep_document_records_the_resolved_plan():
    from publishable.replication import Repeat
    from publishable.sweep import expand, sweep_document

    conds = expand({"sweep": {"baseline": {"analysis.method": "pearson"},
                              "grid": {"analysis.method": ["spearman"]}}})
    repeats = [Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)]
    order = [(0, "seed17"), (0, "seed42"), (1, "seed17"), (1, "seed42")]
    doc = sweep_document(conds, repeats, "sha256:abc", order)

    assert doc["design_digest"] == "sha256:abc"
    assert doc["conditions"] == [
        {"index": 0, "label": "baseline", "values": {"analysis.method": "pearson"},
         "is_baseline": True},
        {"index": 1, "label": "method=spearman", "values": {"analysis.method": "spearman"},
         "is_baseline": False},
    ]
    assert doc["repeats"] == [{"kind": "seed", "label": "seed17", "seed": 17},
                              {"kind": "seed", "label": "seed42", "seed": 42}]
    assert doc["order"] == [[0, "seed17"], [0, "seed42"], [1, "seed17"], [1, "seed42"]]


def test_the_document_is_plain_yaml_safe_data():
    """It is written with the artifact writer, so it must hold no custom types."""
    import yaml
    from publishable.replication import Repeat
    from publishable.sweep import expand, sweep_document

    doc = sweep_document(expand({"sweep": {"grid": {"a.x": [1]}}}),
                         [Repeat("seed", "seed01", 1)], "sha256:d", [(0, "seed01")])
    assert yaml.safe_load(yaml.safe_dump(doc)) == doc
```

- [ ] **Step 2: Run and watch it fail**

Run: `uv run pytest tests/test_sweep.py -k sweep_document -v`
Expected: FAIL — `ImportError: cannot import name 'sweep_document'`

- [ ] **Step 3: Implement**

```python
def sweep_document(
    conditions: list[Condition],
    repeats: list["Repeat"],
    digest: str,
    order: list[tuple[int, str]],
) -> dict[str, Any]:
    """The `sweep.yaml` payload: the resolved plan, as plain YAML-safe data.

    Fold membership belongs here too per § The other files a run writes; folds
    are a later slice and the key is absent rather than empty, so its absence
    is not read as "no folds were drawn".
    """
    return {
        "design_digest": digest,
        "conditions": [
            {"index": c.index, "label": c.label, "values": dict(c.values),
             "is_baseline": c.is_baseline}
            for c in conditions
        ],
        "repeats": [{"kind": r.kind, "label": r.label, "seed": r.seed} for r in repeats],
        "order": [[index, label] for index, label in order],
    }
```

Import `Repeat` under `TYPE_CHECKING` so `sweep.py` stays free of a runtime dependency on `replication`.

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_sweep.py -v && uv run ruff check . && uv run mypy`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/sweep.py tests/test_sweep.py
git commit -m "Write down the plan a run actually resolved"
```

---

