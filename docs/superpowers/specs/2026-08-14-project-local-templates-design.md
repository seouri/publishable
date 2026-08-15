# H7a Project-local templates — design

**Goal:** a template written into `templates/` in a project's own repo is **found**, so
`experiment_type: my_assay` resolves without any package being installed. This is the third of the
three homes `reference.md` § Templates already specifies, and the only one with nothing behind it.

**Why it is first.** All nine experiments in the feasibility analysis stop at `E-TEMPLATE-UNKNOWN`
before any other check runs — a template is what declares an experiment's `parameters`, and core ships
exactly one. Until a project can supply its own, nothing else in the roadmap is reachable.

**What it is not.** Not the plugin system. Entry-point resolution, `register_resolver`,
`register_probe`, `register_writer`, probes, the `Apparatus`, the change gate, `plugin new` and
`list-templates` are all H7b/H7d. A local template is *installed nowhere and distributed to nobody*.

---

## The measurement this rests on

`docs/superpowers/H7a-SCOPING.md`. Its load-bearing findings:

- **Two of § Templates' four claims are already build-true and currently vacuous.** `code_hash` covers
  `templates/**` (`hashes.HASHED_TREES = ("src", "templates")`) and `run` refuses a dirty `templates/`
  — both probed. H7a builds neither; **it makes both load-bearing**, since today the only thing that
  can live there is a file no config can resolve.
- **`BaseTemplate` has nine members and only five are live.** `parameter_spec`, `validate(config)`,
  `aggregate`, `naming_pattern`, `default_repeats` are read. `field_convention`, `required_env`,
  `apparatus_probe`, `apparatus_facts` are declarable and **dead** — grep finds them only in
  `base.py` and `generic.py`. The stub `generate template` writes must emit the five, not the nine.
- **Staticness is encoded in three signatures, not just in a dict.** `get_template(name)` and
  `template_names()` take no argument, `_BUILTIN` is module-level, and `template_names()` is called
  *inside* the `E-TEMPLATE-UNKNOWN` message — so the "known:" list cannot name a local template
  without a repo root reaching it.

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | Eager or lazy discovery | **Eager** — import every `templates/*.py` on every resolution | The scoping called this undetermined; § Creating a plugin settles it. A collision "fail[s] at load, naming both providers", and *"install order and import order are the only tie-breaks available, and both are properties of a machine rather than of a design."* **Lazy discovery makes import order decide which template you get**, which is the outcome that rule exists to refuse. Two local files claiming one name must be caught whether or not the config names either |
| 2 | What `plugin:` holds for a local template | **`null`** — no change to anything | Also called undetermined; the schema's own comment settles it — `plugin: null  # e.g. "someuser/publishable-llm@v1.2.0"` names a **distributable source**, and a local template has none. § Three hashes says `code_hash` pins it instead |
| 3 | `template_version` under a local template | **Write nothing and do not warn** | § Three hashes: *"`template_version` isn't the answer for a local template — it's a string its author remembers to bump."* Today `materialize_config` would write core's own module constant and `_check_versions` would compare a local template's config against it — a string certifying nothing. This is trap (c), and it is the single best reason the slice is not three lines |
| 4 | The README half of `generate template` | **Deferred, and the gap recorded in `reference.md`** | § Generators promises the parameter table "is added to the README", but the scaffolded README has no region for one, and `generate_experiment` never touches the README at all — a **pre-existing** defect plus a genuinely under-specified spot. Inventing a region here would be legislating. Not `spec-defects.md`: gitignored, does not survive the merge |
| 5 | Collision across the H7a/H7b seam | **H7a refuses local × local and local shadowing `generic`; local shadowing an installed plugin is H7b's** | No installed plugin can exist until entry points do, so the third case is unreachable. H7's own scoping asks for it as a named H7b deliverable, following the H3c-3 precedent |
| 6 | Where the widened promise is written down | **In § Creating a plugin, beside the argument it qualifies** | See below — this is the one documented promise this slice changes |

## The promise this slice widens, and why that is the interesting part

