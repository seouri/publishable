# H7b Part B — whole-branch review

Reviewed: branch `h7b-resolvers`, 24 commits, against `main` at `470a830`. Reviewed 2026-08-17.

Gates at HEAD, run in the foreground before any mutation: `uv run pytest` → **2108 passed, 1 skipped,
2 xfailed** (matches the expected count exactly); `ruff check` clean; `ruff format --check` clean
(80 files); `mypy` clean (45 source files).

Probes ran from `tests/test_zz_wbprobe.py` and `scratchpad/subproc_probe.py`, both **deleted after
the review**. Every resolver probe used a *real installed distribution* discovered through
`importlib.metadata` running *real resolver code*, never a monkeypatch of `resolve_units` — the thing
under review is what user code inside a resolver can do, and a patched call site cannot answer that.
Every mutation was reverted by copying a scratchpad backup over the file (never `git checkout --`)
and **re-verified by behaviour**, not by `git status`.

**Verdict: NOT READY TO MERGE.** One Critical credential leak, verified at the real terminal, plus
three Important findings. Two remedies for the Critical are given below, both verified against the
console script and the full suite; they close different amounts, which the finding states.

---

## Findings

### C1 — Critical, **BLOCKS MERGE**. A resolver's `sys.exit()` leaks a declared credential verbatim, at both `validate` and `run`

Task 32 closed decision 3's containment for `Exception` and stopped one type short. Both new handlers
catch `except Exception`; `SystemExit` and `KeyboardInterrupt` derive from `BaseException`, so a
resolver body calling `sys.exit("could not authenticate with key " + os.environ["MY_KEY"])` escapes
`main` entirely.

**Verified at the real terminal** — a real `leaky-1.0.dist-info` on `PYTHONPATH` registering a real
resolver, driven through the console script as a subprocess:

```
===== publishable validate : exit 1 =====
could not authenticate with key SENTINEL-sk-abc123
>>> CREDENTIAL IN OUTPUT: True

===== publishable run : exit 1 =====
could not authenticate with key SENTINEL-sk-abc123
>>> CREDENTIAL IN OUTPUT: True
```

No `E-` code, no redaction, no collector — and *worse* than the traceback decision 3 was written
about, because the bare `SystemExit` message prints alone with nothing marking it as a fault core
recognised. An in-process probe over fourteen resolver bodies reproduces it for `KeyboardInterrupt`
and a bare `BaseException` too; every `Exception`-derived shape is correctly redacted at both commands
(enumerated under *Verified correct* below).

**Why this is in scope, not a residual the slice knowingly accepted.** Four independent reasons, the
third decisive:

1. **Decision 3 rules "Contained, at both `validate` and `run`"** for "a **non**-`PublishableError`
   from a resolver". `SystemExit` is exactly that. The ruling is not honoured.
2. **`reference.md` § Errors asserts the guarantee unconditionally.** `E-RESOLVER-RAISED`'s row:
   `command_run` "contains the identical raise at `run`, through a fresh, redacting `Collector`
   rather than letting it end the command in an un-redacted traceback — the one output no redacting
   surface sees." False for this class. This is `CLAUDE.md`'s first *Habits that cost real work*
   entry — a claimed guarantee the code does not provide — in a **normative § Errors row**.
3. **The four documents already state the rule, for this exact exception, and core already
   implements it one call earlier.** `reference.md` § Errors core raises, the `E-PLUGIN-LOAD` row:
   *"An entry point whose module raises while importing, or calls `sys.exit()` at module scope.*
   **`SystemExit` is a `BaseException` and so needs its own `except`** *— a plugin building an
   `argparse` parser at import would otherwise end the command with the plugin's own exit code and
   no diagnostic at all."* `plugins.load_entry_point` gives `SystemExit` its own arm with that
   verbatim justification. So **the same plugin calling `sys.exit()` at module scope is contained as
   `E-PLUGIN-LOAD`, and calling it inside the resolver body leaks a credential.** That is not a
   considered boundary; it is the documents' own rule applied at import and not at iteration, in the
   slice that built both call sites.
