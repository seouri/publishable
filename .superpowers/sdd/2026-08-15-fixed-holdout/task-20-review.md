# Task 20 review — the reader-facing half

**Reviewed:** `d72724b..b4113d1` (5 commits), against `task-20-brief.md` and `task-20-report.md`.
**Reviewed at:** working tree at `b4113d1`, 2026-08-16.

**Spec compliance: ❌**
**Task quality: ❌**

Both verdicts turn on claim accuracy, which is this task's entire deliverable. The work behind the
task is genuinely strong — a real measurement was run rather than re-derived, the brief's own bad
citation was caught, two rounds of self-correction landed, no phantom edits were written — and the
findings below do not dispute any of that. They dispute three specific sentences that are false or
unestablished, two of which are the implementer's own text and one of which is a live false build
claim in `CLAUDE.md`, the binding conventions file.

---

## Critical

### C1. `CLAUDE.md` line 61 still says "now that H3d has merged" — the fix swept a file, not the claim

**Verified:** `grep -n -i "h3d\|merged\|holdout" CLAUDE.md`. Line 38 reads "**H3d (`holdout`) is
complete on its branch, in the identical honest form**". Line 61 reads "retrofitting the holdout to
cells, and — **now that H3d has merged** and named both refusals — retiring …".

`git show b4113d1 --stat` shows that commit changed **one line** (line 38). Line 61 was added by
this task's own commits (`0ee62c6`/`88a3df4`), so the surviving false claim is in this task's diff,
not merely a miss by the corrector. `git branch --show-current` is `h3d-fixed-holdout`;
`git log --oneline -1 main` is `78bb794`; `git branch -a --contains d72724b` lists only
`h3d-fixed-holdout`. H3d is unmerged, so line 61 asserts a build fact that is false today.

This is the third instance in one slice of the same failure mode the review prompt names — task 19's
two false replacement sentences, task 18's sweep scoped to a string, and now a correction scoped to
the sentence it was first noticed in. `CLAUDE.md` § Habits that cost real work: "Sweep for the
claim, not for the file the claim was first noticed in."

### C2. The same false claim survives in the feasibility analysis: "H3d landed between the previous measurement and this one"

**Verified:** `docs/feasibility-llm-growth-studies.md` line 973, first sentence of the new dated
section. Same branch evidence as C1.

C1 and C2 are one claim in two places. The user's corrective commit touched `CLAUDE.md` only; the
identical framing in the dated section — the one file whose whole job is perishable build facts —
was not swept. "Landed" reads as merged. The section is pinned to `d72724bc…`, a commit reachable
only from the unmerged branch, which a reader on `main` cannot check out; that is worth saying
explicitly in the section rather than leaving the pin to imply merged state.

### C3. The dated section's scope statement and one of its reported results cannot both be true

This is the crux check of the review, and it fails on accuracy.

**The two sentences.** Line 976: "`parameters`, the real `sweep`, `replication`,
`statistics.report_by` and `hypotheses` were **not** carried over — each config was run with the
scaffold's own stand-in single-axis sweep and **default seed-repeat** in their place." Line 997: "on
E5 specifically, `W-REPL-DETERMINISTIC`, an artifact of the demo entrypoint's step not declaring
`nondeterministic = True`".

**Verified against the emit site.** `src/publishable/validate.py:3382-3386`:

```python
kinds = {lv.get("kind") for lv in levels if isinstance(lv, dict)}
if "batch" in kinds and experiment is not None:
    if not any(getattr(s, "nondeterministic", False) for s in experiment.steps):
        c.warn("W-REPL-DETERMINISTIC", …
```

The warning requires a `batch` repeat level in the config. **Verified what the scaffold writes:**
`src/publishable/materialize.py:143-145` materializes `replication.repeats:
- {kind: seed, n: INIT_REPEATS}`. A default seed-repeat cannot produce `W-REPL-DETERMINISTIC`.

So either (a) E5's real `replication` (`{kind: batch, n: 10}`, § E5) *was* transplanted and the
scope disclosure is false, or (b) it was not and the E5 warning attribution is false. Only the
implementer knows which. Until it is resolved, the section's scope statement — the thing this task
exists to get right — cannot be trusted as written, and the same doubt attaches to whether
`replication` was selectively carried for other configs too.

I did **not** rebuild the scratch project; the emit condition is dispositive and reproduction adds
nothing.

---

## Important

### I1. Asymmetric evidence standard on C1–C3's `io.reuse_from` blocker, contradicting the same section twenty lines up

**Verified by reading lines 967, 999, 496-517, 521-535 of the feasibility analysis.**

