# Tasks 8-11 report — the collision matrix, three-valued provenance, template version, plugin hint

**Status:** All four tasks implemented, tested, mutation-checked, and committed separately.

**Commits:**
- Task 8 — `0b5e909` — the template collision matrix over three sources, decided from metadata
- Task 9 — `6e223d4` — template provenance is three-valued at the merge, and an installed name is known but unloaded
- Task 10 — `78b6276` — a template reports its own version, and W-TEMPLATE-VERSION compares against it
- Task 11 — `69458c3` — an unresolved experiment_type names the plugin the config points at

**Test summary:** full suite green at each commit — 2013 / 2015 / 2017 / 2018 passed (+2 xfailed
throughout), i.e. predecessor's 2006 +7, +2, +2, +1 exactly as each brief predicted. `ruff check`,
`ruff format --check`, `mypy` clean at every commit.

## `installed` reachability at the two class-taking readers

**Unreachable at both**, as the spec and briefs said it would be. `validate._check_versions` and
`materialize.materialize_config` both call `is_local_template(type(template))` on a class already
in hand; no installed claim ever carries a class in Part A (`Claim.cls` is `None` for `provenance ==
"installed"`), so neither reader's local/non-local branch ever sees the third value. Confirmed by
construction, not merely asserted: task 9's mutation (b) (answering `template_provenance` from a
two-valued predicate) only reddens `template_provenance` itself, and no fixture in this batch can
feed a class-taking reader an installed claim.

## `E-TEMPLATE-INSTALLED-UNSUPPORTED`'s filing

`docs/superpowers/spec-defects.md`, new entry `## OPEN — an installed template's name resolves but
its class is never loaded`, **owner: unassigned** — exactly as task 9's brief specified. Retiring it
needs `Claim.cls` populated for an installed claim, `is_local_template`'s two callers reading
`Claim.provenance` instead, and `provenance.plugin_versions`; none of that is H7b Part B's nine
tasks (the resolver half), so no slice currently owns it.

## Mutation results (all reverted by hand-editing the file back, never `git checkout --`; `__pycache__` cleared before each rerun)

**Task 8 — `_claims`/`_check_plugin_collisions`, four prescribed:**
- (a) drop the entry-point loop → all 4 named tests FAIL. Confirmed.
- (b) `for name in sorted(claims)` → `for name in claims` — **the brief's own fixture did not
  discriminate.** `test_the_colliding_template_name_reported_is_the_first_in_name_order` passed
  under both the correct implementation and this mutant, because its three colliding names all come
  from `scan_group`, which already returns its group pre-sorted by name — so an unsorted walk over an
  entry-point-only claim set coincides with a sorted one by construction, no matter which claim
  happens to be scanned "first". Verified empirically both ways before concluding this, not just by
  inspection. **Fixed** by strengthening the test: added a fourth collision that shadows core's own
  `generic` (via a local `templates/mine.py`), which is *always* the first key `_claims` inserts
  (from `_BUILTIN`, before any entry point is scanned) regardless of its alphabetical rank. With that
  mixed-source collision in the fixture, the correct implementation now provably picks `a_one` (`a` <
  `g`) while the mutant picks `generic` (inserted first, never sorted) — verified both directions with
  a standalone reproduction before touching the shipped test. This is exactly the "prescribed mutation
  turned out blind" shape `CLAUDE.md` warns about, and it would have shipped a non-discriminating test
  had it not been checked against the mutant before trusting it.
- (c) name one claimant instead of all → the 2 named tests FAIL (plus the pre-existing shadow test,
  as the brief anticipated). Confirmed.
- (d) `.load()` the entry point → `ModuleNotFoundError`, not an `AssertionError`, exactly as
  prescribed (pins decision 3). Confirmed.

**Task 9 — provenance, two prescribed**, both confirmed exactly as predicted (mutant (a) collapses
the installed branch, fails on the "not in found" half; mutant (b) answers from a two-valued
predicate, fails on the `"installed"` assertion since the fixture needs all three values to
discriminate).