4. `validate.py`'s handler does name the residual in a comment. That is honest about the code but
   does not license it — and **`cli.py`'s handler, the security site where the credential is in
   scope, names no residual at all.** The slice's three documents disagree with each other about
   whether this case is closed.

**Two remedies, both verified. Note their scopes differ — the narrow one does NOT close everything
this finding reports.**

*Narrow (two tokens):* `except Exception` → `except (Exception, SystemExit)` at `cli.py:1351` and
`validate.py:1360`. Gives, at both commands:

```
  error   E-RESOLVER-RAISED    data.units
          resolution raised SystemExit: could not authenticate with key <redacted:MY_KEY>
>>> CREDENTIAL IN OUTPUT: False
```

Full suite green (`2139 passed` = 2108 + my 31 probes), `ruff`/`mypy` clean. **But it closes
`SystemExit` only** — the `KeyboardInterrupt` and bare-`BaseException` cases this finding also
reports still put the credential on stderr. Anyone applying this fix and marking C1 closed would be
wrong, which is why both scopes are stated here rather than left to be discovered.

*Full (recommended, also verified):* `except BaseException as exc:` with
`if isinstance(exc, KeyboardInterrupt): raise` as the handler's first two lines, at both sites.
Closes all three probed cases (`CREDENTIAL IN OUTPUT: False` at both commands through the console
script) with the **full suite green at 2108, `ruff` and `mypy` clean**, and keeps Ctrl-C propagating
untouched so a slow resolver stays interruptible. Redaction happens at *render*, so rendering before
the re-raise leaks nothing. Both remedies were reverted afterwards and the leak re-confirmed present,
so each is what closed it rather than something else.

