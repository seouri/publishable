# H5a — write-side integrity and the reserved-column namespace — design

H5a is the first of H5's two sub-slices. It owns everything that happens **before and during a write**
to a per-unit table or a row-shaped artifact: what a column may hold, what a column may be called, and
what happens to a value on its way into a cell. H5b owns everything **downstream of a write that already
works** — a non-numeric column reaching `collapse_repeats`, `summarize_step` and the table a template's
`aggregate` receives.

The charter this replaces is one row in
[the spine design](2026-08-08-implementation-spine-design.md) § The hardening slices:
*"`units.parquet` integrity: non-numeric recorded columns, cross-row type unification, and the
reserved-column namespace `finalize` merges into"*. That row does not survive its own scoping:
**two of its three items are built.** The measurement is [`H5-SCOPING.md`](../H5-SCOPING.md), dated
2026-08-21 and pinned to `0bd29a3`; **it is this design's input and it supersedes the charter.**

---

## What this slice is, in one paragraph

`units.parquet` is written correctly today for the ordinary case and is unguarded at three edges. An
attribute may take the name of a structural column and replace it. A value on its way into a `.csv` or
`.parquet` cell is checked by nothing, so a structure lands in a cell the reader cannot give back, and a
NumPy scalar beside its Python counterpart is refused as a type clash it is not. H5a closes the three
edges from the write side and states, in `reference.md`, the rules that were already enforced and never
written down.

---

## The measurement this rests on

**Measured on 2026-08-21 against commit `38df123`** (`main` at HEAD, clean tree — a docs-only commit on
top of the `0bd29a3` the scoping pinned). Read-only: nothing under `src/`, `tests/`, `README.md`,
`docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md` or
`docs/feasibility-llm-growth-studies.md` was edited to produce it, and no entry in
[`spec-defects.md`](../spec-defects.md) was touched. Every project and run directory built for it lives
under the session scratchpad. **This document is the only file this pass writes.**

Gates at this commit: `uv run pytest` → **2835 passed, 1 skipped, 2 xfailed**, run directly.

### What this pass measured that the scoping did not

The scoping is trusted for its 17 encoder cases, its four namespace probes and its four end-to-end runs.
Six things were measured here because a decision below turns on them, and each is a claim this document
makes on its own evidence.

| Measured here | Result | How |
|---|---|---|
| A structural cell in `.parquet` | **written and round-trips** — `[{"v": [1,2]}, {"v": [3]}]` reads back as lists; a `dict` cell reads back as a mapping | direct `_encode_parquet` → `_decode_parquet` |
| The same structural cell in `.csv` | **written and does NOT round-trip** — reads back as the string `'[1, 2]'` | direct `_encode_csv` → `_decode_csv` |
| A `bytes` cell in `.csv` | writes the repr `b'x'` | same |
| A plain `io.record` column named `measurement` | **written to `units.parquet` unrefused** — `{'unit': 'U1', 'site': 'n', 'measurement': 'HIJACK', 'v': 1.0}` — while the `measurement=` branch three lines away refuses it | real `StepIO.record` + `finalize` |
| A **resolver-yielded structural attribute value** | **written unrefused** — `{'unit': 'U1', 'tags': [1, 2], 'v': 1.0}`; nothing between `resolve_units` and `finalize` types an attribute value | real `Unit`/`UnitList` + `finalize` |
| Whether coercing a row changes a legal artifact's bytes | **no** — `.parquet` from `np.float64`/`np.int64`/`np.str_`/`np.bool_` is **byte-identical** to the same column from `float`/`int`/`str`/`bool`, and `.csv` is byte-identical because `csv.DictWriter` calls `str()` | both encoders, byte comparison |
| `E-STEP-RETURN-TYPE`'s emit sites | **three, not two** — `grep -rn 'E-STEP-RETURN-TYPE' src/` returns `coercion.py`, `artifacts.py` **and `runner.py`** (a step's `run` returning a non-mapping) | read, then grepped |

That last row is the point of the house rule. The scoping enumerated two sites by reading; the grep
found a third. **Nothing below is stated about an emit site without the grep behind it.**

### The three claims of the scoping's that this design changes

1. **`_check_column_types`' exact-type normalization is not the defect** (Decision 5). Its input was.
   The scoping's task 7 prescribes fixing the normalization; doing that after coercion lands would add
   grouping logic no fixture can reach.
2. **The `np.bool_` message that names one type twice is not fixed by editing the message** (Decision 5).
   Coercion makes that case *legal*, and after it a two-name message is structurally impossible.
3. **H5a *is* a behaviour change to `run`** (see § The behaviour change, said loudly). The scoping's
   second ground for the split says only H5b is. The split still holds on the other two grounds, and on a
   sharper reading of this one.

---

## Decisions

### 1. The cross-row unification rule is stated as it is, and the code's own answer is not changed here

`reference.md` § The per-unit tables states the column *set* and no rule at all for what happens when two
rows disagree on a column's type. The rule the code enforces, measured 17 ways by the scoping, is:

- a column of one type round-trips, `str` and `bool` included;
- `int` beside `float` **promotes to float**, in both declaration orders;
- `None` is not a type — it is skipped, so a column of all `None` and a column mixing `None` with one
  type both round-trip;
- an empty row set writes an empty table and raises nothing;
- **everything else refuses** with `ContractError` · `E-STEP-RETURN-TYPE`, naming the column, both types
  and one unit for each.

**Grounds for documenting rather than revising.** The promote/refuse boundary is the one
`design-principles.md` already draws for a quantity: a per-unit metric that is whole for some units and
fractional for others is ordinary, and `bool` beside `int` is a type confusion silence would hide. Both
halves are pinned by tests that predate this slice. There is no defect here — only a rule an author
cannot learn from the documents.

**Where the code's answer is arguably wrong, and the route.** A column whose values are `str` for some
units and `float` for others is refused at the write, which costs the whole execution's record for a
step that has already run. The alternative — write the column as `str` and let the reader see the
mixture — is the more forgiving reading and it is **not adopted here**, because a mixed column is
exactly the case `E-STEP-COLUMN-UNKNOWN`'s and H5b's downstream work has to arbitrate: whether the table
`aggregate` receives carries such a column at all is **H5b's Decision 10**, and deciding the write's
strictness before the read's tolerance would fix the wrong end. Filed, not built, owner **H5b**.

**Cost if wrong.** If the rule as documented is the wrong rule, the document now says so in the present
tense and a later slice must change both ends. That is the ordinary cost of documenting a built rule, and
it is smaller than the cost of leaving the rule discoverable only by collision — which is what
`spec-defects.md`'s 2026-08-11 amendment already calls a documentation debt with H5 as its owner.

### 2. `measurements.parquet`'s column set is `unit`, `measurement`, then every recorded key — and **no** declared attribute

