## Task 4: `_check_resample` — the `method` enum, and the `n >= 80` floor

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`. Test `tests/test_validate.py`.

**Interfaces:**
- Consumes: `envelope.LEAF_TYPES`'s three `statistics.resample.*` entries (Task 3); `stats.min_honest_draws`; `diagnostics.Collector` (`.error(code, path, message)` / `.warn(...)`).
- Produces: `validate._check_resample(doc, roster, c)` — the one function Tasks 5, 6, 7 and 8 extend. Its call site in `validate_config` is fixed here.

**Where it sits, and why (spec decision 5).** `validate_config`'s sequence today is `… _check_fold_stratify_by → _check_replication → _check_unimplemented → _check_sweep → _check_contrasts → _check_hypotheses → _check_report_by`. `_check_resample` goes **immediately after `_check_sweep`**, before `_check_contrasts`. It needs the resolved roster (Task 5's declared-attribute test and Task 8's cluster count) and, for Task 6, the resolved comparison family that `_check_sweep` also computes. This is the one ordering question H4a inherits from H7a's `validate_config` reshuffle.

**The floor is mandatory, and it must land before anything honours `n`.** `stats.t_over_units` returns `None` below 2 units. `stats.percentile_over_units` returns `None` below 2 units **and** below `min_honest_draws(confidence)` draws. So once Task 14 wires the column branch, a `resample: {n: 50}` nulls `ci95` on **every column in the run**, silently. `min_honest_draws(0.95)` is exactly **80**.

**Signature.** `def _check_resample(doc: dict[str, Any], roster: "UnitList | None", c: Collector) -> None`. `roster` is the same value `_check_units` returned and `_check_report_by` already takes.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
_RESAMPLE_UNITS = {"from": "index.csv", "key": "patient_id", "attributes": ["cohort"]}


def test_an_unknown_resample_method_is_refused(write_config):
    """`bootstrap` is the whole enum. An unstated one-value enum makes
    `method: bootstap` a shrug; a stated one makes it a diagnostic."""
    found = codes(
        write_config(
            {
                "data.units": _RESAMPLE_UNITS,
                "statistics": {"resample": {"method": "bootstap", "n": 2000}},
            }
        )
    )
    assert "E-STATS-RESAMPLE-METHOD" in found
    # The positive companion, in the same test: the legal spelling is NOT
    # refused, so this cannot pass by the check rejecting every method string.
    assert "E-STATS-RESAMPLE-METHOD" not in codes(
        write_config(
            {
                "data.units": _RESAMPLE_UNITS,
                "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
            }
        )
    )


@pytest.mark.parametrize("n", [0, -1, 79])
def test_a_resample_n_below_the_honest_floor_is_refused(write_config, n):
    """`percentile_over_units` returns `None` below `min_honest_draws(0.95)` = 80
    draws, so a declared `n: 50` would null `ci95` on EVERY column in the run
    with no diagnostic. The floor is what makes that impossible, and it lands
    before any code honours `n` — validate-before-honour, inside the slice.

    Three values, not one: `0` and `-1` are the not-a-positive-count fault and
    `79` is the floor itself, and a check written as `n < 1` passes the first two
    while letting the third through. `79`/`80` is the boundary pair, so an
    off-by-one (`n <= 80`) fails the companion below rather than passing."""
    found = codes(
        write_config(
            {
                "data.units": _RESAMPLE_UNITS,
                "statistics": {"resample": {"method": "bootstrap", "n": n}},
            }
        )
    )
    assert "E-STATS-RESAMPLE-N" in found


def test_a_resample_n_at_the_floor_is_accepted(write_config):
    """The positive companion `79` above needs: exactly 80 is honest, so an
    off-by-one in either direction fails one of the two."""
    found = codes(
        write_config(
            {
                "data.units": _RESAMPLE_UNITS,
                "statistics": {"resample": {"method": "bootstrap", "n": 80}},
            }
        )
    )
    assert "E-STATS-RESAMPLE-N" not in found


def test_the_resample_floor_message_names_the_number_and_the_consequence(write_config):
    messages = messages_by_code(
        write_config(
            {
                "data.units": _RESAMPLE_UNITS,
                "statistics": {"resample": {"method": "bootstrap", "n": 50}},
            }
        )
    )
    message = messages["E-STATS-RESAMPLE-N"]
    assert "80" in message
    assert "no interval" in message
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k resample_method or resample_n -x`. Expect `KeyError`/`assert ... in found` failures: neither code exists.

- [ ] **Step 3: Implement** — in `src/publishable/validate.py`.

  (a) Add to the imports from `publishable.stats`: `min_honest_draws`.

  (b) Add the call, immediately after `_check_sweep(doc, template, c, fold_basis=basis)`:

```python
    _check_sweep(doc, template, c, fold_basis=basis)
    # After `_check_sweep`, not before it, and this is the one ordering question
    # H4a inherits from H7a's prologue reshuffle: the strata check needs the
    # resolved roster and the declared attributes, and the `n` bound needs the
    # resolved comparison family, which `_check_sweep` is the first thing to
    # compute. Before `_check_contrasts`, which reports the shape faults in a
    # `statistics.contrasts` block this one only counts.
    _check_resample(doc, roster, c)
    _check_contrasts(doc, c, roster)
```

  (c) Add the function. Put it immediately before `_check_report_by`, which it most resembles:

