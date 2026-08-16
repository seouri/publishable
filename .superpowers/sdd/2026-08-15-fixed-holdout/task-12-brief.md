## Task 12: `units.holdout_seed_for` — the derivation and its own digest suffix

**Files:** Modify `src/publishable/units.py`. Modify (append) `tests/test_units.py`.

**Interfaces:**
- Consumes: `units.units_hash(units: UnitList) -> str`; `units.assign_seed_for(block, axis, digest, roster) -> int` as the model.
- Produces:

```python
def holdout_seed_for(block: Mapping[str, Any], digest: str, roster: UnitList) -> int:
```

**Why it is not `_seed_from`.** `units._seed_from(digest)` hardcodes `sha256(f"{digest}|folds")`. A holdout is not a fold and must not draw the same partition a `fold` level would from the same digest — they are mutually exclusive declarations today (`E-DATA-HOLDOUT-FOLD`), so nothing *observes* the collision, and that is precisely the argument against relying on it: the suffix is what makes the two independent whatever a later slice permits.

**Why it is not `assign_seed_for`.** That one is per-axis and reads `block["seed"]` under an axis name a holdout does not have. The construction is otherwise identical and is copied deliberately: `f"{digest}|holdout|{units_hash(roster)}"`, sha256, first four bytes big-endian.

**The load-bearing half: a pinned integer is returned literally, and the digest is not consulted at all on that path.** `sweep.sample_seed_for`'s own words. "Pinning an integer is the deliberate act, and the one to take for anything you intend to cite" — so a pinned holdout must survive a roster that grows, shrinks, or reorders. Task 4 already stripped `holdout.seed` from `design_digest` for the matching reason.

**`bool` is excluded.** `isinstance(True, int)` is `True`, and `seed: true` is not a pin — `validate` refuses it as `E-DATA-HOLDOUT-SEED`, and this function must not honour it as `1`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_units.py`:

```python
def test_a_pinned_holdout_seed_is_returned_literally_and_ignores_the_digest():
    """`sweep.sample_seed_for`'s load-bearing half, copied: on the pinned path
    the digest is not consulted at all, so a pinned split survives a roster
    that grows, shrinks or reorders.

    Three varying inputs against one pin, because a function that read ANY of
    them would move for at least one of these."""
    block = {"method": "random", "frac": 0.2, "seed": 4321}
    assert holdout_seed_for(block, "sha256:aaa", _roster(10)) == 4321
    assert holdout_seed_for(block, "sha256:bbb", _roster(10)) == 4321
    assert holdout_seed_for(block, "sha256:aaa", _roster(11)) == 4321


def test_a_boolean_seed_is_not_a_pin():
    """`isinstance(True, int)` is `True`, and `seed: true` is not a pin —
    `validate` refuses it as `E-DATA-HOLDOUT-SEED`, and honouring it as `1`
    here would record a derived seed under a key the config wrote
    deliberately."""
    derived = holdout_seed_for({"seed": True}, "sha256:aaa", _roster(10))
    assert derived != 1
    assert derived == holdout_seed_for({}, "sha256:aaa", _roster(10))


def test_the_derived_holdout_seed_mixes_the_digest_and_the_resolved_roster():
    """§ What `auto` derives from's new row. Each assertion changes exactly one
    input, so a derivation that ignored either would fail one of them."""
    base = holdout_seed_for({}, "sha256:aaa", _roster(10))
    assert base == holdout_seed_for({"seed": "auto"}, "sha256:aaa", _roster(10))
    assert base != holdout_seed_for({}, "sha256:bbb", _roster(10))
    assert base != holdout_seed_for({}, "sha256:aaa", _roster(11))
    # `units_hash` covers the roster IN RESOLVED ORDER, so a reordered roster
    # is a different trial and must draw a different split.
    reordered = UnitList(list(_roster(10))[::-1])
    assert base != holdout_seed_for({}, "sha256:aaa", reordered)
    assert 0 <= base < 2**32


