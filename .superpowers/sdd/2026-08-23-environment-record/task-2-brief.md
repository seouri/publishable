## Task 2: Ruling O written into § The two files — `hardware: {cpu_count: 32}`, and where a GPU goes instead

> **Bindings that reach this task:** **Ruling O**, restated in full below. The documents lead, so this
> task lands before the code that implements it.

**RULING O, restated here in full:** `hardware` carries **`cpu_count` and NOT `gpu`**. Grounds, from
`CLAUDE.md` § Invariants' core-vs-plugin test — *would it be identical for a wet-lab assay, a
simulation sweep, and an LLM benchmark?* — a CPU count is `os.cpu_count()`, stdlib, answerable
everywhere; a GPU is not, and core cannot probe one without a dependency or a subprocess. **The
apparatus is the existing route for anything core cannot observe**, and H7d Parts A and B built it for
exactly this. **§ The two files shows `hardware: {gpu: "1x A100 80GB", cpu_count: 32}`, and that
example must change.** This task's ruling is **which way**: the `gpu` **fact leaves the example**, and a
sentence naming the apparatus as its route replaces it.

**Why not the other way — measured, so the reader can check it.** Sourcing `gpu` from the apparatus
*inside* that example would give the worked example a probe. § The apparatus core can only observe says
*"An experiment whose measurements never leave the machine declares nothing and records `apparatus:
null` — **the worked example throughout this document is one**"*, and the same `run.yaml` example
carries `apparatus: null   # no probe declared`. Changing that is a change to the shared worked example
`CLAUDE.md` § The worked example governs, and Ruling O does not authorize it.

**Cost if wrong, and it goes in the document rather than only here.** *A reader of a bundle cannot tell
what hardware produced a number unless the producer declared an apparatus probe.* That is the trade
this project makes everywhere else, and **it must be stated beside the change rather than hidden**.

**Steps**

- [ ] In `docs/reference.md` § The two files, change the one line
      `    hardware: {gpu: "1x A100 80GB", cpu_count: 32}` to `    hardware: {cpu_count: 32}`.
      **Nothing else in that fenced block moves** — `os`, `hostname`, `manager`, `python_version`,
      `uv_lock` and `uv_lock_hash` keep the values and the comments they already carry, and
      `apparatus: null` stays.
- [ ] Add, in the prose that follows the block, **one** short passage: that `hardware` carries the CPU
      count core can read on any machine and nothing else; that a GPU, an instrument revision or a
      hosted model deployment is an **apparatus fact** and **link** to § The apparatus core can only
      observe rather than restating what that section says; and the cost, stated — a reader cannot tell
      what hardware produced a number unless the producer declared a probe.
- [ ] **Sweep for `gpu` and for `A100` over the four documents named individually** — `README.md`,
      `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md` — and over
      `CLAUDE.md`. Filter the **file list**, never the output. **Prove the sweep can fail** with a
      control string known to be present in each file. Report every hit and what you did about it.
      This plan measured: `gpu`/`A100` appear in `docs/reference.md` only at the line being edited, and
      in `tests/test_report.py` as **apparatus** fixture facts, which are correct and must not move.
- [ ] Mechanical pass on the edited file: every relative link and `#anchor` resolves, no two headings
      produce the same anchor, every table row matches its header's column count, no trailing
      whitespace, tab or invisible unicode, fenced blocks skipped in all of it.
- [ ] Run **arm R** and report that it passes **without an edit**. If it fails, stop: Ruling O's edit
      touched a worked-example literal and that is a finding for the controller, not something to fix
      by editing an arm with no authorized editor.
- [ ] Four gates. **Delta: 0 tests.** Commit.

**What this task must NOT touch.** `src/`. `tests/` — arm R is **run**, never edited. Any other key of
the `environment` block in the example. § What `study add` redacts (task 4's). § Errors core raises
(task 5's). § Templates (task 6's).

---