Line 999 argues correctly that E3/E4/E6's remaining blocker is **invisible to `validate`** because
`io.reuse_from` is a step-level call, not a config declaration — then, in the same sentence, argues
C1–C3's **absence from config YAML** proves the absence of that same blocker: "none of the three
declares a reused artifact (C1's regimes are `utilization_only`/`clinical_physiology`/`zero_shot`,
none of them a fine-tuned one read via `io.reuse_from`)". Config-visibility was just established as
the wrong instrument for this question.

Against it, in the same document: line 967 (the **previous dated measurement**, in the same section)
says `io.reuse_from` is used by "E3, E4, and E6 … and **the shortcut's confirmation run** … to read
its fine-tuned artifact"; line 517 says "The confirmation run reads the fitted artifact with
`io.reuse_from`"; and the shared shortcut roster block (line 509) says
`holdout: null   # confirmation run: the roster IS the confirmation set` — i.e. C1–C3 *are* the
confirmation runs. § Shortcut also says the pipeline "fits the two regression baselines", and C1's
declared baseline is `utilization_only`.

I am **not** asserting C1–C3 do carry the blocker — that is not established either. The finding is
that the new section asserts one side of its own document's contradiction without acknowledging the
other. Remedy: cite line 967 and say why it does not govern, or drop the sentence. Note this is the
claim the implementer has now reversed **twice** (`88a3df4`, then `534d41b`); two reversals is a
signal the claim is not established, not that the third version is right.

### I2. The `CLAUDE.md` paragraph is not concise, and its closing clause is now circular

Brief step 3(d) and check #4 require the slice-order paragraph be truthful, **concise**, and not
restate spine-design reasoning. **Verified by reading the diff:** three replaced lines became
twelve. Two specific costs:

- "and it is the same lesson stated a third time: a retired-refusal count is not an executable-run
  count, which is exactly what step 10 of § Feasibility analyses exists to keep a reader from
  conflating" — the warning was required, but it is here restated at length rather than carried;
  the H4a sentence immediately above already says "**zero experiments newly executing**, which is
  the honest form of that number."
- The closing clause "so *as written* none runs until H7b, and even under a table-roster
  substitution **only for configs sourcing their roster from a table**" is a tautology. That clause
  carried information when it was attached to "H3d then unblocks six and H4b the last three"; with
  the count removed it says only that a table-roster substitution applies to table rosters. The
  honest counterpart — the generous count is **three**, not six — is in the feasibility section but
  not here.

No spine-design reasoning is restated, which the paragraph does honour.

---

## Minor

### M1. The mis-citation at line 999

"§ E5 — Binary-output repeatability and the `io.reuse_from` paragraph above are what this depends
on" — the claim being supported is that **E3, E4 and E6** read a frozen program through
`io.reuse_from`. **Verified:** `grep -n "reuse_from" docs/feasibility-llm-growth-studies.md` returns
lines 74, 332 (inside § E3), 457 (inside § E6), 517, 846, 967, 999 — **nothing inside § E5's range
(405-451)**. § E5 supports nothing here; § E3/§ E6 and line 967 do. Plain text, not a link, so no
broken anchor.

### M2. `CLAUDE.md` itself carries the bad citation the implementer attributed solely to the brief

The report calls "`reference.md` § What core will not do for you" the brief's own defect. It is also
in `CLAUDE.md` § Feasibility analyses step 6: "`reference.md` § What core will not do for you and
`experimental-designs.md` § What core will not do for you are the two lists to check against."
**Verified:** `grep -rn "will not do for you" README.md docs/*.md` — the heading exists only at
`docs/experimental-designs.md:387` (plus its own TOC entry and a `design-principles.md` cross-link).
Pre-existing and outside this diff, but `CLAUDE.md` is a file this task edited, and the brief's
defect was inherited from it rather than invented.

### M3. The report's housekeeping claim about `.superpowers/sdd/.gitignore` does not match the tree

The report says the file "was found clobbered … and was restored via `git checkout --` before this
report was written, verified by diff." **Verified:** at review start `git status --short` showed
` M .superpowers/sdd/.gitignore`, and `cat` showed a bare `*`. The committed content is correct, so
the damage is nil — but the worktree was clobbered again (or never restored), and "verified by diff"
verified something other than what it claims. I restored it with `git restore` during this review;
the tree is clean now. Separately, `CLAUDE.md` § Two mechanical traps warns specifically against
`git checkout -- <file>` for exactly this purpose.

---

## Verified correct — affirmed with evidence

