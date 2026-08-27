# W2 scoping — what a template's `validate` receives

Read-only measurement against `main` at `92634af`, on 2026-08-27. Every identifier, call-site
count and probe result below was grepped or run against that tree, never remembered. Spec
claims and build facts are labelled separately throughout.

Chartered by [`spec-defects.md`](spec-defects.md)'s entry *`template.validate` receives a plain
dict, while § The importable surface says it receives the dot-access config node*, filed
2026-08-27. `W1` is the sibling slice, merged; the `W` names are explained there.

**Verdict: 7 tasks, and the fix is a deletion.** The elegant answer is not to build the
wrapper the document describes. It is to delete the one clause that describes it, because
**the document already contradicts itself** — the paragraph justifying the `raw` accessor says
in so many words that *"`validate` and a template's `validate(config)` both need the underlying
mapping"*, which is exactly what the code hands them. The only fiction is the wrap-then-unwrap
step in between.

**Baseline at `92634af`:** `uv run pytest -q` → **3461 passed, 1 skipped, 2 xfailed**, 374 s.

---

## 0. Three measurements that decide the design

### 1. On core's own materialized config, the documented idiom raises

`reference.md` § The importable surface promises the node *"is how a cross-block rule reads
`data.units.holdout` without core handing it a second shape."* Run against a config
`publishable generate experiment --template my_assay` had just written, wrapping it in `Config`
and walking the seven paths a cross-block rule would actually ask about:

```
OK    data.units.holdout = None
RAISE statistics.contrasts: E-STEP-PARAM-UNKNOWN: statistics.contrasts is not a path this config holds
RAISE statistics.report_by: E-STEP-PARAM-UNKNOWN: statistics.report_by is not a path this config holds
RAISE statistics.resample: E-STEP-PARAM-UNKNOWN: statistics.resample is not a path this config holds
RAISE statistics.null_test: E-STEP-PARAM-UNKNOWN: statistics.null_test is not a path this config holds
RAISE sweep.grid:          E-STEP-PARAM-UNKNOWN: sweep.grid is not a path this config holds
OK    hypotheses = []
```

**Five of seven raise**, and the two that pass are accidents of what `init` materializes:
`holdout` reads because `init` writes it as an explicit `null`, and `hypotheses` because it
writes `[]`. § The one config file is explicit that `init` writes no `resample` key at all and
leaves the optional `statistics` sub-blocks out, so this is the ordinary case rather than an
edge one.

So the wrapper's one advantage — uniform dot-access — is **unavailable in exactly the case the
method exists for.** A cross-block rule's question is *is this block declared*, and a reader
that raises on an undeclared path cannot answer it. A template author would write
`try`/`except ContractError` around every probe, or reach for `config.raw` and be back to a
mapping.

### 2. The document contradicts itself, and the code implements the half that makes sense

Two paragraphs of § The importable surface, both about this argument:

> **The root config node carries exactly one accessor, `raw`; every nested node carries
> none.** … It is at the root only, because the root is the one node core hands to something
> other than a step — **`validate` and a template's `validate(config)` both need the underlying
> mapping** — and a nested node has no such caller.

> A template's `validate(self, config)` **receives this same object**, which is how a
> cross-block rule reads `data.units.holdout` without core handing it a second shape.

The first says both callers need the mapping. The second says one of them gets the node. The
code hands the mapping directly and skips the round trip — which is the first paragraph's own
conclusion reached by the shortest route. **Prefer deleting a claim to rewriting it**: the
clause to delete is the round trip.

### 3. `raw` has no reader in `src/` at all

`grep -rn "\.raw\b" src/` → **nothing** (excluding its own `def`). Its readers are ten
assertions in `tests/test_runner.py`, all of the form `cfg.raw["parameters"][...]` or
`parameters_hash(cfg.raw)`.

So the accessor's entire stated justification names **two calls that do not happen**: core's
`validate` works on `dict`s throughout (`_check_metadata(doc: dict[str, Any], …)` and every
sibling), and the template gets a `dict`. This is the *"an unbuilt reader of a shipped
surface"* row in a new costume — a shipped accessor whose reason has no reader.

