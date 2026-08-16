## Task 4: The `assign` per-axis whole-leaf closure

**Files:** Modify `src/publishable/envelope.py`, `docs/reference.md`; Test `tests/test_validate.py`

**H3c-1 was assigned this and did not ship it**, and § The one config file records the gap in so many words: *"`envelope.py` still types the block a bare `dict` with no per-axis-key closure, so a misspelled field inside an axis block (`stratifyy_by` for `stratify_by`) is silently ignored"*. **This lands ahead of tasks 5–13, which add four new keys inside those blocks** — every one of them silently ignorable until this is closed.

- [ ] **Step 1: Write the failing test**

```python
def test_a_misspelled_key_inside_an_assign_block_is_reported(write_config):
    """`stratifyy_by` is silently ignored today: `envelope.py` types
    `data.units.assign` a bare `dict` and none of its children, so nothing
    closes an axis block. The control is the correctly spelled key, which must
    NOT be reported — an allowlist that rejects everything passes the first
    assertion and fails the design."""
    units = {
        "allocation": "between",
        "assign": {"arm": {"method": "by_attribute", "stratifyy_by": ["site"]}},
    }
    assert "E-CONFIG-KEY-UNKNOWN" in codes(write_config({"data.units": units}))
    ok = {
        "allocation": "between",
        "assign": {"arm": {"method": "by_attribute", "from": "arm"}},
    }
    assert "E-CONFIG-KEY-UNKNOWN" not in codes(write_config({"data.units": ok}))
```

- [ ] **Step 2: Run it and confirm it fails** on the first assertion, not the second.
- [ ] **Step 3: Implement.** The axis *keys* are user-chosen names no fixed dotted path can name — that is why the block was left open. Close it one level down: every axis block's **own** keys are the closed set `{method, from, ratio, block_size, stratify_by, seed}`. Read how `check_envelope` reports an unknown key elsewhere and use the same code.
- [ ] **Step 4: Mutate** — remove one name from the closed set and confirm a test names it. **Then check the reverse**: a config using every one of the six must report nothing.
- [ ] **Step 5: Amend § The one config file's gap sentence** — it currently records this as unclosed. The document changes with the code.
- [ ] **Step 6: Commit.**

---