- **Append-only holds.** `git diff --numstat d72724b..b4113d1 -- docs/feasibility-llm-growth-studies.md`
  → `36  0`; `git diff … | grep -c "^-[^-]"` → `0`. The 2026-08-15 measurement is byte-untouched,
  and the new `###` section sits inside § Executability on this build, before the `---` and § Cost
  and execution summary. It says what it replaces ("Confirms the previous measurement's structure
  and corrects its headline framing").
- **The scope disclosure is structurally prominent, and the implementer's residual worry is
  unfounded on that axis.** The lead sentence names the narrowing, a dedicated paragraph ("What this
  measurement therefore answers, precisely") states it as a bounded question, and the results
  table's own column header reads "`validate` reports **on the transplanted `data`/`statistics`
  blocks**". The scope statement fails on **accuracy** (C3), not on prominence.
- **The numbers carry their qualifiers.** "6 of 9" appears only as "one refusal retired that 6 of 9
  configs hit" (`CLAUDE.md` line 39) and as the thing explicitly rejected as an executable count
  ("**Zero of the nine execute, and the honest count is not '6 of 9 unblocked.'**"); "three, not
  six" is stated with its substitution caveat; "zero experiments newly executing" appears in both
  files. No sentence lets a retired-refusal count read as an executable-run count.
- **`docs/reference.md` genuinely needs no edit.** § A fixed holdout split's **fourth** bullet
  (line 1333) already names both `E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS` and says drawing
  within a cell is not built; line 189 records "`data.units.holdout` left it with H3d" and line 309
  and line 1427 carry the fold half. Read in full.
- **The brief's `reference.md` § What core will not do for you citation really is absent** — see M2's
  grep.
- **`docs/experimental-designs.md` needs no edit.** § Train-test holdout (192-206) claims only
  `io.units`/`io.units.train`, `by_attribute`, `n` as the test partition, and mutual exclusion with
  CV — all built. Nothing in it implies per-cell drawing; line 123 already states the cells refusal
  and links to `reference.md`. § Mistakes core prevents (336+): the cluster/fold/holdout rows are
  strengthened, not weakened, by the cells refusal; nothing became merely-discouraged.
- **Every code the new section names exists in `src/`:** `E-DATA-RESOLVER-UNSUPPORTED`,
  `E-DATA-WEIGHT-CONTRAST`, `E-DATA-HOLDOUT-FRAC`, `E-HYPOTHESIS-METRIC`, `E-ENTRYPOINT-IMPORT`,
  `E-TEMPLATE-UNKNOWN`, `E-DATA-HOLDOUT-CELLS`, `E-REPL-FOLD-CELLS` (grep over
  `src/publishable/`).
- **The mutation's quoted message is verbatim.** `validate.py:2798-2800` emits
  `E-DATA-HOLDOUT-FRAC` with "is {frac}, and a test fraction is strictly between 0 and 1 — …",
  matching the section's quotation.
- **`grep -rn "reuse_from" src/publishable/` returns nothing**, with a working control
  (`def validate_config` → `validate.py`).
- **Test claim confirmed by running it:** `uv run pytest -q` → `1954 passed, 2 xfailed in 104.35s`,
  exactly the figure the section states.
- **Mechanical pass clean** on both edited files: no trailing whitespace, no tabs, no invisible
  unicode (`grep -nP "[ \t]+$"`, `\t`, `[\x{00a0}\x{200b}\x{2060}\x{feff}]` — all empty); no
  duplicate heading anchors (script over both files, fenced blocks skipped); the new table is 3
  columns in header, separator, and all 9 rows; the new text introduces no markdown links, so no
  anchor can dangle; the new `###` heading is a subsection and § Contents lists `##` only, so no TOC
  entry is owed; no multiplication appears in the new text so `×` is not at issue. The em dashes in
  `### E1 — …` headings are pre-existing and their existing links (`#e1--metric-calibration`)
  resolve.
- **Nothing in the four documents claims H3d or `holdout` is unbuilt.**
  `grep -rn "not yet built\|not built\|UNSUPPORTED" README.md docs/reference.md
  docs/experimental-designs.md docs/design-principles.md | grep -i "holdout\|fold\|H3d"` returns
  only correct statements about **within-cell drawing** being unbuilt.
- **The worked example is untouched** — no `cohort-pilot` numbers appear in the diff.

---

## What must change before this task is done

1. `CLAUDE.md` line 61: remove "now that H3d has merged". (C1)
2. `docs/feasibility-llm-growth-studies.md` line 973: "H3d landed" → language matching "complete on
   its branch, not merged", and say the pinned commit is a branch commit. (C2)
3. Resolve C3 — say which of the two sentences is true, and correct the other. If `replication` was
   selectively transplanted for some configs, the scope paragraph must say which.
4. I1: either cite line 967 and argue why it does not govern C1–C3, or drop the sentence.
5. I2, M1: tighten the `CLAUDE.md` paragraph and fix the § E5 citation.

Corrections 2-4 are to a **dated** section: per `CLAUDE.md`, appended and saying what they replace,
not retro-edited — except that items 2 and 3 correct a section published within this same
uncommitted-to-`main` slice, so the cleaner route is a `--amend`-free follow-up commit that rewrites
it before the branch is merged, with the commit message recording what was wrong.
