# Task 15 (batch 8) review: `generate report`, and the table-parser assertion its Status flip moves

Reviewed `51fb7cb` (code) and `37a8f68` (report), against
`docs/superpowers/specs/2026-08-21-report-study-design.md` Decisions 2 and 17,
`docs/superpowers/plans/2026-08-21-report-study.md` § Corrections 3, and `task-15-brief.md`.

## Verdicts

**Spec compliance: PASS, with two document filings and one family-wide filing.** Decision 2's grounds
(`format` has no base default; `generate report` always writes the line) are true of the shipped class
and of both generator arms, verified by importing the generated file rather than reading it. Decision
17's four requirements hold: the class is written, `package_name`/`E-EXPERIMENT-UNKNOWN` are reused
rather than reinvented, `E-REPORT-EXISTS` joins the `E-*-EXISTS` family with its § Errors row in the
raising commit, and the scaffolded body renders all four standard sections through real discovery.
Correction 3's post-edit state matches exactly, and the edited assertion is proven able to fail. The
one substantive hole — `--format` interpolated verbatim into a Python string literal — turned out to be
**a family-wide, pre-existing defect class rather than this task's** (see Major 1 and Minor 1), which
is why this is a PASS with a filing rather than a FAIL.

**Task quality: PASS, with reservations.** No pin on this branch is one that cannot fail: I ran the
non-degenerate form of the prescribed exists-check mutation, a bogus-status mutation against the
edited table assertion, and an inversion of the discovery callback's vacuity guard, and each fired on
the right assertion. Reverts were verified by behaviour *and* by byte-diff. All four gates match the
brief's stated deltas. The reservations, in order of how close each came to a FAIL: the report flagged
`--format`'s unvalidated value as its one judgement call and adjudicated it **from the `--input-dir`
precedent rather than by running it** — and `--input-dir` seeds YAML where this seeds a Python literal,
which is the whole of Major 1; the new docstring in `generate_report` routes that fault to a code it
does not reach; the arity justification is transferred from `generate template` and is false here; and
the mutation narrative understates its own evidence.

---

## Findings

### Major 1 — a user-supplied string is interpolated into generated Python with no escaping, family-wide. **Pre-existing, and not task 15's; unowned and unfiled**

Verified by running, all through `main(...)` in scaffolded projects:

- **`generate report`** (`src/publishable/generators/report.py:31`, `format = "{fmt}"` in `REPORT_PY`;
  written at `:66`): `--format 'ht"ml'` → exit `0`, file written, `compile()` →
  `SyntaxError: unterminated string literal (detected at line 6)`. `--format 'html\n    x = ('` →
  same. `--format 'x"\n    import os\n    os.system("echo PWNED_AT_IMPORT")  # '` → exit `0`, the file
  **compiles**, and the injected statement runs at import: the value reaches the class body, not only
  the literal.
- **`generate step`** (`src/publishable/generators/step.py:16`, `# TODO: implement {step_name}`, and
  `:41–46`, which rewrites `experiment.py`): `generate step cohort-pilot 'foo"bar'` → exit `0`; the
  step file itself compiles (the name lands in a comment) but **`src/cohort_pilot/experiment.py` no
  longer parses** — `SyntaxError: unterminated string literal` — because the name is interpolated into
  `from .steps.step02_foo"bar import Step as Foo"bar`. A newline-bearing name produces a file whose
  *name* spans three lines and the same corrupt `experiment.py`.

So the defect class is the family's, it predates this task, and `generate step`'s instance is strictly
worse: `generate report` writes one new file the user can delete, while `generate step` **corrupts an
existing file it did not create**, at exit `0`, with the pipeline's step order in it. The root cause is
the same absent guard I record under *Inherited* below — `package_name` is
`experiment.replace("-", "_")` and nothing validates a name or a flag value before it reaches a
`str.format` over a Python template. `generate template` is the one member with a guard
(`is_usable_name`).

