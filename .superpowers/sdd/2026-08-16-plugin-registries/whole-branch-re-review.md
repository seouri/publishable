# H7b Part A — whole-branch **re-review** (scoped to the fix round)

Re-reviewed `h7b-registries` at `381060a` on 2026-08-17, against the findings in
`whole-branch-review.md` (written at `88688e1`). Scope: **whether those findings were closed, and
whether closing them introduced anything new.** The whole-branch review was not repeated.

Gates re-run at HEAD, in the foreground: **2060 passed, 1 skipped, 2 xfailed** (113.7 s);
`ruff check` clean; `ruff format --check` 78 files unchanged; `mypy` clean over 44 source files.

The fix round is one commit (`381060a`) touching 8 files. Its only **behavioural** changes are two
diagnostic message strings (`E-DATA-RESOLVER-UNSUPPORTED`, `W-TEMPLATE-VERSION`); everything else is
prose, docstrings, a spec-defects entry, and one new test.

**Verdict: READY TO MERGE.** C1 is closed and no surviving instance of its class exists. Three new
findings — **N1 Important**, **N2 Trivial**, **N3 Trivial** — are recorded below. None is a behaviour
defect and none holds the merge: N1 is a false justification clause in a docstring, self-falsified by
the same sentence's own list, and it is tiered and unblocked on exactly the whole-branch review's own
I2 precedent (a false docstring claim about callers, one clause to close, Important but not
blocking). It is worth fixing promptly because it is this slice's dominant defect shape, entering in
the commit whose job was closing three other instances of it.

Every mutation below was reverted **by restoring a pre-mutation copy of the file**, never by
`git checkout --`, and each revert was verified by re-running the affected tests to green.
`git diff --stat` is empty at the end of this review.

---

## The findings, one line each

| # | Status | Note |
|---|---|---|
| **C1** | **Closed** | The clause is deleted; the surrounding sentence reads correctly without it. Re-swept independently (below) — no surviving instance in the four documents, `spec-defects.md`, or `src/` |
| **I1** | **Closed** | The count is replaced by an enumeration that names all **six** codes, including `E-TEMPLATE-INSTALLED-UNSUPPORTED`, and by "every code above has passed". Verified against the code |
| **I2** | **Closed** | Both docstrings now state the absence and date it to `deaed2b`. The dated claim is **true at `deaed2b` and still true at HEAD** |
| **I3** | **Closed** | Message and comment now say *"a resolver cannot be dispatched in this build"*. Nothing in `tests/` pinned the old fragment. The new wording is true and stays true through all of Part A |
| **I4** | **Closed** | All six surfaces verified caller-free; owners are slices or unassigned; the group-generic / template-specific split is right. One Trivial defect in the entry's *stated verification* — see N2 |
| **M1** | **Closed, with N1** | `_claims`'s docstring now names its two cross-module importers and argues why it stays private — but the justification clause it adds is false. See **N1** |
| **M2** | **Closed** | `_dispatch_generate`'s new docstring accurately describes the accept-and-drop behaviour and the per-`kind` validation. Verified by reading all three branches |
| **M3** | **Closed** | `W-TEMPLATE-VERSION` now says "the template's default"; nothing pinned the old wording |
| **M4** | **Closed** | Filed as its own `## OPEN` entry with **Owner: H7b Part B**. Verified: `register_writer`/`register_reader` raise `ContractError` · `E-PLUGIN-COLLISION` at decoration, and `load_entry_point`'s `except Exception` would re-code it as `E-PLUGIN-LOAD` once anything loads a plugin |
| **M5** | **Closed, and the test is discriminating** | Mutation named and run — see below |
| **M6** | **Closed** | `apparatus.py`'s row is now `# per-condition facts, the change gate, `Apparatus` — not yet built`; `plugins.py`'s row holds the four registries. No row claims the probe registry twice. `Apparatus` in that row agrees with § The importable surface's `not yet built` row |

---