```python
RESAMPLE_METHODS = ("bootstrap",)
"""Every value `statistics.resample.method` may take — `reference.md`
§ Statistical reporting's *Resample methods* table, which is the enum this
tuple enforces.

**A closed, one-value enum on purpose.** `bootstrap` is the only value the
schema shows and the only construction `stats.py` has, and § Statistical
reporting's construction tables enumerate the method strings core *emits*
(`percentile_over_units`, `paired_percentile_over_units`) — outputs, not inputs
a config may name. Stating the enum is what makes `method: bootstap` a
diagnostic rather than a shrug, and what makes adding a second value a
documented change rather than a silent one."""


def _check_resample(doc: dict[str, Any], roster: "UnitList | None", c: Collector) -> None:
    """`statistics.resample`, once it is honored rather than refused.

    Every check here presupposes the declaration is a mapping; a scalar or a
    list is `check_envelope`'s `E-CONFIG-TYPE` (`statistics.resample` is typed
    `dict`), and a wrong-typed child is the same, because Task 3 closed the
    block one level in. So this reads values rather than re-testing types, the
    same division `_check_report_by` keeps with the envelope.

    **The `n` floor is the load-bearing one.** `stats.percentile_over_units`
    returns `None` below `min_honest_draws(confidence)` draws — 80 at 95 % — so
    a declared `n: 50` would null `ci95` on every recorded column in the run,
    silently and with nothing in the record saying why. Refusing it here is why
    `validate` learns about `n` in the same slice that teaches `summarize_step`
    to honor it, rather than a slice later.
    """
    statistics = doc.get("statistics") or {}
    resample = statistics.get("resample")
    if not isinstance(resample, dict) or not resample:
        return
    method = resample.get("method")
    # `None`/absent means the documented default, `bootstrap` — § Statistical
    # reporting: declaring `resample` "changes the method or the count rather
    # than switching the behaviour on". Only a value actually named is checked.
    if method is not None and (not isinstance(method, str) or method not in RESAMPLE_METHODS):
        shown = f"`{method}`" if isinstance(method, str) else type(method).__name__
        c.error(
            "E-STATS-RESAMPLE-METHOD",
            "statistics.resample.method",
            f"is {shown}, not one of {', '.join(f'`{m}`' for m in RESAMPLE_METHODS)}",
        )
    n = resample.get("n")
    floor = min_honest_draws()
    # `bool` excluded explicitly: `isinstance(True, int)` is `True` in Python,
    # and `resample: {n: true}` is already `E-CONFIG-TYPE` from the envelope —
    # a value flagged wrong-typed there must not also drive this check.
    if n is not None and isinstance(n, int) and not isinstance(n, bool) and n < floor:
        c.error(
            "E-STATS-RESAMPLE-N",
            "statistics.resample.n",
            f"is {n}; a percentile interval needs at least {floor} draws before both "
            "of its ranks are interior, so below that the lower endpoint IS the "
            "smallest draw while the upper keeps shrinking — low-biased and "
            f"systematically too narrow. Under {floor} core reports no interval at "
            "all, so this would null `ci95` on every metric in the run rather than "
            "narrowing one",
        )
```

  (d) Register both codes in `docs/reference.md` § Errors `validate` reports, beside `E-STATS-REPORTBY-UNKNOWN`:

```markdown
| `statistics.resample.method` names a value other than `bootstrap` — the whole enum, [§ Statistical reporting](#statistical-reporting)'s *Resample methods*. Unset (`null`) is accepted and takes the documented default | `E-STATS-RESAMPLE-METHOD` |
| `statistics.resample.n` is below 80, the fewest draws both percentile ranks are interior at. Refused rather than warned because under it core reports no interval at all, so a declared `n: 50` would null `ci95` on every metric in the run rather than narrowing one | `E-STATS-RESAMPLE-N` |
```

  And add the § Validation row, beside *Clusters enough to resample*:

```markdown
| Resample draws are honest | `statistics.resample: {n: 50}` — below 80 draws a percentile interval's lower endpoint is the sample minimum, so core reports none and every metric in the run loses its `ci95` |
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k resample`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`. Then the doc mechanical pass: table rows match column counts, no trailing whitespace, `#statistical-reporting` resolves.

- [ ] **Step 5: Mutate** — in `validate.py`, change `if n is not None and isinstance(n, int) and not isinstance(n, bool) and n < floor:` to `... and n < 1:`. Run `uv run pytest tests/test_validate.py -k resample_n`. `test_a_resample_n_below_the_honest_floor_is_refused[79]` must FAIL while `[0]` and `[-1]` still pass — which is exactly why three values are parametrized and not one. Delete `__pycache__`, edit `n < 1` back to `n < floor` in place, re-run. Then a second mutation: change `floor = min_honest_draws()` to `floor = 81`; `test_a_resample_n_at_the_floor_is_accepted` must FAIL. Revert in place.

- [ ] **Step 6: Commit** — `feat: E-STATS-RESAMPLE-METHOD and the 80-draw floor, before anything honours n`.

---