**Filing needed**, owner nobody: either sanitize at the interpolation (`repr()` for a literal, a
bare-word check for an identifier) or extend `is_usable_name`-style validation across the family. One
line fixes `generate report`; `generate step` needs the guard before it rewrites `experiment.py`.
Graded Major on the branch because a generator silently writing non-parsing Python into `src/**` — the
tree `code_hash` covers — is a real defect; graded **not task 15's** because the identical class ships
in a sibling built several slices ago, and the rubric that puts the missing name guard under
*Inherited* has to put this there too.

### Minor 1 — task 15's own instance of Major 1, and a new docstring that routes it to the wrong code

`src/publishable/generators/report.py:47–53`: *"`fmt` is written verbatim, whatever it is … a class
declaring anything else is `report`'s own refusal to make (`E-REPORT-FORMAT`, at render)"*.

**Verified by running** `report <run.yaml>` against a real committed run: `--format pdf` →
`E-REPORT-FORMAT`, exit 1 — the claim holds for a value that parses. `--format 'ht"ml'` →
**`E-REPORT-OVERRIDE-IMPORT`**, exit 1, *"could not be imported: unterminated string literal"* — the
class declares no `format` at all, and *whatever it is* is false for that subset. This is the
*comment claiming a guarantee the code does not provide* row, and unlike Major 1 the sentence is new
in this commit, so it is this task's. Prefer fixing the interpolation, which makes the sentence true,
to rewriting the sentence.

Also this task's, and the reason the miss is a reservation rather than nothing: brief step 4 and
Decision 17 state *"the scaffolded body must be runnable as-is"* as **this generator's** requirement,
and the report's § Concerns raised exactly this surface and settled it on precedent. The two shipped
`--format` assertions use `"html"` and `"markdown"` only, so the property is unpinned at the one value
class that breaks it.

### Minor 2 — the arity justification is copied from `generate template` and is false for `generate report`

`src/publishable/cli.py:3997–4004` (the `if kind == "report":` comment), repeated verbatim in
`tests/test_cli.py:953`'s docstring and in the report's *What was built*: *"the CLI-table test probes
every built generator with two junk positionals inside this repository, so a generator that wrote
first would scaffold a report override into the working tree that a later `report` run would then
discover."*

**Verified by reading `test_reference_cli_tables_match_what_the_cli_does` (`tests/test_cli.py:9426`)
and by running:** the probe is `main(["generate", "report", "_probe_a", "_probe_b"])` with the cwd at
this repo, and `generate_report` refuses unless `src/_probe_a/` is an existing directory — it is not.
`generate report no-such-experiment` gives `E-EXPERIMENT-UNKNOWN`, exit 1, `src/` unchanged. A
write-first `generate report` would therefore scaffold nothing under that probe. The hazard is real
for `generate template`, which writes `templates/<name>.py` for any usable name, and does not
transfer. The arity check is right and worth keeping; the sentence justifying it is another
generator's. Prefer deleting the transferred clause to rewriting it.

### Minor 3 — the report's mutation-1 account answers from a proxy; the pin is stronger than it says

`task-b8-report.md` § Mutations, mutation 1, reports *"3 of 5 new tests failed … the other two
failures are collateral: this mutant makes `path.exists()` unconditionally true immediately after
every write"*, which leaves the refuse-before-write property looking as though nothing pins it alone.

**Verified by running the non-degenerate arm** — the prescribed swap is degenerate, so I built the one
that raises the right code at the right exit *and* overwrites:

```python
existed = path.exists()
resolved_fmt = fmt if fmt is not None else "markdown"
path.write_text(REPORT_PY.format(pkg=pkg, fmt=resolved_fmt))
if existed:
    raise ContractError(..., code="E-REPORT-EXISTS")
```

`uv run pytest tests/test_cli.py -k generate_report` → **1 failed, 4 passed**, the failure being
`test_generate_report_refuses_an_existing_file` on
`assert mine.read_text() == "# hand-written, and worth more than a stub\n"`. The bytes-changed
assertion **discriminates on its own**, so the property is pinned and there is no Major here; the
finding is against the report's account of its own evidence. Reverted by writing the pre-mutation copy
back, re-running (`5 passed`), and `diff` → identical.

### Minor 4 — pin asymmetry on the two arms Decision 2's grounds rest on

