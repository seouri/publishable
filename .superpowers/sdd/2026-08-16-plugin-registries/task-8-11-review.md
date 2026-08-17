# Tasks 8-11 review — collision matrix, three-valued provenance, template version, plugin hint

Reviewed at `5618c7a`, against `c909080..5618c7a`, per-commit (`0b5e909`, `6e223d4`, `78b6276`,
`69458c3`) rather than from the combined diff. Baseline re-established before the first mutation:
**2018 passed, 2 xfailed**; `ruff check`, `ruff format --check`, `mypy` all clean at HEAD.

**Disposition: C1 blocks.** It ships a normative `reference.md` row that is false of one of the two
surfaces the row itself claims to govern, and a diagnostic that contradicts itself inside a single
string. I1 and I2 do not block but should be closed in this slice — both have a discriminating
fixture already present in the suite, named below. M1-M4 do not block.

Every mutation below was applied by editing the file, run with `__pycache__` cleared, and reverted by
editing back — never `git checkout --`. Each revert was verified by `diff` against a pre-mutation
copy (`REVERT CLEAN` in all four cases) and the suite re-run to 2018/2.

---

## Verdicts

| Task | (a) a check that could not fail | (b) a comment/docstring claiming a guarantee the code does not provide |
|---|---|---|
| 8 | **FAIL** — I1 | **PASS**, with M1 |
| 9 | **PASS** for the two tests it added — both discriminate; the untested second emit site is scored under (b) as C1, not here | **FAIL** — C1 |
| 10 | **FAIL** — I2 | **PASS**, with M2 |
| 11 | **PASS**, with M3 | **PASS** |

---

## C1 — Critical — task 9 — `E-TEMPLATE-UNKNOWN`'s **second** emit site is now false, and its message contradicts itself

Spec correction 1 is explicit: for an installed-only name, `E-TEMPLATE-UNKNOWN` "would be **false**".
Task 9 closed that at `validate.validate_config`. It did not close it at the **other** emit site.
`generators/experiment.py:54-59` still does `resolve_template(...) → None → raise
ContractError(unknown_template_message(...), code="E-TEMPLATE-UNKNOWN")`, and after task 8
`resolve_template` returns `None` for an installed-only name while its `known` list now **contains
that very name**.

Verified empirically, not by reading — a throwaway test calling `generate_experiment` against a
`git_repo` plus `installed("dist-one", "1.0", {"publishable.templates": {"vendor_assay": ...}})`:

```
CODE: E-TEMPLATE-UNKNOWN
MESSAGE: names `vendor_assay`, which no template — core's, an installed plugin's, or this
         project's own `templates/` — registers (known: generic, vendor_assay)
```

Three things are wrong at once and they compound:

1. The **code** is the one spec correction 1 says is false there.
2. The **message** asserts "an installed plugin's … registers" nothing, then prints the name in its
   own `known:` list — a single string contradicting itself.
3. `docs/reference.md` § Errors `validate` reports, the `E-TEMPLATE-UNKNOWN` row **rewritten by task
   11**, states the condition as "names a template that neither core, nor any installed
   distribution's `publishable.templates` entry points, nor this project's own `templates/`
   registers" and says **"this row governs both"** surfaces. The row is now false of one of the two
   surfaces it claims to govern.

This is precisely the misreading `CLAUDE.md` records for this exact code: *"`E-TEMPLATE-UNKNOWN` had
two emit sites; a task scoped by a single call site missed the second … § Errors carries one row per
code, not per emit site, so a diagnostic's unit of work is every site that raises or reports it."*
The regression was created jointly — task 8 put installed names into `known`, task 9 fixed one site —
but task 9 is the task that minted the distinction and fixed one of two sites, so the **code** half is
scored against it. The **doc** half is task 11's: `69458c3` is the commit that rewrote the
`E-TEMPLATE-UNKNOWN` row into "this row governs both", replacing the row's previously-true "not yet
checked" sentence with a claim that is false at the `generate` surface.

It was reachable **before** this batch only in the sense that no installed name existed; task 8 made
it reachable and no test in the batch exercises `generate experiment` against an installed name at
all. The report's own residual list concedes only that "the `generate experiment` emit site's
*absence* of a hint is untested" — the untested thing is larger than the hint.

**Route:** either `generate_experiment` reads the claim's provenance and raises
`E-TEMPLATE-INSTALLED-UNSUPPORTED` too, or the shared message stops claiming the installed set was
searched. Whichever is chosen, the reference.md row must stop saying it governs both surfaces
identically, and a test must exercise the second site.

