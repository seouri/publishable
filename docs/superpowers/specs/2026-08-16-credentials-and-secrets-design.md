# H7c — credentials and secrets — design

**Goal:** a template declares the environment variables it needs, `validate` reports a missing
one before anything executes, and a credential value never reaches a record. `Param(requires_env=)`
becomes constructible, `BaseTemplate.required_env` gets its first reader, and `secrets.py` loads
`.env`.

**What it delivers, stated honestly.** **Zero refusals retired and zero experiments newly
executing.** This slice retires nothing, because there is no refusal here to retire — the two
§ Validation rows have existed since H1 with nothing behind them, and the family has no
`-UNSUPPORTED` member. What it delivers is the **prerequisite for H7b's payoff**: the feasibility
analysis's `llm_screen` template declares `Param(..., requires_env=...)`, and `Param.__init__`
rejects that keyword today, so the plugin H7b's registry would resolve **cannot be written** until
this lands. It also closes a defect `CLAUDE.md` names by hand.

**What it is not.** Not entry points, not the four registries, not resolvers, not `plugin new` —
all H7b. Not the probe's credential (H7d). Not the README `credentials` region, which is routed to
a filing rather than built; see decision 7.

---

## The measurement this rests on

`docs/superpowers/H7c-SCOPING.md`, taken 2026-08-16 against `main` at `d86290c`, alongside its
companion `H7b-SCOPING.md` of the same date and pin. The charter's **7** becomes **14**, and two of
its seven items move — one shrinks to nothing, one is routed out.

The charter also called this slice order-independent. That is the claim the companion scoping
falsified, and it is why this slice is being built first rather than last.

---

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | One code or two, for the template-level set and the swept-value set | **Two** | They are one mechanism with two collectors, but `reference.md` § Errors carries one row per code **because a row carries one message**. `E-TEMPLATE-UNKNOWN`'s two-surfaces-one-row precedent turns on its two surfaces sharing a message; these two cannot — one names a template, the other must name a parameter, a value, and the condition that selected it. One row enumerating both is exactly the shape the one-row-per-code rule exists to avoid |
| 2 | Whether the `requires_env` totality check mints a code | **No — it is `E-TEMPLATE-LOAD`, and not even a § Errors row is owed** | `reference.md` says a bad mapping is rejected *"when the template loads"* — the identical phrasing it uses for `default=None` without `nullable=True`, which ships as a `ValueError` from `Param.__init__` surfacing as `E-TEMPLATE-LOAD`, whose rows already enumerate *"raises while importing"*. The scoping probed this end to end rather than reasoning from the phrasing. The charter's "New identifier" was wrong |
| 3 | What happens to a credential value that reaches a failing step's exception text | **Redact by exact value at the two record-writing sites, and say a redaction happened** | This is the one surface where a value can enter a record. Scrubbing the whole text destroys the debugging the record exists for; leaving it violates *"Secrets are the one thing never captured."* Core **knows the exact values it read**, so it can answer the direct question — which is the whole point of decision 4 |
| 4 | How a leak is detected | **By exact value, never by pattern** | `CLAUDE.md` § Answering a question with a proxy, twice-burned in H7a. A name ending `_KEY`, or a high-entropy string, fails open on a credential named `instrument_pw` and fails closed on a config value that happens to look random. The direct question is *is this the value core read out of the environment* |
| 4a | The limit of decision 4, stated rather than discovered | **Core redacts only values it read for a declared variable. A step that reads the environment itself is outside what core can know, and the documents must say so** | Decision 4's strength is that core answers from knowledge rather than from a guess — and the same property bounds it. `io` hands a step no credential, so a step reaching `os.environ` directly holds a value core never saw and cannot match. Promising more than that would be a guarantee the code does not provide, in the one document whose job is to prevent them |
| 5 | Where `.env` is loaded | **Two sites — `validate`, and before any step runs — and the single-site sentence is reconciled** | Three § Validation rows are unbuildable unless `validate` reads the environment. This is **not** a breach of `validate`'s promise: that promise is *"creates nothing and reaches nothing off the machine"*, and `.env` is on-machine. Say that precisely rather than flagging a breach that is not one |
| 6 | The fixture for the union over resolved conditions | **Three choices, a sweep selecting two, and a third whose variable is deliberately unset** | The union is the entire reason `requires_env` exists rather than a static `required_env`, and **the evidence base contains no fixture for it** — all nine feasibility configs resolve a single provider. Two choices cannot separate the three candidate readings; the scoping counted them first and sized the fixture to the count |
| 7 | The README `credentials` region | **Filed, not built** | The scoping found the region does not exist in a freshly scaffolded README, so there is nothing for `generate experiment` to merge into. This is the one point where the two scopings disagree — the companion routes the region wholesale to `docs`, and it is right about the merge and wrong about the region, which is `new`'s to emit. Building the merge against an absent region is the charter item to refuse |
| 8 | What this slice exports | **Nothing** | `requires_env` is a `Param` keyword and `required_env` a class attribute, so the one-import-root list does not move. A slice that adds no name should say so, or the next reader reads the absence as an omission |

