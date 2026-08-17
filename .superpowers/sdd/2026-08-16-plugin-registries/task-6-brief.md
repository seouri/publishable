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

