# Batch 6 review — tasks 9, 10, 11: `diff`'s apparatus row, exit code and config side, upstream block and CLI arm

Reviewed 2026-08-21 against `h8b-diff-freeze` at `f138536`, in a clean worktree. Grading on the
scale batches 1–5 used: **PASS with findings** means every finding closes in a fix round without
re-opening a decision.

## Verdicts

- **Spec compliance: PASS with findings.** Decisions 2, 4, 5 and 6 are all built as ruled, and I
  verified each **by running the real command** — every shape below came out of
  `main(["diff", …])`, not a direct call. The findings are two unpinned ruled behaviours, one false
  comment, and document/prose defects; none contradicts a decision.
- **Task quality: PASS with findings.** The report's one claim that "deserves scrutiny" survived
  verification (Decision 4 *was* already the code's shape, and its pins are real — mutation-proved).
  Four Majors: three ruled behaviours are mutation-blind (the CLI arm, Decision 2's third
  sub-ruling, the upstream block's `not captured` render), and Fixture U carries a comment asserting
  a relaxation that did not ship — one that licenses the very edit destroying its discriminating
  half.

## Gates — reproduced myself, not read

`uv run ruff check .` clean · `uv run ruff format --check .` → **88 files** · `uv run mypy` →
**49 source files** clean · `uv run pytest` → **2623 passed, 1 skipped, 2 xfailed** (158 s). Run
before any mutation and again after every revert; both runs identical. **Tree left clean**
(`git status --porcelain` empty; `src/publishable/diff.py` and `src/publishable/cli.py` diffed
byte-identical against pre-mutation copies, never `git checkout`).

---

## Findings

### Major 1 — `diff`'s CLI arm is entirely unpinned; a weakened guard leaves the suite green

`src/publishable/cli.py:3753-3756`. **Verified by mutation.** No shipped test invokes
`main(["diff", …])` with anything but `test_reference_cli_tables_match_what_the_cli_does`'s two
valid-arity junk positionals (`tests/test_cli.py:9248`, where the call is *constructed* from the
table row rather than written literally — a grep for `main(["diff"` misses it, which is the
one-spelling proxy this repo tracks). Every new test in `tests/test_diff.py` calls `command_diff`
directly. Replacing the guard

```python
if len(rest) != 2 or any(p.startswith("-") for p in rest):
```

with `if len(rest) < 1:` — dropping both the arity rule and the flag rejection — left the **full
suite at 2623 passed, 1 skipped, 2 xfailed**. So task 11 step 4's whole prescription (exactly two
paths, no flags, the message `` `diff` takes exactly two paths and no flags ``, `EXIT_INVOCATION`) is
unpinned, and the guard is additionally load-bearing against a traceback: without it
`main(["diff", p])` reaches `Path(rest[1])` and raises `IndexError`.

`test_reference_cli_tables_match_what_the_cli_does` cannot see this: it probes with **two** junk
positionals (valid arity) and its built-row branch asserts only two *absences* of stderr text
(`tests/test_cli.py:9256-9258`), no exit code. The report's evidence for the arm is a single prose
probe (`main(["diff", "_probe_a", "_probe_b"])` → `E-IO-FAILED`) — precisely `CLAUDE.md`'s *reading a
subprocess probe as a pin* row, named there as having shipped unpinned five times in three slices.
I confirmed all four invocation shapes behave correctly today by running them (1 path, 3 paths,
leading `-`, 0 paths → exit 2 with the documented message); the defect is that nothing holds them
there.

### Major 2 — Decision 2's third sub-ruling has no fixture, and the mutation is blind

`src/publishable/diff.py:253-257`. Decision 2, the design's own third sub-ruling and task 9's brief
step 3 all require that *a condition key present in one side's `facts` and not the other gets its own
line rather than being skipped*. The code implements it; **nothing tests it.** `grep -rn "no
apparatus recorded for" tests/` returns nothing. **Verified by mutation:** replacing the branch with a
bare `continue` (skip the condition) left the **full suite at 2623 passed**. A1 puts both conditions
on both sides, A2's one-sided arm exercises a `null` `provenance.apparatus` — a *different* branch in
`_render_apparatus_row` — and the key-reorder test compares hashes. No fixture makes the two
condition-key sets differ. This is `CLAUDE.md`'s *a seam named in the brief and instantiated by no
fixture*. I confirmed the behaviour is correct today by a direct `_render_row` call on two hand-built
records: `  01_m=s  no apparatus recorded for B`.

Note while fixing it: that message near-collides with the one-sided message — `no apparatus recorded
for B` (a condition missing from B's `facts`) versus `B recorded no apparatus` (B has no apparatus
block at all). Different states, near-identical words, neither separable by grep.

### Major 3 — Fixture U's section comment licenses the edit that would destroy its discriminating half

`tests/test_diff.py:918-921`:

> `# Only `uv.lock` is `not captured` on both sides (no lockfile committed) rather than literally`
> `# `identical` — a deliberate, reported relaxation; see the batch report.`

**The comment invites a reader to relax the one assertion Fixture U exists for** — the five
`identical`s that prove the upstream block carries information no row does — and it cites the batch
report as authority for doing so. **Verified false three ways.** The test 130 lines below commits a real `uv.lock`, asserts
`run_x_yaml["provenance"]["environment"]["uv_lock_hash"] is not None`, asserts `"not captured" not in
out`, and asserts `identical` for **every** `ROW_LABELS` entry. The batch report says the opposite in
its own words (*"Fixture U had to be built with a genuinely non-null `uv.lock`"*). And I ran the
fixture: all five rows print `identical`. So the comment is a leftover from an earlier attempt that
now points a reader at a disclosure the report does not contain — and it licenses exactly the edit
that would destroy the fixture's discriminating half. `CLAUDE.md`: *prefer deleting a claim to
rewriting it.*

### Major 4 — the upstream block's `not captured` render is unreachable from any fixture

`src/publishable/diff.py:_upstream_hash_repr`. Task 11 step 3 and § Corrections correction 7
prescribe it: an upstream entry's `code_hash`/`parameters_hash` **can** be `None`
(`UpstreamLedger.record` copies them with `record.get(...)`), and printing `None…` would be
Decision 1's false-identity shape. The render is correct; **nothing reaches it.** Verified by
mutation: replacing the body with `return _truncated(value)` — which would raise `AttributeError` on
a `None` — leaves `tests/test_diff.py` at **41 passed**, and `diff` is tested in no other file
(`grep -rln "command_diff\|from publishable.diff" tests/` → `tests/test_diff.py` only). No fixture
builds an upstream entry with a missing hash; one hand-built record closes it. The open filing this
render deliberately does not dispose of is untouched and still names H9 — I confirmed it is present
and unstruck.

### Minor 1 — the `Does` cell's "five rows" is false in the common case

`docs/reference.md:3539` — *"then five rows … and an `upstream` block …, naming it when all five rows
agree despite it."* Decision 2 **omits** the apparatus row when both sides are `null`, which is every
`generic` pair and is what README § The loop you'll actually live in and `design-principles.md` § Same
code, different parameters both show. **Verified by running:** a `generic`-vs-`generic` pair prints
four rows, no `apparatus` line at all. The cell should say what the omission rule makes true.

### Minor 2 — a garbled sentence in the new § Operation commands paragraph

`docs/reference.md:3551-3552`: *"and a probe answering `apparatus` is not something `diff` is one of
[the four places](#the-apparatus-core-can-only-observe) that call one."* The clause does not parse.
The argument behind it (Decision 5's grounds) is right; the sentence needs rewriting.

### Minor 3 — § Exit codes still contradicts shipped behaviour (task 12's, recorded so it cannot be lost)

`docs/reference.md:3565`, the `1` row, still reads *"a `diff` of runs that don't share a hash"*.
**Verified by running:** `main(["diff", run_a, run_b])` with `parameters_hash DIFFERS` returns **0**.
Task 10's brief step 2 asked for the deletion; the implementer followed the controller and left it to
task 12. **That was the right call** — the controller outranks the brief, and the deletion belongs
with the rest of task 12's document work. But the branch now ships `diff` as `built` beside a
normative row that contradicts it, and **no test binds the two directions**, so task 12 must not lose
it.

### Minor 4 — the truncation claim stopped at the file its brief named

`src/publishable/diff.py:213-215` — `_truncated`'s docstring: *"the width all three worked outputs
show"*. Two of the three show `sha256:8e21…`; `docs/design-principles.md:119-121` still shows
`sha256:8e21...` (ASCII). Task 9 changed `reference.md`'s `...` → `…` on the explicit ground that a
line copied from a document must match a line the function prints, and did not sweep the third
document. `CLAUDE.md`: *sweep for the claim, not for the file the claim was first noticed in.*

### Minor 5 — the `not captured`/`not comparable` control is one-directional

`test_h8b_run_vs_run_control_never_prints_not_comparable` exists; the converse —
a config side never prints `not captured`, which `_render_parameters_hash_mixed`'s docstring claims
in full ("has no reachable case here") — is asserted nowhere. **Verified true by running** a
config-vs-run pair: no `not captured` in the output. One `assert "not captured" not in out` in either
existing config-side test closes it.

### Minor 6 — nothing asserts `apparatus` prints **fourth** in real output

The emitted-order pin's literal now covers four labels; position is pinned by the `ROW_LABELS ==`
literal and by the `reference.md` sequence-equality test, and the emitted-order half still
discriminates — **verified by mutation:** `for row in reversed(ROW_LABELS)` in `command_diff` fails
`test_h8b_row_order_is_pinned` at its emitted-list assertion (`tests/test_diff.py:520`), not at the
constant assertion. So this is a gap rather than a hole: Fixture U already renders all five rows and
could carry the ordered assertion for free. **Verified by running** that the real order is
`code_hash, input_manifest, uv.lock, apparatus, parameters_hash`.

### Minor 7 — one report claim is not about the same thing as its evidence

Report § Gates: *"no shipped test other than the two named CLI-table tests changed outcome"* —
implying those two changed outcome. They did not: both passed before the flip (arm absent, document
`NOT BUILT`, constant key present) and after (arm present, document `built`, key removed). What
changed is which **branch** each exercises, which is what the report's own task-11 section says two
paragraphs earlier. Small, but it is the fourth consecutive batch with a claim and an evidence
sentence about different things.

### Minor 8 — the closing config-count claim is reasoned, not measured

Report's last paragraph: *"the table stays 8 of 8 · 0 · 7 · 1, unchanged by any of the three tasks."*
I checked the four numbers against `docs/feasibility-llm-growth-studies.md` § Executability's H8a
entry — **they are that table's, exactly**, and no fifth number is minted. But § Executability is
task 12's, the batch ran no measurement, and the review brief asked for no config-count claim. Keep
the "H8b moves no count" expectation; drop the restated table until task 12 measures it.

### Minor 9 — `_render_apparatus_row`'s `letter_a`/`letter_b` parameters have no caller

`src/publishable/diff.py:280-282`. `_render_row` calls `_render_apparatus_row(record_a, record_b)`;
the two letter parameters exist only as their own defaults (`grep -rn "_render_apparatus_row"
src/ tests/` → one definition, one call). Declarable and unread, the shape `CLAUDE.md`'s
unbuilt-reader row tracks — either thread the letters from the caller or drop the parameters.

### Minor 10 — the M2 fixture's per-condition reorder is a no-op

`test_h8b_apparatus_identical_survives_a_facts_key_reorder` reverses both the condition mapping and
each condition's fact mapping, and its comment describes "one record's `facts` mapping re-serialized
in a different key order". Each condition holds exactly **one** fact (`calibration_id`), so
`dict(reversed(list(fact_map.items())))` changes nothing; only the outer two-condition reversal does
work. The fixture still discriminates M2 through that outer reversal — the `or` in its own guard is
what keeps it honest — but the inner half is decoration, and a reader may take it for coverage of
per-fact ordering that does not exist.

### Minor 11 — `apparatus DIFFERS` fires on a `null → value` transition the gate deliberately permits

**Verified by running**, with a probe answering `None` in run A and `CAL-X` in run B:

```
apparatus          DIFFERS
  00_model=m1.calibration_id  null → CAL-X
```

`reference.md` § The apparatus core can only observe says of exactly that transition: *"Neither is
evidence the apparatus moved."* `diff` reports observations rather than gate verdicts, so this is
defensible as built — but **no decision, document sentence or filing says so**, and a reader who
knows the gate's rule will read `DIFFERS` as the gate's change. Worth a sentence somewhere, or a
filing.

### Minor 12 — an empty-string fact value renders as nothing

**Verified by running** (probe answering `""`): `  00_model=m1.calibration_id   → CAL-X`. `null` gets
the word `null` and an absent key gets `(absent)`, but `_render_leaf("")` returns the empty string,
so an empty value is visually indistinguishable from a missing left operand — the same
false-appearance class Decision 1's `not captured` exists to prevent.

---

## What I verified by running, and found sound

- **Decision 4, all three outcomes through `main`.** Rendered-with-differences → **0** (with
  `parameters_hash DIFFERS` and its delta line present); rendered-identical → **0**;
  could-not-render → **1**, both flavours (`E-IO-FAILED` for a missing path, two
  `E-UPSTREAM-RECORD-MISSING` findings for two empty directories in one run).
- **The exit pins are real, and the report's "already the shape from task 8" claim survives.**
  Mutating `command_diff`'s return to `EXIT_WRONG` when any rendered line contains `DIFFERS` fails
  **seven named tests on assertions**, including `test_h8b_config_vs_config_same_shape` at
  `assert code == EXIT_OK` (`assert 1 == 0`) and `test_h8b_fixture_r2_the_documented_payoff`. Not a
  collection error, not a proxy — the mutation sits at the return.
- **The `ROW_LABELS` edit is one label in its documented position with nothing reordered** (fourth,
  before `parameters_hash`; diff-verified), and the report's reasoning for leaving the emitted-order
  literal at four labels **checks out**: `run_a_project` uses template `generic`, both sides record
  `apparatus: null`, and the row is omitted — confirmed by running that pair and finding no
  `apparatus` line.
- **Both doc-agreement inversions are inversions, not loosenings.** The README/design-principles arm
  is still full equality (against `ROW_LABELS` minus `apparatus`) and still fails on a renamed label
  or an added row; the `reference.md` arm went from `"apparatus" in labels` plus filtered equality to
  **full sequence equality**, which is strictly stronger and now pins position too. One note for the
  record: task 9 step 10 authorized *one* edit (the row-order assertion) and **three** tests moved,
  one of them renamed. Task 8's own docstring anticipated it and the report discloses it, so this is
  a scope note, not a finding.
- **Decision 2, all four shapes, through `main` with a real installed probe plugin.** `DIFFERS` with
  **two** condition-qualified detail lines; `identical` with its digest and no detail; one-sided
  `DIFFERS` naming the right side in **both** operand orders (`B recorded no apparatus` /
  `A recorded no apparatus`); both-null **omitted** entirely. Verdict from `.hash`, details from
  `.facts`, as ruled.
- **`not captured` and `not comparable` are different words on different paths, and the fixtures say
  so.** Config side: `parameters_hash` computed (`DIFFERS` with real delta lines) and the other four
  `not comparable` with their reasons verbatim; run-vs-run control asserts `not comparable` nowhere;
  the unparseable-config third path renders neither word and exits 1. All confirmed by running.
- **Fixture U is honest, not over-fitted.** The design's own Fixture U demands *"the five rows must
  all read `identical`"*, and the looser gate would print "these runs differ only in their upstreams"
  over a pair whose lockfile was never captured — Decision 1's named cost-if-wrong. The mechanism is
  the right one: an environment variable the starter step reads at call time (so `code_hash` cannot
  move), a real committed lockfile established before either compared run, and `<output_dir>/latest`
  rather than a glob. Keep it.
- **`entry['run_id']`'s direct index is safe** — `UpstreamLedger.record` does `record["run_id"]` on
  the write side, so an entry without it cannot exist; only the two hashes are `.get`-copied, and
  both render `not captured`.
- **A config side that parses to a mapping but is not a config does not crash** — `parameters_hash`
  over `{}`, `{"a": 1}`, `{"parameters": "notamapping"}` all return a digest.
- **Scope.** Only `docs/reference.md` moved among the four documents (the apparatus fence, the
  `Status` and `Does` cells, the new § Operation commands paragraph) — all in scope for tasks 9-11.
  `E-DIFF-CONFIG-UNREADABLE` appears in **no** document, correctly left to task 12's § Errors.
  `tests/test_cli.py` is untouched, so task 13's guard-pin arms are intact. No positional locators,
  no `x`-for-`×` in the new prose.
- **Mechanical pass on the changed document region.** Both new anchors resolve; no trailing
  whitespace, tab or invisible unicode on any added line; and the apparatus fence's alignment matches
  the emitter character for character — label padded to 19, `identical` padded to 13, and the detail
  qualifiers padded to the longest-in-batch plus two (33 → 35, so 9 spaces after the 26-character
  qualifier and 2 after the 33-character one).

## What I could not check

- Whether task 12 actually lands the § Exit codes deletion, the § Errors rows and the § Executability
  re-measurement — out of this batch by the controller's own ruling; Minor 3 exists so the first of
  those cannot be lost.
- **M2 and M3 I did not re-run.** Both were verified by inspection instead: M3 (dropping the
  condition qualifier) fails Fixture A1's *second* assertion — `len(detail_lines) == 2` still passes
  and then `startswith(condition + ".")` finds zero — and M2's outer two-condition reversal is a
  genuine reorder, so a `json.dumps` without `sort_keys` differs there. Both discriminate; I spent
  the suite runs on the blindness claims instead, where a green suite is the only proof.
- Whether the `draft` label is right for a **genuine** draft run. `draft` is H9's; the pin is against
  a hand-set `draft: true` on a real record, which the report discloses and which is the most this
  batch could do.