---

## What the scoping overturned

**The charter is three-quarters refusals, and the honouring is what has no test.** A missing key, an
unknown key, an unset variable — all refusals. `CLAUDE.md` records this exact shape from H3c:
*"`validate` refused bad `block_size` values while nothing checked the draw used a good one."* Here
the honouring is that a correctly declared `requires_env` over a satisfied environment **validates
clean**, and that the union is computed over the right condition set. Without it, ignoring
`requires_env` entirely passes the suite.

**The no-leak invariant is held by absence, not by a filter.** Core reads no environment variable
at all today, so the charter's leak test is `CLAUDE.md`'s *control asserting only absences* — it
passes identically if nothing ran. Decision 3 gives it something that must report.

**Closing `required_env` is a defect closure, and it falsifies a `CLAUDE.md` example.** That file
names the attribute *by hand* as its canonical instance of *"an unbuilt reader of a **shipped**
surface"*. This slice is the first reader, so the example stops being true and the row needs a
surviving one. `field_convention`, `apparatus_probe` and `apparatus_facts` remain — and H7b takes
`apparatus_probe`, so pick from the other two.

---

## The traps

| Trap | The rule |
|---|---|
| A fixture with too few providers | Two choices cannot separate *union over resolved conditions* from *union over all choices* from *the requirement of the written value* — with a two-value `choices` the sweep selects both and all three readings agree. **Count the readings first, then size the fixture.** Decision 6 is that count |
| An absence proved by an environment that was empty anyway | `os.environ` is inherited from the test runner. "The variable is unset, so `validate` reports" passes on a machine where nothing was ever set, **and would pass if the check did not exist** — while the positive test fails mysteriously on a developer machine that happens to have it. Both directions need `monkeypatch.delenv`/`setenv`, and the negative needs a control that sets the variable and expects silence |
| A monkeypatch aimed at a name the load path no longer calls | The two load sites are **in different modules**, so a patch on one while asserting the other's behaviour is not obviously wrong on inspection |
| A `Param` fault that is not a `validate` finding | Decision 2's early return collapses the whole report to one error, so a test asserting a finding **list** rather than membership is pinned to the collapse. And for an *installed* plugin the same fault is not a finding at all until H7b lands — a test written against an installed distribution measures H7b, not H7c |
| Reading the `-UNSUPPORTED` family in | This slice retires **no** refusal and must mint no `-UNSUPPORTED` on the way in. The family has no refusal at all, only missing checks |

---

## Task decomposition — 14

From the scoping's § 8, in its order. **Part A (1–6) declares, renders and documents, and reads
nothing; Part B (7–11) reads the environment; Part C (12–14) proves it and sweeps.**

1. The § Validation ↔ § Errors identifiers, settling decision 1 with grounds.
2. § Errors' load-refusal prose and its count phrase — **shared with H7b task 2**; this slice owns it.
3. **`Param(requires_env=)` — the constructor argument.** The H7b prerequisite.
4. `Param.comment()` renders the per-value requirement against every choice.
5. § Templates' constraint table — `requires_env` stays **out** of the closed vocabulary.
6. § Package layout and § The importable surface; decision 8 written down.
7. `secrets.py` and the `python-dotenv` dependency.
8. The two load sites, and the reconciled sentence.
9. **`required_env` checked at `validate`** — the first reader; `CLAUDE.md`'s example replaced.
10. **`requires_env` union over the conditions the sweep resolves.**
11. The expansion modes the union must cover — `baseline`, `paired`, `groups`, `ablate.remove`.
12. **The no-leak test, with a mutation that can fail**, and decision 3's redaction.
13. The owned prose sweep — **named files**, since the development record is tracked.
14. `spec-defects.md` filings, including decision 7's routing correction.

**Sequencing.** 1 before everything. **Task 3 is the H7b prerequisite and nothing else in this
slice gates it** — if the combined work must be interrupted, 3 is the task that must have landed.
The seam, if this slice itself runs long, is **6/7**: Part A changes no behaviour beyond `Param`'s
constructor and its rendered comment, needs no new dependency, and already contains task 3.

---

## Out of scope, with the route

Entry points, the four registries, resolvers, `plugin new` — **H7b**, which needs none of this
slice except task 3. The apparatus probe and its credential — **H7d**. `io.reuse_from` — unbuilt
and unowned by any H7 sub-slice, which is a gap this slice files rather than closes. The README
`credentials` region and its `cp .env.example .env` line — **filed** under decision 7, owned by
whichever slice next edits `new`'s README emission.

---

## Corrections from planning — appended 2026-08-16, replacing nothing above but qualifying it

The plan author found four disagreements with this spec or the scoping, and a fifth surfaced when
the controller checked the first. All five are carried in the plan; the two that change what gets
built are recorded here.

