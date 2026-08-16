# Task 12 review — the no-leak test, the redaction, and decision 4a's boundary

Reviewed `a7c664b..1979a78` on `h7c-credentials`. Baseline reproduced before and after every
mutation: **1993 passed, 2 xfailed**; `ruff check` clean; `ruff format --check` 76 formatted, 0 to
reformat; `mypy` clean on 43 files. Every mutation was applied by editing the file, reverted by
editing it back, and verified byte-identical against a scratchpad copy with `diff` — never
`git checkout --`. `__pycache__` deleted before each run. The tree is back to `1979a78` exactly.

## Verdicts

1. **Spec compliance — ❌**
2. **Task quality — ❌**

**Where each defect originates, because the routing differs.** Spec compliance fails on **C1**: the
shipped normative document carries a security guarantee the code does not provide, and check 6's
second half (*"nothing elsewhere promises more"*) also fails. **That prose was dictated verbatim by
the brief** — steps 5's fenced block at brief lines 505-509 contains "two places", "at both",
"Declare it, and it is covered" and "leaves the rest of the message intact" word for word, and the
design doc's correction 1 asserts the undercount it rests on. The implementer copied it. So C1's
fix belongs to the spec and the brief, not to the implementation, whose two boundaries are correct
and pinned. The implementer's miss is the narrower one of not catching a brief/code disagreement —
which `CLAUDE.md` calls expected, and which they *did* catch three other times (see the report's
§ Where the brief/spec disagreed).

Task quality fails independently and needs no such hedge: **I1** alone carries it — the full suite
stays green under a mutation that empties this task's `validate.py` wiring, leaving ~45 lines of its
own production code pinned by nothing.

---

## Findings

### C1 (Critical) — a **sixth** exception-serialization site bypasses `Collector.render()`, and a declared credential reaches stderr verbatim

`src/publishable/cli.py:2845-2846`, in `main`:

```python
    except PublishableError as exc:
        print(f"  error   {exc.code:<20} {exc}", file=sys.stderr)
```

This interpolates an exception into text printed to **stderr** without going through
`Collector.render()`, so the redaction never runs. It is reachable: `validate.py:695` calls
`template.validate(doc)` **unguarded**, so a template's `validate` raising any `PublishableError`
propagates out of `validate_config`, out of `_dispatch`, and lands here.

**Verified, not reasoned.** Probe appended to `tests/test_validate.py` (since removed): a
`GenericTemplate` with `required_env = ["PUBLISHABLE_PROBE_TOK"]` and a `validate` that raises
`ContractError("upstream key " + os.environ["PUBLISHABLE_PROBE_TOK"], code="E-TEMPLATE-RULE")`,
driven through `main(["validate", path])`:

```
exit=1
STDERR='  error   E-TEMPLATE-RULE      upstream key sk-probe-sentinel-4242\n'
```

The value is **declared** — it is exactly the case decision 4a says *is* covered.

Three consequences:

- `docs/reference.md` § Secrets & credentials, as this task wrote it, says core turns an exception
  into text *"a reader sees in **two places**"* and replaces each credential value *"at **both**"*.
  There is a third, and it is uncovered. That clause is a security guarantee the code does not
  provide — the (b) class this review was told to weight hardest.
- The design doc's correction 1 argues *"Two edits cover all five constructions and cannot diverge
  as a sixth is added."* A sixth already existed when the measurement was taken.
- **The measurement was scoped by a proxy.** `grep -rn 'type(exc).__name__' src/publishable/*.py`
  answers *"where is the `type(exc).__name__` idiom used"*, not *"where does an exception's text
  become output"*. This site formats bare `{exc}` and is invisible to that grep. This is
  `CLAUDE.md` § Answering a question with a proxy, and § Scoping a diagnostic by the helper it
  calls, in the slice whose stated purpose is refusing proxies.

**The count is earned by a sweep, not by an incidental read.** `cli.py:2846` first surfaced while
reading around `io_c`, which would have been the same mistake one level down, so the claim was
re-derived by a sweep scoped to the question — *where does an exception's text become output* —
rather than to an idiom:

```
$ grep -rn 'str(exc)\|{exc}\|{exc!r}\|str(e)\|{err}\|str(err)' src/publishable/*.py
```

**Fourteen hits, not five.** Classified by where each one's text goes:

