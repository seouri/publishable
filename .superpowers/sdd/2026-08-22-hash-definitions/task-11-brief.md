## Task 11: `W-PARAM-UNSET` at `validate`, and the shared helper

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is how the previous
> slice shipped a Critical, and this pointer is the fix. **Ruling F (the exclude chain) changes the
> command every hashing task runs.**

**Surface: `validate` through a `Collector`.**

**Files:** `src/publishable/validate.py`, `docs/reference.md`, `tests/test_validate.py`.

**The warning, and its boundary — which is the part that would otherwise be an overclaim.**
`W-PARAM-UNSET` is reported by `validate._check_parameters` for every `parameter_spec` path that carries
a default and that this config does not set — **one diagnostic naming all of them**, on
`W-TEMPLATE-VERSION`'s own enumerating message shape, never one per parameter. **It covers the
`parameters` block only.** An omitted **core-schema** key is the same symptom through the same code
(`Node.__getattr__` → `E-STEP-PARAM-UNKNOWN`) and is **filed, not built** — task 12 files it —
**unassigned, with the reason**: core itself reads core-schema keys defensively (`(config.get("sweep")
or {})`), so an omitted one harms nothing core does; the only casualty is a **step** reaching for it
through `cfg`, and knowing whether a step does that means reading its body, which is the line core does
not cross. Closing it would need either the forbidden defaults structure or the greenfield line crossed.

**It is a warning and not an error, and the reason is measured.** Omitting a defaulted parameter is what
almost every hand-written config does; a freshly `init`-ed config sets all four of `generic`'s, so the
warning does **not** fire for a scaffolded project. And core cannot know whether a step reads the
parameter.

**`W-TEMPLATE-VERSION` keeps its unset-and-defaulted clause** (Decision 11). The clause is **true**, so
*prefer deleting a claim to rewriting it* does not license removing it — that rule is about false claims.
What changes is that both sites compute the list through **one** helper, which is the `covered_config`
precedent for how two sites do not drift.

**§ Corrections 7 and 8 bind this task.**

- [ ] **Step 1: extract the shared helper.** `_check_versions` already computes exactly this list —
      `[path for path, param in template.parameter_spec.items() if path not in set_here and param.default
      is not MISSING]`. Extract it once and call it from both sites. **Non-behavioural**: arm F asserts
      `W-TEMPLATE-VERSION`'s full message and **zero characters change**.
- [ ] **Step 2: report the warning from `_check_parameters`**, after the existing `E-PARAM-MISSING` loop,
      at path `parameters`, enumerating every unset-and-defaulted path in one message and stating the
      consequence (`cfg.parameters.<path>` raises `E-STEP-PARAM-UNKNOWN`).
- [ ] **Step 3: Fixture K, with its control arm.** Two configs against `generic`: one omitting
      `analysis.confidence` and `analysis.drop_missing` — the warning fires **naming both**, exit 0,
      `has_errors` False — and one setting all four, where **no** warning fires. **The second arm is what
      makes the first non-vacuous**, and it fails if the check fires unconditionally.
- [ ] **Step 4: mutations 10, 11 and 12.** (10) Delete the call site — caught by Fixture K's first arm;
      **check the render's other diagnostics for the string `analysis.drop_missing` first** rather than
      assuming nothing else produces it. (11) Fire for parameters that **are** set — caught by the
      control arm. (12) Delete `W-TEMPLATE-VERSION`'s unset clause after the extraction — caught by arm F,
      which asserts the full message and of which **the clause is a substring**.
- [ ] **Step 5: mutation 13 is NAMED BLIND IN ADVANCE and owes a replacement.** Replacing the shared
      helper's body at **one** of its two call sites with an inlined copy is caught by nothing: two
      identical implementations produce identical results, which is what sharing them prevents. **The
      replacement is a reading obligation, and it is stated as one: the batch review reads both call
      sites and reports that each calls the helper.**
- [ ] **Step 6: run the full suite and report the count of tests whose render changed.** **This plan
      measured that count and it is ZERO** (§ Corrections 7): with the warning wired in exactly this
      shape, `uv run pytest -q` returned **2931 passed, 1 skipped, 2 xfailed** — no failures. The
      positive control fired (a direct `_check_parameters` call over a config omitting two of `generic`'s
      four produced exactly one `W-PARAM-UNSET` naming both; the complete config produced none), and an
      instrumented run of `tests/test_validate.py`, `tests/test_templates.py`, `tests/test_materialize.py`
      and `tests/test_diagnostics.py` showed the warning firing in **7** tests, all still passing.
      **The measurement is valid for THIS shape — one diagnostic, at path `parameters`.** A per-parameter
      shape, or a different `path`, moves finding counts and path sets and **the measurement must be
      re-run.** A non-zero count is a **disagreement to report**, and for each moved test say whether the
      assertion was *updated* or *loosened*.
- [ ] **Step 7: DELETE the false clause in a shipped test's docstring. § Corrections 8.**
      `test_an_unset_parameter_is_named_only_when_the_version_moved`'s docstring reads *"a config matching
      the installed version draws no warning at all, so a defaulted parameter it omits is not
      reported."* After this task the second clause is **false** and the test **still passes**, because
      its assertion is `"W-TEMPLATE-VERSION" not in codes(path)`. **Delete the false clause; keep the
      test's name** — it is still true of `W-TEMPLATE-VERSION`, and renaming it breaks every grep that
      finds it. **This edit sits OUTSIDE guard-pin arm F**, whose claim is that the *message* changes zero
      characters; say so in the report so a reviewer does not read it as an arm-F violation.
- [ ] **Step 8: the § Warnings row and the § Validation row.** One § Warnings core reports row for
      `W-PARAM-UNSET` covering its **one** emit site, stating the condition rather than the wording, and
      one § Validation row — a row there and a code there are the same check seen from two ends.
      **`W-TEMPLATE-VERSION`'s row does not change** (Decision 11), and `E-STEP-PARAM-UNKNOWN`'s does not
      either: its row describes a `cfg` path the config does not hold, which stays exactly true.
      **Mechanical pass** on both edits.
- [ ] **Step 9: grep before claiming.** `grep -rn "W-PARAM-UNSET" src/ tests/ docs/*.md README.md` → **0**
      at `f8450f9`, control `E-CODE-DIRTY` → 3. Re-run and report both.

**Delta:** +2 tests, plus one deleted docstring clause.

**What this task must NOT touch.** `_check_versions`' behaviour or message. `hashes.py`. The core-schema
half — **filed, not built**. `E-PARAM-MISSING`'s condition, which is about a **defaultless** parameter
and is a different check.

**Guard-pin arms this task may edit: F — and the specified edit is ZERO characters.** Arm F passing
unedited after this task is the proof that the extraction was behaviour-preserving.

---

