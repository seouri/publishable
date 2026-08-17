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

