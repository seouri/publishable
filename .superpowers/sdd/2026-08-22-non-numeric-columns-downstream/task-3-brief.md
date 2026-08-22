## Task 3: § The per-unit tables' routed question decided, § Statistical reporting, and `W-STATS-REPEATS-DISAGREE` minted

**Surface: documents. Runs before any code reports the warning** — the documents lead, and a § Warnings
row is normative specification rather than a build claim.

**Files:** `docs/reference.md`, `docs/superpowers/spec-defects.md`

- [ ] **Step 1: § The per-unit tables — decide the routed mixed-type question (Decision 11).** The
      section currently ends the paragraph about a column that is `str` for some units and a number for
      others with *"The more forgiving reading … is a live question for how the table `aggregate`
      receives should treat such a column, and is not decided here."* **Replace the open clause with the
      decision**: on the **read** side a column is published as a metric only when **every** value
      carried for it is a real number, so one string in a column of floats costs that column its metric
      block and nothing else — the column still reaches `aggregate`, where a template that knows what
      the mixture means can use it. On the **write** side `E-STEP-RETURN-TYPE` is **not** loosened,
      because loosening it would make a column's published-or-not status depend on the data rather than
      on the config: one run of a config would publish a metric and the next would not, with no
      diagnostic distinguishing them.
      **This is the total rule over however a mixed column arises**, which is what makes it a decision
      rather than a reachability claim — measured: `summarize_step` over a column with **one** `None`
      cell and five floats publishes **no** metric block for it at all (this plan's probe `p3`).

- [ ] **Step 2: § Statistical reporting states what `aggregated` may not hold.** A metric block's `value`
      is a number, so a recorded column earns a block only when every value carried for it is a real
      number. **One sentence, in the section that already defines the metric block**, and it must not
      contradict the `basis: repeats` and `reported: true` cases the section already carries — read them
      first and say in the report which you read.

- [ ] **Step 3: mint `W-STATS-REPEATS-DISAGREE` in § Warnings core reports.** **One row, covering its
      single emit site.** Place it among the `W-STATS-*` rows by code — its siblings are
      `W-STATS-NULLTEST-FAMILY` and `W-STATS-REPORTBY-THIN`; **locate them by their codes, never by
      position.** The row states the condition, not the wording: *a step's recorded column is not a
      number and disagrees across the repeats of at least one unit, so that unit's cell is `None`; the
      per-repeat `units.parquet` files still hold every observation, and the declared route for a
      within-unit collapse is `data.units.measurements`.* Fires at **`run`** time.
      **Why one site is the whole story, established by reading and then confirmed:** the aggregation
      phase collapses once per (condition, step); the stratum loop re-filters the same `collapsed` rather
      than collapsing again. Confirmed by `grep -n 'collapse_repeats(' src/publishable/*.py` → **one**
      production call site plus the definition. **Run that grep yourself and report it** — a diagnostic's
      unit of work is every site that raises *or* reports it, and a task scoped by a helper's single call
      site has already missed a second site once in this repo.

- [ ] **Step 4: three § Errors rows are asserted, not edited. Read each emit site, then grep.** In that
      order — the reverse is the substitution § Answering a question with a proxy is about.
      `E-STEP-KEY-COLLISION`: its row already names *"a derived key against a recorded column"* and
      already says this site is re-reported as `W-STATS-AGGREGATE-FAILED` rather than raised; **no emit
      site is added, the same site sees a wider input, so the row does not move.**
      `E-STEP-COLUMN-UNKNOWN`: its row describes *"a column no row of the unit table holds"*, which
      stays exactly true as the held set widens. **No change.**
      `E-STEP-RETURN-TYPE`: **no change** — step 1 decides the read and leaves the write strict.
      **Report the greps and the sites, and if a row turns out narrower than its code, that is a finding
      and it is filed rather than quietly widened.**

- [ ] **Step 5: file the write-side residual, unassigned with a reason.** `spec-defects.md` gets a new
      entry: *whether `E-STEP-RETURN-TYPE` should ever be forgiving for a genuinely mixed `.parquet`
      column.* **Owner: unassigned, with the reason** — no remaining slice (H6, H9, H3c-3's remaining 14)
      has the write side as its surface, and H5a is merged. **Name in the entry that H5a's design said of
      this question "Filed, not built, owner H5b" and that no such filing existed** —
      `grep -n 'more forgiving' docs/superpowers/spec-defects.md` → **0 lines** at `ee8085e`, control
      `grep -c 'E-STEP-RETURN-TYPE' docs/superpowers/spec-defects.md` → **4**, so the sweep can hit.
      **Run both and report them.** *A design line saying "Filed" is not a filing* — second instance in
      one slice pair, and saying so is part of the entry.

- [ ] **Step 6: both consistency passes on these edits**, in the shape task 2's steps 3 and 4 give.
      **Enum comments:** grep for any inline `# a | b | c` comment listing warning or error codes and
      confirm none enumerates the `W-STATS-*` set — if one does, it gains the new code.

- [ ] **Step 7.** No mutation; **named blind in advance** for the same reason task 2's is. Its
      replacement is task 5's Fixtures C and D, which pin the warning at its site, and the B1 review's
      *is the mint's row true of the site batch 2 will add?* check.

- [ ] **Step 8: run** the four commands (no test delta) and **commit**: `H5b task 3: decide the mixed
      column's read, state what aggregated may not hold, mint W-STATS-REPEATS-DISAGREE, file the write
      side`.

---