§ Creating a plugin justifies entry-point resolution by saying `validate` can answer "no installed
package registers `plate_wells`" ***without importing a line of that package***, "which matters because
importing a module runs its top level and `validate` is documented as creating nothing and reaching
nothing."

A local template's decorator argument **is** its registration, so its name cannot be learned without
importing the file — and decision 1 makes that *every* file in `templates/`, not only the one named.
**So `validate` will import user files no config references.**

This does not breach the greenfield invariant: importing is not inspecting, and core still never reads
the body of user Python — it is the same line `validate` already crosses for `entrypoint`. But it
**widens** that exception from one named module to a whole directory, and a documented promise changing
is not an implementation detail. The document changes first.

## The traps, and where each lives

| Trap | The rule |
|---|---|
| The registry becomes process-global while being repo-dependent | A decorator writing into a module-level dict cross-contaminates two projects in one process — this test suite today, `study add` later. Build the mapping **per call** from a repo root, with the decorator draining into a transient collection. `base_experiment.load_experiment`'s `sys.modules` purge is the precedent **and the reasoning** |
| Path-imported modules aliasing across repos | Two repos can both hold `templates/my_assay.py`. The module-naming scheme must make them distinct — the exact failure the purge above exists to prevent |
| The hoist reordering documented findings | `find_repo_root` must move **above** the template check and stay **silent on failure**: § Errors pins `E-TEMPLATE-UNKNOWN` as firing "exactly once, since that check returns immediately after", with none of the other rows. The existing `repo_root = None` precedent is the pattern. **No repo → local discovery is skipped, `generic` still resolves** |
| A signature change failing collection rather than a test | Three test bindings call `get_template` positionally, one as a **one-argument monkeypatch lambda**. A partial change breaks collection, which reads as a broken suite rather than a failing assertion |
| User code failing at `validate` | A `templates/*.py` that raises on import, registers nothing, or registers a non-`BaseTemplate` must be a **finding**, not a traceback. `validate` collects and never raises |
| `__pycache__` dirtying the tree | Probed clean **in a scaffolded project** — its `.gitignore` carries `__pycache__/`. A hand-made repo without that entry would go dirty on `validate` and fail `run`. Worth one sentence |

## Task decomposition — 15

Ten code, five documentation, from the scoping's own enumeration.

1. `register_template` — define, export from `publishable/__init__.py` and `__all__`, decorator-is-registration semantics.
2. Path discovery, **eager** per decision 1; record where the module lives.
3. Registry signatures: `get_template` / `template_names` take an optional repo root and merge builtins with locals **per call**; update all three test bindings atomically.
4. Hoist `find_repo_root` above the template check, silent on failure, preserving the early-return order.
5. Wire the other two `get_template` call sites — `cli.command_run`'s `aggregate` block and `generate_experiment`.
6. Process hygiene: per-repo registration and a non-aliasing module-naming scheme.
7. Collision and shadow refusal + its new code (local × local, local shadows `generic`), naming both providers.
8. Load-failure diagnostic + its new code.
9. `generate template`: the stub emitting only the **five live** members, greenfield refusal on an existing file, and its `_dispatch_generate` route. README half deferred per decision 4.
10. `template_version` / `plugin` under a local template, per decisions 2 and 3.
11. § Generators' `template` row → `built`, the inline `NOT BUILT` spelling in the `generate` row, and removal from `cli.NOT_BUILT_GENERATORS` — **atomically**, since the CLI tables are bound in both directions by tests.
12. § The importable surface: split the four-`register_*` row so only `register_template` reads `built`.
13. § Package layout: add the discovery module, if task 2 lands a new file.
14. `E-TEMPLATE-UNKNOWN`: message wording, its § Errors row, and the "(known: …)" list now including local names.
15. § Errors rows for the two new codes, plus decision 6's sentence in § Creating a plugin and decision 4's recorded gap.

## Out of scope, with the route

Entry-point resolution · `register_resolver`/`register_probe`/`register_writer` · probes, `Apparatus`,
the change gate · `plugin new` · `list-templates` · `publishable docs` and the managed README regions ·
`BaseReport`/`generate report` — all H7b, H7d or H8. `code_hash` and the dirty gate are **already
built**; this slice makes them load-bearing rather than touching them.
