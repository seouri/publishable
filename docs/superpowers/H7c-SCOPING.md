# H7c scoping — secrets, `required_env`, `requires_env`

Read-only measurement against `main` at `d86290c`, on 2026-08-16. This is the **first**
scoping of H7c against the code; the charter's seven items are `H7-SCOPING.md` § 8's
enumeration, pinned to `cb96c7d`, carried verbatim into the spine design. Six slices have
landed since (H3c-1, H3c-2, H7a, H4a, H3d, plus the format commit this document pins).
Every identifier below was grepped or probed against that tree, never remembered. Spec
claims and build facts are labelled separately throughout.

**Verdict: 14 tasks**, against the charter's 7. The growth is the usual direction and has
four sources: the charter has no task for the documentation debt it itself names (three
§ Validation rows with no identifier), no task for the owned prose sweep (twelve sites
across the four documents before `tests/`), no task for the *one* surface on which a
secret value can actually reach a record, and it treats `.env` loading as one call site
where the specification requires two. One charter item shrinks and one is routed out
entirely; both are argued in § 7 rather than absorbed.

**Baseline at `d86290c`:** `uv run pytest -q` → **1957 passed, 2 xfailed**, 109 s. Probes below
ran against that tree with nothing modified, most of them inside a real scaffolded project
(`publishable new proj`, `generate experiment --template generic`, an outside `input_dir`
holding a two-row `index.csv`) rather than by reading source.

**This document does not re-measure `H7b-SCOPING.md`**, pinned to the same commit and the
same day. It contradicts it in exactly one place, § 8, and says so there.

---

## 0. Executive summary — the five things that change what H7c is

1. **The charter's "New identifier" on the `requires_env` totality check is wrong, and the
   precedent is already shipped.** `reference.md:1633` says `validate` rejects a bad
   mapping *"when the template loads"* — the identical phrasing `reference.md:1602` uses
   for `default=None` without `nullable=True`, which is built as a `ValueError` from
   `Param.__init__` and surfaces as `E-TEMPLATE-LOAD` — a code whose § Errors rows already
   enumerate *"raises while importing"* as one of three covered shapes, so not even a row
   is owed. Probed end to end. H7c mints **at most two** codes, not three, and the
   one-or-two question is § 3's open decision rather than this summary's to settle. § 2.
2. **Core reads no environment variable at all today, so the "nothing leaks" invariant is
   currently held by absence, not by a filter — and the charter's task 6 is a control
   asserting only absences.** § 4 names the one surface where a value can enter a record
   by accident (`run_record.py:37` / `runner.py:713` write a failing step's exception
   text) and the mutation that makes the test able to fail.
3. **The union-over-resolved-conditions check — the whole reason `requires_env` exists —
   has no fixture anywhere in the evidence base.** `llm.provider` appears in **no** YAML
   block of the nine feasibility configs; both `sweep.paired` entries are `[]`. All nine
   resolve a single provider, for which a static `required_env` would have sufficed. H7c
   must mint its own fixture. § 5.
4. **`required_env` and `requires_env` are one mechanism with two collectors, and the
   open decision is one code or two.** They differ only in when the set is known and in
   what the message must name. The `E-TEMPLATE-UNKNOWN` two-surfaces-one-row precedent
   (`reference.md:570`) does *not* settle it, because that row's two surfaces share one
   message and these two cannot. § 3.
5. **`validate` reads `.env`, and the specification says core loads it "before any step
   runs".** Two load sites, not one, and the sentence needs reconciling. This is **not** a
   breach of `validate`'s promise: `reference.md:3109`/`:3177` promise it *"creates nothing
   and reaches nothing **off the machine**"*, and `.env` is on-machine. Say it precisely
   rather than flagging a breach that isn't one. § 4.

---

## 1. What exists — measured