**Recommended: keep the accessor, delete the false reason, file the reader gap.** Removing a
public accessor from [§ The importable surface](../reference.md)'s enumerated list is a
behaviour change to a shipped surface, and a slice chartered to correct a documentation defect
may not make one — the W1 precedent for that ruling is one file over. The reason that measures
true is narrower and worth stating: `raw` is how anything holding a **node** obtains a plain
mapping, which after this slice means a step or a template's `aggregate` rather than
`validate`.

---

## 1. What exists — measured

| Fact | Where | Measured |
|---|---|---|
| One call site, and it passes the parsed document | `validate.py:793` | `template.validate(doc)`, with `doc` from `load_document` → `yaml.safe_load` |
| The guard around it catches `SystemExit` and `Exception` | `validate.py:792-806` | so a raise becomes `E-TEMPLATE-RULE` *"raised while validating: …"*, which is why this defect is cheap to hit and easy to miss |
| Nothing else calls it | — | a `grep -rnE` over `src/` for `template.validate`, `.validate(doc` and `.validate(config` returns that one line plus one comment above it |
| The declared type is `Any` | `templates/base.py:26` | `def validate(self, config: Any) -> list[str]`, docstring *"Cross-field rules. Receives the WHOLE config; [] when OK."* |
| Both generated templates take `config` and read nothing | `plugin_scaffold.py:77`, `generators/template.py:51` | so neither shape is pinned by what core scaffolds |
| The suite pins neither shape | `tests/test_validate.py:5062` | the one stub defining `validate(self, config)` is `RuleBreaker`, whose body is `return ["a cross-field rule was broken"]` and never reads `config` |
| `aggregate`'s `cfg` **is** a node, and dot-access works there | a real `run` at `937591f` | `cfg.parameters.analysis.threshold` computed a published `hit_rate`; that half of the document is true |

**Homes of the claim, swept newline-insensitively** across the four documents, the tutorial,
the feasibility analysis and `CLAUDE.md` — because `grep -F` cannot match a phrase that wraps,
and the sweep was proven able to fail against a string known present:

| File | Carries |
|---|---|
| `reference.md` | **the false half** — the *"receives this same object"* sentence, and `raw`'s *"both need the underlying mapping"* justification |
| `reference.md` § Templates | the **true** half — *"`validate` receives the whole config, not only `parameters`"* — which stays exactly as written |
| `docs/tutorial-writing-a-plugin.md` § 4 | the workaround, taught with a link to the filing |
| `docs/feasibility-llm-growth-studies.md:891` | the true half only, in prose with no code — nothing to fix |
| `CLAUDE.md` | the invariants bullet naming `raw`'s two callers |

---

## 2. The alternative, and why it loses

**Wrap `doc` in `Config` at the call site.** One line, and it makes the sentence true as
written. It loses on three counts, in descending order of weight:

1. **It breaks the method's purpose** (§ 0.1): five of seven optional paths raise on core's own
   generated config, so every cross-block rule needs a `try` or a `raw`.
2. **The raise carries a step's identifier.** `Node.__getattr__` raises
   `E-STEP-PARAM-UNKNOWN`, so a template asking whether a block is declared would be refused
   under a code whose § Errors row is about **step code reading a parameter**, nested inside an
   `E-TEMPLATE-RULE`. Two codes, neither describing what happened.
3. **It breaks every template already written**, including the one in
   `docs/tutorial-writing-a-plugin.md` § 4 and any built against the shipped behaviour, whose
   `.get` chains become `E-STEP-PARAM-UNKNOWN` on the first call.

A **third** option — a new reader that returns `None` for a legal-but-absent envelope path and
raises for an illegal one — is genuinely nicer than either, and is refused anyway: it is a
second config shape in a project whose importable surface is an enumerated list and whose
stated rule is that *what core hands a step is minimal on purpose*. A reader type existing for
one method is the surface this project refuses.

**Is `aggregate` keeping the node an inconsistency?** No, and the answer is a distinction the
four documents already draw hard: `aggregate` reads **resolved** values — a condition's `cfg`,
where every parameter has a value and a miss really is a typo — while `validate` reads
**declarations**, absences included. *Declared vs. derived* is one of the cross-document
consistency classes. One method reads what the file says; the other reads what the run resolved.
Two questions, two shapes, and the shapes follow the questions.

---

## 3. Decomposition — 7 tasks

### Part A — the document says what the code does · 5

