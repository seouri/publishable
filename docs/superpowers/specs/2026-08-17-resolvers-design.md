# H7b Part B — resolvers, and retiring `E-DATA-RESOLVER-UNSUPPORTED` — design

**Goal:** a plugin's resolver builds the unit roster. `data.units.from: {resolver: name}` runs, the
unit checks that need a roster become real, and the refusal that has stood since H1 is retired.

**What it delivers, and this is the first non-zero payoff in the project's history.** **Three of the
nine experiments in the feasibility analysis have no remaining core-side blocker** — E1, E2 and E5.
Not nine: E3, E4 and E6 stay blocked on `io.reuse_from`, which is unbuilt and **unowned by any H7
sub-slice**, and C1–C3 on `E-DATA-WEIGHT-CONTRAST`, which is H4b's. Two qualifications belong beside
the number rather than in a footnote: the plugin must exist (task 21 scaffolds one; a hand-written
package already works), and a declared probe is neither executed nor recorded.

**What it is not.** Not `io.reuse_from`. Not the apparatus — H7d. Not weighted contrasts — H4b.

---

## The measurement this rests on

`docs/superpowers/H7b-PartB-SCOPING.md`, taken 2026-08-17 against `main` at `53090e9`, **after Part A
merged**. It re-measures `H7b-SCOPING-2.md` § 9 Part B, taken one day and one slice earlier, whose
**nine** tasks become **thirteen** and **five of whose conclusions did not survive** — two of them
load-bearing enough to change what gets built.

---

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | Does `validate` import a plugin? | **Yes, when it runs a resolver — and the invariant Part A built is narrower than the sentence claiming it** | § Where units come from is explicit and reasoned: a resolver *"runs at `validate` and `dry-run`, not only at `run`"*, because every unit check is a question about the resolved table, and deferring them costs four hours into a run. Executing a resolver imports it. What Part A actually built and tested is that **a NAME resolves from package metadata without importing** — so a config naming an uninstalled or broken plugin gets a clean diagnostic. Both are true; the sentence saying `validate` never imports a plugin overstates the second into the first, and it is the sentence that changes |
| 2 | The credential-leak fix | **Both halves, not the one both prior documents prescribed** | They say *"move the credential computation, not wrap the call."* Verified: `redact` has exactly two call sites — `Collector.render` and `runner.execute_plan` — and `main`'s handler is **neither**; it prints `{exc}` raw. Moving the computation alone produces values nothing applies. So: set `c.credentials` before the roster resolves **and** route the resolver's raise through `command_run`'s existing collector, which is a redacting surface |
| 3 | A **non**-`PublishableError` from a resolver | **Contained, at both `validate` and `run`** | `_check_units` guards only `except ContractError`, so a plugin resolver raising `KeyError` breaks the *"`validate` never raises"* contract. And the scoping ran a fourth probe neither prior document did: at `run` such a raise **escapes `main` entirely as a traceback with the credential in it.** A traceback is the one output no redacting surface sees |
| 4 | `check_registration` at `validate`, or only at `run`? | **At `validate`** | Decision 1 settles it: `validate` already loads the resolver to run it, so the object is in hand and the decorator-vs-key disagreement is knowable there. Deferring it to `run` would report at `run` a fault `validate` had the evidence for — the shape `CLAUDE.md` calls a check `validate` cannot see |
| 5 | `hash_index`, a documented rule with no code | **Closed here, for the table case as well as the resolver's** | `build_manifest`'s `index_names` has zero callers in `src/` and zero mentions in `tests/`; probed, every `sha256` comes back `None`. It is **broken for the table case too**, so task 31's resolver half cannot be built on it without closing it. It is also unfiled — a documented rule with no code and no filing is the exact pair `CLAUDE.md` says to grep for before building on a row |
| 6 | `resolve_units` needs `cfg`, which it never receives | **A defaulted keyword** | 60 call sites in `tests/` alone. A required parameter is a 60-site change with no behavioural content; a defaulted keyword threads the one caller that has a `cfg` and leaves the rest true |
| 7 | The payoff figure | **Three of nine, with both qualifications attached** | The first non-zero count this project has produced, and precisely the moment to state it carefully. `CLAUDE.md`'s feasibility procedure step 10 exists because a refusal-count has repeatedly been read as an executable-count; a *newly correct* count read without its qualifications would be the same error with the sign flipped |

---

## What the re-scoping overturned

**The credential-leak remedy was wrong in both prior documents**, and the error is decision 2's.

**"H7d blocks all nine" is false.** `apparatus_probe` has exactly one reader in `src/` —
`validate._check_probe`, a metadata name check. Nothing reads it at run. It is a **false-record**
problem (`cli.py` writes `"apparatus": None` unconditionally), not an execution blocker. That is
why the count is three rather than zero.

**"A test that goes red when the two lines swap" is a non-discriminating mutation.** Part A's own
comment says redaction happens at *render*, not construction, so swapping the two lines changes
nothing. The mutation that can fail resolves the roster before the **template**.

**Part A already wrote several of Part B's documentation tasks in advance** — three § Errors rows
exist carrying `Not yet emitted:` markers, and `E-RESOLVER-SWEPT-PARAM` settles a reuse-or-mint
question the prior document left open. Two prior tasks shrink accordingly.

---

## The traps

