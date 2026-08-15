# Task 6 report — per-repo registration, non-aliasing module names

## Status

Complete. `uv run pytest` (1657 passed, 2 xfailed), `uv run ruff check .`, `uv run mypy` all green.
`ruff format .` was not run.

**Read the addendum at the bottom with this.** Review found two real defects in what is
described below — a `sys.path` restore that a template could defeat, and a residue
assertion that enumerated names by hand. Both are fixed; where this section and the
addendum disagree, the addendum is current.

## What I found before writing anything

I probed both reported failures against the pre-change `discover_local`. **The brief's
premise for failure 1 is wrong, and I did not contort the test to rescue it.**

| Probe | Result against the old code |
|---|---|
| Two repos, each `templates/my_assay.py`, plain classes | **Passes already.** The old code popped the stem from `sys.modules` *before and after* each import, so repo B re-imported fresh and got B's class |
| Two repos, each `templates/my_assay.py` importing a sibling `.py` helper | **Passes already**, but by accident: every `templates/*.py` is itself imported by discovery, so the helper was popped too |
| Two repos, each `templates/my_assay.py` importing `templates/support/` (a *package*, so discovery never imports it directly) | **Fails.** Repo B's class silently carries repo A's `ORIGIN` |
| `templates/json.py` whose top level says `import json` | **Fails.** It imports itself, `saw_stdlib_json` is `False`, and `sys.modules["json"]` is left *deleted* for the rest of the process |

So the sharper repro (failure 2) is real exactly as described. Failure 1 is real only
where the helper is a **directory** — a regular or namespace package, which discovery
never imports directly and therefore never popped. A sibling `.py` helper passes, because
discovery imports every `templates/*.py` itself and pops it on the way out. That
directory shape is what the test uses.

*(An earlier draft of this paragraph said "the sibling-helper shape", which contradicted
the table above it and the fixture below it. Corrected here, since the review's brief
inherited the error from it.)*

## Implementation (`src/publishable/templates/discovery.py`)

Two mechanisms, and they close different failures — this is the part not to conflate:

1. **`_module_name(repo_root, stem)`** — `_publishable_local_<sha256(repo_root)[:12]>_<stem>`.
   Keyed on the resolved repo root as well as the stem, so two projects never share a
   `sys.modules` entry; prefixed so the name cannot land on a real module, which is what
   stops `templates/json.py` being bound as `json` and importing itself.
2. **`_import_file`** — `spec_from_file_location` + `exec_module`, with `sys.modules`
   snapshotted and put back afterwards. The restore is **scoped**, not blanket: a new
   entry is removed only if it is our synthetic name or `_is_local` places it under
   `templates_dir`; a *replaced* entry is restored wherever it lives (that is the
   stdlib-clobber path). A blanket restore would un-import whatever a template
   legitimately pulled in — numpy, which `publishable` itself loads — and trade a
   discovery bug for a C-extension re-initialisation bug elsewhere in the process.
   `templates_dir` now goes on the **end** of `sys.path`, not the front, so a template
   may still import a sibling helper without that directory shadowing stdlib or
   site-packages for the duration — and `sys.path` is snapshotted and restored whole
   (**corrected in the addendum**; the index this originally used was defeated by a
   template that mutates `sys.path` during its own import).
3. **`_is_local`** tests `__file__` **and every entry of `__path__`**. `__file__` alone
   misses a namespace package — a helper directory with no `__init__.py`, which is the
   default shape since nobody adds one on purpose, and which has no `__file__` at all.
   Left cached, it hands the next repo the previous repo's submodules. Measured: repo A
   doing `import plain.data` and repo B doing `import plain` then reading `plain.data`
   gives B repo A's value. That asymmetric pair cannot be a fixture — once the residue
   is gone repo B correctly raises `AttributeError` rather than returning a value — so
   the test asserts the residue's absence directly.

`importlib.import_module` and `sys.path.insert(0, ...)` are gone.

## Tests (`tests/test_templates.py`)

Four added (the fourth in the addendum):

