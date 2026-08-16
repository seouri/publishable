### Task 3: Retire one refusal, add four

**Files:**
- Modify: `src/publishable/validate.py` — the `E-SWEEP-UNSUPPORTED` block in `_check_unimplemented`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `Collector`.
- Produces: `E-SWEEP-PAIRED-UNSUPPORTED`, `E-SWEEP-ABLATE-UNSUPPORTED`, `E-SWEEP-SAMPLE-UNSUPPORTED`, `E-SWEEP-GROUPS-UNSUPPORTED`. `E-SWEEP-UNSUPPORTED` exists nowhere afterwards.

**This task gets its own reviewer gate** because retiring a blanket refusal is exactly where the door reopens one level down. It happened in S1 with `sweep` and was prevented in S2 by splitting `data.units` into seven refusals.

- [ ] **Step 1: Write the failing tests**

`tests/test_validate.py` already has a `write_config` fixture and a `codes(path)` helper — reuse them.

```python
def test_baseline_and_grid_are_now_accepted():
    found = codes(write_config({"sweep": {"baseline": {"analysis.method": "pearson"},
                                          "grid": {"analysis.method": ["spearman"]}}}))
    assert not [c for c in found if c.startswith("E-SWEEP")]


@pytest.mark.parametrize(
    "mode,value,code",
    [
        ("paired", [{"analysis.method": "pearson"}], "E-SWEEP-PAIRED-UNSUPPORTED"),
        ("ablate", {"from": "baseline", "remove": ["a.b"]}, "E-SWEEP-ABLATE-UNSUPPORTED"),
        ("sample", {"n": 40, "ranges": {}}, "E-SWEEP-SAMPLE-UNSUPPORTED"),
        ("groups", [{"by": "arm", "levels": ["a", "b"]}], "E-SWEEP-GROUPS-UNSUPPORTED"),
    ],
)
def test_each_unimplemented_mode_is_refused_on_its_own(write_config, mode, value, code):
    assert code in codes(write_config({"sweep": {mode: value}}))


def test_an_empty_or_null_mode_is_not_a_declaration(write_config):
    """`init` may write these absent or null; only a truthy value is refused."""
    found = codes(write_config({"sweep": {"grid": {"analysis.method": ["spearman"]},
                                          "paired": [], "ablate": None,
                                          "sample": None, "groups": []}}))
    assert not [c for c in found if c.endswith("-UNSUPPORTED")]


def test_every_sweep_refusal_message_defers_rather_than_scolds(write_config):
    for mode, value, code in [
        ("paired", [{"a.b": 1}], "E-SWEEP-PAIRED-UNSUPPORTED"),
        ("ablate", {"from": "baseline"}, "E-SWEEP-ABLATE-UNSUPPORTED"),
        ("sample", {"n": 1}, "E-SWEEP-SAMPLE-UNSUPPORTED"),
        ("groups", [{"by": "arm"}], "E-SWEEP-GROUPS-UNSUPPORTED"),
    ]:
        c = Collector()
        validate_config(write_config({"sweep": {mode: value}}), c)
        message = next(f.message for f in c.findings if f.code == code)
        assert "later slice" in message, f"{code} must defer, not scold"
```

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_validate.py -k sweep -v`
Expected: FAIL — the blanket `E-SWEEP-UNSUPPORTED` still fires and none of the four exist.

- [ ] **Step 3: Replace the blanket block**

In `_check_unimplemented`, delete the `E-SWEEP-UNSUPPORTED` block entirely and put this in its place:

```python
    sweep = doc.get("sweep") or {}
    for mode, code, why in (
        ("paired", "E-SWEEP-PAIRED-UNSUPPORTED",
         "couples parameters into one axis"),
        ("ablate", "E-SWEEP-ABLATE-UNSUPPORTED",
         "emits 1 + n one-change conditions and reads the baseline rather than re-emitting it"),
        ("sample", "E-SWEEP-SAMPLE-UNSUPPORTED",
         "draws continuous ranges and labels its conditions `NN_sample`"),
        ("groups", "E-SWEEP-GROUPS-UNSUPPORTED",
         "is an axis over units rather than parameters, so it needs `data.units.allocation` "
         "and `data.units.assign`"),
    ):
        if sweep.get(mode):
            c.error(
                code,
                f"sweep.{mode}",
                f"{why}, and is specified but not implemented in this build — this build "
                "expands `baseline` and `grid` only; the other modes will be honored in a "
                "later slice",
            )
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_validate.py -v && uv run ruff check . && uv run mypy`
Then confirm the retired identifier is gone: `grep -rn "E-SWEEP-UNSUPPORTED" src/ tests/` — expected: no matches.

- [ ] **Step 5: Record the identifiers**

```bash
cat >> docs/superpowers/spec-defects.md <<'EOF'

## New error identifiers: the four sweep modes

`E-SWEEP-PAIRED-UNSUPPORTED`, `E-SWEEP-ABLATE-UNSUPPORTED`, `E-SWEEP-SAMPLE-UNSUPPORTED`,
`E-SWEEP-GROUPS-UNSUPPORTED`. None is in § Errors core raises, which enumerates raise-time
codes. They replace the blanket `E-SWEEP-UNSUPPORTED` S1 introduced, following the pattern S2
used when it split `data.units`: retiring a blanket refusal must not leave the modes it covered
silently accepted. Retire these entries as each mode lands.
EOF
git add src/publishable/validate.py tests/test_validate.py docs/superpowers/
git commit -m "Refuse each unimplemented sweep mode on its own"
```

---

