# Task 15 report

**Status:** Done — `docs/reference.md` edited in the four assigned sections; § Errors' `E-TEMPLATE-UNKNOWN` row and § The one config file untouched, as instructed.

**Commit:** `075455e` — `docs/reference.md` only, staged and committed by itself. The repo also has an unrelated, uncommitted change to `src/publishable/generators/experiment.py` (a wording tweak to the `E-TEMPLATE-UNKNOWN` message: "core's" → "core") that appears to be the concurrent task-14 review's in-progress edit, since this is a shared working tree with no worktree isolation. I left it unstaged and uncommitted rather than touch it or fold it in.

**Summary:** Added the sentence § Creating a plugin owed (`validate` importing every `templates/*.py` to learn its registration, beside the entry-point paragraph's "without importing a line of that package" claim); rewrote § The generated README's paragraph to stop claiming `generate experiment` populates the experiments/credentials regions (both NOT BUILT per § Generators) and recorded `required_env`'s deadness plus the parameter table's missing README region; widened § Exit codes' `E-STEP-EXISTS` clause into a shared-behaviour statement naming all four greenfield-refusal codes (`E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS`, `E-STEP-EXISTS`, `E-TEMPLATE-EXISTS`) while explicitly excluding `E-ARTIFACT-EXISTS`; added one sentence to § Templates on `templates/__pycache__/` being covered by the scaffold's `.gitignore`.

**Verification:** Confirmed `required_env` is declared-but-unread via grep across `src/` before writing the claim down. Ran a link/anchor check against every heading in `docs/reference.md` (fenced code excluded) — no broken anchors introduced by my edits. `uv run pytest -q`: 1682 passed, 2 xfailed, 1 failed — `test_generate_experiments_unknown_template_message_matches_validates`, failing only because of the uncommitted `experiment.py` wording change noted above; unrelated to any docs-only edit here. `ruff check` clean on the touched path.

**Concerns:**
1. ~~The uncommitted `experiment.py` change~~ — resolved by the coordinator: it was task-14's reviewer mutating source files concurrently in the same unworktreed tree, not a conflict on my end. My commit contained only `docs/reference.md`, so it cost nothing. No action needed.
2. Out-of-scope finding re: § Secrets & credentials' `required_env`/`requires_env` claim — the coordinator ruled this **not a defect**: `secrets.py` is itself marked "not yet built" in § Package layout, so that sentence is a specification claim about an unbuilt module, the sanctioned pattern here. Distinguishing rule to carry forward: an unbuilt reader of an *unbuilt* surface is spec; an unbuilt reader of a *shipped* surface (like `BaseTemplate.required_env`, which is what I correctly flagged in the generated-README paragraph) is a defect.

## Addendum: routed finding from task 14's review

**Status:** Done — commit `6468842`, `docs/reference.md` only.

Task 14 rewrote `E-TEMPLATE-UNKNOWN`'s message and its § Errors `validate` reports row to say a template name must resolve against core, an installed plugin, *or* the project's own `templates/` — three homes, not one. That left § Creating a plugin's "**Four registries, one mechanism.**" paragraph stale: it still said `validate` reports a config naming one "that no installed package registers," which is exactly true for resolvers, probes, and writers but incomplete for templates, which now have a second, path-based resolution route the other three don't.

Fix: qualified that one clause for templates — "templates are the one registry where that's not the whole check, since a name can also resolve against [the project's own `templates/`]; [§ Errors `validate` reports] states the row in full" — pointing at the row task 14 already wrote and at § Templates' own three-homes explanation (which I'd already extended in `075455e`), rather than restating either. The paragraph's "four registries, one mechanism" framing is untouched, and the very next paragraph's "no installed package registers `plate_wells`" claim (a resolver, entry-point-only in this build) is left alone since it's still exactly true and my edit doesn't touch it.

Verified: `git diff` shows a single-sentence change, no other lines moved. `uv run pytest -q` → 1684 passed, 2 xfailed (the new baseline after task 14 landed at `e9eaa71`), no trailing whitespace/tabs introduced, `ruff check` clean.
