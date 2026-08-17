# H7b Part A — whole-branch review

Reviewed `h7b-registries` (37 commits) against `main` at `ba87aae`, on 2026-08-17 at `88688e1`.
Gates re-run at HEAD: **2059 passed, 1 skipped, 2 xfailed**; `ruff check` clean; `ruff format --check`
78 files unchanged; `mypy` clean over 44 source files.

**Verdict: NOT READY TO MERGE**, on C1 alone. C1 is the shape this slice already shipped four of — a
build-state claim in a normative document that a *later task in the same slice* falsified — and it is a
one-clause deletion. Nothing in the code is wrong: every defect below is in what the prose and the
docstrings claim about the code.

Every mutation below was reverted **by editing the file back**, never by `git checkout --`, and each
revert was verified by re-running the affected tests to green (`git status --porcelain` empty at the
end of the review).

---

## Critical

### C1 — § Creating a plugin says installed-name collisions are not checked. Task 8 checks them. **Blocks merge.**

`docs/reference.md` § Creating a plugin, the paragraph beginning *"A name is claimed once, and a
collision is refused rather than resolved"*, ends its enumeration with:

> — **the installed cases arrive with entry-point resolution; today only the two local cases and the
> local-core shadow are checked.**

That clause is **false at HEAD**, and it is false because of this branch.

**How verified.** `git log -S"today only the two local cases" main..HEAD` shows the clause was added
by `24a56ff` (the tasks 1-6 fix round); `git show main:docs/reference.md` confirms `main`'s sentence
ended at *"naming both providers."* with no such clause. Task 8 (`0b5e909`) then made an installed
distribution a third claim source in `registry._claims`, which raises `E-TEMPLATE-COLLISION` over the
complete claim set. Four tests pin exactly the cases the clause excludes and pass at HEAD:
`test_two_installed_distributions_claiming_one_template_name_are_refused`,
`test_an_installed_distribution_may_not_shadow_a_core_name`,
`test_a_local_template_may_not_shadow_an_installed_one` (`tests/test_templates.py:1028-1086`), and
`validate._check_plugin_collisions` reports the other four groups
(`tests/test_validate.py:test_two_installed_distributions_claiming_one_resolver_name_are_reported`).

An early task marked a state honestly, a later task in the same slice changed the state, and the
marker was not revisited. The remedy is deleting the clause (the surrounding sentence is correct
without it), not rewording it.

---

## Important

### I1 — "Five codes return `validate_config` early … That is five *codes*." Six do. Does not block merge.