| Sites | Route | Covered? |
|---|---|---|
| `cli.py:2011`, `:2096`, `:2443` | `aggregate_c.warn` → `render()` | ✅ |
| `runner.py:707` | `redact(...)` directly | ✅ |
| `validate.py:586`, `:1170`, `:2581`, `:2710`, `:3541` | `c.error` after `:599` → `render()` | ✅ |
| `validate.py:477`, `:545` | `c.error` **before** `:599` | ⚠️ see M2 (`:477` is a YAML parse error — no credential possible) |
| `cli.py:2853` | `io_c` → `render()`; but `detail` lands in the **`path`** slot, which `render()` never redacts | ⚠️ no live leak |
| `base_experiment.py:46`, `sweep.py:332` | build a `ContractError` *message*; `_preloaded_experiment` swallows and `validate_config` re-reports through the collector | ✅ |
| **`cli.py:2846`** | **direct `print(..., file=sys.stderr)`, no collector** | **❌** |

Also checked `command_report`, `command_diff`, `command_resume` and `_dispatch` — no exception
interpolation in any of them. So `cli.py:2846` is the **only** output path the two-boundary ruling
misses, and "a sixth" is now a measured claim rather than an assumed one. The design's "five
constructions" is itself an undercount of the interpolations; it is only the *uncovered* count that
matters, and that is one.

Note the same handler also puts `exc.strerror` into a `Diagnostic`'s **`path`** slot at
`cli.py:2854`; `render()` redacts `f.message` only, never `f.path` or `f.code`. No current site puts
a credential in `path`, so that is not a live leak — but the asymmetry is undocumented.

### I0 (Important, prose) — "Declare it, and it is covered" is ambiguous, and `io.record` is the reading it loses under

`docs/reference.md` § Secrets & credentials closes decision 4a with *"Declare it, and it is
covered."* Redaction runs at two serialization boundaries only. A **declared** credential a step
writes through `io.record` reaches unit artifacts unredacted.

**Verified.** Probe (since removed) with `GenericTemplate.required_env =
["PUBLISHABLE_TEST_TOKEN"]` and a step doing `io.record(unit.key, {"tok": token})`:

```
LEAKS=['run_.../seed30/step01_summarize_units/units.parquet',
       'run_.../seed40/...', 'run_.../seed47/...', 'run_.../seed52/...', 'run_.../seed61/...']
```

**Deliberately not Critical**, and the distinction matters for routing. The clause sits inside a
paragraph whose whole subject is *matching* — *"core redacts only values it read … holds a value
core never saw and **cannot match**"* — so the defensible reading of "covered" is "matchable at the
two sites the paragraph above just enumerated", not "scrubbed from everywhere including a record a
step chose to write". Core **should not** scrub what a step deliberately records; there is no
coverage gap here for the code to close. What the probe demonstrates is that a one-word security
claim carries two readings and the document does not say which. Narrow the wording — "covered *in
an exception's text and in a diagnostic*" — and nothing in `src/` changes.

C1 is the only Critical: a demonstrated uncovered output path with a working repro.

### I3 (Important) — the cross-document sweep required by check 6 was not done; another document still promises more

`docs/experimental-designs.md:381`:

> | **Credentials in a shared config** | The config stores variable names; values live in `.env` and
> are **never captured, logged, or written to any artifact** |

Unqualified, and falsified by both I0's probe (a declared credential in `units.parquet`) and by
4a's own admitted bound (an undeclared variable). Task 12 added the bound to `reference.md` and to
nowhere else. `CLAUDE.md` § Habits that cost real work: *"Sweep for the claim, not for the file the
claim was first noticed in."*

`docs/design-principles.md:40` (*"Secrets are the one thing never captured"*) is softer and links
straight to the qualified section, so it survives — but only just.

### I1 (Important) — the whole `validate.py` half of the wiring is a check that cannot fail

**Mutation M1:** `validate.py:599` → `c.credentials = {}`.

**Result: full suite 1993 passed, 2 xfailed — identical to baseline.** No test in the repository
pins that line, and therefore none pins `declared_credential_names_for` (`validate.py:834-893`, ~45
lines including its docstring) either. `grep -rn declared_credential_names tests/` returns exactly
one hit, and it is a word inside test 4's *docstring*.