`tests/test_cli.py:890`, `test_generate_report_seeds_format_from_the_flag_and_markdown_when_omitted`.
The `--format html` arm `compile`/`exec`s the generated text and asserts `Report.format == "html"`;
the omitted-flag arm asserts only `'format = "markdown"' in text`. Decision 2's grounds are that every
generated class can be **observed** to take a value, and the default arm is where "observed" does the
work. **Verified by running** that the code is right — `exec`ing the default arm's text gives
`Report.format == 'markdown'`, and `hasattr(BaseReport, "format")` is `False`. Two added lines close
the pin.

### Minor 5 — the `E-EXPERIMENT-UNKNOWN` arm asserts the code but not the half that protects a repo

`tests/test_cli.py:983`, `test_generate_report_on_a_missing_package_is_e_experiment_unknown`, asserts
`"E-EXPERIMENT-UNKNOWN" in printed` and nothing about disk, where its three sibling refusal arms
(arity, exists, and `generate template`'s) all assert *and nothing reached disk*. **Verified by
running** that nothing is written: after the refusal `src/` lists exactly `['.gitkeep',
'cohort_pilot']`. A pin gap, not a code defect.

### Minor 6 — the new docstring's own sentence contradicts the assertions it describes

`tests/test_cli.py:9372`, `test_reference_cli_tables_are_parsed_at_all`: *"a parser returning `[]` for
a table still satisfies 'a subset of the valid statuses, non-empty' only if it finds at least one
row"*. A `[]` parse gives an empty `statuses` and fails `assert statuses, column` outright, so it
satisfies neither half — the premise is false and the conclusion does not follow. The four assertions
are correct; the sentence explaining them is not, and here a docstring is a claim.

### Minor 7 — § A report override's fenced block is labelled `— generated` and is no longer what the generator writes

`docs/reference.md:3777` onward. Its first line is `# src/cohort_pilot/report.py — generated`, the
exact line `REPORT_PY` emits, but the block also carries a second
`yield self.section("Method agreement", body=render_scatter(io.read_condition(...)))` against an
undefined `render_scatter`, and one blank line before `class` where the generated file has two.
**Verified by running** `generate report` and comparing bytes.

This is the commit that makes it a build claim: while the § Generators row read `NOT BUILT` the label
was aspirational, and Decision 17 rules the scaffold yields nothing but the `yield from` plus a `TODO`,
so the two are now *specified* to differ. Either the block loses `— generated` or the extra `yield`
gets a `# …and one you add:` marker. Task 16 owns § A report override's sweep; filing rather than
fixing here is defensible, but nothing is filed.

### Minor 8 — § Creation commands' `generate` args cell does not name `--format`

`docs/reference.md:3551`, Arguments cell: *"generator, name, generator args (`experiment` accepts
`--plugin`)"*. `report` is now built and accepts `--format`, so the parenthetical is no longer total
over the generators that take a flag. Task 15's brief forbade other edits to that cell and task 16
owns cross-cutting document work — a filing with an owner, but no filing exists.

### Minor 9 (low) — the new § Errors row locates its sibling by position

`docs/reference.md:583`: *"for the same reason as `study new`'s row above"*. It names the sibling,
which is the prescribed form; `above` is the positional garnish `CLAUDE.md` counts wrong twice. Drop
the word.

---

## What held, verified rather than read

- **Attack 4 — the generated file resolves, and the guard against the fallback is live.**
  `render_with_override` (`src/publishable/report.py:832`) calls `render(...)` **outside** every
  `except` — the only `try` wraps `importlib.import_module` — so an `AssertionError` inside the
  callback propagates rather than becoming `E-REPORT-OVERRIDE-RAISED`. **Verified by inverting** the
  callback's `assert cls is not None` to `assert cls is None` against a real committed run:
  `pytest.raises(AssertionError)` catches it. The shipped arm therefore does distinguish the resolved
  `cohort_pilot.report.Report` from the no-override fallback, which renders the identical four
  sections, and its `titles == ["Conditions", "Deltas", "Hypothesis verdicts", "Attrition"]` is an
  exact ordered list.