1. **Decision 3's "the two record-writing sites" is wrong in both directions, and the correction
   improves it.** The plan measured **one** construction site and proposed redacting there; the
   controller then measured **five** — `runner.py`'s step-error text, three
   `W-STATS-AGGREGATE-FAILED` warnings in `cli.py` carrying a template's exception, and
   `validate.py`'s entrypoint-import failure. Verified that `run_record.py` mentions diagnostics
   nowhere, so the three warnings do **not** reach `run.yaml` — but task 12's leak sweep covers
   **stdout and stderr**, so they are in scope by this slice's own definition of a leak.
   **Ruling: redact at the two serialization boundaries, not at any construction site.**
   `Diagnostic.render()` is the chokepoint every diagnostic's text passes through, and the
   step-error path is the other. Two edits cover all five constructions and cannot diverge as a
   sixth is added; five edits at construction are five places for the next one to be forgotten.
   This is the same argument that put `holdout_values_fault` behind one authority in H3d.
2. **`draft` and `resume` are in `cli.NOT_BUILT_COMMANDS`.** The scoping's task 8 names them as
   load sites. Only `command_run` is buildable, so one site is built, the document's sentence is
   written as specification, and the inheritance is recorded — the same treatment the scoping
   itself gave `dry-run`. No stub.
3. **`command_run` binds no template before `execute_plan`**, and its only `get_template` call
   sits after it, without `repo_root` — which resolves no project-local template. Left unfixed,
   the redaction would silently no-op for exactly the templates this slice serves while every
   `GenericTemplate` fixture stayed green. The plan resolves the template before `execute_plan`
   and pins the defect with a mutation that drops `repo_root`.
4. **Three prescribed mutations could not discriminate and were replaced**, with the reasons
   written into the plan: the scoping's own leak mutation was a *fixture* change rather than a
   mutation; a `condition.selectors` deletion was blind because a group axis's name is not a
   `parameter_spec` path; and a redact-by-pattern mutation was blind against a `sk-`-prefixed
   sentinel.
5. **`field_convention` is the survivor for `CLAUDE.md`'s example** — verified unread, where
   `apparatus_probe` is H7b's and `apparatus_facts` H7d's.

**Task count is unchanged at 14.** Decision 3's correction changes where task 12 edits, not how
many tasks there are.

**Correction to correction 1, same day, before any of it was built:** it names the first boundary
`Diagnostic.render()`. The method is `Collector.render()` — `Diagnostic` is a frozen four-field
dataclass with no methods, and `Collector` holds the findings and renders them. The controller
misjoined a class list and a method line read from the same file in two separate greps; the plan
author read `diagnostics.py` and caught it. The ruling is unchanged and is in fact strengthened:
redacting per-`Diagnostic` would need the values at construction, which is the thing this ruling
exists to avoid.

**Correction to correction 4, appended 2026-08-16 after task 10 shipped:** it recorded the
`condition.selectors` deletion as a **blind** mutation, on the reasoning that `wanted` is keyed on
`parameter_spec` paths and a group axis's name is not one. Task 10's implementer reached the same
conclusion independently and recorded the skip as structurally unpinnable, because
`E-SWEEP-PATH-DUPLICATE` refuses a config naming a group axis with a declared parameter's path.

**Both were wrong, and task 10's reviewer proved it by building the fixture.** `validate` **collects
rather than aborting**, so the duplicate-path refusal does not stop the check from running: with
`groups: [{by: llm.provider, levels: [ollama]}]`, deleting the skip yields an extra
`E-CRED-PARAM-MISSING` for `ollama`. The mutation is not blind, the skip is now pinned, and the
lesson is narrower than "check your mutations" — **a refusal elsewhere in `validate` does not make a
later code path unreachable**, because nothing in `validate` short-circuits on a finding.

**Correction to correction 1, appended 2026-08-16 after task 12's review:** it says **five**
exception-text construction sites. There are **six**. The controller measured them with
`grep -rn 'type(exc).__name__' src/publishable/*.py` — **which is itself a proxy**, of exactly the
kind decision 4 forbids elsewhere in this document. `cli.py`'s drift reporter formats a bare
`{exc}` and prints straight to stderr, so it matches no such grep, and task 12's reviewer reproduced
a declared credential reaching stderr verbatim through it.

**The two-boundary ruling is not weakened by this — it is vindicated by it.** Had redaction been
placed at construction sites, the sixth would simply have been missed and nothing would have caught
it; the reviewer found it precisely because the document now claims a *complete* boundary set, which
is a claim strong enough to falsify. The repair is to bring the sixth site inside a boundary, not to
enumerate a sixth edit.

**The lesson is the one this slice keeps relearning.** A grep for one *spelling* of a thing answers
"where does this spelling appear", not "where does this happen" — the same substitution that made a
pattern-based leak check unacceptable in decision 4, applied by the author of decision 4 while
measuring for it.
