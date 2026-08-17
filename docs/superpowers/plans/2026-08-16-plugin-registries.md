# H7b Part A — plugin registries and entry points — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a plugin installed on the machine can register a template, a resolver, a probe, a writer
and a reader, and `validate` answers whether a name is registered **from package metadata alone,
without importing a line of that package**. The collision matrix over those names is decided at
load, over the complete claim set, and reported in name order rather than left to install order.
No refusal is retired and no experiment newly executes: `E-DATA-RESOLVER-UNSUPPORTED` stays alive
through every task here and Part B retires it.

**Architecture:** a new `src/publishable/plugins.py` wraps `importlib.metadata.entry_points` and is
the only module in core that names an entry-point group. It exposes a **metadata-only** scan —
`scan_group(group)` returns `{name: [EntryPoint, …]}` keyed by the entry-point key, with every
provider that claimed it — and never calls `EntryPoint.load()`. `templates/registry.py` grows a
third claim source from that scan: `_claims(repo_root)` builds one mapping from core's `_BUILTIN`,
`discover_local`'s findings and the `publishable.templates` scan, decides every collision over the
complete set in name order, and records each claim's **provenance** (`core` / `local` / `installed`)
and its **provider** string. `_merged` is rebuilt on top of `_claims` and still returns only classes
core can hand back — core's and this repo's — because an installed template's class would cost the
import the entry-point mechanism exists to avoid. A config naming an installed-only template is
therefore *known* and *unresolvable*, reported as a `-UNSUPPORTED` refusal of its own rather than as
`E-TEMPLATE-UNKNOWN`. `is_local_template` is replaced at both of its readers by
`template_provenance(cls)`, which asks the direct question at the merge instead of trusting a
marker. The other four registries — `register_resolver`, `register_probe`, `register_writer`,
`register_reader` — live in `plugins.py` beside the scan, each populating a process-level mapping
the decorator fills when a plugin module is imported, with `register_writer`/`register_reader`
feeding `artifacts.WRITERS`/`artifacts.READERS` under an enforced key symmetry. Two load-time
helpers ship with them and have no production caller in this slice, each named as such:
`check_registration` (the decorator argument against the entry-point key) and `load_entry_point`
(import-failure containment including `SystemExit`).

**Spec:** docs/superpowers/specs/2026-08-16-plugin-registries-design.md

**Task count: 20**, exactly the spec's § Task decomposition and the re-scoping's § 9 Part A, in
their order and their grain. No task was split, merged, or moved.

**Sequencing.** Task 1 before everything: it mints the identifiers later rows and messages cite.
**Task 3 before task 7** — task 3 settles the fifth group, and task 7's scan covers five groups
rather than four because of it. Task 7 before 8, 9 and 20, which all read the scan. Task 4's
§ Package layout marker is retired **inside task 7's commit**, not task 4's, so the document never
claims a module that is not there. Task 13 ships its reader with its export. Tasks 19 and 20 are
what Part B's first tasks build on. Tasks 6 and 18 edit the same § Creation commands row twice, in
that order.

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced because an
implementer sees only its own task brief.

**Commands.** Tests `uv run pytest`. Lint `uv run ruff check .`. Format `uv run ruff format .`.
Types `uv run mypy`. All four must pass before a commit.

**Verify format with `uv run ruff format --check .`, never the bare form.** A previous brief in this
repo wrote the bare form where it meant `--check` and rewrote 67 files. **The repo is format-clean:
`ruff format --check .` reports 76 files, 0 to reformat. Keep it that way.**

**Baseline.** `uv run pytest -q` is **1999 passed, 2 xfailed**. A task that leaves the count below
its own additions has broken something. Every task states its expected count.

**`E-DATA-RESOLVER-UNSUPPORTED` stays alive through all of Part A.** Every test on a
resolver-adjacent config asserts its new finding appears **alongside** that code, never instead of
it, and **never asserts on the total set of codes** — so Part B's task 24 retires it by deleting one
line from each test rather than rewriting them. The probe that establishes this is the re-scoping's
§ 4 matrix: every `RES` row that earns a second code prints it beside the wholesale refusal.

**`validate` collects rather than aborting.** A refusal elsewhere never makes a later check
unreachable. Two independent readers got this wrong in H7c and a reviewer disproved it by building
the fixture. Do not infer unreachability from a refusal; build the config and look.

**Every new error site is pinned by its MESSAGE, not only its code.** Use the `fragment` +
`messages_by_code(path)[code]` pattern already in `tests/test_validate.py`. Both helpers are defined
at the top of that file: `codes(path)` returns the set of every finding's code,
`messages_by_code(path)` returns `{code: message}`. Where two branches emit one code, their messages
must be *distinguishable* and each pinned separately. **A message assertion is not automatically a
discriminating one** — one in a previous slice was vacuous because the message's invariant tail
contained the asserted fragment either way. Assert a fragment only one branch can produce.
**`messages_by_code` collapses duplicate-code findings last-wins**, so a code emitted more than once
per config must be asserted with a counted helper in the shape of `tests/test_validate.py`'s
`_findings_of`, not through `messages_by_code`.

**`tests/conftest.py` has an autouse fixture restoring `os.environ` around every test. Do not add a
second.** Nothing in this slice reads the environment, but nothing in this slice may add a second
autouse fixture of any kind either — the registries this slice mints are process-global and their
restoration belongs in the test file that mutates them, as a plain `yield` fixture requested by
name.

**Nothing in Part A may narrow Part B's options on the credential-leak fix.** Concretely, and these
are prohibitions rather than guidance: **do not add a `try` around `resolve_units` in
`cli.command_run`**; **do not widen or narrow `_check_units`'s `except ContractError`**; **do not
move `validate_config`'s `c.credentials = credential_values(...)` line** relative to the checks
around it. `command_run` computes its credential set 182 lines after `resolve_units` with no
enclosing `try`, and `_check_units` guards only `except ContractError`; Part B's task 28 owns both,
and its remedy is to move the credential computation rather than to wrap the call.

**The installed-distribution fixture, and what it does and does not exercise.** Decision 6 says an
entry-point *metadata* scan cannot be exercised by a fixture that only writes files. The fixture
this slice builds writes files — and the reason that is not the thing decision 6 forbids is worth
stating rather than slipping past. `importlib.metadata` discovers a distribution by scanning each
`sys.path` entry for a `*.dist-info` directory holding a `METADATA` file, and reads its entry points
out of `entry_points.txt` beside it. That is exactly what `uv` and `pip` write, so a directory
holding a hand-written `dist-info` **is** an installed distribution as far as every API this slice
calls is concerned. Probed at `ff51864` against a two-distribution fixture: `entry_points(group=…)`
returned both providers of a duplicated name, and `EntryPoint.name`, `.value`, `.dist.name` and
`.dist.version` were all readable with nothing imported.

What the fixture **does** exercise: dist-info discovery off `sys.path`, group selection, one name
claimed by two distributions, and every metadata attribute this slice reads. What it does **not**
exercise: `pyproject.toml`'s `[project.entry-points."publishable.resolvers"]` table becoming
`entry_points.txt`. That translation is `hatchling`'s and core reads no `pyproject.toml`, so it is
outside what any test here could pin — a named residual, not a gap. Four mechanical rules:

- **One directory per arrangement.** `importlib.metadata`'s `FastPath` caches on `(root, mtime)`.
  Never add a second `.dist-info` to a directory already scanned in the same test; build a fresh
  directory instead.
- Call `importlib.invalidate_caches()` after prepending, always. It is cheap and it removes a flake
  class that would otherwise be misdiagnosed as a scan bug.
- Use **`monkeypatch.syspath_prepend`**, never a new autouse fixture and never a bare
  `sys.path.insert`. Per-test `monkeypatch` already restores `sys.path`.
- The project floor is `requires-python = ">=3.11"`. Use the selection API `entry_points(group=…)`;
  the dict-returning form is gone in 3.12+.

**Mutation discipline, every task.** Apply the named mutation to the file it names. Run the named
test. Confirm it **FAILS**. Then `find . -name __pycache__ -type d -exec rm -rf {} +`. Then revert
**by editing the file back in place** — **never `git checkout -- <file>`**, which destroys
uncommitted work and has been mistaken for a revert twice in this repo. Confirm the test **PASSES**
again, and verify the revert by *behaviour*, never by `git status`.

**A mutation is a claim too.** Before writing or believing "this mutation must fail test X", read
the *body* of test X and check the two branches can actually produce different results. Across the
last three slices six prescribed mutations were blind, one defended with an articulate argument that
was simply wrong. Where this plan concludes a mutation cannot discriminate, it says so and
prescribes a different one; do the same for any mutation you add. Two shapes this slice is
specifically exposed to: **swapping a value between `WRITERS` and `READERS` cannot fail**, because
they hold the same keys — the mutation that can is adding a key to one dict only; and **two elements
cannot distinguish four orderings**, so a collision fixture needs two installed distributions and
names whose sorted order differs from their install order.

**Test-design rules this repo enforces.**

- A control that asserts only an absence passes identically if nothing ran. Every such assertion
  needs a positive companion **produced by the code under test**, in the same test.
- **Test the honouring, not only the refusal.** This slice is mostly refusals. A correctly declared
  registry over a clean claim set must resolve, and the scan must return what a distribution
  actually declared — without that, a scan returning `{}` unconditionally passes every refusal test.
- **Never filter the output of a sweep whose job is to find a string — filter the file list.** A
  reviewer checking this exact rule lost a true hit to `grep -v superpowers`. Prove each sweep can
  fail by running it against a string known to be present. The four documents must be **named** in a
  sweep, since the development record is tracked and `*.md` no longer means what it used to.
- **Read a target test file's existing module-level names before naming a helper.** The names
  already taken in the files this slice touches are listed in each task.
- **A check written where the roster is not proves nothing.** Under a resolver the surviving checks
  are the declaration-against-declaration ones; a test that mutates `cluster_by` to prove a resolver
  path works proves nothing, because that check fires today with the refusal in place.

**Documentation rules.** `×` not `x` for multiplication, including inside fenced blocks. Hyphen,
never an en dash, in anything that becomes a filename or an anchor. **Cite by section**
(`reference.md` § "Creating a plugin"), never by line number. **No positional references** — do not
locate a table row as "the two rows above" or "further up"; name what a sibling row *does*, and when
you insert or remove a row, check every row it moved and every count phrase near it. **No counts in
comments or docstrings** — state what a set *is*. **Do not enumerate call sites.** **Prefer deleting
a claim to rewriting it**: a round closing a false-claim finding closed it by propagating the claim
to two more sites. After any `*.md` edit run the mechanical pass: every relative link and `#anchor`
resolves, no two headings in a file share an anchor, every table row matches its header's column
count and none is empty, no trailing whitespace, tab, or invisible unicode — skipping fenced code
blocks in all of them. Any inline `# a | b | c` enum comment must list every value its table defines.

**The four normative documents LEAD; `src/` follows.** `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`. Where they and the code disagree, **the
document changes first** and the gap is recorded in `docs/superpowers/spec-defects.md`. The
cross-document pass governs those four **only** — never the development record under
`docs/superpowers/`, where a correction is appended rather than retro-edited. `spec-defects.md` is
the one exception: a closed gap is struck there rather than left to mislead.

**`reference.md` § Errors `validate` reports carries one row per code covering every emit site**,
not one row per site. `E-TEMPLATE-UNKNOWN` cost a slice a round by being scoped to one of its two
emit sites, and it still has two: `validate._check_shape`'s caller reports it, and
`generators/experiment.py` raises it, both through `registry.unknown_template_message`.

**What Part A settles that the spec left open, stated once here so no task re-derives it.** Decision
3 states the invariant as "`validate` resolves a name *without importing a line*" — of resolution,
not merely of the negative answer. Part A therefore **never calls `EntryPoint.load()`**, and the
consequence is that an installed template's *class* is never held. A config naming an installed-only
template name is **known and unresolvable**: task 9 mints `E-TEMPLATE-INSTALLED-UNSUPPORTED` for it,
which is the undocumented `-UNSUPPORTED` build family — **no § Errors row, and it must not gain
one** — retired wholesale by whichever slice loads an installed template. That slice is **not Part
B**, whose nine tasks are the resolver half; task 9 files the residual with its owner stated as
unassigned. The direct consequence for tasks 9 and 10: `installed` is **unreachable at both of
`is_local_template`'s class-taking readers** in Part A, and each of those tasks says so rather than
pretending a fixture reaches it.

**Identifiers this slice mints.** Confirm the family is still free before task 1 by sweeping the
file list, not by filtering output:
`grep -rnE "E-(RESOLVER|PROBE|PLUGIN|READER)[A-Z-]*" docs/reference.md docs/design-principles.md docs/experimental-designs.md README.md src/`
→ must be empty; can-fail control on the identical file list,
`grep -oE "E-TEMPLATE[A-Z-]*" docs/reference.md | sort -u` → five distinct codes.

| Code | Fault | Row in | Emitted in |
|---|---|---|---|
| `E-RESOLVER-UNKNOWN` | `data.units.from.resolver` names a resolver no installed distribution registers | 1 | **Part B task 24** |
| `E-RESOLVER-MEASUREMENT-FIELD` | `measurements.by` names a field the resolver yields no attribute for | 1 | **Part B task 25** |
| `E-RESOLVER-SWEPT-PARAM` | a resolver reads a parameter the sweep varies | 1 | **Part B task 26** |
| `E-PROBE-UNKNOWN` | a template's `apparatus_probe` names a probe no installed distribution registers | 1 | **13** |
| `E-PLUGIN-COLLISION` | one entry-point key in a non-template group claimed by two distributions, or a writer claiming a suffix core already writes | 2 | **8**, **14** |
| `E-PLUGIN-DECORATOR` | a `@register_*` argument disagreeing with the entry-point key that named it | 2 | **16** (no production caller in Part A) |
| `E-PLUGIN-LOAD` | an entry point whose module raises, or calls `sys.exit()`, while importing | 2 | **17** (no production caller in Part A) |
| `E-ARTIFACT-UNREADABLE` | a suffix with a registered writer and no reader, read back through `io` | 15 | **15** |
| `E-UV-ADD` | `uv add` failing for a `--plugin` argument on `generate experiment` | 18 | **18** |
| `E-UNITS-SOURCE-AMBIGUOUS` | a `data.units.from` mapping declaring both `glob` and `resolver` | 19 | **19** |
| `E-TEMPLATE-INSTALLED-UNSUPPORTED` | `experiment_type` names a template an installed distribution registers, which this build does not load | — (`-UNSUPPORTED`: no row) | **9** |

Nine codes, minted across five tasks. `E-ARTIFACT-UNREADABLE` and `E-UV-ADD` are minted in the task
that emits them rather than in task 1 or 2, because neither is a plugin-registry identifier: the
first belongs to the `ArtifactError` family and the second to a creation command, and both are rows
in § Errors **core raises** rather than in § Errors `validate` reports. Tasks 1 and 2 mint the seven
that a reader would look for under "what does a plugin registry refuse".

**Codes this slice extends rather than mints.** `E-TEMPLATE-COLLISION` gains the three plugin
template cases (task 8). `E-TEMPLATE-UNKNOWN` gains the `plugin` hint (task 11).
`W-TEMPLATE-VERSION` is compared against the template's own `version` (task 10).

**§ Errors' five-code early-return count does not move, and neither does `validate.py`'s "two
codes" comment.** Both count the codes that can reach `validate_config`'s `except ContractError`
around `resolve_template`. Every plugin-side *template* collision this slice mints rides
`E-TEMPLATE-COLLISION` and arrives there; the four non-template codes are reported as findings by
checks that do not raise into that guard. Task 2 records the decision and its grounds; **no task
increments either number.**

---

## Task 1: § Validation ↔ § Errors — the resolver family's identifiers

**Files:** Modify `docs/reference.md`. No `src/` change, no test change.

**Interfaces:**
- Consumes: § Validation's rows *Resolver is installed*, *Resolver supplies the attributes*,
  *Resolver supplies the measurement field*, *Resolver is condition-independent* and *Probe is
  installed* — read them by name from the § Validation table; each is two cells,
  `Check | Example failure`, and **no row in that table names a code**. § Errors `validate` reports'
  table, header `| Reported when | Code |`.
- Produces: four § Errors rows — `E-RESOLVER-UNKNOWN`, `E-RESOLVER-MEASUREMENT-FIELD`,
  `E-RESOLVER-SWEPT-PARAM`, `E-PROBE-UNKNOWN` — each marked with the task or slice that emits it.
  Task 13 emits the fourth; Part B emits the other three.

**The reuse-vs-mint ruling, settled here.** The re-scoping's § 5(d) leaves open whether a resolver
reading a swept parameter reuses `E-STEP-SWEPT-PARAM` or mints its own. **Mint
`E-RESOLVER-SWEPT-PARAM`.** `E-STEP-SWEPT-PARAM` is documented in § Errors core raises as a
`ContractError` a *step* raises at run time from `"run"` or `"summary"` scope, and a reader holding
that identifier is sent to § Step scope, which describes a different fault at a different time. The
mechanism is shared — `config.SweptAway`'s `Node.__getattr__` raises on the read — and sharing a
mechanism is not sharing a fault; `discover_local` already relabels a coded `ContractError` from
user code as `E-TEMPLATE-LOAD` for the same reason. Write that argument into the row.

**A § Errors row whose check does not exist yet is the thing this repo has got wrong before** —
five § Validation rows once described checks with no emit site, no check and no test. So each row
below carries its build state explicitly, in the same present-tense-plus-marker style
§ The one config file and § CLI reference already use.

- [ ] **Step 1: Read before writing.** Read the five § Validation rows named above and confirm each
      still reads as measured — `Resolver supplies the attributes` is the one that is *partial*
      today (`E-UNITS-ATTR-MISSING`, worded against a table) and it is **not** this task's to mint;
      Part B task 25 generalizes it. Read § Errors `validate` reports' header and the rows around
      the insertion point. Run the identifier sweep from Global Constraints and its control.

- [ ] **Step 2: Add four rows to § Errors `validate` reports.** Place them adjacent to each other.
      Locate the insertion point by naming the row you put them after — the row reporting a
      **template name claimed twice** is a good anchor and is named here by what it does, not by
      where it sits. After inserting, re-read every row the insertion moved and every count phrase
      near them.

```
| [`data.units.from.resolver`](#where-units-come-from) names a resolver that no installed distribution registers under the `publishable.resolvers` entry-point group. Answered from package **metadata**, so a name that is absent costs no import at all — [§ Creating a plugin](#creating-a-plugin-publishable-plugin-new) makes that the whole argument for entry points, and a check that reached for the object behind the name would have changed the guarantee whatever it returned. The message names every group member it did find, the way an unresolved template names the templates it knows, because the ordinary cause is a spelling and the ordinary remedy is reading the list. **Not yet emitted:** the resolver source is refused wholesale in this build, and this code replaces that refusal when the dispatch lands | `E-RESOLVER-UNKNOWN` |
| [`data.units.measurements.by`](#what-isnt-a-repeat) names a field, and the resolver the roster came from yields no attribute of that name to collapse on. A table source reports the same fault against its columns; a resolver has no columns beyond the attributes it declares, so the field a CSV would simply have carried has to be yielded, and this is where that obligation is checked. Separate from the attribute check next to it because the two name different declarations and a reader fixing one is not fixing the other. **Not yet emitted:** a resolver-produced roster does not exist in this build | `E-RESOLVER-MEASUREMENT-FIELD` |
| A resolver reads a parameter the [sweep](#expansion-modes) varies. The unit table is one table for the whole run, so conditions that resolved different units could not be paired and `n` would mean something different in each — [§ Where units come from](#where-units-come-from) states the rule. Its own code rather than the [`E-STEP-SWEPT-PARAM`](#errors-core-raises) the read itself raises: that identifier is a step's, reached at run time from `"run"` or `"summary"` scope, and a reader holding it is sent to a section describing a different fault at a different time. Sharing the mechanism — a sentinel substituted for a swept path, raising on the read — is not sharing the fault, the same way a coded `ContractError` from a local template's top level is reported as `E-TEMPLATE-LOAD` rather than under the code it carried. An [apparatus probe](#the-apparatus-core-can-only-observe) carries no such restriction and usually does read a swept parameter. **Not yet emitted:** no resolver is executed in this build | `E-RESOLVER-SWEPT-PARAM` |
| The resolved template declares an [`apparatus_probe`](#the-apparatus-core-can-only-observe) that no installed distribution registers under the `publishable.probes` entry-point group. Answered from metadata, the same way and for the same reason a resolver name is. Reported at `experiment_type` — the field that decided which template's declaration applies — since the probe name is the template's rather than the config's, and a reader who cannot install the plugin fixes this by choosing a different template. A template declaring no probe is the ordinary case and draws nothing here | `E-PROBE-UNKNOWN` |
```

- [ ] **Step 3: Do not touch § Validation.** Its rows already state all five checks and its table
      names no code by design — a row there and a code here are the same check seen from the two
      ends, and the section's own preamble says so. Confirm you changed nothing in it.

- [ ] **Step 4: Mechanical pass.** Every `#anchor` in the four new rows resolves against a heading
      that exists (`#where-units-come-from`, `#creating-a-plugin-publishable-plugin-new`,
      `#what-isnt-a-repeat`, `#expansion-modes`, `#errors-core-raises`,
      `#the-apparatus-core-can-only-observe`), no duplicate anchors, each new row has exactly two
      cells, no trailing whitespace, no tab, no invisible unicode, no en dash where a hyphen belongs.
      Skip fenced code blocks.

- [ ] **Step 5: Cross-document pass.** The four documents only. Nothing here changes the worked
      example, a config field, an enum comment, or a version. Confirm by sweeping the four documents
      by **name** for the four new identifiers — each must appear in `reference.md` alone.

- [ ] **Step 6: Verify.** `uv run pytest` — a document-only change must leave **1999 passed, 2
      xfailed**. Also `uv run ruff format --check .` → 76 files, 0 to reformat.

- [ ] **Step 7: Mutation — and this task has none that can reach it.** Stated rather than
      manufactured. At this commit all four codes are strings in a table; nothing in the suite reads
      them. **Task 13 closes `E-PROBE-UNKNOWN`** — it pins that row's message by fragment, so a
      wrong code or a wrong wording in that row goes red there. **Nothing in Part A closes the other
      three**: `E-RESOLVER-UNKNOWN` is Part B task 24's, `E-RESOLVER-MEASUREMENT-FIELD` task 25's,
      `E-RESOLVER-SWEPT-PARAM` task 26's. Do **not** invent a test that greps the document for a
      code — that pins prose to a literal and creates a maintenance obligation nobody owns. The
      verification available here is the re-read: each row must state a condition no other row in
      the table states, and each must name its build state.

- [ ] **Step 8: Commit.** `docs: mint the resolver family's identifiers, and E-PROBE-UNKNOWN`

---

## Task 2: § Errors core raises + § Creating a plugin — the four load-time refusals with no identifier

**Files:** Modify `docs/reference.md`. No `src/` change, no test change.

