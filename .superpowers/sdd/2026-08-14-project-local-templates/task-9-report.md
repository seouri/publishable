# Task 9 report — `generate template` (task 11 absorbed)

**Status:** complete. Commit `358aad4`. `1676 passed + 2 xfailed`; ruff and mypy clean; `ruff format` not run.

## What landed, in one commit

| Part | Where |
|---|---|
| The generator | `src/publishable/generators/template.py` (new) — `TEMPLATE_PY`, `class_name`, `is_usable_name`, `generate_template` |
| The routing | `cli.py` `_dispatch_generate`, a `template` branch ahead of the `NOT_BUILT_GENERATORS` check |
| The constant | `template` removed from `cli.NOT_BUILT_GENERATORS`, **and its comment's count** ("materializes two" → three), four lines above the edit |
| § Generators' row | status `built`; the Creates cell now names the refusal and the name rule, and marks the README half unbuilt |
| § Operation commands' `generate` row | the inline `` `template` (NOT BUILT) `` spelling dropped |

Five parts, then, counting the comment — which is the tasks-7/8 failure shape and was sitting inside the diff's own file.

## Decisions

**`E-TEMPLATE-EXISTS`, and no documented row.** I checked before minting: `E-EXPERIMENT-EXISTS` appears nowhere in `reference.md`, and `E-STEP-EXISTS` appears only in § Exit codes' prose as the *example* of "a creation command refusing to overwrite an existing file … exits 1". Generator-time exists-codes are therefore outside both § Errors tables by precedent, so this commit adds no row. The refusal does exit 1, matching that sentence.

**The README clause was not left standing.** § Generators promised "Its parameter table is added to the README" while the code never touches the README. A row marked `built` asserting that would be a false build fact, so the clause is now "Adding its parameter table to the README is NOT BUILT: the scaffolded README carries no managed region for one." No region was invented; task 15 still owns the gap (and the same defect sits, untouched, in the `experiment` row, which claims "a row in the README's managed experiments table"). The parser constraint is respected: the exact substring `` `template` (NOT BUILT) `` no longer occurs anywhere in the document, while `` `report` (NOT BUILT) `` survives.

**Name and arity are invocation errors (exit 2), not new codes.** Exactly one positional; the name must be `str.isidentifier()` and not `__`-prefixed. Both checks precede any disk write — the CLI-table test invokes every *built* generator as `generate template _probe_a _probe_b` with cwd = this repository and asserts no exit code, so a write-first generator scaffolds `templates/_probe_a.py` into the working tree, where every later `discover_local` in the session reads it. A test asserts the templates directory listing is unchanged across all wrong invocations.

## The dimension the tests can see

A file-existence check cannot see identity — this slice has shipped seven checks that could not fail, two of exactly that shape. So:

- the round trip goes through `get_template("my_assay", root)`, and asserts the class name, that it is not the class `get_template("generic", root)` returns, and the stub's one `Param` (`my_assay.threshold`, default `0.5`) as an exact key set. A merge handing back `GenericTemplate`, or a stub registering a bare `BaseTemplate` with an empty spec, both die;
- **a second name, `plate_wells`, generated in its own project** — because with one example everywhere, nothing distinguished a derivation from a hard-coded `my_assay`, which is this slice's signature defect and would have been its eighth instance. Two segments on purpose: a `class_name` that capitalized the whole string reads `Plate_wellsTemplate` and dies. `get_template("my_assay", other) is None` reads the same assertion the other way and covers cross-registration between the two projects;
- a second test runs `generate_experiment --template my_assay` and asserts the materialized `parameters` is `{"my_assay": {"threshold": 0.5}}` — the stub is *usable*, not merely importable, which the round trip alone cannot show (a dotted path `materialize_config` or `validate` rejected would still register);
- the dead-four test's control is a first loop asserting all five live names are present, so a stub emitting nothing does not pass by absence;
- the refusal test asserts the pre-existing file's whole text, so a generator that printed the refusal and wrote anyway fails.

## Mutations (applied in place, `__pycache__` deleted, reverted by edit, never `git checkout`)

