## Task 7: the three stale claims — one deleted, one rewritten, one deleted

> **Bindings that reach this task:** design Decision 13. **Prefer deleting a claim to rewriting it** —
> a rewrite invents; a deletion cannot. A round that closed a false-owner comment closed it by
> **propagating the claim to two more sites**, which is why that rule is stated here rather than
> assumed.

| Where | The claim | What to do |
|---|---|---|
| `src/publishable/secrets.py` module docstring | *"`provenance.environment` is assembled from `os`, `hostname`, `hardware` and `uv.lock` alone"* | **DELETE the enumeration.** It is **false at `2b18435`** — the block is `{manager, python_version, uv_lock, uv_lock_hash}`, so it names three keys that did not exist and omits three that did — and it stays false after task 3, which adds the three and removes none of the four. The sentence's job is *"Never touches provenance"*, and the structural ground beside it — *"nothing in this module imports `publishable.provenance` or writes into the document it builds"* — carries the whole claim on its own |
| `src/publishable/study.py::_redact` docstring | `hostname` *"is never written today (measured at `ebf642a`: `provenance.environment` is `{manager, python_version, uv_lock, uv_lock_hash}`) — it is H6's … becomes 'redacted' the day H6 writes it, with no code change here"* | **REWRITE to the fact**, the one exception the rule allows: the sentence's subject *is* the arrival of this slice. The day arrived, no code changed here, and Fixture E is the pin. Keep the dated `ebf642a` measurement and mark it superseded rather than deleting the history |
| `tests/test_study.py::_fixture_y_record` docstring | the same `ebf642a` parenthetical, plus *"which nothing in this build writes"* | **DELETE the parenthetical.** The fixture's own reason for existing — a hand-built record exercising every redacted field at once — survives unchanged, and it stays valuable **beside** Fixture E rather than replaced by it. This is a **docstring** edit to a test named as guard-pin arm S, authorized here and nowhere else; **no assertion and no value in `_fixture_y_record` moves** |

**Steps**

- [ ] Make the three edits.
- [ ] **Sweep for the claim, not for the file the claim was first noticed in.** Three sweeps in one
      slice stopped one file short. Grep — newline-insensitively, over `src/`, `tests/`, the four
      documents **named individually**, `CLAUDE.md`, and `docs/superpowers/spec-defects.md` — for
      `never written`, `ebf642a`, and `manager, python_version` (whitespace-flattened). **Report every
      hit and what you did about it.** A tracked record (`docs/superpowers/**`,
      `.superpowers/sdd/**`) is **appended to, never retro-edited** — a spec records what was decided
      when it was written, and `spec-defects.md` is the one live list.
- [ ] Run arm S and report both tests pass. The docstring edit moves no assertion; report the
      `git diff` line count.
- [ ] Four gates. **Delta: 0 tests.** Commit.

**What this task must NOT touch.** Any assertion in `tests/test_study.py`. `study.py`'s or
`secrets.py`'s **code**. The other stale-claim candidates a sweep may turn up in a tracked record —
report them, do not retro-edit them.

---

