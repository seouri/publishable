# Task 14 report

**Status:** done.

**Commit:** `24da5fc`

**Test summary:** `uv run pytest -q` → 1682 passed, 2 xfailed (baseline 1681 passed + 2 xfailed, plus the one new test). `uv run ruff check .` and `uv run mypy` both clean.

**Concerns:**

- `src/publishable/generators/experiment.py:55` raises `E-TEMPLATE-UNKNOWN` with the same stale wording ("no installed template registers `{template_name}`"). It's a raise at generate time, not a `validate` finding, so the § Errors row this task edited doesn't govern it, and it's outside this task's file list (`validate.py`, `docs/reference.md`, `tests/test_validate.py`). Left untouched; routing it is the controller's call.
- The § Errors row now discloses that the plugin leg of the message is aspirational (no entry-point resolution exists in this build yet), mirroring the disclosure already present on the sibling `E-TEMPLATE-COLLISION` row. Flagging in case a later task (entry-point resolution) needs to revisit this row's wording once the plugin registry is real.

---

## Addendum — ruling from coordinator, addressed in commit `d972d21`

Coordinator ruled the concern above **inside** this task rather than routed onward: `E-TEMPLATE-UNKNOWN` is one code with two emit sites (`validate.py` and `generators/experiment.py:55`), and the § Errors row governs the code, not one call site — so a second emitter still saying "no installed template registers" left the row describing only one of two live messages.

**What changed** (`src/publishable/generators/experiment.py`):
- The raise now uses the same wording as `validate.py`'s message: `` names `{template_name}`, which no template — core's, an installed plugin's, or this project's own `templates/` — registers (known: {…}) ``, built from `template_names(repo_root)` — this call site already had `repo_root` in scope (task 5's wiring), so only the message text was stale, never the resolution itself.
- Added the `(known: …)` list here too. It didn't exist before (the old message named no templates at all), and since `repo_root` is already in scope the cost is one import (`template_names` alongside `get_template`). The only remaining difference between the two messages is mechanical: one is a `ContractError` raise (`str(exc)`), the other a collected `Collector` finding — same text either way.
- `docs/reference.md`'s `E-TEMPLATE-UNKNOWN` row rewritten to state the *condition* (per this table's own rule, restated just above it: "Each row states the condition, not the wording") rather than describe message text: neither core nor local `templates/` registers the name, an installed plugin's is not yet checked (mirrors `E-TEMPLATE-COLLISION`'s existing disclosure), and the row now says explicitly that two surfaces (`validate` and `generate experiment`) raise it and that this one row governs both.

**Test:** `tests/test_cli.py::test_generate_experiments_unknown_template_message_matches_validates` — distinct names throughout (local template `cohort_local`, unknown name `not_anywhere`, matching the `validate.py` test's pattern) asserting the exact `str(excinfo.value)`. Mutated twice and confirmed each catches it, reverting in place both times:
1. Reverted the raise to the old wording — test failed on the message text.
2. Changed `template_names(repo_root)` → `template_names()` — test failed on the known-list (`generic` only, missing `cohort_local`).

**Verified:** grepped tracked `*.md` and all of `tests/` for `"no installed template registers"` again — no hits outside `docs/superpowers/` (gitignored, exempt). Confirmed no third site reports/raises `E-TEMPLATE-UNKNOWN` (`grep -rn "E-TEMPLATE-UNKNOWN" src/` → exactly `validate.py` and `generators/experiment.py`). `uv run pytest -q` → 1683 passed, 2 xfailed (1682 baseline + this new test); `ruff check .` and `mypy` both clean; `__pycache__` deleted before each verification run.

---

## Second addendum — review round 2, addressed in commit `e9eaa71`

Review of the addendum above returned two Important findings and two Minor. All four addressed.

**Important 1 — the two messages were pinned equal only by two hard-coded literals happening to agree, and the test's own name claimed a guarantee it didn't provide.** Reviewer proved it by mutating only `generators/experiment.py`'s string: exactly one test failed, `validate.py`'s copy was never consulted. Fixed by extracting `publishable.templates.registry.unknown_template_message(name, repo_root)` as the single construction — both `validate.py` and `generators/experiment.py` now call it rather than each holding its own f-string. Rewrote `test_generate_experiments_unknown_template_message_matches_validates` to drive both surfaces from one repo (writes a valid config via `generate_experiment`, corrupts its `experiment_type`, runs `validate_config` on it, and separately calls `generate_experiment` again with the same unknown name) and assert **the two live outputs equal each other** — not each against its own literal (the literal assertion stays too, underneath the equality one). Mutated `generators/experiment.py` back to a divergent hard-coded string (bypassing the shared helper) and confirmed the equality assertion fails; reverted in place and confirmed it passes again.

**Important 2 — `validate` does not raise, and the row said it did.** `validate_config`'s own comment states it is "contracted never to raise." Reworded the § Errors row: `validate` reports the code as a finding, never raising it; `generate experiment` raises it as a `ContractError`. The distinction between the two "Errors core raises" / "Errors validate reports" sections is preserved rather than flattened.

**Minor 3 — § The one config file's parallel sentence (`experiment_type` names the template and must resolve to...) carried the same three-homes claim with no unbuilt-plugin disclosure, unlike the § Errors row fixed in the same area.** Added the same disclosure there, linking to the `E-TEMPLATE-UNKNOWN` row in § Errors as the fuller version of the same fact — same claim, one place, not two.

**Minor 4 — the row didn't cover a missing or empty `experiment_type`, though both surfaces route through this exact code today.** Confirmed by direct call: `unknown_template_message("", None)` produces `` names ``, which no template... ``. Row's condition clause now opens "is missing, empty, or names a template...". New test `tests/test_validate.py::test_a_missing_or_empty_experiment_type_is_the_same_unknown_template` covers both the deleted-key and explicit-empty-string shapes and the empty-backtick-pair message text. Mutated `validate.py`'s `doc.get("experiment_type", "")` default to `"generic"` and confirmed the deleted-key case then failed (silently resolved to the builtin instead of drawing the code); reverted in place and confirmed passing.

**Not addressed, out of scope:** the two "no installed package registers" sentences at `docs/reference.md:3326` and `:3328` describing the four-registries mechanism collectively (templates, resolvers, probes, writers) — left as-is per the first round's ruling, routed to task 15.

**Verified:** re-grepped tracked `*.md`/`tests/` for the old wording — clean outside `docs/superpowers/`. `uv run pytest -q` → 1684 passed, 2 xfailed; `ruff check .` and `mypy` clean; `__pycache__` deleted before each run. Note: an unrelated commit (`075455e`, task 15 territory — entry-point/README/exit-code prose) landed in this same non-worktree repo between the two addenda; diffed it against my edits and confirmed no overlapping lines in `docs/reference.md`.
