# H3d — whole-branch **re-review** (scoped: were the review's findings closed?)

Reviewed on 2026-08-16: `.superpowers/sdd/2026-08-15-fixed-holdout/whole-branch-review.md`'s
findings against the fix commit `db2c482` (diff `review-452062d..85e6d4c.diff`), on branch
`h3d-fixed-holdout`. **Not a re-review of the slice** — only whether each finding was closed,
and whether closing it introduced anything new.

**Verdict: all six findings and all three residues are closed — but the closure of I1
introduced two false clauses in `reference.md` § Errors core raises, and the R3 correction
introduced a third false clause in a dated section. Four one-clause documentation repairs
(three false claims + one false docstring claim), then ready to merge.** No code defect, no
wrong number reaching a user, no test that cannot fail.

Every mutation below was reverted by restoring the file's exact prior bytes and re-verified by
re-running the affected tests — never by `git status`, never with `git checkout --` against a
mutated source file. `git status --porcelain` clean at the end (the one modification found at
session start, `.superpowers/sdd/.gitignore` clobbered to a bare `*` by `sdd-workspace`, was
restored from `HEAD`). **This new record needs `git add -f`.**

Gates were re-verified by the requesting session and not re-run here, except the full suite,
which I ran twice under mutation (1957 passed + 2 xfailed both times, mutations reverted).

---

## Finding by finding

### I1 — two run-time raises with no § Errors *core raises* row: **closed, but both new rows carry a false reachability clause**

Both rows landed (`reference.md:998` for `E-DATA-HOLDOUT-VALUES`, `:999` for
`E-DATA-HOLDOUT-EMPTY`), in the § Errors core raises table, in the house style, beside the
`E-DATA-ASSIGN-LEVELS` precedent the review named. Every other claim in them checks out
against `units.py:1407` and `units.py:1485-1493`. But each row's *reachability* clause — the
half that says where a run meets the fault — is wrong, and in both cases it is wrong in the
direction that hides a validate-clean-then-abort surface, which is the thing I1 existed to
document.

**N1 (Important). The `EMPTY` row's "the two draws `validate` cannot check itself" is an
incomplete enumeration, and the omitted case is reachable from a clean `validate`.**

Row 999 reads: *"raised here for the two draws `validate` cannot check itself: a stratified
draw … and a clustered draw …"*. There is a **third** path, in the plain unstratified,
unclustered draw: `validate._check_holdout` tests only `test_size == 0`
(`validate.py:3005-3020`), and never the train side. Verified by execution:

```
holdout_sizes(2, 0.9) = (0, 2)
holdout_for(2-unit roster, {method: random, frac: 0.9}) -> RAISED E-DATA-HOLDOUT-EMPTY
  "…leaves the train side empty"
```

