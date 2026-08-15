# Task 12 — the consistency passes and the slice's exit criterion

**Status: PASS.** Every check below ran with a control that had to report and did.
Two defects were found and fixed (one commit); everything else was already clean.

Suite at close: `1226 passed, 2 xfailed`. `ruff check` clean, `mypy` clean over 40
source files. `ruff format` was not run.

Commit added by this task:

- `313bc97` — *docs: cite the validation rows by title, and stop naming a retired code in src*

---

## 1. Both retirements, both directions

**Command (Python direction):**

```
grep -rn --include='*.py' -E 'E-DATA-MEASUREMENTS-UNSUPPORTED|E-DATA-WEIGHT-UNSUPPORTED' src/ tests/
```

**Command (Markdown direction):**

```
git ls-files '*.md' | xargs grep -n -E 'E-DATA-MEASUREMENTS-UNSUPPORTED|E-DATA-WEIGHT-UNSUPPORTED'
```

**Proof each can fail.** The Markdown pipeline is the one that cannot be trusted on an
empty result, so the *identical* pipeline was re-run with two live codes substituted:

```
git ls-files '*.md' | xargs grep -n -E 'E-DATA-WEIGHT-CONTRAST|E-UNITS-COLLAPSE-RULE'
```

It printed five rows (`docs/reference.md` 414, 415, 420, 475, 888), so `git ls-files`
was non-empty and `xargs` carried the pattern. The Python direction's control was
`E-DATA-WEIGHT-CONTRAST`, which printed `src/publishable/validate.py`.
`--include='*.py'` kept `__pycache__` out.

**Result.** Zero hits in any tracked `*.md`, including the exempt `docs/superpowers/*`
tree — nothing there needed excluding. One hit in `src/`, now fixed:

- `src/publishable/envelope.py` carried `E-DATA-MEASUREMENTS-UNSUPPORTED` inside an
  explanatory comment ("a `colapse` typo unreachable by any check the moment
  `E-DATA-MEASUREMENTS-UNSUPPORTED` retired"). Rewritten to "the moment the block's
  wholesale refusal retired" — the explanation is unchanged, and the string is gone, so
  the mechanical check will not re-flag it on every future slice.

**Deliberately kept, do not "fix" these.** `tests/test_validate.py` (two sites) and
`tests/test_cli.py` still name both retired codes: `assert "E-DATA-MEASUREMENTS-UNSUPPORTED"
not in found` is a *retirement guard*, the mirror of the check, and the `test_cli.py`
mention is the comment that stops an `xfail` from silently XPASSing. The check is scoped
to `src/**/*.py` for exactly this reason.

## 2. The `NOT BUILT` count reads Nine

`docs/reference.md` § The one config file, prose after the fence: **"Nine declarations
above are not yet built"**. The fence carries exactly nine `NOT BUILT` marks, and they map
one-to-one onto the nine names in the prose — the cross-check no grep gives you:

| Mark | Named in prose as |
|---|---|
| `from:` | the `{resolver: <name>}` form of `data.units.from` |
| `allocation:` | any `data.units.allocation` other than `within` |
| `cluster_by:` | `data.units.cluster_by` |
| `holdout:` | `data.units.holdout` |
| `assign:` | `data.units.assign` |
| `groups:` | `sweep.groups` |
| `- {kind: seed, n: 5}` | a `fold` repeat level's `stratify_by` |
| `resample:` | `statistics.resample` |
| `null_test:` | `statistics.null_test` |

`measurements:` and `weight_by:` are the two lines whose `NOT BUILT` marks the branch
diff removes, and they are absent from the prose list. Exactly those two left; nothing
else moved.

## 3. Registry integrity, both directions

**Command.** Every `"E-…"`/`"W-…"` string literal in `src/**/*.py` against every
identifier in the four documents, `comm` both ways.

- **Documented but not emitted: empty.** No stale registry row survives.
- **Emitted but not documented: 17**, all pre-existing. Nine are the surviving
  `-UNSUPPORTED` family (`E-DATA-ALLOCATION-`, `-ASSIGN-`, `-CLUSTER-`, `-RESOLVER-`,
  `E-REPL-FOLD-STRATIFY-`, `E-STATS-NULLTEST-`, `E-STATS-RESAMPLE-`, `E-SWEEP-GROUPS-`),
  which § The one config file states are *deliberately* outside the validate-time
  registry. The other eight (`E-CODE-DIRTY`, `E-EXPERIMENT-EXISTS`, `E-EXPERIMENT-UNKNOWN`,
  `E-GIT-NO-COMMIT`, `E-GIT-NO-REPO`, `E-INPUT-CHANGED`, `E-PROJECT-EXISTS`,
  `E-RUN-ID-EXHAUSTED`, `E-RUN-LOCKED`) were verified **present on `main` unchanged** by
  extracting `main`'s `src/` into a scratch tree and diffing the code sets. Pre-existing
  scope, not introduced here, and not fixed here.
- **Introduced by this slice: 8 codes, all documented.** `E-DATA-MEASUREMENTS-COLLAPSE-TYPE`,
  `E-DATA-MEASUREMENTS-INVALID`, `E-DATA-WEIGHT-CONTRAST`, `E-DATA-WEIGHT-INVALID`,
  `E-DATA-WEIGHT-UNKNOWN`, `E-STEP-MEASUREMENT-UNDECLARED`, `E-UNITS-COLLAPSE-RULE`,
  `W-DATA-WEIGHT-UNDECLARED`. **Retired: exactly the 2.**

**What this pass did *not* verify.** The brief's step 3 also asks that "every new row's
condition be read from its emit site rather than from this plan" — the prose of each new
registry row against the code that emits it. That is condition-text verification, owned by
tasks 2–11 as each row landed; this pass verified **identifiers and tests**, both
directions, and spot-checked the two rows whose conditions carry the least obvious claims:
§ Errors `validate` reports' `E-DATA-MEASUREMENTS-INVALID` row ("reported alone, since
there is then no `by` or `collapse` to check either" — asserted directly, three sites in
`tests/test_validate.py` pin the companion codes *out* of the findings) and its
`E-DATA-WEIGHT-CONTRAST` row ("the *resolved* family is the test rather than the
declaration" — six test sites, including both the single-baseline accept and the
declared-contrast-without-a-baseline refuse). Neither is a substitute for reading all
eight rows, and neither was asked of this task by the parent's recast.