| Surface | Status at `d86290c` |
|---|---|
| `Param.requires_env` | **Absent.** `Param.__init__` takes `type_` plus twelve keyword-only arguments (`param.py:15–31`) and `requires_env` is not among them. Probe: `Param(str, default="a", choices=["a"], requires_env={"a": []})` → `TypeError: Param.__init__() got an unexpected keyword argument 'requires_env'`; control, the same call without it, constructs and its `comment()` returns `choices: a` |
| `BaseTemplate.required_env` | **Declarable, read nowhere.** `templates/base.py:15` (`list[str] = []`), re-declared at `templates/builtin/generic.py:9`. `grep -rn "required_env" src/` returns those two declarations plus one comment in `generators/template.py:9` saying the `generate template` stub omits it. The only other reader in the tree is an assertion, `tests/test_templates.py:20` |
| `secrets.py` | **Does not exist.** `ls src/publishable/*.py \| wc -l` → 31, and no `secrets.py` among them. § Package layout carries it as `— not yet built` (`reference.md:3603`) |
| `python-dotenv` | **Not a dependency.** `pyproject.toml:6` declares `pyyaml`, `numpy`, `scipy`, `pyarrow`. `grep -rln "dotenv" src tests pyproject.toml uv.lock` → exit 1; control, the same grep for `pyyaml` over `pyproject.toml uv.lock` → two hits |
| Any environment read in core | **None.** `grep -rln "os.environ\|getenv" src/publishable` → exit 1; control, the same grep for `subprocess` → `provenance.py`, `scaffold.py` |
| `.env` in the scaffold | **Built.** `scaffold.py:8–10`'s `GITIGNORE` opens with `# Credentials — never committed` / `.env`; `scaffold.py:92` writes `.env.example` with a names-only header |
| The generated README's `credentials` managed region | **Absent — a documented surface with no code.** § The generated README (`reference.md:3238–3247`) shows a `cp .env.example .env` setup line and a `<!-- publishable:begin credentials -->` region with a *"(none yet — added as experiments declare them)"* placeholder row. `grep -n "publishable:begin\|env.example\|Required credentials"` over a freshly scaffolded `README.md` returns `overview` and `experiments` and nothing else; control, the same grep finds both regions that do exist. § 7 |
| Error codes for the family | **Zero.** `grep -in "credential\|\.env\|E-ENV\|secret"` over `reference.md`'s § Errors `validate` reports (lines 401–967) returns one hit, and it is prose about an expired probe credential at `:734`, not a row; control, the same range for `template` returns 29 hits. § Warnings core reports carries `W-ENV-UNLOCKED`, which is `uv.lock`, not credentials |
| `spec-defects.md` entries | **None for this family.** `grep -n "required_env\|requires_env\|secret\|credential\|\.env"` returns five hits, all `provenance.environment` or `.env.example`-in-a-scaffold-overwrite prose. `grep -n "H7c"` → nothing. § 7 |

---

## 2. The totality check mints no code — the precedent is shipped

`reference.md:1633`: *"`validate` rejects a mapping with a missing or unknown key **when
the template loads**, naming both sets."*

`reference.md:1602`, one section up, for the sibling constraint: *"A `Param` declaring
`default=None` without `nullable=True` is rejected **when the template loads**, rather than
at the first config that leaves it alone."*

The second is built, as a `ValueError` raised from `Param.__init__` (`param.py:34–35`).
**What a reader needs to know is what a user sees**, and that was probed rather than
reasoned:

```
$ publishable new proj && cd proj
$ publishable generate experiment --template generic bad --input-dir … --output-dir …
$ publishable validate configs/bad/config.yaml          # control, before the bad template
  error   E-UNITS-KEY-MISSING  data.units …             3 problems

$ cat > templates/badnull.py                            # Param(str, default=None)
$ publishable validate configs/bad/config.yaml
  error   E-TEMPLATE-LOAD      experiment_type
          the project-local template `…/templates/badnull.py` raised while importing and
          registers nothing usable: ValueError('default=None requires nullable=True')
  1 problem (1 error, 0 warnings)

$ sed -i '' 's/default=None)/default=None, nullable=True)/' templates/badnull.py
$ publishable validate configs/bad/config.yaml          # control fires again
  3 problems (3 errors, 0 warnings)
```

Three things this establishes, none of which the charter has:

- **A `Param` construction fault is already a load fault with an identifier**, and the
  `ValueError` text is interpolated verbatim into `E-TEMPLATE-LOAD`'s message
  (`discovery.py:313`). So `requires_env`'s three faults — no `choices`, a key naming no
  choice, a choice with no key — are raised the same way and need **no new identifier**.
  The *"naming both sets"* requirement is a message requirement on the `ValueError`.
- **It is an early return.** The bad template collapsed a three-error report to one. That
  is § Errors' documented ordering working, and it means H7c adds nothing to the
  early-return prose at `reference.md:432–456` — but a task must check it, because that
  prose enumerates the load refusals and H7b task 2 is already editing it.
- **This holds only for a project-local template.** An *installed* plugin whose module
  raises at import is H7b task 17's containment, which does not exist. So the totality
  check is fully testable under H7c alone and only for the `templates/` path — state it
  rather than let a plan discover it.