**Interfaces:**
- Consumes: § Creating a plugin's paragraph beginning **"A name is claimed once, and a collision is
  refused rather than resolved"**, which enumerates the cases in prose and today closes with "The
  two local cases are the ones this build checks"; § Errors core raises' table row whose `Type ·
  code` cell is `ContractError · E-TEMPLATE-COLLISION`; § Errors `validate` reports' row for the
  same code, whose closing clause reads "A local name an **installed plugin** registers is the same
  fault and is not yet checked".
- Produces: § Errors core raises rows for `E-PLUGIN-COLLISION`, `E-PLUGIN-DECORATOR` and
  `E-PLUGIN-LOAD`; `E-TEMPLATE-COLLISION`'s two rows extended to the three plugin template cases;
  and the recorded decision that **neither** § Errors' five-code early-return count **nor**
  `validate.py`'s "two codes" comment moves.

**The decision this task exists to make, and it is a negative one.** The re-scoping's § 6 narrowed
this task to exactly one question: does a plugin-side load fault add a *code* to the set that can
reach `validate_config`'s `except ContractError` guard? **It does not.** A plugin-side **template**
collision is decided inside `_claims`, which `resolve_template` calls, so it arrives at that guard
as `E-TEMPLATE-COLLISION` — a code already counted. The three new codes are reported by checks that
do not raise into it: `E-PLUGIN-COLLISION` by the non-template collision check task 8 adds to
`validate_config`'s check list; `E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD` by helpers with no
production caller in Part A at all. So "Five faults" stays five and "two codes" stays two, and this
task writes the distinction down so the next reader does not increment a number that must not move.

**Why the four cases are not one code.** § Creating a plugin's paragraph puts five things in one
sentence: two installed plugins registering one name, a plugin registering `generic`, a plugin
claiming an extension core already writes, two local files registering one name, and a local file
taking an installed name. Three of those are **template** names and belong under
`E-TEMPLATE-COLLISION`, whose row already states the rule and the reason and whose message names
providers. The writer-suffix case is not a template name at all, and a reader who greps
`E-TEMPLATE-COLLISION` for a `.fastq.gz` fault finds a row about `templates/`. Hence
`E-PLUGIN-COLLISION` for the non-template groups.

- [ ] **Step 1: Read all three sites and confirm each still reads as measured.** § Creating a
      plugin's collision paragraph, § Errors core raises' `E-TEMPLATE-COLLISION` row, and § Errors
      `validate` reports' `E-TEMPLATE-COLLISION` row. Then read § Errors `validate` reports'
      early-return paragraph and count its enumerated faults — `E-CONFIG-PARSE`, container-shaped
      `E-CONFIG-SHAPE`, `E-TEMPLATE-LOAD`, `E-TEMPLATE-COLLISION`, `E-TEMPLATE-UNKNOWN` — five — and
      `validate.py`'s comment inside `validate_config`'s `except ContractError` guard, which reads
      "two codes". Confirm both, and change **neither**.

- [ ] **Step 2: Add three rows to § Errors core raises' table** (`| Raised by | Type · code |`).
      Place them after the row that reports **a project-local `templates/*.py` failing to load**,
      which is the nearest sibling by subject; name it that way and not by position.

```
| One entry-point key claimed by two installed distributions in [`publishable.resolvers`, `publishable.probes`, `publishable.writers` or `publishable.readers`](#creating-a-plugin-publishable-plugin-new), or a [writer](#steps-and-artifacts) claiming a suffix core itself writes. Decided over the **complete** claim set for the group and reported in **name order**, not in the order the metadata scan happened to walk one: install order is a property of a machine rather than of a design, so it may not decide which fault is reported either. The message names every distribution that claimed the key, as `<distribution> <version>`, which is what a reader uninstalls. The template groups' equivalent is `E-TEMPLATE-COLLISION` rather than this code, since a template name has a second home — [the project's own `templates/`](#templates-where-parameters-are-defined) — and one row cannot state both sets of providers | `ContractError` · `E-PLUGIN-COLLISION` |
| A [`@register_*` argument](#creating-a-plugin-publishable-plugin-new) disagreeing with the entry-point key that named it. The entry point is the registration and the decorator is a declaration checked against it, so two spellings of one name with no rule for which is canonical is refused rather than resolved — the [defaults-file argument](#there-is-no-separate-defaults-file) again. Reached only where the object behind a key is actually loaded, which is `run` and `dry-run`: `validate` answers a name from metadata and never holds the decorated object, so **`validate` cannot see this disagreement**, and that is a property of the guarantee rather than a gap in the check | `ContractError` · `E-PLUGIN-DECORATOR` |
| An entry point whose module raises while importing, or calls `sys.exit()` at module scope. `SystemExit` is a `BaseException` and so needs its own `except` — a plugin building an `argparse` parser at import would otherwise end the command with the plugin's own exit code and no diagnostic at all. Reached at the same two commands `E-PLUGIN-DECORATOR` is, and for the same reason: `validate` never imports a plugin. The fault names the entry point and the distribution rather than the module, since a distribution is what a reader uninstalls or pins | `ContractError` · `E-PLUGIN-LOAD` |
```

- [ ] **Step 3: Extend `E-TEMPLATE-COLLISION` to the three plugin cases, in both of its rows.** In
      § Errors core raises, replace the row's opening clause "A template name claimed twice as a
      repo's `templates/` is discovered and merged — two local registrations of one name, or a local
      registration of a name core itself registers" with:

```
| A template name claimed twice as core's own registry, an [installed distribution's](#creating-a-plugin-publishable-plugin-new) `publishable.templates` entry points, and a repo's [`templates/`](#templates-where-parameters-are-defined) are merged — two local registrations of one name, a local registration of a name core itself registers, two installed distributions registering one name, an installed distribution registering a name core itself registers, or a local registration of a name an installed distribution registers. Decided over the complete claim set from all three sources and reported in name order. An installed claimant is named as `<distribution> <version>`, a local one as `<path>::<ClassName>`, and core's own as its dotted class path — each being what a reader changes to resolve it. **An installed claimant is a name, never a class:** the claim is read from package metadata, so no plugin is imported to decide a collision, which is the guarantee [§ Creating a plugin](#creating-a-plugin-publishable-plugin-new) states and the reason a refused installed claim carries no credential to redact.
```

      In § Errors `validate` reports, **delete** the row's closing clause "A local name an
      **installed plugin** registers is the same fault and is not yet checked: no entry point is
      resolved in this build, so there is no second claimant for core to see" — the claim is now
      false and deleting it is preferred to rewriting it. Replace nothing; the row's opening, which
      task 8 amends, carries the cases.

- [ ] **Step 4: Amend § Creating a plugin's collision paragraph.** Its closing sentence reads "The
      two local cases are the ones this build checks, and `E-TEMPLATE-COLLISION` is the code all of
      them carry — the plugin cases arrive with entry-point resolution, and until then there is no
      installed template for a local one to collide with." Replace it with:

```
[`E-TEMPLATE-COLLISION`](#errors-validate-reports) is the code every **template** case carries and [`E-PLUGIN-COLLISION`](#errors-core-raises) is the code the other four groups carry, including a writer claiming a suffix core already writes: a template name has a second home in a project's own `templates/`, and one row cannot state both sets of providers.
```

      Do not add a build-state marker to that sentence: task 8 lands the check and task 5 owns the
      `NOT BUILT` sweep.

- [ ] **Step 5: Record that neither count moves.** In § Errors `validate` reports' early-return
      paragraph, immediately after the sentence beginning "That is five *codes*", add:

```
A plugin-side collision adds no sixth: an installed distribution's template claim is decided in the same merge a local one is, so it arrives here as `E-TEMPLATE-COLLISION` — a code already counted. The identifiers a plugin registry mints for its other groups ([`E-PLUGIN-COLLISION`](#errors-core-raises), `E-PLUGIN-DECORATOR`, `E-PLUGIN-LOAD`) are reported by checks that do not return early, so none of them reaches this list either.
```

- [ ] **Step 6: Mechanical pass** over every edited region: anchors resolve, table rows have exactly
      two cells, no trailing whitespace, no tab, no invisible unicode. Skip fenced blocks. Then
      **sweep the four documents by name** for `is not yet checked` and read each surviving hit —
      the ones this task did not delete belong to task 5.

- [ ] **Step 7: Verify.** `uv run pytest` → **1999 passed, 2 xfailed**. `uv run ruff format --check .`
      → 76 files, 0 to reformat.

- [ ] **Step 8: Mutation — none reaches this task, and the reason is worth stating.** Both count
      phrases are unpinnable: nothing in the suite reads `validate.py`'s comment text or
      `reference.md`'s "Five faults" sentence, so changing either number leaves all 1999 tests
      green. Do **not** manufacture a test that greps a document for a number. The three new rows
      are closed later — **`E-PLUGIN-COLLISION` by tasks 8 and 14**, which pin its message by
      fragment. **`E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD` are pinned by tasks 16 and 17 at the unit
      level only**, since neither has a production caller in Part A; no task in this slice reaches
      them end to end, and that is stated in those tasks rather than hidden here. The verification
      available here is step 1's re-read.

- [ ] **Step 9: Commit.** `docs: the four load-time refusals get identifiers, and neither count phrase moves`

---

## Task 3: Decision 2's fifth group — `publishable.readers`, settled and filed

**Files:** Modify `docs/reference.md`, `docs/superpowers/spec-defects.md`. No `src/` change, no test
change.

**Interfaces:**
- Consumes: § Creating a plugin's `[project.entry-points."publishable.writers"]` TOML block and the
  paragraph beginning **"Four registries, one mechanism"**, whose closing clause reads "it takes the
  object and returns `bytes`, and its reader inverts it"; § The importable surface's row whose
  `Name` cell is `register_resolver · register_probe · register_writer`.
- Produces: a fifth entry-point group `publishable.readers` and a fifth decorator `register_reader`,
  documented; and a `spec-defects.md` entry recording that the gap existed and is now closed by
  specification, with the code owed by tasks 14 and 15.

**The ruling and its grounds, from decision 2.** `io.write` dispatches on the longest registered
suffix and `StepIO._read` **inverts the same table** — its own docstring says so. The asymmetry is
what produces a bare `KeyError` for a third-party writer today, proved by mutation in the
re-scoping's § 5(a). `CLAUDE.md`'s invariant that *each core writer takes exactly what its reader
gives back* presumes a reader exists for every writer; a "stated convention" that a writer's entry
point resolves its own inverse would leave that invariant true of core and false of plugins. So:
**mint the fifth group.** Four registries become five, and § Creating a plugin's "Four registries,
one mechanism" heading sentence moves with it.

- [ ] **Step 1: Read before writing.** Read § Creating a plugin's four TOML entry-point blocks and
      the "Four registries, one mechanism" paragraph in full. Read § Steps and artifacts' sentence
      about `io.write`'s dispatch. Confirm the gap is still unfiled:
      `grep -n "publishable.readers" docs/superpowers/spec-defects.md` → exit 1, with
      `grep -n "register_resolver" docs/superpowers/spec-defects.md` → six hits as the can-fail
      control on the identical file.

- [ ] **Step 2: Add the fifth TOML block** to § Creating a plugin's `pyproject.toml` example,
      immediately after the `publishable.writers` block:

```toml
[project.entry-points."publishable.readers"]
".fastq.gz" = "publishable_my_assay.writers.fastq:read"
```

- [ ] **Step 3: Rewrite the "Four registries" paragraph's opening.** Replace **"Four registries, one
      mechanism.** Templates, [resolvers](#where-units-come-from),
      [probes](#the-apparatus-core-can-only-observe), and [writers](#steps-and-artifacts) are each an
      entry-point group and a `@register_*` decorator" with:

```
**Five registries, one mechanism.** Templates, [resolvers](#where-units-come-from), [probes](#the-apparatus-core-can-only-observe), [writers and readers](#steps-and-artifacts) are each an entry-point group and a `@register_*` decorator
```

      and replace the paragraph's closing clause "it takes the object and returns `bytes`, and its
      reader inverts it" with:

```
it takes the object and returns `bytes`, and its reader inverts it — which is a fifth group rather than a convention, because [`io.write` dispatches on the writer table and `io.read_upstream` indexes the reader table](#steps-and-artifacts), so a suffix present in one and absent from the other is a promise core cannot keep. A writer registered without its reader is refused at load for that reason, the same breath in which a suffix core already writes is.
```

- [ ] **Step 4: Split § The importable surface's `not yet built` row into two.** The existing row's
      `Name` cell reads `register_resolver · register_probe · register_writer`. Replace that one row
      with two, keeping the `Kind`, `Status` and `Is` columns' shape:

```
| `register_resolver` · `register_probe` | decorator | not yet built | Two more of the five plugin registries — see [Creating a plugin](#creating-a-plugin-publishable-plugin-new) |
| `register_writer` · `register_reader` | decorator | not yet built | The registries an artifact suffix is claimed through, in the pair `io.write` and `io.read_upstream` require — see [Creating a plugin](#creating-a-plugin-publishable-plugin-new) |
```

      **Splitting the row is what keeps the sentence "Importing one raises `ImportError` today"
      true**, because that sentence derives its claim from the `Status` column rather than from an
      enumeration of names. Do not replace it with a list. Tasks 12, 13, 14 and 15 each move a
      `Status` cell as their name lands; this task moves none.

- [ ] **Step 5: Update the paragraph immediately under § The importable surface's fenced import
      example** if it says "four" anywhere, and re-read the sentence "One of the four plugin
      registries" in `register_template`'s own row — it must become "One of the five plugin
      registries". Sweep the four documents by name for `four plugin registries` and
      `Four registries`, read each hit, and fix every one. Can-fail control: the same sweep for
      `plugin registries` must return strictly more hits.

- [ ] **Step 6: File it.** Append to `docs/superpowers/spec-defects.md`:

```markdown
## STRUCK 2026-08-16 — `publishable.readers` had no entry-point group, so a third-party writer had no reader

**Was:** § Creating a plugin declared four entry-point groups and said of a writer "its reader
inverts it", with no mechanism for supplying one. `artifacts.WRITERS` and `artifacts.READERS` are
two module dicts, `io.write` dispatches through `_suffix_for`, which iterates `WRITERS` alone, and
`StepIO._read` indexes `READERS` — so a suffix registered as a writer and not as a reader gives
`io.read_upstream` a bare `KeyError` rather than a coded `ArtifactError`. Proved by mutation
(`H7b-SCOPING-2.md` § 5a): adding one key to `WRITERS` alone reproduced it, and deleting the key
restored the read. Filed here for the first time — `H7c` task 14 filed four entries in this family
and none of them was this one.

**Closed by specification** in H7b Part A task 3: a fifth group `publishable.readers` and a fifth
decorator `register_reader`, with `register_writer` refusing a suffix that has no reader. The code
is owed by tasks 14 and 15 of the same slice; this entry is struck when task 15 lands, not before.
```

      Note the entry is written as STRUCK-on-landing rather than OPEN: it is closed in the document
      by this task and in the code by task 15. **Task 15's last step re-reads this entry and
      confirms the strike is honest.** Use `git add -f` when committing, per `CLAUDE.md`.

- [ ] **Step 7: Mechanical pass** over § Creating a plugin and § The importable surface: anchors
      resolve, the two new table rows have exactly four cells each, TOML fence closes, no trailing
      whitespace, no tab, no invisible unicode. `spec-defects.md` is development record — the
      cross-document pass does not govern it, the mechanical one does.

- [ ] **Step 8: Verify.** `uv run pytest` → **1999 passed, 2 xfailed**. The § The importable surface
      table is read by no test at this commit; confirm that by running `uv run pytest tests/test_cli.py -q`
      and observing it green, since that file is the one that parses `reference.md` tables and it
      parses the **CLI** tables, not this one.

- [ ] **Step 9: Mutation — none reaches this task.** Every deliverable is a document sentence or a
      defects entry. The `Status` cells stay `not yet built`, so nothing changed behaviour and no
      test can go red. **Task 15 closes it**: it builds `register_reader`, enforces the symmetry, and
      its own test pins the refusal's message. Stated rather than manufactured.

- [ ] **Step 10: Commit.** `docs: mint the publishable.readers group, and file the gap it closes`

---

## Task 4: § Package layout + § The importable surface — a home for the shared scan

**Files:** Modify `docs/reference.md`. No `src/` change, no test change. **Its § Package layout
marker is retired inside task 7's commit** — see the ordering note.

**Interfaces:**
- Consumes: § Package layout's fenced tree, whose lines are `│   ├── <file> # <description>` and
  whose entries marked `— not yet built` are specified-and-unbuilt; the paragraph beneath it
  beginning "**Modules marked `— not yet built` are specified and unbuilt.**"
- Produces: a `plugins.py` line in that tree, marked `— not yet built` at this commit; and the
  statement in § The importable surface that the scan is core's own and reaches a user through no
  import.

**Ordering note the implementer must respect, and it is copied from H7c's tasks 6/7 because it is
the same shape.** § Package layout's marker means "specified and unbuilt", so retiring it is a
**build claim**. Add the line **with** its marker here; **retire the marker as the last step of task
7, in task 7's own commit**, so the document never claims a module that is not there. This task's
step 3 is therefore explicitly deferred and task 7 executes it. Recorded in both tasks so a reader
of either finds it.

- [ ] **Step 1: Read the tree and pick the insertion point by neighbour, not by position.** The
      entry for `param.py` reads `│   ├── param.py # Param: type, default, constraints, help`, and
      `envelope.py` follows it. `plugins.py` belongs beside the modules that answer "what is
      installed", not beside the config machinery — put it immediately after the `manifest.py` line,
      which is the nearest entry that is also about what the machine supplies rather than what the
      config declares. Name that neighbour in your commit message.

- [ ] **Step 2: Add the line.** Keep the column alignment of its neighbours exactly — the tree is a
      fenced block and `ruff format` does not touch it, so misalignment survives to the reader:

```
│   ├── plugins.py             # entry-point metadata scan; the resolver/probe/writer/reader registries — not yet built
```

      Note what the comment does **not** say: it does not enumerate the groups' names and it does
      not say "five". A count in a comment goes stale; what the set *is* is "the registries that are
      not templates'", and the templates' own registry stays in `templates/{base,registry,discovery}`
      where the tree already puts it.

- [ ] **Step 3: DEFERRED to task 7's last step.** Retiring `plugins.py`'s `— not yet built` marker.
      Do not do it here; the module does not exist at this commit.

- [ ] **Step 4: State that the scan is not an import.** In § The importable surface, after the
      paragraph beginning "**Not everything core adds is a name on this table, and the credential
      mechanism is the example.**", add:

```
**The five plugin registries move this table; the machinery behind them does not.** `@register_resolver` and its siblings are names you import and decorate with, so each has a row. What resolves those names — a scan of installed package metadata, run by core before your code exists — reaches you through no import at all, and the module holding it is [core's own source](#package-layout) rather than a name on this list. That is the same boundary `cfg` and `io` sit on: constructed by core, handed to you, never imported.
```

- [ ] **Step 5: Mechanical pass** over both edited regions: anchors resolve (`#package-layout`), the
      fenced tree's box-drawing characters are `│`, `├──` and `└──` as its neighbours use, no
      trailing whitespace, no tab, no invisible unicode. Skip fenced blocks for the table/heading
      checks but **do** check the tree line's trailing whitespace by hand, since it lives inside a
      fence and the whitespace rule is unconditional in this repo.

- [ ] **Step 6: Verify.** `uv run pytest` → **1999 passed, 2 xfailed**.

- [ ] **Step 7: Mutation — none reaches this task, and one later task partly closes it.** § Package
      layout is read by no test. The `— not yet built` markers in it are not bound to `src/`'s
      contents by anything. **Task 7 closes the half that matters**: it creates `src/publishable/plugins.py`
      and retires this line's marker in the same commit, so a marker retired against a module that
      does not exist would be caught by task 7's own import in its test file. The paragraph added in
      step 4 is unpinnable and stays that way; **nothing closes it.** Stated, not papered over.

- [ ] **Step 8: Commit.** `docs: plugins.py gets a home in the tree, marked unbuilt until task 7`

---

## Task 5: The `NOT BUILT` markers and the enum comments

**Files:** Modify `docs/reference.md`, `src/publishable/materialize.py`, `tests/test_materialize.py`.

**Interfaces:**
- Consumes: § The one config file's identifying-fields paragraph, which begins "**The four
  identifying fields above `metadata` say what this config is written against**" and contains the
  clause "the plugin case is not yet checked, since no entry point is resolved in this build";
  `materialize.py`'s `data.units.from` line, which today renders
  `'    from: index.csv                # index.csv | {glob: "*.dcm"}'`; § The one config file's own
  `from:` line, which renders `# index.csv | {glob: "*.dcm"} | {resolver: <name>} (NOT BUILT)`;
  § Where units come from's second `from` enum, which is the three-line fenced YAML block showing
  `from: index.csv`, `from: {glob: "*.dcm"}` and `from: {resolver: plate_wells}`.
- Produces: the generated config's `from` comment listing **every** value § The one config file
  defines, with the unbuilt one marked; and the identifying-fields clause corrected.

**What this task does NOT retire, and why each is somebody else's.** § The one config file's
"**Two** declarations above are not yet built" and the `from:` line's own `(NOT BUILT)` are **Part
B's**, retired by task 24 with the refusal. § Errors' `E-TEMPLATE-COLLISION` clause was deleted by
task 2. § Errors' `E-TEMPLATE-UNKNOWN` clause is **task 11's**. § Creating a plugin's "The two local
cases" sentence was rewritten by task 2. § The importable surface's three-name row was split by task
3. § CLI reference's `plugin new` and `list-templates` rows and § Package layout's
`plugin_scaffold.py` stay `NOT BUILT` — the first two are Part B task 21's and the third with them.
§ Creation commands' and § Generators' `--plugin` claims are **task 6's**. Sweep for each of those
strings and confirm you left it alone rather than assuming.

**The live defect this task closes.** Re-probed by generating a real config: `reference.md` writes
`# index.csv | {glob: "*.dcm"} | {resolver: <name>} (NOT BUILT)` while `materialize.py` writes
`# index.csv | {glob: "*.dcm"}` — **two values where the document defines three**. The enum-comment
rule is a cross-document invariant, and nothing in the suite pins that line: `grep -rn 'glob' tests/`
returns only `Path.glob` calls, so this line has been wrong and green.

**Names already at module level in `tests/test_materialize.py`:** `rendered`, `_MARKED_LATER_SLICE`,
`_MARKED_FIELD_PATHS`, `_refusal_codes`, `_rendered_with_default`, `_rendered_with_keys`, plus the
`test_*` functions. Add no helper; extend an existing test.

- [ ] **Step 1: Write the failing assertions.** In `tests/test_materialize.py`, replace the body of
      `test_the_generated_units_block_carries_its_comments` with:

```python
def test_the_generated_units_block_carries_its_comments():
    """The `from` enum lists every value § The one config file defines, and marks
    the one this build refuses.

    Two values where the document defines three was live and green until this
    test: nothing else in the suite reads this line. The `(NOT BUILT)` marking is
    asserted *with* a refusal below rather than alone, because a marking core does
    not honour is exactly as misleading as a missing one.
    """
    text = rendered()
    assert '# index.csv | {glob: "*.dcm"} | {resolver: <name>} (NOT BUILT)' in text
    assert "# within | between" in text
```

      and append, beside it:

```python
def test_the_from_enum_s_not_built_marking_is_honoured_by_core(git_repo, tmp_path):
    """The marking is a claim about behaviour, so it is checked against behaviour.

    `_MARKED_FIELD_PATHS`'s `(x: later slice)` convention cannot carry this one —
    its regex reads a single unqualified value and `{resolver: <name>}` holds a
    colon — so the `(NOT BUILT)` spelling § The one config file already uses is
    what `init` writes, and this is its honesty check. Asserted *alongside* the
    wholesale refusal rather than on the whole code set, so retiring
    `E-DATA-RESOLVER-UNSUPPORTED` is a one-line deletion here.
    """
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "index.csv").write_text("patient_id\np1\n")

    text = materialize_config(
        template=get_template("generic"),
        template_name="generic",
        name="cohort-pilot",
        input_dir=str(input_dir),
        output_dir=str(tmp_path / "output"),
        entrypoint="cohort_pilot.experiment:CohortPilotExperiment",
    )
    doc = yaml.safe_load(text)
    doc["metadata"]["description"] = "a pilot"
    doc["metadata"]["authors"] = ["A"]

    config_path = git_repo / "configs" / "cohort-pilot" / "config.yaml"
    config_path.parent.mkdir(parents=True)

    # The value `init` actually writes validates clean — the positive companion,
    # without which the refusal below could pass on an unrelated fault.
    assert _refusal_codes("from", doc, config_path) == []

    doc["data"]["units"]["from"] = {"resolver": "plate_wells"}
    assert "E-DATA-RESOLVER-UNSUPPORTED" in _refusal_codes("from", doc, config_path)
```

- [ ] **Step 2: Run and see it fail.** `uv run pytest tests/test_materialize.py -q`.
      `test_the_generated_units_block_carries_its_comments` must fail on the three-value string.
      The second test must **pass already** — it asserts today's behaviour, and it is here as the
      honesty half of the marking rather than as a new refusal. If it fails, the brief is stale and
      the refusal moved; stop and say so.

- [ ] **Step 3: Implement.** In `src/publishable/materialize.py`, replace the `from` line:

```python
        '    from: index.csv                # index.csv | {glob: "*.dcm"} '
        "| {resolver: <name>} (NOT BUILT)",
```

      Two source lines, one rendered line — the file's line-length limit is 100 and the joined
      string is longer. Confirm the rendered output has exactly one `#` on that line and no double
      space where the two fragments meet.

- [ ] **Step 4: Run and see it pass.** `uv run pytest tests/test_materialize.py -q`, then the whole
      suite: **1999 + 1 new test passed, 2 xfailed.**

- [ ] **Step 5: Correct the identifying-fields clause.** In § The one config file, the sentence
      beginning "`experiment_type` names the template and must resolve to one core, an installed
      plugin, or this project's own `templates/` registers" continues "— the plugin case is not yet
      checked, since no entry point is resolved in this build, the same disclosure
      [`E-TEMPLATE-UNKNOWN`](#errors-validate-reports) carries". **Delete that clause**, leaving the
      sentence to read "…or this project's own `templates/` registers;". Deleting rather than
      rewriting: the disclosure it points at is task 11's to replace, and propagating a claim to a
      second site is how a previous round closed a false-claim finding by making it worse.

- [ ] **Step 6: Confirm § Where units come from's enum is already total.** Its fenced YAML shows all
      three `from` forms. Read it and change nothing — it is the reference the two comment spellings
      are checked against, and it was correct.

- [ ] **Step 7: Mechanical pass** over § The one config file's edited paragraph: anchors resolve, no
      trailing whitespace, no tab, no invisible unicode, no en dash. Then **sweep the four documents
      by name** for `no entry point is resolved in this build` and read every surviving hit —
      exactly one must remain, in § Errors `validate` reports' `E-TEMPLATE-UNKNOWN` row, which is
      task 11's. Can-fail control: the same sweep before your edit returns strictly more.

- [ ] **Step 8: Verify.** All four commands. `uv run ruff format --check .` → 76 files, 0 to
      reformat — `materialize.py`'s two-line string must be formatted as `ruff` wants it, so run
      `uv run ruff format .` and then `--check` and confirm the diff is only your line.

- [ ] **Step 9: Mutate — one, and it discriminates.** In `materialize.py`, drop the second fragment
      so the line renders `# index.csv | {glob: "*.dcm"}` again.
      `test_the_generated_units_block_carries_its_comments` must FAIL on its first assertion.
      **Checked against the test body:** the assertion is an `in` over the full three-value literal,
      which the two-value render cannot contain. Then revert by editing the file back, delete
      `__pycache__`, re-run, confirm green.

      A second mutation is available and **cannot discriminate**, so do not use it: changing
      `(NOT BUILT)` to `(NOT-BUILT)` fails the same assertion for the same reason and proves nothing
      the first does not. The marking's *honesty* is what the second test covers, and its mutation
      lives in Part B: retiring `E-DATA-RESOLVER-UNSUPPORTED` without retiring the marking makes
      `test_the_from_enum_s_not_built_marking_is_honoured_by_core` go red, which is the coupling it
      exists to create.

- [ ] **Step 10: Which deliverable no mutation reaches.** The § The one config file clause deleted
      in step 5 is prose and nothing pins it; **nothing in this slice closes that**, and task 11's
      companion deletion is in the same position. Stated rather than papered over.

- [ ] **Step 11: Commit.** `fix: init's from comment lists every value the schema defines, and marks the unbuilt one`

---

## Task 6: Decision 5's honest marking of `--plugin`

**Files:** Modify `docs/reference.md`. No `src/` change, no test change.

**Interfaces:**
- Consumes: § CLI reference § Creation commands' row whose first cell is
  `` `publishable generate` (`g`) `` and whose `Notes` cell ends "`experiment` accepts `--plugin`";
  § Generators' row whose first cell is `` `experiment` ``; § Plugins' opening paragraph, whose
  second sentence reads "`--plugin <github-username>/<repo>` runs
  `uv add git+https://github.com/<user>/<repo>` and nothing more."
- Produces: all three correct **at this commit**, where `--plugin` is accepted and silently dropped.
  **Task 18 makes them true and reverts this task's markings**, and each edit here names task 18 in
  its own commit message so the pair is findable from either end.

**Decision 5's ruling, and why the marking comes first.** Probed at `ff51864`:
`publishable generate experiment p2 --template generic --plugin someuser/publishable-llm …` exits 0,
writes `plugin: null`, and installs nothing — `grep -rn "uv add" src/` is empty, with
`grep -rln "uv_lock" src/` returning `cli.py` and `uv_support.py` as the can-fail control. Both
document claims are false today. The `Status` column is this repo's own device for exactly that
distinction, and correcting a row before the feature lands rather than after is what the column is
for. **This survives a green suite** because `tests/test_cli.py`'s CLI-table test asserts set
equality between the documents' `NOT BUILT` rows and `cli.NOT_BUILT_COMMANDS` and says nothing about
the arguments column — so **neither this task's edit nor task 18's is pinned by a test**, and both
say so.

**Do not mark the `generate` command row itself `NOT BUILT`.** `generate experiment` is built; one
of its flags is not. Marking the row would fail the CLI-table test, which reads the `Status` cell
and compares it against `cli.NOT_BUILT_COMMANDS`, and would be false besides.

- [ ] **Step 1: Re-probe rather than trust this brief.** In a scratch directory outside the repo,
      `uv run publishable new proj`, then inside it
      `uv run publishable generate experiment p2 --template generic --plugin someuser/publishable-llm --input-dir <outside> --output-dir <outside>`;
      confirm exit 0 and `plugin: null` in the generated config. Run `grep -rn "uv add" src/` and
      its control. Record both in the task report. If either has changed, stop.

- [ ] **Step 2: Mark § Creation commands' `generate` row.** Its `Notes` cell ends with
      "`experiment` \| `step` \| `template` \| `report` (NOT BUILT); `experiment` accepts
      `--plugin`". Replace the trailing clause so it reads:

```
`experiment` \| `step` \| `template` \| `report` (NOT BUILT); `experiment` accepts `--plugin` (NOT BUILT — the flag parses and is dropped)
```

      **Check the CLI-table test still passes before going further**: it asserts
      `(f"`{kind}` (NOT BUILT)" in text) == (status == "NOT BUILT")` for each **generator** kind
      parsed out of the § Generators table, and `--plugin` is not a generator kind, so this addition
      must not perturb it. Run `uv run pytest tests/test_cli.py -q` at this step, not at the end.

- [ ] **Step 3: Mark § Generators' `experiment` row.** Its `Produces` cell ends "Adding a row to the
      README's managed experiments table is NOT BUILT — the same half `generate template` does not
      write either". Append one sentence to that cell:

```
`--plugin` is accepted and dropped: the flag parses, nothing is installed, and `plugin:` is written `null` — NOT BUILT, and the [`plugin` field](#the-one-config-file) is a readable note rather than an install instruction in either case.
```

- [ ] **Step 4: Mark § Plugins' opening claim.** Replace its second sentence with:

```
`--plugin <github-username>/<repo>` runs `uv add git+https://github.com/<user>/<repo>` and nothing more — **NOT BUILT** in this build, where the flag parses and is dropped. No registry, no bespoke installer, no new trust boundary beyond "this is a git dependency," because it is one. Pin however `uv` supports: `--plugin someuser/publishable-llm@v1.2.0`.
```

      Keep the rest of the paragraph untouched — the pinning sentence is part of the specification
      and stays present tense.

- [ ] **Step 5: `--plugin` is legal, and say why once.** A reader who has just read
      § Operation commands will read a flag on `generate` as a violation. Immediately after the
      sentence you edited in step 4, add:

```
A flag here rather than a field in the file is not the exception it looks like: [operation commands](#operation-commands) take paths and nothing else, and `generate` is a **creation** command — the file it would read does not exist yet, which is the whole distinction that rule draws.
```

- [ ] **Step 6: Mechanical pass** over all three edited regions: anchors resolve
      (`#the-one-config-file`, `#operation-commands`), each edited table row still has its header's
      column count, the escaped pipes `\|` inside table cells are preserved, no trailing whitespace,
      no tab, no invisible unicode.

- [ ] **Step 7: Verify.** All four commands. `uv run pytest` → **1999 passed, 2 xfailed** (task 5
      added one, so **2000 passed** if task 5 has landed — state the number you actually see against
      the number your predecessor task left).

- [ ] **Step 8: Mutation — none reaches this task, and the reason is a finding worth carrying.**
      `tests/test_cli.py`'s CLI-table test binds **command names and `Status` markers**, not the
      `Arguments` or `Notes` cells. Deleting every word this task wrote leaves the suite green.
      **Task 18 closes it in one direction only**: it builds `uv add` and the `plugin` field and
      reverts these markings, and its own tests pin the behaviour — but nothing then pins that the
      markings were removed. Do **not** add a test that greps a document cell for `NOT BUILT`; that
      converts a self-maintaining `Status` column into a second source of truth. **Record in the
      commit message that task 18 reverts these three edits**, which is the only mechanism that
      keeps them from outliving the flag.

- [ ] **Step 9: Commit.** `docs: --plugin is marked NOT BUILT until task 18 builds it`

---

## Task 7: The entry-point metadata scan, five groups, no `.load()`

**Files:** Create `src/publishable/plugins.py`, `tests/test_plugins.py`. Modify `tests/conftest.py`,
`docs/reference.md` (§ Package layout's marker, deferred from task 4).

**Interfaces:**
- Consumes: `importlib.metadata.entry_points(group: str) -> EntryPoints` — the 3.10+ selection API,
  read from the stdlib; `EntryPoint` carries `.name`, `.value`, `.group` and `.dist`, where `.dist`
  is a `Distribution | None` carrying `.name` and `.version`. **`EntryPoint.load()` exists and is
  never called by this module.**
- Produces, consumed by tasks 8, 9, 11, 13, 14, 15, 16, 17 and 20:
  - `GROUPS: tuple[str, ...]` — every entry-point group core reads.
  - `scan_group(group: str) -> dict[str, list[EntryPoint]]` — keys sorted by name, providers within
    a key sorted by provider string. **Metadata only.**
  - `provider_of(ep: EntryPoint) -> str` — `"<distribution> <version>"`, the string every collision
    message names a claimant by.
  - `names(group: str) -> list[str]` — sorted keys of `scan_group(group)`.

**The guarantee this module exists to keep, stated once.** § Creating a plugin justifies the entry
point mechanism by "core resolves it from installed package metadata — so `validate` can answer 'no
installed package registers `plate_wells`' without importing a line of that package". Decision 3
states that invariant of **resolution**, not merely of the negative answer. So no function in this
module calls `.load()`, and no caller added in Part A does either. A check that reaches for the
object behind a name has changed the guarantee whatever it returns.

**The fixture, and what it costs.** See Global Constraints for the full argument and the four
mechanical rules. In short: a directory holding a hand-written `<name>-<version>.dist-info/` with
`METADATA` and `entry_points.txt`, prepended to `sys.path` with `monkeypatch.syspath_prepend`, **is**
an installed distribution to every API this module calls — that is the layout `uv` and `pip` write
and the layout `importlib.metadata` scans for. It costs no build step, no network, no `slow` marker,
no mutation of the project venv, and no new dependency in `pyproject.toml`. It does not exercise
`hatchling` turning a `pyproject.toml` entry-points table into `entry_points.txt`; core reads no
`pyproject.toml`, so that is outside anything a test here could pin, and it is named as a residual
rather than left implicit.

**The fixture goes in `tests/conftest.py`, not in `tests/test_plugins.py`.** Tasks 8, 13, 14, 15, 16
and 17 all need it and three of them write in `tests/test_templates.py` and `tests/test_validate.py`;
a fixture defined in one test module is not visible from another. **Names already at module level in
`tests/conftest.py`:** `_restore_environ`, `git`, `EXPERIMENT_MODULE`, `write_experiment_module`,
`git_repo`. `installed` and `_DIST_METADATA` are free. It is a **plain fixture requested by name**,
never autouse — the suite already has the only autouse fixture it is allowed, and adding a second is
forbidden by Global Constraints. `tests/test_conftest_helpers.py` imports `git` from this module and
asserts on `git_repo`; it must stay green untouched.

- [ ] **Step 1a: Add the fixture to `tests/conftest.py`.** Append:

```python
_DIST_METADATA = """\
Metadata-Version: 2.1
Name: {name}
Version: {version}
"""


@pytest.fixture
def installed(tmp_path: Path, monkeypatch):
    """Write a real installed distribution and put it where `importlib.metadata` looks.

    A `<name>-<version>.dist-info/` holding `METADATA` and `entry_points.txt` is
    exactly what `uv` and `pip` write, and `importlib.metadata` finds a
    distribution by scanning each `sys.path` entry for one — so this exercises
    the real discovery path rather than a patch of `entry_points`. What it does
    not exercise is a build backend turning a `pyproject.toml` entry-points table
    into `entry_points.txt`; core reads no `pyproject.toml`, so that translation
    is outside anything a test here could pin.

    Each call gets its own directory. `importlib.metadata`'s path cache is keyed
    on a directory and its mtime, so adding a second `.dist-info` to a directory
    already scanned in the same test can be served from cache; two distributions
    therefore means two calls and two directories.

    A plain fixture rather than an autouse one, and requested by name:
    `monkeypatch.syspath_prepend` already restores `sys.path` per test, and the
    environ fixture above is the only autouse fixture this suite has.
    """
    made = 0

    def _install(dist_name: str, version: str, groups: dict[str, dict[str, str]]) -> Path:
        nonlocal made
        made += 1
        site = tmp_path / f"site{made}"
        info = site / f"{dist_name.replace('-', '_')}-{version}.dist-info"
        info.mkdir(parents=True)
        (info / "METADATA").write_text(_DIST_METADATA.format(name=dist_name, version=version))
        (info / "entry_points.txt").write_text(
            "".join(
                f"[{group}]\n" + "".join(f"{k} = {v}\n" for k, v in entries.items()) + "\n"
                for group, entries in groups.items()
            )
        )
        monkeypatch.syspath_prepend(str(site))
        importlib.invalidate_caches()
        return site

    return _install
```

      and add `import importlib` to the file's existing import block (`os`, `subprocess`,
      `pathlib.Path`, `pytest` today), keeping `ruff`'s `I` rule happy.

- [ ] **Step 1b: Write the failing tests.** Create `tests/test_plugins.py`:

```python
# tests/test_plugins.py
import pytest

from publishable.plugins import GROUPS, names, provider_of, scan_group


def test_the_groups_core_reads_are_the_five_the_document_declares():
    """Named rather than counted: `reference.md` § Creating a plugin shows one
    `[project.entry-points."publishable.*"]` block per registry."""
    assert set(GROUPS) == {
        "publishable.templates",
        "publishable.resolvers",
        "publishable.probes",
        "publishable.writers",
        "publishable.readers",
    }


def test_an_absent_group_is_empty_and_a_present_one_is_not(installed):
    """The control and its positive companion in one test: an empty answer proves
    nothing on a machine where no plugin is installed, so the same call must
    return something once a distribution declares it."""
    assert scan_group("publishable.resolvers") == {}
    installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "pkg_one.r:resolve"}})
    found = scan_group("publishable.resolvers")
    assert list(found) == ["plate_wells"]
    assert found["plate_wells"][0].value == "pkg_one.r:resolve"


def test_a_scan_selects_its_own_group_only(installed):
    installed(
        "dist-one",
        "1.0",
        {
            "publishable.resolvers": {"plate_wells": "pkg_one.r:resolve"},
            "publishable.probes": {"assay_instrument": "pkg_one.p:probe"},
            "console_scripts": {"whatever": "pkg_one.cli:main"},
        },
    )
    assert list(scan_group("publishable.resolvers")) == ["plate_wells"]
    assert list(scan_group("publishable.probes")) == ["assay_instrument"]
    assert scan_group("publishable.writers") == {}


def test_two_distributions_claiming_one_name_both_arrive(installed):
    """The metadata scan reports every claimant; deciding between them is the
    collision check's job and not this function's. Two distributions, because one
    cannot produce this arrangement at all."""
    installed("dist-two", "2.0", {"publishable.resolvers": {"plate_wells": "pkg_two.r:resolve"}})
    installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "pkg_one.r:resolve"}})
    providers = [provider_of(ep) for ep in scan_group("publishable.resolvers")["plate_wells"]]
    assert providers == ["dist-one 1.0", "dist-two 2.0"]


def test_names_are_sorted_and_the_sort_is_not_the_install_order(installed):
    """`zz_first` is installed first and sorts last; `aa_second` is installed
    second and sorts first. Two names in one arrangement cannot tell sorted order
    from insertion order — with two, the reverse of insertion IS sorted for one
    arrangement — so three names are declared and their install order is neither
    sorted nor reverse-sorted.
    """
    installed(
        "dist-order",
        "1.0",
        {
            "publishable.resolvers": {
                "zz_first": "pkg.r:a",
                "aa_second": "pkg.r:b",
                "mm_third": "pkg.r:c",
            }
        },
    )
    assert names("publishable.resolvers") == ["aa_second", "mm_third", "zz_first"]


def test_the_scan_imports_nothing(installed, monkeypatch):
    """The whole argument for entry points, asserted rather than described.

    The entry point points at a module that does not exist, so any `.load()` —
    core's or a caller's — raises `ModuleNotFoundError`. The scan returning
    normally is the proof, and the second half proves the fixture could have
    caught one: calling `.load()` on the very object the scan returned raises.
    """
    installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "no_such_module:resolve"}}
    )
    found = scan_group("publishable.resolvers")
    assert provider_of(found["plate_wells"][0]) == "dist-one 1.0"

    with pytest.raises(ModuleNotFoundError):
        found["plate_wells"][0].load()
```

- [ ] **Step 2: Run and see it fail.** `uv run pytest tests/test_plugins.py -q` →
      `ModuleNotFoundError: No module named 'publishable.plugins'`.

- [ ] **Step 3: Implement.** Create `src/publishable/plugins.py`:

```python
"""Entry-point discovery for the registries a plugin declares.

docs/reference.md § Creating a plugin. Every name a config can write for a
plugin artifact resolves through this module, and it resolves from **package
metadata**: nothing here calls `EntryPoint.load()`, and nothing that calls this
module may either. That is not a performance choice. § Creating a plugin
justifies the whole entry-point mechanism by `validate` being able to answer
"no installed package registers `plate_wells`" without importing a line of that
package, and `validate` is documented as creating nothing and reaching nothing
off the machine. A check that reaches for the object behind a name has changed
the guarantee whatever it returns.

The cost of that, stated rather than discovered: a claim read from metadata is a
name and a provider and nothing else. A refusal computed from it therefore has
no class to interrogate — no `parameter_spec`, no `required_env` — which is why
a plugin-side collision cannot redact a credential the way a project-local one
can. See `templates/registry.py` and § Creating a plugin for that residual.

Templates are scanned through here like everything else, but they are *merged*
in `templates/registry.py`, because a template name has a second home — a
project's own `templates/` — and the merge is the one place holding all three
sources at once.
"""

from importlib.metadata import EntryPoint, entry_points

GROUPS = (
    "publishable.templates",
    "publishable.resolvers",
    "publishable.probes",
    "publishable.writers",
    "publishable.readers",
)
"""Every entry-point group core reads, one per registry § Creating a plugin declares."""


def provider_of(ep: EntryPoint) -> str:
    """What a reader uninstalls or pins, which is a distribution rather than a module.

    Falls back to the entry point's own target only when `entry_points()` handed
    back an unattached object, which its own construction does not produce — kept
    so a message can never interpolate `None`.
    """
    dist = ep.dist
    if dist is None:  # pragma: no cover - entry_points() always attaches one
        return ep.value
    return f"{dist.name} {dist.version}"


def scan_group(group: str) -> dict[str, list[EntryPoint]]:
    """Every claim on every key in `group`, keyed by the key a config writes.

    A list per key rather than a single entry point, because two installed
    distributions claiming one key is a fault to *report* — naming both — rather
    than one to resolve by whichever the scan walked first. Keys come back in
    name order and claimants in provider order for the same reason: install order
    is a property of a machine, so it may not decide what a message says either.
    """
    found: dict[str, list[EntryPoint]] = {}
    for ep in entry_points(group=group):
        found.setdefault(ep.name, []).append(ep)
    return {name: sorted(found[name], key=provider_of) for name in sorted(found)}


def names(group: str) -> list[str]:
    """The keys `group` registers, in name order."""
    return list(scan_group(group))
```

- [ ] **Step 4: Run and see it pass.** `uv run pytest tests/test_plugins.py -q`, then the whole
      suite: **the count your predecessor left, plus 6.** `uv run mypy` must be clean — probed
      against this exact shape under `strict = true` over `files = ["src"]` and it is; `EntryPoint`
      and `EntryPoints` are typed in the stdlib, so **no `[[tool.mypy.overrides]]` is expected**. If
      one is reported anyway, add `module = "importlib.metadata"` with `ignore_missing_imports = true`
      and **say so in the task report** — the contingency is named here so it is not discovered.

- [ ] **Step 5: Retire task 4's marker, in this commit.** In § Package layout, delete
      `— not yet built` from the `plugins.py` line so it reads:

```
│   ├── plugins.py             # entry-point metadata scan; the resolver/probe/writer/reader registries
```

      Deferred from task 4 for the reason task 4 states: the marker means "specified and unbuilt",
      so retiring it is a build claim and belongs in the commit that makes it true.

- [ ] **Step 6: Mechanical pass** over the § Package layout edit: the tree line's alignment matches
      its neighbours, no trailing whitespace introduced.

- [ ] **Step 7: Mutate — three, each with the test that must go red, each checked against the test
      body.**

  **(a) Return in walk order instead of name order.** In `scan_group`, change the return to
  `{name: found[name] for name in found}`. `test_names_are_sorted_and_the_sort_is_not_the_install_order`
  must FAIL. **Checked against the test body:** its fixture declares three names whose declaration
  order (`zz_first`, `aa_second`, `mm_third`) is neither sorted nor reverse-sorted, so the mutant's
  output differs from the asserted list under either candidate reading. A two-name fixture would
  **not** discriminate — with two names the reverse of insertion order is sorted order for one
  arrangement — which is why the fixture has three.

  **(b) Keep one claimant per name.** Change the accumulation to `found[ep.name] = [ep]`.
  `test_two_distributions_claiming_one_name_both_arrive` must FAIL: it asserts a two-element list of
  providers, and the mutant yields one. **Checked against the test body:** the fixture installs two
  distributions in two directories, so both claims genuinely reach the scan; a one-distribution
  fixture could not tell this mutant from correct code.

  **(c) Sort claimants by something that is not the provider.** Change the inner sort key to
  `lambda ep: ep.value`. `test_two_distributions_claiming_one_name_both_arrive` must FAIL — its
  fixture's values are `pkg_two.r:resolve` and `pkg_one.r:resolve`, whose sort order is the reverse
  of the providers' (`dist-one 1.0` before `dist-two 2.0`). **Checked against the test body:** the
  fixture was written with the value order deliberately opposed to the provider order, which is what
  makes this mutation discriminate; had both agreed it would have been blind.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green. **Never `git checkout --`.**

- [ ] **Step 8: Which deliverable no mutation reaches.** **`GROUPS`' membership is pinned only by a
      test asserting set equality against a literal**, so a group added to the tuple and to that
      test in one edit would pass — which is unavoidable for a constant and is why the test's
      docstring names § Creating a plugin as the authority rather than counting. **`provider_of`'s
      `dist is None` branch is unreachable** through `entry_points()` and is marked
      `# pragma: no cover`; nothing reaches it and nothing will. **The no-`.load()` guarantee is
      pinned by `test_the_scan_imports_nothing` only for `scan_group`** — a *caller* added later
      that loads is not caught here, and no test in this slice catches one. Tasks 8, 9, 11, 13, 14
      and 20 each restate the prohibition in their own text; that is the whole of the enforcement,
      and it is stated rather than claimed to be more.

- [ ] **Step 9: Verify and commit.** All four commands.
      `feat: the entry-point metadata scan, five groups, and no .load()`

---

## Task 8: The collision matrix, over metadata only

**Files:** Modify `src/publishable/templates/registry.py`, `src/publishable/validate.py`,
`docs/reference.md`, `tests/test_templates.py`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `plugins.scan_group`, `plugins.provider_of` (task 7);
  `registry._merged(repo_root: Path | None) -> dict[str, type[BaseTemplate]]`, which today builds
  `local = discover_local(repo_root)`, raises `PartialLoadError` for a local name in `_BUILTIN`, and
  returns `{name: found.cls for name, found in local.items()} | _BUILTIN`;
  `discovery.LocalTemplate(cls, provider)`; `discovery.PartialLoadError(message, *, code,
  partial_templates)`.
- Produces:
  - `registry.Claim` — a `NamedTuple` carrying `provider: str` and `cls: type[BaseTemplate] | None`.
    **`cls` is `None` for an installed claim and that is the point**, not an omission. **Task 9 adds
    a third field in front of these two**, so every construction here is written with keywords: a
    positional call would silently rebind when that field lands, and this is the cheapest place to
    make that impossible.
  - `registry._claims(repo_root: Path | None) -> dict[str, Claim]` — the merge, over all three
    sources, having decided every collision.
  - `_merged` rebuilt on `_claims`, still returning only the names whose claim carries a class.
  - `validate._check_plugin_collisions(c: Collector) -> None` — `E-PLUGIN-COLLISION` over the four
    non-template groups, called from `validate_config`.

**The matrix, and why two distributions.** The cases are entry-point × entry-point, × core, × local.
**One installed distribution cannot produce the first arm at all**, so the fixture proves the others
by accident if it has one — that is the trap this task is named in. Two distributions, in two
directories, per the fixture's own docstring.

**Name order, not discovery order.** Providers are named in the message and the *name* reported when
several collide is the first in name order. `discover_local` already establishes both properties for
the local-vs-local case and its comment says why; `_claims` takes the same shape rather than
inventing a second one. The re-scoping's probe is the live evidence that walk order is not name
order: `entry_points(group=…)` returned `dist-two` before `dist-one` for one arrangement.

**No `.load()`.** An installed claim is a name and a provider. Deciding a collision from metadata is
the whole reason the mechanism exists, and it is also why task 20's residual exists: a refused
installed claim carries no class, so nothing of its credentials can be redacted.

**Do not change `discover_local`.** Two local claims of one name still raise inside it, before
`_claims` sees anything, which is why every existing local-collision test stays green untouched.
Run those tests and observe them green rather than assuming it.

**Names already at module level in `tests/test_templates.py`:** `_modules_under`,
`_two_repos_each_holding_my_assay`, `ALPHA_TEMPLATE`, `BETA_TEMPLATE`, `REAL_ONE_TEMPLATE`,
`DUNDER_TEMPLATE`, `CLAIMS_DUPLICATED_A`, `CLAIMS_DUPLICATED_B`, `CLAIMS_TWICE_ON_ONE_CLASS`,
`CLAIMS_GENERIC`, `CLAIMS_TWICE_IN_ONE_FILE`, `RAISES_ON_IMPORT`, `REGISTERS_NOTHING`, plus the
`test_*` functions. `CLAIMS_MY_ASSAY` is free.

- [ ] **Step 1: Read the two existing shadow tests before touching the message.**
      `test_a_local_template_may_not_shadow_a_core_name` asserts three fragments of the raise's
      text — `"generic"`, `f"{templates / 'mine.py'}::LocalGeneric"`, and
      `"publishable.templates.builtin.generic.GenericTemplate"` — and
      `test_the_shadow_is_refused_however_the_registry_is_asked` asserts the code from three entry
      points. Any message you write must keep all three fragments. Read both bodies now; a message
      rewrite that drops one is the failure this step exists to prevent.

- [ ] **Step 2: Write the failing tests.** Append to `tests/test_templates.py`:

```python
CLAIMS_MY_ASSAY = """\
from publishable import BaseTemplate, register_template


@register_template("my_assay")
class LocalAssay(BaseTemplate):
    parameter_spec = {}
"""


def test_two_installed_distributions_claiming_one_template_name_are_refused(installed, tmp_path):
    """Entry-point × entry-point — the arm one distribution cannot produce.

    Both providers are named, as `<distribution> <version>`, which is what a
    reader uninstalls. Decided from metadata: neither module exists, so a
    verdict that reached for either class would raise `ModuleNotFoundError`
    instead of reporting.
    """
    installed("dist-two", "2.0", {"publishable.templates": {"my_assay": "no_two:T"}})
    installed("dist-one", "1.0", {"publishable.templates": {"my_assay": "no_one:T"}})

    with pytest.raises(ContractError) as excinfo:
        get_template("my_assay", tmp_path)
    assert excinfo.value.code == "E-TEMPLATE-COLLISION"
    message = str(excinfo.value)
    assert "my_assay" in message
    assert "dist-one 1.0" in message
    assert "dist-two 2.0" in message


def test_an_installed_distribution_may_not_shadow_a_core_name(installed, tmp_path):
    """Entry-point × core. Core's claimant is named as its dotted class path,
    there being no file to rename."""
    installed("dist-one", "1.0", {"publishable.templates": {"generic": "no_one:T"}})

    with pytest.raises(ContractError) as excinfo:
        get_template("generic", tmp_path)
    assert excinfo.value.code == "E-TEMPLATE-COLLISION"
    message = str(excinfo.value)
    assert "dist-one 1.0" in message
    assert "publishable.templates.builtin.generic.GenericTemplate" in message


def test_a_local_template_may_not_shadow_an_installed_one(installed, tmp_path):
    """Entry-point × local, and the case that needs both a repo and a
    distribution. Both providers are named in their own spelling — a path and a
    class for the local one, a distribution and a version for the installed."""
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "mine.py").write_text(CLAIMS_MY_ASSAY)
    installed("dist-one", "1.0", {"publishable.templates": {"my_assay": "no_one:T"}})

    with pytest.raises(ContractError) as excinfo:
        get_template("my_assay", tmp_path)
    assert excinfo.value.code == "E-TEMPLATE-COLLISION"
    message = str(excinfo.value)
    assert f"{templates / 'mine.py'}::LocalAssay" in message
    assert "dist-one 1.0" in message


def test_the_colliding_template_name_reported_is_the_first_in_name_order(installed, tmp_path):
    """Three colliding names, installed in an order that is neither sorted nor
    reverse-sorted, so neither candidate reading of "which one is reported"
    survives. Two names could not tell them apart.
    """
    claims = {"m_two": "no:T", "a_one": "no:T", "z_three": "no:T"}
    installed("dist-two", "2.0", {"publishable.templates": claims})
    installed("dist-one", "1.0", {"publishable.templates": claims})

    with pytest.raises(ContractError) as excinfo:
        get_template("a_one", tmp_path)
    assert "`a_one`" in str(excinfo.value)
    assert "m_two" not in str(excinfo.value)
    assert "z_three" not in str(excinfo.value)


def test_a_clean_installed_claim_is_not_a_collision(installed, tmp_path):
    """THE HONOURING, and the control that makes every refusal above about a
    collision rather than about installing anything at all: one distribution
    claiming a name nothing else claims raises nothing, and the name is known.
    """
    installed("dist-one", "1.0", {"publishable.templates": {"my_assay": "no_one:T"}})
    assert "my_assay" in template_names(tmp_path)
    assert get_template("my_assay", tmp_path) is None  # known, and not loaded — decision 3
```

      And append to `tests/test_validate.py`:

```python
def test_two_installed_distributions_claiming_one_resolver_name_are_reported(
    installed, write_config
):
    """`E-PLUGIN-COLLISION` over a non-template group, reported rather than
    raised, and reported for a repo whose config names no resolver at all — a
    registry core cannot make sense of is refused however it is asked.

    Asserted ALONGSIDE nothing: this config declares a table source, so
    `E-DATA-RESOLVER-UNSUPPORTED` is not in play. The resolver-adjacent
    companion is the second half of this test.
    """
    installed("dist-two", "2.0", {"publishable.resolvers": {"plate_wells": "no_two:r"}})
    installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "no_one:r"}})

    found = messages_by_code(write_config())
    message = found["E-PLUGIN-COLLISION"]
    assert "publishable.resolvers" in message
    assert "plate_wells" in message
    assert "dist-one 1.0" in message
    assert "dist-two 2.0" in message

    # Alongside, never instead of: a config that DOES name a resolver still
    # carries the wholesale refusal. Part B deletes this one line.
    both = codes(write_config({"data.units.from": {"resolver": "plate_wells"}}))
    assert "E-PLUGIN-COLLISION" in both
    assert "E-DATA-RESOLVER-UNSUPPORTED" in both


def test_one_distribution_per_plugin_name_reports_nothing(installed, write_config):
    """THE CONTROL. A check that reported unconditionally would pass the test
    above; this is what makes that one about a collision."""
    installed(
        "dist-one",
        "1.0",
        {
            "publishable.resolvers": {"plate_wells": "no_one:r"},
            "publishable.probes": {"assay_instrument": "no_one:p"},
        },
    )
    assert "E-PLUGIN-COLLISION" not in codes(write_config())
```

- [ ] **Step 3: Run and see them fail.** `uv run pytest tests/test_templates.py tests/test_validate.py -q`.
      The five template tests fail because no installed claim reaches the merge (four raise nothing;
      `test_a_clean_installed_claim_is_not_a_collision` fails on `template_names`). The two validate
      tests fail on `KeyError: 'E-PLUGIN-COLLISION'` and, for the control, pass already — a control
      that passes before the implementation is expected and is not evidence of anything until its
      sibling passes too.

- [ ] **Step 4: Implement the merge.** In `src/publishable/templates/registry.py`, add the import
      `from publishable.plugins import provider_of, scan_group`, add `NamedTuple` to the `typing`
      import, and replace `_merged` with:

```python
class Claim(NamedTuple):
    """One registration of one template name, and who made it.

    `cls` is `None` for an installed claim, and that is the mechanism rather than
    a gap: an entry point is resolved from package metadata, so core knows the
    name and the distribution without importing a line — see `plugins.py`. The
    consequences are that an installed name is *known* and not *resolvable* in
    this build, and that a refused installed claim carries no class whose
    declarations could be read.
    """

    provider: str
    cls: type[BaseTemplate] | None


def _claims(repo_root: Path | None) -> dict[str, Claim]:
    """Every claim on every template name, from all three sources, verdict reached.

    The three sources are core's own registry, the installed distributions'
    `publishable.templates` entry points, and — when a repo root is given — that
    repo's `templates/`. Collected in full before any verdict, on
    `discover_local`'s precedent and for its reason: a verdict reached while a
    claim set was still partial is a verdict over the wrong set. Reported in name
    order, and claimants within a name in provider order, because install order
    and import order are properties of a machine rather than of a design.

    Two local registrations of one name never reach here — `discover_local`
    refuses that pair itself, knowing what a repo declares — so this function
    sees at most one local claimant per name.
    """
    claims: dict[str, list[Claim]] = {}
    for name, core in _BUILTIN.items():
        claims.setdefault(name, []).append(
            Claim(provider=f"{core.__module__}.{core.__qualname__}", cls=core)
        )
    for name, entries in scan_group("publishable.templates").items():
        for ep in entries:
            claims.setdefault(name, []).append(Claim(provider=provider_of(ep), cls=None))
    local = discover_local(repo_root) if repo_root is not None else {}
    for name, found in local.items():
        claims.setdefault(name, []).append(Claim(provider=found.provider, cls=found.cls))
    for name in sorted(claims):
        if len(claims[name]) > 1:
            who = " and ".join(sorted(claim.provider for claim in claims[name]))
            raise PartialLoadError(
                f"the template name `{name}` is claimed more than once: {who} — a "
                "template that could redefine another's name could change what a "
                "config means without changing the config, which is what "
                "`parameters_hash` exists to make impossible. Install order and "
                "import order are the only tie-breaks available, and both are "
                "properties of a machine rather than of a design. Rename yours.",
                code="E-TEMPLATE-COLLISION",
                partial_templates=[
                    claim.cls
                    for these in claims.values()
                    for claim in these
                    if claim.cls is not None
                ],
            )
    return {name: these[0] for name, these in claims.items()}


def _merged(repo_root: Path | None) -> dict[str, type[BaseTemplate]]:
    """The names this build can hand back a class for: core's and this repo's.

    An installed name is in `_claims` and not here. `template_names` reads
    `_claims`, so the name is known; `get_template` reads this, so it is not
    resolved — see `Claim.cls`.
    """
    return {
        name: claim.cls for name, claim in _claims(repo_root).items() if claim.cls is not None
    }
```

      Then change `template_names` and `resolve_template`'s known-name list to read `_claims`:

```python
def template_names(repo_root: Path | None = None) -> list[str]:
    return sorted(_claims(repo_root))
```

      and in `resolve_template`, replace `merged = _merged(repo_root)` /
      `return (cls() if cls else None), sorted(merged)` with a single `_claims` call so the
      docstring's "one merge" promise still holds:

```python
    claims = _claims(repo_root)
    claim = claims.get(name)
    cls = claim.cls if claim is not None else None
    return (cls() if cls else None), sorted(claims)
```

      **`_claims` is called once per `resolve_template`, exactly as `_merged` was** — the
      docstring's argument is that asking for the two halves separately would import every
      `templates/*.py` twice, and that argument is unchanged.

- [ ] **Step 5: Implement the non-template check.** In `src/publishable/validate.py`, add
      `from publishable.plugins import provider_of, scan_group` and:

```python
def _check_plugin_collisions(c: Collector) -> None:
    """One entry-point key claimed by two installed distributions, outside templates.

    Templates are not here: a template name has a second home in a project's own
    `templates/`, so its verdict is reached at the merge that holds all three
    sources and is reported as `E-TEMPLATE-COLLISION`. These four groups have one
    source each, so the verdict is a property of the machine's installed set
    alone and is reported wherever it is noticed.

    Reported rather than raised, and reported for every config rather than only
    for one naming a colliding key: a registry core cannot make sense of is
    refused however it is asked, which is the same shape `_claims` takes for a
    `templates/` core cannot merge. Read from metadata, so no plugin is imported
    to reach a verdict.
    """
    for group in GROUPS:
        if group == "publishable.templates":
            continue
        for name, entries in scan_group(group).items():
            if len(entries) > 1:
                who = " and ".join(sorted(provider_of(ep) for ep in entries))
                c.error(
                    "E-PLUGIN-COLLISION",
                    "plugin",
                    f"key `{name}` in the `{group}` entry-point group is claimed by "
                    f"{who} — install order is the only tie-break available and it is "
                    "a property of a machine rather than of a design. Uninstall one",
                )
```

      Import `GROUPS` alongside `provider_of`/`scan_group` — and note that task 13 adds `names` to
      the same import line, so leave it as a parenthesized multi-name import that `ruff`'s `I` rule
      is happy to extend. Call it from `validate_config`
      immediately after `_check_entrypoint`, which is the nearest check that is also about what the
      machine supplies rather than what the config declares — name that neighbour in the commit
      message rather than a position.

- [ ] **Step 6: Update `reference.md`.** In § Errors `validate` reports' `E-TEMPLATE-COLLISION` row,
      replace the opening clause "A template name is claimed twice where this build can see both
      claimants: two [project-local `templates/*.py`](#templates-where-parameters-are-defined)
      registrations of one name — in two files, or twice in one file — or a local registration of a
      name core itself registers (`generic`)" with:

```
| A template name is claimed twice across core's own registry, the [installed distributions'](#creating-a-plugin-publishable-plugin-new) `publishable.templates` entry points, and this project's own [`templates/`](#templates-where-parameters-are-defined): two local registrations of one name — in two files, or twice in one file — a local registration of a name core registers, two installed distributions registering one name, an installed distribution registering a name core registers, or a local registration of a name an installed distribution registers.
```

      Leave the rest of the row — the eager-discovery paragraph, the `E-TEMPLATE-LOAD` preemption,
      the provider-naming rules — as it stands; task 2 already extended the § Errors core raises
      twin and deleted the "not yet checked" clause here.

- [ ] **Step 7: Run and see them pass.** `uv run pytest tests/test_templates.py tests/test_validate.py -q`,
      then the whole suite. **Every pre-existing collision and shadow test must still pass
      untouched** — run `uv run pytest tests/test_templates.py -q -k "shadow or claim or collision"`
      and read the list. Expected total: your predecessor's count **+ 7**.

- [ ] **Step 8: Mutate — four, each checked against the test body it must redden.**

  **(a) Skip the installed source.** Delete the `scan_group("publishable.templates")` loop from
  `_claims`. `test_two_installed_distributions_claiming_one_template_name_are_refused`,
  `test_an_installed_distribution_may_not_shadow_a_core_name`,
  `test_a_local_template_may_not_shadow_an_installed_one` and
  `test_a_clean_installed_claim_is_not_a_collision` must all FAIL. **Checked against the bodies:**
  the first three expect a raise the mutant does not make; the fourth asserts `"my_assay" in
  template_names(tmp_path)`, which the mutant cannot satisfy. This is the mutation that proves the
  third source is wired, and the fourth test is the one that proves it for the *non*-colliding case
  — without it, a `_claims` that raised unconditionally on any installed name would pass the first
  three.

  **(b) Verdict in walk order rather than name order.** Change `for name in sorted(claims):` to
  `for name in claims:`. `test_the_colliding_template_name_reported_is_the_first_in_name_order` must
  FAIL. **Checked against the body:** three names are declared in the order `m_two`, `a_one`,
  `z_three` within each distribution, so the mutant reports `m_two` and the test asserts `` `a_one` ``
  is named and `m_two` is not. Two names could not discriminate — with two, the reverse of
  declaration order is sorted order for one arrangement — which is why there are three.

  **(c) Name one claimant instead of all.** Change `who` to `claims[name][0].provider`.
  `test_two_installed_distributions_claiming_one_template_name_are_refused` must FAIL on its
  `"dist-two 2.0"` assertion, and `test_a_local_template_may_not_shadow_an_installed_one` on one of
  its two. **Checked against the bodies:** both assert two distinct provider strings and the mutant
  produces one. Note the pre-existing `test_a_local_template_may_not_shadow_a_core_name` also goes
  red, which is fine — a mutation must fail *at least* the named test.

  **(d) Reach for the class.** In `_claims`, change the installed branch to
  `Claim(provider_of(ep), ep.load())`. **`test_a_clean_installed_claim_is_not_a_collision` must FAIL
  with `ModuleNotFoundError`**, because its fixture's entry point names a module that does not
  exist. **Checked against the body:** the fixture deliberately points at `no_one:T`, so the failure
  is the load and not a assertion — read the traceback and confirm it is `ModuleNotFoundError` from
  `_claims`, not an `AssertionError`. **This is the mutation that pins decision 3**, and it is the
  only one that does; the other three would all pass with `.load()` in place.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green. **Never `git checkout --`.**

- [ ] **Step 9: Which deliverable no mutation reaches.** **`_check_plugin_collisions`' choice of
      reporting path (`"plugin"`) is unpinned** — both new validate tests read
      `messages_by_code`/`codes`, neither of which sees a finding's path, and adding a path
      assertion would pin a field no § Errors row states. Left deliberately; **nothing closes it.**
      **`Claim.provider` for core's own claimant is pinned only through the pre-existing shadow
      test's dotted-class-path fragment**, which is enough — that fragment cannot be produced any
      other way. **The `partial_templates` expression is knowingly still a proxy at this commit** —
      it names `claims.values()` rather than `local.values()`, which is already the right concept,
      but nothing distinguishes them until an installed claim carries a class, which Part A never
      makes it do. **Task 20 documents that residual**; no mutation in this slice reaches it, and
      task 20 says so again rather than claiming otherwise.

- [ ] **Step 10: Verify and commit.** All four commands.
      `feat: the template collision matrix over three sources, decided from metadata`

---

## Task 9: Template provenance becomes three-valued

**Files:** Modify `src/publishable/templates/registry.py`, `src/publishable/templates/discovery.py`,
`src/publishable/validate.py`, `src/publishable/materialize.py`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `tests/test_templates.py`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `registry.Claim` and `registry._claims` (task 8); `discovery.is_local_template(cls:
  type[BaseTemplate]) -> bool`, which reads a marker `_import_file` stamps and whose two callers are
  `validate._check_versions` (`is_local_template(type(template))`) and `materialize.materialize_config`
  (`local = is_local_template(type(template))`).
- Produces:
  - `Claim.provenance: str` — `"core"`, `"local"` or `"installed"`, decided at the merge where all
    three sources are in hand.
  - `registry.template_provenance(name: str, repo_root: Path | None) -> str | None` — the direct
    question, answered from `_claims` rather than from a marker on a class.
  - `validate` reporting `E-TEMPLATE-INSTALLED-UNSUPPORTED` for a name whose only claim is installed.
  - `is_local_template` **kept and unchanged**, still stamping and still read — see the ruling below.

**The ruling on `is_local_template`, and it is narrower than "replace the predicate".** The
re-scoping's § 10 says the direct question is asked at the merge, and it is: `Claim.provenance` is
decided there, from the source a claim came from, with no proxy. But its two readers take a **class**
and not a name, and in Part A no installed claim ever carries a class — decision 3 forbids the load.
So **`installed` is unreachable at both class-taking readers in this slice**, and rewriting them to
consult a three-valued predicate would thread a value no fixture can produce, which is precisely the
"seam named in the brief and instantiated by no fixture" shape that passed 1700+ tests in an earlier
slice. `is_local_template` therefore stays exactly as it is, keeps both callers, and keeps its
docstring's stated boundary. What is three-valued is the **claim**, and it is observable at three
places that do not take a class: `template_provenance`, the collision message's provider spellings
(task 8), and the new refusal below.

**The refusal this task mints, and why it is the `-UNSUPPORTED` family.** After task 8 an installed
template name is *known* and unresolvable. Reporting `E-TEMPLATE-UNKNOWN` for it would be false —
the message says "no template … registers" and one does. Reporting nothing would let
`validate_config` fall through to `template is None` and return with a wrong finding. So:
`E-TEMPLATE-INSTALLED-UNSUPPORTED`, the undocumented build family — **no § Errors row, and it must
not gain one** — retired wholesale by whichever slice loads an installed template. **That slice is
not Part B**, whose nine tasks are the resolver half; this task files the residual with its owner
stated as unassigned, which is the honest form.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_templates.py`:

```python
def test_provenance_is_decided_at_the_merge_for_each_of_the_three_sources(installed, tmp_path):
    """The direct question, asked where all three sources are in hand.

    All three values in one arrangement, because a fixture with two could not
    tell a three-valued answer from a boolean one renamed.
    """
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "mine.py").write_text(CLAIMS_MY_ASSAY)
    installed("dist-one", "1.0", {"publishable.templates": {"vendor_assay": "no_one:T"}})

    assert template_provenance("generic", tmp_path) == "core"
    assert template_provenance("my_assay", tmp_path) == "local"
    assert template_provenance("vendor_assay", tmp_path) == "installed"
    assert template_provenance("nothing_claims_this", tmp_path) is None
```

      and to `tests/test_validate.py`:

```python
def test_an_installed_only_template_name_is_known_and_refused(installed, write_config):
    """Known, and not resolved: core answers the name from metadata and does not
    import the distribution to get a class. So the finding is neither
    `E-TEMPLATE-UNKNOWN` — which would be false — nor silence.
    """
    installed("dist-one", "1.0", {"publishable.templates": {"vendor_assay": "no_one:T"}})

    found = messages_by_code(write_config({"experiment_type": "vendor_assay"}))
    assert "E-TEMPLATE-UNKNOWN" not in found
    message = found["E-TEMPLATE-INSTALLED-UNSUPPORTED"]
    assert "vendor_assay" in message
    assert "dist-one 1.0" in message

    # THE CONTROL: a name nothing claims is still `E-TEMPLATE-UNKNOWN`, so the
    # refusal above is about the installed claim rather than about any
    # unresolved name.
    assert "E-TEMPLATE-UNKNOWN" in codes(write_config({"experiment_type": "nothing_claims_this"}))
```

- [ ] **Step 2: Run and see them fail.** `ImportError` on `template_provenance`, and
      `KeyError: 'E-TEMPLATE-INSTALLED-UNSUPPORTED'`.

- [ ] **Step 3: Implement.** In `registry.py`, add `provenance: str` to `Claim` — **first field**,
      so the collision message's `claim.provider` reads stay unambiguous only if you update every
      construction; construct with keywords rather than positionally to make that impossible to get
      wrong:

```python
class Claim(NamedTuple):
    provenance: str
    provider: str
    cls: type[BaseTemplate] | None
```

      Construct core's as `Claim(provenance="core", provider=…, cls=core)`, an entry point's as
      `Claim(provenance="installed", provider=provider_of(ep), cls=None)`, and a local one as
      `Claim(provenance="local", provider=found.provider, cls=found.cls)`. Then add:

```python
def template_provenance(name: str, repo_root: Path | None = None) -> str | None:
    """Where the template `name` resolves from — `core`, `local`, `installed` — or
    `None` if nothing claims it.

    Asked at the merge, which is the one place holding all three sources, and
    answered from which source a claim came from rather than from anything
    observable on a class afterward. `discovery.is_local_template` answers a
    narrower question about a class that is already in hand, and keeps its two
    callers: nothing in this build ever holds an installed template's class, so a
    class-taking predicate has no third value to return.
    """
    claim = _claims(repo_root).get(name)
    return claim.provenance if claim is not None else None
```

      In `validate.py`, inside `validate_config`, replace the `if template is None:` block with:

```python
    if template is None:
        # One merge, for the reason `resolve_template`'s docstring already gives:
        # `_claims` runs local discovery, which imports every `templates/*.py`
        # and executes every user top level. Asking `template_provenance` and
        # then `_claims` would do that twice more in a command that has already
        # done it once.
        claim = _claims(repo_root).get(name)
        if claim is not None and claim.provenance == "installed":
            c.error(
                "E-TEMPLATE-INSTALLED-UNSUPPORTED",
                "experiment_type",
                f"names `{name}`, which {claim.provider} registers as a "
                "`publishable.templates` entry point — but core resolves an installed "
                "template's name without importing its package, and loading one is not "
                "implemented in this build; installed templates will be honored in a "
                "later slice. Use a project-local `templates/` file or a core template "
                "for now",
            )
        else:
            c.error(
                "E-TEMPLATE-UNKNOWN",
                "experiment_type",
                unknown_template_message(name, known),
            )
        return None  # every later check reads the spec
```

      importing `_claims` from `publishable.templates.registry`. `template_provenance` is the public
      answer for a caller that has only a name; `validate_config` needs the provider string too, so
      it takes the claim itself and reads both off one merge. **Both branches return `None`** — the reason the existing branch does ("every later check reads the
      spec") is unchanged, and `validate` collecting rather than aborting does not mean a check with
      no template can run.

- [ ] **Step 4: Do not touch `materialize.py`'s or `_check_versions`' `is_local_template` call.**
      Read both and confirm you left them alone. Task 10 changes what `_check_versions` *compares*,
      not how it decides to skip.

- [ ] **Step 5: Document it — and do NOT change any count phrase in § The one config file.** The
      sentence reading "**Two** declarations above are not yet built" counts *config declarations
      marked `NOT BUILT` in the fenced example*, and an `experiment_type` naming an installed
      template is not one. Read that rule first, then edit. In the identifying-fields paragraph — the
      same sentence task 5 edited — the clause now reads "…or this project's own `templates/`
      registers;". Extend it:

```
…or this project's own `templates/` registers — an installed one is answered from package metadata, so a name no distribution declares is refused without importing anything, and a name one *does* declare is [not yet loadable in this build](#the-one-config-file);
```

      and add `E-TEMPLATE-INSTALLED-UNSUPPORTED` to the sentence in the same section that names the
      `-UNSUPPORTED` family, which reads "**Two declarations above are not yet built, and each is
      marked `NOT BUILT` where it appears**". Do **not** change its count — that sentence counts
      *config declarations* marked `NOT BUILT` in the fenced example, and an installed template name
      is not one of them. Instead append to that sentence's own paragraph:

```
A third refusal in the same family is not a declaration at all and so is marked nowhere above: an `experiment_type` naming a template an installed distribution registers is refused, because core resolves such a name from package metadata and this build does not load what the name points at. It carries `E-TEMPLATE-INSTALLED-UNSUPPORTED` and, like every `-UNSUPPORTED` code, [no row in the registry below](#errors-validate-reports).
```

- [ ] **Step 6: File the residual.** Append to `docs/superpowers/spec-defects.md`:

```markdown
## OPEN — an installed template's name resolves but its class is never loaded — **Owner: unassigned**

H7b Part A task 8 makes an installed distribution's `publishable.templates` entry point a claim in
the merge, so its name is known, collisions against it are decided, and `template_names` lists it.
Task 9 refuses a config naming one, as `E-TEMPLATE-INSTALLED-UNSUPPORTED` — the `-UNSUPPORTED` build
family, no § Errors row.

The refusal exists because decision 3 of `2026-08-16-plugin-registries-design.md` states the
entry-point invariant of **resolution** and not merely of the negative answer: "`validate` resolves a
name *without importing a line*". Loading the one entry point a config names would answer a narrower
reading of the same sentence and is the natural next step, but it is a decision, not an oversight,
and it is not H7b Part B's — Part B is the resolver half and its nine tasks do not touch template
loading.

**What retiring it needs:** `Claim.cls` populated for an installed claim; `is_local_template`'s two
class-taking callers (`validate._check_versions`, `materialize.materialize_config`) reading
`Claim.provenance` instead, since `installed` becomes reachable at both for the first time; and
`provenance.plugin_versions` recording which distribution supplied it. **Owner: unassigned.**
```

      Use `git add -f` per `CLAUDE.md`.

- [ ] **Step 7: Run and see them pass**, then the whole suite. Expected: predecessor's count **+ 2**.
      Every pre-existing `E-TEMPLATE-UNKNOWN` test must still pass — run
      `uv run pytest -q -k "unknown"` and read the list.

- [ ] **Step 8: Mutate — two.**

  **(a) Collapse the branch.** In `validate_config`, delete the `if provenance == "installed":` arm
  so every unresolved name reports `E-TEMPLATE-UNKNOWN`.
  `test_an_installed_only_template_name_is_known_and_refused` must FAIL on its first assertion
  (`"E-TEMPLATE-UNKNOWN" not in found`). **Checked against the body:** the test asserts both the
  absence of the wrong code and the presence of the right one, so the mutant fails on the first and
  would fail on the second too; and its control asserts the *other* direction with a name nothing
  claims, so a mutant that always reported the new code would fail there instead.

  **(b) Answer provenance from a class rather than from the merge.** Change `template_provenance` to
  `return "local" if name in discover_local(repo_root or Path(".")) else "core"`.
  `test_provenance_is_decided_at_the_merge_for_each_of_the_three_sources` must FAIL on its
  `"installed"` assertion. **Checked against the body:** the fixture declares all three sources in
  one arrangement, so the mutant's two-valued answer differs from the expected one for
  `vendor_assay`. A two-source fixture could not discriminate — that is why the test builds all
  three.

  Revert each by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 9: Which deliverable no mutation reaches, stated plainly.** **`installed` is unreachable
      at `validate._check_versions` and at `materialize.materialize_config`** — both take a class,
      and no installed claim carries one in this slice. No test here pins their behaviour under a
      third value because no fixture can produce one, and inventing a fake class to feed them would
      pin a path core never takes. **Nothing in Part A or Part B closes this**; the `spec-defects.md`
      entry filed in step 6 is where it lives, owner unassigned. **`Claim.provenance` for the `core`
      value is pinned only by `template_provenance("generic", …)`**, which is enough — no other
      source can produce it.

- [ ] **Step 10: Verify and commit.** All four commands.
      `feat: template provenance is three-valued at the merge, and an installed name is known but unloaded`

      Note for step 1: `tests/test_templates.py` must import `template_provenance` alongside its
      existing `from publishable.templates.registry import get_template, template_names`.

---

## Task 10: `BaseTemplate.version`, and `W-TEMPLATE-VERSION` against it

**Files:** Modify `src/publishable/templates/base.py`, `src/publishable/templates/builtin/generic.py`,
`src/publishable/validate.py`, `src/publishable/materialize.py`,
`src/publishable/generators/template.py`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `tests/test_templates.py`.

**Interfaces:**
- Consumes: `BaseTemplate`'s class attributes, which today are `naming_pattern`, `field_convention`,
  `default_repeats`, `required_env`, `apparatus_probe`, `apparatus_facts`, `parameter_spec`, plus
  the methods `validate` and `aggregate`; `materialize.TEMPLATE_VERSION`, the module constant
  `"1.0.0"`; `validate._check_versions(doc, template, c)`, whose warning message reads
  `f"is {declared} but the installed template reports {TEMPLATE_VERSION}{detail}"`;
  `materialize.materialize_config`, which writes `template_version: "{TEMPLATE_VERSION}"` for a
  non-local template and omits the line for a local one.
- Produces: `BaseTemplate.version: str | None = None`; `GenericTemplate.version = TEMPLATE_VERSION`;
  `_check_versions` comparing against **the template's own** reported version; `materialize` writing
  **the template's own** version.

**Row 212's first half, and what actually closes it.** `spec-defects.md`'s Row 212 says
`_check_versions` compares the declared `template_version` against a module constant rather than
against the installed template's own reported version, and that closing it means `BaseTemplate`
declaring a `version` attribute — a four-document change. That is exactly this task. What it does
**not** do is make the third provenance reachable there: task 9 states that no installed claim
carries a class in Part A, so `_check_versions` still sees only core's own template and this repo's.
The gap the attribute closes is the **false guarantee in the message** — "the installed template
reports" is a claim about a template core did not write — and the hard-coded comparison. Both are
real and both are fixed here; the reachability is not, and the `spec-defects.md` amendment says so
rather than striking the row outright.

**Two counts in comments that go stale here, and `CLAUDE.md` forbids both.**
`generators/template.py`'s comment says the stub emits "five members … and none of `BaseTemplate`'s
other four", and that `reference.md` § Templates "shows all nine". Adding `version` moves both.
**Rewrite them to state what each set *is*** rather than to increment a number — that is the rule,
and re-incrementing is how this repo has gone wrong before.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_templates.py`:

```python
def test_a_template_reports_its_own_version_and_the_base_declares_none():
    """`None` and a string are different claims: the first is "this template
    tracks no version", which is every template that does not set one, and the
    second is what `template_version` in a config is compared against."""
    assert BaseTemplate.version is None
    assert get_template("generic").version == TEMPLATE_VERSION


def test_the_version_warning_names_what_the_template_reports_not_a_core_constant(
    tmp_path: Path, git_repo: Path
):
    """The false guarantee Row 212 names, closed by comparing against the class.

    A local template declaring a version of its own is still skipped — that is
    `_check_versions`' first line and § Three hashes' rule — so the observable
    change is that the comparison reads the class rather than a module constant,
    and the fixture that shows it is a subclass whose `version` differs from
    core's.
    """
    from publishable.diagnostics import Collector
    from publishable.validate import _check_versions

    class Versioned(BaseTemplate):
        version = "9.9.9"
        parameter_spec = {}

    c = Collector()
    _check_versions({"template_version": "1.0.0"}, Versioned(), c)
    message = next(f.message for f in c.findings if f.code == "W-TEMPLATE-VERSION")
    assert "9.9.9" in message
    assert TEMPLATE_VERSION not in message

    # THE CONTROL, produced by the code under test: a config declaring the
    # version the template reports draws nothing at all.
    quiet = Collector()
    _check_versions({"template_version": "9.9.9"}, Versioned(), quiet)
    assert [f.code for f in quiet.findings] == []
```

      `tests/test_templates.py` imports `BaseTemplate` already; add
      `from publishable.materialize import TEMPLATE_VERSION`.

- [ ] **Step 2: Run and see it fail.** `AttributeError: type object 'BaseTemplate' has no attribute
      'version'`.

- [ ] **Step 3: Implement.** In `src/publishable/templates/base.py`, add beside the other class
      attributes:

```python
    version: str | None = None
```

      with a docstring-adjacent comment stating what it is rather than counting the attributes
      around it:

```python
    # What this template reports as its own spec version, which a config's
    # `template_version` is compared against. `None` for a template that tracks
    # no version — the base's answer, and the right one for a project-local file,
    # whose version is a string its author remembers to bump rather than a fact
    # core can check.
```

      In `src/publishable/templates/builtin/generic.py`, add
      `from publishable.materialize import TEMPLATE_VERSION` and `version = TEMPLATE_VERSION`.
      **Check the import direction before writing it:** `materialize` imports
      `publishable.param`, `publishable.templates.base` and `publishable.templates.discovery`, and
      imports neither `registry` nor `builtin.generic`, so `generic → materialize → discovery →
      base` introduces no cycle. Confirm by running `uv run python -c "import publishable"` and then
      the suite; a cycle shows as an `ImportError` at collection, not later.

      In `src/publishable/validate.py`, replace `_check_versions`' comparison and message:

```python
    if is_local_template(type(template)):
        return
    reported = type(template).version
    declared = doc.get("template_version")
    if reported is None or not declared or declared == reported:
        return
```

      and the warning's message:

```python
        f"is {declared} but the template reports {reported}{detail}",
```

      Then amend the docstring paragraph that reads "`TEMPLATE_VERSION` is core's own constant —
      comparing a config's declared string against it is meaningless for a template core did not
      write" so it states the current rule:

```python
    A local template is skipped regardless of what `template_version` declares,
    and so is any template reporting no version of its own. What a config's
    declared string is compared against is the template's own `version`, read
    off the class: a module constant would be core's answer for a template core
    did not write, which `docs/reference.md` § Three hashes rejects — a
    `template_version` "isn't the answer for a local template — it's a string
    its author remembers to bump."
```

      In `src/publishable/materialize.py`, replace the two `TEMPLATE_VERSION` interpolations so the
      generated header and field carry what the template reports:

```python
    local = is_local_template(type(template))
    reported = None if local else type(template).version
    header_version = "" if reported is None else f" v{reported}"
```

      and `*([] if reported is None else [f'template_version: "{reported}"']),`. **`TEMPLATE_VERSION`
      stays defined in `materialize.py`** — `generic.py` reads it and `validate.py` no longer does;
      remove `validate.py`'s now-unused import and let `ruff` confirm it.

- [ ] **Step 4: Rewrite the two stale counts.** In `src/publishable/generators/template.py`, replace
      "The stub emits five members — `parameter_spec`, `validate`, `aggregate`, `naming_pattern`,
      `default_repeats` — and none of `BaseTemplate`'s other four" with a statement of what each set
      is:

```python
# The stub emits `parameter_spec`, `validate`, `aggregate`, `naming_pattern` and
# `default_repeats`, and none of the rest. `required_env` has a reader
# (`validate` checks it), but a stub declaring `[]` would only ever satisfy that
# check trivially and would still teach its reader to set a field this generated
# file has no other use for. `version` is omitted for a sharper reason: a
# project-local template is never version-checked at all, so a version in this
# file would be a string nothing reads. `field_convention`, `apparatus_probe`
# and `apparatus_facts` are declared on the base class and read by nothing in
# this build. `docs/reference.md` § Templates: where parameters are defined
# shows the whole set, because that example is core's own `generic` rather than
# a file you are about to edit.
```

      Note the last sentence drops "all nine" for "the whole set" — the rule is to state what a set
      *is*, and a count in a comment is what went stale. **Task 13 edits this same comment again**
      when `apparatus_probe` gains a reader; do not pre-empt it.

- [ ] **Step 5: Document it.** In § Templates' fenced class example, add `version = "1.0.0"` after
      `default_repeats = 1`, and in § The importable surface's "What you define, and what is core's"
      table, the `BaseTemplate` row's **Defaulted** column reads "`validate(self, config)` returns
      `[]`" — extend it to "`validate(self, config)` returns `[]`, `version` is `None`". In
      § Validation's *Template version moved* row, the example failure reads "`template_version` is
      `1.0.0` but installed `generic` reports `1.2.0`" — leave it; it was already stated against the
      template rather than a constant and is now true.

- [ ] **Step 6: Amend Row 212 rather than striking it.** Append to that section in
      `docs/superpowers/spec-defects.md`:

```markdown
**AMENDED 2026-08-16 (H7b Part A task 10): the comparison is fixed; the reachability is not.**
`BaseTemplate.version` now exists, `GenericTemplate` reports it, `_check_versions` compares a
config's `template_version` against `type(template).version`, and `materialize` writes what the
template reports. The false guarantee this row named — a warning saying "the installed template
reports" while comparing against core's own module constant — is gone.

What remains, and it is why this row is amended rather than struck: **no installed template's class
is ever held in this build**, so the comparison still only ever runs against core's own template and
a project-local one is still skipped. `Claim.cls` is `None` for an installed claim by decision 3 of
`2026-08-16-plugin-registries-design.md`. This row's own words — "It becomes observable when a
plugin ships a template with a version of its own" — are still the condition, and it is now filed
separately as `## OPEN — an installed template's name resolves but its class is never loaded`,
**owner unassigned**. Strike this row when that one is closed, not before.
```

- [ ] **Step 7: Run and see it pass**, then the whole suite. `tests/test_materialize.py`'s
      `test_the_four_identifying_fields_are_present` and
      `test_a_local_template_carries_no_core_template_version` are the regression controls and must
      pass **unchanged**: `generic.version` equals `TEMPLATE_VERSION`, so the generated config is
      byte-identical. Confirm that by running those two by name and reading the result. Expected
      total: predecessor's count **+ 2**.

- [ ] **Step 8: Mutate — two.**

  **(a) Compare against the constant again.** In `_check_versions`, change `reported =
  type(template).version` to `reported = TEMPLATE_VERSION` (re-adding the import).
  `test_the_version_warning_names_what_the_template_reports_not_a_core_constant` must FAIL on
  `assert "9.9.9" in message` — the mutant compares `"1.0.0"` against `"1.0.0"` and returns early,
  so the `next(...)` raises `StopIteration` before the assertion. **Checked against the body:** the
  fixture's `Versioned.version` is deliberately `"9.9.9"` while its config declares `"1.0.0"`, which
  is what makes the two branches produce different results; a fixture whose version happened to
  equal `TEMPLATE_VERSION` would have been blind. Read the failure and confirm it is
  `StopIteration`, not an `AssertionError` — if it is an `AssertionError` the early return was
  transcribed wrong.

  **(b) Drop the `reported is None` guard.** Remove `reported is None or` from the early return.
  Nothing in the suite goes red, **and that is the finding**: no template in the tree reports `None`
  while also being non-local, so the guard is unreachable today. **Do not keep this mutation and do
  not manufacture a fixture for it** — a `BaseTemplate` subclass with no version, registered in a
  repo's `templates/`, is local and skipped one line earlier. State in the task report that the
  guard is defensive and unpinned, and that the task that populates `Claim.cls` for an installed
  claim is what first reaches it.

  Revert (a) by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 9: Which deliverable no mutation reaches.** `materialize`'s use of
      `type(template).version` **is not independently pinned**: `generic.version` equals
      `TEMPLATE_VERSION`, so writing either produces the same file and every materialize test passes
      under both. A fixture that separated them would have to be a non-local template reporting a
      different version, which is the unreachable case named in mutation (b). Stated rather than
      papered over; **nothing in this slice closes it.** § Templates' `version = "1.0.0"` line and
      the § The importable surface cell are prose and unpinned, as every document row in this slice
      is.

- [ ] **Step 10: Verify and commit.** All four commands.
      `feat: a template reports its own version, and W-TEMPLATE-VERSION compares against it`

---

## Task 11: `E-TEMPLATE-UNKNOWN`'s `plugin` hint

**Files:** Modify `src/publishable/templates/registry.py`, `src/publishable/validate.py`,
`src/publishable/generators/experiment.py`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `registry.unknown_template_message(name: str, known: Sequence[str]) -> str`, whose body
  is `f"names \`{name}\`, which no template — core's, an installed plugin's, or this project's own
  \`templates/\` — registers (known: {', '.join(known)})"`, and which has exactly two callers:
  `validate.validate_config` and `generators/experiment.generate_experiment`. **§ Errors carries one
  row per code covering every emit site**, and this code has two.
- Produces: `unknown_template_message(name, known, plugin=None)`; the hint rendered at the
  `validate` site, which is the one that holds a config; and the `generate` site passing `None`
  explicitly, since no config exists there yet.

**Row 211, and the exact thing it asks for.** The row is *"`experiment_type` names `llm_diagnostic`,
which no installed plugin registers — `plugin` says it should come from
`someuser/publishable-llm`."* `validate_config` reports the code and lists the known names but not
the `plugin` field's hint. The row's own justification for waiting was that the hint "is only useful
once an unresolvable `experiment_type` can name a template some *uninstalled* distribution
registers, which is the entry-point resolution H7 owns" — task 7 lands that, so the wait is over.

**The one wording, and why the change is one wording rather than two.**
`unknown_template_message` exists so `validate`'s finding and `generate_experiment`'s raise cannot
drift; the re-scoping confirmed it is still the single source. Change it there and both surfaces
move. **Do not add a second literal at either call site.**

- [ ] **Step 1: Write the failing test.** Append to `tests/test_validate.py`:

```python
def test_an_unresolved_template_name_names_the_plugin_the_config_points_at(write_config):
    """Row 211. The hint is the config's own `plugin` field, which is a readable
    note beside `uv.lock` rather than an install instruction — so the message
    says where the template was expected to come from and does not offer to
    fetch it.
    """
    found = messages_by_code(
        write_config({"experiment_type": "llm_diagnostic", "plugin": "someuser/publishable-llm"})
    )
    message = found["E-TEMPLATE-UNKNOWN"]
    assert "llm_diagnostic" in message
    assert "someuser/publishable-llm" in message
    assert "generic" in message  # the known list is still printed

    # THE CONTROL: with no `plugin` declared the message must not invent one, and
    # must not carry the hint's connective either — a fragment that appeared
    # under both declarations would pin nothing.
    plain = messages_by_code(write_config({"experiment_type": "llm_diagnostic"}))["E-TEMPLATE-UNKNOWN"]
    assert "someuser/publishable-llm" not in plain
    assert "`plugin` says" not in plain
```

- [ ] **Step 2: Run and see it fail.** The first `assert "someuser/publishable-llm" in message`
      fails; the control passes already, which is expected and proves nothing until its sibling does.

- [ ] **Step 3: Implement.** In `registry.py`:

```python
def unknown_template_message(
    name: str, known: Sequence[str], plugin: str | None = None
) -> str:
    """The one wording for a name neither `resolve_template` call site resolved —
    `validate`'s finding and `generate_experiment`'s raise both read this
    rather than each keeping its own copy, so the two surfaces cannot drift
    the way two hard-coded literals eventually would.

    Takes the already-resolved names rather than a repo root, so building the
    message costs no second discovery: each caller has just merged, and has
    them in hand.

    `plugin` is the config's own field, when the caller has a config. It is a
    readable note beside the authoritative pin in `uv.lock` rather than a second
    one — core never installs from it — so the hint says where the template was
    expected to come from and stops there. A caller with no config passes
    `None`: `generate experiment` is writing the file that would hold it.
    """
    hint = f" — `plugin` says it should come from `{plugin}`" if plugin else ""
    return (
        f"names `{name}`, which no template — core's, an installed plugin's, "
        f"or this project's own `templates/` — registers "
        f"(known: {', '.join(known)}){hint}"
    )
```

      In `validate.py`'s `validate_config`, the `E-TEMPLATE-UNKNOWN` branch task 9 wrote becomes:

```python
            plugin = doc.get("plugin")
            c.error(
                "E-TEMPLATE-UNKNOWN",
                "experiment_type",
                unknown_template_message(
                    name, known, plugin if isinstance(plugin, str) and plugin else None
                ),
            )
```

      The `isinstance` guard is not defensive padding: `plugin` is typed `str` by `LEAF_TYPES` and a
      wrong type there is `E-CONFIG-TYPE`'s finding, but a leaf fault is deliberately non-fatal, so
      this branch is reachable with a list or a mapping in that field and interpolating one would
      print a `repr` into a hint. The same reasoning `_check_units`' `input_dir` and `key` guards
      already carry.

      In `generators/experiment.py`, pass the third argument explicitly rather than relying on the
      default, so a reader of that call site sees the decision:

```python
        raise ContractError(
            unknown_template_message(template_name, known, plugin=None),
            code="E-TEMPLATE-UNKNOWN",
        )
```

- [ ] **Step 4: Update § Errors `validate` reports' `E-TEMPLATE-UNKNOWN` row.** It reads
      "`experiment_type` is missing, empty, or names a template neither core nor this project's own
      [`templates/`](#templates-where-parameters-are-defined) registers. An installed plugin's is
      not yet checked either: no entry point is resolved in this build, so there is no plugin
      registry for a name to be found in or missing from." **Delete the second sentence** and
      replace the first:

```
| `experiment_type` is missing, empty, or names a template that neither core, nor any installed distribution's `publishable.templates` entry points, nor this project's own [`templates/`](#templates-where-parameters-are-defined) registers — the installed set read from package metadata, so a name no distribution declares is refused without importing one. When the config declares a [`plugin`](#the-one-config-file), the message names it: that field is a readable note about where the template was expected to come from, so a reader who has not installed it learns that from the diagnostic rather than from a missing-name list. Two surfaces meet this condition — `validate` reports it as a finding, never raising it, and [`generate experiment`](#creation-commands) raises it as a `ContractError` — and this row governs both, the two built from one shared message; the hint appears only at the first, `generate` being the command that writes the file the field would live in | `E-TEMPLATE-UNKNOWN` |
```

- [ ] **Step 5: Strike Row 211.** Append to that section in `docs/superpowers/spec-defects.md`:

```markdown
**STRUCK 2026-08-16 (H7b Part A task 11).** `unknown_template_message` takes the config's `plugin`
field and renders it, so `validate`'s finding names where the template was expected to come from.
The row's stated precondition — that an unresolvable `experiment_type` can name a template some
uninstalled distribution registers — is satisfied by task 7's metadata scan and task 8's merge.
`generate experiment` passes `None` and shows no hint, deliberately: it is writing the file that
would hold the field.
```

- [ ] **Step 6: Run and see it pass**, then the whole suite. Every pre-existing
      `E-TEMPLATE-UNKNOWN` test must still pass **untouched** — none of them declares a `plugin`,
      so none sees the hint. Run `uv run pytest -q -k "unknown_template or TEMPLATE_UNKNOWN"` and
      read the list. Expected: predecessor's count **+ 1**.

- [ ] **Step 7: Mutate — two.**

  **(a) Render the hint unconditionally.** Change the `hint` line to
  `hint = f" — \`plugin\` says it should come from \`{plugin}\`"`.
  `test_an_unresolved_template_name_names_the_plugin_the_config_points_at` must FAIL on its control
  half: the second config declares `plugin: None`, so the mutant renders "`plugin` says it should
  come from `None`", and the test asserts "`plugin` says" is absent. **Checked against the body:**
  the control asserts on the *connective* rather than only on the value, which is what makes it
  discriminate — an assertion on `"someuser/publishable-llm" not in plain` alone would pass under
  this mutant.

  **(b) Interpolate the hint at the call site instead of in the shared message.** In `validate.py`,
  revert to `unknown_template_message(name, known)` and append the hint to the returned string.
  **This mutation cannot be caught by any test in the suite** — the rendered message is identical.
  Stated here rather than prescribed: the property at stake is that the two surfaces share one
  wording, and the only thing enforcing it is that `generate_experiment` has no hint to append.
  **Do not run this one**; it is recorded so nobody proposes it as proof of the shared-message
  property, which no test holds.

  Revert (a) by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 8: Which deliverable no mutation reaches.** **The `generate experiment` emit site is
      unpinned for the hint** — it passes `None` and no test asserts that it does, because the
      message it produces is byte-identical to the one it produced before this task. `tests/` does
      cover that site for the code itself; the *absence* of a hint there is not covered and nothing
      in this slice covers it. **The `isinstance` guard on `plugin`** is pinned by nothing either: no
      test declares a non-string `plugin`. Both stated; neither is closed later.

- [ ] **Step 9: Verify and commit.** All four commands.
      `feat: an unresolved experiment_type names the plugin the config points at`

---

## Task 12: `register_resolver`, exported

**Files:** Modify `src/publishable/plugins.py`, `src/publishable/__init__.py`,
`docs/reference.md`, `tests/test_plugins.py`.

**Interfaces:**
- Consumes: `publishable/__init__.py`'s import block and its `__all__`, which today lists
  `ArtifactError`, `ArtifactExistsError`, `BaseExperiment`, `BaseStep`, `BaseTemplate`,
  `ContractError`, `Estimate`, `Param`, `PublishableError`, `Unit`, `register_template`;
  `discovery.register_template(name) -> Callable[[type[BaseTemplate]], type[BaseTemplate]]`, the
  shape every registry decorator follows — record and return unchanged.
- Produces: `plugins.RESOLVERS: dict[str, Callable[..., Any]]`;
  `plugins.register_resolver(name: str) -> Callable[[F], F]`, exported from `publishable`; the
  § The importable surface `Status` cell for `register_resolver` moved to `built`.

**What this task deliberately does not build, and where it says so.** `register_resolver` fills a
mapping when a plugin module is imported, and **nothing in Part A imports a plugin module.** So the
decorator has no production caller in this slice and `RESOLVERS` is populated only by a test. That
is not the shipped-but-unread shape the traps name — `register_probe` is, and task 13 ships its
reader for exactly that reason. A resolver's reader is `resolve_units`' dispatch, which is Part B
task 23, and this task's own text names it. **The export is what a plugin author needs to be able to
write the plugin at all**, which is the whole of what Part A promises.

**Return the object unchanged.** `register_template`'s decorator returns `cls` so
`class X(BaseTemplate)` still resolves for every later reference to `X`; a resolver is a plain
function and the same rule applies for the same reason — `@register_resolver("plate_wells")` above
`def resolve(io, cfg)` must leave `resolve` callable from the module that defined it.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_plugins.py`:

```python
def test_register_resolver_records_the_name_and_returns_the_function(registries):
    """The decorator's two obligations. Returning the object unchanged is the
    half a decorator gets wrong silently: a `None` return leaves the plugin's own
    module holding `None` under the name it just defined, and its own test suite
    is where that surfaces."""
    from publishable.plugins import RESOLVERS, register_resolver

    @register_resolver("plate_wells")
    def resolve(io, cfg):
        return ["a unit"]

    assert RESOLVERS["plate_wells"] is resolve
    assert resolve(None, None) == ["a unit"]  # still callable under its own name


def test_a_resolver_is_importable_from_the_one_root():
    """`reference.md` § The importable surface: everything you write against is
    imported from `publishable` itself. A plugin importing
    `publishable.plugins.register_resolver` is not a supported spelling even
    where it works."""
    import publishable

    assert "register_resolver" in publishable.__all__
    assert publishable.register_resolver is not None
```

      and add the registry-restoring fixture to `tests/conftest.py`, beside `installed`. It goes
      there rather than in `tests/test_plugins.py` because `tests/test_artifacts.py` needs it in
      task 15 and a fixture defined in one test module is invisible from another — putting it in
      one file now and moving it in three tasks' time is churn with a chance to forget:

```python
@pytest.fixture
def registries():
    """Restore the process-level plugin registries around a test that fills them.

    These mappings are module-global by design — a decorator runs at import and
    has nowhere else to put what it recorded — so a test that registers a name
    leaks it into every test after it. Restored by snapshot rather than by
    unsetting what was seen, which covers a test that replaces an entry as well
    as one that adds it. A plain fixture requested by name: the suite's one
    autouse fixture is `conftest`'s environ restore and there may not be a
    second.
    """
    from publishable import artifacts, plugins

    saved = (
        dict(plugins.RESOLVERS),
        dict(plugins.PROBES),
        dict(artifacts.WRITERS),
        dict(artifacts.READERS),
    )
    yield
    for live, was in zip(
        (plugins.RESOLVERS, plugins.PROBES, artifacts.WRITERS, artifacts.READERS),
        saved,
        strict=True,
    ):
        live.clear()
        live.update(was)
```

      **`PROBES`, `WRITERS` and `READERS` are named here although tasks 13, 14 and 15 create them**
      — write the fixture whole in this task and let those tasks use it, rather than growing it
      three times and leaving three chances to forget one. That means this task defines `PROBES` in
      `plugins.py` too, as an empty mapping with no decorator; task 13 adds the decorator. Say so in
      the commit message.

- [ ] **Step 2: Run and see it fail.** `ImportError: cannot import name 'register_resolver'`.

- [ ] **Step 3: Implement.** In `src/publishable/plugins.py`, add to the imports
      `from collections.abc import Callable` and `from typing import Any, TypeVar`, then:

```python
F = TypeVar("F", bound=Callable[..., Any])

RESOLVERS: dict[str, Callable[..., Any]] = {}
"""Every resolver a plugin module registered, by the name a config writes.

Module-global because a decorator runs when a plugin is imported and has nowhere
else to put what it recorded. That is the opposite arrangement from
`templates/registry.py`'s per-call merge, and for a reason that does not apply
here: two projects resolved in one process must never see each other's
`templates/`, but an installed distribution is the same distribution for both.
"""

PROBES: dict[str, Callable[..., Any]] = {}
"""Every apparatus probe a plugin module registered. See `RESOLVERS`."""


def register_resolver(name: str) -> Callable[[F], F]:
    """Record `name -> fn` for this process and return `fn` unchanged.

    The entry point is the registration and this argument is a declaration
    checked against it — `reference.md` § Creating a plugin — so this records
    what the source says and `check_registration` is what compares the two.
    Returned unchanged so the plugin's own module keeps a callable under the
    name it just defined, which is what makes the artifact testable in its own
    suite.
    """

    def decorator(fn: F) -> F:
        RESOLVERS[name] = fn
        return fn

    return decorator
```

      In `src/publishable/__init__.py`, add `from publishable.plugins import register_resolver` and
      `"register_resolver"` to `__all__`, keeping both alphabetical — `ruff`'s `I` rule sorts the
      imports and `__all__` is hand-sorted today, so put it after `"register_template"`? **No:
      `"register_resolver"` sorts before `"register_template"`.** Place it there and confirm by
      reading the list rather than by assuming.

- [ ] **Step 4: Move the `Status` cell.** In § The importable surface, task 3 split the `not yet
      built` row in two. The row whose `Name` cell is `` `register_resolver` · `register_probe` ``
      must now be split again so the two names can carry different statuses:

```
| `register_resolver` | decorator | built | The registry a [`data.units.from.resolver`](#where-units-come-from) name resolves through — see [Creating a plugin](#creating-a-plugin-publishable-plugin-new) |
| `register_probe` | decorator | not yet built | The registry an [`apparatus_probe`](#the-apparatus-core-can-only-observe) name resolves through — see [Creating a plugin](#creating-a-plugin-publishable-plugin-new) |
```

      Splitting rather than rewriting the prose beneath: the sentence "Importing one raises
      `ImportError` today" derives its claim from the `Status` column, and it stays true and
      self-maintaining only while each name's status is its own cell. Also update § The importable
      surface's fenced import example, which already reads
      `from publishable import BaseStep, Estimate, Unit, register_resolver` — read it and confirm no
      change is needed.

- [ ] **Step 5: Run and see them pass** — and run **`uv run pytest -q` whole**, not
      `tests/test_plugins.py` alone. The fixture added in step 1 lives in `tests/conftest.py`, and a
      `conftest.py` that raises at collection fails every file in the suite while collecting one
      file says nothing. Expected: predecessor's count **+ 2**.

- [ ] **Step 6: Mutate — two.**

  **(a) Return `None` from the decorator.** Change `return fn` to `return None` (and let `mypy`
  complain — run the test before fixing the type error).
  `test_register_resolver_records_the_name_and_returns_the_function` must FAIL on
  `assert resolve(None, None) == ["a unit"]` with `TypeError: 'NoneType' object is not callable`.
  **Checked against the body:** the test calls the decorated name after decorating it, which is the
  only thing that can tell "returns the function" from "records the name"; the `RESOLVERS` assertion
  alone passes under this mutant.

  **(b) Record under a fixed key.** Change `RESOLVERS[name] = fn` to `RESOLVERS["resolver"] = fn`.
  The same test must FAIL on `RESOLVERS["plate_wells"]` with a `KeyError`. **Checked against the
  body:** the test looks the name up rather than checking `len(RESOLVERS)`, so the two branches
  differ.

  Revert each by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 7: Which deliverable no mutation reaches.** **`RESOLVERS` has no production reader in
      this slice** — nothing in `src/` looks a resolver up, so a decorator that recorded into a
      throwaway dict would pass every test here. **Part B task 23 closes it**, where `resolve_units`
      dispatches through this mapping. Named rather than hidden, and it is the reason this task is
      *not* the shipped-but-unread shape task 13 guards against: a resolver's reader has an owner
      and a task number, and `register_probe`'s did not until task 13 gave it one.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: register_resolver, exported — and the registry-restoring fixture the next three tasks use`

---

## Task 13: `register_probe`, and the check that reads it

**Files:** Modify `src/publishable/plugins.py`, `src/publishable/__init__.py`,
`src/publishable/validate.py`, `src/publishable/generators/template.py`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `tests/test_plugins.py`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `plugins.PROBES` and the decorator shape from task 12; `plugins.names(group)` from task
  7; `BaseTemplate.apparatus_probe: str | None`, declared on the base class and **read by nothing**
  at this commit; `validate_config`'s check sequence, which calls `_check_required_env` and
  `_check_requires_env` from the resolved template before setting `c.credentials`.
- Produces: `plugins.register_probe`, exported; `validate._check_probe(template, c) -> None`
  emitting `E-PROBE-UNKNOWN`; § Validation's *Probe is installed* row backed by a real emit site.

**Why the export and the reader ship together, and it is the trap this task is named in.**
`register_probe` exported bare would be the **fourth** declarable-and-unread surface beside
`field_convention`, `apparatus_probe` and `apparatus_facts` — and the first *exported* one.
`CLAUDE.md` names the distinction precisely: an unbuilt reader of an **unbuilt** surface is
specification, and an unbuilt reader of a **shipped** surface is a defect. So the § Validation
*Probe is installed* row is what consumes it, and that means `validate` reading
`BaseTemplate.apparatus_probe` for the first time. Not defensible as a bare export, and this task
does not attempt it.

**What it is still not.** `Apparatus`, probe execution, the ledger, per-condition facts and the
change gate are **H7d**. This ships registration and the is-it-registered answer, and only because
that row consumes it.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_plugins.py`:

```python
def test_register_probe_records_the_name_and_returns_the_function(registries):
    from publishable.plugins import PROBES, register_probe

    @register_probe("assay_instrument")
    def probe(cfg):
        return {"model": "x"}

    assert PROBES["assay_instrument"] is probe
    assert probe(None) == {"model": "x"}


def test_a_probe_is_importable_from_the_one_root():
    import publishable

    assert "register_probe" in publishable.__all__
```

      and a template fixture plus two tests to `tests/test_validate.py`:

```python
_PROBING_TEMPLATE = """\
from publishable import BaseTemplate, register_template


@register_template("probing")
class Probing(BaseTemplate):
    apparatus_probe = "assay_instrument"
    parameter_spec = {}
"""


def test_a_declared_probe_no_distribution_registers_is_reported(git_repo, write_config):
    """The first reader `BaseTemplate.apparatus_probe` has ever had.

    Answered from metadata, so an absent name costs no import — which is also why
    this reports rather than raising: nothing was loaded to fail.
    """
    templates = git_repo / "templates"
    templates.mkdir()
    (templates / "probing.py").write_text(_PROBING_TEMPLATE)

    found = messages_by_code(write_config({"experiment_type": "probing", "parameters": {}}))
    message = found["E-PROBE-UNKNOWN"]
    assert "assay_instrument" in message
    assert "publishable.probes" in message


def test_an_installed_probe_satisfies_the_check_and_a_template_declaring_none_draws_nothing(
    installed, git_repo, write_config
):
    """THE HONOURING, and the control in one test.

    Without the first half, a `_check_probe` that reported unconditionally passes
    the refusal test above. Without the second, one that reported for every
    template — including `generic`, which declares no probe — would too.
    """
    templates = git_repo / "templates"
    templates.mkdir()
    (templates / "probing.py").write_text(_PROBING_TEMPLATE)
    installed("dist-one", "1.0", {"publishable.probes": {"assay_instrument": "no_one:probe"}})

    assert "E-PROBE-UNKNOWN" not in codes(
        write_config({"experiment_type": "probing", "parameters": {}})
    )
    assert "E-PROBE-UNKNOWN" not in codes(write_config())  # `generic` declares none
```

- [ ] **Step 2: Run and see them fail.** The plugins tests on `ImportError`, the validate tests on
      `KeyError: 'E-PROBE-UNKNOWN'`. **The honouring test fails on its first assertion only if the
      check exists**; before the implementation it passes vacuously, which is expected — a control
      proves nothing until its sibling passes, and this one is written to go red under the
      mutations in step 6 rather than here.

- [ ] **Step 3: Implement.** In `plugins.py`, beside `register_resolver`:

```python
def register_probe(name: str) -> Callable[[F], F]:
    """Record `name -> fn` for this process and return `fn` unchanged. See
    `register_resolver` for why the mapping is module-global and why the object
    comes back untouched."""

    def decorator(fn: F) -> F:
        PROBES[name] = fn
        return fn

    return decorator
```

      Export it from `publishable/__init__.py` and add `"register_probe"` to `__all__` in sorted
      position — read the list rather than assuming where that is.

      In `validate.py`:

```python
def _check_probe(name: str, template: Any, c: Collector) -> None:
    """The resolved template's `apparatus_probe` against the installed probes.

    Read from package metadata, so a name no distribution declares is refused
    without importing one — the same guarantee every other plugin name is
    answered under. Reported at `experiment_type` because the declaration is the
    template's rather than the config's: a reader who cannot install the plugin
    changes which template the experiment uses, and `experiment_type` is where
    that decision is written.

    Takes the registered name rather than recovering it from the class, which
    cannot be done: a class knows what it was decorated with only until the
    pending buffer is drained, and `validate_config` is holding the name anyway.

    A template declaring no probe is the ordinary case and draws nothing —
    `reference.md` § The apparatus core can only observe: an experiment whose
    measurements never leave the machine declares nothing and records
    `apparatus: null`.
    """
    declared = getattr(template, "apparatus_probe", None)
    if not isinstance(declared, str) or not declared:
        return
    known = names("publishable.probes")
    if declared in known:
        return
    listed = ", ".join(known) if known else "none installed"
    c.error(
        "E-PROBE-UNKNOWN",
        "experiment_type",
        f"resolves template `{name}`, which declares `apparatus_probe: {declared}` — "
        "a name no installed distribution registers in the `publishable.probes` "
        f"entry-point group (registered: {listed})",
    )
```

      Call it as `_check_probe(name, template, c)` from `validate_config`, immediately after `_check_requires_env`, which is the nearest
      check that also reads a declaration off the resolved template rather than off the config —
      name that neighbour in the commit message. **Placing it before the `c.credentials` line is
      deliberate and load-bearing:** a finding appended before that line is still redacted at
      `render`, because redaction happens at render and `Diagnostic` is a frozen record, and moving
      the check after it would look identical while quietly depending on ordering. Do **not** move
      the `c.credentials` line to accommodate it — Global Constraints forbids that outright.

- [ ] **Step 4: Falsify the comment `generators/template.py` carries.** Task 10 rewrote that comment
      and left "`field_convention`, `apparatus_probe` and `apparatus_facts` are declared on the base
      class and read by nothing in this build." That is now false. **Sweep for the claim, not for
      the file** — `grep -rn "read by nothing\|apparatus_probe" src/ docs/reference.md docs/superpowers/spec-defects.md`
      and read every hit — then correct each:

```python
# `field_convention` and `apparatus_facts` are declared on the base class and
# read by nothing in this build; `apparatus_probe` is read (`validate` checks it
# against the installed probes) but a stub declaring `None` would only ever
# satisfy that check trivially.
```

- [ ] **Step 5: Amend the `spec-defects.md` entry that names the family.** That file carries
      `## OPEN — BaseTemplate.field_convention is declarable and read by nothing`. Read it: if it
      names `apparatus_probe` as a sibling, append an amendment saying `apparatus_probe` gained a
      reader in H7b Part A task 13 and the family is now `field_convention` and `apparatus_facts`.
      **Do not restate the whole entry** and do not retro-edit its original text — a correction is
      appended in the development record.

- [ ] **Step 6: Also amend `CLAUDE.md`'s worked example if it still points here.** `CLAUDE.md`
      § Misreadings' *unbuilt reader of a shipped surface* row cites a member of this family. Read
      it; if it names `apparatus_probe`, move it to `field_convention`, which is still unread. If it
      already names `field_convention`, leave it and say so in the report. **This is the one file
      outside the four documents that a task may edit here**, and only because the re-scoping's § 9b
      names the obligation.

- [ ] **Step 7: Run and see them pass**, then the whole suite. Expected: predecessor's count **+ 4**.

- [ ] **Step 8: Mutate — three.**

  **(a) Delete the check's call site.** Remove `_check_probe(...)` from `validate_config`.
  `test_a_declared_probe_no_distribution_registers_is_reported` must FAIL with
  `KeyError: 'E-PROBE-UNKNOWN'`. **Checked against the body:** the test indexes `messages_by_code`
  by that code, so a missing finding is a `KeyError` rather than a silent pass. This is the mutation
  that proves the export has a reader at all, which is the whole reason this task exists.

  **(b) Report regardless of the installed set.** Change `if declared in known: return` to
  `if False: return`. `test_an_installed_probe_satisfies_the_check_and_a_template_declaring_none_draws_nothing`
  must FAIL on its **first** assertion. **Checked against the body:** the fixture installs a
  distribution declaring exactly that probe name, so the two branches genuinely differ; without the
  installed distribution the test could not tell this mutant from correct code, which is why it
  takes the `installed` fixture.

  **(c) Report for a template declaring no probe.** Change the guard to
  `if declared is None: declared = "?"` — i.e. drop the early return. The same test must FAIL on its
  **second** assertion, where `generic` declares nothing. **Checked against the body:** the second
  assertion runs `write_config()` with no override, so the resolved template is `generic`, whose
  `apparatus_probe` is `None`. This is the mutation the second half of that test exists for, and the
  reason both halves live in one test rather than two.

  Revert each by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 9: Which deliverable no mutation reaches.** **`PROBES` has no production reader** —
      `_check_probe` reads the *metadata* scan, not the decorator's mapping, because answering from
      metadata is the guarantee and the decorator's mapping is only populated once a plugin has been
      imported. **H7d closes it**, where a probe is actually executed. So `register_probe` is
      exported with a reader for the *name* and none for the *object*, which is a narrower claim
      than "it ships with its reader" and is the true one — say so in the task report. The
      `E-PROBE-UNKNOWN` message's *path* (`experiment_type`) is unpinned, as every finding path in
      this slice is.

- [ ] **Step 10: Verify and commit.** All four commands.
      `feat: register_probe, and the Probe-is-installed check that reads apparatus_probe`

---

## Task 14: `register_writer`, and the refusal of a core-suffix claim

**Files:** Modify `src/publishable/plugins.py`, `src/publishable/artifacts.py`,
`src/publishable/__init__.py`, `docs/reference.md`, `tests/test_plugins.py`.

**Interfaces:**
- Consumes: `artifacts.WRITERS`, a module dict whose keys are `.json`, `.yaml`, `.jsonl`, `.csv`,
  `.parquet`; `artifacts._suffix_for(name: str) -> str | None`, which lower-cases the name's last
  path component and returns the **longest** registered suffix of it, iterating `WRITERS`;
  `artifacts.StepIO.write(self, name, obj) -> Path`, which calls `WRITERS[suffix](obj)` when
  `_suffix_for` answers.
- Produces: `artifacts.CORE_SUFFIXES: frozenset[str]`, snapshotted at import;
  `plugins.register_writer(suffix: str) -> Callable[[F], F]`, exported, writing straight into
  `artifacts.WRITERS`; a `ContractError` · `E-PLUGIN-COLLISION` for a suffix core itself writes.

**One table, not two.** `register_writer` writes into `artifacts.WRITERS` rather than keeping a
mapping of its own, because `io.write` dispatches through `_suffix_for`, which iterates `WRITERS`,
and a second table would be a second source of truth for "what suffix does core know" — the
defaults-file problem in a dict. `plugins.py` importing `artifacts` introduces no cycle:
`artifacts` imports `coercion`, `errors` and `sweep`, none of which reaches back.

**The key space here is an extension, not a name**, which is why the refusal is a *shadow* check
rather than a *duplicate* check. Two distributions claiming one extension is task 8's
`E-PLUGIN-COLLISION` over the `publishable.writers` group, decided from metadata and reported by
`validate`; a plugin claiming an extension **core** writes is decided here, at registration, because
core's own table is not in anyone's metadata. **One code, two decision points, deliberately** —
§ Creating a plugin's "A name is claimed once" paragraph puts both in one sentence, and splitting
the code would make a reader grep two.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_plugins.py`:

```python
def test_a_third_party_suffix_reaches_io_write_s_dispatch(registries, tmp_path):
    """Registration is only real if `io.write` finds it, so the assertion is over
    the dispatch rather than over the dict — `_suffix_for` is what decides, and
    it iterates `WRITERS`."""
    from publishable import artifacts
    from publishable.plugins import register_writer

    @register_writer(".fastq.gz")
    def write_fastq(rows):
        return b"@read\n"

    assert artifacts._suffix_for("sample.fastq.gz") == ".fastq.gz"
    assert artifacts.WRITERS[".fastq.gz"] is write_fastq

    # The longest registered suffix still wins, which is what a compound
    # extension is registered for: `.gz` alone must not claim this name.
    @register_writer(".gz")
    def write_gz(rows):
        return b""

    assert artifacts._suffix_for("sample.fastq.gz") == ".fastq.gz"


def test_a_writer_may_not_claim_a_suffix_core_writes(registries):
    """A plugin that could redefine `.csv` could change what an artifact means
    without changing the step that wrote it."""
    from publishable.errors import ContractError
    from publishable.plugins import register_writer

    with pytest.raises(ContractError) as excinfo:

        @register_writer(".csv")
        def write_csv(rows):
            return b""

    assert excinfo.value.code == "E-PLUGIN-COLLISION"
    message = str(excinfo.value)
    assert ".csv" in message
    assert "core" in message


def test_a_suffix_core_does_not_write_is_accepted(registries):
    """THE CONTROL, and the honouring: a refusal that fired for every suffix
    would pass the test above. Paired here rather than left implicit."""
    from publishable import artifacts
    from publishable.plugins import register_writer

    @register_writer(".fastq")
    def write_fastq(rows):
        return b""

    assert ".fastq" in artifacts.WRITERS
```

- [ ] **Step 2: Run and see them fail.** `ImportError: cannot import name 'register_writer'`.

- [ ] **Step 3: Implement.** In `src/publishable/artifacts.py`, immediately beneath the `READERS`
      dict:

```python
CORE_SUFFIXES = frozenset(WRITERS)
"""The suffixes core itself writes, fixed at import.

Snapshotted rather than read live, because `plugins.register_writer` adds to
`WRITERS` and a shadow check reading the live table would start refusing one
plugin's suffix on behalf of another's. What a plugin may not claim is what
*core* writes, which is a property of this file and not of what is installed.
"""
```

      In `src/publishable/plugins.py`, add `from publishable.artifacts import CORE_SUFFIXES, WRITERS`
      and `from publishable.errors import ContractError`, then:

```python
def register_writer(suffix: str) -> Callable[[F], F]:
    """Record a writer for `suffix` in the table `io.write` dispatches through.

    One table rather than a registry of its own: `io.write` finds a writer with
    `_suffix_for`, which iterates `artifacts.WRITERS`, and a second mapping would
    be a second answer to "what suffix does core know".

    A suffix core itself writes is refused here rather than resolved by import
    order — `reference.md` § Creating a plugin — because a plugin that could
    redefine `.csv` could change what an artifact means without changing the step
    that wrote it. Two *plugins* claiming one suffix is the other half of the same
    rule and is decided from entry-point metadata by `validate`, since core's own
    table appears in nobody's metadata and an installed pair appears in no table.
    """

    def decorator(fn: F) -> F:
        if suffix in CORE_SUFFIXES:
            raise ContractError(
                f"a writer claims `{suffix}`, which core itself writes — a plugin that "
                "could redefine a core suffix could change what an artifact means "
                "without changing the step that wrote it. Claim a suffix of your own",
                code="E-PLUGIN-COLLISION",
            )
        WRITERS[suffix] = fn
        return fn

    return decorator
```

      Export it from `publishable/__init__.py` and add `"register_writer"` to `__all__` in sorted
      position.

- [ ] **Step 4: Move the `Status` cell and correct one document claim.** In § The importable
      surface, task 3's row `` `register_writer` · `register_reader` `` must split so the two
      statuses differ; `register_writer` becomes `built`, `register_reader` stays `not yet built`
      until task 15:

```
| `register_writer` | decorator | built | The registry an artifact suffix's writer is claimed through — see [Steps and artifacts](#steps-and-artifacts) |
| `register_reader` | decorator | not yet built | Its inverse, which `io.read_upstream` dispatches through — see [Steps and artifacts](#steps-and-artifacts) |
```

      In § Errors core raises, the `E-PLUGIN-COLLISION` row task 2 wrote already names the
      core-suffix case; read it and confirm it does, and change nothing if so.

- [ ] **Step 5: Run and see them pass**, then the whole suite. **`tests/test_artifacts.py` is the
      regression surface** — `WRITERS` and `READERS` are module dicts and a test that leaks a key
      breaks unrelated dispatch. Run `uv run pytest tests/test_artifacts.py -q` on its own **and**
      then the whole suite in one process, and compare: a `registries` fixture that fails to restore
      shows as a pass alone and a failure together. Expected total: predecessor's count **+ 3**.

- [ ] **Step 6: Mutate — three.**

  **(a) Write into a private table.** Change `WRITERS[suffix] = fn` to a module-level
  `_PLUGIN_WRITERS[suffix] = fn`. `test_a_third_party_suffix_reaches_io_write_s_dispatch` must FAIL
  on its `_suffix_for` assertion. **Checked against the body:** the assertion is over the dispatch
  function, not over a dict this task controls, so a second table cannot satisfy it. **This is the
  mutation that pins "one table, not two"**, and the `WRITERS[".fastq.gz"] is write_fastq`
  assertion alone would not.

  **(b) Read the live table for the shadow check.** Change `if suffix in CORE_SUFFIXES:` to
  `if suffix in WRITERS:`. **Nothing in the suite goes red**, and that is worth knowing before it is
  believed: no test registers one plugin suffix and then a second plugin's identical one. **Add the
  fixture that discriminates** rather than accepting a blind mutation — append to
  `test_a_suffix_core_does_not_write_is_accepted`:

```python
    # A second plugin claiming the SAME suffix is not this check's refusal — it
    # is decided from entry-point metadata, where both claimants are visible.
    # Registering twice in one process is what a plugin's own test suite does,
    # and refusing it here would refuse that.
    @register_writer(".fastq")
    def write_fastq_again(rows):
        return b""

    assert artifacts.WRITERS[".fastq"] is write_fastq_again
```

  With that appended, mutation (b) makes the test FAIL on the second registration's raise. Run the
  mutation **after** adding the assertion, and record in the task report that the mutation was blind
  until the fixture was sized for it.

  **(c) Refuse nothing.** Delete the `if suffix in CORE_SUFFIXES:` raise.
  `test_a_writer_may_not_claim_a_suffix_core_writes` must FAIL with `DID NOT RAISE`. **Checked
  against the body:** it wraps the decoration in `pytest.raises`, so the absence of the raise is the
  failure. Note this mutation also leaves `.csv` overwritten in `WRITERS` — the `registries` fixture
  restores it, which is the fixture doing its job; if a later test in the same run fails on CSV
  encoding, the fixture is wrong and that is the finding.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green.

- [ ] **Step 7: Which deliverable no mutation reaches.** **`CORE_SUFFIXES`' membership** is a
      snapshot of a literal and a mutation adding a suffix to `WRITERS` above the snapshot line
      would change both together — unavoidable for a derived constant, and the reason the docstring
      states what it is rather than listing it. **`register_writer` has no production caller**: no
      plugin is imported in this slice, so `WRITERS` is only ever extended by a test. The reader for
      the *object* arrives when a plugin is loaded at `run`, which no task here owns; task 15 makes
      the *table's* invariant enforceable, which is the half that is closable now.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: register_writer feeds io.write's own table, and refuses a suffix core writes`

---

## Task 15: `WRITERS`/`READERS` symmetry, made an enforced invariant

**Files:** Modify `src/publishable/plugins.py`, `src/publishable/artifacts.py`,
`src/publishable/__init__.py`, `docs/reference.md`, `docs/superpowers/spec-defects.md`,
`tests/test_plugins.py`, `tests/test_artifacts.py`.

**Interfaces:**
- Consumes: `artifacts.StepIO._read(path: Path) -> Any`, a `@staticmethod` whose body is
  `suffix = _suffix_for(path.name)` / `if suffix is not None: return READERS[suffix](path.read_bytes())`
  / `return path.read_bytes()`, and whose docstring reads "Inverts the same table `write` dispatches
  through — see `WRITERS`/`READERS`"; `artifacts.READERS`, the five-key inverse;
  `errors.ArtifactError(message, *, code)`.
- Produces: `plugins.register_reader(suffix: str) -> Callable[[F], F]`, exported, writing into
  `artifacts.READERS`; `_read` raising `ArtifactError` · `E-ARTIFACT-UNREADABLE` for a suffix
  `WRITERS` holds and `READERS` does not; `_read`'s docstring corrected; the `spec-defects.md` entry
  task 3 filed, struck.

**The defect, proved by mutation rather than by reading.** The re-scoping's § 5(a) probed it live:
adding `.fastq` to `WRITERS` alone and calling `StepIO._read(Path('a.fastq'))` raised a bare
`KeyError('.fastq')`; deleting the key restored `b'x'`. `_read`'s docstring says it inverts the
table `write` dispatches through, and it does not — it *dispatches* on `WRITERS` and *indexes*
`READERS`, which is true only by the coincidence that the two hold the same keys. § Steps and
artifacts' promise that "what a writer takes is what its reader gives back" is the thing that breaks.

**The mutation that can fail is adding a key to one dict only.** Swapping a *value* between the two
cannot fail — they hold the same keys, so the two branches cannot differ. This is stated in the
scoping and repeated here because it is the exact shape of a blind mutation.

**`E-ARTIFACT-UNREADABLE` is minted here**, in § Errors core raises, beside the `ArtifactError`
family's existing three codes. It is not an `-UNSUPPORTED` refusal and it carries a row.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_artifacts.py`:

```python
def test_a_suffix_with_a_writer_and_no_reader_is_a_coded_refusal(registries, tmp_path):
    """The bare `KeyError` § Steps and artifacts' promise breaks on.

    The mutation that can fail is adding a key to ONE dict — swapping a value
    between them cannot, since both hold the same keys.
    """
    from publishable import artifacts
    from publishable.errors import ArtifactError

    artifacts.WRITERS[".fastq"] = lambda rows: b"x"
    target = tmp_path / "a.fastq"
    target.write_bytes(b"x")

    with pytest.raises(ArtifactError) as excinfo:
        artifacts.StepIO._read(target)
    assert excinfo.value.code == "E-ARTIFACT-UNREADABLE"
    assert ".fastq" in str(excinfo.value)

    # THE CONTROL, produced by the code under test: with the reader supplied,
    # the same path reads. Without this the assertion above would pass for a
    # `_read` that refused every unknown suffix, including the ones it is
    # supposed to hand back as raw bytes.
    artifacts.READERS[".fastq"] = lambda data: {"read": data.decode()}
    assert artifacts.StepIO._read(target) == {"read": "x"}


def test_a_suffix_neither_table_knows_is_still_raw_bytes(tmp_path):
    """The behaviour that must survive the refusal above: an unregistered suffix
    is bytes, and always was."""
    from publishable import artifacts

    target = tmp_path / "a.bin"
    target.write_bytes(b"\x00\x01")
    assert artifacts.StepIO._read(target) == b"\x00\x01"
```

      and to `tests/test_plugins.py`:

```python
def test_register_reader_completes_the_pair_io_read_upstream_needs(registries, tmp_path):
    """Registering both halves is what a plugin does, and the pair is what makes
    the round trip real — asserted as a round trip rather than as two dict
    entries, since two entries is what the broken state also looks like."""
    from publishable import artifacts
    from publishable.plugins import register_reader, register_writer

    @register_writer(".fastq")
    def write_fastq(rows):
        return "|".join(rows).encode()

    @register_reader(".fastq")
    def read_fastq(data):
        return data.decode().split("|")

    target = tmp_path / "a.fastq"
    target.write_bytes(artifacts.WRITERS[".fastq"](["a", "b"]))
    assert artifacts.StepIO._read(target) == ["a", "b"]


def test_a_reader_may_not_claim_a_suffix_core_reads(registries):
    from publishable.errors import ContractError
    from publishable.plugins import register_reader

    with pytest.raises(ContractError) as excinfo:

        @register_reader(".csv")
        def read_csv(data):
            return []

    assert excinfo.value.code == "E-PLUGIN-COLLISION"
```

      `tests/test_artifacts.py` needs the `registries` fixture, which task 12 already put in
      `tests/conftest.py` for exactly this reason — request it by name and add nothing. Confirm it
      is there before writing the test; if it is in `tests/test_plugins.py` instead, task 12 was
      implemented against a stale brief and moving it is this task's first step.

- [ ] **Step 2: Run and see them fail.** The artifacts test fails with `KeyError: '.fastq'` — the
      defect itself, reproduced — and the plugins tests on `ImportError`.

- [ ] **Step 3: Implement.** In `src/publishable/artifacts.py`, replace `_read` whole:

```python
    @staticmethod
    def _read(path: Path) -> Any:
        """Reads back what `write` wrote, through the inverse of the table it
        dispatched on.

        Two tables and one dispatch: `_suffix_for` decides from `WRITERS`, and
        the reader is then looked up in `READERS`. That is an inversion only
        while the two hold the same keys, which core's own five do and a plugin's
        pair need not — so the gap is a coded refusal rather than the bare
        `KeyError` it was, and § Steps and artifacts' promise that what a writer
        takes is what its reader gives back is stated where it can be enforced.
        A suffix *neither* table knows is not a fault at all: it is the raw-bytes
        case `write` already accepts.
        """
        suffix = _suffix_for(path.name)
        if suffix is None:
            return path.read_bytes()
        reader = READERS.get(suffix)
        if reader is None:
            raise ArtifactError(
                f"`{path.name}` claims the suffix `{suffix}`, which has a registered "
                "writer and no reader — a writer and its reader are registered as a "
                "pair, and core cannot invert one it was never given",
                code="E-ARTIFACT-UNREADABLE",
            )
        return reader(path.read_bytes())
```

      `ArtifactError` is already imported in that module. In `src/publishable/plugins.py`, add
      `READERS` to the `artifacts` import and:

```python
def register_reader(suffix: str) -> Callable[[F], F]:
    """Record a reader for `suffix`, the inverse `io.read_upstream` dispatches to.

    Refuses a core suffix for the reason `register_writer` does, and under the
    same code: the pair is one claim on one extension, so redefining half of it
    is redefining it.
    """

    def decorator(fn: F) -> F:
        if suffix in CORE_SUFFIXES:
            raise ContractError(
                f"a reader claims `{suffix}`, which core itself reads — a plugin that "
                "could redefine a core suffix could change what an artifact means "
                "without changing the step that wrote it. Claim a suffix of your own",
                code="E-PLUGIN-COLLISION",
            )
        READERS[suffix] = fn
        return fn

    return decorator
```

      Export it and add `"register_reader"` to `__all__` in sorted position.

- [ ] **Step 4: Document it.** Add a row to § Errors core raises' table, beside the row that reports
      an extension **no writer claims** handed a non-`bytes` object — name that sibling by what it
      does:

```
| [Reading](#steps-and-artifacts) a name whose suffix has a registered writer and no reader. A writer and its reader are [registered as a pair](#creating-a-plugin-publishable-plugin-new), through two entry-point groups, because `io.write` dispatches on the writer table and `io.read_upstream` looks up the reader table — an inversion only while the two hold the same keys. A suffix *neither* table knows is not this fault: that is the raw-bytes case `io.write` already accepts, and it reads back as bytes | `ArtifactError` · `E-ARTIFACT-UNREADABLE` |
```

      Move § The importable surface's `register_reader` `Status` cell to `built`.

- [ ] **Step 5: Strike the defects entry.** Read the `## STRUCK 2026-08-16 — publishable.readers had
      no entry-point group` entry task 3 wrote and confirm every claim in it is now true — the group
      is documented, the decorator exists, and the refusal is coded. If any is not, fix the code
      rather than the entry.

- [ ] **Step 6: Run and see them pass**, then the whole suite. Expected: predecessor's count **+ 4**.
      **`tests/test_artifacts.py` in full is the regression surface** — every `io.write`/`_read`
      round trip for the five core suffixes must be untouched, since `READERS.get` returns the same
      callables `READERS[...]` did for every key that exists.

- [ ] **Step 7: Mutate — three.**

  **(a) Restore the bare index.** Change `reader = READERS.get(suffix)` / the `None` guard back to
  `return READERS[suffix](path.read_bytes())`.
  `test_a_suffix_with_a_writer_and_no_reader_is_a_coded_refusal` must FAIL with `KeyError` raised
  where `ArtifactError` was expected. **Checked against the body:** the test adds `.fastq` to
  `WRITERS` **only**, which is the one arrangement in which the two branches differ. A test that
  swapped a value between the dicts would pass under both.

  **(b) Refuse the raw-bytes case too.** Change `if suffix is None: return path.read_bytes()` to
  raise the same `ArtifactError`. `test_a_suffix_neither_table_knows_is_still_raw_bytes` must FAIL,
  and so must several pre-existing `tests/test_artifacts.py` round trips over unregistered
  extensions. **Checked against the body:** the test writes `a.bin`, whose suffix is in neither
  table, and asserts the bytes come back. This is the mutation that keeps the refusal narrow.

  **(c) Let a reader claim a core suffix.** Delete `register_reader`'s `CORE_SUFFIXES` raise.
  `test_a_reader_may_not_claim_a_suffix_core_reads` must FAIL with `DID NOT RAISE`.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green.

- [ ] **Step 8: Which deliverable no mutation reaches.** **The invariant is enforced at the read,
      not at registration** — a plugin that registers a writer and never a reader is refused only
      when something reads that suffix, and no test asserts that `register_writer` alone leaves the
      tables asymmetric, because asserting that would pin the absence of a check this task
      deliberately did not add. Registering the pair is the plugin author's obligation and the
      diagnostic names it; a registration-time check would have to know whether the reader is
      merely registered *later in the same module*, which it cannot. Stated as a design consequence,
      not a gap: **nothing closes it and nothing should.**

- [ ] **Step 9: Verify and commit.** All four commands.
      `feat: register_reader, and a suffix with no reader is a coded refusal rather than a KeyError`

---

## Task 16: The decorator-vs-key check at load

**Files:** Modify `src/publishable/plugins.py`, `docs/reference.md`, `tests/test_plugins.py`.

**Interfaces:**
- Consumes: `importlib.metadata.EntryPoint`, whose `.name` and `.group` this reads and whose
  `.load()` it does not call; `plugins.RESOLVERS`, `plugins.PROBES`, `artifacts.WRITERS`,
  `artifacts.READERS`.
- Produces: `plugins.check_registration(ep: EntryPoint, declared: Sequence[str]) -> None`, raising
  `ContractError` · `E-PLUGIN-DECORATOR`; `plugins.declared_names(group: str, obj: object) ->
  list[str]`, the names a loaded object is registered under in that group's mapping.

**Why the caller supplies `declared` rather than this function computing it.** The four function
registries map name → object, so "what did this object declare" is a reverse lookup over a mapping
`plugins.py` holds. Templates do not: `register_template` records into `discovery._pending`, which a
discovery pass drains, and reaching into that buffer from here would make one function depend on
whether anything had drained it yet. So the *comparison* lives here, in one place, and each caller
computes the declared names the way its own group records them. `declared_names` is provided for the
four that share a shape.

**`validate` cannot see this disagreement, and that is a property rather than a gap.** The check
compares a decorator argument against an entry-point key, and a decorator argument exists only once
the module has been imported. `validate` answers a name from metadata and never holds the decorated
object. So this is reached at `run` and `dry-run` — **and in Part A it is reached nowhere**, because
nothing here imports a plugin. The task ships the comparison and its unit tests; the call site
arrives with plugin loading, which no task in this slice owns. Stated in the § Errors row task 2
wrote and stated again here.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_plugins.py`:

```python
def test_a_decorator_argument_matching_its_key_is_accepted(registries):
    """The honouring. Without it, a check that raised unconditionally passes
    every refusal below."""
    from importlib.metadata import EntryPoint

    from publishable.plugins import check_registration, declared_names, register_resolver

    @register_resolver("plate_wells")
    def resolve(io, cfg):
        return []

    ep = EntryPoint(name="plate_wells", value="pkg.r:resolve", group="publishable.resolvers")
    assert declared_names("publishable.resolvers", resolve) == ["plate_wells"]
    check_registration(ep, declared_names("publishable.resolvers", resolve))


def test_a_decorator_argument_disagreeing_with_its_key_is_refused(registries):
    """Two spellings of one name with no rule for which is canonical is a drift
    nobody detects until a config names the loser — the defaults-file argument."""
    from importlib.metadata import EntryPoint

    from publishable.errors import ContractError
    from publishable.plugins import check_registration, declared_names, register_resolver

    @register_resolver("plate_positions")
    def resolve(io, cfg):
        return []

    ep = EntryPoint(name="plate_wells", value="pkg.r:resolve", group="publishable.resolvers")
    with pytest.raises(ContractError) as excinfo:
        check_registration(ep, declared_names("publishable.resolvers", resolve))

    assert excinfo.value.code == "E-PLUGIN-DECORATOR"
    message = str(excinfo.value)
    assert "plate_wells" in message      # the key
    assert "plate_positions" in message  # the decorator argument
    assert "pkg.r:resolve" in message    # where to look


def test_an_object_registered_under_several_names_satisfies_any_of_them(registries):
    """One function may serve two keys — a plugin registering the same resolver
    under an old name and a new one is not a disagreement. The check is
    membership, not equality, and a fixture with one name could not tell the two
    readings apart."""
    from importlib.metadata import EntryPoint

    from publishable.plugins import check_registration, declared_names, register_resolver

    def resolve(io, cfg):
        return []

    register_resolver("plate_wells")(resolve)
    register_resolver("plate_positions")(resolve)

    for key in ("plate_wells", "plate_positions"):
        ep = EntryPoint(name=key, value="pkg.r:resolve", group="publishable.resolvers")
        check_registration(ep, declared_names("publishable.resolvers", resolve))


def test_an_object_that_registered_nothing_is_refused_and_says_so(registries):
    """The distinguishable branch: "declared a different name" and "declared no
    name at all" are different mistakes with different remedies, so their
    messages must differ. Pinned separately, because both carry one code."""
    from importlib.metadata import EntryPoint

    from publishable.errors import ContractError
    from publishable.plugins import check_registration

    ep = EntryPoint(name="plate_wells", value="pkg.r:resolve", group="publishable.resolvers")
    with pytest.raises(ContractError) as excinfo:
        check_registration(ep, [])

    message = str(excinfo.value)
    assert "calls no `@register_" in message   # only this branch says this
    assert "declares `" not in message         # and only the other branch says that
```

- [ ] **Step 2: Run and see them fail.** `ImportError: cannot import name 'check_registration'`.

- [ ] **Step 3: Implement.** In `src/publishable/plugins.py`, add
      `from collections.abc import Sequence` to the imports, then:

```python
def _registry_for(group: str) -> dict[str, Callable[..., Any]] | None:
    """The mapping a group's decorator fills, or `None` for a group whose
    registration is not a name-to-object mapping.

    Templates are the `None` case: `register_template` records into a pending
    buffer a discovery pass drains, so what a template class declared is known to
    whoever drained it and not to this module.
    """
    return {
        "publishable.resolvers": RESOLVERS,
        "publishable.probes": PROBES,
        "publishable.writers": WRITERS,
        "publishable.readers": READERS,
    }.get(group)


def declared_names(group: str, obj: object) -> list[str]:
    """Every name `obj` is registered under in `group`'s mapping, in name order.

    A list rather than one name because one function may serve two keys — a
    plugin keeping an old resolver name alongside a new one registers twice — and
    that is not a disagreement.
    """
    registry = _registry_for(group)
    if registry is None:
        return []
    return sorted(name for name, registered in registry.items() if registered is obj)


def check_registration(ep: EntryPoint, declared: Sequence[str]) -> None:
    """The `@register_*` argument against the entry-point key that named it.

    `reference.md` § Creating a plugin: the entry point is the registration and
    the decorator is a declaration checked against it. Two spellings of one name
    with no rule for which is canonical is a drift nobody detects until a config
    names the loser, so loading fails naming both rather than letting one
    silently win.

    Takes the declared names rather than computing them, so one comparison serves
    every group: a template's registration lands in a pending buffer its
    discovery pass drains, and a reverse lookup here would depend on whether
    anything had drained it yet.

    Reached only where an object behind a key has actually been loaded, which is
    not `validate` — `validate` answers a name from package metadata and never
    holds the object. That is the guarantee working rather than a check missing.
    """
    if ep.name in declared:
        return
    if declared:
        detail = f"declares `{'`, `'.join(declared)}` instead"
    else:
        detail = "calls no `@register_*` naming it"
    raise ContractError(
        f"the entry point `{ep.name}` in `{ep.group}` points at `{ep.value}`, which "
        f"{detail} — the entry point is the registration and the decorator is a "
        "declaration checked against it, so two spellings of one name are refused "
        "rather than resolved. Make them agree",
        code="E-PLUGIN-DECORATOR",
    )
```

      **The two branches' messages are distinguishable and each is pinned separately**, per Global
      Constraints: only the disagreement branch contains "declares `", and only the
      registered-nothing branch contains "calls no `@register_". Check that neither fragment appears
      in the other's rendered message before believing the tests — the invariant tail is shared, so
      a fragment chosen from it would be vacuous.

- [ ] **Step 4: Document the consequence.** § Errors core raises' `E-PLUGIN-DECORATOR` row, written
      by task 2, already states that `validate` cannot see the disagreement. Read it and confirm; if
      it does not, fix the row here rather than adding a second statement elsewhere.

- [ ] **Step 5: Run and see them pass**, then the whole suite. Expected: predecessor's count **+ 4**.
      `uv run mypy` must be clean — `EntryPoint(name=…, value=…, group=…)` is its documented
      constructor and is typed.

- [ ] **Step 6: Mutate — three.**

  **(a) Compare against the first declared name.** Change `if ep.name in declared:` to
  `if declared and ep.name == declared[0]:`.
  `test_an_object_registered_under_several_names_satisfies_any_of_them` must FAIL on its
  `plate_positions` iteration — `declared` sorts to `["plate_positions", "plate_wells"]`, so
  `plate_wells` fails. **Checked against the body:** it loops over both keys, which is what makes
  membership distinguishable from equality; a single-key fixture would pass under both.

  **(b) Collapse the two message branches.** Change the `else` to produce the same string as the
  `if`. `test_an_object_that_registered_nothing_is_refused_and_says_so` must FAIL on
  `assert "calls no \`@register_" in message`. **Checked against the body:** the empty-`declared`
  call renders `declares `` instead` under the mutant, which contains neither asserted fragment in
  the right direction — and the test's second assertion, `"declares \`" not in message`, catches it
  from the other side.

  **(c) Refuse nothing.** Delete the raise. Both refusal tests FAIL with `DID NOT RAISE`, and
  `test_a_decorator_argument_matching_its_key_is_accepted` still passes — which is the point of
  having it: it is what proves the refusal tests are about a disagreement rather than about the
  function raising.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green.

- [ ] **Step 7: Which deliverable no mutation reaches, stated plainly.** **`check_registration` has
      no production caller in this slice and no task in Part A or Part B gives it one.** It is
      reached when a plugin's entry point is loaded, which is the same unowned work
      `spec-defects.md`'s `## OPEN — an installed template's name resolves but its class is never
      loaded` describes for templates and which the apparatus slice will need for probes. The tests
      here exercise the comparison directly and prove nothing about where it is called from.
      **`_registry_for`'s `None` branch for templates** is pinned only by `declared_names` returning
      `[]`, which no test asserts — add nothing; a test that pinned it would pin the absence of a
      template registry mapping, which is a design choice stated in the docstring.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: the decorator-vs-key comparison, and the consequence that validate cannot see it`

---

## Task 17: Import-failure containment, `SystemExit` included

**Files:** Modify `src/publishable/plugins.py`, `docs/reference.md`, `tests/test_plugins.py`.

**Interfaces:**
- Consumes: `discovery.drain_pending() -> list[tuple[str, type[BaseTemplate]]]`, which hands over
  the accumulated registrations and empties the buffer; `discovery.PartialLoadError(message, *,
  code, partial_templates)`; `EntryPoint.load()`.
- Produces: `plugins.load_entry_point(ep: EntryPoint) -> Any`, raising `PartialLoadError` ·
  `E-PLUGIN-LOAD` and carrying whatever the failed import left in the pending buffer.

**The pattern to copy is the widened one, and copying the old one drops the payload.** H7c changed
`discover_local`'s two `except` arms from *discarding* the pending buffer to
`partial.extend(cls for _, cls in drain_pending())`, so a file that raised **after** its
`@register_template` still hands back the class whose declarations a credential redaction reads. A
plugin module raises at the same point in its own life, so it needs the same drain — and copying the
pre-H7c shape would silently drop it. That is the whole of what "WIDENED" means in the re-scoping's
task 17 row.

**`SystemExit` needs its own `except`.** It is a `BaseException`, so a broad `except Exception` does
not see it. A plugin calling `sys.exit()` at module scope, or building an `argparse` parser at
import, would otherwise end the command with the plugin's own exit code and no diagnostic — the one
outcome core is contracted never to produce. `discover_local` and `validate_config`'s entrypoint
import both already carry the pair; this is the third.

**This is the module's only function that imports anything**, and its docstring says so, because the
rest of `plugins.py` exists to answer without importing.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_plugins.py`:

```python
def test_a_plugin_module_that_raises_is_a_coded_refusal_naming_the_distribution(installed):
    """A traceback out of a command is the outcome core is contracted never to
    produce. The distribution is named rather than the module, because a
    distribution is what a reader uninstalls or pins."""
    from publishable.errors import ContractError
    from publishable.plugins import load_entry_point, scan_group

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "boom_module:resolve"}}
    )
    (site / "boom_module.py").write_text("raise RuntimeError('kaboom')\n")

    ep = scan_group("publishable.resolvers")["plate_wells"][0]
    with pytest.raises(ContractError) as excinfo:
        load_entry_point(ep)

    assert excinfo.value.code == "E-PLUGIN-LOAD"
    message = str(excinfo.value)
    assert "plate_wells" in message
    assert "dist-one 1.0" in message
    assert "RuntimeError" in message


def test_a_plugin_module_calling_sys_exit_is_contained_too(installed):
    """`SystemExit` is a `BaseException`, so the broad arm does not see it — the
    mutation for this is deleting the `except SystemExit` and watching pytest
    exit rather than report."""
    from publishable.errors import ContractError
    from publishable.plugins import load_entry_point, scan_group

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "exiting_module:resolve"}}
    )
    (site / "exiting_module.py").write_text("import sys\nsys.exit(3)\n")

    ep = scan_group("publishable.resolvers")["plate_wells"][0]
    with pytest.raises(ContractError) as excinfo:
        load_entry_point(ep)

    assert excinfo.value.code == "E-PLUGIN-LOAD"
    assert "SystemExit: 3" in str(excinfo.value)


def test_a_class_a_failing_plugin_declared_before_raising_is_carried(installed):
    """The widened pattern. A class body finishes running before its own
    decorator is reached, so a module that raises AFTER registering still leaves
    a fully formed class — carried on the refusal so a caller that never gets a
    usable object can still read what it declared.
    """
    from publishable.plugins import load_entry_point, scan_group

    site = installed(
        "dist-one", "1.0", {"publishable.templates": {"my_assay": "half_module:T"}}
    )
    (site / "half_module.py").write_text(
        "from publishable import BaseTemplate, register_template\n"
        "\n"
        "\n"
        "@register_template('my_assay')\n"
        "class T(BaseTemplate):\n"
        "    required_env = ['SOME_KEY']\n"
        "\n"
        "\n"
        "raise RuntimeError('after registering')\n"
    )

    ep = scan_group("publishable.templates")["my_assay"][0]
    with pytest.raises(Exception) as excinfo:
        load_entry_point(ep)

    carried = getattr(excinfo.value, "partial_templates", None)
    assert carried is not None
    assert [cls.required_env for cls in carried] == [["SOME_KEY"]]


def test_a_plugin_module_that_imports_cleanly_hands_back_its_object(installed):
    """THE HONOURING. Every test above asserts a refusal; without this one a
    `load_entry_point` that raised unconditionally would pass all three."""
    from publishable.plugins import load_entry_point, scan_group

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "good_module:resolve"}}
    )
    (site / "good_module.py").write_text("def resolve(io, cfg):\n    return ['a unit']\n")

    ep = scan_group("publishable.resolvers")["plate_wells"][0]
    assert load_entry_point(ep)(None, None) == ["a unit"]
```

      **`installed` returns the site directory**, which is on `sys.path`, so writing a module beside
      the `.dist-info` makes it importable — that is why the fixture returns a `Path` rather than
      `None`, and why these are the only tests in the slice whose entry points name a module that
      exists. Note that `test_a_class_a_failing_plugin_declared_before_raising_is_carried` leaves an
      entry in `discovery._pending` if the drain is missing; that is the defect it exists to catch
      and it is **also a leak into the next test**, so run this file twice in a row and confirm both
      runs are green before believing either.

- [ ] **Step 2: Run and see them fail.** `ImportError: cannot import name 'load_entry_point'`.

- [ ] **Step 3: Implement.** In `src/publishable/plugins.py`, add
      `from publishable.templates.discovery import PartialLoadError, drain_pending`, then:

```python
def load_entry_point(ep: EntryPoint) -> Any:
    """Import what `ep` points at, containing every way a plugin's top level can fail.

    **The one function in this module that imports anything.** Everything else
    answers from package metadata, which is the guarantee § Creating a plugin
    justifies the whole mechanism by; this is what a command calls once it has
    resolved a name and actually needs the object.

    `SystemExit` gets its own arm because it is a `BaseException` and the broad
    one below does not see it: a plugin calling `sys.exit()` at module scope, or
    building an `argparse` parser at import, would otherwise end the command with
    the plugin's own exit code and no diagnostic at all.

    Whatever the failed import left in the pending registration buffer is drained
    onto the refusal rather than discarded. A class body finishes running before
    its own `@register_*` call is reached, so a module that raises after
    registering still leaves a fully formed class — and a caller that never gets
    a usable object can still ask that class what credentials it declares. It is
    drained rather than kept for the next load either way: a registration this
    import made is not the next one's to inherit.

    The distribution is named rather than the module, because a distribution is
    what a reader uninstalls or pins.
    """
    try:
        return ep.load()
    except SystemExit as exc:
        raise PartialLoadError(
            f"the entry point `{ep.name}` in `{ep.group}`, from {provider_of(ep)}, called "
            f"`sys.exit()` while importing and registers nothing usable: SystemExit: {exc.code}",
            code="E-PLUGIN-LOAD",
            partial_templates=[cls for _, cls in drain_pending()],
        ) from exc
    except Exception as exc:
        raise PartialLoadError(
            f"the entry point `{ep.name}` in `{ep.group}`, from {provider_of(ep)}, raised "
            f"while importing and registers nothing usable: {exc!r}",
            code="E-PLUGIN-LOAD",
            partial_templates=[cls for _, cls in drain_pending()],
        ) from exc
```

      **`{exc!r}` rather than `{exc}`**, matching `discover_local`'s wording, which is why the test
      asserts `"RuntimeError"` rather than `"kaboom"` alone. **`plugins` importing
      `templates.discovery`** introduces no cycle: `discovery` imports `errors` and `templates.base`
      and nothing else of core's. Confirm with `uv run python -c "import publishable"` before
      running the suite.

- [ ] **Step 4: Document it.** § Errors core raises' `E-PLUGIN-LOAD` row, written by task 2, already
      states the `SystemExit` half and the distribution-naming half. Read it and confirm; fix the
      row here if it does not, rather than adding a second statement.

- [ ] **Step 5: Run and see them pass**, then the whole suite **twice in a row in one command**
      (`uv run pytest -q && uv run pytest -q`) — a drain that fails to empty the buffer shows as a
      second-run failure in `tests/test_templates.py`, whose discovery tests assert on exactly what
      the buffer holds. Expected: predecessor's count **+ 4**.

- [ ] **Step 6: Mutate — three.**

  **(a) Discard instead of draining.** Change both `partial_templates=` expressions to `[]`.
  `test_a_class_a_failing_plugin_declared_before_raising_is_carried` must FAIL on
  `assert [cls.required_env for cls in carried] == [["SOME_KEY"]]`. **Checked against the body:**
  the module registers a class and *then* raises, so the buffer is genuinely non-empty at the
  moment of the raise; a module that raised before registering could not tell this mutant from
  correct code, which is why the fixture's `raise` is the last line.

  **(b) Delete the `except SystemExit` arm.** `test_a_plugin_module_calling_sys_exit_is_contained_too`
  must FAIL — and it will fail by **pytest itself exiting**, not by an assertion, since `SystemExit`
  propagates. Run it as `uv run pytest tests/test_plugins.py -q -k sys_exit` on its own and read the
  exit code; that is the observable, and it is the whole reason the arm exists.

  **(c) Never drain on the broad arm only.** Change the `except Exception` arm's
  `partial_templates=` to `[]` while leaving the `SystemExit` arm draining. The same test as (a)
  must FAIL, because its fixture raises a `RuntimeError`. **This is what proves the two arms are
  separately wired**, which mutation (a) does not.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green.

- [ ] **Step 7: Which deliverable no mutation reaches.** **`load_entry_point` has no production
      caller in this slice**, for the same reason `check_registration` does not: nothing in Part A
      loads a plugin. Named here and filed against the same unowned work. The `from exc` chaining is
      unpinned — no test reads `__cause__` — and deliberately so; adding an assertion would pin a
      traceback detail no document states.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: plugin import-failure containment, SystemExit included, draining the pending buffer`

---

## Task 18: `--plugin` built — `uv add`, and the `plugin` field written

**Files:** Modify `src/publishable/cli.py`, `src/publishable/generators/experiment.py`,
`src/publishable/materialize.py`, `docs/reference.md`, `tests/test_cli.py`,
`tests/test_materialize.py`.

**Interfaces:**
- Consumes: `cli._dispatch_generate(command, rest) -> int`, which parses `--x y` pairs into `opts`
  and everything else into `positional`, then checks
  `missing = [f"--{o}" for o in ("template", "input-dir", "output-dir") if o not in opts]`;
  `generators.experiment.generate_experiment(*, repo_root, name, template_name, input_dir,
  output_dir) -> Path`; `materialize.materialize_config(*, template, template_name, name, input_dir,
  output_dir, entrypoint) -> str`, which writes the literal `"plugin: null"`;
  `subprocess.run`, used by `scaffold.py` for `git init`/`git add`/`git commit` and the pattern to
  follow.
- Produces: `generate_experiment(..., plugin: str | None = None)`; `materialize_config(...,
  plugin: str | None = None)` writing `plugin: <value>` or `plugin: null`; a `uv add
  git+https://github.com/<user>/<repo>` run before the package is scaffolded; the three `NOT BUILT`
  markings task 6 added, reverted.

**Order matters and the reason is the same one `generate template` already carries.** `uv add` must
run **before** anything reaches disk, and before `resolve_template`: the whole point of `--plugin`
is that the template it names comes from the package being installed, so resolving first would
refuse a name the install is about to provide. And a failed install must leave no half-scaffolded
package — `generate experiment` already refuses if `src/<pkg>/` exists, so a retry after a failed
install must find a clean tree.

**`--plugin` is legal on a creation command**, which task 6 wrote into § Plugins. Do not re-argue it
here.

**The install is real, so the test is marked.** `pyproject.toml` declares
`markers = ["slow: exercises real uv or network"]`. A test that actually runs `uv add
git+https://…` needs the network and is `@pytest.mark.slow`; the ordinary tests patch the runner.
**Patch by full module attribute path** — `publishable.generators.experiment.<name>` — and say so in
the test's own comment, since the same helper name could plausibly live in `cli`.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_materialize.py`:

```python
def test_the_plugin_field_carries_what_generate_was_told(tmp_path: Path):
    """`plugin` is a readable note beside the authoritative pin in `uv.lock`
    rather than a second one — so it records the argument verbatim, including a
    version suffix, and core never installs from the field itself."""
    text = materialize_config(
        template=get_template("generic"),
        template_name="generic",
        name="cohort-pilot",
        input_dir=str(tmp_path / "in"),
        output_dir=str(tmp_path / "out"),
        entrypoint="cohort_pilot.experiment:CohortPilotExperiment",
        plugin="someuser/publishable-llm@v1.2.0",
    )
    assert yaml.safe_load(text)["plugin"] == "someuser/publishable-llm@v1.2.0"

    # THE CONTROL, and the regression: with no plugin the field is `null`, which
    # is what every other test in this file's generated config asserts.
    plain = materialize_config(
        template=get_template("generic"),
        template_name="generic",
        name="cohort-pilot",
        input_dir=str(tmp_path / "in"),
        output_dir=str(tmp_path / "out"),
        entrypoint="cohort_pilot.experiment:CohortPilotExperiment",
    )
    assert yaml.safe_load(plain)["plugin"] is None
```

      and to `tests/test_cli.py`. **The invocation pattern is this file's own and is not invented
      here**: `main(["new", str(root)])` scaffolds, `monkeypatch.chdir(root)` puts
      `_dispatch_generate`'s `find_repo_root(Path.cwd())` in the right place, and `main([...])` is
      compared against `EXIT_OK` / `EXIT_WRONG` — read
      `test_generate_experiment_cli_resolves_a_project_local_template` and follow it exactly.
      `main`, `EXIT_OK` and `EXIT_WRONG` are already imported at module level, as are `yaml`,
      `pytest` and `Path`. **Add no module-level helper**; the file's existing ones are
      `run_a_project`, `_new_project_with_a_generated_template` and `GENERATED_TEMPLATE`, and
      nothing here needs a fourth.

```python
def test_generate_experiment_installs_the_plugin_before_it_scaffolds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The order is the behaviour: `uv add` runs before `resolve_template`,
    because the template the config names is the one being installed.

    Patched at `publishable.generators.experiment.uv_add` — the full module
    attribute path, since a same-named helper in `cli` would be a plausible
    wrong target.
    """
    calls: list[tuple[str, str]] = []

    def fake_uv_add(repo_root: Path, requirement: str) -> None:
        calls.append((str(repo_root), requirement))

    monkeypatch.setattr("publishable.generators.experiment.uv_add", fake_uv_add)

    root = tmp_path / "proj"
    data = tmp_path / "data"
    data.mkdir()
    (data / "index.csv").write_text("patient_id\np1\n")
    assert main(["new", str(root)]) == EXIT_OK
    monkeypatch.chdir(root)

    assert (
        main(
            [
                "generate",
                "experiment",
                "pilot",
                "--template",
                "generic",
                "--plugin",
                "someuser/publishable-llm",
                "--input-dir",
                str(data),
                "--output-dir",
                str(tmp_path / "results"),
            ]
        )
        == EXIT_OK
    )
    assert calls == [(str(root), "git+https://github.com/someuser/publishable-llm")]
    config = yaml.safe_load((root / "configs" / "pilot" / "config.yaml").read_text())
    assert config["plugin"] == "someuser/publishable-llm"

    # THE CONTROL: no `--plugin`, no install, and the field stays `null`. Without
    # it, an implementation that always installed would pass the assertion above.
    calls.clear()
    assert (
        main(
            [
                "generate",
                "experiment",
                "pilot2",
                "--template",
                "generic",
                "--input-dir",
                str(data),
                "--output-dir",
                str(tmp_path / "results2"),
            ]
        )
        == EXIT_OK
    )
    assert calls == []
    plain = yaml.safe_load((root / "configs" / "pilot2" / "config.yaml").read_text())
    assert plain["plugin"] is None


def test_a_failed_plugin_install_scaffolds_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """A retry after a failed install must find a clean tree — `generate
    experiment` refuses an existing `src/<pkg>/`, so a half-scaffolded package
    would make the failure permanent."""

    def fake_uv_add(repo_root: Path, requirement: str) -> None:
        raise ContractError("uv add failed: no such repository", code="E-UV-ADD")

    monkeypatch.setattr("publishable.generators.experiment.uv_add", fake_uv_add)

    root = tmp_path / "proj"
    data = tmp_path / "data"
    data.mkdir()
    (data / "index.csv").write_text("patient_id\np1\n")
    assert main(["new", str(root)]) == EXIT_OK
    monkeypatch.chdir(root)

    assert (
        main(
            [
                "generate",
                "experiment",
                "pilot",
                "--template",
                "generic",
                "--plugin",
                "someuser/publishable-llm",
                "--input-dir",
                str(data),
                "--output-dir",
                str(tmp_path / "results"),
            ]
        )
        == EXIT_WRONG
    )
    assert "E-UV-ADD" in capsys.readouterr().err
    assert not (root / "src" / "pilot").exists()
    assert not (root / "configs" / "pilot").exists()
```

      **`EXIT_WRONG` is asserted rather than "not `EXIT_OK`"** because this file's own control
      pattern does that — `test_generate_experiment_cli_resolves_a_project_local_template` asserts
      the specific exit code *and* the specific identifier on stderr, "not just some refusal". If a
      `ContractError` from `generate_experiment` reaches `main`'s handler as some other exit code,
      **read `main`'s dispatch and assert what it actually produces** rather than weakening the
      assertion; record what you found in the task report.

- [ ] **Step 2: Run and see them fail.** The materialize test on
      `TypeError: materialize_config() got an unexpected keyword argument 'plugin'`; the CLI tests
      on `AttributeError` from the `monkeypatch.setattr` target, which does not exist yet.

- [ ] **Step 3: Implement.** In `src/publishable/materialize.py`, add `plugin: str | None = None` to
      `materialize_config`'s keyword-only parameters and replace the literal `"plugin: null"` with:

```python
        f"plugin: {plugin if plugin else 'null'}",
```

      In `src/publishable/generators/experiment.py`, add `import subprocess` and:

```python
def uv_add(repo_root: Path, requirement: str) -> None:
    """`uv add <requirement>` in the project, and nothing more.

    `reference.md` § Plugins: no registry, no bespoke installer, no new trust
    boundary beyond "this is a git dependency," because it is one. The install
    is what makes the plugin a normal `pyproject.toml` line and a pinned
    `uv.lock` entry, which is what gives `reproduce` the exact version free.
    """
    result = subprocess.run(
        ["uv", "add", requirement], cwd=repo_root, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise ContractError(
            f"`uv add {requirement}` failed: {result.stderr.strip() or result.stdout.strip()}",
            code="E-UV-ADD",
        )


def plugin_requirement(spec: str) -> str:
    """`<user>/<repo>` or `<user>/<repo>@<ref>` to what `uv add` takes."""
    return f"git+https://github.com/{spec}"
```

      and give `generate_experiment` a `plugin: str | None = None` keyword, installing **first**:

```python
    if plugin:
        uv_add(repo_root, plugin_requirement(plugin))
    template, known = resolve_template(template_name, repo_root)
```

      passing `plugin=plugin` through to `materialize_config`. In `cli._dispatch_generate`'s
      `experiment` branch, pass `plugin=opts.get("plugin")`. **`--plugin` must not join the
      `missing` list** — it is optional; read that list and confirm you did not add it.

      **Add `E-UV-ADD` to § Errors core raises**, beside the row that reports a project-local
      `templates/*.py` failing to load — name that sibling by what it does:

```
| `uv add` failing for a [`--plugin`](#plugins-where-domain-knowledge-lives) argument on `generate experiment`. Raised before anything reaches disk, so a retry finds a clean tree: `generate experiment` refuses an existing `src/<pkg>/`, which would make a half-scaffolded failure permanent. The message carries `uv`'s own output, since what went wrong is `uv`'s to say — a bad repository name, a ref that does not exist, no network | `ContractError` · `E-UV-ADD` |
```

- [ ] **Step 4: Revert task 6's three markings.** § Creation commands' `generate` row loses
      `(NOT BUILT — the flag parses and is dropped)`; § Generators' `experiment` row loses the
      sentence task 6 appended; § Plugins' opening sentence loses `— **NOT BUILT** in this build,
      where the flag parses and is dropped`. **Leave task 6's step-5 paragraph** about creation
      versus operation commands — it is a permanent clarification, not a marking. Re-read § Plugins
      after editing and confirm the paragraph still reads as one sentence's worth of correction
      rather than two.

- [ ] **Step 5: Config completeness.** § The one config file's fenced example already carries
      `plugin: null`; nothing is added by this task, and the identifying-fields paragraph already
      says "`plugin` names where the template came from, and is a readable note beside the
      authoritative pin in `uv.lock` rather than a second one — core never installs from it". Read
      that clause and confirm it is still true: **core installs from the flag, never from the
      field**, which is exactly what it says. Change nothing.

- [ ] **Step 6: A slow test that runs the real thing.** Add one, marked, so the patched tests are
      not the only evidence `uv add` is invoked correctly:

```python
@pytest.mark.slow
def test_uv_add_really_installs(tmp_path):
    """`markers = ["slow: exercises real uv or network"]`. The patched tests
    above prove the wiring; this proves the command line."""
```

      Fill it in against a real repository the project already depends on rather than inventing one,
      and if no such dependency is installable offline, **write the test as a `pytest.skip` with the
      reason stated** rather than leaving the marker unused. Say in the task report which you did.

- [ ] **Step 7: Run and see them pass**, then the whole suite **excluding slow**
      (`uv run pytest -q -m "not slow"`) and then including it, and report both counts. Expected
      without slow: predecessor's count **+ 3**.

- [ ] **Step 8: Mutate — three.**

  **(a) Install after scaffolding.** Move the `if plugin:` block below `resolve_template`.
  `test_a_failed_plugin_install_scaffolds_nothing` must FAIL on
  `assert not (repo / "src" / "pilot").exists()`. **Checked against the body:** the fake raises, so
  under the mutant the package directory is already created when it does. The ordering test's
  `calls == [...]` assertion would **not** catch this — it only records that the call happened —
  which is why the tree assertion exists.

  **(b) Install unconditionally.** Change `if plugin:` to `if True:`, passing `None` through.
  `test_generate_experiment_installs_the_plugin_before_it_scaffolds` must FAIL on its control's
  `assert calls == []`. **Checked against the body:** the control invokes `generate experiment` with
  no `--plugin` and asserts no call was recorded, so the two branches differ.

  **(c) Write the field from the requirement rather than from the argument.** Change
  `plugin=plugin` to `plugin=plugin_requirement(plugin) if plugin else None`.
  `test_the_plugin_field_carries_what_generate_was_told` does **not** catch this — it calls
  `materialize_config` directly. The CLI test's
  `config["plugin"] == "someuser/publishable-llm"` does. **Named because the obvious target is the
  wrong one**: run the CLI test, not the materialize test, for this mutation.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green.

- [ ] **Step 9: Which deliverable no mutation reaches.** **Task 6's three document markings being
      reverted is unpinned** — no test reads those cells, as task 6 said. **Nothing closes it**;
      the coupling is this task's commit message, which must name task 6. **`plugin_requirement`'s
      handling of an `@ref` suffix** is pinned only by the materialize test's round trip of the
      *field*, not by an assertion that `git+https://github.com/user/repo@v1` is what `uv` receives
      — add one to the ordering test's first arm if you want it, and say in the report whether you
      did.

- [ ] **Step 10: Verify and commit.** All four commands.
      `feat: --plugin runs uv add and writes the plugin field — and reverts task 6's markings`

---

## Task 19: Decision 4 — envelope closure of `data.units.from`, and the mutual exclusion

**Files:** Modify `src/publishable/envelope.py`, `src/publishable/validate.py`,
`docs/reference.md`, `tests/test_envelope.py`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `envelope.LEAF_TYPES`, an ordered dict whose entry `"data.units.from": (str, dict)` stops
  at the mapping; `envelope._known_containers()`, which derives every dotted prefix a `LEAF_TYPES`
  path implies, and the three module constants computed from it at import — `_KNOWN_LEAVES`,
  `_KNOWN_CONTAINERS`, `_KNOWN_OR_EXEMPT`; `envelope._check_unknown_keys`, which checks **containers
  before leaves** so a path that is both is descended into; `envelope.check_envelope`'s type loop,
  which walks a dotted path and stops at the first non-mapping node;
  `validate._check_unimplemented`'s resolver emit, which reads
  `units.get("from")` and reports `E-DATA-RESOLVER-UNSUPPORTED` when `"resolver" in source`;
  `units.resolve_units`, which branches `str` → table, `{glob: …}` → glob, else raise
  `E-UNITS-SOURCE-MISSING`.
- Produces: `LEAF_TYPES` entries `"data.units.from.glob": str` and `"data.units.from.resolver": str`;
  `validate._check_units_source(doc, c) -> None` emitting `E-UNITS-SOURCE-AMBIGUOUS`; two false
  comments in `envelope.py` deleted.

**The two faults, both measured rather than reasoned.** Probed at `ff51864` against a real scaffolded
project with the closure applied in-process and one field mutated at a time:

```
from: index.csv                      → []
from: {glob: "*.csv"}                → []
from: {resolver: x}                  → ['E-DATA-RESOLVER-UNSUPPORTED']
from: {resolverr: x}                 → ['E-CONFIG-KEY-UNKNOWN', 'E-UNITS-SOURCE-MISSING']
from: {glob: "*.csv", resolver: x}   → ['E-DATA-RESOLVER-UNSUPPORTED']
from: {resolver: 123}                → ['E-CONFIG-TYPE', 'E-DATA-RESOLVER-UNSUPPORTED']
```

The `E-CONFIG-KEY-UNKNOWN` message carries `did you mean \`resolver\`?`, which is the closure's
`difflib` hint working. **Both new codes on the misspelling row come from the closure and from
`resolve_units` respectively, and `validate` collects, which is why both appear** — do not write a
test asserting one of them alone.

**The both-keys fault, and why it is minted now.** `_check_unimplemented` branches on
`"resolver" in source` and `_check_units` skips on the same test, so `validate` calls a
both-keys mapping a resolver; `resolve_units` branches on `"glob" in source` **first**, so a run
would call it a glob. Two answers to one declaration. It is unreachable today because the refusal
stands, and **reachable the moment Part B's dispatch lands** — so the refusal belongs in the slice
that closes the envelope, not the one that opens the path.

**Where the check lives, and why not in `_check_unimplemented`.** Its own function, called from
`validate_config` immediately before `_check_units`. Not in `_check_unimplemented`, whose resolver
entry Part B task 24 deletes — a sibling emit inside that block would be deleted with it, and this
refusal is permanent. Not in `_check_data`, which returns early when there is no git repo.

**Names already at module level in `tests/test_envelope.py`:** read them before adding anything.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_envelope.py` a check on the closure
      itself, using whatever that file's established way of calling `check_envelope` is:

```python
def test_a_misspelled_from_key_is_reported_rather_than_ignored():
    """The closure's whole purpose. `envelope.py`'s own module docstring claimed
    this key was "reported by no check in this build", which was false even
    before the closure — `resolve_units` reported it as a missing source — and is
    now false twice over, with a `difflib` hint naming the key meant."""
    findings = check_envelope({"data": {"units": {"from": {"resolverr": "x"}}}})
    codes = {code for code, _, _ in findings}
    assert "E-CONFIG-KEY-UNKNOWN" in codes
    message = next(m for code, _, m in findings if code == "E-CONFIG-KEY-UNKNOWN")
    assert "did you mean `resolver`?" in message

    # THE CONTROL: both spelled keys, and the string form, report nothing here —
    # so the check above is about an unknown key rather than about descending
    # into `from` at all.
    assert check_envelope({"data": {"units": {"from": {"resolver": "x"}}}}) == []
    assert check_envelope({"data": {"units": {"from": {"glob": "*.dcm"}}}}) == []
    assert check_envelope({"data": {"units": {"from": "index.csv"}}}) == []


def test_a_wrongly_typed_from_child_is_a_type_finding():
    findings = check_envelope({"data": {"units": {"from": {"resolver": 123}}}})
    assert [(code, path) for code, path, _ in findings] == [
        ("E-CONFIG-TYPE", "data.units.from.resolver")
    ]
```

      and to `tests/test_validate.py`:

```python
def test_a_from_mapping_declaring_both_glob_and_resolver_is_refused(write_config):
    """Two answers to one declaration: `validate` reads it as a resolver
    (`_check_unimplemented` tests `resolver in source`) and `resolve_units` would
    read it as a glob (it tests `glob` first). Unreachable while the wholesale
    refusal stands and reachable the moment dispatch lands, so the refusal is
    minted in the slice that closes the envelope.

    Asserted ALONGSIDE the wholesale refusal, never instead of it, and never on
    the whole code set — Part B deletes one line here.
    """
    found = messages_by_code(
        write_config({"data.units.from": {"glob": "*.csv", "resolver": "plate_wells"}})
    )
    message = found["E-UNITS-SOURCE-AMBIGUOUS"]
    assert "glob" in message
    assert "resolver" in message
    assert "E-DATA-RESOLVER-UNSUPPORTED" in found

    # THE CONTROLS, both produced by the code under test: either key alone is not
    # ambiguous. Without these, a check that fired for any mapping would pass.
    assert "E-UNITS-SOURCE-AMBIGUOUS" not in codes(
        write_config({"data.units.from": {"glob": "*.csv"}})
    )
    resolver_only = codes(write_config({"data.units.from": {"resolver": "plate_wells"}}))
    assert "E-UNITS-SOURCE-AMBIGUOUS" not in resolver_only
    assert "E-DATA-RESOLVER-UNSUPPORTED" in resolver_only
```

- [ ] **Step 2: Run and see them fail.** The envelope tests report no `E-CONFIG-KEY-UNKNOWN` and no
      `E-CONFIG-TYPE`; the validate test fails on `KeyError: 'E-UNITS-SOURCE-AMBIGUOUS'`.

- [ ] **Step 3: Implement the closure.** In `src/publishable/envelope.py`, add two entries
      immediately after `"data.units.from": (str, dict),`:

```python
    # Closed one level in, the arrangement `data.units.measurements` and
    # `.holdout` already have: the two keys a `from` mapping may carry are fixed,
    # so leaving the block whole makes a typo among them unreachable by any check
    # — which is what a `resolverr` was until this closure, reported only as a
    # missing source and never as a misspelled key. Closed here **before** the
    # resolver's own wholesale refusal retires, the same order `resample` took:
    # the shape is checked before the values are honoured.
    "data.units.from.glob": str,
    "data.units.from.resolver": str,
```

      **Nothing else changes.** `_KNOWN_LEAVES`, `_KNOWN_CONTAINERS` and `_KNOWN_OR_EXEMPT` are
      derived at import from `LEAF_TYPES`, so both the container closure and the `difflib` hint pick
      the entries up for free; `_check_unknown_keys` checks containers before leaves, so
      `data.units.from` — now both — is descended into rather than stopped at; and
      `check_envelope`'s type loop stops at a non-mapping node, so a string `from` still types
      cleanly against `(str, dict)` and reaches neither new entry. **Verify each of those three by
      running the tests rather than by reading**, since all three are properties of code this task
      does not touch.

- [ ] **Step 4: Implement the mutual exclusion.** In `src/publishable/validate.py`:

```python
def _check_units_source(doc: dict[str, Any], c: Collector) -> None:
    """A `data.units.from` mapping may declare `glob` or `resolver`, not both.

    Two answers to one declaration: this module reads such a mapping as a
    resolver — `_check_unimplemented` and `_check_units` both test for the
    `resolver` key — while `units.resolve_units` tests for `glob` first and would
    resolve it as a glob. Whichever is right, they cannot both be, and a run that
    executed one while `validate` had checked the other is the fault this refuses.

    Its own function rather than a branch beside the resolver refusal, because
    that refusal retires and this one does not: a `from` naming two sources is
    ambiguous whether or not resolvers are honoured.
    """
    units = _units_declaration(doc.get("data") or {}, c) or {}
    source = units.get("from")
    if isinstance(source, dict) and "glob" in source and "resolver" in source:
        c.error(
            "E-UNITS-SOURCE-AMBIGUOUS",
            "data.units.from",
            "declares both `glob` and `resolver`, which name two different ways of "
            "finding the same roster — `from` says how core finds a unit, and a "
            "declaration with two answers has none. Declare one",
        )
```

      Call it from `validate_config` immediately before `_check_units`, which is the check that
      resolves the roster this declaration decides the shape of.

- [ ] **Step 5: Delete `envelope.py`'s two false comments.** In the module docstring, the sentence
      "a misspelled `resolverr` in a `data.units.from` mapping is reported by no check in this
      build" is false and its subject is now closed — **delete the clause** and let the surrounding
      argument about whole leaves stand on `measurements`' and `holdout`'s example, which it already
      does. In `_check_unknown_keys`' docstring, "a `from` dict's `resolver` is reached by no check
      in this build: not here, and not by `_check_shape`, which checks a container's shape and never
      the names inside one" is false in both halves — `_check_unimplemented` reads it, and now this
      closure does. **Delete that clause too**, keeping the sentence's general rule about not
      descending into a known leaf "unless the table also declares paths BENEATH it", which is
      exactly what these two new entries are and is the mechanism a reader needs.

      Preferring deletion to rewriting is the rule here: a round in this repo closed a false-claim
      finding by propagating the claim to two more sites.

- [ ] **Step 6: Document it.** Add a row to § Errors `validate` reports, beside the row reporting a
      `data.units.from` that names no usable source — name that sibling by what it does:

```
| [`data.units.from`](#where-units-come-from) is a mapping declaring **both** `glob` and `resolver`. `from` answers one question — how core finds a unit — and a declaration with two answers has none: one form builds the table from matching paths and the other hands the work to a plugin, and they resolve different rosters. Refused rather than ordered, for the reason every collision in this document is: a rule for which key wins would be a rule nobody could read off the config | `E-UNITS-SOURCE-AMBIGUOUS` |
```

      And in § Validation, add a row beside the check that reports **where units come from**:

```
| One source per roster | `data.units.from` declares `{glob: "*.dcm", resolver: plate_wells}`; the two find different units |
```

- [ ] **Step 7: Run and see them pass**, then the whole suite. **`tests/test_envelope.py` in full is
      the regression surface** — the closure changes what `_known_containers()` derives, so any test
      asserting on the set of known containers or on `_immediate_children` moves. Run that file
      first and read every failure; a failure there is a real consequence to be understood, not a
      fixture to be edited. Expected: predecessor's count **+ 3**.

- [ ] **Step 8: Mutate — three.**

  **(a) Remove one closure entry.** Delete `"data.units.from.glob": str`.
  `test_a_misspelled_from_key_is_reported_rather_than_ignored` must still pass — `resolverr` is
  still unknown — but its **control** `check_envelope({"data": {"units": {"from": {"glob": "*.dcm"}}}}) == []`
  must FAIL, since `glob` becomes an unknown key. **Checked against the body:** the control asserts
  the empty list for both spelled keys, so removing either entry reddens it. **This is the mutation
  that proves both entries are wired**, and the misspelling assertion alone does not.

  **(b) Require only one key for the ambiguity.** Change the condition to
  `"glob" in source or "resolver" in source`. `test_a_from_mapping_declaring_both_glob_and_resolver_is_refused`
  must FAIL on its **first control** (`glob` alone). **Checked against the body:** the test declares
  each key alone as well as both, which is the only arrangement in which the two readings differ; a
  test asserting only the both-keys case would pass under this mutant.

  **(c) Report instead of alongside.** In `_check_unimplemented`, guard the resolver emit with
  `and "glob" not in source`. `test_a_from_mapping_declaring_both_glob_and_resolver_is_refused` must
  FAIL on `assert "E-DATA-RESOLVER-UNSUPPORTED" in found`. **This is the mutation that pins the
  alongside-never-instead-of discipline**, and it is the one that would go quiet if a future task
  wrote the test against a total code set instead.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green.

- [ ] **Step 9: Which deliverable no mutation reaches.** **The two deleted comments are unpinned** —
      nothing reads a docstring — and **nothing closes that**; the verification is that the claims
      they made are now demonstrably false, which step 1's tests show. **`_check_units_source`'s
      finding path (`data.units.from`)** is unpinned as every path in this slice is.

- [ ] **Step 10: Verify and commit.** All four commands.
      `feat: data.units.from is closed one level in, and a mapping naming two sources is refused`

---

## Task 20: Decision 3 — `PartialLoadError` semantics for the entry-point half, and its residual

**Files:** Modify `src/publishable/templates/registry.py`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `registry._claims`' `PartialLoadError(..., partial_templates=[claim.cls for these in
  claims.values() for claim in these if claim.cls is not None])`, written by task 8;
  `discovery.PartialLoadError`, whose docstring says it "carries every class this discovery pass got
  far enough to construct"; `validate_config`'s `except ContractError` guard, which reads
  `getattr(exc, "partial_templates", None)` and sets `c.credentials` from what those classes
  declare; `secrets.redact(text, values)`, which replaces a value by exact match.
- Produces: the payload expression named as the concept it is, in a comment; § Secrets & credentials
  extended with the second case redaction does not cover; a `spec-defects.md` entry for the residual.

**The residual, stated exactly.** H7c gave `discovery`/`registry` a `PartialLoadError` whose payload
is the classes a discovery pass constructed, so a credential a *refused* file declared can still be
redacted out of the refusal's own message. Task 8 added a third claim source to the merge that
raises it. **The entry-point half structurally cannot carry a class**: the scan is metadata-only, by
decision 3, so a plugin-side collision holds no `parameter_spec` and no `required_env` to read, and
its finding cannot be redacted the way a local one's is. That is a **documented residual, not a
defect to fix** — the natural repair is calling `.load()`, which destroys the exact invariant the
mechanism exists for, and the temptation will arrive dressed as "we need the class to redact its
credentials."

**What task 8 already got right, and what is left.** Task 8's expression reads `claims.values()`
rather than `local.values()`, so it already names "every class this pass constructed" rather than
"every local class" — the proxy the re-scoping's § 10 flags is gone. What is left is that **nothing
distinguishes the two**: no installed claim carries a class in Part A, so the two expressions are
behaviourally identical and **no mutation reaches the difference.** This task says that in the code,
in the document, and in the defects file, rather than adding a test that cannot fail.

- [ ] **Step 1: Write the test that *is* available.** Append to `tests/test_validate.py`:

```python
_CREDENTIALED_TEMPLATE = """\
from publishable import BaseTemplate, register_template


@register_template("generic")
class Shadower(BaseTemplate):
    required_env = ["SHADOW_KEY"]
    parameter_spec = {}
"""


def test_a_collision_redacts_what_a_local_claimant_declared_and_cannot_redact_an_installed_one(
    installed, git_repo, write_config, monkeypatch
):
    """Both halves of decision 3 in one test, because the second is only legible
    beside the first.

    A local claimant's class is in hand at the merge, so its declared credential
    is redacted out of the collision's own message. An installed claimant is a
    name and a distribution — the scan never imported it — so nothing of what it
    declares is available to match against, and that is the mechanism rather than
    a gap.
    """
    monkeypatch.setenv("SHADOW_KEY", "SENTINEL-sk-abc123")
    templates = git_repo / "templates"
    templates.mkdir()
    (templates / "mine.py").write_text(_CREDENTIALED_TEMPLATE)

    c = Collector()
    validate_config(write_config(), c)
    rendered = c.render()

    assert "E-TEMPLATE-COLLISION" in rendered
    # The local claimant's declaration reached `c.credentials`, which is the
    # whole of what `partial_templates` is for. Asserted on the RENDERED text,
    # since redaction happens at render.
    assert "SENTINEL-sk-abc123" not in rendered
    assert "<redacted:SHADOW_KEY>" in rendered or "SHADOW_KEY" in rendered
```

      **Read `_CREDENTIALED_TEMPLATE` against the message before believing this test**: the value is
      only redacted if it appears in the message at all, and a collision message names providers
      rather than credentials. If the sentinel never appears in the un-redacted message, the
      `not in` assertion is vacuous — **so first run the test with `redact` disabled** (patch
      `publishable.diagnostics.redact` to return its first argument, by full module attribute path)
      and confirm the sentinel **is** present. If it is not, the collision message does not carry a
      credential, and this test cannot discriminate: **delete it, and record in the task report that
      no test in this slice reaches the payload at all.** That outcome is acceptable and expected;
      what is not acceptable is shipping the assertion without checking.

- [ ] **Step 2: Name the concept in the code.** In `registry._claims`, above the
      `partial_templates=` expression:

```python
                # Every class this merge constructed, whether or not it ends up
                # usable — the same set `discover_local` accumulates, so a caller
                # that never gets a resolved template can still ask an abandoned
                # class what credentials it declares. An installed claim
                # contributes nothing here and structurally cannot: its claim is
                # read from package metadata and no module was imported, so there
                # is no class to ask. That is the cost of the guarantee rather
                # than a gap in this expression — see § Secrets & credentials.
```

      **Do not enumerate which sources contribute** — that is a call-site enumeration in a comment,
      which this repo has had go stale twice.

- [ ] **Step 3: Document the second uncovered case.** § Secrets & credentials' paragraph beginning
      "A template's own file failing to load or colliding with another is covered too" ends with
      "The one case that isn't: a raise from *inside* a class body, before its own
      `@register_template` line is ever reached, leaves no class behind to ask, and a value that
      reaches only that text is not matched." **Replace "The one case that isn't" with an
      enumeration of two**, since there are now two and the sentence's own construction counts:

```
Two cases aren't. A raise from *inside* a class body, before its own `@register_template` line is ever reached, leaves no class behind to ask. And a collision involving a template an **installed distribution** registers carries no class either, for a sharper reason: such a claim is read from [package metadata](#creating-a-plugin-publishable-plugin-new) and no module was imported, which is the guarantee that makes `validate` cheap and safe — so there is nothing to ask what it declares, and reaching for the class to find out would trade that guarantee for a redaction. In both, a value that reaches only that text is not matched.
```

- [ ] **Step 4: File the residual.** Append to `docs/superpowers/spec-defects.md`:

```markdown
## OPEN — a plugin-side collision carries no class, so its finding cannot be redacted — **Owner: none; accepted**

H7c's `PartialLoadError` carries the classes a discovery pass constructed, so a credential a refused
`templates/*.py` declared is redacted out of the refusal's own message. H7b Part A task 8 adds
installed distributions as a third claim source to that merge, and an installed claim carries **no
class**: the scan is metadata-only by decision 3 of
`2026-08-16-plugin-registries-design.md`, so nothing was imported and there is no `required_env` or
`parameter_spec` to read.

**Filed as accepted rather than as work.** The repair is to call `EntryPoint.load()`, which destroys
the invariant the entry-point mechanism exists for — that `validate` resolves a name without
importing a line — and § Creating a plugin justifies the whole design by that promise. A named
residual beats a silently weaker guarantee. Recorded here so the next reader meets the argument
rather than the temptation, which will arrive dressed as "we need the class to redact its
credentials."

**Bound on the exposure.** A collision message names providers — a distribution and a version, a
path and a class name — and interpolates no declaration, so the text at risk is an exception's
rather than a credential's by construction. What is unmatched is a credential value appearing in a
message core built from an installed claimant's own data, and no such message exists today.

**Struck when** an installed template's class is held at the merge, which is
`## OPEN — an installed template's name resolves but its class is never loaded`, owner unassigned.
The two close together or not at all.
```

- [ ] **Step 5: Run.** `uv run pytest` — the whole suite. Expected: predecessor's count **+ 1**, or
      **+ 0** if step 1's test proved vacuous and was deleted. Report which.

- [ ] **Step 6: Mutate — one, and its scope is narrow.**

  **(a) Empty the payload.** Change `partial_templates=[...]` to `partial_templates=[]`. If step 1's
  test survived, it must FAIL on `assert "SENTINEL-sk-abc123" not in rendered` — the local
  claimant's declaration no longer reaches `c.credentials`, so the value is printed whole.
  **Checked against the test body:** the assertion is over rendered text and the value is set in the
  environment by `monkeypatch.setenv`, so `credential_values` returns it and redaction has something
  to match — that chain is what makes the two branches differ, and it is exactly what step 1 tells
  you to verify before believing the test.

  **The mutation that does NOT exist, stated so nobody proposes it.** Changing
  `claims.values()` to `local.values()` — the proxy this task is about — **cannot fail any test in
  this suite**, because no installed claim carries a class, so the two expressions produce the same
  list for every fixture that can be built in Part A. It is a mathematical no-op here. Do not write
  a test for it, and do not claim one covers it.

  Revert by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 7: Which deliverable no mutation reaches.** **The whole of decision 3's residual.** No
      mutation distinguishes a payload that names every constructed class from one that names every
      local class, and none can until an installed claim carries a class. **Nothing in Part A or
      Part B closes it**; the `spec-defects.md` entry filed in step 4 is where it lives, and it is
      filed as accepted rather than as work. The § Secrets & credentials sentence is prose and
      unpinned, as every document sentence in this slice is.

- [ ] **Step 8: Final sweep for this slice.** Before committing, run the identifier sweep by **file
      list** over the four documents and `src/`, and read every hit:
      `grep -rnE "E-(RESOLVER|PROBE|PLUGIN|READER|UNITS-SOURCE-AMBIGUOUS|TEMPLATE-INSTALLED)[A-Z-]*" docs/reference.md docs/design-principles.md docs/experimental-designs.md README.md src/`.
      Every code minted by this slice must appear where its task put it and nowhere else, and
      `E-TEMPLATE-INSTALLED-UNSUPPORTED` must have **no § Errors row** — that is the `-UNSUPPORTED`
      family's rule and this is the last chance to catch a row someone added. Can-fail control on the
      identical file list: `grep -oE "E-TEMPLATE[A-Z-]*" docs/reference.md | sort -u`.

- [ ] **Step 9: Verify and commit.** All four commands.
      `docs: a metadata-only collision carries no class, and the residual is filed as accepted`

---