`reference.md` § The per-unit tables gives this file one row of a table ("the uncollapsed rows, present
only when a step passed `measurement=`") and one sentence, both about *rows*. Its **columns** are
specified nowhere, and its column set differs from its sibling's in a way a reader would not guess:
`units.parquet` carries every declared attribute and this file carries none.

**Grounds for no attributes, rather than for adding them.** An attribute comes from the roster, not from
an execution: it is constant across every measurement of one unit. Repeating it on each `(unit,
measurement)` row is a denormalization core would then have to keep consistent with `units.parquet`, for
a value the reader can already join on `unit`. § Templates already gives the same argument in the other
direction — a declared attribute "is carried through **unchanged** rather than averaged … it has nothing
to collapse across a unit's repeats" — and this file is precisely the *uncollapsed* table, where there is
nothing for an attribute to be uncollapsed into.

**The three column groups are disjoint, and that is enforced rather than assumed.** `io.record`'s
`measurement=` branch refuses a recorded key named `unit`, one named `measurement`, and one shadowing a
declared attribute — three separate raises, all `E-STEP-KEY-COLLISION`, all measured by the scoping's
probes A–C. So the column set is a concatenation with no collision possible, and the document may state
it as one.

**Cost if wrong.** If a reader needs an attribute per measurement row, they join. If that join turns out
to be the common case, adding the columns later is additive to a file with no core reader.

### 3. `RESERVED_FIELDS` splits, because it answers two questions under one name

Today `units.RESERVED_FIELDS = ("key", "paths", "attributes")`, checked at three call sites (the table
source, the glob source, the resolver source) and reported by `validate` as `E-UNITS-ATTR-RESERVED`. It
becomes two constants:

| Constant | The question it answers | Members | Why a member is in it |
|---|---|---|---|
| `UNIT_FIELDS` | *Can `unit.<name>` reach this attribute?* | `key`, `paths`, `attributes` | `Unit` is a frozen dataclass whose `__getattr__` resolves attributes; a field of the same name wins, so the attribute is unreachable by the accessor the documents give for it |
| `RESERVED_COLUMNS` | *Would this attribute silently occupy a column that already means something?* | `unit`, `measurement`, `by` | each already names a column in a per-unit table or a block in the record, and an attribute of that name lands in the same column set |

**Grounds for two rather than one wider tuple.** The two sets have **different lifetimes**. `Unit.key`
cannot be freed: the accessor is the type's own API. `unit` could be freed tomorrow by renaming the
key column, and `by` by renaming a stratum block's key. A single frozenset makes those one fact, and
`spec-defects.md`'s own filing states the cost of that in advance — *"`RESERVED_FIELDS` currently means
'field names on `Unit`' and the fix needs it to mean 'names an attribute may not take', which are two
different sets; conflating them is how the next reserved column gets missed."* The next reserved column
gets missed by being added to whichever set the reader happens to open.

**What each costs if conflated.** Conflated, a reader adding a fourth structural column to
`units.parquet` has to know that a tuple named for `Unit`'s fields is where a column name goes; and a
reader freeing `unit` has to work out which three of six members are safe to remove. Both are the same
failure — a set whose membership rule cannot be stated — and it is the one this repo has already paid for
in `_collapse_measurements`, where the same three names are spelled as a bare literal tuple.

**One thing deliberately not done: the literals are not swept.** `artifacts.py` spells `"unit"` and `"measurement"` at both guard
sites and schema sites. Only the **guards** are re-pointed at the constant —
`record`'s collision checks, `_collapse_measurements`' structural-column exclusion, and `finalize`'s
`key != "unit"`. A row key written as `{"unit": unit_key}` is the schema, not a guard, and replacing it
with a constant would make the schema read as configurable while producing exactly the mutation-blind
refactor `CLAUDE.md` § Mechanical traps warns about. Grounds stated so an implementer does not "finish"
the sweep.

### 4. The reserved-attribute refusal mints `E-UNITS-ATTR-COLUMN`, and the mint precedes the code

`E-UNITS-ATTR-RESERVED` keeps its meaning — an attribute named for a field of `Unit`. A new identifier,
**`E-UNITS-ATTR-COLUMN`**, refuses an attribute named `unit`, `measurement` or `by`. It is written into
three `reference.md` sections **before any code**: § Validation's *Attribute names aren't reserved* row
(which today shows only the `Unit`-field case), § Errors `validate` reports, and § Steps and artifacts'
reserved-name paragraph.

**Grounds for minting rather than widening `E-UNITS-ATTR-RESERVED`.** The strongest argument *against*
minting is in this document already: § Errors `validate` reports argues, for `E-UNITS-ATTR-MISSING`
covering a non-string attribute name, that it is *"one identifier for one user-facing question ('is this
a real column?') rather than a second code for the type-shaped version of the same fault."* That test —
**mint when the fault differs, reuse when only the shape of the same fault differs** — is the right test,
and it points the other way here. The two faults differ, on the lifetime argument of Decision 3: one
says *this name belongs to the type you are declaring against*, permanently; the other says *this name
belongs to a column in the artifact*, revocably. Merging them re-conflates at the diagnostic layer
exactly what Decision 3 splits at the constant layer. `E-APPARATUS-FACT-TYPE`'s own row states the same
principle for a code sharing `coerce_scalars` with `E-STEP-RETURN-TYPE`: sharing a mechanism is not
sharing a fault.

**Rejected alternative, recorded:** reuse `E-UNITS-ATTR-RESERVED` with a two-clause row. Cheaper, and
it would leave the four documents' `E-` registry one entry shorter. Rejected on the two grounds above.
**Cost if wrong:** one more identifier in a registry the four documents enumerate, and a reader who
greps for the old code on a `by` collision finds nothing. Mitigated because both rows sit in the same
table and the § Validation row names both cases.

**The `by` case is why this is not a rename of an existing rule.** § Steps and artifacts says of the
reserved *metric* set: *"it is a set of one today; anything added to it is a breaking change to what a
template's `aggregate` may return."* That sentence must **not** be re-argued as though this slice added
to it, because it does not: the set it describes is *what `aggregate` may return*, and it stays `{by}`.
What H5a adds is a **different set with a different subject** — what `data.units.attributes` may name —
and `by` is in both for one underlying reason (a stratified block keys its rows by `by`). The document
edit is therefore to *distinguish the two namespaces*, and to say that `by` sits in both. Whether
`aggregate` returning `unit` or `measurement` should also be refused is a question about the metric
namespace and the `_attributed` merge: **out of scope, route H5b**, whose task 14 owns exactly that
arbitration.

**How this refusal relates to H8c's structural stratum test, and why neither is redundant.** H8c had to
stop identifying a `report_by` stratum by the string `by` — a recorded column legitimately named `by` was
being silently dropped from a render — and replaced the name test with a structural one: *a stratum is
identifiable by where it sits, not by what it is called.* This refusal does not restore the name test and
must never be cited as licence to. **The two answer different questions.** The refusal removes one
**producer** of a `by` column — a declared attribute — and not the **possibility** of one, because a step
*recording* a column called `by` stays legal by design, on § Steps and artifacts' own argument that the
retry which would raise it re-runs against executions that already completed. So a `by` column still
reaches the record, `report` still has to tell a stratum from a metric, and the structural test is still
the only thing that can. The refusal narrows the **namespace**; the structural test decides **meaning**.
**Cost if wrong:** if a later reader takes this refusal as making the name test safe again, they
reintroduce H8c's defect against a column the refusal never covered — which is why the argument is
written here rather than left to be inferred from the fact that one of the two names is now unavailable.

### 5. **Ruling on `io.write` versus `coerce_scalars`: the two row-shaped writers coerce; `io.write` does not**

`io.record` runs `coerce_scalars` on its values. `io.write` does not run it on anything. The coercion
lands **inside `_encode_csv` and `_encode_parquet`** — core's two row-shaped writers — and not in
`io.write`, and not in any other writer.

**Why coercion at all.** `CLAUDE.md` § Invariants is precise that *"each core writer takes exactly what
its reader gives back"*, and § Steps and artifacts states that as a promise: *"What a writer takes is what
its reader gives back, so a round trip through an artifact is true by construction rather than by
convention."* Measured, that promise is false in three ways at once, for the **one table row** that
covers `.csv` and `.parquet` together:

- a `[1, 2]` cell comes back a `list` from `.parquet` and the **string** `'[1, 2]'` from `.csv` — one
  documented row, two answers;
- a `bytes` cell comes back as the string `"b'x'"` from `.csv`;
- and the surface's own declared contract — *"a sequence of mappings, one per row, every value a
  scalar"* — has **no emit site at all**, which is `CLAUDE.md`'s *assuming a documented rule has code
  behind it* misreading in its documented form.

Coercion is the check that contract already asked for. It also retires the spurious refusal the scoping
found: `io.write("scores.parquet", result.rows)` — the shape § Steps and artifacts' own worked step
uses — raises `E-STEP-RETURN-TYPE` today when a model's rows carry `np.float64` beside a plain `float`,
with a message telling the author their column "recorded both a float64 … and a float". Rows out of a
model or a dataframe carry NumPy scalars; this is the ordinary case, refused.

**Why in the writers and not in `io.write`.** `io.write` dispatches through `WRITERS[suffix]`, and a
**plugin** registers into that registry. Coercing before dispatch would impose a flat-mapping-of-scalars
rule on every plugin writer — including one whose format legitimately takes nesting — and would break
`.json`/`.yaml`, whose documented input is *"any nesting of mappings, sequences, and scalars"*. The rule
belongs to the **format** whose contract states it, which is where the document states it, so it belongs
in the function that implements that format. A plugin writer's input stays the plugin's business.

**What a user observes, in each case.**

| The write | Today | After H5a |
|---|---|---|
| `.parquet` rows with `np.float64` beside `float` | `ContractError` · `E-STEP-RETURN-TYPE`, naming two types that are both floats | writes, and the file is **byte-identical** to the all-`float` version |
| `.parquet` rows with a `[1, 2]` cell | writes a list column | `ContractError` · `E-STEP-RETURN-TYPE`, naming the column and the row |
| `.csv` rows with a `[1, 2]` cell | writes `"[1, 2]"`, reads back a string | same refusal |
| `.csv` rows with a `bytes` cell | writes `b'x'` | same refusal — `bytes` is not in `_SCALARS` |
| a row that is not a mapping | `AttributeError` or nonsense columns | `ArtifactError` · `E-ARTIFACT-UNWRITABLE`, which is the code § Steps and artifacts **already** promises for "handing a writer anything else" |
| any legal write | — | **byte-identical**, measured on both encoders |
| `.json`, `.yaml`, `.jsonl`, a plugin's format | — | **unchanged**; no coercion runs |

**The message names the artifact, and that costs one `try`.** A writer sees rows and not a name, and the
registry's signature is a plugin contract that may not grow a parameter. So `io.write` wraps its
`WRITERS[suffix](obj)` call in one `except ContractError` and re-raises with the artifact name
**prefixed and the code preserved**, `from exc` — the same catch-and-re-code
`apparatus.check_facts` already makes over `coerce_scalars`. It prefixes and never rewords, so a plugin
writer's own message survives inside it. A recipe is its calls plus where they sit: this `try` encloses
the dispatch and nothing else, so a `ContractError` from `io.path`'s existence check is not caught by it.

**Cost if wrong.** Three writes that succeed today start failing (a structural cell in either format, a
`bytes` cell, a non-mapping row) — see § The behaviour change. If any of them is a real use, the remedy is
the same one the document already gives: `io.write("x.json", …)` takes nesting, and `.pkl`/`.npz` take
bytes. And if coercion in the writers is later judged the wrong home, moving it into `io.write` behind a
format test is a strictly smaller change than the reverse.

**What this ruling makes visible and does not close, measured here.** Ruling that only the two
row-shaped writers coerce leaves the other three uncovered, and that is not a neutral silence:
`io.write("x.yaml", {"v": np.float64(1.0)})` raises a bare `yaml.RepresenterError`, and
`io.write("x.json", …)` / `.jsonl` raise a bare `TypeError` for `np.int64` and `np.bool_` (both measured;
`np.float64` and `np.str_` happen to survive `json.dumps` because it accepts a `float`/`str` subclass).
**That is the traceback-instead-of-diagnostic `coercion.py`'s own docstring says it exists to prevent**,
in the section this slice edits, now visibly excluded rather than merely unaddressed.

**Out of scope for H5a, with grounds, and filed.** `.json`/`.yaml`/`.jsonl` take *"any nesting of
mappings, sequences, and scalars"*, so `coerce_scalars` — which walks a flat mapping — cannot be applied
to them. Covering them needs a **recursive** scalar walk, which is a new function and a separate decision
about whether nesting-taking writers should share the flat rule's vocabulary at all; inventing it inside a
slice about row-shaped tables would be the kind of scope creep that ships an unpinned second source of
truth for what a scalar is. **No remaining slice has `io.write`'s nesting writers as its surface**, so
task 12 files it as *unassigned with a reason* — the form this repo already uses — with the measurement
above and with the route named: one recursive walk, three writers, one decision.

**Rejected alternative, recorded:** coerce in `io.write` *only* for a step's own call and leave
`finalize`'s write uncoerced. It would have kept Decision 6 out of this slice. Rejected because
`finalize` is the write where a structural cell does the most damage — it is the published inference
base — and because two write paths with two rules is the divergence *One rule, all three surfaces*
exists to prevent.

### 6. Roster attribute values are coerced at `resolve_units`, so Decision 5 cannot turn a completed run into a late `ContractError`

`finalize` writes `units.parquet` through `self.write(...)`, so Decision 5's coercion applies to core's
own write. Measured: **nothing between `resolve_units` and `finalize` types an attribute value**, and a
resolver yielding `Unit(attributes={"tags": [1, 2]})` writes a list column today. With Decision 5 and
nothing else, that run would raise `ContractError` inside `finalize` — **after every execution is paid
for**, at the one write core owns, losing the record for work already spent.

So `resolve_units` runs every source's attribute values through `coerce_scalars` on its way out,
rebuilding each `Unit` with the coerced mapping. A NumPy scalar becomes its Python counterpart (which is
what `pyarrow` already stored, so no artifact moves); a structural value **refuses at roster
resolution**, which `validate` reaches and `run` reaches before the first execution.

**The code is `E-RESOLVER-YIELD`, widened — not a new identifier.** By Decision 4's own test, the fault
here does not differ: `E-RESOLVER-YIELD` already means *what this resolver yielded is not something core
can build a roster row from*, and a `Unit` carrying an unusable attribute value is that fault in a second
shape. Only a resolver can produce it — a table source hands every value through `csv.DictReader` as a
`str`, and a glob yields no attributes at all — so the code's family is right. Its § Errors row is widened
to cover both shapes; the row already exists, so no registry entry is minted.

**Why coerce rather than only refuse.** A resolver computing an attribute from a dataframe hands back
`np.float64` as naturally as a step does, and refusing it would refuse the ordinary case. Coercing makes
`Unit.attributes` values **guaranteed scalars for every consumer** — `cluster_by`, `weight_by`, a fold's
`stratify_by`, `holdout.from` and `_attributed`'s merge all read them — which is a real invariant this
build does not currently have, and it is what makes Decision 5's write incapable of a structural cell
from the roster side.

**Checked, because this is the one place Decision 6 could have moved a published number.**
`stats._is_numeric` is an `isinstance` test, and `numpy.int64` is **not** an `int` subclass (measured) —
so a coercion turning `np.int64` into `int` could in principle promote a dropped column into an averaged
one. It cannot, for attributes: `cli._attributed` merges the roster into the table's **rows only, never
into `collapsed`**, and its own docstring names this exact hazard — *"a numeric attribute … would be
published as a metric with its own `ci95` … not reachable while every roster attribute arrives from
`csv.DictReader` as a string, and the reason not to depend on that staying true."* A resolver already
makes a numeric attribute reachable today and it still does not become a metric, because the merge is
into rows. **Recorded** values are a different path and are already coerced at `io.record`. So no key's
reported value moves. Task 6's implementer should re-read that docstring rather than trust this
paragraph.

**Cost if wrong.** The `Unit` a resolver constructed is replaced by an equal-but-coerced one; `Unit` is
frozen and hashable by `key`, so nothing promises object identity, but a resolver holding a reference to
its own yielded object and expecting core to hold the same one would be surprised. Named here so the
implementer states it in the docstring rather than discovering it. And a resolver yielding a structural
attribute value stops working — a fourth new refusal, disclosed below.

**This decision exists only because of Decision 5.** If Decision 5 is reversed, this one goes with it,
and the list-valued attribute column stays. Said plainly so the two are never separated.

### 7. `np.str_` coerces; `np.bytes_` stays refused, on the `_SCALARS` ground

`_coerce_one` tests `type(value) in _SCALARS` — exact, deliberately, because `numpy.float64` is a real
`float` subclass and an `isinstance` test would let it through uncoerced into `yaml.safe_dump`. The next
line refuses anything with `__len__`, before the protocol checks, because *"a NumPy array satisfies
`__float__`, `__index__`, and `__bool__` just as a scalar does"*. `np.str_` has `__len__`, so it is
refused there. So does `np.bytes_`.

The fix is one branch, after the exact-type test: **a value that is already a `str` by inheritance is
that string** — `str.__str__(value)`, which returns an exact `str` and preserves the value.

**What makes the two different, rather than asserting it.** `str` **is** in `_SCALARS` and `bytes` **is
not**. `np.str_` is a genuine subclass of `str` (measured), so it is already one of the four types this
module accepts and the only thing wrong with it is that its type is not exactly `str` — the identical
situation `np.float64` is in, which the exact-type comment describes and the `item()` unwrap handles.
`np.bytes_` is a subclass of `bytes`, and **plain `bytes` raises the same code with the same message**
(measured): a `bytes` value has no place in a cell whose reader gives back a `str`, and admitting the
NumPy spelling of a type core refuses in its Python spelling would be the divergence *One rule* exists to
prevent. **So `np.bytes_` is refused for the reason `bytes` is refused, and the `__len__` guard is no
longer part of the answer for either.** A fix that admits `np.str_` must not be argued as also settling
`np.bytes_` — the scoping's own refinement, and the docstring says which ground each rests on.

**Why `str` only, and why not "any `_SCALARS` type by inheritance".** The other three types have no
`__len__`, so they never reach the guard: `np.float64` and `np.int64` are handled by the `item()` unwrap,
and `np.bool_` — which is **not** a `bool` subclass (measured) — is handled there too, which is exactly
why the unwrap must stay ahead of the `__index__` fallback. A branch covering all four would be three
parts unreachable. **`str` only** is the minimal branch that changes the answer.

**A widening this decision accepts on purpose.** Any `str` subclass now coerces, not only NumPy's — a
`class Color(str, Enum)` member becomes its string value. That is a decision, not a side effect of the
constructor chosen: `str(Color.RED)` is `'Color.RED'` under Python 3.11+ and would have **corrupted the
value silently**, which is why the branch calls `str.__str__` (measured: `'red'`) and why the docstring
must say so. Accepting the widening is right — a `str`-enum in a recorded column is a value, not a
structure — and the alternative, a NumPy-specific type test inside `coercion.py`, would put library
knowledge in a module whose whole argument is that it tests protocols and not vendors.

**Cost if wrong.** A user-defined `str` subclass carrying meaning beyond its characters loses that
meaning in a column. It lost it more thoroughly before, by being refused.

### 8. `_check_column_types` keeps exact-type grouping; its **input** was the defect

The scoping's task 7 prescribes fixing `_check_column_types`' exact-type normalization so a NumPy scalar
and its Python counterpart are one group. **That is not built here, and the grounds matter.**

With Decision 5 in place, `_encode_parquet` coerces before it collects columns, so every value the check
sees is exactly `bool`, `int`, `float`, `str` or `None`. The normalization is then **correct as written**:
`int` and `float` fold to `float`, and the surviving groups are exactly `{bool, float, str}`. Adding a
second, coercion-aware normalization would put NumPy knowledge in two modules and create a branch **no
fixture can reach** — which the repo's own rule permits only when "no mutation *can* reach this" is the
claim, and here the opposite is true.

**Two consequences worth carrying.**

- **The "names one type twice" defect is closed by making its case legal, not by editing its message.**
  `np.bool_` beside `bool` produced *"recorded both a bool … and a bool"*; after coercion the column is
  homogeneous and writes. And a two-name message becomes **structurally impossible**: `int` and `float`
  are one group, so no two surviving groups can report the same type name. That is a stronger fix than a
  reworded message, and it is why the pin is a *round-trip* assertion rather than a message assertion.
- **The check's docstring now carries a precondition, which makes it a safety claim needing a mutation.**
  It must say that its input is already coerced and that its correctness depends on that. Task 11's
  mutation is exactly the removal of the coercion call, and the assertion that catches it is named there.

**Cost if wrong.** If a later caller reaches `_check_column_types` with uncoerced rows, the exact-type
grouping silently returns the two-floats refusal this slice retires — a regression with no new code in it.
That is precisely why the pin is the coercion deletion rather than an assertion about the grouping: the
mutation reproduces the future caller's mistake.

The check's **message** does change, in one respect: it says *"io.record's values, a step's return, and a
template's aggregate take the same scalars"* and reports each row as `unit 'row 0'` when the rows came
from `io.write`. It names a surface the caller was not using. The message names the surface it was reached
through, passed in as the `where` every other refusal in `coercion.py` already carries.

### 9. `io.record`'s plain branch refuses a column named `measurement`, closing an asymmetry nothing filed

Measured here, filed nowhere: `io.record(key, {"measurement": ...})` **without** `measurement=` is
accepted and writes a `measurement` column into `units.parquet`, while the `measurement=` branch three
lines away refuses the identical key with `E-STEP-KEY-COLLISION`. The refusal becomes symmetric.

**Grounds.** In one step's directory, `units.parquet` and `measurements.parquet` are siblings, and
`_collapse_measurements` **consumes** the measurement axis on its way into `units.parquet` — the column
is dropped there precisely because it has no meaning once the rows are one unit. So a `measurement`
column in `units.parquet` means "the axis, consumed" for a measured unit and "whatever the step recorded"
for a plain one, in the same file, in the same column.

**Unconditional, not gated on whether `data.units.measurements` is declared.** The `unit` guard is
unconditional and this matches it. Gating would make one line of step code legal or illegal depending on
a config block elsewhere — the same *"depending on which call the step happened to make first"*
arbitrariness `record`'s own docstring argues against for the settle rules.

**Cost if wrong.** A step recording a domain column genuinely called `measurement` must rename it; it is
the same cost `unit` already imposes, and the message says which name to avoid and why.

### 10. `finalize`'s `columns` list is deduped by name

`columns = ["unit", *attribute_names, *recorded]` can hold `"unit"` twice: `recorded` excludes it,
`attribute_names` does not. The scoping's verdict is right — it is harmless in the file, because each row
is built as a dict comprehension over `columns` and the duplicate collapses. It is fixed as the list bug
it is.

**Grounds, given that Decision 4 makes it unreachable from a config.** After Decision 4 an attribute
named `unit` refuses at validate and at roster resolution, so no *config* can produce the duplicate. The
dedupe is kept anyway because `finalize` is called with a `UnitList` core constructs, and a `Unit` is on
[§ The importable surface](../../reference.md#the-importable-surface) — a caller can build one directly,
which is the layer the pin exercises. A list whose correctness depends on a refusal three modules away is
a safety argument in a comment; deduping locally is one line and needs no argument.

**Cost if wrong.** None identified. The artifact does not move — that is measured, not assumed, since the
comprehension already collapsed the duplicate.

### 11. Nothing in H5a moves a config count, and the one row H5 does move is H5b's to write

The four-row table in [the feasibility analysis](../../feasibility-llm-growth-studies.md) § Executability
on this build reads **8 of 8 · 0 · 7 · 1**. H5a moves no row, and mints no fifth number.

- **Row 1 (8 of 8 validating clean) is unmoved, and this was checked rather than assumed** — because
  three of H5a's four new refusals are reachable at `validate`. The analysis declares exactly two
  attribute lists (E-family, C-family); neither contains `unit`, `measurement` or `by`. Its one
  `io.record` payload names none of the three either — checked because Decision 9's refusal is a
  *recorded*-side one, and an attribute sweep would have missed it. It contains no row-shaped `io.write`.
- **Rows 2 and 3** are `io.reuse_from`'s and H4's. Untouched.
- **Row 4** is where H5 lands, and the scoping's re-derivation of its own predicate stands: *"free of
  every core-side dependency this analysis can name"* has one more nameable dependency — a non-numeric
  recorded column vanishing between the write and `aggregate` — it meets **all nine** configs, so naming
  it moves row 4 from **1 to 0 today**, and the fix moves it back to **1**. That is a re-derivation of an
  existing row, not a new figure.

**Ruling: H5b appends that § Executability entry, not H5a.** The dependency is real today and its fix is
H5b's `collapse_repeats` change; an entry H5a dates to its own landing would be dated to a commit that
did not change the predicate. **The alternative was to disclose at the earliest possible date** — append
it here, and let H5b append the restoration — and it is rejected only on that ground, so: **if H5b does
not land in this development cycle, the entry must be appended regardless of which slice does it**,
because row 4 reads `1` today and the honest figure is `0`. The re-derivation is carried in full in this
paragraph so the fact survives H5b slipping.

---

## The behaviour change, said loudly

**The scoping's second ground for splitting H5 says *"Only H5b is a behaviour change to `run`."* That is
not true of this design, and pretending otherwise is how a shipped command's behaviour moves without an
argument in the open.** This project has ruled twice — H7d Part B, H8b Decision 7 — that additive is
fine and changing what an existing key reports needs the argument made in the open. Here is the argument.

**Four things that run today stop running.** Each is a refusal on code that is already broken in the
artifact, and each is named so no reviewer has to find it:

1. A **structural or `bytes` cell** in a `.csv` or `.parquet` written through `io.write` (Decision 5).
2. A **row that is not a mapping** handed to either writer (Decision 5) — which makes an existing
   documented refusal true rather than inventing one.
3. A **declared attribute** named `unit`, `measurement` or `by` (Decision 4), at `validate` and at `run`.
4. A **resolver-yielded attribute value** that is structural (Decision 6), at `validate` and at `run`.

**One refusal retires.** `io.write` of `.parquet` rows mixing a NumPy scalar with its Python counterpart
— the shape § Steps and artifacts' own worked step produces — stops raising.

**One refusal is added on the recorded side.** A plain `io.record` column named `measurement`
(Decision 9).

**What does *not* move, and this is the load-bearing half.**

- **No existing key in `run.yaml` reports a different value.** H5a touches neither `stats.py` nor the
  aggregate phase; that is H5b's whole surface.
- **A legal run's artifacts are byte-identical.** Measured on both encoders: a `.parquet` column written
  from `np.float64`, `np.int64`, `np.str_` or `np.bool_` is byte-identical to the same column from the
  Python scalar, and `.csv` is byte-identical because `csv.DictWriter` already calls `str()`. Coercion
  therefore changes no file that writes today and stays legal.
- **No shipped command breaks**, because none reads `units.parquet` (§ Testability below).

**The split still holds**, on the scoping's other two grounds and on a sharper reading of this one:
different files with one contact point; H5b's first task is a document decision needing an argument
against `design-principles.md` and H5a's document work is already argued; and the two behaviour changes
are **different classes** — H5a refuses input that produces a corrupt artifact, H5b changes what an
existing key may contain. H5b's task 18 (pin `aggregated` byte-identical for a numeric-only run) has no
H5a equivalent because H5a cannot reach `aggregated`.

---

## Refusals, each with its route

| Refused here | Route |
|---|---|
| Changing the write's promote/refuse boundary for a genuinely mixed column | **H5b**, Decision 10 — the read's tolerance decides the write's strictness, not the reverse |
| Refusing a **recorded** column named `by` | **Nowhere; it stays legal by design.** § Steps and artifacts' argument holds: the retry that would raise it re-runs against executions that already completed, so the column keeps its value and draws `W-STATS-STRATUM-SHADOWED` |
| Refusing `aggregate` from **returning** `unit` or `measurement` | **H5b task 14**, which owns the `_attributed`/`E-STEP-KEY-COLLISION` arbitration where a derived key meets a column |
| A non-numeric column reaching `collapse_repeats`, `summarize_step` or `aggregate`'s table | **H5b**, tasks 11–13. The silent `n_valid: 0.0` over six `True` rows is that slice's Critical, and **H5a must not make it harder to fix**: nothing here narrows what a column may hold, and Decision 6's coercion makes attribute values *more* uniform for the table H5b widens |
| The second empty-level gate in `cli.py`'s stratum loop | **H5b task 15.** Unreachable until `collapse_repeats` admits a unit with no numeric column — which is a `stats.py` change, not the "non-numeric columns land" its filing claims |
| Coercing the rows a **nesting-taking** writer receives — `.json`, `.yaml`, `.jsonl` | **Unassigned with a reason**, filed by task 12 with the measurement in Decision 5: those three take any nesting, so the flat walk does not apply, and a recursive one is a new function and a separate decision. No remaining slice has them as its surface |
| Hashing `units.parquet` | **Out of scope, and named so it is not folded in.** `units_hash` covers the roster; a hash over the table is a new `provenance` key and an argument against § Three hashes. **H6's** boundary if anyone wants it |
| `E-STEP-COLUMN-UNKNOWN`'s behaviour | **H5b task 17.** H5a changes no column the table holds |
| The `report_by`-under-`resample` gap, `repeat_spread`'s `std: 0.0`, a degenerate stratum's missing warning | **H4 or unassigned, and they stay there** — on H4b-2's precedent. H5a touches no `stats.py` construction |
| `field_convention`, declarable on a shipped class and read by nothing | **Not H5's.** Named because § Misreadings calls it the sole remaining example of an unbuilt reader of a shipped surface, and an implementer reading `units.py` will meet it |
| Folds inside cells | **H3c-3.** `collapse_repeats`' `fold_members` is H5b's contact point, not H5a's |

---

## The discriminating fixtures

**A fixture is a claim too.** Every literal below is computed, and the computation is named. Nothing is
asserted from a hand-copied number.

### Fixture W — the writer round trip, per format

Rows built in the test, written through a real `StepIO.write`, read back through the registered reader,
and compared to the **input rows as coerced** — not to a hand-written expectation, so the claim is the
round trip rather than a literal someone typed. Arms: homogeneous `float`; `np.float64` beside `float`;
`np.str_` beside `str`; `np.bool_` beside `bool`; `int` beside `float` (asserting every value is a
`float` afterwards, which is the promotion, and computed by `isinstance` over the decoded rows rather
than by a literal). Both `.csv` and `.parquet`, because the two disagreed before this slice and the
disagreement is the defect.

### Fixture B — byte identity for a legal write

The NumPy-spelled and Python-spelled versions of one column are written to two artifacts and the two
files' **bytes** compared. The literal is not a number at all — it is an equality between two files the
test produces — which is how the "no legal artifact moves" claim in § The behaviour change is checked
rather than believed. Run for both formats.

### Fixture S — the structural cell, on each side of the row set

A `[1, 2]` cell in the **first** row and a `[1, 2]` cell in the **last** row of a multi-row set, each
arm asserting the refusal names the column and the row index. Both sides, because a check that stops at
the first row passes a fixture whose only offending row is the first — the decoy-sort-position trap in
its row-order form.

### Fixture N — the non-mapping row

A `.csv` and a `.parquet` write whose rows are `[{"v": 1.0}, "not a mapping"]`, asserting
`ArtifactError` · `E-ARTIFACT-UNWRITABLE` rather than `AttributeError`. The claim is the *type* of the
failure, so the assertion is on the exception class and code, and a control writes the same rows with the
string removed and asserts the file exists.

### Fixture A — the reserved attribute name, with a decoy on **each** side

Three arms — `unit`, `measurement`, `by` — each declared in a `data.units.attributes` list that **also**
holds a legal attribute sorting **before** it (`aaa_site`) and one sorting **after** it (`zzz_site`).
Grounds: the existing refusal reports the first offending name and stops, so a fixture with the reserved
name in one position cannot distinguish "reports the first offender" from "reports the first name" or
from an ordering that happens to agree. Two names only ever distinguish two answers.

Each arm asserts `E-UNITS-ATTR-COLUMN` **and** that the message names the offending attribute; a fourth
arm declares `paths` and asserts `E-UNITS-ATTR-RESERVED`, which is what proves the two codes are told
apart rather than one having swallowed the other. Run through `validate_config` (so the report path is
exercised) and through `resolve_units` (so the run path is).

### Fixture R — the resolver's structural attribute value

A registered resolver yielding `Unit(key=…, attributes={"tags": [1, 2], "site": "north"})`, asserting
`E-RESOLVER-YIELD` at `validate`. Its **positive control** is the same resolver yielding
`{"score": np.float64(1.5), "site": "north"}`, asserting the roster resolves and that
`roster[0].attributes["score"]` is **exactly `float`** — computed with `type(...) is float`, not
`isinstance`, because `np.float64` passes `isinstance`. Without that control the arm proves only that
something was refused.

### Fixture M — the `measurement` column, both branches

Arm 1: plain `io.record` with a `measurement` key → `E-STEP-KEY-COLLISION`. Arm 2: the same key through
`measurement=` → the same code, which already passes and is kept so the symmetry is what the test
asserts. Arm 3, the control that stops arms 1 and 2 from being a test of nothing: a plain record with a
column named `measurements` (plural) **writes**, asserted by reading the parquet and finding the column —
because a guard written as a prefix or a substring test would swallow it.

### Fixture D — `finalize`'s deduped columns

A `UnitList` built directly, one `Unit` carrying an attribute named `unit`, and the assertion on the
**column list** `finalize` builds rather than on the file — since the scoping measured that the file is
already correct, an assertion on the file would pass before and after and prove nothing. The claim is
about the list, so the assertion is about the list.

### Fixture C — the coercion branch, `str` against `bytes`

`np.str_('a')` coerces to exactly `str` with value `'a'`; `np.bytes_(b'a')` and plain `b'a'` both raise
`E-STEP-RETURN-TYPE`; a `str`-Enum member coerces to its **value** (`'red'`, asserted as the literal the
enum declares, which is why `str.__str__` and not `str()`); `np.array([1.0, 2.0])` and `np.array(1.0)`
both **still raise**, which is the positive control proving the `__len__` guard still does the job it
exists for.

### Fixture E — the empty and all-`None` row sets

An empty row list writes an empty table and raises nothing; a column whose every value is `None`
round-trips as `None` in every row. Both are the arms a coercion change is most likely to break silently,
and both are asserted on the decoded rows.

---

## The mutations, each with the assertion that catches it and two branches that can differ

**Checked in advance: for each, the mutated and unmutated code produce different observable results.**
The repo has shipped mutations that were what the code already did, whose branches could not differ, and
that were satisfied by neighbouring output.

| Mutation | Caught by | The two branches differ because |
|---|---|---|
| Delete the `coerce_scalars` call from `_encode_parquet` | Fixture W's `np.float64`-beside-`float` arm → raises `E-STEP-RETURN-TYPE` instead of round-tripping | measured today: that exact input raises. Unmutated it writes. This is also the mutation that pins Decision 8's docstring precondition |
| Delete it from `_encode_csv` only | Fixture S's `.csv` arm → the list cell writes `"[1, 2]"` and the refusal never comes | the two encoders are separate functions, so a mutation in one must be caught by a `.csv` assertion; the `.parquet` arm would stay green and that is why both formats are in every arm |
| Change `_check_column_types`' normalization from `float if actual in (int, float)` to `actual` | Fixture W's `int`-beside-`float` arm → raises instead of promoting | measured: promotion is the current behaviour and the mutant refuses it. Note the *reverse* mutation (folding more types together) is **not** prescribed: after coercion the surviving types are `{bool, float, str}` and folding any two changes no legal outcome — a mutation whose branches cannot differ, named here so nobody writes it |
| Remove the `str`-by-inheritance branch from `_coerce_one` | Fixture C's `np.str_` arm → raises | measured today: it raises. Unmutated it returns `'a'` |
| Move that branch **after** the `__len__` guard | the same arm → raises | the guard refuses `np.str_` first; placement is the whole of the fix, and a mutation one line off tests a different property |
| Replace `str.__str__(value)` with `str(value)` | Fixture C's `str`-Enum arm → the value becomes `'Color.RED'` | measured: the two constructors disagree on exactly this input, and agree on `np.str_` — which is why the enum arm exists at all |
| Drop `unit` (or `measurement`, or `by`) from `RESERVED_COLUMNS` | Fixture A's arm for that name → validates clean | each arm names one member, so a one-member deletion fails exactly one arm. A single arm covering all three would fail on any deletion and tell nobody which |
| Point the attribute check at `UNIT_FIELDS` instead of both constants | Fixture A's three arms fail, and the `paths` arm passes | the two constants are disjoint, so aiming at one is observable through the other |
| Merge the two codes — raise `E-UNITS-ATTR-RESERVED` for a reserved **column** | Fixture A's code assertions | the arms assert the codes separately; this is the mutation that makes Decision 4's mint load-bearing rather than decorative |
| Remove the attribute coercion from `resolve_units` | Fixture R's refusal arm → the structural value survives to `finalize`, and the **control** arm's `type(...) is float` assertion fails | two assertions, two directions: one proves the refusal, one proves the coercion. A single arm would leave the coercion half unpinned, which is Decision 6's actual payload |
| Delete the `except ContractError` wrapper in `io.write` | Fixture S's assertion that the message names the **artifact** | the writer's own message names the column and the row and never the artifact, so the two messages differ in a substring the assertion picks. Checked: no other part of the message contains the artifact name, so this is not an assertion neighbouring output satisfies |
| Widen that wrapper to enclose the whole body of `io.write` rather than the dispatch alone | a control asserting the `E-ARTIFACT-UNWRITABLE` message for an **unregistered suffix** is *not* prefixed with the artifact name | that raise sits in `io.write`'s own `else` branch, outside the dispatch, so a wrapper around the body reaches it and a wrapper around the dispatch does not — and it is an `ArtifactError`, so the `except` must be widened to the shared base for the mutation to be expressible at all, which is the point. **`io.path`'s `ArtifactExistsError` cannot serve here**: it is an `ArtifactError` sibling of `ContractError`, so an `except ContractError` never catches it, widened or not, and a control built on it passes in both branches — a mutation whose two branches cannot differ, named so nobody writes it |
| Replace the plain branch's `measurement` guard with a substring or prefix test | Fixture M's arm 3 → `measurements` refuses | measured: the plural column writes today, so the mutant and the original disagree on it |
| Delete `finalize`'s dedupe | Fixture D's column-list assertion | measured: the list holds `unit` twice today and the **file** does not change, so only a list assertion can tell them apart |
| Make the roster coercion refuse `np.float64` rather than coerce it | Fixture R's control arm | the control asserts a resolved roster, so refusal and coercion are different outcomes |

**Two mutations named as blind in advance**, so nobody reads their silence as confirmation. Emptying
`_check_column_types`' body leaves the suite green in the NumPy cases *after* Decision 5 lands, because
coercion has already removed the clash — that is Decision 8's point, not evidence the check is dead;
the bool/int and str/int pins are what keep it honest. And deleting Decision 10's dedupe changes no
file's bytes, which is why its assertion is on the list.

---

## Testability, and what the absent reader means

`units.parquet` has **no reader in core** — `report`, `study`, `diff`, `freeze` and `lineage` contain the
string `parquet` zero times, and no hash covers the table. Two consequences pull in opposite directions
and both are load-bearing.

**It makes H5a cheap.** No shipped command can break. That is measured, and it inverts the risk framing
the charter's own wording invites.

**It makes H5a's tests unusually easy to write wrong.** A corruption in `units.parquet` is invisible to
every test that goes through `run.yaml` — which is every test in `tests/test_cli.py` that checks a
metric. **A parquet assertion has to open the file.** Fixtures W, B, S, E and M all do.

**And the one documented consumer is user code**, which widens the exposure the `unit`-shadow filing
records: § Steps that need every condition shows a `summary` step calling
`io.read_condition(c, "step02_score", "units.parquet")`, which dispatches to the same `_decode_parquet`
these fixtures exercise. So the shadow does not only corrupt the published file — it corrupts what that
step reads. **The filing's severity bound is narrower than the exposure**, and amending it to say so is
part of task 12.

---

## The sibling that already got it right

Three places in this repo already solved a problem H5a meets, and each is copied rather than reinvented:

- **`coerce_scalars` is the one scalar walk.** Decision 5 adds a fourth call site to a function with
  three; it does not write a writer-specific type check. *One rule, all surfaces* is the argument, and
  the function is the implementation of it.
- **`apparatus.check_facts`' catch-and-re-code** is the precedent for `io.write` prefixing the artifact
  name onto a writer's `ContractError`, and it is copied **with its containment** — the `try` encloses
  the dispatch and nothing else. A recipe is its calls plus where they sit.
- **`_contained`** is the precedent for one guard called with a different base rather than duplicated,
  and it is why Decision 3 re-points the three attribute call sites at one pair of constants instead of
  adding a fourth spelling.

And one that is **H5b's**, named here so H5a does not spend it: `units.rule_for` / `coerce_for_rule` /
`apply_rule` already solve the collapse-across-repeats problem for `measurements`, including a
constant-column shortcut. H5b's task 12 reuses them. H5a needs none of it, because nothing here collapses
anything.

---

## Task decomposition — 12, up from the scoping's 9

| # | Task | Surface |
|---|---|---|
| 1 | § The per-unit tables states the cross-row unification rule (Decision 1) | `reference.md` |
| 2 | § The per-unit tables states `measurements.parquet`'s column set and that it carries no declared attribute, unlike its sibling (Decision 2) | `reference.md` |
| 3 | § Errors core raises: `E-STEP-RETURN-TYPE`'s row widened to **all three** emit sites — a value core can't record, a step's `run` returning a non-mapping, and a written `.csv`/`.parquet` whose rows disagree on a column's type; and `E-ARTIFACT-UNWRITABLE`'s row widened to its new non-mapping-row site (Decisions 5, 8) | `reference.md` § Errors |
| 4 | Mint `E-UNITS-ATTR-COLUMN` in § Validation, § Errors `validate` reports and § Steps and artifacts, **before any code**, distinguishing the metric namespace from the attribute namespace rather than re-arguing the reserved-metric sentence (Decision 4) | `reference.md`, three sections |
| 5 | Split the constant; refuse a reserved column name at all three attribute call sites; `validate` reports it (Decisions 3, 4) | `units.py`, `validate.py` |
| 6 | Coerce roster attribute values at `resolve_units`; widen `E-RESOLVER-YIELD` and its § Errors row (Decision 6) | `units.py`, `reference.md` |
| 7 | `io.record`'s plain branch refuses a `measurement` column (Decision 9) | `artifacts.py` |
| 8 | `finalize`'s `columns` deduped by name (Decision 10) | `artifacts.py` |
| 9 | Coerce inside `_encode_csv` and `_encode_parquet`; refuse a non-mapping row with `E-ARTIFACT-UNWRITABLE`; `io.write` prefixes the artifact name onto a writer's `ContractError`; `_check_column_types` takes a `where` and states its precondition; § Steps and artifacts states the writer's coercion and which formats it covers (Decisions 5, 8) | `artifacts.py`, `reference.md` |
| 10 | The `str`-by-inheritance branch in `_coerce_one`, with the two grounds named in the docstring (Decision 7) | `coercion.py` |
| 11 | Fixtures W, B, S, N, A, R, M, D, C, E and every mutation above | `tests/` |
| 12 | Filings: strike the dead half of the `units.parquet` type-unification entry and close its live half; close the `np.str_`/`np.bytes_` row; close the `unit`-shadow entry and **widen its severity bound** to the `read_condition` consumer; re-own the two residue rows to H5b by name; file what H5a leaves open | `spec-defects.md` |

**Why 12 and not the scoping's 9**, item by item, so the delta is auditable:

- **+1 for task 6.** Created by Decision 5 and not optional: without it, Decision 5 turns a today-weird
  run into a `ContractError` at `finalize`, after every execution is paid for. The scoping did not measure
  that attribute values are untyped.
- **+1 for task 7.** Measured by this pass, filed nowhere, and the same class as the guard three lines
  away.
- **+1 for splitting the scoping's task 9** into pins (11) and filings (12). Grounds: a
  documents-and-filings task is the one whose output no later batch reads, and this repo's record is that
  *a batch with no review is where the findings will be* — three of one gate's four Majors lived in
  exactly such a task. Separating them makes each reviewable.
- **−0 elsewhere.** The scoping's task 7 shrank (Decision 8 drops half of it) but grew by the
  non-mapping-row refusal and the `where` threading, so it stays one task.

**The order is 1–4, then 5–10, then 11, then 12.** Task 4 first among the code tasks' inputs because the
identifier must exist in the four documents' registry before anything raises it; tasks 5 and 6 before 9
because 9's coercion is what makes 6 necessary and shipping them out of order leaves a window where
`finalize` can raise late.

**H5a stays the smaller half.** H5b is 10 tasks over `stats.py` and `cli.py` with a document decision
needing an argument against `design-principles.md` at its head. H5a first stays the right order — and
the scoping's own inversion clause stands: the *worse* defect is H5b's, and if severity decides the order
rather than size, nothing in H5a blocks it. Nothing in this design depends on H5a shipping first.

---

## The consistency sweep this slice owes

The mechanical pass in full, plus these cross-document classes, because `reference.md` edits in five
sections cannot be checked by a link checker:

- **`E-UNITS-ATTR-COLUMN` appears in § Validation, § Errors `validate` reports, and § Steps and
  artifacts**, and nowhere claims a scope narrower than its code. One row per code, every site — the
  shape that was a whole-branch Major on H8a and H8b and shipped twice inside H8c.
- **The reserved-metric sentence in § Steps and artifacts** must still say the set `aggregate` may not
  return is one, because H5a does not add to it. Grep for "set of one" and check the surrounding
  paragraph distinguishes the two namespaces.
- **§ Templates' "whatever the step recorded plus every declared unit attribute"** must **not** be edited
  here. It is false of the code for a non-numeric recorded column and that is **H5b's task 10**; a
  half-edit in H5a would leave the document asserting a narrowing nobody argued.
- **§ Steps and artifacts' writer/reader table** gains the coercion statement, and the sentence *"Handing
  a writer anything else … raises `ArtifactError` · `E-ARTIFACT-UNWRITABLE`"* becomes true rather than
  aspirational — check both halves of that row read consistently afterwards.
- **`E-STEP-RETURN-TYPE`'s row** is the one to re-read after task 9 lands, because the row and the code
  are the same check from two ends and task 9 adds an end.
- **A sweep for any removed string over the four documents, `CLAUDE.md`, and the feasibility analysis** —
  naming the four documents rather than globbing `*.md`, since the development record is tracked. Filter
  the file list, never the output.
- **`experimental-designs.md` § Mistakes core prevents is a candidate for a new row** — an attribute
  silently replacing the unit key is exactly its subject matter — and it is a **decision for task 4**,
  not a gap in the document today. The scoping swept that section row by row and found nothing there falsified.

---

## What could not be measured, and what this design assumed

- **Whether any real project writes a structural cell to `.csv`/`.parquet` through `io.write`.** Decision
  5 refuses it, and the only evidence about frequency is that the feasibility analysis contains no
  row-shaped `io.write` at all. The cost of being wrong is a refusal on a use nobody has demonstrated,
  with `.json` as the documented route.
- **Whether `csv.DictWriter`'s `str()` and coercion agree for every scalar, or only for the ones probed.**
  Byte identity was measured for `float`/`int`/`bool`/`str` and their NumPy spellings, which is the set
  `_SCALARS` closes over — but it is a probe over four types, not a proof over the type lattice. Task 11's
  Fixture B is where that becomes a pin.
- **A `measurements.parquet` written by a real run.** Decision 2 states its column set from the code and
  from direct `StepIO` probes; no scratchpad config here declared `data.units.measurements` either, which
  is the scoping's own gap carried forward rather than closed. Task 2's fixture should be the first one.
- **Whether a plugin writer raising `ContractError` benefits from `io.write`'s prefix or is confused by
  it.** No plugin writer exists to try. Assumed beneficial, because the prefix names the artifact and
  never rewords the message.
- **Whether `E-UNITS-ATTR-COLUMN` fires at `run` for a *table* source as well as a resolver.**
  `resolve_units` runs at both surfaces so it should, but the dual-surface behaviour of
  `E-UNITS-ATTR-RESERVED` is documented nowhere and was not measured here. Task 5's implementer should
  measure it and state it, on `E-UNITS-ATTR-MISSING`'s row as the precedent for how a dual-surface raise
  is written down.

---

## Ruling from the controller, 2026-08-21 — the behaviour change is approved, and why it is not the one I refused before

**Saying loudly that H5a is a behaviour change to `run`, against the scoping's own split ground, was the
deliverable.** A design that had quietly inherited *"only H5b changes behaviour"* would have shipped four
stoppages under a sentence saying there were none.

**Approved.** The distinction the design draws is the right one and I am adopting it as the test:
**H5a refuses corrupting input; H5b changes what an existing key may contain.** Those are different acts.

**Measured, at `38df123`, because the direction matters more than the label:** a `bytes` cell written
through `.csv` comes back as **the string `"b'x'"`**, and a `[1, 2]` cell as **`'[1, 2]'`** — while
`.parquet` round-trips both intact. So **the same documented promise** — § Steps and artifacts' *"what a
writer takes is what its reader gives back"* — **is true for one format and false for the other, on one
table row.** Refusing that cell does not take a working behaviour away; it **converts silent corruption
into a loud refusal**, which is the same direction this project ruled for the silent unit drop: *no
diagnostic is the only one of the options that cannot be right.*

**Contrast with what I refused on H7d Part B.** There, `run_status` would have been widened so
`max_failed_fraction`'s truncation reported `partial` instead of `completed` — **changing what an existing
key reports for a run that was already correct**, and doing it in a slice about something else, while a
shipped test's docstring argued for the current answer. Nothing here resembles that: no `run.yaml` key's
value moves, and **a legal run's artifacts are byte-identical** (measured).

**Four requirements, and they are the price of the approval.**

1. **Each of the four stoppages is named in the documents, with what ran before and what happens now.**
   A user whose run stops must be able to find the sentence that says why. "Four things that run today
   stop" is a design's phrasing, not a document's.
2. **Byte identity for a legal run is PINNED, not measured once.** The design probed four NumPy spellings
   across both formats; Fixture B must make it a pin, because *a correct fix shipped unpinned* has
   happened seven times here.
3. **Decision 6 is not optional and the plan must treat it as load-bearing.** Coercing roster attribute
   values at `resolve_units` exists because Decision 5 alone would turn a **completed** run into a
   `ContractError` inside `finalize` — **after every execution is paid for.** That is this repo's named
   habit (*every execution paid for, the record lost*), and it is the one way this slice could do real
   damage. **Pin the ordering, not just the coercion.**
4. **The retiring spurious refusal is stated as a retirement**, not left implicit — a refusal that stops
   firing is as observable as one that starts.

**On the `by` question I asked about: the answer is better than the question.** The refusal removes one
**producer** of a `by` column and not the **possibility**, because a step *recording* `by` stays legal —
so `report`'s structural test remains **the only thing that can tell a stratum from a metric**, and the
refusal is **explicitly not licence to reintroduce a name test anywhere.** That reasoning must survive
into the code comments, because the sixth instance of *a name standing in for a structural fact* on this
project was exactly this column.

**And one filed gap I am endorsing rather than folding in:** `.yaml` raising a bare `RepresenterError`
and `.json`/`.jsonl` a bare `TypeError` for `np.int64`/`np.bool_` is the traceback-instead-of-diagnostic
class `coercion.py` exists to prevent, and closing it needs a **recursive** walk. Filing it
unassigned-with-a-reason is correct; **widening this slice to reach it would be the mistake.**

**Cost if this ruling is wrong:** a project whose steps write structural or `bytes` cells through
`io.write` sees a refusal where it previously saw a silently mangled artifact — and finds out at write
time rather than at analysis time. I would rather be wrong in that direction.