## 1. C1 — re-swept independently

Not by repeating the fix's grep list. Enumerated by **reading where the claim could live**, then
confirming by grep:

- § Creating a plugin, read end to end. The clause is gone; the collision paragraph, the
  entry-point-is-the-registration paragraph, and the two-things-register-without-an-entry-point
  paragraph carry no build-state marker.
- § Errors `validate` reports — every row mentioning `installed` (`E-PLUGIN-COLLISION`,
  `E-PROBE-UNKNOWN`, `E-RESOLVER-UNKNOWN`, `E-TEMPLATE-COLLISION`, `E-TEMPLATE-UNKNOWN`).
  `E-RESOLVER-UNKNOWN`'s **Not yet emitted** is correct — grep confirms **no emit site** in `src/`.
  `E-PROBE-UNKNOWN` carries no such marker and **does** have an emit site (`validate.py:976`).
- § Errors core raises — `E-TEMPLATE-COLLISION` and `E-PLUGIN-COLLISION` rows; both describe the
  complete three-source / four-group decision this branch built.
- § The one config file (lines 193, 195), § Validation's rows, § The importable surface, § Templates
  (three homes), § Package layout, § CLI reference's `Status` column, § Secrets & credentials.
- `README.md`, `design-principles.md`, `experimental-designs.md` — swept for every build-state idiom
  (`not yet built|not implemented|later slice|NOT BUILT|specified, not built|arrives with`). No
  plugin-registry build claim in any of the three.
- `src/` and `docs/superpowers/spec-defects.md`, swept for `only the local|not checked|no collision|
  arrives with entry-point|entry-point resolution`.

**Nothing false survives.** Two things worth stating rather than filing:

- `docs/feasibility-llm-growth-studies.md:956` still reads *"`E-DATA-RESOLVER-UNSUPPORTED` — the
  plugin registry is not implemented, so no resolver can be named"*. It sits inside
  § Executability on this build, **"Measured on 2026-08-15 against commit `2fdc957`"**, and a
  feasibility analysis is non-normative and exempt from the cross-document pass. A dated build fact
  going stale is the mechanism working, not a defect — this is exactly the section CLAUDE.md's
  procedure step 10 exists to create. **Not a finding.** Whoever writes the next measurement will
  re-derive it against the new message.
- § Validation's *Resolver is installed* row carries no unbuilt marker while its code
  (`E-RESOLVER-UNKNOWN`) is marked *Not yet emitted*. **Pre-existing** — byte-identical on `main`,
  untouched by this branch. Out of scope; noted so it is not re-discovered as new.

## 2. I3 — the message change, and what pinned the old one

- `grep -rn "plugin registry is not implemented|registry is not implemented|not implemented in this
  build"` over `src/`, `tests/` and `docs/` (excluding the development record): the only remaining
  hits are `E-STATS-NULLTEST-UNSUPPORTED`'s own unrelated string and `E-SWEEP-SAMPLE-BASELINE`'s
  § Errors row. **Nothing in `tests/` ever held the fragment** — all ten `E-DATA-RESOLVER-UNSUPPORTED`
  references in `tests/` assert on the *code*. Confirmed the fix's claim independently.
- **The new wording is true.** `RESOLVERS`, `register_resolver`, the `publishable.resolvers` group,
  and `_check_plugin_collisions` over it are all built; what is absent is dispatch —
  `load_entry_point` has no caller and `resolve_units` has no resolver arm. *"a resolver cannot be
  dispatched in this build"* is precisely the surviving fact.
- **It stays true through Part A.** Part A's 20 tasks are complete at HEAD and none of them dispatches;
  the design's *What it is not* assigns the dispatch to Part B, whose task 24 deletes this refusal.
  There is no remaining Part A task that could falsify the sentence.
- `validate.py:1257`'s `_check_units` docstring bullet — the other place naming this refusal — reads
  *"resolvers are plugin artifacts and already refused as `E-DATA-RESOLVER-UNSUPPORTED`;
  `resolve_units` cannot execute a resolver either"*. True, and it makes no registry claim.
