### Task 6: The refusals and `min_reported_n`

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `resolve_contrasts`; the resolved conditions from `sweep.expand`; `validate.py`'s `Collector` convention.
- Produces: retires `E-STATS-CONTRASTS-UNSUPPORTED`; adds `E-STATS-CONTRAST-UNKNOWN` (an `of`/`against` naming no condition) and `E-STATS-CONTRAST-NESTED` (naming another contrast's `id`); the `min_reported_n` warning is Task 7's, at the point `n_paired` is known.

**Contrasts compare conditions and do not nest.** `reference.md` and `design-principles.md` both say it: anything comparing two contrasts — a dose-response ordering, a difference-in-differences, a nested mean over cells — is an **interaction** and stays a `summary`-step `Estimate`. So a contrast naming another contrast's `id` is refused, and the message should point at that route rather than merely saying no.

**Before minting either identifier, grep `docs/reference.md`.** Several codes this project "added" already existed in its registry.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_declared_contrast_is_no_longer_refused(write_config):
    found = codes(write_config({
        "sweep": {"baseline": {"analysis.method": "pearson"},
                  "grid": {"analysis.method": ["spearman"]}},
        "statistics": {"contrasts": [
            {"id": "s", "of": "method=spearman", "against": "baseline"}]}}))
    assert "E-STATS-CONTRASTS-UNSUPPORTED" not in found


def test_an_unresolvable_side_is_refused(write_config):
    assert "E-STATS-CONTRAST-UNKNOWN" in codes(write_config({
        "sweep": {"baseline": {"analysis.method": "pearson"},
                  "grid": {"analysis.method": ["spearman"]}},
        "statistics": {"contrasts": [
            {"id": "s", "of": "method=nope", "against": "baseline"}]}}))


def test_a_contrast_naming_another_contrast_is_refused(write_config):
    """Contrasts do not nest — that is an interaction, and it belongs in a
    summary-step Estimate."""
    found = codes(write_config({
        "sweep": {"baseline": {"analysis.method": "pearson"},
                  "grid": {"analysis.method": ["spearman"]}},
        "statistics": {"contrasts": [
            {"id": "a", "of": "method=spearman", "against": "baseline"},
            {"id": "b", "of": "a", "against": "baseline"}]}}))
    assert "E-STATS-CONTRAST-NESTED" in found


def test_no_declared_contrasts_still_validates_clean(write_config):
    found = codes(write_config({"statistics": {"contrasts": []}}))
    assert not [c for c in found if c.startswith("E-STATS-CONTRAST")]
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_validate.py -k contrast -v`
Expected: the first FAILS because the block is still refused wholesale; the others FAIL because the codes do not exist.

- [ ] **Step 3: Implement**

Remove `E-STATS-CONTRASTS-UNSUPPORTED` from the refusal list, then check each declared entry: `of` and `against` must resolve to a condition label, **unless** the name matches another entry's `id`, which is the nested case and gets its own code. Grep the whole tree for `E-STATS-CONTRASTS-UNSUPPORTED` afterwards — `src/`, `tests/`, and the four documents — and confirm it is gone.

Order matters: check nesting **before** unknown, so `of: "a"` naming a contrast reports the nested code rather than the less specific unknown-label one.

- [ ] **Step 4: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Accept declared contrasts, and refuse the ones that nest"
```

---

