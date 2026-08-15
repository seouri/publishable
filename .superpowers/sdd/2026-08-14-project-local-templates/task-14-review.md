# Task 14 review — `E-TEMPLATE-UNKNOWN` stops being about installation

Reviewed: `a0d2ab6..d972d21` (commits `24da5fc`, `d972d21`), against working tree at `075455e`
(task 15's docs-only commit is an ancestor of HEAD; it touches `docs/reference.md` only and does
not alter the code under review).

**Spec compliance: ✅**
**Task quality: approved with findings** (2 Important, 5 Minor)

---

## What was verified, and how

**Baseline reproduced.** `1683 passed, 2 xfailed`; `uv run ruff check .` → all checks passed;
`uv run mypy` → no issues in 42 source files. `ruff format --check` not raised (known, out of scope).

**Emit sites.** `grep -rn "E-TEMPLATE-UNKNOWN" src tests docs README.md` → exactly two raise/report
sites in `src/`: `validate.py:517` and `generators/experiment.py:58`. **No third site.** A third
*call site* of `get_template` exists — `cli.py:1491`, the run-time `aggregate` lookup — but it neither
raises nor reports the code, `validate` having gated the name upstream. The § Errors table carries one
row per code, so the row governing both emitters is correct.

**Message agreement.** Both sites now produce byte-identical text (the line breaks differ, the
concatenation does not):
`names `<name>`, which no template — core's, an installed plugin's, or this project's own `templates/` — registers (known: …)`.

**Old string gone.** No occurrence of `no installed template registers` in any tracked file or in
`tests/`. (`docs/superpowers/` gitignored, exempt.)

**Mutations run where the behaviour lives**, `__pycache__` deleted before each run, reverted by
in-place edit and each revert verified by `diff` against a pre-mutation copy (tree `CLEAN` after):

| Mutation | Result |
|---|---|
| `experiment.py` message only: `core's` → `core` | **1 failed** (`tests/test_cli.py::test_generate_experiments_unknown_template_message_matches_validates`), 1682 passed. `validate.py`'s copy untouched and green — see Important 1 |
| `experiment.py`: `template_names(repo_root)` → `template_names()` | 1 failed, and the assertion diff is exactly `- s (known: cohort_local, generic)` / `+ s (known: generic)` — the failure is the **missing local name**, not formatting |
| `validate.py`: `template_names(repo_root)` → `template_names()` | 1 failed (`test_the_unknown_message_lists_local_templates_among_the_known`), same diff, same attribution |

**Distinct-name trap holds in both tests.** Local template `cohort_local`, requested name
`not_anywhere`; the asserted string contains both, so neither assertion can pass by the interpolated
name coinciding with a known name. This holds for the `excinfo` assertion in `tests/test_cli.py` too —
it asserts `str(excinfo.value)` in full, not a substring.

**Mechanical pass on the two edited `docs/reference.md` lines.** `#creation-commands` and
`#templates-where-parameters-are-defined` both resolve; no duplicate anchors in the file; both edited
rows are 2-column and match the header; no `x`-for-`×`. `git diff a0d2ab6..d972d21 -- docs/reference.md
| grep -nP '^\+.*([ \t]$|\t)'` is empty, so **no added line in either commit** — table row or prose —
carries trailing whitespace or a tab. No count phrase
near the edited row is disturbed — "Five faults return `validate_config` early" is unchanged and still
lists `E-TEMPLATE-UNKNOWN`, and no phrase counts rows or disclosures.

**The two out-of-brief edits are both correct.**
- § The one config file's `experiment_type` sentence carried the same stale claim, in the same
  document, about the same check. Fixing it with the row is in scope, not scope creep.
- The condition-not-wording rework is backed by that section's own sentence at `docs/reference.md`
  § Errors `validate` reports ("Each row states the condition, not the wording"), which is real and
  sits above the table.
- The unbuilt-plugin disclosure follows an **existing** form rather than inventing one: the sibling
  `E-TEMPLATE-COLLISION` row already reads "is not yet checked: no entry point is resolved in this
  build". Not an undated build fact in the objectionable sense.

---

## Findings

### Important

