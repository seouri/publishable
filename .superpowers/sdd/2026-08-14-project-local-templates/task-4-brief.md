## Task 4: Hoist `find_repo_root` above the template check, silently

**Files:** Modify `src/publishable/validate.py`; Test `tests/test_validate.py`

**The ordering constraint § Errors pins:** `E-TEMPLATE-UNKNOWN` fires "exactly once, since that check returns immediately after", with none of the other rows. **A hoisted `find_repo_root` that reported a missing repo would put a new finding ahead of a documented one.** The existing `try: … except ContractError: repo_root = None` below is the pattern to reuse.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_local_template_validates_through_the_real_path(tmp_path):
    """End to end: a config naming a local template no longer draws
    E-TEMPLATE-UNKNOWN. THE CONTROL: a config naming a template that exists
    nowhere still draws it, so a check that stopped reporting entirely fails."""

def test_no_repo_means_local_discovery_is_skipped_and_generic_still_resolves(tmp_path):
    """A config outside any repo. `find_repo_root` raises; the hoist must
    swallow it. Assert the exact finding set — an added finding here would
    break the documented early-return order."""

def test_an_unknown_template_still_reports_exactly_one_finding(tmp_path):
    """§ Errors: the check "returns immediately after", so none of the other
    rows appear. Assert the exact set, not that the code is present."""
```

- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutate** — let `find_repo_root`'s `ContractError` propagate (the no-repo test fails); report a finding on a missing repo (the exact-set assertions fail).
- [ ] **Step 6: Commit.**

---