- `test_two_repos_in_one_process_do_not_cross_contaminate` — asserts **class identity**
  (`__doc__` is `"A's"`/`"B's"`, `origin` is `"A"`/`"B"` from each repo's own helper,
  `type(a) is not type(b)`), plus `_modules_under(tmp_path) == []`, plus `__module__`
  inequality. Each repo ships both helper shapes — `support/` with an `__init__.py`,
  `plain/` without.
- `test_a_repos_own_templates_are_reachable_from_a_second_call` — the control: per-repo
  naming must not make a repo resolvable only once.
- `test_a_template_named_for_a_stdlib_module_does_not_import_itself` — `saw_stdlib_json is
  True` (also the control: skipping stdlib-named files would leave the template
  unresolved) and `sys.modules["json"]` still has `loads`.

`templates/io.py` is named in the docstring rather than tested: clobbering
`sys.modules["io"]` mid-suite is a worse failure than the one being guarded.

## Mutation testing — applied, run, reverted, verified by behaviour

*(Superseded by the addendum's five-mutation table, run against the current code.)*

Each mutation: edit, `rm -rf __pycache__`, `uv run pytest`, restore, `rm -rf
__pycache__`, re-run. No `git status` was used as evidence.

| Mutation | Result |
|---|---|
| `_module_name` returns `stem` alone (**the named one**) | Both new tests **FAIL**. Cross-repo dies on `assert 'my_assay' != 'my_assay'`; the json test dies on `saw_stdlib_json is False` with `<class 'json.Jsonish'>` |
| `_is_local`'s `__path__` clause returns `False` | Cross-repo **FAILS** on the residue assertion |
| Replace the scoped restore with `del sys.modules[module_name]` | Cross-repo **FAILS** on `assert 'A' == 'B'` — the `origin` leak |
| All reverted | 19/19 in the file, 1656 passed / 2 xfailed in the suite |

The finished tests were also re-run against the **pre-task-6** `discovery.py` (from
`HEAD~1`): both new tests fail there, so neither is a tautology of the new code.

**Be precise about which mutation kills what.** The stem mutation kills the json test
*behaviourally*. It kills the cross-repo test only through the `__module__` inequality —
the `origin` leak is closed by the `sys.modules` restore, which the naming mutation does
not touch. The `__module__` assertion is asserting the deliverable (non-aliasing names),
not standing in for identity, and the identity assertions are there beside it.

## Concerns

**Can anything still leak between repos?** One residual path, and it is not closable here:
a template that imports a helper living *outside* its own `templates/` — a top-level
`src/shared.py`, say, reached because the repo's `src/` happens to be on `sys.path` from
an earlier `load_experiment`. The scoped restore deliberately leaves such an entry alone,
because removing arbitrary site-packages/`src` modules is the worse hazard. Within
`templates/`, and for the synthetic module names themselves, nothing persists between
calls — asserted, not asserted-about: the cross-repo test checks `sys.modules` directly.
There is no memo at any layer, and `discover_local` re-imports on every call.

A second, narrower one: a template that mutates another module's attributes in place
(`numpy.foo = ...`) is not undone, because the restore compares module *identity*, not
contents. Undoing that is not achievable without deep-copying `sys.modules`.

A third: `sys.path.append` means a template's `import x` prefers a real installed `x` over
its own `templates/x.py`. That is the correct precedence, but it is a behaviour change
from the front-insert, and it is undocumented in the four documents (tasks 11–15).

**Task 7:** the return shape is **unchanged** — `dict[str, type[BaseTemplate]]`, and
`found[name] = cls` still overwrites silently. Nothing in the naming scheme affects task
7's dispatch. Flagging for them: that shape still carries no **file path** per provider,
and `cls.__module__` is now a synthetic hashed name, so it is not usable as a provider
label — naming both providers will need the path threaded through explicitly.

---

# Addendum — review response

Three findings from review, all accepted. Two were real defects in what I shipped; both
are fixed, and both fixes are mutation-proven on the **behavioural** assertion, not on a
state assertion standing in for one.

## 1. `del sys.path[entry]` — the `sys.path` index was the same bug one layer down

The index was captured *before* `exec_module`, so a template that mutates `sys.path` on
its own top level — itself, or through any library it imports — invalidates it. Measured
against `3beabee`, two repos each with `templates/helperx.py` and a `my_assay.py` doing
`sys.path.insert(0, '/zzz')`:

- `type(a).origin, type(b).origin` → `A`, `A` — **repo B served repo A's helper**
- `/Users/joon/src/tries/publishable/src` silently **deleted** from `sys.path`
- repo A's `templates/` left on `sys.path` **permanently**

And 19/19 passed with it. My comment asserting the correctness property was wrong; worse,
it asserted a property the code did not have, which is the failure mode this slice keeps
producing.

Fixed by snapshotting `sys.path` beside `sys.modules` and restoring it whole:
`before_path = list(sys.path)` … `sys.path[:] = before_path`. Symmetric with the line
above it, and the docstring now says why neither an index nor a `remove` is sufficient.

`test_a_template_that_mutates_sys_path_does_not_leak_to_the_next_repo` covers it. Each
template does **both** `sys.path.insert(0, '/zzz')` **and**
`sys.path.append(os.path.dirname(__file__))`, so the test kills the `remove`-the-string
variant too — `remove` takes the first occurrence, which is discovery's, leaving the
template's copy and the same permanent entry.

## 2. The residue assertion enumerated two names by hand

`"plain" not in sys.modules and "support" not in sys.modules` would pass a defect that
evicted `plain` but left `plain.data` — and `import plain.data` consults
`sys.modules["plain.data"]` first, so a stale submodule is a live leak on its own.
Replaced with `_modules_under(tmp_path)`, which **computes** every `sys.modules` key
whose `__file__` or `__path__` resolves under the directory. Nothing is enumerated.

## 3. Report summary sentence corrected

"failure 1 is real only in the sibling-helper shape" contradicted my own table and my own
fixture — a sibling `.py` *passes*; the leak needs a helper **directory**. Corrected in
place above, with a note, since the review's brief inherited the error from it.

## Mutation testing — five mutations, all on the current code

Each: edit, `rm -rf __pycache__`, `uv run pytest`, revert, `rm -rf __pycache__`, re-run.
Behaviour only; `git status` was never used as evidence.

| Mutation | Dies on |
|---|---|
| `sys.path[:] = before_path` → index-based `del` (the shipped bug) | `type(b).origin == "B"` → `'A' == 'B'` |
| `sys.path[:] = before_path` → `sys.path.remove(str(templates_dir))` | `type(b).origin == "B"` → `'A' == 'B'` |
| Drop the `sys.modules` restore | `type(b).origin == "B"` → `'A' == 'B'` |
| `_is_local`'s `__path__` clause → `False` | `_modules_under(tmp_path) == []` → `['plain']` |
| `_module_name` returns `stem` alone | `type(a).__module__ != type(b).__module__` |
| All reverted | 20/20 in the file, **1657 passed / 2 xfailed** suite-wide; ruff and mypy clean |

The first three kill on the cross-repo leak itself, which is the strongest available kill.

## Task 7 routing — stronger than I stated

The review is right and I understated it. The restore **deletes the module object**, so
`inspect.getfile` on a discovered class raises `TypeError: … is a built-in class` — the
file path is not merely unlabelled, it is **unrecoverable** from the class. Threading the
path through `discover_local`'s return is therefore mandatory for task 7, not stylistic.
The return shape is still `dict[str, type[BaseTemplate]]` and still overwrites silently.

## Remaining concerns

Unchanged from above: a helper imported from *outside* `templates/` (a repo's `src/`, on
`sys.path` from an earlier `load_experiment`) is deliberately not evicted, and in-place
mutation of another module's attributes is not undone. Both are documented trade-offs
against un-importing C extensions, not oversights.

Noted as routing, not mine: the `sys.path.append` precedence sentence has no owner in
tasks 11–15; the coordinator is widening task 15 by one sentence.
