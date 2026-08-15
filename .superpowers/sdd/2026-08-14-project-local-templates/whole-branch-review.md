# Whole-branch review — H7a, project-local templates

Branch `h7a-local-templates`, 26 commits `4681bda..6468842`, 13 files, +2199/−55.
Reviewed against the diff, the spec, the plan, the ledger, and the tree at `6468842`.

**Verdict: findings.** No Critical. Three Important, five Minor. The shipped behaviour is
correct: the acceptance property holds end-to-end, and every previously-vacuous mechanism this
slice makes load-bearing (`code_hash` over `templates/**`, `run`'s dirty gate, `__pycache__`)
was verified to hold. Two of the three Importants are text — a contract break on a reachable
path, and a guarantee three artifacts claim that the code refutes; the third is two documented
ordering guarantees no test can fail.

---

## What was verified to hold

**The acceptance property, end-to-end, exercised rather than read.**

| Property | Result |
|---|---|
| `templates/<name>.py` resolves by name through `validate` | `✓ config valid` on a `generate template` → `init` → `validate` chain |
| … through `run` | full run rc 0; the local `aggregate`'s fingerprint metric lands in `run.yaml` |
| … through `generate experiment` / `init` | config written, `experiment_type: my_assay`, no `template_version` key, header carries no version clause |
| Core's builtins resolve beside a local | `template_names(A) == ['generic', 'shared']` |
| Two files claiming one name are refused naming both | `E-TEMPLATE-COLLISION`, both `path::Class` providers present |
| A local shadowing `generic` | `E-TEMPLATE-COLLISION`, names the file and `GenericTemplate` |
| A broken file is a finding, not a traceback | `E-TEMPLATE-LOAD` from `discover_local`; reported as a finding by `validate` |
| Two repos in one process never see each other's templates | `get_template("shared", A/B/A)` → `AClass`/`BClass`/`AClass`, in one interpreter |
| Locality stamp does not leak | `is_local_template(GenericTemplate)` still `False` after discovering an unrelated repo |
| `generate template` refuses an existing file | `E-TEMPLATE-EXISTS`, rc 1 |

**Item 3 of the brief — mechanisms this slice makes load-bearing, none touched by the branch.**
Both hold, and neither was tested by any task.

- `code_hash` moves when `templates/my_assay.py` is edited, and returns to its previous value
  when the edit is reverted in place.
- `run` refuses a dirty `templates/` — `E-CODE-DIRTY  src/** or templates/**`, rc 1, against an
  otherwise-valid config.

**Item 4 — `__pycache__`.** The scaffolded `.gitignore` (`scaffold.GITIGNORE`) carries
`__pycache__/` and `*.py[cod]`. After a `validate` that writes `templates/__pycache__/`,
`git status --porcelain` is empty and `code_hash` is byte-identical. (See Minor 1 for the
document's stated *reason*, which is wrong even though the claim is right.)

**Item 1 — the `discovery.py` seams.** `_import_file`'s `sys.path` and `sys.modules`
snapshot/restore, the stamp task 10 moved inside it, and the drain discipline compose correctly.
The two `except` branches drain because the exception escaped before `_import_file`'s own drain;
the `not registered` and `bad is not None` branches correctly do not, having already been
drained. `finally` runs on `SystemExit` too. The restore's "new entry, or replaced entry"
split reads correct, and the second loop restores anything the import deleted.

**The locality predicate has no third fail-open** (brief's standing-defect item). Checked
explicitly rather than assumed: the stamp lands on the registered class's own `__dict__`, and
only when *that class's own defining module* resolves under this repo's `templates_dir` —
answering "is this local?" from the fact rather than from a proxy, which is what closed the two
earlier fail-opens. Builtins are therefore never stamped (probe-verified: `generic is_local =
False` after discovering an unrelated repo in the same process), a class a template merely
imports and registers is not stamped, class objects are fresh on every import so nothing carries
between repos, and no inheritance path can read the marker `True` for a class the repo does not
own — a subclass of a stamped local class is itself only reachable from inside that same
`templates/`. The one boundary case is Minor 5, and it fails closed rather than open.

**Item 5 — mechanical and cross-document passes.** A slugger-accurate sweep over
`README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`
(fenced blocks skipped) finds: no unresolvable `#anchor`, no unresolvable relative link or
cross-file fragment, no duplicate heading anchor, no table row whose column count differs from
its header (escaped `\|` accounted for), no trailing whitespace, tab, or invisible unicode, no
`x` used as multiplication, no en dash in a heading. Sweeps over every tracked `*.md` (filtering
the file list, never the output) for `no installed template` / `installed package registers` /
`generate template` / `register_template` turn up one stale site, Minor 2. A separate sweep for
`template_version` — the field whose semantics this branch changed twice — is **clean**: every
remaining site is either the status-neutral schema enumeration (`design-principles.md` § Core vs.
plugin, `reference.md` § What `parameters_hash` covers), a `generic` example where the field is
correctly present, or already carries the local-template caveat task 10 added.

**Constraints.** `__init__.py` adds exactly `register_template` and nothing else; § The
importable surface's row split is accurate and derives its build claim from the `Status` column
rather than restating it. `generate template` is a creation command taking a name — the
operation commands are untouched. The greenfield widening in § Creating a plugin ("So `validate`
does import user files no config references … importing is not inspecting … it widens that
exception from one named module to a whole directory") is accurate and sufficient — see
Important 1 for the one thing it understates.

---

## Important

### I1 — `validate` imports every `templates/*.py` twice on the unknown-name path, and the second import is outside the `try`

`validate.py` resolves the template inside a guard, then builds the diagnostic outside one:

```python
try:
    template = get_template(name, repo_root)          # discover_local #1
except ContractError as exc:
    c.error(exc.code, "experiment_type", str(exc)); return None
if template is None:
    c.error("E-TEMPLATE-UNKNOWN", "experiment_type",
            unknown_template_message(name, repo_root))   # discover_local #2 — unguarded
```

`unknown_template_message` → `template_names(repo_root)` → `_merged` → `discover_local`.

Measured by counting `discover_local` calls through one `validate_config`: **2** on an unknown
`experiment_type`, **1** on a resolvable one. `generators/experiment.py:52,55` has the identical
pair.

Two consequences.

1. **It contradicts an explicit ruling on this branch.** Ledger, task 10: "Re-discovery would
   re-execute every user file's top level inside validate, which § Creating a plugin contracts
   to reach nothing — the eager-import exception this slice widens is once per validate, not
   twice." Task 14 reintroduced exactly that, from a different file, and no per-task review
   could see it. Every user top level, and every side effect in it, runs twice.
2. **A `ContractError` from discovery #2 escapes `validate_config`.** Reproduced: a
   `templates/*.py` whose top level is not idempotent in-process (raises on a second import),
   plus a config naming an unknown `experiment_type` → `ContractError · E-TEMPLATE-LOAD`
   propagates out of `validate_config`. That is the outcome the emit site's own comment forbids
   — "reported at all because `validate` is contracted never to raise" — and it is the same
   shape task 8 spent a fix round closing for `SystemExit`. Every other finding collected in
   that pass is discarded with it.

The trigger is ordinary user code, not a contrivance, and the reason is the restore's own
verified semantics: `_import_file` undoes only `sys.modules` entries under `templates_dir` or
ones the import *replaced*, so anything a template imports from **outside** `templates/` keeps
its module-level state across both discoveries. A template that registers into such a shared
object at module scope — a declarative `Base` imported from `src/<pkg>/`, or any third-party
registry that refuses a duplicate name — raises on import #2 deterministically, with no mistake
on the author's part.

Blast radius is bounded: `main()` catches `PublishableError` and prints a diagnostic, so a CLI
user sees `error E-TEMPLATE-LOAD …` rather than a traceback. It is still a contract break on a
reachable path, and a library caller of `validate_config` gets the raise.

Cheap fix: have the message read the already-merged mapping (or pass `template_names`' result
in), so one `validate` performs one discovery; failing that, move the message construction
inside the same `try`.

### I2 — "a collision among the files that *did* load is still found" is false, and it is asserted in three places

The clause appears verbatim, in substance, in:

- `discovery.py`, `discover_local`'s docstring — "a collision among the files that *did* load
  cleanly is still found rather than masked by the first file that didn't";
- `docs/reference.md` § Errors `validate` reports, the `E-TEMPLATE-LOAD` row — "a genuine
  collision among the files that *do* load is still found rather than masked by whichever file
  broke first" — **normative**;
- `tests/test_templates.py::test_a_broken_file_does_not_abandon_discovery_of_the_rest_of_the_directory`,
  whose docstring gives it as the harm the test exists to prevent.

The code does the opposite. `if load_faults: raise load_faults[0]` precedes the collision loop
entirely; `claims` is fully populated and then never read.

Measured — `templates/{a.py raises, b.py→dup, c.py→dup}` → `E-TEMPLATE-LOAD`. Delete `a.py`,
clear `__pycache__`, rerun → `E-TEMPLATE-COLLISION`. The collision is masked by the file that
broke first, exactly as the sentence denies.

Each of the three passages then *immediately* states the LOAD-before-COLLISION precedence rule
that makes the masking mandatory, so each contradicts itself in place. The test docstring is the
worst instance: it claims the property while its own sibling
`test_a_load_failure_is_reported_before_a_collision_in_the_same_directory` asserts the opposite,
which is this repo's most-repeated defect class sited in the artifact whose job is to catch it —
a reader greps "is this checked?", finds the name, and stops.

The claim that *is* true and sufficient: every file is still imported, so a well-formed template
elsewhere is not skipped, **and the collision is still computed over a complete set of claims**
— which is the reason the precedence is safe, not an argument that both are reported. Rewrite
the clause in all three places to say that, and drop "rather than masked".

### I3 — two documented ordering guarantees survive their own mutations against the full suite

Both mutations run where the behaviour lives, in `discover_local`; both leave **1684 passed +
2 xfailed** — the branch's own green baseline.

| Mutation | Guarantee it should break | Suite |
|---|---|---|
| `for name in sorted(claims)` → `reversed(list(claims))` | "a colliding name is reported in name order rather than in the order the files happened to be read … import order … may not decide which fault is reported either" (`discover_local` docstring) | green |
| `sorted(templates_dir.glob("*.py"))` → `sorted(…, reverse=True)` | "Reported for the first such file in sorted order" (docstring **and** `reference.md`'s `E-TEMPLATE-LOAD` row) | green |

The cause is the ledger's own named shape, *a dimension no assertion can see*: every fixture in
the suite has **exactly one** colliding name and **exactly one** broken file, so no assertion can
distinguish an ordering at all. The ledger records the first as "probe-verified with the
later-sorting collision's files importing first" — a probe run by the implementer, which does not
survive into the branch.

Both are cheap to close, and each needs the fixture shape the suite lacks rather than another
assertion on an existing one: for the walk, **two** broken files whose alphabetically-later one
is imported first, asserting the earlier is named; for the collision, **two** distinct colliding
names, asserting the alphabetically-first is the one reported. Verified after reverting that the
guarantees do hold today — `aaa.py`/`zzz.py` both raising reports `aaa.py`; names `aaa`/`zzz`
both colliding reports `aaa`.

---

## Minor

**M1 — the `__pycache__` sentence attributes the right claim to the wrong mechanism.**
§ Templates: "scaffolded alongside a `.gitignore` that already excludes it, **so neither the
dirty gate nor `code_hash` notices**." `code_hash` reads the working tree, not git — its own
docstring says so — so `.gitignore` has no bearing on it. Its immunity is unconditional and comes
from `hashes._SKIP_DIRS = {"__pycache__", …}` and `_SKIP_SUFFIXES = {".pyc", ".pyo"}`. The
follow-on ("a hand-assembled repo whose `.gitignore` omits that line goes dirty at `validate` and
fails `run`") is right about the dirty gate and, by sharing the subject, implies `code_hash`
would move too. It would not.

**M2 — § Validation's `| Template is installed |` row is now the wrong check name.** A template
need not be installed. Task 14 fixed the `E-TEMPLATE-UNKNOWN` row and § The one config file; this
row — the sibling immediately above the "Template name is claimed once" row task 7 inserted — was
not revisited, and that section's own intro ("The table below states each check by the mistake it
catches") makes the label the claim. "Template resolves" would do it. The example in the cell is
still accurate for the plugin case.

**M3 — `discover_local`'s "Discards whatever the pending buffer already held before this call" is
conditional in the code.** `if not templates_dir.is_dir(): return {}` precedes the
`drain_pending()` that makes the promise. A repo with no `templates/` leaves a stale
registration queued for the *next* repo's discovery to inherit and misattribute — the exact
attribution class this slice shipped several times. Reachable rather than theoretical:
`cli._preloaded_experiment` imports user Python *before* `validate_config` runs, so a
module-scope `@register_template` anywhere under `src/**` queues a pending entry, and the early
return is what decides whether it is discarded. Moving `drain_pending()` above the `is_dir`
check costs one line.

**M4 — `_import_file`'s "so a file may import a sibling helper" holds only at module scope.**
`sys.path[:] = before_path` removes `templates_dir` before the class is ever used, so a helper
imported inside `aggregate` rather than at the top level raises a bare `ModuleNotFoundError` at
run time with no diagnostic. Verified with `importlib.import_module("__helper")` inside
`aggregate` (a plain `import __helper` there additionally hits Python's private-name mangling).
Scope the sentence to import time.

**M5 — a `BaseTemplate` subclass defined under `src/**` but registered from `templates/*.py` is
judged non-local.** `_is_local` asks where the *defining* module's file sits, which is correct
for the leak it was built for, but such a class then gets core's `template_version` written by
`init` and compared by `_check_versions` — the version lie task 10 removed. Narrow, and
defensible as "not a project-local template"; noted because § Three hashes' reason ("a string its
author remembers to bump") applies to it identically.

---

## Not raised

`ruff format --check` flags ~39 files repo-wide — pre-existing, out of scope per the brief.
`registry.py`'s "S1 knows only core's own" opening is pre-existing at `4681bda`.

## Method notes

Mutations were run where the behaviour lives and reverted by editing the file back from a copy
taken before mutating — never `git checkout`. The revert was verified **by behaviour** (two
broken files report the alphabetically-first; two colliding names report the alphabetically-first)
and then by a clean `git status` and a green suite. Sweeps filtered the file list, never the
output. `templates/__pycache__` was cleared between discovery probes. Tree left clean at
`6468842`, **1684 passed + 2 xfailed**.
