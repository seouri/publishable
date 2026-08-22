## Task 2: § Templates states what the collapsed table carries

**Surface: documents.** Design Decision 10. **The sentence is not narrowed — it is made true for the
first time**, so no argument against `design-principles.md` is owed. `H5-SCOPING` task 10's premise
(*"narrowing it needs an argument"*) was wrong, and the design says so.

**Files:** `docs/reference.md`

**The section is `Templates: where parameters are defined`, anchor
`#templates-where-parameters-are-defined` — NOT the later `## Templates` section, which is the
`my_assay` parameter table.** Two headings in this file answer to "§ Templates" and the design cites the
first. **Grep for the sentence rather than for the heading:** `grep -n 'Columns are whatever the step'
docs/reference.md` returns exactly one line, and that paragraph is the target (§ Corrections 8).

- [ ] **Step 1.** The paragraph already reads *"Columns are whatever the step recorded plus every
      declared unit attribute"* and already says of a declared attribute *"A declared attribute is
      carried through **unchanged** rather than averaged … It is a column here and nothing else — never
      a metric."* **Add the recorded-column half beside it, in the same shape**, stating three things:
      a recorded column that is not a number is carried too; across a unit's repeats it collapses to its
      value when every repeat agreed and to `None` when they did not, because a non-numeric column has
      no average and `data.units.measurements.collapse` governs measurements rather than repeats; and it
      is a column and never a metric, for the reason § Statistical reporting gives.
      **Do not restate the four-operation contract, and do not touch it.**

- [ ] **Step 2.** Link the collapse sentence to [§ What isn't a repeat](../../reference.md#what-isnt-a-repeat), whose
      *"Attributes constant within a key collapse to that value with no rule needed"* is the rule this
      reuses, and to § Warnings core reports for the disclosure. **Verify both anchors resolve** by
      grepping the headings; a `#anchor` that does not exist is a mechanical-pass failure.

- [ ] **Step 3: the mechanical pass on this edit only.** Every relative link and `#anchor` resolves; no
      trailing whitespace, tab or invisible unicode; no table row's column count changed; `×` not `x`.
      **Skip fenced blocks.**

- [ ] **Step 4: the cross-document pass on this edit only.** Two classes can bite here. **Config
      completeness:** this edit names no new config field, so nothing is owed to § The one config file —
      **check that claim by grepping your own diff for a backticked `data.` or `statistics.` path and
      confirming each already appears there.** **Declared vs. derived:** the collapse rule describes a
      derived value; grep the four documents by name for any passage showing a repeat-level collapse
      rule as a *settable* input, and report what you grepped.

- [ ] **Step 5.** No mutation: a document has no behaviour. **Named blind in advance.** Its replacement
      is task 4's Fixture A and task 5's Fixtures C, D and L, which pin the behaviour this sentence
      describes, plus the B1 review's document-against-future-code read.

- [ ] **Step 6: run** the four commands (no test delta) and **commit**: `H5b task 2: § Templates states
      that a non-numeric recorded column is carried, and how it collapses across repeats`.

---

