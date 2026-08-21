# Batch 5 (tasks 8-9) review — `report <run.yaml>` end to end, and the draft refusal

Reviewed at `96b7060` on `h8c-report-study`. Gates re-run in the foreground before anything else:
`ruff check .` clean, `ruff format --check .` **90 files**, `mypy` **50 source files**,
`uv run pytest` **2746 passed, 1 skipped, 2 xfailed** — every number matching the report's own.
Stale `pytest-of-*` and `__pycache__` cleared first. **Every claim marked *verified by running* was
produced by my own fixtures through the real command** — the console script
(`uv run publishable report …`) for anything where a traceback or a stream matters, `main([...])`
for exit codes — never by calling `command_report`. Mutations were applied by editing the file,
reverted by restoring a scratchpad copy, and each revert verified **by behaviour** (re-running the
probe that the mutation changed), never by `git status` and never with `git checkout --`.

## Verdicts

- **Spec compliance: FAIL**, on two grounds, both verified by running; everything else in the
  batch's scope is compliant.
  1. **Plan § Corrections correction 7 does not hold end to end.** `report` prints a declared
     credential's value verbatim to stderr — finding **Critical 1**. The redaction the correction
     ruled is wired for the *render* fault and absent from a fault the same function's own new code
     introduces one line earlier.
  2. **Decision 6's "`2` only for an invocation fault" is violated, and the interim diagnostic
     contradicts the `Status` cell flipped in the same commit** — finding **Major 1**.
  Verified compliant, by running: Decision 1 (form by file name; `E-REPORT-FORM` at exit 1 through
  `main`); Decision 6's three status arms (`completed`, `partial`, `failed` each exit **0** at the
  console script over my own runs — a genuinely `partial` record and a genuinely `failed` one, built
  by a step that fails after the second repeat and by one that always fails); Decision 7 in full
  (exit 1, **stdout byte-empty**, **no file created or modified anywhere under the project or the
  output tree** — snapshotted before/after — and the override, which I made raise with the
  credential in it, never ran, proving the check precedes it); Decision 16's medium selection (an
  `format = "html"` override prints a self-contained page at exit 0 through the console script);
  correction 5's one-commit rule (`65207c1` carries arm, constant key and `Status` cell together);
  correction 6 (both new codes' § Errors rows land in the commit that raises them, in correct
  alphabetical position); and consistency with `diff`'s Decision 4 — a read command's exit code
  reports whether it could read.
- **Task quality: FAIL — one Critical, three Majors, six Minors.** The batch's own reported work
  reproduces exactly: I re-ran M5's shape (return non-zero on a `failed` record) and
  `test_fixture_f_a_wholly_failed_run_also_renders_at_exit_0` fails **on its assertion**
  (`assert 4 == 0`, `tests/test_report.py:1805`), not on a crash; the credential redaction of a
  render-time raise works and its positive control leaks when unwired. The Critical is the same
  leak class the batch was explicitly asked to close, reached by a route no brief named and no test
  touches. Arm D did **not** fire (`tests/test_diff.py` untouched; its arms pass).

## Findings

### Critical 1 — a declared credential reaches stderr verbatim from `report`, through `get_template` outside every `try`

`src/publishable/report.py:1074-1075` (`template = get_template(name, repo_root)` and the
`declared_credential_names_for` call on the next line).

`command_report` resolves the template **before** `credentials` exists and **outside any
`except`**, so a project-local template that raises while importing escapes `command_report`
entirely into `cli.main`'s bare `except PublishableError` — the handler
`docs/superpowers/spec-defects.md` files as *"prints an exception un-redacted, by construction"*,
and the same handler H7b Part A's leak and H7d Part A batch 3's leak both reached. This is the
fourth instance of that class and the second in which the fix closed one call site rather than the
shape.

**Verified by running**, with a positive control:
- Built a project whose **project-local** template declares
  `required_env = ["PUBLISHABLE_TEST_REPORT_CRED"]`, ran it green, then made the template module's
  top level raise *after* its `@register_template` call, carrying the credential's value.
