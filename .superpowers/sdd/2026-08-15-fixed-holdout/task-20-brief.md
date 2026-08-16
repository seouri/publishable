## Task 20: The reader-facing half — the honest count, and `experimental-designs.md`

**Files:** Modify `docs/feasibility-llm-growth-studies.md`, `docs/experimental-designs.md`, `docs/reference.md`, `CLAUDE.md`.

**Interfaces:**
- Consumes: nothing.
- Produces: the dated, commit-pinned build claim, and the two normative sections a reader checks against.

**Never state a build fact undated.** `CLAUDE.md`'s feasibility procedure step 10: a claim about what the tool *does today* is perishable in a way a spec claim is not, so it is dated and pinned to a commit and kept in a section of its own. § Executability on this build is the shape — "Measured on \<date\> against commit \<sha\>", every refusal named by its code.

**The honest count, and it is not the charter's.** Write **this**, not "unblocks 6 of 9":

> H3d retires **one refusal that 6 of 9 configs hit** (`E-DATA-HOLDOUT-UNSUPPORTED`, E1–E6; the three shortcut configs declare `holdout: null`), and **zero experiments newly execute.** All nine still declare a resolver and still earn `E-DATA-RESOLVER-UNSUPPORTED`, which is H7b's. C1–C3 keep `E-DATA-WEIGHT-CONTRAST` on top of that.
>
> Under a **table-roster substitution the analysis does not itself make**: E1, E2 and E5 would validate clean and could run. **E3, E4 and E6 would validate clean and still cannot execute** — each reads its frozen compiled program through `io.reuse_from`, which this analysis's own § Executability records as *"no such method exists yet"*. So even the generous count is **three**, not six, and it rests on a substitution nobody has written.

**Re-measure rather than restate.** The scoping measured this on 2026-08-15 against `78bb794`, and this slice has changed the build. **Run the six holdout-declaring configs through `validate` yourself** and write down what they actually report at the merge commit. If any number differs from the scoping's, the measurement wins and the difference goes in the commit message.

- [ ] **Step 1: Write the failing test** — a measurement script, kept only as long as this task, in the scratchpad rather than in the repo:

```bash
cd /Users/joon/src/tries/publishable
# Extract each YAML block from the feasibility analysis into a scratch config,
# point it at a real repo and a table roster, and run `validate`. Record the
# exact code list per config. This is a MEASUREMENT, not a test — its output is
# what gets written into the dated section.
git rev-parse HEAD          # the sha to pin
date -u +%Y-%m-%d           # the date to write
```

- [ ] **Step 2: Run it, confirm it fails** — `grep -n "Measured on" docs/feasibility-llm-growth-studies.md` shows the previous measurement's date and sha, both now stale. That is the confirmation: the section exists and is out of date, which is exactly the state step 10 exists to keep visible.

- [ ] **Step 3: Implement** — four edits.

  (a) `docs/feasibility-llm-growth-studies.md` § Executability on this build: **append** a new dated measurement rather than editing the old one — this is analysis output, and a correction is appended and says what it replaces. New heading line "Measured on \<today\> against commit \<sha\>", then the honest-count block above with every code named, then the per-config table of what each of E1–E6 and C1–C3 now reports. Say explicitly that `E-DATA-HOLDOUT-UNSUPPORTED` no longer appears and that `E-DATA-RESOLVER-UNSUPPORTED` still does.

  (b) `docs/experimental-designs.md` § Train-test holdout: check the section against what this slice built — every claim it makes must now be honoured or refused with a named code — and § Mistakes core prevents: confirm nothing it lists became merely-discouraged rather than structurally impossible. The cells refusal *strengthens* that section rather than weakening it; say so if the section's wording implies folds and holdouts are drawn per cell (task 8 already rewrote the one paragraph that did — **read it first** rather than rewriting it twice).

  (c) `docs/reference.md`: re-check § What core will not do for you against this slice. A holdout inside cells is now a **named refusal with a code**, not an unstated gap, so it belongs there if that list enumerates refusals of that kind.

  (d) `CLAUDE.md`: update the slice-order paragraph. H3d has landed; the remaining order is **H4b → H7b → the rest**, with H3c-3 named as the owner of both the cells retrofit and the cells refusal's retirement. State H3d's payoff in the honest form — one refusal retired that 6 of 9 hit, one live defect closed, zero experiments newly executing — and keep the existing warning that a refusal count read as an executable count is what step 10 exists to prevent.

- [ ] **Step 4: Run, confirm it passes** — `grep -n "Measured on" docs/feasibility-llm-growth-studies.md` shows both the old measurement and the new one, in that order, with the new one naming what it replaces. Then the **mechanical pass** on all four files (the feasibility analysis is exempt from the cross-document pass and subject to this one in full): links and anchors resolve, no duplicate anchors, table rows match headers, no trailing whitespace or tabs, `×` not `x`, hyphens not en dashes in anything that becomes an anchor. Then the **cross-document pass** on the three normative files: the shared worked example is untouched (this slice adds no `cohort-pilot` numbers — confirm it), config completeness holds (§ The one config file's fenced example carries every `holdout` field this slice enforces), every enum comment lists every value its table defines, and nothing shows a derived value as a settable input. Then `uv run pytest` and the three other commands one last time.

- [ ] **Step 5: Mutate** — the claim that can silently be wrong here is the measurement. Take the **one** config the new section says now validates clean under a table-roster substitution, break one field of it deliberately (a `frac: 0` say), and confirm `validate` reports the code the section would have to name. If it reports something else, the section's claim about that config is what is wrong.

- [ ] **Step 6: Commit** — `docs: the honest H3d payoff, dated and pinned`. Use `git add -f` for anything under `.superpowers/sdd/` if the workspace gitignore has been clobbered, and restore that file's content to a bare `*` if `scripts/sdd-workspace` has rewritten it.

---

## Closing checks before the branch is finished

Not a task — the whole-branch review's own list, gathered here so it is not re-derived.

- `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` all clean.
- `grep -rn "E-DATA-HOLDOUT-UNSUPPORTED" src/ tests/ docs/` returns nothing.
- Task 1's two pins still pass, unedited. A no-holdout run is byte-identical to `78bb794`.
- Every one of the thirteen codes in Global Constraints has a § Errors row, a check that emits it, and a test that sees it emitted. `CLAUDE.md`: a row and a code are the same check seen from two ends, and **either end can be missing**.
- Every mutation named in the plan was actually run, actually failed, and was reverted **in place**.