**And `E-TEMPLATE-LOAD`'s scope is enumerated in four places, all of which already cover
it.** This was checked rather than assumed, because a code whose row enumerates its cases
owes a prose edit when a case is added:

```
$ grep -n "E-TEMPLATE-LOAD" docs/reference.md src/publishable/templates/discovery.py
reference.md:568, :1007, :3414      each: "raises while importing, imports cleanly but
                                    never calls @register_template, or registers a class
                                    that is not a BaseTemplate subclass"
discovery.py:252–259                the same three, in the docstring
```

A `Param` construction fault is the **first** of the three — the module raises while
importing — so the enumeration is already total over it and **no § Errors row is owed**.
Control, per the rule that an enumerating row must be distinguished from a generic one:
`E-DATA-ASSIGN-RATIO` at `reference.md:475` enumerates its cases the same way, so the grep
can tell the two shapes apart.

**Two codes remain to mint**, for § Validation's *Credentials present* (`reference.md:264`)
and *Credentials a swept value needs* (`:265`) — or one, per § 3.

---

## 3. One mechanism, two collectors — the decision H7c owes

`required_env` and `requires_env` reduce to the same thing: **a set of variable names that
must be present in the environment at check time.** They differ in two ways only.

| | `BaseTemplate.required_env` | `Param(requires_env=)` |
|---|---|---|
| When the set is known | At template load. It is a class attribute | After `expand`, from the resolved conditions |
| What the message must name | The template | The parameter, the value, and the condition that selected it |
| § Validation row | *Credentials present* (`:264`) | *Credentials a swept value needs* (`:265`) |

**The precedent does not settle it.** `reference.md:570`'s `E-TEMPLATE-UNKNOWN` row governs
two emit surfaces under one code *because they are "the two built from one shared
message"*. Here the two messages cannot be shared — one names a template and one must name
a condition label — so the `CLAUDE.md` rule that *§ Errors carries one row per code, not
per emit site* cuts the other way: two messages that differ in what they identify are two
rows, or one row that must enumerate both, which is the shape that row exists to avoid.

**Recommendation, not a ruling: two codes.** But the decision belongs in the design, made
explicitly, because it determines whether task 1 writes one row or two and whether the
union check can reuse the template-level collector's emit site.

**Closing `required_env` is a defect closure, not a neutral addition.** `CLAUDE.md`
§ Reading the documents names this attribute *by hand* as the canonical example of *"an
unbuilt reader of a **shipped** surface"*, and `H7b-SCOPING.md` § 5c re-measures it as one
of four such members. H7c is the first reader. That has a consequence the charter has no
task for: **`CLAUDE.md`'s example stops being true when H7c lands**, and the row needs a
surviving example — `field_convention`, `apparatus_probe` and `apparatus_facts` are the
three that remain, and H7b task 13 takes `apparatus_probe`.

---

## 4. Secrets — what must never happen, and the one place it can

**What the documents specify.** A secret is a credential *value*. The config holds only the
environment variable's **name** (`reference.md:3474`, with the inline comment *"the NAME,
never the value"*). Core loads `.env` via `python-dotenv`, *"never reads it into
provenance, and gitignores it in every scaffold"* (`:3464`). `design-principles.md:40`
states it as a principle: *"Secrets are the one thing never captured."* The payoff claim is
at `reference.md:3477`: *"`report` and `diff` output is safe to send as-is: there's nothing
secret to redact, because there was never anything secret in it."*

**Which surfaces would need to exclude a secret — measured, and the answer is almost
none.**

| Surface | Can a value reach it? |
|---|---|
| `code_hash` | **No.** `hashes.HASHED_TREES = ("src", "templates")`. `.env` is in neither, and is gitignored besides |
| `parameters_hash` | **No.** It hashes the config, which holds names |
| `input_manifest_hash` | **No.** It is built from `input_dir`, which may never resolve inside the repo |
| `provenance` | **No** — nothing in `src/` reads the environment at all. `provenance.environment` is `os`/`hostname`/`hardware`/`uv_lock`, and `reference.md:3072` already treats `hostname` as the sensitive one |
| `run.yaml` | **Yes, by one path.** `run_record.py:37` writes `entry["error"] = r.error` for any non-`completed` execution |
| `executions.jsonl` | **Yes, the same path.** `runner.py:713` writes `"error": error` into the ledger |

So **the invariant is currently maintained by absence**: core reads no environment
variable, so nothing can leak. H7c is the slice that starts reading them, and the one
accident it must survive is a step whose exception text carries the value — a client
library that interpolates an API key into a URL in its error message, which is ordinary.