| Mutation | Result |
|---|---|
| `if path.exists()` → `if False` (overwrite) | `test_generate_template_refuses_an_existing_file` FAILED; PASS after revert |
| stub emits `apparatus_probe = None` | `test_the_generated_stub_declares_only_the_live_members` FAILED; PASS after revert |
| doc row → `NOT BUILT`, constant untouched | **both** binding tests FAILED (`..._are_parsed_at_all` on set equality, `..._match_what_the_cli_does[Generator]` because the built branch answers instead of the diagnostic) |
| the reverse — `template` back in the constant, doc `built` | `..._are_parsed_at_all` FAILED on set equality; the behavioural test passes, because the new branch shadows the constant. That asymmetry is the atomicity argument in one line |
| `@register_template("{name}")` → `@register_template("my_assay")` (hard-code the derivation) | round-trip test FAILED on the second name; PASS after revert. Before the second name was added, this mutation passed everything — the check was about the name, not the derivation |
| `class_name` → `name.capitalize() + "Template"` | round-trip test FAILED (`Plate_wellsTemplate`); PASS after revert |

## Concerns

1. **Atomicity: yes, and sharper than "the constant".** The branch sits *ahead* of the `NOT_BUILT_GENERATORS` check, so implementing without editing the constant does not merely leave a stale marker — it makes the marked row stop producing its diagnostic, failing the behavioural test. The fourth mutation above shows the constant alone cannot hold the line. The doc-only direction fails the other test. So the three edits and the implementation are genuinely one atom; the plan's task 11 named three of four.
2. **On the stub's contents, one disagreement worth recording.** The five-not-nine rule is right for `apparatus_probe`/`apparatus_facts`/`field_convention`, but `required_env` is a near-miss: `Param(requires_env=...)` *is* live, and a reader who wants a template-wide credential has no signpost in the stub. I emitted the five as instructed; if `required_env` ever gains a reader, the stub is where it should reappear.
3. **The stub's `parameter_spec` key is derived from the template name** (`my_assay.threshold`). That is a deliberate fingerprint for the identity assertion as well as a sensible default; a reviewer preferring a neutral prefix should know the round-trip test asserts the exact key.
4. **`isidentifier()` admits `True`, `None`, `on`, `off`.** A template named `on` gives a config whose `parameters` key round-trips through YAML 1.1 as a boolean. Seen, not guarded: a stricter pattern would be policy this spec does not state, and the failure is loud and immediate rather than silent.
5. **Not fixed, deliberately:** § Generators' `experiment` row still claims it "adds a row to the README's managed experiments table", which `generate_experiment` does not do. Same defect class as the one I marked on the `template` row, but it belongs to task 15's record rather than to this diff. — *Superseded by review round 1; see below.*

---

## Review round 1 (amended into the same commit)

Both required clauses taken, all three offered strengthenings taken.

**1 — the neighbouring row.** Marking the `template` row's README half while leaving the `experiment` row's identical claim unmarked made the neighbour read as *affirmatively true*, which is a new false signal rather than an inherited one. The `experiment` row's Creates cell now ends "Adding a row to the README's managed experiments table is NOT BUILT — the same half `generate template` does not write either". No region invented, § The generated README untouched; task 15 still owns both. The first draft of that clause said "for `template` below" — a phrase locating a table row by position, which the standing rule forbids — and it was rewritten to name the command instead.

**2 — the `__` clause.** The prose stated two facts where the code ANDs two conditions. Now: "takes a name `templates/<name>.py` can be imported under **and not one prefixed with `__`**, which discovery skips".

**3 — the dead-members test now checks two dimensions, because neither sees the other's failure.** An `ast` parse of the class body pins the declared set *exactly*; the text check that the four dead names appear nowhere is kept beside it. The reviewer's stated failure mode is the one an `ast` parse **cannot** see: comments are not in the tree, so a commented-out `apparatus_probe` is invisible to a parse and visible only to the text check. What the parse adds is the other half — a substring check cannot tell a declaration from a mention, so it accepts a member renamed or demoted to prose. Both proved by mutation:

| Mutation | Result |
|---|---|
| stub emits `# apparatus_probe = None` (commented out) | FAILED on the text loop — the dimension the `ast` parse is blind to |
| `parameter_spec` → `parameter_spec_typo` | FAILED on the declared-set equality, while `"parameter_spec" in text` still held — the dimension the text loop is blind to |

**4 — the zero-positional case now asserts its stderr** exactly, like every other invocation case, instead of discarding it.

**5 — the refusal test now asserts the message names `templates/my_assay.py`**, not only the code: a refusal saying "already exists" and nothing else would have passed.

Suite after the amendments: `1676 passed + 2 xfailed`, ruff and mypy clean. Every mutation above was applied in place and reverted in place; no `git checkout`, and `__pycache__` deleted around each.

**Accepted without re-argument:** `E-TEMPLATE-EXISTS`'s missing durable record and the `required_env` reader in § The generated README both route to task 15. The second is the better justification for my concern 2 than the one I gave — the member has a *specified* reader, itself unbuilt, which is the same defect shape as the parameter-table clause one row away.