| Trap | The rule |
|---|---|
| The no-import invariant dying silently | It is pinned by two tests at `scan_group` and `get_template`, **neither of which Part B touches.** So a resolver that imports at the wrong moment leaves both green. Decision 1 narrows the claim; the tests must be extended to pin the narrowed one, or the guarantee survives only as prose |
| A refusal's message describing the build | Part A had to rewrite `E-DATA-RESOLVER-UNSUPPORTED`'s message because it claimed the registry was unimplemented — which Part A implemented. **This slice retires that code entirely**, so every sentence describing what cannot be done must be re-read, not just the row |
| Reading a mutation's silence as confirmation | Twice in Part A a task emptied a payload, saw the suite stay green, and concluded it was unreachable — while a discriminating test existed both times. A mutation that changes nothing is evidence about the **tests** |
| Inferring unreachability from a refusal | **`validate` collects rather than aborting.** Three readers across two slices got this wrong |
| A grep for one spelling | It shipped a credential leak two slices ago. Enumerate by reading, then confirm by grep |
| The `Status` column left behind | Retiring the wholesale refusal moves rows in § CLI reference and § The one config file. Part A shipped a Critical where a row still said `not yet built` about something exported |

---

## Task decomposition — 13

From the re-scoping's § 10, in its order.

21. `plugin new` / `plugin_scaffold.py` — five entry-point groups, five decorators.
22. **Decision 1 settled**, and the three `reference.md` sentences and two `plugins.py` claims it moves.
23. The read-only resolver `io` — `read_input` and nothing else.
24. Resolver name resolution and load, with **decision 4**'s `check_registration` siting.
25. **Dispatch in `resolve_units`**, `cfg` threaded per decision 6; yield order preserved.
26. **Retire `E-DATA-RESOLVER-UNSUPPORTED` and the `_check_units` skip in one change.**
27. Attribute projection; `E-UNITS-ATTR-MISSING`'s message generalized past a table.
28. `E-RESOLVER-MEASUREMENT-FIELD` emitted, marker struck.
29. Condition-independence — `SweptAway`-substituted `cfg`; `E-RESOLVER-SWEPT-PARAM` emitted.
30. `provenance.plugin_versions`; the four dated *no production caller* notes retired.
31. **Decision 5** — `hash_index`, table case and resolver case.
32. **Decisions 2 and 3** — the credential leak, both halves, and the non-`PublishableError` containment.
33. The owned prose sweep and the reader-facing half, including **decision 7**'s dated count.

**Sequencing.** 22 before 24 — the decision decides whether 24 exists in the form written. 23 before
25; 24 before 25, which needs the object. 25 before 26, 27, 28 and 29. **26 is last among the
refusal-retiring tasks**, so the wholesale refusal stays alive as long as possible and every earlier
test asserts alongside it. 32 may not be deferred past 26: the leak becomes reachable the moment a
resolver runs.

**If it runs long, drop 21** — `plugin new` is the only task nothing else depends on, and a
hand-written package already works.

---

## Out of scope, with the route

`io.reuse_from` — **unbuilt and unowned by any H7 sub-slice**, and the reason E3, E4 and E6 stay
blocked. This slice files it with an owner rather than closing it. The apparatus and its probe —
**H7d**, which also owns the false `"apparatus": None` record. Weighted contrasts — **H4b**, and the
reason C1–C3 stay blocked.

---

## Corrections from planning — appended 2026-08-17, replacing nothing above but qualifying it

The plan author found nine disagreements with this spec or the scoping. Four change what gets built.

1. **Decision 2's "route through `command_run`'s existing collector" cannot be taken literally.**
   `command_run` already does `if c.findings: print(c.render())` before the roster resolves, so
   appending to `c` and rendering again would re-print every warning and inflate the counts line. The
   file's own convention for a post-validate finding is a **fresh `Collector()` with `.credentials`
   assigned** — `dirty_c`, `warn_c` and `drift_c` all do exactly that. The ruling stands; its
   mechanism is a fresh collector, and the task says why.
2. **Three codes this spec does not name are minted**, each with an emit site and a test:
   `E-RESOLVER-YIELD` (a resolver yielding a non-`Unit`, which would otherwise escape `validate` as an
   `AttributeError`), `E-RESOLVER-RAISED` (decision 3's containment needs an identifier), and
   `E-RUN-RESOLVER-UNCONFIGURED` (decision 6's named price for the defaulted `cfg`, joining an existing
   § Errors row rather than taking one of its own).
3. **`hash_index` is broken for the *glob* case too**, not only the table and resolver cases decision 5
   names — `_from_glob` sets `paths=(rel,)` and `_from_table` sets `paths=()`. Task 31 writes
   `index_names` as one expression covering every source, so none is left silently at `sha256: None`.
4. **`E-RESOLVER-MEASUREMENT-FIELD` is emitted ungated**, where the obvious move would inherit the
   table arm's `technical_n["max"] > 1` gate. That gate would make the code narrower than its own
   normative row: a table's `by` may name a step-invented identity, while a resolver has no columns,
   so § Where units come from makes yielding it an obligation. The difference is deliberate and stated
   in the task.

**Also recorded, not changing the build:** `E-UNITS-SOURCE-MISSING`'s row becomes false at task 25 and
appears in neither scoping section, so task 25 owns it; `_wide_swept_paths` must move to `sweep.py`
because `validate` needs it and `validate → cli` is a cycle; the filed `E-PLUGIN-COLLISION` →
`E-PLUGIN-LOAD` re-code is decided in task 24 by letting it stand, since the alternative would let any
coded `ContractError` from a plugin's top level escape containment; and **tasks 25, 27, 28 and 29
cannot test through `validate_config` at their own commits**, because the resolver skip is only deleted
at 26 — each tests its own function directly and task 33 re-asserts end to end.

**Task count is 13.**