**Task 10 — version, two prescribed:**
- (a) compare against the module constant again — **failure mode differed from the brief's
  prediction, because the brief's own test fixture was buggy.** The test declared
  `template_version: "1.0.0"` in the config while asserting `TEMPLATE_VERSION not in message` —
  but `TEMPLATE_VERSION == "1.0.0"`, so that value is printed regardless (as the *declared* field,
  not the *reported* one) even under the correct, un-mutated implementation. Caught before trusting
  the test: ran it green under the correct code first, then noticed the assertion was checking a
  string that appears in the message by construction of the fixture, not by the bug it claims to
  guard. Fixed by declaring `"2.0.0"` instead, which is used nowhere else, so `TEMPLATE_VERSION not
  in message` is a real property again. Under that fix, mutant (a) fails with an `AssertionError` on
  `"9.9.9" in message` (not the brief's predicted `StopIteration`) because with `declared="2.0.0"`
  the mutant's `reported = TEMPLATE_VERSION = "1.0.0"` differs from `declared`, so the early return
  doesn't fire and a message is built — just the wrong one. Confirmed FAIL, correctly discriminating.
- (b) drop the `reported is None` guard → nothing reddens, exactly as the brief said (defensive,
  unpinned; the task that first populates `Claim.cls` for an installed claim is what reaches it).
  Confirmed and not kept.

**Task 11 — plugin hint, one prescribed (mutation (b) explicitly not run, per brief):**
- (a) render the hint unconditionally → FAILS on the control half exactly as prescribed
  (`"`plugin` says" in plain` when the mutant prints "come from `None`"`). Confirmed.

## Where a brief or the spec disagreed with the code

1. **Task 8's own prescribed test fixture for the write_config override syntax was wrong.** The
   brief's `test_two_installed_distributions_claiming_one_resolver_name_are_reported` used
   `write_config({"data.units.from": {"resolver": "plate_wells"}})`, but the `write_config` fixture's
   dotted-override walk requires every intermediate key to already exist in `base_config` — `data`
   has no `units` key by default, so this raises `KeyError: 'units'` in the fixture itself rather than
   producing the intended config. Reproduced the `KeyError` standalone before changing anything.
   Fixed to `write_config({"data.units": {"from": {"resolver": "plate_wells"}, "key": "well"}})`,
   matching the convention every other `data.units`-touching test in the file already uses.

2. **Task 8's reference.md instruction to "leave the rest of the row as it stands" was inconsistent
   with its own new opening clause.** The pre-existing `E-TEMPLATE-COLLISION` row (§ Errors validate
   reports) carried a sentence — "An installed distribution claiming one of these names is the same
   fault and is not yet checked here: no entry point is resolved..." — that directly contradicts the
   new opening clause the same step installs (which already lists all five collision shapes,
   including two installed-distribution cases, as checked). Removed that now-false sentence rather
   than leaving it, since keeping it would have shipped a self-contradicting row in the same edit.

3. **Task 9's own prescribed code for the `if template is None:` branch reintroduces the exact
   double-discovery bug its surrounding comment argues against.** The brief's snippet calls
   `_claims(repo_root).get(name)` inside that branch, *in addition to* the `resolve_template(name,
   repo_root)` call already made earlier in `validate_config` (which itself calls `_claims` once) —
   two full local-discovery passes per call whenever the template is unresolved. This is precisely
   what `resolve_template`'s own docstring, and the comment the brief supplies for the new code, argue
   must never happen. Caught immediately by two failing pre-existing regression tests pinned exactly
   on this property: `test_one_validate_discovers_local_templates_once_on_the_unknown_name_path`
   (asserts a discovery call count of 1) and `test_a_template_whose_import_is_not_idempotent_survives_
   an_unknown_name` (a template whose second import raises, proving a second discovery would crash).
   Fixed by replacing the earlier `resolve_template(name, repo_root)` call with a single
   `claims = _claims(repo_root)` call, deriving `template`, `known`, and `claim` all from that one
   merge — restoring the true "one merge per `validate_config` call" invariant the brief's own prose
   states but its code did not implement.

4. **A pre-existing test's monkeypatch was aimed at a name `validate.py` no longer imports.**
   `test_a_template_cross_field_rule_is_reported` patched `validate_mod.resolve_template` to inject a
   stub template; removing that import (per the fix above) silently defused the patch — exactly the
   "monkeypatch left aimed at a name the code no longer calls" trap `CLAUDE.md` names. Fixed by
   rerouting the patch to `validate_mod._claims`, returning a one-entry `Claim` dict instead.

None of these four are scored as findings against the *implementation* — they are corrections to the
briefs' own prescribed text (a fixture syntax error, a stale doc sentence the brief's own edit made
false, a double-discovery bug in prescribed code, and the monkeypatch fallout from fixing it) — each
verified by reproducing the failure first, then fixing, then re-confirming green.

## Concerns / residuals carried forward (as each brief already flags)

- Task 8: `_check_plugin_collisions`'s `"plugin"` reporting path is unpinned by any test; `Claim.
  provider` for core's own claimant is pinned only via the pre-existing shadow test;
  `partial_templates`'s expression is still a proxy (`claims.values()` vs. the narrower `local.
  values()`) until `Claim.cls` can ever be non-`None` for an installed claim — task 20's to close.
- Task 9: `installed` unreachable at `_check_versions`/`materialize_config`, filed with owner
  unassigned as detailed above.
- Task 10: `materialize`'s use of `type(template).version` is not independently pinned from
  `TEMPLATE_VERSION` (since `generic.version == TEMPLATE_VERSION`), as the brief already states.
- Task 11: the `generate experiment` emit site's *absence* of a hint is untested (only the code
  itself is), and the `isinstance` guard on a non-string `plugin` is pinned by nothing — both flagged
  by the brief and left as is.

**Sequencing followed:** 8 → 9 → 10 → 11, `_merged`/`_claims` re-read fresh between each rather than
worked from a stale copy, as instructed.
