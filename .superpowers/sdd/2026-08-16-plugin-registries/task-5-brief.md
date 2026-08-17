## Task 5: The `NOT BUILT` markers and the enum comments

**Files:** Modify `docs/reference.md`, `src/publishable/materialize.py`, `tests/test_materialize.py`.

**Interfaces:**
- Consumes: § The one config file's identifying-fields paragraph, which begins "**The four
  identifying fields above `metadata` say what this config is written against**" and contains the
  clause "the plugin case is not yet checked, since no entry point is resolved in this build";
  `materialize.py`'s `data.units.from` line, which today renders
  `'    from: index.csv                # index.csv | {glob: "*.dcm"}'`; § The one config file's own
  `from:` line, which renders `# index.csv | {glob: "*.dcm"} | {resolver: <name>} (NOT BUILT)`;
  § Where units come from's second `from` enum, which is the three-line fenced YAML block showing
  `from: index.csv`, `from: {glob: "*.dcm"}` and `from: {resolver: plate_wells}`.
- Produces: the generated config's `from` comment listing **every** value § The one config file
  defines, with the unbuilt one marked; and the identifying-fields clause corrected.

**What this task does NOT retire, and why each is somebody else's.** § The one config file's
"**Two** declarations above are not yet built" and the `from:` line's own `(NOT BUILT)` are **Part
B's**, retired by task 24 with the refusal. § Errors' `E-TEMPLATE-COLLISION` clause was deleted by
task 2. § Errors' `E-TEMPLATE-UNKNOWN` clause is **task 11's**. § Creating a plugin's "The two local
cases" sentence was rewritten by task 2. § The importable surface's three-name row was split by task
3. § CLI reference's `plugin new` and `list-templates` rows and § Package layout's
`plugin_scaffold.py` stay `NOT BUILT` — the first two are Part B task 21's and the third with them.
§ Creation commands' and § Generators' `--plugin` claims are **task 6's**. Sweep for each of those
strings and confirm you left it alone rather than assuming.

**The live defect this task closes.** Re-probed by generating a real config: `reference.md` writes
`# index.csv | {glob: "*.dcm"} | {resolver: <name>} (NOT BUILT)` while `materialize.py` writes
`# index.csv | {glob: "*.dcm"}` — **two values where the document defines three**. The enum-comment
rule is a cross-document invariant, and nothing in the suite pins that line: `grep -rn 'glob' tests/`
returns only `Path.glob` calls, so this line has been wrong and green.

**Names already at module level in `tests/test_materialize.py`:** `rendered`, `_MARKED_LATER_SLICE`,
`_MARKED_FIELD_PATHS`, `_refusal_codes`, `_rendered_with_default`, `_rendered_with_keys`, plus the
`test_*` functions. Add no helper; extend an existing test.

- [ ] **Step 1: Write the failing assertions.** In `tests/test_materialize.py`, replace the body of
      `test_the_generated_units_block_carries_its_comments` with:

```python
def test_the_generated_units_block_carries_its_comments():
    """The `from` enum lists every value § The one config file defines, and marks
    the one this build refuses.

    Two values where the document defines three was live and green until this
    test: nothing else in the suite reads this line. The `(NOT BUILT)` marking is
    asserted *with* a refusal below rather than alone, because a marking core does
    not honour is exactly as misleading as a missing one.
    """
    text = rendered()
    assert '# index.csv | {glob: "*.dcm"} | {resolver: <name>} (NOT BUILT)' in text
    assert "# within | between" in text
```

      and append, beside it:

```python
def test_the_from_enum_s_not_built_marking_is_honoured_by_core(git_repo, tmp_path):
    """The marking is a claim about behaviour, so it is checked against behaviour.

    `_MARKED_FIELD_PATHS`'s `(x: later slice)` convention cannot carry this one —
    its regex reads a single unqualified value and `{resolver: <name>}` holds a
    colon — so the `(NOT BUILT)` spelling § The one config file already uses is
    what `init` writes, and this is its honesty check. Asserted *alongside* the
    wholesale refusal rather than on the whole code set, so retiring
    `E-DATA-RESOLVER-UNSUPPORTED` is a one-line deletion here.
    """
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "index.csv").write_text("patient_id\np1\n")

    text = materialize_config(
        template=get_template("generic"),
        template_name="generic",
        name="cohort-pilot",
        input_dir=str(input_dir),
        output_dir=str(tmp_path / "output"),
        entrypoint="cohort_pilot.experiment:CohortPilotExperiment",
    )
    doc = yaml.safe_load(text)
    doc["metadata"]["description"] = "a pilot"
    doc["metadata"]["authors"] = ["A"]

    config_path = git_repo / "configs" / "cohort-pilot" / "config.yaml"
    config_path.parent.mkdir(parents=True)

    # The value `init` actually writes validates clean — the positive companion,
    # without which the refusal below could pass on an unrelated fault.
    assert _refusal_codes("from", doc, config_path) == []

    doc["data"]["units"]["from"] = {"resolver": "plate_wells"}
    assert "E-DATA-RESOLVER-UNSUPPORTED" in _refusal_codes("from", doc, config_path)
```

