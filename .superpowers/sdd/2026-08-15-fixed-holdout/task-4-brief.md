## Task 4: `design_digest` excludes `holdout.seed`

**Files:** Modify `src/publishable/hashes.py`, `docs/superpowers/spec-defects.md`. Modify (append) `tests/test_hashes.py`.

**Interfaces:**
- Consumes: `hashes._units_excluding_assign_seed(units: Any) -> Any` and `hashes.design_digest(config: dict[str, Any]) -> str`.
- Produces: `hashes._units_excluding_drawn_seeds(units: Any) -> Any` — the same function, renamed, now dropping `holdout.seed` as well as every `assign.<axis>.seed`. `design_digest` calls it in place of the old name.

**Why this lands before any pin is reachable.** `spec-defects.md` carries this as the explicitly **open** half of a closed entry, whose owner it names as "the slice that builds `data.units.holdout`". The defect is that `design_digest` canonicalizes `data.units` wholesale, so a **pinned** `holdout.seed` would move the digest that every *other* derived draw in the run reads — the `seed` repeat stream, the sample draw, each `assign.<axis>.seed`. Pinning one seed to cite it would silently redraw everything else, which is the confounding the digest's own section exists to prevent. It must land before task 5 makes a pinned seed reachable at all.

**The rename is the point, not decoration.** A function named `_units_excluding_assign_seed` that also drops a holdout's seed is a false name of exactly the class `CLAUDE.md` records a dozen instances of. `grep -rn _units_excluding_assign_seed src/ tests/ docs/` before and after; every site moves.

- [ ] **Step 1: Write the failing test** — append to `tests/test_hashes.py`:

```python
def test_a_pinned_holdout_seed_does_not_move_the_design_digest():
    """A seed that is itself inside the digest it is mixed with makes the
    derivation self-referential — and worse, moves every OTHER derived draw in
    the run. `assign.<axis>.seed` is already excluded for that reason; this is
    the same exclusion one field over.

    The positive companion is in the same test: changing a NON-seed holdout
    field MUST move the digest, or an implementation that dropped the whole
    `holdout` block would pass the first assertion alone."""
    base = {"data": {"units": {"from": "index.csv", "key": "patient_id",
                               "holdout": {"method": "random", "frac": 0.2}}}}
    pinned = {"data": {"units": {"from": "index.csv", "key": "patient_id",
                                 "holdout": {"method": "random", "frac": 0.2,
                                             "seed": 1234}}}}
    other_pin = {"data": {"units": {"from": "index.csv", "key": "patient_id",
                                    "holdout": {"method": "random", "frac": 0.2,
                                                "seed": 9999}}}}
    assert design_digest(base) == design_digest(pinned)
    assert design_digest(pinned) == design_digest(other_pin)

    widened = {"data": {"units": {"from": "index.csv", "key": "patient_id",
                                  "holdout": {"method": "random", "frac": 0.3}}}}
    assert design_digest(base) != design_digest(widened)


def test_the_seed_exclusion_covers_assign_and_holdout_together():
    """One config carrying both pins. Asserted together because the two
    exclusions are one function: an implementation that returned early after
    rewriting `assign` would leave `holdout.seed` in, and a config with only
    one pin cannot tell that apart from a correct one."""
    def cfg(assign_seed, holdout_seed):
        return {"data": {"units": {
            "from": "index.csv", "key": "patient_id",
            "assign": {"arm": {"method": "random", "seed": assign_seed}},
            "holdout": {"method": "random", "frac": 0.2, "seed": holdout_seed},
        }}}

    assert design_digest(cfg(7, 11)) == design_digest(cfg(8, 12))
    # A non-seed edit inside the SAME two blocks still moves it, so the
    # exclusion is per-field rather than per-block.
    moved = {"data": {"units": {
        "from": "index.csv", "key": "patient_id",
        "assign": {"arm": {"method": "blocked", "seed": 7}},
        "holdout": {"method": "random", "frac": 0.2, "seed": 11},
    }}}
    assert design_digest(cfg(7, 11)) != design_digest(moved)


def test_the_seed_exclusion_never_raises_on_a_shape_it_did_not_expect():
    """`validate` reaches `design_digest` before a config is known-good, so a
    non-mapping `holdout` must be left exactly as given rather than unpacked.
    Each of these must return a digest instead of raising."""
    for holdout in ("nonsense", ["a", "list"], 3, None):
        assert design_digest(
            {"data": {"units": {"holdout": holdout}}}
        ).startswith("sha256:")
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_hashes.py -k "holdout_seed or exclusion" -x`. The first two fail on the equality assertions; the third passes already (the current function returns `units` untouched when `assign` is not a mapping — which is a **coincidence of the current shape**, not a guarantee, and is why it is pinned before the rewrite rather than after).

- [ ] **Step 3: Implement** — in `src/publishable/hashes.py`, rename and widen:

```python
def _units_excluding_drawn_seeds(units: Any) -> Any:
    """`data.units` with every drawn partition's own `seed` dropped —
    `assign.<axis>.seed` from each axis block, and `holdout.seed`.

    `assign` is a mapping of axis name -> block, so its exclusion is per-axis:
    an axis's own `seed` is dropped from its own block only, never the whole
    `assign` subtree and never a sibling axis's `seed`. `holdout` is a single
    block, so its exclusion is one key. See docs/reference.md § What `auto`
    derives from: each of these seeds mixes the digest with the roster, and a
    seed that is itself inside the digest it is mixed with would make the
    derivation self-referential.

    **The wider harm is the reason this is not merely tidy.** `design_digest`
    canonicalizes `data.units` wholesale, and every other derived draw in the
    run reads the digest — the `seed` repeat stream, `sweep.sample`, each
    axis's assignment. Leaving a pinned seed in would mean that pinning one
    partition to cite it silently redrew all the others, which is the exact
    confounding § What `auto` derives from exists to prevent.

    Every other field of both blocks still moves the digest, which is the
    point: widening `frac`, restratifying, or changing an axis's `method` is a
    different design and must not be reproducible under the same digest.

    `design_digest` runs at run time on a validated config, but `validate`
    reaches it too (indirectly, via `expand` -> the `sample` seed derivation),
    so a malformed config can arrive here first. This function never raises: a
    non-mapping `units`, a non-mapping `assign`, a non-mapping axis block, or a
    non-mapping `holdout` is left exactly as given rather than unpacked, so the
    caller's canonical JSON encoding still runs over *something* instead of
    crashing on a shape it did not expect.
    """
    if not isinstance(units, dict):
        return units
    out = units
    assign = out.get("assign")
    if isinstance(assign, dict):
        new_assign = {}
        changed = False
        for axis, block in assign.items():
            if isinstance(block, dict) and "seed" in block:
                new_assign[axis] = {k: v for k, v in block.items() if k != "seed"}
                changed = True
            else:
                new_assign[axis] = block
        if changed:
            out = {**out, "assign": new_assign}
    holdout = out.get("holdout")
    if isinstance(holdout, dict) and "seed" in holdout:
        out = {**out, "holdout": {k: v for k, v in holdout.items() if k != "seed"}}
    return out
```

  and in `design_digest`, replace the call and widen its docstring's first line:

```python
def design_digest(config: dict[str, Any]) -> str:
    """`data.units` (every field except a drawn partition's own `seed`) and `sweep.groups`.

    A parameter edit redraws nothing, and neither does pinning or changing an
    axis's `assign.seed` or `data.units.holdout.seed` — see
    `_units_excluding_drawn_seeds`.
    """
    units = _units_excluding_drawn_seeds((config.get("data") or {}).get("units"))
```

  Then sweep for the old name — **by claim, not by the file this task happens to name**: `grep -rn _units_excluding_assign_seed src/ tests/ docs/`. Every hit moves, including the `spec-defects.md` entry, whose *closed* half names the old function.

  Then in `docs/superpowers/spec-defects.md`, strike the open half. Replace the paragraph beginning "**One field over, the same defect is latent.**" with:

```markdown
**~~One field over, the same defect is latent.~~ Closed by H3d, task 4.**
`hashes._units_excluding_assign_seed` was renamed `_units_excluding_drawn_seeds` and now
drops `data.units.holdout.seed` as well as each `assign.<axis>.seed`, so a pinned holdout
seed no longer perturbs any other derived draw. `reference.md` § What `auto` derives from
gained the matching row and named `E-DATA-HOLDOUT-SEED` in the same slice.
```

  and change the entry's trailing "The `holdout.seed` half above remains open" sentence to say it is closed by H3d task 4.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_hashes.py -k "holdout_seed or exclusion"`, then `uv run pytest`, then `uv run ruff check . && uv run ruff format . && uv run mypy`. Then re-run `grep -rn _units_excluding_assign_seed src/ tests/ docs/` — it must return **nothing**. Prove the sweep can fail by running it against `_units_excluding_drawn_seeds`, which must return hits.

- [ ] **Step 5: Mutate** — in `src/publishable/hashes.py`, change the holdout branch's condition from `if isinstance(holdout, dict) and "seed" in holdout:` to `if False and isinstance(holdout, dict) and "seed" in holdout:`. Run `uv run pytest tests/test_hashes.py -k "holdout_seed or exclusion"`. Both `test_a_pinned_holdout_seed_does_not_move_the_design_digest` and `test_the_seed_exclusion_covers_assign_and_holdout_together` must **FAIL**. Delete `__pycache__`, edit the condition back in place, re-run; both pass. Then a second mutation proving the *positive* companion is not vacuous: change the exclusion to drop the whole block — `out = {**out, "holdout": None}` in place of the dict comprehension. `test_a_pinned_holdout_seed_does_not_move_the_design_digest` must **FAIL** on `design_digest(base) != design_digest(widened)`. Revert in place.

- [ ] **Step 6: Commit** — `fix: exclude data.units.holdout.seed from the design digest`.

---