The line is not dead code — it covers a real surface. Probe appended to `tests/test_validate.py`
(since removed): an entrypoint whose module raises with a declared credential in its text, rendered
through the collector.

| Build | `c.render()` |
|---|---|
| M1 applied | `could not be imported: RuntimeError: boom sk-probe-sentinel-4242` — **leaked** |
| as shipped | redacted; probe passes |

So this is the shape the slice's own charter names: a headline deliverable wired through a path that
works and is pinned by nothing. The four new tests all render `command_run`'s `aggregate_c`; not one
renders a `validate` collector carrying a credential. Every existing `E-ENTRYPOINT-IMPORT` test
reads `c.findings` directly through `codes()`/`messages_by_code()` and never calls `render()`.

The fixture the suite is missing is small — the probe above is 15 lines.

### I2 (Important) — the report's "Mutation outcomes (all four, both halves each)" describes two mutations

Step 7 of the brief mandates a third: *"drop `repo_root` from `get_template(...)`. This test must
FAIL … while the two `GenericTemplate` tests above stay green. Verify both halves."* The report has
no entry for it. Its § *Where the brief/spec disagreed* does not claim it was skipped either — it is
simply absent, under a heading that reads as exhaustive.

**I ran it. It passes cleanly**, so the code is right and the reasoning in check 5 holds — but the
report asserted a completeness it did not have, which is the same class as a comment claiming a
guarantee the code does not provide.

### M1 (Minor) — "leaves the rest of the message intact" is false for short or ordinary-text values

`redact` has no minimum-length guard and replaces every occurrence. Fails **closed** (safe), so this
is not a security defect — but the normative clause is wrong. See the degenerate probes below;
`{"TOK": "e"}` turns `completed 4 units` into `compl<redacted:TOK>t<redacted:TOK>d 4 units`.

### M2 (Minor) — `validate_config`'s three early returns render unredacted

`validate.py:546`, `:553` (`E-TEMPLATE-LOAD`, `E-TEMPLATE-COLLISION`, `E-TEMPLATE-UNKNOWN`) return
before `c.credentials` is set at `:599`. A project-local `templates/*.py` raising at import with a
credential in its message therefore renders it raw. Structurally hard to fix — at that point core
has resolved no template and knows nothing declared — so this is genuinely inside 4a's bound. It is
recorded because the code comment at `:593-598` correctly claims coverage of `E-ENTRYPOINT-IMPORT`
and says nothing about the three findings it *cannot* cover. Confirmed by reading; not probed.

There is **no** early return between `_check_entrypoint` and `:599` — the comment's actual claim
holds. Verified by reading `validate_config` in full.

### M3 (Minor) — `drift_c.credentials` and `allocation.json` are nominal coverage

`cli.py:2648` (`drift_c.credentials = credentials`) is unpinned; its only finding,
`E-INPUT-CHANGED`, is core-authored path text, so no credential can reach it. Harmless, correct as a
safe default, worth knowing it is untested.

Likewise `allocation.json`: the brief asks the sweep to cover it, and `_files_under` globs so it
would be — but no fixture in this family declares an assignment or a holdout, so no run in the four
tests ever writes one. Nominal, not demonstrated. The brief itself rules this acceptable.

---

## The eight required checks

**1. Redaction is by exact value, never by pattern — ✅.** `secrets.redact` matches only on
`values.items()`; no name inspection, no regex, no entropy test anywhere in the module.
`credential_values` builds its mapping from *declared names*, so nothing is filtered by shape. Both
failure directions probed — results below.

The brief's claim that mutation (c) needs nothing here because
`test_redaction_replaces_the_exact_value_and_names_the_variable` covers it is **half right**: that
test pins the **fail-closed** direction (`sk-zzzzzz` untouched). Its fail-open half uses
`OPENAI_API_KEY` — a secret-*looking* name — so a name-pattern filter mutation would leave it green.
The property holds structurally (there is no name-matching code to mutate), so this is not a
finding, but the brief's justification is stated more strongly than the fixture supports.