- `uv run publishable report <run.yaml>` → exit 1, stderr:
  `error   E-TEMPLATE-LOAD  … RuntimeError('template top level boom, carrying sekrit-probe-h8c-b5-XYZ123')`
  — **the sentinel verbatim**.
- **Positive control on the same project, same raise, same shell:** `uv run publishable validate
  <config>` prints the identical message with `<redacted:PUBLISHABLE_TEST_REPORT_CRED>`. So the
  mechanism exists, the promise is live, and `report` is the surface that drops it.
- It is *not* inside `reference.md` § Secrets & credentials' two carve-outs: the raise is after
  registration, so a class survives to read `required_env` off, which is the case that section says
  **is** covered — *"a file that raises after that call … still leaves a class core can read
  `required_env` off, and that declared set is redacted into the `E-TEMPLATE-LOAD` /
  `E-TEMPLATE-COLLISION` finding itself."*

**The precedent cited as the recipe already solves this.** `src/publishable/freeze.py:219-231`
wraps its own template resolution in `try / except KeyboardInterrupt / except BaseException`, builds
the credential set from the exception's `partial_templates`, and refuses with a redacting
`Collector`. Task 8 copied the recipe's three *calls* and not its containment.

The batch report's claim — *"`main`'s own bare `except PublishableError` handler is never reached by
anything this function raises internally"* — is false, and it is the claim that would have caught
this. `E-TEMPLATE-COLLISION` and `E-TEMPLATE-UNKNOWN` leave by the same door.

**The fix is local to `report.py`, and I checked rather than assumed.** Swept every `get_template` /
`_claims` call site (`grep -n "get_template\|_claims(" src/publishable/*.py`): `validate.py:541` and
`freeze.py:220` resolve inside a `try` that refuses with a redacting collector; `cli.py:2001` and
`cli.py:2665` are unguarded but reasoned safe in writing — *"Cannot raise: `validate_config` already
made the same call and returned without error"* — and `command_run` really does validate first.
`command_report` **does not validate first**, which is exactly why it is the only caller where the
shape is live. So this is task 8's to close and needs no widening of the `spec-defects.md` entry's
owner.

### Major 1 — a built command tells the user the command is not built, at an exit code Decision 6 forbids

`src/publishable/report.py:1034-1037` (the bundle arm) and `src/publishable/cli.py:165-179`
(`_report_not_built`, whose own docstring scopes it to *"a specified-but-unbuilt **name**"*).

**Verified by running:** `uv run publishable report /tmp/bprobe/study.yaml` prints
`` `publishable report` is specified but not built in this version — see docs/reference.md § Building one ``
and exits **2**.

Two defects in one line:
- The sentence is **false as of this same commit**, which flipped § Operation commands' `report`
  row to `built`. The run form is built and the message says the command is not. Correction 5's
  authorization of this interim is explicitly for a subcommand *"still marked `NOT BUILT`"* —
  `study add` under task 11 — which is precisely what `report` no longer is.
- Exit **2** contradicts Decision 6: *"`report` exits `1` only for its own refusals and `2` only
  for an invocation fault."* A well-formed `study.yaml` path is not an invocation fault; a script
  keying on 2 now cannot tell "you typed it wrong" from "this form is not built yet".
- **Nothing can catch it**: `test_reference_cli_tables_match_what_the_cli_does`
  (`tests/test_cli.py:9287-9289`) asserts, for an unmarked row, that
  `"is specified but not built"` does **not** appear — but it probes
  `main(["report", "_probe_a", "_probe_b"])`, which the arity refusal answers first, so the one
  route that prints the forbidden sentence is unreachable from the test that forbids it. The
  batch's own pinning test asserts the sentence is **present**, i.e. it pins the defect.