**The codeless-table trap.** § Validation's checks table carries no identifiers, so the
identifier grep sees none of its rows. Both rows this slice added there were checked by
hand instead: *"Measurement axis exists"* → `E-UNITS-ATTR-MISSING`
(`tests/test_validate.py` has positive assertions at three sites plus discriminating
negatives), *"Weighted deltas aren't computed"* → `E-DATA-WEIGHT-CONTRAST`.

**Registry counts — brief defect.** The brief's step 3 predicts § Errors `validate`
reports 65 → **69** and § Warnings core reports 18 → **19**. Counting each table's rows
by their **last column** (the row's own code — line 889 carries two codes in one row, so
a naive identifier count over-reads):

| Registry | `main` | `HEAD` | Brief predicted |
|---|---|---|---|
| § Warnings core reports | 18 | **19** | 19 ✓ |
| § Errors `validate` reports | 65 | **71** | 69 ✗ |
| § Errors core raises | 19 | **23** | not predicted |

The observation, without guessing at how the brief got 69: **six** rows were added to
§ Errors `validate` reports, of which **three** are dual-registry by design —
`E-DATA-MEASUREMENTS-COLLAPSE-TYPE`, `E-DATA-WEIGHT-INVALID` and `E-UNITS-COLLAPSE-RULE`
are each reached from `validate` *and* raised at run time, and the rows say so ("the same
reuse `E-REPL-SEED-COLLISION` above illustrates"). Neither counting convention yields 69
(all six → 71, none of the three → 68), so the brief's figure is not reconstructible and
no cause is claimed here. **No prose in any of the four documents states a registry size**
(grepped for it), so there is nothing to fix in the docs either way.

## 4. H3a's four § Validation rows, by title

All four verified by title. All four have an implemented check, the identifier the row
implies, and a `validate`-path test that produces it — each with a discriminating negative
twin, so none of them is a probe that reports for every input.

| Row title | Identifier | Emit site | Positive test |
|---|---|---|---|
| Collapse rule fits the column | `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` | `validate.py` (validate path), `units.py` (run path) | `test_a_mean_collapse_over_a_string_column_is_refused` |
| Weight attribute exists | `E-DATA-WEIGHT-UNKNOWN` | `validate.py`, two sites | `test_a_weight_by_naming_no_attribute_is_reported` |
| Weights are usable | `E-DATA-WEIGHT-INVALID` | `validate.py`; `stats.py` at run time | `test_a_zero_weight_is_refused`, `test_a_negative_weight_is_refused` |
| Weighting looks undeclared | `W-DATA-WEIGHT-UNDECLARED` | `validate.py` | `test_a_weight_looking_column_warns_when_nothing_declares_it` |

The collapse row was the one to check hardest, because its code is reachable from two
paths and a grep cannot tell them apart. Its positive test goes through the **validate**
path — `codes(path)` over a config whose `index.csv` carries a string `site` column under
`collapse: mean` — and its negative twin (`test_a_per_column_map_sparing_the_string_column_is_accepted`)
proves the remedy the row names actually works. The zero and negative weight cases are
separate tests on purpose: a check written `< 0` passes the negative case and lets a zero
through.

**Defect found and fixed.** Five test docstrings cited these rows by the stale numbers the
brief warned about — "Row 243", "Row 291", "Row 292" ×2, "Row 293" — which are now 244,
293, 294 and 296. All five now cite the row **title** under `§ Validation`, which is
stable. This is `CLAUDE.md`'s "cite by section, never by line number" rule; the numbers
had already gone stale within the same slice that wrote them.

(`src/publishable/validate.py` carries one further row-number citation, to
`docs/superpowers/spec-defects.md`'s "Row 216 has two readings". It is **pre-existing on
`main`** — outside this slice's diff — and left alone. Worth naming, because
`spec-defects.md` is gitignored, so that citation points at a file no merge carries.)

## 5. `partition_units` is untouched

**Command.** `git show main:src/publishable/units.py` into a scratch file, then compare
the two `partition_units` bodies by `ast.get_source_segment` — a text compare of the
function itself, which a hunk-header grep cannot do.

```
main len 603   head len 603   IDENTICAL
control resolve_units: DIFFERENT (expected)
```

**Proof it can fail:** the same comparison over `resolve_units`, which this slice did
change, reported DIFFERENT. H3a's claim to being first in H3 holds; H3b and H3c can rely
on it.

## 6. The worked example did not move

**Command.** A probe extracting every worked-example figure — `0.581 0.607 0.412 0.026
−0.007 0.059 −0.169 −0.213 −0.125 0.488 0.661 0.517 0.683 0.347 0.477 0.014`, the
hashes `8e21 1a2b 3d8a 6b1f 2f5c8d0`, `240 228 12`, and `cohort-pilot`/`cohort_pilot` —
from `git show <ref>:<file>` for each of the four documents, counted per file, diffed
between `main` and `HEAD`. **Result: IDENTICAL.** The branch diff touches zero lines
mentioning `cohort-pilot`.

**Proof it can fail — a real temporary commit**, as the brief prescribes, since a
two-dot diff cannot see the working tree. `0.581` → `0.582` in `docs/reference.md`,
committed as `TEMP: mutate a worked-example figure`, probe re-run: it **reported**
(`docs/reference.md 1 0.581` disappeared from the counts). `git reset --hard HEAD~1`
restored `313bc97`. `0.581` was chosen over `12` or `240` precisely because it has no
symmetric neighbour a mutation could coincide with.

**Neither field is declared by the worked example.** Every occurrence of `measurements:`
or `weight_by:` in the four documents is either the § The one config file *schema* fence
(both `null`, which is the schema and not a declaration), § Weighted samples' own example,
§ What isn't a repeat's own example, or `experimental-designs.md`'s varied-domain
`read_id` example. The feasibility analysis carries its own, which is its exemption.

## 7. The mechanical pass

A throwaway script, written fresh for this pass: fence-aware (structure checks skip
fenced blocks), checking relative links, `#anchor` resolution, duplicate anchors per file,
table row/header column counts, empty table rows, trailing whitespace, tabs, and invisible
unicode, over the four documents plus `CLAUDE.md` and the feasibility analysis.
**Result: clean — 6 files, 171 anchors.**

**Proof it can fail, and the trap it fell into first.** A mutated copy of
`docs/reference.md` was seeded with four defects: a broken anchor
(`#errors-validate-reportz`), a 3-cell row plus an empty row in a 2-column table, trailing
whitespace on a heading, and a duplicate `## Validation` heading. The first run over the
copy **reported nothing for every input** — the script's `ROOT` was hard-coded at the real
repo, so it read the pristine files no matter which path it was handed. This is the exact
failure the brief names. After making `ROOT` overridable it reported all four:

```
docs/reference.md:203: trailing whitespace
docs/reference.md:335: duplicate anchor 'validation' (also line 203)
docs/reference.md:216: table row has 3 cells, header has 2
docs/reference.md:217: empty table row
docs/reference.md:211: missing anchor #errors-validate-reportz
```

Two of the script's own probes were wrong at first and were fixed rather than suppressed,
which is what turned the three "known false positives" into real passes:

- the slugger collapsed runs of whitespace, so a heading whose `—` or `/` leaves *two*
  spaces produced one hyphen where GitHub produces two. That is the whole cause of
  `secrets--credentials`, `naming-conventions--repeat-defaults`, the `executions.jsonl`
  heading, `within-subjects--repeated-measures`, `between-subjects--parallel-arm-trial`,
  `allocationjson--who-went-where` and `e6--compiled-program-transfer`. With the slugger
  corrected, **all seven resolve**, and the final run was made with the false-positive
  suppression list **emptied** — so those three anchors are genuinely checked, not skipped.
- the table splitter split on `|` inside code spans, so `` `mean | median | sum` `` read as
  extra cells. All four "column count" hits were this.

Style rules: no `N x N` in any tracked document (control: `docs/reference.md` has 4
instances of the correct `N × N`); no en dash in any heading in the four documents
(control: a scratch file with `# A – B` reported).

## 8. The cross-document pass

| Class | Result |
|---|---|
| **The shared worked example** | Clean — § 6 above, verified by temporary commit |
| **Config completeness** | Clean. Every `data.units.*` key any module in `src/` names — `allocation`, `assign`, `attributes`, `cluster_by`, `from`, `holdout`, `key`, `measurements`, `weight_by` — appears in § The one config file's fence. Control: a bogus key reported |
| **Enum comments** | Clean, and this is the class the slice most plausibly broke. `collapse` accepts exactly five rules (`units.COLLAPSE_RULES = ("mean", "median", "sum", "first", "mode")`). `reference.md` § The one config file: `collapse is mean \| median \| sum \| first \| mode, or a per-column map`. `experimental-designs.md`: `# or median \| sum \| first \| mode, or per column` beside `collapse: mean` — five values in both, matching the code |
| **Schema fields in prose** | Clean. `measurements.by` and `.collapse` are named in prose and exist in the fence's comment; § The one config file says explicitly that the comment is where they live and that both are keys the closed schema checks |
| **Declared vs. derived** | Clean, and checked by hand. `technical_n`, `n.effective` and `weighted_by` appear **only** in results fences (a `r: {value: …}` block, `run.yaml`-shaped) and in prose describing what core *reports*. No passage shows any of the three as a settable input, in any of the four documents |
| **Versions** | Untouched by this slice. `CITATION.cff` `version: 0.1.0`; README's v0.x notice unchanged |
| **Prevented mistakes** | Clean. `experimental-designs.md` § Mistakes core prevents rows for technical replicates and for an enriched sample now describe *implemented* behaviour — `{kind: technical}` refused by name, `data.units.measurements` collapsing at resolution, `weight_by` recording `weighted_by`, and the warning when an attribute looks like a weight and nothing declares it. No document still calls either field unbuilt |

## Concerns

1. **The brief's registry counts are wrong** (65 → 69; actual 65 → 71), because three
   codes belong in both registries by design. Nothing to fix in the docs — no document
   states a count — but a later slice copying "69" forward would inherit the error. The
   brief's other numbers, including the stale row numbers it correctly warned about, were
   accurate.
2. **Eight pre-existing codes are emitted and documented nowhere** (`E-CODE-DIRTY`,
   `E-EXPERIMENT-EXISTS`, `E-EXPERIMENT-UNKNOWN`, `E-GIT-NO-COMMIT`, `E-GIT-NO-REPO`,
   `E-INPUT-CHANGED`, `E-PROJECT-EXISTS`, `E-RUN-ID-EXHAUSTED`, `E-RUN-LOCKED` — nine
   strings, eight distinct concerns). Present on `main`; out of this slice's scope;
   flagged for whoever owns the registry next.
3. **`validate.py` cites `docs/superpowers/spec-defects.md`, which is gitignored.**
   Pre-existing. The citation survives a merge; the file it points at does not.
4. The two H2-era `xfail(strict=True)` handles and `E-DATA-WEIGHT-CONTRAST` are as the
   brief describes: known, deliberate, not reported as defects.
5. `ruff format .` was deliberately not run.
6. **`.superpowers/` is gitignored**, so this report file is untracked and does not
   survive a merge — the same class of problem as concern 3. The durable record of this
   task is commit `313bc97` and the message returned to the caller.

`pytest`, `ruff check` and `mypy` were all re-run against the delivered tree after the
last edit, not before it.