def test_the_holdout_seed_is_not_the_fold_seed_for_the_same_digest():
    """`_seed_from` hardcodes `|folds`. The two declarations are mutually
    exclusive today (`E-DATA-HOLDOUT-FOLD`), so nothing observes a collision —
    which is the argument for the suffix rather than against it: the two stay
    independent whatever a later slice permits."""
    assert holdout_seed_for({}, "sha256:aaa", _roster(10)) != _seed_from("sha256:aaa")


def test_the_holdout_seed_is_not_an_assign_axis_seed_for_the_same_digest():
    """The other neighbour, and the one whose construction this copies: same
    digest, same roster, different suffix."""
    roster = _roster(10)
    assert holdout_seed_for({}, "sha256:aaa", roster) != assign_seed_for(
        {}, "holdout", "sha256:aaa", roster
    )
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_units.py -k holdout_seed -x`. All fail on `ImportError`; add `holdout_seed_for`, `_seed_from` and `assign_seed_for` to the test module's import list and re-run.

- [ ] **Step 3: Implement** — in `src/publishable/units.py`, add immediately after `assign_seed_for`:

```python
def holdout_seed_for(block: Mapping[str, Any], digest: str, roster: UnitList) -> int:
    """The seed `data.units.holdout` draws its split with.

    `reference.md` § What `auto` derives from: a holdout's `seed` mixes "digest
    + the resolved roster" — the digest because the split is a property of the
    design, and `units_hash(roster)` because it covers the roster **in resolved
    order**, so two runs that resolved the same units in a different sequence
    did not draw the same trial (§ Where units come from).

    **Its own suffix, `|holdout`, and not `_seed_from`'s `|folds`.** A holdout
    is not a fold, and the two must not draw the same partition from the same
    digest. They are mutually exclusive declarations at this commit
    (`E-DATA-HOLDOUT-FOLD`), so nothing *observes* a collision — which is the
    argument FOR the suffix rather than against it: relying on a refusal
    elsewhere to keep two derivations apart is how they come to agree by
    accident the moment that refusal moves.

    **Not `assign_seed_for` either**, whose payload carries an axis name a
    holdout does not have. The construction is otherwise copied deliberately:
    the same digest, the same `units_hash`, the same four bytes read big-endian
    — one derivation shape for every drawn partition in the config.

    A pinned integer is returned literally, and — the load-bearing half, copied
    from `sweep.sample_seed_for`'s own docstring — **the digest is not consulted
    at all** on that path, only read out of `block`. "Pinning an integer is the
    deliberate act, and the one to take for anything you intend to cite," so a
    pinned split must survive a roster that grows, shrinks, or reorders, and
    `hashes.design_digest` strips `holdout.seed` for the same reason: a pinned
    seed must not move the digest it would otherwise be mixed with.

    `bool` is excluded from the pin: `isinstance(True, int)` is `True`, and
    `seed: true` is not a pin — `validate` refuses it as
    `E-DATA-HOLDOUT-SEED`, and honouring it as `1` would record a derived seed
    under a key the config wrote deliberately.
    """
    seed = block.get("seed", "auto")
    if isinstance(seed, int) and not isinstance(seed, bool):
        return seed
    payload = f"{digest}|holdout|{units_hash(roster)}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_units.py -k holdout_seed`, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — two.

  (a) Change the payload's `|holdout|` to `|assign|holdout|`. `test_the_holdout_seed_is_not_an_assign_axis_seed_for_the_same_digest` must **FAIL** — that is precisely `assign_seed_for({}, "holdout", ...)`'s payload. Revert in place; re-run.

  (b) Change `if isinstance(seed, int) and not isinstance(seed, bool):` to `if isinstance(seed, int):`. `test_a_boolean_seed_is_not_a_pin` must **FAIL** on both of its assertions. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: units.holdout_seed_for, with its own digest suffix`.

---