**Recommendation: take the full one.** The narrow one leaves a residual that has to be argued for —
and the argument is weaker than it looks. A plugin calling `sys.exit()` is an ordinary accident
(exactly the `E-PLUGIN-LOAD` row's `argparse` case), whereas a resolver *constructing*
`KeyboardInterrupt("…secret…")` is not a threat core owes a defence against. But bare `BaseException`
sits between the two and the full remedy costs nothing extra, so there is no reason to reason about
where the line falls.

Needs beside the code: a test with a resolver calling `sys.exit()` carrying a sentinel, asserting the
sentinel is absent **and** `<redacted:...>` present (an absence-only assertion passes on a run that
never raised); a test that Ctrl-C still propagates, or the re-raise is unpinned; `validate.py`'s
residual sentence rewritten to name `KeyboardInterrupt` alone (or deleted, if the full remedy lands
and nothing is residual); and no change to the § Errors row, which becomes true.

---

### I1 — Important, **blocks merge**. `E-RESOLVER-RAISED` is reported for **table** and **glob** faults, where no resolver exists, and the comment asserting otherwise is false

`validate.py`'s new arm carries: *"The table and glob branches raise `ContractError` and nothing
else, so this arm is a resolver's by construction rather than a catch-all over core."* Probed by
constructing the faults rather than by reading:

| Config's source | `validate` reports |
|---|---|
| `from: bad.csv` (a table whose CSV holds invalid UTF-8) | **`E-RESOLVER-RAISED`** |
| `from: {glob: "/etc/*.conf"}` (an absolute glob pattern) | **`E-RESOLVER-RAISED`** |
| `from: adir` (a table naming a directory) | `E-UNITS-SOURCE-MISSING` (correct) |
| `from: {glob: "[["}` | `E-UNITS-EMPTY` (correct) |

So a user whose CSV is mis-encoded is told `resolution raised UnicodeDecodeError` under a code whose
own § Errors row says *"A resolver's own body raises something that is not a `ContractError`"* — a
diagnostic naming a resolver for a config that declares none. The code is emitted where its own
normative row states it does not apply.

**This is not a regression, and that matters for how it is fixed.** On `main`, `_check_units` had two
`except` arms; this branch has three. Before this slice a mis-encoded table escaped `validate` as a
traceback, breaking *"`validate` never raises"* outright. So the slice **improved** containment and
mislabelled it. The fix is therefore not to narrow the arm away but to branch on the source, keeping
`E-RESOLVER-RAISED` for a resolver source only.

**Not cheap, and the obvious shortcut is wrong.** Reusing `E-UNITS-SOURCE-MISSING` for the table/glob
arm would falsify its own row, which names *"a table that is not a file under `input_dir`, or … none
of a table name, a `{glob: ...}` mapping, or a `{resolver: ...}` mapping"* — a file that exists and
will not decode is neither of those. **So this needs a new identifier** (`E-UNITS-SOURCE-UNREADABLE`
or similar), which in this repo means a § Errors row and a test alongside the code change. That is the
route I recommend; the alternative of stretching an existing row is the cheaper-looking option and is
the one that would leave a false normative row behind. The false comment should be **deleted rather
than rewritten**, per this repo's own rule.

---

### I2 — Important, **blocks merge** (cheap). Task 33's inherited `cli.py` `cfg`-threading obligation is unmet, and it was pinnable

The tasks 27-29 review assigned this in writing: *"The `cli.py` half is still open and remains task
33's"* — mutating `cli.py`'s `resolve_wide_cfg(doc, wide_swept_paths(...))` to
`resolve_wide_cfg(doc, set())` leaves the suite green. **Re-measured at HEAD with `__pycache__`
cleared: the mutation leaves all 2108 tests passing.** Task 33 (`ba57bc7`) added three tests, all in
`test_validate.py`, and **no `test_cli.py` test at all**. The task 30-33 report's "Answers to the
three required statements" section does not mention this obligation.

**And the seam is pinnable — I built the discriminating test.** A resolver reading a swept parameter
only on its *second* call (a module-level counter; `command_run` calls `validate_config` first, which
does its own `resolve_wide_cfg`, then `cli.command_run` makes the call the mutation empties):

- **HEAD:** exit 1, `E-RESOLVER-SWEPT-PARAM` reported.
- **Mutated:** exit 0 — **the run completes**, handing the resolver a swept parameter's real value and
  building a roster the run then treats as one table for the whole run.

That is the `data.units` is-one-roster-per-run invariant going unenforced silently, which is the
strongest kind of thing to leave unpinned. Roughly 30 lines in `test_cli.py` closes it.

This is the **second instance in one slice** of the rule the tasks 27-29 review already ruled on —
*a deferral inherits the expiry of the claim licensing it*. There the licence had expired; here the
obligation was simply not discharged and the report is silent rather than wrong.

---

### I3 — Important, does not block by itself (but must not merge as written). Two premature build claims: the slice asserts it has merged

- `CLAUDE.md:59` — **"H7b Part B (resolver dispatch) merged on 2026-08-17, against commit
  `f9d99148c3be5590420e7cff3a3598f2d529ecf2`."**
- `docs/feasibility-llm-growth-studies.md:1065` — **"H7b **Part B** merged at the commit above and
  retires `E-DATA-RESOLVER-UNSUPPORTED`."**

Neither has happened: the branch is unmerged, 24 commits ahead of `main`. Both are dated,
commit-pinned assertions of a merge *event*, which is the sharpest form of the error `CLAUDE.md`'s
feasibility procedure step 10 exists to prevent. They become true on merge, so the remedy is
sequencing — land them in the merge commit, or reword to "lands with" — not deletion.

A third site is the same claim in a milder form and is **acceptable as written**: `reference.md`
§ The one config file's *"The `{resolver: <name>}` form of `data.units.from` left this list with H7b
Part B"* is the standing present-tense form that document uses for H3d and H4a, and the `NOT BUILT`
marker it describes is correctly gone. Flagged only so the fix to the two above is not swept over it.

Also checked and correct: `plugin new` is marked `built` in § CLI reference and really dispatches
(scaffolded a package under `/tmp` as a subprocess); no `NOT BUILT`/`not yet built` marker outlived
its slice; `E-DATA-RESOLVER-UNSUPPORTED` is absent from `src/` and from all four documents, surviving
only in the development record (correctly not retro-edited) and in two test docstrings asserting its
absence.

---

### M0 — Minor. Four codes whose § Errors rows sit under *validate reports* are now printed by `run`, without the dual-surface note their neighbours carry

`cli.py:1361` is `roster_code = exc.code if isinstance(exc, PublishableError) else "E-RESOLVER-RAISED"`,
so a coded `ContractError` out of resolution is reported **at `run`** under its own code. My I2 probe
observed exactly this: `E-RESOLVER-SWEPT-PARAM` — whose row lives in § Errors **`validate` reports** —
printed by `command_run`'s fresh collector. Because a resolver is nondeterministic user code that may
behave differently on the second call, the same is reachable for `E-UNITS-ATTR-MISSING`,
`E-UNITS-KEY-DUPLICATE` and `E-UNITS-EMPTY`.

No row *forecloses* this, so nothing is false — but `reference.md` does track dual-surfacing
explicitly where it happens (`E-RESOLVER-YIELD`, `E-TEMPLATE-COLLISION` and `E-TEMPLATE-LOAD` all say
so in their rows), and these four now share the property and say nothing. Given the standard is "every
site that raises **or reports** it", these rows want the one-clause note their neighbours carry. Minor
because the behaviour is right and arguably the best available — reporting the real fault under its
real code beats re-coding it — and only the documentation lags.

### M1 — Minor. `E-RESOLVER-SWEPT-PARAM`'s message composes into a sentence that gives an impossible remedy

`units.py` builds it as `f"resolver \`{name}\` reads {exc}. ..."`, interpolating a whole sentence
after "reads". The rendered result (captured from my probe):

> resolver `plate_wells` reads `parameters.analysis.method` **is varied by** `sweep`, so it has no
> single value at this scope; **read it from a `condition`- or `repeat`-scoped step**. … Read a
> parameter the sweep leaves alone

Two defects in one string: it is ungrammatical, and it offers **two conflicting remedies of which the
first is impossible** — a resolver is not a step and has no condition or repeat scope to move to. The
correct remedy is the clause at the end. Interpolate `exc.message`'s subject only, or compose the
sentence rather than embedding a foreign one.

### M2 — Minor. `ResolverIO`'s docstring still points a reader at task 31 as future work

`artifacts.py`: *"Task 31 (`hash_index` naming what a resolver read) is where whether either matters
gets decided; this class does not decide it."* Task 31 landed and **decided both questions** — the
answer is in `spec-defects.md` ("The two `ResolverIO` questions task 23's docstring left as task
31's, decided. Both are benign."). This is the same shape as the Critical the tasks 25-26 review
closed: a docstring naming a closed task as the owner of a decision already recorded. Replace the
pointer with the decision, or with a pointer to where it lives.

### M3 — Minor. A `spec-defects.md` amendment names a function that does not exist

`spec-defects.md:6122` credits `RESOLVERS`'s first reader to `_resolve_resolver`'s scan-then-load.
The function is **`_resolver_for`**; `_resolve_resolver` appears nowhere in `src/`. The substance is
right — `RESOLVERS` is genuinely read now, through `declared_names` → `_registry_for` → `RESOLVERS`,
which I verified rather than assumed, so the entry's *claim* stands and only its name is wrong.

### M4 — Minor, cross-task drift. A ledger-closed Minor was silently reopened by a later task

The tasks 25-26 fix round closed a Minor by moving `ResolverIO` construction *inside* `command_run`'s
`if units_decl` ternary, recording *"so nothing is constructed for a run with no units block."* Task
31 moved it back out (`resolver_io = ResolverIO(input_dir)`, unconditional) because it needs
`read_paths` after the call. **The change is right and the ledger sentence is now false.** Per this
repo's rule the ledger is not retro-edited: append a correction saying what it replaces.

### M5 — Minor. The count's "not settled" caveat is stated asymmetrically

§ Executability's *What this measurement does not settle* says a clean `validate` is necessary but
not sufficient for E3/E4/E6, because `io.reuse_from` is invisible to any config. That cuts both ways:
a clean `validate` does not establish "no remaining core-side blocker" for E1/E2/E5 either, and the
section does not say so. **I checked the three by reading rather than by validate's silence and the
count survives** (see below), but the caveat should be symmetric — the three "Yes" rows rest on
reading each design's prose, exactly as the three "No" rows do.

---

## Verified correct (probed, not read)

- **Task 30 — `provenance.plugin_versions`.** Doc and code agree: `reference.md:725` states it is
  "populated only when `data.units.from.resolver` names a plugin", which is what
  `versions_for(RESOLVER_GROUP, ...)` does. Its test carries a real table-sourced control, so an
  unconditionally-populated dict would not pass. Confirmed end to end in my own runs.
- **Task 31 — `hash_index`, all three sources.** My own end-to-end probe, one `input_dir`, real runs,
  reading the real `manifest/input.json`. No source is left silently at `sha256: None`:

  | source | hashed | left `null` |
  |---|---|---|
  | table | `index.csv` | `a.dcm`, `b.dcm`, `layout.csv`, `unnamed.txt` |
  | glob | `a.dcm`, `b.dcm` | `index.csv`, `layout.csv`, `unnamed.txt` |
  | resolver | `a.dcm`, `b.dcm`, `layout.csv` | `index.csv`, `unnamed.txt` |

  The resolver row is the spec's § Where units come from sentence exactly — what the resolver *read*
  (`layout.csv`) **plus** what its units *name* — and each row carries an unnamed control file that
  stays `null`, so `hash_index` behaving like `hash_all` would fail it. Path forms match by
  construction (`_from_glob` and `build_manifest` both use `relative_to(input_dir).as_posix()`).
- **The narrowed no-import invariant — both halves discriminate independently at HEAD**, re-run seven
  commits after the ledger proved it, `__pycache__` cleared:
  - unconditional load at the validate level → **only** `test_validate_imports_no_plugin_for_a_config_that_names_no_resolver` fails;
  - `_resolver_for` fabricating a `Unit`-yielding generator and never importing → **only** `test_a_resolver_source_is_no_longer_refused_wholesale` fails.

  Neither mutation reddens both, so neither half is doing nothing.
- **`validate` never raises — by shape enumeration, not by grep.** Fourteen resolver bodies at both
  `validate` and `run`. Every `Exception`-derived shape becomes a finding: returns `None`/`int`
  (`E-RESOLVER-RAISED`, `'NoneType' object is not iterable`), returns `str`/`dict`, yields a
  non-`Unit`, yields a duck-typed object with `.key` (all `E-RESOLVER-YIELD`), raises mid-generator
  after two valid yields (`E-RESOLVER-RAISED` — so the `try` is **not** decorative and the roster is
  materialized inside `resolve_units`), duplicate keys (`E-UNITS-KEY-DUPLICATE`), and a `ContractError`
  keeps its own code. The **only** escapes are C1's `BaseException` family.
- **§ Errors covers every emit site.** `E-RESOLVER-RAISED` has two emit sites (`validate.py:1369`,
  `cli.py:1361`) and **one** row naming both. The two codes that shipped rowless mid-slice
  (`E-RESOLVER-YIELD`, `E-RUN-RESOLVER-UNCONFIGURED`) both have rows now, the latter joining the
  existing `E-RUN-*` row with its "six"→"seven" count phrase updated. C1 and I1 falsify that row's
  *content*, not its coverage.
- **`CLAUDE.md`'s invariants, checked directly.** Units stay the inference base (`Unit`/`UnitList`
  untouched; only three module-level functions added, so `io.units`' three operations plus `.train`
  are unchanged). The three hashes stay split: `hashes.py` is untouched, so `code_hash` still covers
  only `src/**`+`templates/**`, a plugin's version is recorded in `provenance.plugin_versions` rather
  than folded into any hash, and task 31 touched `input_manifest_hash` alone. **No new
  behaviour-changing environment variable** — the branch adds no `os.environ`/`getenv` read to
  `src/`. Operation commands still take paths only; `plugin new` is a creation command, which the
  invariant permits. `input_dir`/`output_dir`-inside-the-repo is still checked before task 32's moved
  block, since `validate_config` runs first in `command_run`.
- **Mechanical documentation pass: clean** over all four documents plus `CLAUDE.md` and the
  feasibility analysis — links, anchors, duplicate anchors, table widths, trailing whitespace, tabs,
  invisible unicode, fenced blocks skipped. **The checker was proved able to fail** by injecting a
  known-bad anchor before trusting its silence.

---

## My own measurement of the executable count

**Three of nine. Re-measured rather than accepted from the report — with the same substitution, which
bounds what my re-measurement corroborates.**

I rebuilt the harness rather than reusing the implementer's script: a real installed distribution
registering a real `patient_trajectory` resolver yielding 60 synthetic units carrying every attribute
any of the nine names, with each config's `data.units` + `statistics` + `limits` blocks transplanted
from the analysis's own YAML onto a generated project, driven through `main(["validate", ...])`.

**What that does and does not establish.** Like the implementer's, my transplant runs
`experiment_type: generic` against this repo's demo template and stands the demo's own
`analysis.method` axis in for E2's and C1's baselines and C2/C3's contrasts — the real
`growth_screen`/`growth_shortcut` packages do not exist to install. So this is independent
corroboration of **which codes each `data`/`statistics` block earns**, by a separately written
harness, and it inherits the substitution's limits exactly as the section's own entry does. It is not
an independent check of the real designs end to end, and nothing could be until the plugin exists.

| config | errors | warnings |
|---|---|---|
| E1, E2, E3, E4, E5, E6 | *(none)* | `W-DATA-CLUSTER-UNDECLARED` |
| C1, C2, C3 | `E-DATA-WEIGHT-CONTRAST` | `W-DATA-CLUSTER-UNDECLARED` |

This reproduces the section's table exactly, including the warning it excludes as a fixture artifact.
`E-DATA-RESOLVER-UNSUPPORTED` appears nowhere — **the refusal that has stood since H1 is genuinely
retired**, and this is the project's first non-zero executable count.

Six validate clean; the split to three is `io.reuse_from`, which `validate` cannot see. I checked
that by reading rather than by validate's silence (M5), and separately checked the three "Yes"
experiments for *other* unbuilt dependencies, which is the check the section omits:

- `grep -rn reuse_from src/publishable/` → **0 hits**, so E3/E4/E6's blocker is real.
- **E5 leans on three things, and this was the one open question that could have moved the count to
  two.** Its whole result is a `summary`-step `Estimate` marked `reported: true`, read by a hypothesis
  taking no `compare`, recorded as `verdict_rests_on: reported`. All three legs verified as live code,
  not as present-tense specification:
  1. `io.read_condition(condition, step, name, repeat: str | None = None)` — exists with the `repeat`
     keyword E5 needs.
  2. `run_record` expands a summary-returned `Estimate` into `{value, reported: True, ci95, n,
     method}` — so `reported: true` is written, not merely declarable.
  3. `verdict_rests_on` has a single hit in `src/`, which is the trap-shaped situation worth naming: a
     lone hit can be a dead constant. **It is not** — `hypotheses.py:234` writes `obs.rests_on` on the
     verdict path, and `hypotheses.py:74` sets `rests_on="reported"` on exactly the no-`compare`
     branch E5 declares. Read rather than grepped, because one spelling is not evidence of a reader.

  So E5 produces its result and the count stays three. Had leg 3 been a dead constant, E5 would not
  have produced a verdict and the headline would have been **two of nine** — worth recording as the
  check that came closest to overturning the slice's central claim.
- E1/E2 need `holdout` (H3d), bootstrap `resample` (H4a), `correction: holm`, `report_by`,
  `evaluate_on` — all present. **No config declares a non-null `null_test`**, the one
  `-UNSUPPORTED` code still live in that family, so it blocks none of the nine.

Both qualifications the spec requires are carried in the section: the plugin must exist and be
installed, and a declared apparatus probe is neither executed nor recorded (filed as a false
`apparatus: null` record, owner H7d). The count stands at **three**.

---

## Can a credential reach any output?

**Yes — through C1, and only through C1.** A resolver calling `sys.exit(msg)`, or raising
`KeyboardInterrupt`/`BaseException`, puts a declared credential verbatim on stderr at both `validate`
and `run`, verified through the real console script. Every `Exception`-derived path is correctly
redacted at both commands.

`main`'s bare `except PublishableError` handler does still print un-redacted, and the report's claim
about it is **accurate**: it is genuinely pre-existing (filed by H7c task 12/14 as
`## OPEN — main's last-resort stderr handler prints an exception un-redacted, by construction`, owner
unassigned), the filing really exists in `spec-defects.md` rather than only in the ledger, and task
32 does route a resolver's raise away from it. I found no *new* path into it — C1 bypasses it in the
other direction, escaping `main` entirely rather than reaching that handler.

---

## Verdicts on tasks 30–33

| Task | Verdict |
|---|---|
| **30** — `provenance.plugin_versions` | **PASS.** Doc and code agree, the control is real, confirmed end to end. Carries M3 (a wrong function name in its `spec-defects.md` amendment) and inherits M4. |
| **31** — `hash_index` | **PASS, and the strongest task of the four.** All three sources verified end to end by my own probe against real `manifest/input.json` files, each with an unnamed control. Spec correction 3's glob case is genuinely covered. |
| **32** — the credential leak | **FAIL — Critical.** Closed for `Exception`, open for `BaseException`, verified leaking at the real terminal at both commands, against decision 3, against a normative § Errors row, and against core's own `E-PLUGIN-LOAD` handling of the same exception from the same plugin. Also ships I1's false comment and mislabelled code. It did avoid the blind ordering-only mutation, correctly, per the spec's own correction — the failure is scope, not method. |
| **33** — prose sweep and reader-facing half | **FAIL — obligation (b) unmet.** (a) discharged, though by tasks 30/31's tests rather than its own — those are real `main(["run", ...])` executions reading real `run.yaml`, so the milestone is pinned. (b) **not done and pinnable**, proved with a discriminating probe (I2). (c) the dated count is correct, properly dated and commit-pinned, both qualifications carried, and independently reproduced — but it is written around two false "merged" assertions (I3) and one asymmetric caveat (M5). |

---

## Ranked: what would make merging this a mistake

1. **C1** — shipping a credential leak in the slice whose security task was to close credential
   leaks from resolvers, against a rule the four documents already state for this exact exception.
   Two tokens, one test.
2. **I2** — leaving the one-roster-per-run enforcement unpinned when the mutation completes a run
   silently, in a repo that has paid for this exact defect class more than sixteen times, when a
   prior review assigned it in writing and a discriminating test exists (I built it).
3. **I1** — a user-facing diagnostic naming a resolver for configs that declare none, emitted where
   its own normative row says it does not apply, justified by a false comment. Needs a new identifier
   and row, not a stretched existing one.
4. **I3** — merging a branch that says it already merged, at a pinned commit, in both `CLAUDE.md` and
   a dated feasibility measurement.
5. **M0–M5** — four rows missing a dual-surface note, one impossible remedy in a refusal message, two
   stale pointers, one wrong function name, one reopened ledger closure, one asymmetric caveat. None
   blocks.

Everything else I probed holds, and the slice's central claim is real: the resolver dispatches, both
halves of the narrowed no-import invariant pin independently, `hash_index` works for all three
sources, `E-DATA-RESOLVER-UNSUPPORTED` is gone, and **three of nine is the honest number** by my own
measurement.