**2. Degenerate values — ✅.** Doubly guarded for the empty string (`credential_values`'s
`if value:` and `redact`'s `if value:`). Short and substring values over-redact, which is
fail-closed. Results below.

**3. Both boundaries separately pinned — ✅, all four outcomes confirmed.**

| Mutation | test 1 (step-error) | test 2 (success) | test 3 (render) | test 4 (local template) |
|---|---|---|---|---|
| **M3** `runner.py` `error = f"..."` (no redact) | **RED** | green | **green** | **RED** |
| **M4** `diagnostics.py` `render()` → `f.message` | green | green | **RED** | green |

Neither mutation reddens the other's boundary. Both boundaries are doing real work.

**4. The render fixture genuinely reaches `aggregate` — ✅.** Under M4, test 3 failed at
`tests/test_cli.py:8664` (`assert "<redacted:PUBLISHABLE_TEST_AZURE>" in out`) — meaning the
assertion one line above it, `assert "W-STATS-AGGREGATE-FAILED" in out`, **passed**. So the warning
fired, `aggregate` was invoked, and the string reached `capsys` unredacted. `run_a_project`'s
signature has `expect_exit: int = EXIT_OK` and test 3 passes no override, so the run reaches
`EXIT_OK`. Neither assertion is vacuous.

I also checked all four `W-STATS-AGGREGATE-FAILED` emit sites in `cli.py` (2008, 2093, 2232, 2438)
— **every one renders through `aggregate_c`**, which received `.credentials`. The report enumerated
collectors by construction order rather than by which carry foreign text, but the answer happens to
be right; there is no gap here.

**5. The `repo_root` change — ✅, and the reasoning holds.**

**Mutation M2:** `cli.py:1537` → `get_template(doc.get("experiment_type", ""))`.

| test 1 | test 2 | test 3 | test 4 |
|---|---|---|---|
| green | green | **RED** | **RED** |

Test 4's failure is the exact defect predicted: `errors` came back as
`['RuntimeError: POST https://api.example/v1?key=sk-h7c-sentinel-9f3a1c returned 401', …]` — the
sentinel in `executions.jsonl`, unredacted, because `run_template` resolved to `None` and
`credentials` emptied. Both `GenericTemplate` fixtures stayed green, which is what proves tests 3
and 4 were needed. The `run_template`-not-`template` naming is right and the later `get_template`
call is untouched. See I2 on the reporting.

**6. Decision 4a's bound is stated — ⚠️ partially.** `reference.md` states it. But its closing
clause is ambiguous (I0), a third emit site falsifies the paragraph above it (C1), and
`experimental-designs.md` still promises more (I3). The second half of this check — *"nothing
elsewhere promises more"* — fails.

**7. The sweep — ✅ on mechanics, and it can fail.** `_files_under` filters the **file list**
(`sorted(results_dir.rglob("*"))`, `p.is_file()`), never the output. `run_dir = next(results_dir.glob("run_*"))`,
so the run directory is inside the swept root. Proven against strings known to be present:

```
FILES=['run_…/environment/pyproject.toml', 'run_…/executions.jsonl',
       'run_…/manifest/input.json', 'run_…/run.yaml', 'run_…/sweep.yaml']
HITS={'<redacted:PUBLISHABLE_TEST_TOKEN>': ['…/executions.jsonl', '…/run.yaml'],
      'RuntimeError':                      ['…/executions.jsonl', '…/run.yaml'],
      'returned 401':                      ['…/executions.jsonl', '…/run.yaml']}
```

The sweep reads real content in both files that matter. I0's probe additionally showed it reaching
`seed*/step01_summarize_units/units.parquet`, so artifacts are covered as bytes. stdout/stderr are
asserted separately. `allocation.json` — see M3.

**8. What redaction might break — ✅.** Nothing parses these strings. `ExecutionResult.error` has
exactly one consumer, `run_record.py:36-37`, which copies it verbatim into the record; there is no
`startswith`/`split`/regex over it anywhere in `src/`. No traceback of a step exception is printed.
The `<redacted:NAME>` marker cannot be confused with content: it is written inside JSON/YAML string
values by `json.dumps`/`yaml.safe_dump`, and it does not collide with the separate host-path
redaction marker `study add` is specified to use (`reference.md` § 3083 describes that one in prose
only; `study add` is NOT BUILT). Longest-value-first ordering is correct and pinned by
`test_a_value_that_contains_another_value_is_redacted_whole`.

**Mechanical pass on the new prose — clean.** Both new lines: no trailing whitespace, no tab, no
invisible unicode, no en dash. The one link, `[diagnostic](#exit-codes-and-diagnostics)`, resolves
to `### Exit codes and diagnostics` at `reference.md:3133`.

---

## (a) A check that could not fail — the mutation for each test, and what none reaches

| Test | Single-line mutation that reddens it |
|---|---|
| 1 `…reaches_no_artifact_and_the_redaction_says_so` | **M3** — `runner.py`'s `error = redact(...)` → plain f-string. Also: deleting `names = list(getattr(template, "required_env", ...))` from `cli.declared_credential_names` |
| 2 `…step_reads_its_credential_and_the_value_still_reaches_no_artifact` | **None in task 12's code.** Verified: green under M1, M2, M3, M4. It is a control plus a must-report, and its must-report half (`token_len`) pins **task 8's** `load_env`, not this task. Legitimate as a control; named here because the report does not name it |
| 3 `…template_exception_printed_as_a_warning_is_redacted_too` | **M4** — `diagnostics.py`'s `render()` message line. Also **M2** (drop `repo_root`), and deleting `aggregate_c.credentials = credentials` |
| 4 `…project_local_template_s_credentials_are_redacted_too` | **M3**, **M2**, and deleting the `requires_env` loop in `cli.declared_credential_names` |

Both halves of `cli.declared_credential_names` are separately pinned — `required_env` by tests 1/3,
`requires_env` by test 4. That is the one thing the brief most wanted and it is genuinely there.

**What none of the four reaches:**

- `validate.py:599` and all of `declared_credential_names_for` — **I1**, confirmed by full-suite M1.
- The `if path not in condition.selectors` skip inside `cli.declared_credential_names`. Task 10's
  reviewer pinned the *validate* copy of that skip; the `cli.py` copy is a near-duplicate and no
  fixture in this family sweeps a `requires_env` parameter, so its skip, its `except TypeError`
  arm, and its `param.default` fallback are all unexercised.
- `drift_c.credentials` — M3 above.
- `main`'s `except PublishableError` path — **C1**; nothing covers it because nothing redacts there.
- Decision 4a's prose, correctly named by the brief as document-only and unmutable.

## (b) A comment or docstring claiming a guarantee the code does not provide

- **`docs/reference.md` § Secrets & credentials** — *"two places" / "at both"* (C1) and *"Declare
  it, and it is covered"* (I0) and *"leaves the rest of the message intact"* (M1). Three false
  clauses in two paragraphs of a normative security statement.
- **`docs/experimental-designs.md:381`** — *"never captured, logged, or written to any artifact"*
  (I3).
- **`src/publishable/secrets.py:9-11`** — *"The one surface on which a value could reach a record is
  a failing step's exception text, which `redact` below exists for."* Falsified twice by this
  slice's own work: the render boundary exists precisely because there are four other
  constructions, and I0 shows `io.record` is another. Task 7 wrote it; **task 12 is the task that
  established the facts contradicting it** and did not sweep back to it.
- **`src/publishable/runner.py`'s `execute_plan` docstring** and **`cli.py:1531-1536`'s comment** —
  read clause by clause against the code and both are **accurate**. The `repo_root` justification
  in particular is exactly right, and M2 proves it.
- **`diagnostics.py`'s `credentials` docstring** — accurate, except that its *"five sites that build
  an exception string"* inherits C1's undercount.

---

## Probe results, verbatim

### Failure-direction probes

```
--- FAIL-OPEN: a credential whose name looks nothing like a secret
redact('conn failed for instrument_pw=hunter2xyz here', {'instrument_pw': 'hunter2xyz'})
  -> 'conn failed for instrument_pw=<redacted:instrument_pw> here'          REDACTED ✅
redact('LAB_BOX=plainvalue123', {'LAB_BOX': 'plainvalue123'})
  -> 'LAB_BOX=<redacted:LAB_BOX>'                                          REDACTED ✅

--- FAIL-CLOSED: a config value that merely looks random
redact('RuntimeError: token sk-zzzzzzzzzz rejected; nonce 9f3a1c8b2d', {'OPENAI_API_KEY': 'sk-abc123'})
  -> 'RuntimeError: token sk-zzzzzzzzzz rejected; nonce 9f3a1c8b2d'         UNTOUCHED ✅
```

Both directions correct. Redaction consults only the values core read; it never looks at a name or
at a string's shape.

### Degenerate-value probes

```
--- EMPTY STRING
os.environ['PROBE_EMPTY'] = ''
credential_values(['PROBE_EMPTY'])       -> {}                    (dropped at collection)
redact('hello world', {'A': ''})         -> 'hello world'         (guarded again in the loop)
```

Doubly guarded. An empty-string credential cannot corrupt a message — this is the over-eager
failure mode the review asked about, and it does not occur.

```
--- ONE CHARACTER
redact('POST /v1?key=a returned 401', {'TOK': 'a'})
  -> 'POST /v1?key=<redacted:TOK> returned 401'
     (this instance is clean, but every other 'a' in a longer message would also go)

--- VALUE IS A SUBSTRING OF ORDINARY TEXT
redact('RuntimeError: error while parsing', {'TOK': 'error'})
  -> 'RuntimeError: <redacted:TOK> while parsing'
redact('completed 4 units', {'TOK': 'e'})
  -> 'compl<redacted:TOK>t<redacted:TOK>d 4 units'
```

Over-redaction, never under-redaction: **fails closed**, so no security consequence. It does
falsify `reference.md`'s *"leaves the rest of the message intact"* (finding M1). No minimum-length
guard exists; whether one is wanted is a design question, since a genuinely one-character credential
must still be removed.

---

## What is right

The core of the task is sound and the hard parts were done properly. Redaction is by exact value
with no proxy anywhere in the path. Longest-value-first ordering is correct and pinned by a fixture
that can actually tell the two orders apart. The two boundaries discriminate cleanly in all four
directions. The `repo_root` reasoning is correct, non-obvious, and pinned by a test that fails
without it while both `GenericTemplate` fixtures stay green — which is exactly the fail-open shape
`CLAUDE.md` says this repo has shipped twice. The sweep filters the file list and can fail. The
three brief/spec disagreements the report records (`EXIT_PARTIAL` vs `EXIT_FAILED`, `parameters={}`,
the two-function split) were each verified correct on inspection.

## Suggested closure order

**Check `docs/superpowers/spec-defects.md` first** — greps for `template.validate`,
`E-TEMPLATE-RULE`, `redact` and `credential` return nothing relevant, so C1 is not already filed.
Whether it is closed here or filed is a scope call: slice task 14 is *"`spec-defects.md` filings"*,
and guarding `template.validate(doc)` is arguably H7c work only because this task's document is
what promises it. Filing it is defensible; leaving the reference.md sentence unnarrowed is not.

1. **C1** — either extend the redaction to `main`'s `PublishableError` handler (and/or guard
   `template.validate(doc)`), **or** narrow `reference.md`'s "two places"/"at both" to what the code
   does and file the handler. Whichever is chosen, pin it — the probe in C1 is written and short.
