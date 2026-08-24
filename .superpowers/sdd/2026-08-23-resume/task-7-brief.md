## Task 7

**Pointer: Decision 14 binds this task. You define a value object and change no behaviour.**

Add `cli.Resumed`, a **frozen** dataclass:

```python
@dataclass(frozen=True)
class Resumed:
    run_dir: Path
    prior_results: tuple[ExecutionResult, ...]
    attempts: dict[tuple[str, int | None, str | None], int]
    baseline: "apparatus.Observations | None"
    recorded_manifest: dict[str, Any]
```

Frozen for the same reason `Prepared` is: phases 6–10 must not write back into what a second entry
pinned. `prior_results` is a tuple rather than a list so it cannot be appended to in place.

**Add the parameter to `_execute_prepared`'s signature only** — `resumed: Resumed | None = None` — and
assert nothing reads it yet. **Do not thread it through the 36-field unpack block**; correction 19
says why, and your report must show that block unchanged.

**Must not touch:** the unpack block; `Prepared`; any `*.md`; any arm.

**Mutation:** make `Resumed` mutable (caught by a test that asserts `dataclasses.replace` works and
attribute assignment raises `FrozenInstanceError` — a two-branch mutation, checked: a mutable
dataclass permits the assignment).

---

