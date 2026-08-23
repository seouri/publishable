## Task 1: the guard pin — six arms, captured before anything moves

> **Bindings that reach this task:** design Decision 16 (the pin's shape), **Ruling O** (restated
> below, because `hardware`'s shape decides arm P's advance spec and `task-brief` extracts this section
> and nothing else).

**RULING O, restated here in full:** `provenance.environment.hardware` carries **`cpu_count` and NOT
`gpu`**. It is a **mapping** — `{"cpu_count": <int|None>}` — because § The two files shows a mapping
and because `os.cpu_count()` can answer `None`. A GPU is an **apparatus fact**, not a provenance key.
**This decides arm P's advance spec:** the assertion is `set(hardware) == {"cpu_count"}`, never
`isinstance(hardware, int)`. H6a's batch-2 Major was a pin captured against a **superseded signature**,
which forced the next task to choose between a broken import and an unauthorized edit; capturing arm P
in a shape Ruling O has already decided is what prevents the same round-trip here.

**Six arms. Five have NO authorized editor.** The device's whole value is that a passing arm is the
proof. **An implementer may not self-authorize an edit to an arm with no authorized editor, even when
the edit is mechanical and even when it turns out clean** — the route is a controller ruling, which
costs one round-trip and preserves the thing the arm exists for.

| Arm | Where it lives | Sole authorized editor | Advance spec |
|---|---|---|---|
| **P** | `tests/test_cli.py::test_h8b_arm_d_the_five_figures_diff_reads` (exists; H8b's) | **task 3 only** | The `assert environment == {"manager": "uv", "uv_lock": None, "uv_lock_hash": None}` line is **byte-identical after the edit**. Task 3 adds exactly three `.pop(...)` calls and exactly three assertions, listed in task 3 |
| **Q** | `tests/test_cli.py::test_h8b_arm_c_the_records_key_lists_status_and_exit` (exists) | **NONE** | unchanged, byte for byte |
| **R** | `tests/test_cli.py::test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text` (exists) | **NONE** | unchanged, byte for byte |
| **S** | `tests/test_study.py::test_study_add_redacts_hostname_when_present_on_a_synthesized_record` and `test_study_add_leaves_hostname_untouched_when_absent_from_the_source` (exist) | **NONE** for the test bodies; task 7 edits `_fixture_y_record`'s **docstring only** | both bodies unchanged; the docstring edit is named in task 7 so it is not read as an arm edit |
| **T** | **NEW**, `tests/test_cli.py` | **NONE** | written by this task, green against today's behaviour, unchanged thereafter |
| **U** | `tests/test_cli.py`'s `_h6a_pin_project` arms — H6a's own literal digests | **NONE** | unchanged. They assert individual keys, so the three insertions are invisible to them — **which is the additive claim, and a passing arm is the proof** |

**Steps**

- [ ] Re-confirm the baseline with one foreground `uv run pytest -q` and reconcile any difference from
      *2963 passed, 1 skipped, 2 xfailed* **before** doing anything else.
- [ ] **Locate arms P, Q, R, S and U by test name** (`grep -n` for each name) and **add one sentence to
      each docstring** naming its H6b authorization: *"H6b guard-pin arm \<X\>: sole authorized editor
      \<task N | NONE\>."* This is the only edit this task makes to an existing test, it adds no
      assertion and moves no literal, and the report must show the `git diff` line count per arm.
- [ ] **Prove arm R is unaffected by Ruling O's edit** before task 2 makes it: extract
      `_H5A_ARM_D_LITERALS` from `tests/test_cli.py` and test each member against the literal string
      `    hardware: {gpu: "1x A100 80GB", cpu_count: 32}`. **Report the members and the result.** This
      plan measured **no member matches**; a different answer is a disagreement to report, not to
      absorb.
- [ ] **Write arm T** — new coverage. `grep`ped newline-insensitively over every file in `tests/` for
      both codes at `2b18435`: **nine hits, none through `main([...])`** — two direct calls in
      `tests/test_provenance.py`, four monkeypatched raises in `tests/test_validate.py`, one docstring
      each in `tests/test_lineage.py` and `tests/test_study.py`. **Re-run that grep and report it**
      rather than repeating this sentence.

Arm T, three invocations, all measured at the console script before this plan was written:

```python
def test_h6b_arm_t_the_git_layers_two_codes_at_the_cli(tmp_path, capsys, monkeypatch):
    """H6b guard-pin arm T: SOLE AUTHORIZED EDITOR — NONE.

    New coverage. Both codes are raised by `provenance.py` and neither is
    asserted through `main([...])` anywhere in `tests/` at `2b18435`
    (grepped newline-insensitively: nine hits, all direct calls,
    monkeypatched raises, or docstrings). H6b task 5 documents these two
    codes and changes no behaviour, so this arm is what makes the two new
    § Errors rows checkable against behaviour rather than against prose.

    Measured at the installed console script before it was written:
      * `run` on a project whose `.git` was removed  -> E-GIT-NO-REPO, exit 1
      * `generate experiment` with cwd outside a repo -> E-GIT-NO-REPO, exit 1
      * `run` in a `git init`-ed repo with no commit -> E-GIT-NO-COMMIT, exit 1,
        and NOT E-CODE-DIRTY, even though both hashed trees are untracked
    """
```

- [ ] Build arm T's three invocations from `tests/test_cli.py`'s existing project helper. For each:
      assert the exit code is `EXIT_WRONG`, assert the code string appears in **`capsys`' err
      stream** (`main`'s `except PublishableError` prints to stderr — asserted on the stream the thing
      writes to, not on combined output), and for the third **additionally assert `"E-CODE-DIRTY"` is
      absent**, which is the ordering claim design Decision 3's row makes.
- [ ] **Prove arm T can fail.** Run mutation 11 — reorder `provenance.git_provenance` so the dirty
      computation precedes the `HEAD` check — against a **copy** of `provenance.py`, confirm the third
      invocation fails on the `E-CODE-DIRTY`-absent assertion, restore from the copy, and re-run the
      test to confirm it passes again. **Verify the revert by behaviour.**
- [ ] `uv run pytest`, `ruff check`, `ruff format`, `mypy`. **Delta: +1 test** (arm T). Commit.

**What this task must NOT touch.** `src/` — nothing at all. Any assertion, literal or name inside arms
P, Q, R, S or U. `docs/`. The three keys themselves: this task writes no production code.

---