- **Attack 2 — correction 3's edit, diffed from git, and proven able to fail twice.**
  `git show 51fb7cb -- tests/test_cli.py`: the per-table assertion became `assert statuses, column`
  plus `assert statuses <= {"built", "NOT BUILT"}, column`; the Generator row-presence pair
  `("report", "built")` / `("template", "built")` was added mirroring the Command table's; and the two
  `== set(NOT_BUILT_COMMANDS)` / `== set(NOT_BUILT_GENERATORS)` lines are **untouched** —
  `git show --numstat` gives 3 deletions across the whole file, which are the two docstring lines and
  the one replaced assertion, so no other shipped test moved. Not weaker in either direction I could
  reach: editing § Generators' `report` cell back to `NOT BUILT` fails the test on the
  `NOT_BUILT_GENERATORS` set-equality (and fails `…match_what_the_cli_does[Generator]` with it), and
  editing that cell to a **bogus** status (`shipped`) fails on **line 9392, the new subset assertion
  itself**, reporting `Extra items in the left set: 'shipped'` — the parser passes `cell[1]` through
  verbatim, so the assertion task 15 wrote is reachable rather than shadowed by its neighbours. Both
  mutations reverted by editing the cell back; `diff` against pre-mutation copies → identical.
  **One property genuinely left, with a route:** *both statuses present in the Command table* was
  implied by the old set-equality and is now carried only by the two hard-coded Command rows, so
  whoever builds `dry-run` takes it with them when they edit that line. A consequence of a prescribed
  edit, not a defect in this task.
- **Attack 3 — both `format` arms write the line**, verified by importing rather than reading:
  `--format html` → `Report.format == 'html'`, flag omitted → `'markdown'`, and
  `hasattr(BaseReport, "format")` → `False`.
- **Attack 5 — refusal paths leave nothing partial.** Verified by running, each in a scaffolded
  project: arity (`_probe_a _probe_b`, and bare `generate report`) → exit 2, exact stderr, no file;
  `E-REPORT-EXISTS` → exit 1, hand-written bytes intact; missing package → exit 1
  `E-EXPERIMENT-UNKNOWN`, `src/` unchanged; **unwritable package directory** (`chmod 500`) → exit 1
  `E-IO-FAILED` with the *"filesystem refused this operation"* diagnostic, no traceback, and the
  directory listing unchanged — byte-for-byte the same handling `generate template` gives under the
  same `chmod`, so that behaviour is the family's rather than invented here.
- **Attack 6, adjudicated — deferring the *enum* check is right; deferring *syntactic* integrity is
  not.** § A report override states *"`generate report`'s `--format` writes that attribute and does
  nothing else — the class is the source of truth from then on"*, and `E-REPORT-FORMAT`'s § Errors row
  owns the invalid-value refusal at render; verified by running that this routing works
  (`--format pdf` → `E-REPORT-FORMAT`). A second enum check at generate time would be a second source
  of truth for one rule, over a file that is the user's from the moment it is written. **The deferral
  is correct.** What cannot be deferred is that the file the generator writes parses — that is not a
  judgement about the value's meaning but the generator keeping its own promise, which is why the
  escaping question lands under Major 1/Minor 1 and not against the deferral.
- **Attack 7 — the scaffold's comments, each checked against shipped code.** `# TODO: yield
  self.section("<title>", body=...)` matches `BaseReport.section(self, title, *, body)`
  (`src/publishable/report.py:493`). `yield from super().sections(run, io)  # the standard blocks, in
  order` matches `BaseReport.sections`, which yields exactly the four in Decision 5's order. `# html |
  markdown` is total over the two values § Errors and the render-time check define. `from publishable
  import BaseReport` satisfies the one-import-root invariant — `BaseReport` is in
  `publishable.__all__`, not merely importable. `REPORT_PY`'s preamble comment about no base default
  is true of both the class and the generator. The two comment defects are Minor 1 (the routing claim)
  and Minor 2 (the transferred arity hazard).
- **Attack 8 — every new substring assertion checked against what else the file contains.**
  `'format = "html"'` / `'format = "markdown"'` cannot be produced by the trailing `# html | markdown`
  comment or any other line, and the `html` arm additionally asserts the executed class attribute.
  `"src/cohort_pilot/report.py" in printed` on the exists arm is carried by the raise's own message and
  by no diagnostic envelope. The arity arm asserts **exact** stderr equality; the four-sections arm an
  exact ordered list. Nothing I found is satisfiable by neighbouring output — batch 6's shape does not
  recur here.
