## Task 3: `sample` draws its conditions

**Files:**
- Modify: `src/publishable/sweep.py`, `src/publishable/validate.py`
- Test: `tests/test_sweep.py`, `tests/test_validate.py`

**Interfaces:**
- Consumes: `_axes` from task 1
- Produces: `sample` as one axis of realized draws

§ Expansion modes specifies `n`, `method` (`sobol | latin_hypercube | random`), `seed: auto`, and `ranges` with `uniform | int_uniform | log_uniform`. **Sampling is deterministic given its seed**, and `sweep.yaml` records both the seed and the fully realized condition list so a reader never re-derives the design and `reproduce` regenerates it.

- [ ] **Step 1: The seed derivation, already resolved — plus one consequence you must surface**

§ Expansion modes says the seed is "derived from the design digest; recorded in `sweep.yaml`". That digest is `hashes.design_digest(config)`, a **pure** function of the config dict — `hashes.py` imports only `hashlib`, `json`, `pathlib` and `typing`, and `design_digest` touches no file. So `sweep.py` may import it without breaking its own purity: `expand` remains a function of the declaration alone, which is the property its docstring promises. Do **not** add a `digest` parameter to `expand` — it has callers in `validate.py` (×7), `cli.py` (×3), `artifacts.py` (×2), `runner.py` and 23 tests, and the signature churn buys nothing.

Follow `replication.py`'s established derivation shape rather than inventing one:

```python
def _seed_for(digest: str, index: int) -> int:
    payload = f"{digest}|seed|{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")
```

Use a distinct payload tag — `|sample|` rather than `|seed|` — so a sample draw and a repeat seed derived from one digest never collide.

**The consequence to surface, not to fix.** `design_digest` hashes **only** `data.units` and `sweep.groups`, deliberately: its docstring says *"so a parameter edit redraws nothing."* It ignores `sweep.sample` entirely. So two consequences follow, and both are what the document specifies:

- Editing `ranges`, `n` or `method` does **not** change the seed. The draws still change, because they are functions of those values — but the seed does not.
- A project declaring neither `data.units` nor `sweep.groups` has a digest over `{"units": null, "groups": null}` — a **constant**. Every such experiment draws the same sample.

Implement what the document says. **Then state in your report whether the second consequence is intended**, with the evidence either way. It may be correct — a sample is reproducible and nothing says draws must differ across unrelated experiments — or it may be a spec gap worth a `docs/superpowers/spec-defects.md` entry. Do not decide it silently in either direction.

- [ ] **Step 2: Write the determinism test first**

The property that matters most is that two expansions of one config agree:

```python
def test_sample_draws_are_deterministic_given_the_config() -> None:
    """§ Expansion modes: "Sampling is deterministic given its seed", and the
    seed is derived from the design digest — so one config always expands to
    the same conditions, which is what makes `reproduce` regenerate them."""
    config = {
        "sweep": {
            "sample": {
                "n": 8,
                "method": "random",
                "seed": "auto",
                "ranges": {"analysis.confidence": {"uniform": [0.80, 0.99]}},
            }
        }
    }

    first = [dict(c.values) for c in expand(config)]
    second = [dict(c.values) for c in expand(config)]

    assert first == second
    assert len(first) == 8
    assert all(0.80 <= row["analysis.confidence"] <= 0.99 for row in first)
```

- [ ] **Step 3: Run it, implement, run it**

**Implement all three methods — this is not a scope decision, it is already resolved.** `scipy>=1.11` is a declared dependency in `pyproject.toml` and `scipy.stats.qmc` provides both samplers directly: `qmc.Sobol(d=..., seed=...)` and `qmc.LatinHypercube(d=..., seed=...)`, each returning draws in the unit hypercube that you scale into the declared ranges. `random` needs only `numpy`'s generator, which the project already uses for repeat seeding. Refusing a documented method would mint an identifier and a registry row for a feature the dependency hands you.

The three `ranges` forms — `uniform`, `int_uniform`, `log_uniform` — are the scaling step, and each needs its own test: `uniform` linear in the interval, `int_uniform` integral and inclusive of both endpoints, `log_uniform` uniform in the log of the interval. Write a test asserting `sobol`'s draws differ from `random`'s on the same seed, so the method parameter is not silently ignored — a sampler whose method argument does nothing is exactly the silent-skip class H1 spent a task pinning.

- [ ] **Step 4: Record the draws in `sweep.yaml`**

`sweep_document` already writes the resolved plan. Add the seed and confirm the realized conditions are already carried — read the function and § "`sweep.yaml` — the resolved plan" before adding anything, since the conditions may already be recorded and a second copy would be the drift this project keeps finding.

- [ ] **Step 5: Retire `E-SWEEP-SAMPLE-UNSUPPORTED`**, add the "sample ranges" check § Validation states (H1's scoping row 220 — read it for the exact condition), test both, commit.

```bash
git commit -m "feat: expand sample as deterministic draws over declared ranges"
```

---