---

## I1 — Important — task 8 — provider order in `E-TEMPLATE-COLLISION` is pinned by nothing

`registry._claims` builds the claimant list as
`" and ".join(sorted(claim.provider for claim in claims[name]))`. The design's own trap table says
*"Providers are named in the message; the order must be the name's, not the order the scan happened
to walk"*, and task 7's review found this identical trap one level down.

**Mutation:** `sorted(...)` → `list(...)[::-1]` (a genuine reordering, since the local claim is
appended after the entry-point claims and core's before them, so reversal changes the string).
**Result: full suite green — 2018 passed, 2 xfailed.**

The four new collision tests assert provider **membership** only (`"dist-one 1.0" in message`,
`"dist-two 2.0" in message`, `f"{path}::LocalAssay" in message`). Not one asserts an order, so the
`sorted` call is decorative as far as the suite can tell. The report's own repair (§ mutation (b))
separated *name* order from *insertion* order — which I re-verified is genuinely discriminating,
`generic` being `_BUILTIN`'s first insertion and sorting after `a_one` — but it says nothing about
claimant order **inside** a message, which is the half task 7's review flagged.

The same shape holds in `validate._check_plugin_collisions`, whose `sorted(provider_of(ep) …)` is
additionally a **no-op** (`scan_group` already returns each key's list sorted by `provider_of`).
Mutation: reverse it → the two `E-PLUGIN-COLLISION` tests still pass.

**The discriminating fixture already exists**: `test_a_local_template_may_not_shadow_an_installed_one`
has a local claimant (a `/…/templates/mine.py::LocalAssay` path) appended *after* an installed one
(`dist-one 1.0`), so insertion order and sorted order genuinely differ. One
`assert message.index(...) < message.index(...)` closes it.

---

## I2 — Important — task 10 — the `materialize` reader is unpinned; only `_check_versions` is tested

Task 10's claim is that a template reports **its own** version rather than core's module constant, at
**two** readers: `validate._check_versions` and `materialize.materialize_config`. The first is pinned
by the (repaired) `Versioned`/`9.9.9` test. The second is not.

**Mutation:** `materialize.py:104`, `reported = None if local else type(template).version` →
`reported = None if local else TEMPLATE_VERSION`. **Result: full suite green — 2018 passed, 2
xfailed.**

That single mutation reverts the whole materialize half of the task — both the header
`# Generated by … v{reported}` line and the `template_version: "…"` line — and also erases the new
`reported is None` behaviour (a non-local template reporting no version now writes no
`template_version` at all, which nothing exercises either).

The report discloses this as a residual quoting the brief ("`generic.version == TEMPLATE_VERSION`,
so not independently pinned"), but **the fixture obstacle it implies does not exist**:
`materialize_config` takes a template *instance* as a parameter, exactly as `_check_versions` does,
so the same `class Versioned(BaseTemplate): version = "9.9.9"` that pins the first reader pins the
second in one call. A disclosed residual with a cheap fixture is still a check that could not fail —
`CLAUDE.md`'s "testing the refusal, never the honouring".

---

## M1 — Minor — task 8 — the templates skip in `_check_plugin_collisions` is dead by construction

`for group in GROUPS: if group == "publishable.templates": continue`. A duplicated
`publishable.templates` key raises `E-TEMPLATE-COLLISION` inside `_claims`, and `validate_config`
returns from its `except ContractError` block **before** `_check_plugin_collisions` is ever called —
so the loop can never see a colliding template key whether or not the guard is there.

**Mutation:** `if group == "publishable.templates":` → `if False:`. **Full suite green.**

The docstring's opening ("Templates are not here: … so its verdict is reached at the merge") states a
true *reason* and does not overclaim, which is why this is Minor rather than a (b) failure. But it
reads as a live guard, and the branch is unreachable. Either drop it and say why templates need no
skip, or say in the docstring that the guard is belt-and-braces against a future caller that runs
this before the merge.

## M2 — Minor — task 10 — two unused fixtures, and one trivially-true assertion

`test_the_version_warning_names_what_the_template_reports_not_a_core_constant(tmp_path, git_repo)`
uses neither parameter; `git_repo` shells out to `git init`/`add`/`commit` for nothing. Separately,
`assert get_template("generic").version == TEMPLATE_VERSION` is true by the literal
`version = TEMPLATE_VERSION` assignment in `generic.py` — it pins that the assignment exists, which
is worth having, but it can never distinguish "the class reports" from "the constant is read".

The **repair the report claims for the `"1.0.0"` → `"2.0.0"` fixture is real and I verified the
mechanism**: with `declared="2.0.0"`, `reported="9.9.9"`, `TEMPLATE_VERSION="1.0.0"`, the message is
`is 2.0.0 but the template reports 9.9.9`, so `TEMPLATE_VERSION not in message` is a genuine
property; under mutant (a) the message becomes `is 2.0.0 but the template reports 1.0.0` and the
assertion fails. Under the brief's original `"1.0.0"`, the declared value alone put `TEMPLATE_VERSION`
into the message and the assertion was unsatisfiable regardless of the fix. Good catch, correctly
repaired.

## M3 — Minor — task 11 — the `isinstance` guard and the `generate` no-hint path are unpinned

`plugin if isinstance(plugin, str) and plugin else None` — no config in the suite declares a
non-string `plugin` alongside an unresolved `experiment_type`, so the guard could be deleted
undetected (a `plugin: 123` would then render "should come from `123`"). Flagged by the brief and
left; recorded here so it is not lost.

`generate_experiment`'s `plugin=None` is untested but **true by construction** — `None` is the
parameter's default, so passing it explicitly is documentation rather than behaviour, and no mutation
of that argument can differ from deleting it. That half is correct as written; it is C1, not the
hint, that the `generate` site actually gets wrong.

## M4 — Minor — task 9 — `known:` now lists names `validate` would itself refuse

`known = sorted(claims)` includes installed-only names, so a genuinely unknown name is answered with
`(known: generic, vendor_assay)` where `vendor_assay` is a name that, if written, draws
`E-TEMPLATE-INSTALLED-UNSUPPORTED`. Defensible — the name *is* known, which is task 9's whole point —
but a reader following the list hits a second refusal. Worth one clause in the message or a
reference.md sentence.

---

## Answers to the six directed checks

**1. The no-import invariant — held.** Enumerated by reading, then confirmed by grep. `plugins.py`
imports only `EntryPoint, entry_points` from `importlib.metadata`. `provider_of` touches `ep.dist`
(a metadata object) and `ep.value` (the unparsed target string) — neither imports the target.
`templates/registry.py` calls `scan_group`/`provider_of` and constructs `Claim(cls=None)` for every
entry-point claim; `validate._check_plugin_collisions` calls `scan_group`/`provider_of` and nothing
else. Whole-`src/` grep for `.load()` / `import_module` / `__import__` / `importlib` returns only:
`plugins.py`'s docstring prose, `base_experiment.py` (the entrypoint import, pre-existing),
`cli.py` (`importlib.metadata.version`), and `templates/discovery.py` (`importlib.util`, the
*project-local* path load, which is by design). **Nothing in these four tasks reaches for the object
behind an entry-point name.**

One caveat worth recording. The positive assertion lives at one level only —
`test_the_scan_imports_nothing` (task 7) pins `scan_group` with a target module that genuinely
imports and asserts `sys.modules` absence. **No test asserts it at the `_claims`/`get_template`
level**, where tasks 8-9 put the new callers. There, the guarantee is pinned only by the fixtures'
targets being unimportable (`no_one:T`), which is why mutation (d) surfaced as `ModuleNotFoundError`
rather than an assertion failure — the same shape task 7's own docstring warns about. If a later task
(13, 15) makes a fixture distribution's module importable, a `.load()` added inside `_claims` would
go unnoticed. Cheap fix: one `sys.modules` assertion around a `get_template` call on an installed
claim whose module exists.

**2. `E-TEMPLATE-INSTALLED-UNSUPPORTED` is honest at `validate`, and only there.** It fires under
`template is None and claim is not None and claim.provenance == "installed"` — and by construction
that is exactly "the name has claims, all of them installed", since a name with a second claimant
raises `E-TEMPLATE-COLLISION` in `_claims` and never reaches the branch, and `provenance == "core"` /
`"local"` always carry a class. It has **no § Errors row**: its only reference.md appearance is the
prose sentence in § The one config file naming the `-UNSUPPORTED` family, which is where that family
belongs. Its `spec-defects.md` filing states **Owner: unassigned** twice and gives an accurate reason
(retiring it needs `Claim.cls` populated, `is_local_template`'s two callers reading provenance, and
`provenance.plugin_versions` — none of which is Part B's resolver half). Row 212's amendment rather
than strike is also correct. **The failure is at the other emit site — C1.**

**3. The collision matrix — two distributions present, name order repaired, provider order not.**
The `installed` fixture writes real `.dist-info` directories onto `sys.path`, one per call, and the
matrix fixtures use two. The name-order repair is genuine: `generic` is `_BUILTIN`'s first insertion
and sorts *after* `a_one`, so sorted-by-name and first-inserted give different answers, and the test
asserts `a_one` present with `generic`/`m_two`/`z_three` absent — which also rules out reverse-sorted
(`z_three`). That separates all three orderings. The **provider** order inside the message is the
half the repair did not reach — I1.

**4. The single-merge repair — all three halves verified.**
- *One merge per `validate_config`.* Mutation: re-add `claim = _claims(repo_root).get(name)` inside
  the `if template is None:` branch. **Both** pinned regressions fail —
  `test_one_validate_discovers_local_templates_once_on_the_unknown_name_path` and
  `test_a_template_whose_import_is_not_idempotent_survives_an_unknown_name`, the latter with the
  `PartialLoadError: … RuntimeError('this template was imported twice in one process')` that proves a
  second import destroys every finding. 2 failed / 2016 passed. Both still pin it.
- *The rerouted monkeypatch still reaches the behaviour.* Mutation: `for message in
  template.validate(doc):` → `for message in []:`. `test_a_template_cross_field_rule_is_reported`
  fails. The reroute to `validate_mod._claims` returning `{"generic": Claim(..., cls=RuleBreaker)}`
  is live, not defused.
- *No monkeypatch left aimed at a moved name.* Swept `tests/` by file list (not by filtering grep
  output) for `monkeypatch.setattr` lines naming `resolve_template`, `_merged`, `template_names`,
  `get_template`, `is_local_template`, `_claims`, `unknown_template_message`, `TEMPLATE_VERSION`,
  `scan_group`, `entry_points`, `provider_of`. **Exactly one hit — the rerouted one.** Nothing else
  patches a name these four moved.

**5. Task 10's fixture coincidence — repaired, and the shape does not recur.** See M2. I checked the
other three tasks' fixtures for a value coinciding with a constant: task 8's `dist-one 1.0` /
`dist-two 2.0` do not collide with anything asserted (and no order is asserted anyway); task 9's
`Claim(provenance="core", provider="stub")` stub is inert; task 11's `"generic"` assertion is the
known-list, intentionally.

**6. `is_local_template` kept and `installed` unreachable — verified by construction.** Not taken on
the report's word: `Claim(provenance="installed", provider=…, cls=None)` is the single construction
site for an installed claim and it hard-codes `cls=None`. Every class-taking path descends from
`claim.cls` — `_merged` filters `if claim.cls is not None`, `resolve_template`/`get_template` return
`claim.cls()` or `None`, and `validate_config` binds `template = claim.cls() …`. So the two
class-taking readers (`validate._check_versions`, `materialize.materialize_config`) can only ever be
handed a core or local class. `is_local_template` is untouched in the diff. Correct per spec
correction 3.

**7. `E-DATA-RESOLVER-UNSUPPORTED` stays alive and is asserted alongside.** Still emitted at
`validate.py:3839`. `test_two_installed_distributions_claiming_one_resolver_name_are_reported`
asserts `"E-PLUGIN-COLLISION" in both` **and** `"E-DATA-RESOLVER-UNSUPPORTED" in both` for the
resolver-declaring config — the decision-7 form, retired by deleting one line. No assertion in these
four tasks compares against a **total** code set (`codes(...)` is used only with `in` / `not in`, and
`messages_by_code(...)` only by key lookup), so Part B's retirement stays a deletion rather than a
rewrite.

---

## What none of the run mutations reaches

- `_check_versions`' `reported is None` guard — genuinely unreachable in Part A (no non-local
  template with `version = None` is ever handed to it), and disclosed as such.
- `generate experiment`'s `plugin=None` — a no-op against the parameter default; no mutation can
  distinguish it from deletion (the real defect at that site is C1).
- The `isinstance(plugin, str)` guard — M3.
- `Claim.provider` for **core's** claimant beyond the one pre-existing shadow test.
- `partial_templates`' widening from `local.values()` to every claim (it now includes core's
  `GenericTemplate`): behaviour-neutral today because `GenericTemplate.required_env == []`, and it
  widens rather than narrows the redaction set, so it is safe — but it is unpinned, and task 20 owns
  the expression.
- The no-import guarantee at the `_claims`/`get_template` level — see check 1's caveat.