- **Attack 9 — prose and pins.** `grep -rn "E-REPORT-EXISTS" src/ tests/ docs/` (files named, output
  unfiltered): exactly one raise site (`generators/report.py:63`), one test assertion, and three
  document mentions — its § Errors row, § Generators' cell, and § Exit codes' creation-command
  enumeration — so the row is not narrower than the code, the repeat offender on both preceding
  sub-slices. The row and the enumeration sentence land in the raising commit, as deviation (b)
  requires. No count phrase, no `x`-for-`×` in the added text, one positional locator (Minor 9), no
  config-count claim anywhere in the commit or the report. **Arm D did not fire and was not edited:**
  it lives in `tests/test_diff.py`, which `51fb7cb` does not touch (`git show --numstat`: four files,
  none of them that one), and `uv run pytest tests/test_diff.py` → 51 passed.
- **Mechanical pass on `docs/reference.md`**, a throwaway script over the whole file: the two anchors
  the new row introduces (`#generators`, `#three-hashes`) resolve against the computed heading slugs;
  both edited table rows carry their tables' pipe counts (2-column § Errors row → 3 pipes; 4-column
  § Generators row → 5; the § Creation commands row's 8 include three escaped `\|`); zero lines in the
  file carry trailing whitespace or a tab.

## Inherited, and deliberately not graded against this task

Each verified by running both `generate report` and a sibling, and each identical:

- **Unknown flags silently swallowed.** `generate report cohort-pilot --formt html` → exit 0, file
  written with the `markdown` default, no diagnostic; `generate template my_assay --nope x` → exit 0,
  file written. `_dispatch_generate`'s documented behaviour (*"Unrecognized options are silently
  accepted into `opts` and then silently dropped"*), pre-existing and family-wide.
- **`--format=html` (equals form) → bare exit 2 with no message**, the parser consuming the next token
  as a value and finding none. Pre-existing parser shape.
- **No name guard on `<experiment>`.** `../evil`, `a/b` and `cohort pilot` all reach `package_name`
  unchanged and produce `E-EXPERIMENT-UNKNOWN` at `src/../evil/`, `src/a/b/`, `src/cohort pilot/`.
  `pkg_dir.is_dir()` bounds the blast radius to directories that already exist, and `generate step`
  reuses the same helper with the same absence of a guard. This is the same root cause as Major 1 and
  should be filed with it.

## Gates, run in the foreground after clearing `__pycache__` and `pytest-of-*`

| Gate | Result | Expected |
|---|---|---|
| `uv run ruff check .` | All checks passed! | clean |
| `uv run ruff format --check .` | 93 files already formatted | 93 |
| `uv run mypy` | Success: no issues found in 52 source files | 52 |
| `uv run pytest` | 2828 passed, 1 skipped, 2 xfailed (182.25s) | 2828 · 1 · 2 |

## What I could not check

- Whether § A report override's block should lose its `— generated` label or mark the extra `yield`
  (Minor 7) — a document decision for task 16, not something running anything settles.
- Nothing else. The `--format` payloads were driven through `main(argv)`, which is the boundary the
  generator's contract is written over, so a shell's own quoting is above the surface under review
  rather than an unverified layer beneath it.

## Tree state

**Clean.** Three mutations were taken — the non-degenerate exists-check swap in
`src/publishable/generators/report.py`, and two `Status`-cell edits in `docs/reference.md`
(`NOT BUILT`, then the bogus `shipped`) — each against a copy, each reverted by writing the copy back
or editing the cell back, each verified by re-running the affected selection **and** by `diff` against
the pre-mutation copy (identical every time). No `git checkout --` was used. The scratch probe file
`tests/test_zz_b8_probe.py` was deleted. `git status --short` shows only this review file as
untracked; the full suite above ran against the reverted tree.