`frac: 0.9` is inside `(0, 1)` and `test_size = 2 ≠ 0`, so `validate` reports nothing and the
run aborts at the draw — exactly the gap the row is supposed to name. `units.py:1384-1390`
already states the fact in the right words (*"`validate` … does not refuse a zero *train*
side — 2 units at `frac: 0.9` apportions `(0, 2)`"*), so the repair is to widen the clause,
not to invent wording. **Repair: one clause.**

**N2 (Important). The `VALUES` row says a run meets the fault at the draw. A run meets it at
`validate` and exits.**

Row 998 reads: *"a run that validates first meets it at the draw rather than a second time."*
`validate` reports `E-DATA-HOLDOUT-VALUES` whenever the roster resolves and `from` is a
non-empty string (`validate.py:2952-2960`), and `command_run` returns `EXIT_WRONG` on
`c.has_errors` before any draw (`cli.py:1278-1282`). So no run reaches this raise — unlike the
`E-DATA-ASSIGN-LEVELS` precedent, which correctly names *"the three draws that pass
validate-time."* The repo's own test says so: `tests/test_units.py:3220`'s docstring —
*"`validate` refuses this first; the draw refuses it too rather than partitioning on whatever
it finds."* The sibling rows' correct construction is right above it at line 996
(`E-DATA-CLUSTER-UNKNOWN`): *"also reported by `validate` … which is where a run that validates
first meets it."* **Repair: one clause, and the correct form is already in the adjacent row.**

### I2 — missing § Errors *validate reports* row + no validate-surface test: **closed**

- Row added at `reference.md:489`, correctly gated (*"Under `method: by_attribute`"* matches
  `_holdout_constant_column`'s own `method != "by_attribute"` early return, `units.py:484-485`),
  and its family claim is true of `E-DATA-ASSIGN-VARIES`'s row at 481, which names all four codes.
- Three tests added (`tests/test_validate.py:8064-8130`). **All three are falsifiable at the
  code level**: neutering `_holdout_constant_column` to `return {}` (one line) fails
  `test_a_holdout_column_varying_within_a_units_rows_is_reported` and
  `test_validate_reports_rather_than_raising_on_a_varying_holdout`; the control
  (`test_agreeing_holdout_rows_are_not_reported`) passes, as an absence control does, and is
  paired with the positive as required. Reverted, re-verified: 3 passed.
- Named single-line mutations for each: (a) positive — `_holdout_constant_column`'s
  `by_attribute` gate, run above; (b) control — a mutation that makes the check fire on
  agreeing rows (drop the `any(v != values[0] …)` guard at `units.py:877`); (c) message test —
  the fragments below.

**N3 (Minor, false-claim class). The message test's docstring claims it pins the holdout
`why`; it does not.** `test_validate_reports_rather_than_raising_on_a_varying_holdout`'s
docstring says the message assertions exercise *"the `why` from
`CONSTANT_COLUMN_RULES["holdout"]`"*. The asserted fragment `"decided by the order the rows
happen to be in"` is the **shared f-string prefix** at `units.py:889-891`, identical for
`cluster_by`, `weight_by`, `assign` and `holdout` — it does not appear in the holdout `why` at
all (which reads *"leave that decision to the order the rows happen to be in"*). **Verified by
mutation:** replacing the entire `CONSTANT_COLUMN_RULES["holdout"]` message with
`"MUTANT WHY TEXT"` left **the full suite green — 1957 passed, 2 xfailed**. Reverted, byte-identical,
re-verified.

Two mitigations, which are why this is Minor: the other two fragments *are* discriminating
(`"\`data.units.holdout.from\` names 'split'"` pins the declaration key that
`_holdout_constant_column` produces; `"unit 'p1'"` pins the who), and **no sibling's `why` is
pinned either** (`grep` over `tests/` for each of the four `why` texts: zero hits), so this is
parity, not a regression. The defect is the docstring's claim, not the missing assertion.
**Repair: drop or correct that clause — or, better, add `"which side of a split a unit is on
is a fact about the unit"` as a fourth fragment, which would make the claim true.**

### I3 — `units_hash` pinned by nothing: **closed, mutation re-run and confirmed**

Assertion added at `tests/test_cli.py:8221-8235`, recomputing `units_hash` over the re-resolved
whole 20-unit roster. Mutation re-run by me at the provenance call site (`cli.py:2636`):
`units_hash(roster)` → `units_hash(eval_roster)` →
**FAILS** `test_a_declared_holdout_now_validates_and_runs` with two different digests. Reverted by
editing the file back; `diff` against a pre-mutation copy is identical and the test passes. The
assertion compares against a recomputation rather than a literal digest, which is the ruling
the ledger recorded at task 1.

### I4 — `holdout.stratify_by` / `.seed` absent from § The one config file: **closed**

The fence at `reference.md:91-97` now expands all five keys, in the style of the `assign`
block directly below it. Checked against the code, not only against the review:
`envelope.py`'s `LEAF_TYPES` closes the block at exactly `method`, `frac`, `from`,
`stratify_by`, `seed` — the five shown, no more, no fewer. `# random | by_attribute` is total
over `validate.HOLDOUT_METHODS = ("random", "by_attribute")`, so the enum-comment rule holds.
The `frac`/`from` comments are copied verbatim from § A fixed holdout split's own fence
(`reference.md:1318-1323`), so the two cannot drift apart silently. Config-completeness rule
satisfied.

Nit, not a finding: `seed: auto  # design digest + "holdout"` omits the resolved roster, which
`holdout_seed_for` also mixes and which § What `auto` derives from's row names. The sibling
`assign` line abbreviates identically (`# design digest + axis name`, where the table row says
"digest + the axis name + the resolved roster"), so this is parity.

### M1 — future-tense docstring: **closed**

`artifacts.py:337-343` now records what landed, and the record is true: `holdout` is
`build_allocation_document`'s fourth key (`document = {"seed", "arms", "holdout", "strata"}`,
`artifacts.py:299-308`), and `grep -rn 'holdout_hash' src/` returns only this docstring's own
mention — no such function was added to `hashes.py`. The reasoning it preserves is unchanged.

### M2 — unfalsifiable absence assertion: **closed, and the judgment is honest**

I audited the call rather than accepting it. The comment at `tests/test_validate.py:925-928`
marks the line as a permanently-true retirement guard and rests the test's claim on the two
positive assertions above it. That rests correctly: `assert "E-REPL-KIND" in by_code` and
`assert "data.units.holdout" in by_code["E-REPL-KIND"]` are pinned by
`replication.REJECTED_KINDS["holdout"] = "declare \`data.units.holdout\` instead"`
(`replication.py:28`), so changing the routing or dropping `holdout` from the rejected set
fails this test. It is **not** `CLAUDE.md`'s "a control asserting only absences" shape — that
shape is a test whose *only* assertions are absences, and this one's absence is a third line
beside two live ones. Leaving it, labelled, is better than deleting a genuine retirement guard.

One phrasing nit: *"this line alone can never fail"* is in tension with calling it a regression
guard in the next clause — it can fail, and that is its entire purpose, if
`E-DATA-HOLDOUT-UNSUPPORTED` is ever reintroduced. Both halves are present, so it reads
coherently; not worth an edit on its own.

### R1 — `ruff format` config: **closed** (mechanics verified by the requesting session)

`[tool.ruff.format] exclude = ["*.md"]` landed in `pyproject.toml`.
`uv run ruff format --check .` → **39 would be reformatted, 35 already formatted**; every one
of the 39 is a `.py` file (extensions tallied from the `-->` lines: `39 py`, zero Markdown).

### R2 — `spec-defects.md` lesson into `CLAUDE.md`: **closed**

One clause appended to the existing *"A ledger line saying 'filed' is not a filing"* bullet:
*"A filing's claims about the code go stale like any other comment; when you change code a
`spec-defects.md` entry describes, re-read the entry."* It is one sentence, it sits at the end
of the right bullet, and it does not disturb the bullet's two existing lessons. The Format row
edit is the other `CLAUDE.md` change; see the nit below.

### R3 — the dated measurement's correction: **appended, not retro-edited — but it contains a false claim**

**Appended correctly.** `git diff` on `docs/feasibility-llm-growth-studies.md` is **2
insertions, 0 deletions** — nothing in the prior dated text was modified or deleted, and the new
paragraph opens *"**Correction (H3d whole-branch review, 2026-08-16), replacing the withdrawal's
last sentence above:**"*, which is the form `CLAUDE.md` prescribes.

**Its reasoning is sound.** Both code facts it rests on are real:
`materialize.py:145` writes `- {kind: seed, n: INIT_REPEATS}` as `init`'s default repeat, and
`validate.py:3383` gates `W-REPL-DETERMINISTIC` on `"batch" in kinds`. The asymmetry argument —
two independent corroborations for the scope statement, none for the reported warning — holds,
and the containment argument holds too (none of the three codes the section answers for reads
`replication`).

**N4 (Important). Its last sentence is false at the commit that wrote it.** The correction
states: *"`git diff d72724b..HEAD -- src/ tests/` is empty, so no code changed after the commit
this section names."* That was true when the whole-branch review checked it, and the fix commit
`db2c482` — the same commit that appended this sentence — changed
`src/publishable/artifacts.py`, `tests/test_cli.py` and `tests/test_validate.py`. Today:

```
git diff --stat d72724b..HEAD -- src/ tests/
 src/publishable/artifacts.py | 12 ++++----
 tests/test_cli.py            | 15 +++++++
 tests/test_validate.py       | 71 +++++++++++++++++++++++++++++++
```

The section's *conclusions* are unaffected — the `src/` change is a docstring and the test
changes are additions — but the sentence as written is a falsified build claim inside a section
whose whole point is that build claims are dated and checkable. The deeper defect is pinning a
dated claim to **`HEAD`**, a moving reference: feasibility procedure step 10 requires a sha.
**Repair: one clause — name the sha the check was run against, and state what the two later
commits touched (a docstring and added tests).**

---

## Anything new and wrong

Four items, all documentation, all one clause each: **N1**, **N2** and **N4** are false
sentences; **N3** is a docstring claiming a guarantee its assertions do not provide. All four
are the class this branch hit repeatedly, and three of them were introduced by the commit whose
job was closing findings of exactly that class.

Two count/positional nits, reported and not promoted:

- `CLAUDE.md`'s Format row now says *"the 39 currently-unformatted Python files."* The number is
  **true today** (verified above), but it is a count phrase that goes stale on the next
  formatting change, and nothing maintains it. The self-maintaining form — *"the
  currently-unformatted Python files"* — carries the same warning with no expiry, which is the
  repo's own stated preference for a statement that derives over one that enumerates.
- `reference.md:489`'s *"the family `E-DATA-ASSIGN-VARIES` names above"* locates a row partly by
  position, but it names the sibling by code and anchor-links the table, so position is
  decoration rather than the locator. Not a finding.

## Consistency passes

**Mechanical** over the four documents plus the feasibility analysis (fenced blocks skipped):
no duplicate heading anchors, no broken relative link, no table row whose column count differs
from its header, no empty table row, no trailing whitespace, no tab, no invisible unicode. The
18 `#anchor` hits are the known naive-slugger false positives on headings containing `&`, `/`
or an em dash (`#secrets--credentials`, `#allocationjson--who-went-where`,
`#e6--compiled-program-transfer`, …) — each checked by hand against its heading; GitHub's
slugger keeps the doubled hyphen and all 18 resolve. Every anchor the new rows introduce
(`#errors-validate-reports`, `#what-isnt-a-repeat`) resolves.

**Cross-document, config completeness:** satisfied — see I4. `holdout`'s five keys now appear in
§ The one config file and match `envelope.py` exactly. No `run.yaml` example is invalidated: the
fence shows the block's expansion inside a comment, and `holdout: null` — the value `init`
materializes — is unchanged.

## Ready to merge?

**After four one-clause documentation repairs — N1, N2, N4, N3 — yes.** Nothing here is a code
defect, a wrong number, a test that cannot fail, or an unpinned invariant; I3's mutation is
confirmed closed and I2's tests are confirmed falsifiable. But N1, N2 and N4 are false claims in
normative and dated text, and this repo's own standard is that a wrong claim is worse than an
omitted one — the review's "Blocks merge: no" verdicts were all about *missing* rows, and that
calibration should not carry over to rows that assert something untrue.