- **The same function's docstring forbids what its own body does.**
  `src/publishable/report.py:968` states, of the exit codes: *"`2` is `main`'s own invocation-arity
  refusal, decided before this function is ever called."* The bundle arm at
  `src/publishable/report.py:1037` returns 2 from inside the function, sixty lines below that
  sentence. So the exit-code rule was written down and broken in one commit, which makes this the
  repo's most-weighted habit — a comment claiming a guarantee the code does not provide — in the
  same docstring as Minor 1.

Answering the dispatch's question directly: **no, `report <study.yaml>` does not report something
true today.** The honest interim is a bundle-specific diagnostic ("the bundle form of `report` is
not built in this version — see § Building one") at exit 1, with `_report_not_built` left to the
names it is actually about.

### Major 2 — a parseable-but-incomplete record gives a built command a raw traceback, where `diff` tolerates the identical file

`src/publishable/report.py:1077` calling `_report_io_from_record` (defined at
`src/publishable/report.py:927-947`), whose three subscripts `record["execution"]`,
`record["results"]["conditions"]` and `record["config"]["data"]["input_dir"]` are unguarded.

**Verified by running**, one real run's `run.yaml` with one top-level key removed each time, through
the console script:

| dropped key | `report` | `diff` over the same file |
|---|---|---|
| `results` | traceback, `KeyError: 'results'` | exit 0, renders its five rows |
| `execution` | traceback, `KeyError: 'execution'` | — |
| `config` | traceback, `KeyError: 'config'` | — |

Decision 15 rules that "a run record `report` cannot read" is the shipped `E-UPSTREAM-RECORD-*`
family, and a traceback out of a built command is the fault class this project keeps filing — the
same one the batch's own bundle-arm reasoning cites to justify not raising `NotImplementedError`.
It is also internally inconsistent: eight lines above, the same function reads `config`
defensively (`doc if isinstance(doc, Mapping) else {}`) for the credential lookup and then requires
it here.

### Major 3 — the fresh-`KeyboardInterrupt` guard is correct and pinned by nothing

`src/publishable/report.py:1084-1085`.

- **Shipped behaviour verified by running:** an override whose `sections()` raises
  `KeyboardInterrupt("ctrl-c carrying <sentinel>")` gives exit 130 and a traceback ending in a bare
  `KeyboardInterrupt` — **no sentinel** on either stream.
- **Mutation:** `raise KeyboardInterrupt from None` → bare `raise`. **Full suite: 2746 passed, 1
  skipped, 2 xfailed — unchanged.** The same probe then printed
  `KeyboardInterrupt: ctrl-c carrying sekrit-probe-h8c-b5-XYZ123`. Reverted; probe re-run confirms
  the message is stripped again.

So the guard is load-bearing, its removal leaks a declared credential, and the suite is silent
about it. `CLAUDE.md` names this exact shape — *"Five times in three slices a correct fix shipped
unpinned. Verify by probe, then pin by mutation"* — and task 8's brief asked for the
`KeyboardInterrupt` behaviour explicitly. Nothing in `tests/test_report.py` mentions
`KeyboardInterrupt`.

### Minor 1 — the module docstring and the `_dispatch` comment both describe an import the code does not make

`src/publishable/report.py:6-13` — *"this module imports `cli._report_not_built` at module
scope"* — and `src/publishable/cli.py:3732-3734` — *"both `freeze.py` and `report.py` import a
`cli` name at module scope (`declared_credential_names`, `_report_not_built`)"*. The actual import
is **function-local**, inside `command_report` (`report.py:1035`); `freeze.py:32` really is module
scope, so the comment is right about one file and wrong about the other. The batch report repeats
the claim and certifies it with a grep over `cli.py`'s imports — which answers *is the reverse
direction absent*, not *does this module import at module scope*: the one-spelling-grep proxy
again.

**Verified by doing it:** I moved the import to module scope and deleted the local one — `import
publishable.report`, `import publishable.cli` and the command all work, no cycle. So the claim
carries no trap, which is why this is Minor rather than Major; the *reason* offered for the shape
is nonetheless describing a different file. Prefer deleting the paragraph to rewriting it.

### Minor 2 — `E-REPORT-BODY` is pinned at a proxy, against the brief's explicit instruction

`tests/test_report.py:1681-1690` calls `render_markdown` / `render_html` directly with a hand-built
`Section`. Task 8's brief: *"No assertion in this task may be made by calling `command_report`
directly … every assertion in this task goes through `main`."* The guard's real-command route is
unpinned. **Verified reachable by running**: an override yielding `self.section("bad", body=42)`
gives exit 1 and `error   E-REPORT-BODY …` on stderr, so the route works — it is the pin that is
missing. (I also confirmed the row's scoping claim: an override yielding a plain `dict` instead of
a `Section` gives `E-REPORT-OVERRIDE-RAISED`, `'dict' object has no attribute 'title'`, exit 1 —
contained, not a traceback. And a **mapping** body renders: `body={"alpha": 1, "beta": 2}` prints a
one-row table at exit 0.)

### Minor 3 — a positional row locator in a normative § Errors row, and it is wrong

`docs/reference.md:574` (`E-REPORT-OVERRIDE-RAISED`'s row): *"distinguished from every other
`E-REPORT-OVERRIDE-*` row **above**"*. `CLAUDE.md` bans locating a row by position, and the claim
is already false: the rows are alphabetical, so `E-REPORT-OVERRIDE-REPO` — a discovery fault — sits
**below** this one. Name what the sibling rows *do* ("from the discovery faults, which find and
import the class") instead.

### Minor 4 — no test renders a successful override through the command

Every `main(["report", …])` call in the suite is either the no-override path or a *failure* path;
`grep 'format = "html"' tests/test_report.py` → no hits. So Decision 16's medium selection is never
exercised at the surface that prints, and neither is the ordinary success path of an override that
composes with `yield from super().sections(...)`. **Verified working by running** (html page at
exit 0, markdown mapping-body at exit 0) — again a pin gap, not a bug, and the cheapest one in the
batch to close.

### Minor 5 — Decision 2's streaming benefit is not delivered now that printing is real

`command_report` does `text = render_with_override(...)` then `print(text)`, and both renderers
return `str`, so nothing reaches stdout until the last section is computed. Decision 2's stated
user-visible consequence — *"an override that yields a cheap section first and an expensive figure
last should print the cheap one first"* — is therefore false at the command. The renderers' `->
str` signature is batch 4's, but this batch is where the claim became checkable, and it is worth
either sizing the claim down or filing it rather than leaving the decision reading as delivered.

### Minor 6 — a credential an override renders into a section body reaches stdout, and this is the documented limit rather than a defect

**Verified by running:** an override yielding `body="token is " + os.environ[<declared name>]`
prints the value verbatim at exit 0. I am **not** grading this a Critical, against the dispatch's
blanket instruction, on primary-source grounds: `docs/reference.md` § Secrets & credentials states
that *"redaction runs only at the two constructions above — an exception's text becoming an
execution's `error` or a diagnostic's message"*, and that core *"does not scrub what a step
deliberately records"*. A rendered report body is the same deliberate write one surface over. What
is missing is only the sentence: that section enumerates two constructions and does not name a
rendered report among the things it does not cover, so the next reader has to re-derive it. One
sentence, or a filing.

## Checked and clean

- **Correction 5's flip, both directions.** `65207c1` carries the `OPERATION_COMMANDS` entry, the
  `NOT_BUILT_COMMANDS` deletion and the § Operation commands cell. `report a b` and
  `report --format html` both print `` `report` takes exactly one path and no flags `` at exit 2 —
  the one-path arm, no second enforcer.
- **The grep-scope claim, re-run with its scope widened.** `grep -rn '"validate", "run", "freeze"'`
  over `src` and `tests` hits only the definition (`cli.py:136`); `OPERATION_COMMANDS` is read in
  exactly one place (`cli.py:3725`) plus comments, so `report` joining it is a dispatch change and
  not a behaviour change; and prose sweeps over `README.md`,
  `docs/design-principles.md`, `docs/experimental-designs.md` and `docs/reference.md` **named
  individually** found no enumeration of the set that went stale. Hits under
  `docs/superpowers/` are the development record and were left alone. The implementer's claim
  holds and its scope is real.
- **Fixture P's and F's status strings are not vacuous.** The obvious way they could have been
  name-standing-in-for-fact is if the Attrition table said `failed` or `partial` on every render.
  **Verified by running**: a `completed` run's render contains neither string (it contains
  `completed`), a `partial` run's contains both `partial` and `failed`, and a `failed` run's
  contains `failed` and not `partial`. Fixture P also reads the condition and repeat labels back
  from the record and asserts the condition label non-empty first, which is the right shape.
- **Fixture R is instantiated, not merely named.** `test_fixture_r_is_shaped_the_way_this_task_needs`
  pins two conditions, a `score` metric, a `by.cohort` stratum and a one-sided `vs_baseline`, so
  the four-heading assertion reads a page with content in it. The three tests naming the page do
  read the page.
- **Fixture T's provenance is stated and its assertion pair is right** — `assert doc["draft"] is
  False` before flipping (a fixture is a claim too), then exit 1 **and** empty stdout. I added the
  stronger check it did not make: nothing on disk changes.
- **§ Errors rows.** `E-REPORT-BODY` and `E-REPORT-OVERRIDE-RAISED` in `65207c1`, `E-REPORT-DRAFT`
  in `f54c3e7` — each in the commit that raises it (correction 6). The nine `E-REPORT-*` rows are
  in alphabetical order. Mechanical pass over the four added `docs/reference.md` lines: no trailing
  whitespace, no tab, no `x`-for-`×`, every `#anchor` resolves, table row widths correct.
- **The bundle flag-not-refuse carry.** It is in the **plan**, task 10 step 7 — *"Fixture T's
  bundle arm lands HERE, carried in from task 9 by name"* — so a brief extracted by
  `scripts/task-brief` will carry it. It reaches task 10's author, not only the report. (Task 9's
  brief also said task 9 "owns the label"; no label code exists, which is unavoidable with no
  bundle render and is covered by the same carry.)
- **`load_env` is not called** anywhere in `report.py`, as correction 7 required, and the
  docstring's claim about what the credential set can therefore cover is sized correctly.
- **Arm D did not fire.** `tests/test_diff.py` is untouched by the batch and its arms pass.
- **`SystemExit` from an override** is caught by the `except BaseException` arm and reported as
  `E-REPORT-OVERRIDE-RAISED` at exit 1 (verified by running) — the batch disclosed this rather than
  hiding it, and it matches `freeze`'s precedent.

## What I could not check

- **A genuine `draft` run**, for the same reason the plan already records: `publishable draft` is
  H9's. My probe hand-edits a real record, exactly as Fixture T does.
- **A bundle render of any kind** — task 10's code does not exist, so the flag-not-refuse arm is
  unverifiable by construction, and I confirmed only that the carry is routed.
- **Whether `_read_repo_root`'s lenient fallback silently empties the credential set in practice.**
  The docstring names the cost (a project-local template's credentials drop when
  `environment/repo_root.txt` is missing or malformed). I did not build that fixture, because
  Critical 1 makes the same set unreachable on a more common path; both want the same fix round.
- **`E-TEMPLATE-COLLISION` through `report`.** I verified the leak with `E-TEMPLATE-LOAD` and read
  that the collision path leaves by the identical unguarded call; I did not build a second
  distribution to confirm it.

## Tree state

**The tree is clean** — `git status` reports nothing to commit and no untracked files; all three
mutations were reverted and each revert verified by re-running the probe whose behaviour the
mutation had changed. Final foreground `uv run pytest`: **2746 passed, 1 skipped, 2 xfailed**;
`ruff check` clean, `ruff format --check` 90 files, `mypy` 50 source files.