`docs/reference.md` § Errors `validate` reports, preamble (the paragraph beginning *"Five codes return
`validate_config` early, in this order"*). It enumerates `E-CONFIG-PARSE`, `E-CONFIG-SHAPE`,
`E-TEMPLATE-LOAD`, `E-TEMPLATE-COLLISION`, `E-TEMPLATE-UNKNOWN`, then argues at length that a
plugin-side collision "adds no sixth".

**How verified.** Read `validate_config` end to end and enumerated its four return sites
(`src/publishable/validate.py` lines 501, 504, 572, 598). The last one is reached from a two-armed
branch: `E-TEMPLATE-INSTALLED-UNSUPPORTED` (line 576, minted by task 9) **or** `E-TEMPLATE-UNKNOWN`
(line 590), and both fall through to the same `return None  # every later check reads the spec`. That
is six codes, not five.

This paragraph was **edited by this slice** — the whole `E-PLUGIN-COLLISION`/`E-PLUGIN-DECORATOR`/
`E-PLUGIN-LOAD` discussion inside it is new — so the count phrase was in the diff and was reasoned
about, and the one code the slice actually added to the early-return set is the one the reasoning
omits. `CLAUDE.md` names this failure directly ("when you insert or remove a row, check every row it
moved, and every count phrase near it").

**Why Important and not Critical.** The paragraph does two jobs, and only the coupling between them
broke. `-UNSUPPORTED` codes are deliberately absent from the table this paragraph introduces, and task 9
put `E-TEMPLATE-INSTALLED-UNSUPPORTED` where the convention says it belongs (§ The one config file). So
the *rows* are right and the count of rows is right; what is now wrong is the sentence tying the two
together — six codes return, five have rows, and the paragraph's closing "Every other row in this table
fires only once all five have passed" is what the sixth falsifies. The fix is one clause naming the
exception, not a renumber. It does not misdescribe any behaviour a user can observe, which is why it
does not hold the merge.

### I2 — Two docstrings in `plugins.py` name a caller that does not exist

`plugins.py`'s module docstring: loading is *"performed deliberately by a caller that has already
resolved a name and now needs the object: `run`/`dry-run`, once a command is past validation."*
`check_registration`'s: *"Reached only where an object behind a key has actually been loaded, which is
not `validate`."*

**How verified.** `grep -rn "load_entry_point\|check_registration\|declared_names" src/ tests/` returns
hits only inside `plugins.py` itself and `tests/test_plugins.py`; `cli.py` imports nothing from
`publishable.plugins` (`grep -n "plugins" src/publishable/cli.py` → three unrelated lines). No command
loads a plugin in this build, so `run`/`dry-run` is not a caller and `check_registration` is reached
nowhere.

What makes this a finding rather than spec present tense is that **the normative document chose the
other treatment for the same fact**: `reference.md`'s `E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD` rows
both carry *"As measured on 2026-08-17 against commit `deaed2b`, no task has yet given it a production
caller"*. The rows are dated and honest; the source that implements them is not. One clause in the
module docstring closes it. Note also that the ledger records this docstring as the fix for tasks
16-20's C1 — the re-argued paragraph is where the new over-claim entered.

### I3 — `E-DATA-RESOLVER-UNSUPPORTED`'s user-facing message says the plugin registry does not exist

`src/publishable/validate.py:3910` tells the user: *"resolvers are plugin artifacts and **the plugin
registry is not implemented in this build**; resolvers will be honored in a later slice."* The comment
at line 3963 repeats the same phrase.

**How verified.** This branch builds the resolver registry: `register_resolver` and `RESOLVERS`
(`plugins.py`), the `publishable.resolvers` entry-point group in `GROUPS`, and
`_check_plugin_collisions` reporting over it. `reference.md` § The importable surface marks
`register_resolver` **built**, and § Creating a plugin opens with "**Five registries, one mechanism**".
What is unbuilt is the resolver's *dispatch*, which is Part B. So the refusal is right and its stated
reason is now false — a message contradicting two sections of the document that leads it.

**And it is user-observable, not merely loose.** `tests/test_validate.py:12839-12840` asserts that one
`validate` run over a config with a `resolver` source and two colliding resolver distributions emits
**both** `E-PLUGIN-COLLISION` — the resolvers registry deciding a collision over installed metadata —
and `E-DATA-RESOLVER-UNSUPPORTED`, whose text says that registry is not implemented. Two findings in one
output, one of which denies the other. (What is genuinely absent is the *name* check,
`E-RESOLVER-UNKNOWN`, whose § Errors row is correctly marked "Not yet emitted" — so the accurate
sentence is that a resolver cannot be *dispatched*, not that no registry exists.)

This also touches the spec's decision 7: Part B's task 24 is meant to retire the refusal by deleting a
line. Leaving a false reason in the string until then means the wrong sentence is what a user reads for
the whole life of Part A.

### I4 — The shipped-but-unread filing is accurate about what it names and under-counts by four

`docs/superpowers/spec-defects.md`'s new entry *"`PROBES` and `RESOLVERS` are written by their
decorators and read by nothing"* is **correct** on both, with the right owners (H7d and Part B), and the
amendment narrowing the `BaseTemplate`-attribute family to `field_convention` + `apparatus_facts` is
also correct — verified by `grep -rn "field_convention\|apparatus_facts" src/` (declarations only) and
by reading `_check_probe`, which does give `apparatus_probe` a genuine reader.

But the entry presents itself as the slice's account of what it shipped unread, and four more surfaces
this branch added have **no production caller at all**:

| Surface | Added by | Read by |
|---|---|---|
| `plugins.load_entry_point` | task 17 | `tests/test_plugins.py` only |
| `plugins.check_registration` | task 16 | `tests/test_plugins.py` only |
| `plugins.declared_names` | task 16 | `tests/test_plugins.py` only |
| `registry.template_provenance` | task 9 | `tests/test_templates.py` only |

**How verified.** `grep -rn` for each name across `src/` — every hit is its own definition or its own
module's docstring. So the honest answer to "did a sixth creep in" is yes: the family this slice adds
is six, not two. The first three belong to whichever slice first loads a plugin (nobody today — see I2);
`template_provenance` belongs with the *"an installed template's name resolves but its class is never
loaded"* entry, owner unassigned.

---

## Minor

- **M1.** `generators/experiment.py:11` and `validate.py:42` both import the private `_claims` from
  `templates.registry`. Two cross-module callers of a `_`-prefixed name; either promote it or say in
  the module docstring that these two are the exception.
- **M2.** `_dispatch_generate` (`cli.py:2769`) accepts any `--flag value` pair into `opts` and ignores
  what it does not use, so `--plguin`, or `--plugin` passed to `generate step`/`template`, installs
  nothing and says nothing. Pre-existing shape; task 18 gave it a first consequence worth a diagnostic.
- **M3.** `W-TEMPLATE-VERSION`'s message says "left to the **installed** template's default"
  (`validate.py:1106`), while no installed template's class is ever held — the only non-local template
  reachable is core's `generic`. The spec-defects amendment discloses the reachability gap; the message
  wording does not.
- **M4.** A writer or reader claiming a core suffix raises `ContractError` · `E-PLUGIN-COLLISION` at
  decoration. Once something loads a plugin through `load_entry_point`, that raise is caught by its
  broad `except Exception` and re-reported as `E-PLUGIN-LOAD`. That matches the `E-TEMPLATE-LOAD`
  precedent § Errors already documents for a coded error from a local template's top level, but
  `E-PLUGIN-COLLISION`'s row promises its own code for that arm. Worth one sentence before Part B wires
  loading.
- **M5.** `_check_plugin_collisions`'s docstring argues that `publishable.templates` needs no skip in
  its loop, because `validate_config` returns from the `_claims` `except ContractError` branch before
  this function runs. Read the ordering — it holds — and confirmed it behaviourally with a temporary
  probe (two installed distributions claiming one template name → `E-TEMPLATE-COLLISION` present,
  `E-PLUGIN-COLLISION` absent; probe deleted). **Nothing in the suite pins it**: every
  `_check_plugin_collisions` test uses `publishable.resolvers`. If that early return ever moves, one
  fault reports under two codes and no test notices. Worth the regression, which the existing
  `installed` fixture writes in five lines.
- **M6.** § Package layout still lists `apparatus.py  # probe registry, per-condition facts, change
  gate — not yet built` while `plugins.py`'s own row now says it holds "the resolver/probe/writer/reader
  registries". Two rows claiming the probe registry.

---

## Checked and sound — no finding

**The invariant the slice exists for. No path reachable from `validate` imports a plugin.** Enumerated
by reading every caller, not by grepping one spelling: `validate.py` imports exactly `GROUPS`, `names`,
`provider_of`, `scan_group` from `plugins`; `templates/registry.py` imports `provider_of`, `scan_group`;
`load_entry_point` — the one function that calls `EntryPoint.load()` — has no caller anywhere in `src/`.
Then confirmed empirically with a temporary probe (written, run, deleted): a real installed distribution
declaring all **five** groups against a genuinely importable module (`importlib.util.find_spec` non-None),
`EntryPoint.load` monkeypatched to raise, and full `validate_config` run over three configs — plain, one
naming the installed template, one declaring a `resolver` source. No load, and the module stayed absent
from `sys.modules` in all three. The patch's own firing was proved by a positive control before the
probe was believed.

State it with its qualification: **no core path imports a plugin distribution to resolve a name.**
`discover_local` does import this repo's own `templates/*.py`, and `cli` imports the experiment package
before `validate_config` runs — neither is a plugin, and § Creating a plugin documents the local-file
exception explicitly.

**The two positive assertions are intact and discriminating.** Making `scan_group` call `ep.load()`
inside a swallowing `try` failed `test_the_scan_imports_nothing`,
`test_a_plugin_module_calling_sys_exit_is_contained_too` and
`test_get_template_imports_nothing_for_an_installed_claim`. Reverted by editing back; both files green.

**Four more mutations, all caught:**

| Mutation | Test that failed |
|---|---|
| `_check_probe` reads `publishable.writers` instead of `publishable.probes` | `test_an_installed_probe_satisfies_the_check_and_a_template_declaring_none_draws_nothing` |
| `_suffix_for` takes the first match instead of the longest | `test_a_third_party_suffix_reaches_io_write_s_dispatch` |
| `registries` fixture's restore loop replaced with `_ = saved` | `test_the_previous_test_s_registration_did_not_leak` |
| `register_reader` dropped from `__init__.py`'s import line, `__all__` left intact | `test_a_reader_is_importable_from_the_one_root` (AttributeError) |

The last one settles the doubt about the four `assert "X" in publishable.__all__` / `assert
publishable.X is not None` pairs: the attribute access **is** the import, so T13-A's fix does
generalize to all four.

**`CORE_SUFFIXES`'s admitted proxy holds.** `register_reader`'s docstring says checking
`suffix in CORE_SUFFIXES` is "correct only because core's own writer and reader tables in `artifacts.py`
are defined with identical keys". Read both dicts (`artifacts.py:145-159`): the same five keys, in the
same order. The justification is true today, and the docstring is the right place for it.

**One import root.** `publishable.__all__` holds fifteen names; § The importable surface's table
enumerates exactly those fifteen plus the two `not yet built` promises (`BaseReport`, `Apparatus`), with
all five decorators marked `built`. Both directions checked.

**Part B's room was not narrowed.** `_check_units` still guards only `except ContractError`
(`validate.py:1355`); `command_run` calls `resolve_units` at `cli.py:1365` and computes credentials at
`cli.py:1547` — 182 lines later, with no `try`/`except` anywhere between lines 1300 and 1550 (awk scan).
Both halves of the credential-leak fix stay open.

**No behavior-changing environment variable.** `git diff main...HEAD -- src/ | grep -i
"environ\|getenv\|PUBLISHABLE_"` over added lines: nothing. `--plugin` is on a *creation* command
(`generate experiment` / `init`), which the invariant permits, and `uv add` is invoked with an argument
list and no shell.

**New codes are documented.** `E-ARTIFACT-UNREADABLE`, `E-UV-ADD` and `E-UNITS-SOURCE-AMBIGUOUS` each
have a § Errors row. `E-TEMPLATE-INSTALLED-UNSUPPORTED` deliberately has none — the `-UNSUPPORTED` build
family — and is described in § The one config file, as spec correction 1 requires.

**Mechanical pass over the four documents** (script, thrown away): no duplicate heading anchors, no
broken relative link or `#anchor`, no trailing whitespace, tab or invisible unicode outside fences. One
apparent bad link (`units.pred, units.truth`) is a false positive from an indented fence and is present
on `main`.
