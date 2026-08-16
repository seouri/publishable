## Task 9: `n` gains `effective`, and the record carries `weighted_by`

**Files:**
- Modify: `src/publishable/runner.py`, `src/publishable/stats.py`, `src/publishable/run_record.py`
- Test: `tests/test_runner.py`, `tests/test_cli.py`

`reference.md` § The three-part n: `effective` joins `n` **whenever `weight_by` makes Kish's size the one the interval was computed at**, and each part is *present only when it applies* so a design that never weights reads as it always did. That conditionality is the requirement, not a nicety.

- [ ] **Step 1: Write the failing tests**

```python
def test_n_gains_effective_under_a_weighted_design(...):
    assert metric["n"]["effective"] == pytest.approx(expected_kish)
    assert metric["weighted_by"] == "sampling_weight"


def test_n_has_no_effective_key_without_weight_by(...):
    """The regression: an unweighted run's `n` must not grow a key."""
    assert "effective" not in metric["n"]
    assert "weighted_by" not in metric
```

- [ ] **Step 2–4:** Fail, implement, pass.

**The three sites are verified**, all in `runner.py`: the no-roster early return, the no-recording-execution early return, and the accumulating return at the end. All three must agree, and the second test above is what catches having changed only two.

The route from there to a metric is `stats.summarize_step(collapsed, counts, derived=..., seed=..., resample=..., draws=...)` — `counts` **is** the dict those three sites build. So `effective` reaches a metric by riding that argument, and `weighted_by` needs its own way through; decide which and say so, rather than widening `counts` with a key that is not a count.

- [ ] **Step 5: Mutation-test.** Make `effective` unconditional. `test_n_has_no_effective_key_without_weight_by` must FAIL.

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: report the effective n a weighted interval was computed at"
```

---

