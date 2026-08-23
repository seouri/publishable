## Task 4: Ruling Q — the reason in § What `study add` redacts, and the end-to-end bundle pin

> **Bindings that reach this task:** **Ruling Q**, restated in full below. It is the whole of this task.

**RULING Q, restated here in full:** `os` and `hardware` are **NOT** redacted by `study add`;
`hostname` **is**. Grounds: redaction exists for **identity and credentials**, and a bundle reader needs
to know what platform produced a number — that is provenance, not exposure. `hostname` names a machine
and often a person; `os` and `cpu_count` name neither. **Record the reason in § What `study add`
redacts** so the next reader does not re-litigate it, **and pin that a bundle carries them
unredacted** — the `hostname` redaction wiring already exists and was written against a key nobody
wrote, so **the pin is the point** for all three.

**Steps**

- [ ] In `docs/reference.md` § What `study add` redacts, add the **reason** — not two table rows. The
      table's four rows stay four. The passage says: `provenance.environment.os` and `.hardware` travel
      **unredacted** and why — a platform string and a core count name neither a person nor an
      institution, and *what platform produced this number* is provenance, which is what a bundle
      exists to carry; the same line the section already draws for `input_manifest_hash`, which
      survives while its path does not. Say it once, in the section that owns it.
- [ ] **Fixture E — end to end, BOTH halves.** Run a real project. `study new` a bundle **under
      `tmp_path`, outside any repository** — measured: `study new` and `study add` both refuse a bundle
      path inside a git repo (`E-STUDY-IN-REPO`, `provenance.find_repo_root` succeeding is the
      refusal). `study add` the run's `run.yaml`. Then read **both** records — the bundled member and
      the **source** `run.yaml` from the run directory — and assert:

```python
    assert bundled["provenance"]["environment"]["hostname"] == REDACTED
    assert bundled["provenance"]["environment"]["os"] == source["provenance"]["environment"]["os"]
    assert isinstance(bundled["provenance"]["environment"]["os"], str)
    assert bundled["provenance"]["environment"]["os"]
    assert (
        bundled["provenance"]["environment"]["hardware"]
        == source["provenance"]["environment"]["hardware"]
    )
    assert isinstance(bundled["provenance"]["environment"]["hardware"], dict)
```

      **The source record is the positive control.** Comparing against a value the same run produced
      means an implementation that wrote nothing fails **both** halves, where a bare `is not None`
      would pass on an empty string. Asserting only the redaction would leave the not-redacted half
      untested, and *a control asserting only absences passes identically if nothing ran*.
- [ ] **Run both mutations and report each:**
      **7** make `_redact` also redact `os` → the verbatim half fails and the **redaction half still
      passes**, which is why both live in one block.
      **8** make `_redact` stop redacting `hostname` → the redaction half fails **and** arm S's
      synthesized-record test fails. Report both, from a real record and a hand-built one.
- [ ] Run arm S and report that both its tests pass **without an edit**. Fixture E is added **beside**
      the synthesized record, never in place of it: the hand-built record still exercises every
      redacted field at once, and the real record exercises the wiring against a key core now writes.
- [ ] Mechanical pass on the `reference.md` edit.
- [ ] Four gates. **Delta: +1 test.** Commit.

**What this task must NOT touch.** The four rows of § What `study add` redacts — the ruling adds a
**reason**, not rows. `study.py`'s code (only task 7 touches its docstring). Arm S's test bodies. § The
two files (task 2's). § Errors core raises (task 5's).

---

