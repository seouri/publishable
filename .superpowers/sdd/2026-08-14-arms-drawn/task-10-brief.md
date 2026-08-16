## Task 10: `blocked`, `block_size`, and the whole-multiple rule

**Files:** Modify `src/publishable/units.py`, `src/publishable/validate.py`; Test `tests/test_units.py`, `tests/test_validate.py`

- [ ] **Step 1: Write the failing tests.** **The global constraints name this task's fixture trap** — an equal ratio with `auto` over a divisible roster gives `random` and `blocked` the same sizes:

```python
def test_a_blocked_draw_balances_within_every_whole_block():
    """14 units, ratio {1:1}, block_size auto = 4. 14 is NOT a multiple of 4:
    three whole blocks of 4 and a trailing 2, so a draw that balanced only
    overall would pass a size assertion and fail this one. Assert each whole
    block holds exactly 2 and 2, and assert the trailing partial block's actual
    composition rather than ignoring it."""

def test_blocked_reads_the_roster_order_as_data():
    """§ Where units come from: 'the one declaration that reads the order as
    data'. The same units in a different resolved order give a different
    assignment. THE CONTROL: `random` over the same two rosters gives the same
    assignment, because it does not read order."""

def test_auto_block_size_is_twice_the_ratio_sum():
    """{control: 1, treatment: 2} -> sum 3 -> auto 6. And with `ratio: {}` over
    two levels -> auto 4, per § Allocation."""

def test_an_explicit_block_size_must_be_a_whole_multiple_of_the_ratio_sum(write_config):
    """*Block size fills the arms*: block_size 3 with ratio summing to 2 'can't
    hold each arm's share'. The control is 4, which can."""
```

- [ ] **Step 2–4:** Fail, implement, pass. `validate` owns the whole-multiple refusal; `units` owns the draw.
- [ ] **Step 5: Mutations** — balance overall rather than per block; shuffle the roster before blocking; `auto` as the ratio sum rather than twice it.
- [ ] **Step 6:** Note in your report that **appending a unit re-blocks rather than redraws** — boundaries move relative to every earlier unit, so units that never moved rows change arms. Do not write a test asserting otherwise.
- [ ] **Step 7: Commit.**

---