- [ ] **Step 2: Run and see it fail.** `uv run pytest tests/test_materialize.py -q`.
      `test_the_generated_units_block_carries_its_comments` must fail on the three-value string.
      The second test must **pass already** — it asserts today's behaviour, and it is here as the
      honesty half of the marking rather than as a new refusal. If it fails, the brief is stale and
      the refusal moved; stop and say so.

- [ ] **Step 3: Implement.** In `src/publishable/materialize.py`, replace the `from` line:

```python
        '    from: index.csv                # index.csv | {glob: "*.dcm"} '
        "| {resolver: <name>} (NOT BUILT)",
```

      Two source lines, one rendered line — the file's line-length limit is 100 and the joined
      string is longer. Confirm the rendered output has exactly one `#` on that line and no double
      space where the two fragments meet.

- [ ] **Step 4: Run and see it pass.** `uv run pytest tests/test_materialize.py -q`, then the whole
      suite: **1999 + 1 new test passed, 2 xfailed.**

- [ ] **Step 5: Correct the identifying-fields clause.** In § The one config file, the sentence
      beginning "`experiment_type` names the template and must resolve to one core, an installed
      plugin, or this project's own `templates/` registers" continues "— the plugin case is not yet
      checked, since no entry point is resolved in this build, the same disclosure
      [`E-TEMPLATE-UNKNOWN`](#errors-validate-reports) carries". **Delete that clause**, leaving the
      sentence to read "…or this project's own `templates/` registers;". Deleting rather than
      rewriting: the disclosure it points at is task 11's to replace, and propagating a claim to a
      second site is how a previous round closed a false-claim finding by making it worse.

- [ ] **Step 6: Confirm § Where units come from's enum is already total.** Its fenced YAML shows all
      three `from` forms. Read it and change nothing — it is the reference the two comment spellings
      are checked against, and it was correct.

- [ ] **Step 7: Mechanical pass** over § The one config file's edited paragraph: anchors resolve, no
      trailing whitespace, no tab, no invisible unicode, no en dash. Then **sweep the four documents
      by name** for `no entry point is resolved in this build` and read every surviving hit —
      exactly one must remain, in § Errors `validate` reports' `E-TEMPLATE-UNKNOWN` row, which is
      task 11's. Can-fail control: the same sweep before your edit returns strictly more.

- [ ] **Step 8: Verify.** All four commands. `uv run ruff format --check .` → 76 files, 0 to
      reformat — `materialize.py`'s two-line string must be formatted as `ruff` wants it, so run
      `uv run ruff format .` and then `--check` and confirm the diff is only your line.

- [ ] **Step 9: Mutate — one, and it discriminates.** In `materialize.py`, drop the second fragment
      so the line renders `# index.csv | {glob: "*.dcm"}` again.
      `test_the_generated_units_block_carries_its_comments` must FAIL on its first assertion.
      **Checked against the test body:** the assertion is an `in` over the full three-value literal,
      which the two-value render cannot contain. Then revert by editing the file back, delete
      `__pycache__`, re-run, confirm green.

      A second mutation is available and **cannot discriminate**, so do not use it: changing
      `(NOT BUILT)` to `(NOT-BUILT)` fails the same assertion for the same reason and proves nothing
      the first does not. The marking's *honesty* is what the second test covers, and its mutation
      lives in Part B: retiring `E-DATA-RESOLVER-UNSUPPORTED` without retiring the marking makes
      `test_the_from_enum_s_not_built_marking_is_honoured_by_core` go red, which is the coupling it
      exists to create.

- [ ] **Step 10: Which deliverable no mutation reaches.** The § The one config file clause deleted
      in step 5 is prose and nothing pins it; **nothing in this slice closes that**, and task 11's
      companion deletion is in the same position. Stated rather than papered over.

- [ ] **Step 11: Commit.** `fix: init's from comment lists every value the schema defines, and marks the unbuilt one`

---