**I1. Nothing pins the two messages identical — proved empirically, not argued.**
Mutating `generators/experiment.py`'s string alone fails exactly one test; `validate.py`'s copy is
never consulted. Each test hard-codes its own literal of the message. So the failure mode the § Errors
row now asserts away — one code, one row, two emitters, one wording — is caught only against each
site's *own* frozen copy. Edit one message and its own test literal together and the two surfaces
diverge with `1683 passed`. This is the branch's recurring "a dimension no assertion can see": the
property is *agreement between the two*, and no assertion can see it.
The test is also **named and documented for the guarantee it does not provide**:
`test_generate_experiments_unknown_template_message_matches_validates` never touches `validate`'s
message, and its docstring says "one code with two emitters … so the wording must agree" while pinning
one literal on one side. That is this repo's most-repeated defect class (a docstring claiming a
guarantee the code does not provide), and the mutation above is the proof.
Remedy, either is enough: (a) one message builder both sites call, or (b) make the test live up to its
name — drive both surfaces over one fixture and assert
`str(excinfo.value) == messages_by_code(cfg)["E-TEMPLATE-UNKNOWN"]`, comparing the two products rather
than each against a literal. Failing either, rename the test and its docstring to what it checks.

**I2. The row says `validate` *raises*, and `validate` is contracted never to raise.**
New row text: "Two surfaces raise it under this condition, `validate` and `generate experiment`'s own
resolution". `validate.py`'s own comment eight lines above the emit site says core reports the
load-time codes "at all because `validate` is contracted never to raise", and this table distinguishes
the two carefully everywhere else — `E-TEMPLATE-COLLISION`: "Not a finding `validate` computes but a
`ContractError` the merge raises". The row's tail half-concedes it ("whichever reports it"). Not a
wording nit: it is a document sentence contradicting a contract the same document states.
Suggested: "Two surfaces report it — `validate` as a finding, and [`generate experiment`](#creation-commands)'s
own resolution as a `ContractError` raise — and this one row governs both."

### Minor

**M1. The message names a plugin leg this build cannot reach.** Vacuously true in *outcome* (no plugin
can register a template here, so "no installed plugin registers it" never misreports), misleading about
*mechanism*, and disclosed in the § Errors row per existing precedent. No change wanted now; the H7b
slice should re-read the message when the plugin registry becomes real. Same analysis covers the
`(known: …)` list enumerating two of the three named homes.

**M2. § The one config file's rewritten sentence carries no disclosure**, unlike the § Errors row it
was fixed alongside: "must resolve to one core, an installed plugin, or this project's own `templates/`
registers". Present-tense specification is the sanctioned way to write an undated claim, so this is
legitimate — flagged only because the two edits in one commit now disclose asymmetrically.

**M3. The reworked row still does not fully describe the check.** Verified by probe: a config with
`experiment_type` **absent**, and one with it set to `""`, both report `E-TEMPLATE-UNKNOWN` with
"names ``, which no template … registers (known: generic)" — `validate.py:495` reads
`doc.get("experiment_type", "")` and the empty name simply fails to resolve. The row's condition
("`experiment_type` names a template neither core nor …") describes a name that is present and wrong,
not a name that is absent. Pre-existing gap, but a rework *toward stating the condition* is the moment
to close it — "…, or declares no `experiment_type` at all".

**M4. § Creating a plugin still describes the old world for templates.** `docs/reference.md`
§ Creating a plugin: "`validate` reports a config naming one that no installed package registers", and
"`validate` can answer 'no installed package registers `plate_wells`' without importing a line of that
package". The first covers all four registries including templates, for which it is now incomplete;
both describe entry-point resolution that this build does not perform. Outside task 14's file list, and
task 15's `075455e` edited that same section without touching these two sentences — so route it, do not
charge it here.

**M5. Report wording.** The report says `d972d21` "added the `(known: …)` list here too … the cost is
one import" — accurate — but also that `E-TEMPLATE-UNKNOWN` has "two emit sites" full stop. Worth
recording that `get_template` has a **third** caller (`cli.py:1491`) which resolves a template and emits
nothing, precisely because `validate` gated it; a future reader grepping `get_template` rather than the
code will hit it.

---

## Verdicts

- **Spec compliance: ✅** — the documents lead and were changed first; one row per code governs both
  emitters; the unbuilt plugin leg is disclosed in an existing form; no third emitter; the old string
  is gone from every tracked `*.md` and from `tests/`. I2 does not tip this: it is an accuracy defect
  in new prose, fixable in place, not a process violation — the document still led the code, the row
  still governs one code across both emitters, and the disclosure follows precedent.
- **Task quality: approved with findings** — I1 and I2 Important, M1–M5 Minor. I1 is the one worth
  fixing inside this slice: the property the row now asserts is unpinned by any test.