**This makes the charter's task 6 — *"a test that no command's output, and no provenance
field, can carry a secret's value"* — exactly `CLAUDE.md`'s *a control asserting only
absences*: it passes identically if nothing ran.** The test that can fail is:

1. A `.env` holding a distinctive sentinel under a name the config declares.
2. A step that **actually reads it** through `os.environ[…]` and uses it.
3. A sweep of `run.yaml`, `executions.jsonl`, `allocation.json`, every written artifact,
   and stdout/stderr for the sentinel — **filtering the file list, never the output**.
4. The mutation: a step that raises with the sentinel in its exception text. If step 3
   does not go red, step 3 is testing nothing.

Whether that leak is *refused* (scrub known credential values out of `r.error`) or merely
*documented* is a decision H7c owes, and it is the only genuine exclusion question in the
slice. Scrubbing has a cost worth stating: core would have to hold the values it promises
never to hold onto, in order to remove them.

**The `.env` load site is two sites, not one.** § Secrets says core loads `.env` *"before
any step runs"* — an executing-command statement. But § Validation's three credential rows
are `validate`'s, and `validate` cannot report *"`INSTRUMENT_API_TOKEN` is not set in
`.env`"* without loading it. **This is not a contradiction of `validate`'s promise**:
`reference.md:3109` and `:3177` promise only that `validate` *"creates nothing and reaches
nothing **off the machine**"*, and reading a file in the repo root is on-machine. It *is* a
sentence that describes one of two load sites as if it were the only one, and a task must
fix it. A third site is specified and unbuildable: `reference.md:2599` says **`dry-run`**
*"needs what a run needs minus the compute … which means real credentials"* — `dry-run` is
in `cli.NOT_BUILT_COMMANDS`, so that is a claim H7c cannot honour. § 7.

---

## 5. The nine feasibility configs — what actually changes

**None of the nine declares `requires_env`, `required_env`, or a credential in its YAML,
because none of them can: those live in the plugin, not the config.** The question that
matters is what the *template* needs and what the configs resolve.

```
$ grep -n "llm\.provider" docs/feasibility-llm-growth-studies.md
490, 807, 834, 863            # all prose or the plugin's own parameter table
$ grep -n "llm\.model" docs/feasibility-llm-growth-studies.md
455, 469, 470, 490, 833       # :469 is inside E6's `sweep.grid` — control fires
$ grep -n "paired:" docs/feasibility-llm-growth-studies.md
189, 678                      # both `paired: []`
```

| Claim | Measured |
|---|---|
| `llm_screen` declares `required_env = []` | Yes — `:863`, *"Nothing this template needs unconditionally"* |
| `llm_screen` declares `Param(..., requires_env=…)` on `llm.provider` | Yes — `:490`, `:834`, `:941`. This is what `Param.__init__` rejects |
| Any of the nine **sweeps** `llm.provider` | **No.** It appears in no fenced YAML at all. E1's `parameters` block fixes `provider: azure_openai` (`:149`) and the other eight show only their deltas |
| E6, the case the feature was designed for | Its shown `sweep.grid` varies `llm.model` only (`:469`). The Ollama cell is described **in prose** (`:490`) as entering *"as a `sweep.paired` entry coupling `llm.provider` with `llm.model`"* — and E6's `sweep.paired` is `[]` |

**Consequences, in the order they bite:**

1. **H7c retires no refusal, and changes zero configs' `validate` output.** Every one of
   the nine still earns `E-DATA-RESOLVER-UNSUPPORTED` (H7b), and C1–C3 still earn
   `E-DATA-WEIGHT-CONTRAST` (H4b). H7c's deliverable is upstream of `validate` entirely:
   **the analysis's plugin becomes importable.** Today `llm_screen.py` raises `TypeError`
   at module scope, which is not a finding — it is an entry point that cannot load. Writing
   this as an unblocked-run count would repeat the mistake this repo has now made twice.
2. **All nine resolve a single provider, so a static `required_env` would have sufficed
   for every config in the evidence base.** The union-over-conditions check — the entire
   justification for `requires_env` over `required_env` — is **a seam named in the brief
   and instantiated by no fixture**, `CLAUDE.md`'s exact shape. H7c must write its own
   multi-provider config, and the design should say so rather than reaching for E6.
3. **The union is over *all* expansion modes, not just `grid`.** `sweep.NON_PRODUCT_MODES`
   is `("baseline", "ablate")`; a `baseline` fixing `llm.provider` is a resolved condition
   whose credential must join the union, and `ablate.remove` sets a nullable parameter to
   `null` — a nullable parameter with `choices` and `requires_env` is a legal declaration
   whose removed value has no key in the mapping. Neither case has a fixture and neither is
   in the charter.