2. **I1** — one fixture rendering a `validate` collector that carries a credential. The probe in I1
   is 15 lines and is already written.
3. **I0 / I3 / M1** — one prose sweep, narrowing every unqualified claim to the two boundaries.

**Edits vs. appended corrections — these route differently, per `CLAUDE.md` § Checking consistency.**

| File | Treatment |
|---|---|
| `docs/reference.md` § Secrets & credentials | **Edit.** A live normative document; a false security clause is corrected in place, then the mechanical pass re-run |
| `docs/experimental-designs.md:381` | **Edit**, same reason (I3) |
| `src/publishable/secrets.py` module docstring | **Edit** — it is code |
| `docs/superpowers/specs/2026-08-16-credentials-and-secrets-design.md` correction 1 | **Append a further correction saying what it replaces. Do not retro-edit** — the development record holds what was decided when it was written, and its "five constructions … cannot diverge as a sixth is added" is the evidence of how the miss happened |
| `.superpowers/sdd/.../task-12-brief.md`, `progress.md` | **Do not edit.** Same rule |

4. **M2, M3, I2** — record rather than fix.

---

*Housekeeping: `.superpowers/sdd/.gitignore` was found clobbered to a bare `*` at the start of this
review and has been restored to its documented content, per `CLAUDE.md`. `git status --short` now
shows this file as untracked-and-not-ignored, so `task-*-review.md` will commit normally; `git add -f`
is still the safe habit.*