- Nothing else in the four documents says the registry is unimplemented (§ 1 above).

## 3. I1 and I2 — the replacements

**I1.** Read `validate_config` end to end. Four `return None` sites (lines 501, 504, 572, 598); the
last is a two-armed branch, `E-TEMPLATE-INSTALLED-UNSUPPORTED` when `claim.provenance == "installed"`
and `E-TEMPLATE-UNKNOWN` otherwise, both falling through to one `return None`. **Six codes, and the
new sentence names six.** "the last two decided by the same branch and returning at the same site" is
exactly right, and the closing "fires only once **every code above** has passed" now holds — the
sixth code has no row, and the sentence no longer ties row count to return count. Two nits, neither
worth a change: the two arms are listed in the reverse of their source order (unobservable — they are
mutually exclusive, and the sentence says they share a site), and *"A plugin-side collision returns
early under a code already in that set"* is over-broad as a bare clause, corrected by its own colon
and by the next sentence.

**I2.** Both docstrings date to commit `deaed2b`, matching `reference.md`'s `E-PLUGIN-DECORATOR` and
`E-PLUGIN-LOAD` rows verbatim, which is why that commit rather than the fix commit — the docstrings
cite those rows' measurement rather than minting a second one. **The claim is true at `deaed2b`**:
`git grep -n "load_entry_point\|check_registration\|declared_names" deaed2b -- src/` returns only the
three definitions in `plugins.py` (plus `validate.py`'s unrelated local — see N2). **And still true at
HEAD.** A dated claim pinned to an ancestor commit and still true at the tip is the honest shape.

## 4. I4 — the extended filing

Six surfaces, each verified caller-free by reading rather than by one grep:

| Surface | Verified |
|---|---|
| `PROBES` | Defined at `plugins.py:97`, written by `register_probe`, read only by `_registry_for`'s table — which is itself reached only from `declared_names`, which has no caller |
| `RESOLVERS` | Same shape, `plugins.py:87` |
| `plugins.load_entry_point` | Definition only in `src/`; `tests/test_plugins.py` only |
| `plugins.check_registration` | Definition + module docstring in `src/`; `tests/test_plugins.py` only |
| `plugins.declared_names` | Definition only; `validate.py`'s four hits are a **local variable of the same name** in `_check_holdout`, not this function — no module imports it (`validate.py:20` imports `GROUPS`, `names`, `provider_of`, `scan_group` and nothing else) |
| `registry.template_provenance` | Definition + one docstring mention in `src/`; `tests/test_templates.py` only |

**Owners.** `PROBES` → H7d; `RESOLVERS`, `load_entry_point`, `check_registration`, `declared_names`
→ H7b Part B; `template_provenance` → unassigned, folded into
*`## OPEN — an installed template's name resolves but its class is never loaded`*. All are **slices**
or *unassigned*/*none; accepted* — **no owner is a task**. The new M4 entry's owner is **H7b Part B**,
also a slice.

**The split is right.** `load_entry_point`/`check_registration`/`declared_names` take a group and an
entry point and serve all five registries identically — nothing in their signatures or bodies is
template-specific — so their first caller is whichever slice first *dispatches* any group, and Part B
is the first such slice in the standing order (`H3d → H4b → H7b → the rest`, H7d later).
`template_provenance` is the odd one out for a real reason: it is not group-generic, and its gap is
not "nobody dispatches yet" but "no installed template's class is ever held", which is the entry it
was moved to. Correct on both halves.

## 5. M5 — the mutation

The test pins `_check_plugin_collisions`'s docstring argument that `publishable.templates` needs no
skip in its loop, because `validate_config` returns from the `_claims` `except ContractError` branch
first.

**Mutation:** hoist the `_check_plugin_collisions(c)` call from after template resolution
(`validate.py:636`) to immediately after `load_env(repo_root)` and before the `try: claims =
_claims(repo_root)` — i.e. exactly the "early return moves below this call" the docstring warns
about, expressed as moving the call above the return.

**Result:** `test_a_template_collision_reports_only_once_not_also_as_plugin_collision` **fails**
— `AssertionError: assert 'E-PLUGIN-COLLISION' not in {'E-PLUGIN-COLLISION', 'E-TEMPLATE-COLLISION'}`
— while `test_one_distribution_per_plugin_name_reports_nothing` still passes, so the mutation is not
merely breaking the fixture. Reverted from a pre-mutation copy; both tests green again and
`git diff --stat` empty.

The test is discriminating, and it is the *only* thing in the suite that is: every other
`_check_plugin_collisions` test uses `publishable.resolvers`, where the early return does not apply.

## 6. New findings

### N1 — `_claims`'s new docstring justifies its privacy with a clause its own sentence falsifies. **Important, does not block merge.**

Tiered on the whole-branch review's own I2 precedent: a false docstring claim about callers, closable
in one clause, is **Important** — C1 blocked because it was normative prose a *user* reads, and a
false justification a *maintainer* reads does not.

`src/publishable/templates/registry.py`, `_claims`'s docstring, added by this fix round for M1:

> Underscore-private to this module's own readers (`_merged`, `template_names`,
> `template_provenance`, `get_template`), and imported anyway by two callers outside it —
> `validate.py` and `generators/experiment.py` — because both need a `Claim`'s `provenance` to route
> between `E-TEMPLATE-INSTALLED-UNSUPPORTED` and `E-TEMPLATE-UNKNOWN`, **and no public reader here
> returns anything but a resolved class or a bare name.**

The bolded clause is **false**, and it is falsified by the list at the head of its own sentence:
`template_provenance(name, repo_root)` is a public reader in this module whose entire return value is
`claim.provenance` — `"core"`, `"local"`, `"installed"`, or `None`. A reader who takes the clause at
face value concludes the module offers no way to ask for provenance, when it offers exactly that, six
lines below.

**Why the clause is not merely imprecise.** The real reason both callers import `_claims` is stated
correctly at both call sites already, and it is a different reason: each needs the resolved **class**,
the **provenance**, the **known-name list**, *and* the `Claim` itself (which
`installed_template_message` takes) — all from **one** merge, because a second call re-imports every
`templates/*.py` and executes every user top level twice. `validate.py:530-536` says so ("One merge,
so one local discovery … Asking for any of them separately would import every `templates/*.py` a
second time"), and `generators/experiment.py:94-101` says so again. `template_provenance` could not
serve either caller — not because it withholds provenance, but because it costs a second merge and
returns a string where the caller needs a `Claim`.

**The same docstring's two enumerations, checked in the other direction.** One holds, one is loose:

- *"imported anyway by two callers outside it — `validate.py` and `generators/experiment.py`"* /
  *"the two cross-module imports are the whole set"* — **true.** `grep -rn "_claims" src/ tests/`
  returns exactly those two import sites outside `registry.py`. `tests/test_validate.py:4299`
  monkeypatches `validate_mod._claims`, which is validate's own imported binding rather than a third
  import of the registry symbol, so the clause survives it.
- *"this module's own readers (`_merged`, `template_names`, `template_provenance`, `get_template`)"*
  — **loose.** `get_template` reads `_merged`, not `_claims`. It is a transitive reader, and the
  distinction is one the module already draws: `_merged`'s docstring, six lines below, says
  *"`template_names` reads `_claims` … `get_template` reads **this**"*. Two adjacent docstrings now
  answer the same question two ways. Fold into the same edit.

**The remedy** is to replace the clause with the argument that is true and already written twice:
they import `_claims` because they need the class, the provenance, the name list and the claim from
one merge, and no public reader hands back more than one of those. Not a behaviour defect, and it
does not hold the merge — but it is precisely this slice's dominant shape (*a comment claiming a
guarantee the code does not provide*), entering in the commit whose job was closing three other
instances of it, which is the same recursion CLAUDE.md already records.

### N2 — the I4 amendment's stated verification does not reproduce for one of its four rows. Trivial.

`docs/superpowers/spec-defects.md`, the I4 amendment: *"`grep -rn` for each across `src/` returns only
its own definition or its own module's docstring."* For `declared_names` it does not: `validate.py`
returns four hits (3231, 3259, 3266, 3326). They are a **local variable** in `_check_holdout` that
shares the name, so the entry's *conclusion* — no production caller — is correct, and I verified it
independently by reading `validate.py`'s import line, which pulls `GROUPS`, `names`, `provider_of`
and `scan_group` from `plugins` and nothing else.

The defect is in the *how-verified* sentence, in a tracked record whose purpose is that the next
reader does not re-derive it. Someone re-running that grep sees four unexplained `validate.py` hits
and has to re-do the work, or worse, concludes the filing is wrong. One clause naming the shadowed
local closes it.

### N3 — a comment names `resolve_template`, which this branch deleted. Trivial, and **not** from the fix round.

`src/publishable/generators/experiment.py:96`: *"Read through `_claims` rather than
`resolve_template`, because this site also has to tell an installed-only claim apart from a name
nothing claims."* `resolve_template` exists on `main` (`registry.py`, imported at
`generators/experiment.py:8`) and was **removed by this branch**; `grep -rn "def resolve_template"
src/` returns nothing at HEAD. The comment reads as a live alternative that was weighed and rejected,
and a reader who goes looking for it finds nothing.

Introduced by `3f477de` (the tasks 8-11 fix round), not by the commit under re-review, and missed by
the whole-branch review — recorded here because it is the same class as N1 and is one word to fix
(*"rather than the `resolve_template` this branch replaced"*, or drop the clause). Does not block.

## 7. What the whole-branch review verified sound — still sound

The fix round touches `src/` in five places, four of which are docstrings or comments; the two
message strings change no control flow. Re-checked directly rather than inferred:

- **Part B's room is not narrowed.** `_check_units` still guards `except ContractError` only
  (`validate.py:1352`). `command_run` calls `resolve_units` at `cli.py:1365` and computes credentials
  at `cli.py:1547`; an `awk` scan over lines 1300-1560 finds **no `try:` or `except` at all**. Both
  halves of the credential-leak fix stay open.
- **Both no-import assertions are untouched and still present** —
  `tests/test_plugins.py:90 test_the_scan_imports_nothing` and
  `tests/test_templates.py:1128 test_get_template_imports_nothing_for_an_installed_claim`. The fix
  round modifies neither file (its only test change is one addition to `tests/test_validate.py`), so
  the discrimination the whole-branch review proved by mutation is unchanged.
- **`__all__` still holds exactly fifteen names**, matching § The importable surface's fifteen built
  rows: `ArtifactError`, `ArtifactExistsError`, `BaseExperiment`, `BaseStep`, `BaseTemplate`,
  `ContractError`, `Estimate`, `Param`, `PublishableError`, `Unit`, and the five `register_*`.
  `__init__.py` is not in the fix diff.
- **No path reachable from `validate` imports a plugin.** `load_entry_point` — the only caller of
  `EntryPoint.load()` — still has no caller in `src/`; `validate.py` and `templates/registry.py`
  import only metadata-scan functions. The fix round adds no import and no call.

## 8. Mechanical pass over what the fix edited

`docs/reference.md` and `docs/superpowers/spec-defects.md`: no trailing whitespace, tab, or invisible
unicode; the new spec-defects table's two rows match its two-column header; the new anchors
(`#errors-core-raises`, `#errors-validate-reports`) resolve; the new spec-defects heading produces a
unique anchor. `apparatus.py`'s rewritten § Package layout comment keeps the `— not yet built`
suffix the section's own rule requires.