1. **Delete the round-trip clause** in § The importable surface. The sentence keeps its subject
   — a template's `validate` receives the whole document — and loses *"receives this same
   object"*. It gains what the shape actually is, and the reason: a cross-block rule asks
   whether a block is **declared**, and dot-access raises on an undeclared path.
2. **`raw`'s justification** in the same section: its caller set is empty (§ 0.3). Delete the
   two named callers, state the class that measures true — anything holding a node needing a
   mapping — and **file** the zero-reader fact rather than removing a documented accessor.
3. **§ Templates gains the shape and a worked idiom.** Its `holdout`-or-`fold` example is prose
   today; make it code, because a promise whose whole value is that an author can copy it should
   be copyable. It must run against an `init`-materialized config, which § 0.1 shows is not
   automatic.
4. **`BaseTemplate.validate`'s signature and docstring**: `config: Any` → a `Mapping`, and the
   docstring says *declared, not resolved* — the one sentence that stops the next reader
   assuming it mirrors `aggregate`'s `cfg`.
5. **The two generated templates** name the shape in the docstring their author reads first
   (`plugin_scaffold.TEMPLATE_PY`, `generators/template.py`). Both must still run, and the
   CLI-table and scaffold-digest tests must stay green — `plugin_scaffold`'s output is pinned by
   `tests/test_plugin_scaffold.py`, and `generate template`'s by `tests/test_docs.py` and `tests/test_cli.py`, which are the two files naming `generate_template` (grepped).

### Part B — the pins · 2

6. **The documented idiom, end to end.** A template whose `validate` walks
   `config.get("statistics", {}).get("contrasts")` on a config that declares neither returns
   `[]` and reports **nothing**; one that finds a rule broken reports it. Wrapping the argument
   in `Config` fails both — that is the mutation, and it is the whole reason these two fixtures
   exist rather than a type assertion, which would pass against a wrapper that happened to
   expose `.get`.
7. **The five raising paths, pinned as the reason.** A parametrized arm over
   `statistics.contrasts`, `report_by`, `resample`, `null_test` and `sweep.grid` asserting each
   reads as absent through the shipped shape on an `init`-materialized config. This is the arm
   that stops a later slice making the document true by building the wrapper without re-running
   § 0.1's measurement. The sweep of § 1's five files closes with it, the tutorial's § 4 stops
   being a workaround and becomes the rule, and `spec-defects.md`'s entry is struck with the
   readers named.

---

## 4. What is NOT in this slice

- **Removing `raw`.** Argued out in § 0.3: a documentation-correction slice may not change a
  shipped surface. Filed instead, with the measurement.
- **A third config shape** for declaration reads. Argued out in § 2.
- **Changing what `init` materializes** so the node idiom would work. It would make five paths
  present and the wrapper viable — and it changes every generated config, every worked
  `config.yaml` example in the four documents, and `parameters_hash`'s input for anyone
  regenerating. A behaviour change to shipped output, chartered by nothing, to make a sentence
  true that § 2 argues should be deleted.
- **`Node.__getattr__`'s code choice.** `E-STEP-PARAM-UNKNOWN` from a non-step reader is only a
  problem *under* the rejected wrapper. Nothing to fix once the wrapper is refused.

---

## 5. Traps specific to this slice

| Trap | Why it applies here |
|---|---|
| A test whose name claims the guarantee | *"…receives a mapping"* is satisfied by `isinstance(config, dict)`, which a wrapper exposing `.get` would also satisfy. Pin the **behaviour** — an absent optional block reads as absent and produces no finding |
| A control asserting only absences | Task 6's first fixture asserts that **nothing** is reported. Paired with the second, which must report, or it passes identically when `validate` is never called |
| Reporting zero disagreements | § 1's table is six greps and one probe. Every row was run; the *"the suite pins neither shape"* row is the one to re-check before trusting, since that is exactly where this repo's zeros have hidden six times |
| Rewriting a sentence when the thing that was wrong is a claim about a caller | `raw`'s paragraph is wrong about **who calls it**, not about what it does. Deleting the caller list is the fix; re-justifying the accessor from an invented reader is how a false comment gets replaced by a fresher false comment |
| A sweep whose triage discards a true hit | Four of the five files in § 1 carry the **true** half of the claim, which reads exactly like the false half. Attribute every hit before counting it: only `reference.md` needs an edit for the shape |