---

## 6. The ordering constraint against H7b — stated task to task

**H7b Part A (its tasks 1–19) needs nothing from H7c.** Its entry-point tests run against a
synthetic distribution by its own task 7's note, and the metadata scan never calls `.load()`,
so no `parameter_spec` is ever constructed.

**The dependency is exactly one edge:**

> **H7c task 3 (`Param(requires_env=)`, the constructor argument — § 8's Part A) must land before any H7b
> task that imports the feasibility analysis's plugin.** Concretely that is **H7b task 27**
> — the dated executability re-measurement and the owned prose sweep — and any H7b Part B
> test that installs a real resolver written as `llm_screen`. Nothing else.

**The reverse direction is empty, and that is the strongest form of H7c's independence.**
The totality check needs the template-load path, shipped by H7a; the union check needs
sweep expansion, shipped long ago; both are exercised end to end through a **project-local
template with no plugin at all**, as § 2's probe shows. H7c is genuinely shippable first,
alone, and its tests never need an installed distribution.

**Genuinely independent — these can sit anywhere in a combined plan:** tasks 1, 4, 5, 6,
12, 13, 14 of § 8. They touch documents, `param.py`'s rendering, and `spec-defects.md`, and
none of them reads an environment variable or a registry. **Task 2 is independent of the
environment but coordination-constrained with H7b**, per the paragraph below.

**Two shared edits a combined plan must not do twice.** H7b task 2 rewrites § Errors'
early-return ordering prose (`reference.md:432–456`) and fixes `validate.py:519`'s *"two
today"* count; H7c § 2 lands a third and fourth load-refusal shape on the same prose.
And H7b task 4 splits the § The importable surface `register_*` row while H7c must state
in that same section that it exports **nothing** (§ 7). Assign each to one slice.

---

## 7. Two charter items that move, and what the charter does not own

### Charter task 3 shrinks

*"`Param(requires_env=...)`: constructor argument, `choices` requirement, totality-over-choices
check at template load. **New identifier**."* — the identifier is `E-TEMPLATE-LOAD` and
already exists (§ 2). A re-scoping that shrinks a task is unusual here, so the argument is
written down rather than assumed: the shipped sibling constraint uses the same specified
words (*"rejected when the template loads"*), takes the same route, and produces a
diagnostic with the `ValueError` text interpolated. Minting a second code for the same
route would give one fault two identifiers.

### Charter task 7 is routed out

*"`generate experiment` merges new `required_env` into the README's managed credentials
region."* Three facts, none of which the charter had:

- The region **does not exist** in the scaffolded README (§ 1). Without it there is nothing
  to merge into.
- `reference.md:3271` already marks *"merging any new `required_env` into the credentials
  table"* **NOT BUILT**, and calls out in the same paragraph that `required_env` *"compounds
  that gap rather than merely sharing it"* — it is a specified reader of an unread member.
- `publishable docs`, which § The generated README says regenerates every managed region,
  is in `cli.NOT_BUILT_COMMANDS`.

`H7b-SCOPING.md` § 11 routes *"the README managed regions — `credentials`, a parameter-table
region, `generate experiment`'s merge"* to **`docs`**. **This is the one place this document
contradicts it**, and the correction is narrow rather than a disagreement about ownership:
the *static* `credentials` region and the `cp .env.example .env` setup line are written by
**`new`**, i.e. `scaffold.py`'s README constant, not by `docs` — and `docs` has nothing to
populate until they exist. So the routing is right for the merge and wrong for the region.
H7c files it (task 14); whoever owns `new`'s README emits it; `docs` populates it.

### Two more specified surfaces H7c cannot honour, both worth naming so nobody folds them in

| Specified | Why not H7c |
|---|---|
| `reference.md:3517` — `reproduce` step 6 *"copies `.env.example` and lists the `required_env` variables that need values"*, and `:3533`'s consequence | `reproduce` is in `NOT_BUILT_COMMANDS`. The reader of `required_env` here belongs to `reproduce`'s slice, and H7c owes only that the attribute is readable |
| `reference.md:2599` — `dry-run` *"needs what a run needs minus the compute … real credentials"* | `dry-run` is in `NOT_BUILT_COMMANDS`. H7c's load sites are `validate` and the executing commands; `dry-run` inherits the check when it is built |

### What H7c will inevitably touch that the charter does not own

- **`pyproject.toml` and `uv.lock`.** `python-dotenv` is a new runtime dependency — the
  first this project has added since scaffolding. `code_hash` covers `src/**` and
  `templates/**` only, so this does not disturb any recorded hash, but it does move
  `uv.lock`, and every scaffolded project's `pyproject.toml` pins `publishable`.
- **`param.py`'s two false-guarantee sites** (§ 9).
- **`CLAUDE.md` § Reading the documents**, whose *unbuilt reader of a shipped surface* row
  uses `BaseTemplate.required_env` as its worked example (§ 3).
- **The scaffolded README**, if the `credentials` region is emitted here rather than filed.
- **The § Templates constraint table.** `requires_env` must **not** appear in it —
  `CLAUDE.md` § Invariants and `reference.md:1633`'s closing paragraph both make that a rule
  with a reason — but `reference.md:1575` already says *"`Param` carries type, default,
  constraints, help text, and any credential a chosen value requires"*, in the present
  tense, about an argument that does not exist. That sentence is inside the paragraph that
  introduces the closed table, and a task must keep the two apart.

### Documented with no code, and code with no row — the full list for this area

| Documented rule | Code behind it |
|---|---|
| § Validation *Credentials present* (`:264`) | **None** |
| § Validation *Credentials a swept value needs* (`:265`) | **None** |
| § Validation *`requires_env` covers its choices* (`:266`) | **None** — but § 2 shows it needs no new one |
| § Secrets *"Core loads `.env` via `python-dotenv` before any step runs"* (`:3464`) | **None** — no dotenv, no environment read |
| § Secrets *"A template lists what it always needs in `required_env`"* (`:3477`) | **Declaration only.** Nothing reads it |
| § The generated README's `credentials` region (`:3241`) | **None.** `scaffold.py` emits `overview` and `experiments` |
| § Reproducing step 6 (`:3517`) | **None** — `reproduce` unbuilt |
| § Metering *"`dry-run` … needs real credentials"* (`:2599`) | **None** — `dry-run` unbuilt |
| `reference.md:1575` *"`Param` carries … any credential a chosen value requires"* | **None** — present tense about an absent argument |

The reverse direction is empty: there is no code in this area with no documented row,
because there is no code in this area.

---

## 8. Decomposition — 14 tasks

Grain matches `H3d-SCOPING-2.md` and `H7b-SCOPING.md`: each document-table edit and each
new code is its own task.

### Part A — declare, render, and document. Nothing reads the environment · 6

| # | Task | Why separate |
|---|---|---|
| 1 | **§ Validation ↔ § Errors `validate` reports**: mint the identifier(s) for *Credentials present* and *Credentials a swept value needs*; settle **one code or two** (§ 3) with grounds; record in the *`requires_env` covers its choices* row that its identifier is `E-TEMPLATE-LOAD` and that it mints nothing | Three rows with no identifier. `CLAUDE.md` requires the document first, and § 3's decision changes what tasks 9 and 10 emit |
| 2 | **§ Errors' load-refusal prose and its count**: `reference.md:432–456`'s early-return enumeration, and `validate.py:519–531`'s *"two today"* comment, both of which H7b task 2 also edits | A count phrase beside an insertion point — `CLAUDE.md`'s *check every count phrase near it*. Assign to one slice in a combined plan (§ 6) |
| 3 | **`Param(requires_env=)` — the constructor argument**: stored; `choices` required; totality over `choices` in both directions; `ValueError` naming **both sets**, on the `nullable` precedent. Amend `param.py:3`'s *"The constraint vocabulary is closed on purpose"* to say why this argument is not one | **The H7b prerequisite** (§ 6). The docstring is not optional: without it the new argument reads as a widened vocabulary, which is the invariant it must not break |
| 4 | **`Param.comment()` renders the per-value requirement**, against *every* choice rather than the written one (`reference.md:1623–1631`); amend `comment()`'s *"One constraint claims it, else `help`"* docstring | Six sites pin the current string — `grep -rn "choices:" tests/` → 2, `docs/reference.md` → 4 — so the blast radius is small and countable, which is worth recording before a plan assumes otherwise |
| 5 | **§ Templates' constraint table and § The one config file**: `requires_env` stays **out** of the closed table; `reference.md:1575`'s present-tense claim reconciled; the enum-comment cross-document rule re-run over the rendered example | The rule that `requires_env` is not a constraint is normative in two files, and the paragraph introducing the table already contains the sentence that violates it |
| 6 | **§ Package layout + § The importable surface**: retire `secrets.py`'s `— not yet built`, and state explicitly that H7c exports **nothing** — `requires_env` is a `Param` keyword and `required_env` a class attribute, so the one-import-root list does not move | A slice that adds no name to the import root should say so; otherwise the next reader assumes an omission |

### Part B — read the environment · 5

| # | Task | Why separate |
|---|---|---|
| 7 | **`secrets.py` + the `python-dotenv` dependency**: `pyproject.toml`, `uv.lock`, loading from the repo root, idempotent, never into provenance | The module's own § Package layout line promises *"never touches provenance"* — a safety claim in a comment, so it needs a mutation like any other |
| 8 | **The two load sites**: `validate`, and before any step runs in `run`/`draft`/`resume`; reconcile `reference.md:3464`'s single-site sentence; record that this is not a breach of `validate`'s *reaches nothing off the machine* promise | § 4. A plan reading only § Secrets builds one site and silently makes three § Validation rows unbuildable |
| 9 | **`required_env` checked at `validate`** — the template-level set. **The first reader of a shipped-unread attribute**; update `CLAUDE.md`'s worked example, which names it | § 3. A defect closure, not a neutral addition |
| 10 | **`requires_env` union over the conditions the sweep actually resolves**; message names parameter, value, and condition label | § 5. The union is the feature; the message is what distinguishes it from task 9's |
| 11 | **The expansion modes the union must cover**: `baseline`'s fixed values, `paired`, `groups`, and `ablate.remove` against a nullable parameter with `choices` — a resolved value with no key in the mapping | § 5 finding 3. `NON_PRODUCT_MODES` means a baseline is a resolved condition; no fixture exists for any of these |

### Part C — prove it, and sweep · 3

| # | Task | Why separate |
|---|---|---|
| 12 | **The no-leak test, with a mutation that can fail**: a `.env` sentinel, a step that reads it, a sweep of `run.yaml` / `executions.jsonl` / `allocation.json` / artifacts / stdout / stderr with the **file list** filtered rather than the output; the mutation being a step that raises with the sentinel in its message. Decide and document whether `run_record.py:37` and `runner.py:713` scrub or merely disclose | § 4. The charter's version is a control asserting only absences |
| 13 | **The owned prose sweep**: the twelve document sites of § 7's table plus `README.md:10`/`:77`/`:134`, `design-principles.md:39`/`:40`/`:156`/`:211`, `experimental-designs.md:381`/`:382`, and `tests/` — **named** files, since the development record is tracked and `*.md` no longer means the four documents | `CLAUDE.md`: three sweeps in one slice each stopped one file short. Prove each sweep can fail against a string known to be present |
| 14 | **`spec-defects.md` filings**: the absent README `credentials` region and `cp .env.example .env` line (§ 7, with the routing correction against `H7b-SCOPING.md` § 11); `reproduce` step 6's and `dry-run`'s credential readers named with their owning slices; re-owner anything that pointed at "the secrets slice" | This family has **zero** entries today and three deferrals that would otherwise be undocumented. `CLAUDE.md`: a ledger line saying "filed" is not a filing |

### If the combined H7b + H7c slice runs long

**Ship H7c whole (14) before H7b Part A (19).** It is the smaller half, the only half that
is a prerequisite for anything, and the only half testable with no installed distribution
(§ 6). Neither H7c nor either H7b part is then past twenty, which is this repo's own band.

If H7c itself must be split, the seam is **6/7**: Part A changes no behaviour at all beyond
`Param`'s constructor and its rendered comment, has no dependency on `python-dotenv`, and
**already contains the whole H7b prerequisite** (task 3). Part B+C is then a second slice
that H7b never waits on.

---

## 9. False guarantees in the files H7c must edit

| Site | Claim | Status |
|---|---|---|
| `param.py:3` | *"The constraint vocabulary is closed on purpose"* | True today; **false the moment task 3 lands** unless amended, because `requires_env` is explicitly not a constraint (`CLAUDE.md` § Invariants; `reference.md:1633`) |
| `param.py:109` | `comment()`'s *"One constraint claims it, else `help`"* | True today; **false after task 4**, when a choices comment carries per-value credential annotations that are not constraints |
| `reference.md:1575` | *"`Param` carries type, default, constraints, help text, and any credential a chosen value requires"* | **False today**, in the present tense, about an argument `Param.__init__` rejects |
| `reference.md:3477` | *"`validate` confirms each is set … without printing or logging it"* | **Aspirational today** — nothing confirms anything. Not a defect; recorded so it is not "fixed" |
| `reference.md:3603` | `secrets.py`'s *"(never touches provenance)"* | A safety claim about a module that does not exist. `CLAUDE.md`: *if a comment says this cannot happen, make it happen* — task 7 owes the mutation |
| `templates/base.py:15`, `builtin/generic.py:9` | No comment claims anything, and that is the finding: a declarable attribute with no docstring saying nothing reads it | The `generate template` stub omits it deliberately (`generators/template.py:9`), which is the honest containment; the class still ships it |

---

## 10. Traps specific to this slice

**Testing the refusal, never the honouring.** The charter is three-quarters refusals — a
missing key, an unknown key, an unset variable. `CLAUDE.md` records this exact shape from
H3c: *"`validate` refused bad `block_size` values while nothing checked the draw used a
good one."* The honouring here is that a **correctly declared** `requires_env` over a
**satisfied** environment validates clean and that the union is computed over the right
condition set. Without that test, ignoring `requires_env` entirely passes the suite.

**A fixture with too few providers to distinguish the candidate readings.** Two choices
cannot separate "the union over resolved conditions" from "the union over all choices"
from "the requirement of the written value" — with a two-value `choices` where the sweep
selects both, all three readings give the same answer. **Count the readings first (there
are at least three), then size the fixture**: three choices, a sweep selecting two, and a
third whose variable is deliberately unset, is the smallest fixture where each reading
gives a different verdict.

**An absence proved by an environment that was empty anyway.** `os.environ` is inherited
from the test runner. A test asserting *"`AZURE_OPENAI_API_KEY` is not set, so `validate`
reports"* passes on a machine where nothing was ever set, and would pass if the check did
not exist — but the *positive* test fails mysteriously on a developer machine that happens
to have the variable. Both directions need `monkeypatch.delenv`/`setenv`, and the negative
test needs a control that sets the variable and expects silence.

**A monkeypatch aimed at a name the load path no longer calls.** § 4 puts `.env` loading at
two sites. A test patching `load_dotenv` at one and asserting the other's behaviour is
`CLAUDE.md`'s *monkeypatch left aimed at a name the code no longer calls* — and the two
sites are in different modules, so the patch target is not obviously wrong on inspection.

**Answering "is this a secret?" with a proxy.** The temptation in task 12 is to detect
leakage by pattern — a name ending `_KEY`, `_TOKEN`, a high-entropy string. That is
`CLAUDE.md` § Answering a question with a proxy, twice-burned in H7a: the direct question
is *is this exact value one core read out of the environment*, and core knows the answer
because it read it. A pattern check fails open on a credential named `instrument_pw` and
fails closed on a config value that happens to look random.

**Reading the `-UNSUPPORTED` family in.** H7c retires **no** refusal. There is no
`E-SECRET-UNSUPPORTED` and none must be minted on the way in: a narrow refusal of a
combination is documented and carries rows, while this family has no refusal at all, only
missing checks. The § Validation rows have existed since H1 (`H1-SCOPING.md` rows 234, 236)
with nothing behind them.

**A `Param` fault that is not a `validate` finding.** § 2's early return means a bad
`requires_env` mapping collapses the whole report to one error. A test asserting a finding
*list* rather than membership will look correct and be pinned to the collapse. And for an
*installed* plugin the same fault is not a finding at all until H7b task 17 lands — so a
test written against an installed distribution measures H7b, not H7c.

---

## 11. What is NOT in H7c

| Out | Owner |
|---|---|
| Entry points, the four registries, resolvers, `plugin new` | **H7b.** H7c needs none of them (§ 6) |
| `Apparatus`, probe execution, `apparatus_probe`/`apparatus_facts` — the two remaining unread `BaseTemplate` members after task 9 | **H7d** (and H7b task 13 for `apparatus_probe`'s registration answer) |
| `field_convention` — the third unread member | Unowned. Worth a `spec-defects.md` line in task 14 |
| `generate experiment` merging `required_env` into the README credentials table | **`docs`** — but the region it merges into is `new`'s, and absent (§ 7) |
| `reproduce`'s `.env.example` copy and its `required_env` listing | **`reproduce`'s slice** |
| `dry-run` requiring real credentials before it meters | **`dry-run`'s slice** |
| Any change to `HASHED_TREES` | Never. `.env` is outside both hashed trees and gitignored; a secret has no business near `code_hash` |
| Redaction in `report`, `diff`, or `study add` | Never, and `reference.md:3477` states why: *"there was never anything secret in it."* A redactor would be an admission that the design failed |
| Fetching or transmitting a credential | Never — `design-principles.md:211`, a stated non-promise |
