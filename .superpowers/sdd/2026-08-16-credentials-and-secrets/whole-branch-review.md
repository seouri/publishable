# H7c — whole-branch review

**Reviewed:** branch `h7c-credentials`, 37 commits, against `main` at `d86290c`. Read the full
`src/` and document diff, the design spec including its four appended correction sections, the
ledger, and `CLAUDE.md`. Tasks 13 and 14 gated here for the first time; tasks 1–12 not re-reviewed
except where a later task falsified something.

**Gates, re-run at HEAD:** `uv run pytest` → **1994 passed, 2 xfailed**. `ruff check .` → clean.
`ruff format --check .` → 76 files, 0 to reformat. `mypy` → clean, 43 source files. All four re-run
after every mutation was reverted.

**Verdict: NOT READY TO MERGE.** The security property itself holds end to end — see § My own leak
probe — and the honouring tests are real (two mutations proved it). What blocks is three Important
findings, each cheap: two are a sentence, one is a doc-limit narrowing. Nothing here needs a
redesign.

---

## My own end-to-end leak probe

Written independently of the suite, run, then deleted. Credential name deliberately unlike a
secret; value distinctive but not secret-shaped; **declared both ways** so the `required_env` path
and the `requires_env` union path both carry a value.

- Project-local template `plate_assay`, `required_env = ["PLATE_READER_HOST"]`, and
  `reader.vendor` a three-choice `Param` with `requires_env={"acme": ["PLATE_READER_TOKEN"], ...}`,
  config selecting `acme`.
- `.env` set `PLATE_READER_HOST=zqx-marmalade-7781`, `PLATE_READER_TOKEN=zqx-jam-2211`, and
  `SIDECAR_NOTE=zqx-undeclared-5150` — the last **declared nowhere**, as the negative control.
- The scaffolded step raised `RuntimeError("host=… token=… loose=…")` with all three verbatim.

Result, recorded error text:

```
RuntimeError: host=<redacted:PLATE_READER_HOST> token=<redacted:PLATE_READER_TOKEN> loose=zqx-undeclared-5150
```

- `executions.jsonl` and `run.yaml`: both declared values redacted, marker names the variable,
  surrounding text intact.
- Sweep over the **file list** (`rglob("*")`, filtered by path, never filtering the search output):
  5 files, zero hits for either declared value. `allocation.json` absent for this fixture, which is
  why the sweep globs rather than naming files.
- stdout and stderr: zero hits.
- **Sweep-can-fail control:** the same sweep for a string known present (`publishable`) hit 2 files.
- **Negative control:** the undeclared value was *not* redacted — which is what makes the documented
  limit honest rather than aspirational, and is also what falsifies finding 2 below.

**Mutations run against the union rule** (both reverted by editing the file back, then re-verified
by behaviour, never `git checkout --`):

- Replace `param.requires_env.get(value)` with the union over all `choices` → **4 tests fail**,
  including `test_the_union_is_over_the_conditions_the_sweep_resolves` and its honouring companion.
- Delete `if path in condition.selectors: continue` → **1 test fails**
  (`test_a_group_axis_colliding_with_a_credentialed_parameter_still_runs_the_check`), confirming the
  spec's fourth correction: the skip is pinned, and the two earlier "structurally unpinnable"
  verdicts were wrong.

**`Param.comment()` checked by running it**, not by reading a test: it renders
`choices: azure_openai (needs AZURE_OPENAI_API_KEY) | openai (needs OPENAI_API_KEY) | ollama`, and
`materialize._parameters_block`'s padding (`36 - len(entry)`) puts it at column 37 — exactly the
inline placement `reference.md` § Templates now shows. Task 4's review fix is correct.

---

## Findings

### 1. Important — three shipped comments carry a redaction-site count the slice's own next commit falsified. **Blocks merge.**

`src/publishable/diagnostics.py:34–36` justifies the render-boundary placement with *"rather than at
each of the **five** sites that build an exception string: a diagnostic carrying a template's or a
user package's exception is minted in **four** places and **a sixth is one commit away**."*
`src/publishable/runner.py:703` makes the matching claim: *"The other **four** places core
interpolates an exception are diagnostics."* `tests/test_cli.py:8637` repeats it: *"`aggregate`
raising is one of **five** places."*

**How verified.** Enumerated every site by reading, not by grepping one spelling — the substitution
the spec's own final correction says cost this slice a Critical. Sites where core interpolates a
user-code exception into text a reader sees:

| # | Site | Reaches |
|---|---|---|
| 1 | `runner.py:707` step error | `run.yaml`, `executions.jsonl` — redacted |
| 2–4 | `cli.py:2011`, `:2096`, `:2443` `W-STATS-AGGREGATE-FAILED` | stdout via `aggregate_c` — redacted |
| 5 | `validate.py:586` `E-ENTRYPOINT-IMPORT` | `c.render()` — redacted |
| 6 | `validate.py:719` `E-TEMPLATE-RULE` **added by `cd72c3a`, this slice** | `c.render()` — redacted |
| 7 | `discovery.py:312`/`:330` `{exc!r}`, relayed at `validate.py:545` | `c.render()` — **not** redacted, see finding 3 |
| 8 | `cli.py:2846` `main`'s catch-all, bare `{exc}` | stderr — **not** redacted, filed OPEN by task 14 |

So "five sites" is six-plus, "four places" is five-plus, and *"a sixth is one commit away"* describes
a site that already existed when the sentence was written (the reviewer found it in the same task)
and a fifth diagnostic site that the **very next commit on this branch** added. The decision the
comments defend is right; the count carrying it is false. This is `CLAUDE.md` § Habits that cost real
work, first bullet, and § Locating a table row by position's "check every count phrase near it".

**Fix — replace the census with the property, at all three sites in one edit**, so nobody mints a
ninth stale number. Wording that needs no maintenance: *"Redaction happens at `render`, the one place
a finding's text becomes output, rather than at each site that builds an exception string — every
diagnostic reaches output through here, whatever their number, and a site added later is covered
without a second edit."* And in `runner.py`: *"Every other place core interpolates an exception is a
diagnostic, and `Collector.render` covers all of them at once."* Do not fix one and leave the others:
`CLAUDE.md` § Sweep for the claim, not for the file.

### 2. Important — `reference.md` § Secrets & credentials still says there is nothing to redact, four lines above the paragraph saying otherwise. **Blocks merge.**

`docs/reference.md:3485`: *"This is why `report` and `diff` output is safe to send as-is: **there's
nothing secret to redact, because there was never anything secret in it**."* `docs/reference.md:3489`,
added by this slice: *"a step that reaches `os.environ` for a name no declaration mentions holds a
value core never saw and cannot match."*

**How verified.** My probe put an undeclared credential's value verbatim into both `run.yaml` and
`executions.jsonl` (see above). `report` and `diff` read those records, so the 3485 sentence is
false for exactly the case 3489 describes. The two sentences are in the same section, four lines
apart, and this slice rewrote the section.

Task 12's review caught the identical over-claim in `experimental-designs.md:381` (*"never captured,
logged, or written to any artifact"*) and narrowed it. Task 13's brief sent it to re-read
`design-principles.md:40`, which it did. Neither pass reached this sentence — `CLAUDE.md` § Sweep for
the claim, not for the file the claim was first noticed in, third bullet, verbatim.

**Fix:** narrow 3485 the same way 381 was narrowed — the guarantee is about *declared* credentials
and about core never writing a value into a record of its own, not about the record being
categorically secret-free.

### 3. Important — a **declared** credential reaches a rendered diagnostic unredacted through `validate_config`'s template-load early return. **Blocks merge (as a doc correction at minimum).**

`validate_config` sets `c.credentials` only after `resolve_template` succeeds. The
`except ContractError` branch does `c.error(exc.code, "experiment_type", str(exc)); return None` —
before that line — and `E-TEMPLATE-LOAD` embeds the raising file's own exception via
`discovery.py:330`'s `{exc!r}`.

**How verified — reproduced twice, through `main(["validate", …])` so the surface is named rather
than assumed.** Both shapes leak the value **verbatim to stdout**, exit `1`:

| Shape | Result |
|---|---|
| Two files — `a_plate.py` declares `required_env=["PLATE_READER_HOST"]` and loads fine; `b_broken.py` raises with the value at import | value on stdout |
| **One file** — the same template both declares `required_env=["PLATE_READER_HOST"]` and raises with the value after its own `@register_template` | value on stdout |

```
... raised while importing and registers nothing usable: RuntimeError('startup failed for key zqx-single-4242')
```

The single-file shape is the discriminator, and it settles the reading: the **sole** template
declaring the variable is the one whose text leaked, so `reference.md:3489`'s limit — *"core redacts
only values it read for a **declared** variable — one named in a template's `required_env`"* —
promises coverage the code does not provide, with no second-template ambiguity to hide behind. This
is decision 4a's own failure mode: a guarantee stated in the one document whose job is to prevent
them. The boundary placement is not at fault; the credential set is not yet known and cannot be,
because the raise discards the registration (`drain_pending()`) before anything reads the class.

**Fix:** either narrow 3489 to say redaction covers findings made **after** the template resolves
(the load and collision refusals excepted, with the reason), or file it as OPEN with that reasoning.
Do not claim a boundary set is complete without saying which findings precede it.

### 4. Important — `_check_required_env`'s guard names an owner that does not exist, and diverges from the two functions whose docstrings call it "deliberately the same set". Does not block.

`validate.py`: `if not isinstance(names, list): return  # a template declaring something else is not
this check's fault to report`. **`grep -rn "required_env" src/publishable/` returns no other reader**
— nothing anywhere reports a `required_env` that is not a list, so the comment asserts an owner that
does not exist and the path fails open silently. Meanwhile
`validate.declared_credential_names_for` and `cli.declared_credential_names` both do
`list(getattr(template, "required_env", None) or [])`, which for `required_env = "ABC"` yields
`['A', 'B', 'C']`. Both of those docstrings say they read *"the same two collectors"* /
*"deliberately the same set"* the checks read. On this input they do not.

Practical impact is nil (single characters are not credential names), but the comment is false and
the "same set" claim is not held by the code.

### 5. Important — the `PYTHON_DOTENV_DISABLED` filing's reason is a false dichotomy, and the invariant it concedes is the first one `CLAUDE.md` lists. Does not block.

The filing says a fix *"would mean core either not calling `load_dotenv` at all (losing the mechanism
this slice built) or pre-emptively clearing the variable before every call"*.

**How verified.** Read the installed package. `_load_dotenv_disabled()` is consulted by
`load_dotenv` only (`main.py:418`); **`dotenv_values()` does not consult it at all** (`main.py:438`
onward). So a third option exists and preserves everything: **parse with `dotenv_values(path)`, skip
the `None` values, and `os.environ.setdefault` the rest** — `dotenv_values` interpolates by default
exactly as `load_dotenv` does, and `setdefault` *is* `override=False`. The `None` skip is the detail
that makes it work rather than raise: `dotenv_values` returns `None` for a key written with no value
(`FOO` alone) where `load_dotenv` sets `""`, and `missing_env` already counts an empty value as
missing, so skipping it lands in the same place. That keeps the mechanism, keeps the dependency, and
removes the behavior-changing environment variable that `CLAUDE.md` § Invariants' first bullet rules
out.

The filing is otherwise accurate (it does fail closed). The reason is wrong, and the reason is what
justifies leaving it open.

### 6. Minor — the dict-valued-parameter filing's severity survives; its reason does not. Does not block.

The filing says *"the config is refused regardless (by the `choices` check)"* and *"a
`choices`-constrained parameter given a dict value fails its own constraint check."*

**How verified — probed.** `parameters.llm.provider: {a: 1}` against a template whose `llm.provider`
is a three-choice `Param` produced:

```
E-CRED-PARAM-MISSING  parameters.llm.provider   is `acme` in the base parameters, which requires `PLATE_ACME_KEY` …
E-PARAM-UNKNOWN       parameters.llm.provider.a is not a parameter of this template — did you mean `llm.provider`?
```

No `choices` finding. `_flatten` never produces `llm.provider`, so the `choices` check never sees it;
the refusal comes from `E-PARAM-UNKNOWN` on the nested leaf. The defect and the Minor severity both
hold — the message is misleading on an already-refused config — but the sentence explaining *why* is
false, in an entry filed to explain why something was not closed.

### 7. Minor — `command_run` now imports every project-local template one extra time per run. Does not block.

`registry._merged` is documented as *"built fresh on every call — never cached"*, and
`discover_local` re-imports every `templates/*.py`, executing user top level. `resolve_template`
exists specifically so `validate` does that once rather than twice. The new
`run_template = get_template(doc.get("experiment_type", ""), repo_root)` at `cli.py:1537` adds a
third full discovery to a `run` (validate's, this one, and the pre-existing one at `cli.py:1796`).
The comment above it justifies passing `repo_root` and the placement, and says nothing about the
cost. Verified by reading `registry.py:30-46` and `discovery.py:288-300`.

### 8. Minor — spec correction 3's `repo_root` claim is false. Does not block; dev record, so append rather than edit.

The correction says `command_run`'s *"only `get_template` call sits after it, **without `repo_root`**
— which resolves no project-local template."* `git show main:src/publishable/cli.py` shows that call
as `get_template(doc.get("experiment_type", ""), repo_root)` — it already passed it. The real and
sufficient justification is ordering: the call sits after `execute_plan` and inside
`if roster is not None`. The code comment at `cli.py:1530-1536` repeats the `repo_root` reasoning; as
a justification for the *new* call it is true, so no code change is needed.

### 9. Minor — the spec's final correction misnames the sixth site. Does not block.

It says *"`cli.py`'s **drift reporter** formats a bare `{exc}` and prints straight to stderr."* The
site is `main`'s catch-all `except PublishableError` at `cli.py:2846`; the drift reporter is
`drift_c` at `cli.py:2647`, which carries no exception text and *does* get `credentials`. Task 14's
`spec-defects.md` entry describes the handler correctly, so the spec is the only place carrying the
wrong name — which matters because it is the document a later slice will cite.

### 10. Minor — § Exit codes' row `5` says "a missing credential"; the new codes exit `1`. Does not block.

`reference.md:3144` lists *"a missing credential"* among what exit `5` covers.
`command_validate` returns `c.exit_code()`, which is `EXIT_WRONG` (1) for any error, so
`E-CRED-MISSING` and `E-CRED-PARAM-MISSING` exit `1`. The row plausibly means the runtime/apparatus
case, but nothing in the slice reconciled the two now that a credential fault is a `validate`
finding.

### Note, not ranked as a branch finding — 25 records are tracked against `CLAUDE.md`'s rule. Does not block.

Repo hygiene from the documented `.gitignore` clobber rather than anything this slice's changes
introduced, and un-tracking is a separate change; recorded here only so it is not lost.
`git ls-files` on the slice directory returns 14 `task-N-brief.md` and 11 `review-*.diff` files.
`CLAUDE.md` § The development record: *"Two things stay untracked because git already holds them:
task briefs … and every `.diff`."* `.superpowers/sdd/.gitignore` ignores both. They were force-added
during the clobber window; task 13 restored the `.gitignore` (correctly) but the files were never
un-tracked. `git rm --cached` on the 25 paths closes it. No `__pycache__` remains tracked — task 9's
cleanup held.

---

## Job 1 verdicts

**Task 13 — FAILS.** The suspicion in the brief was correct. The sweep reported exactly the two sites
its own brief flagged by name, and its report says *"Disagreements … None found."* Sweeping
independently — by claim shape rather than by spelling, over the four documents, `CLAUDE.md`, `src/`
comments and `tests/` — turned up **four** further stale claims of exactly this family: finding 2
(`reference.md:3485`, in the very section the slice rewrote, and the same over-claim task 12's review
had already fixed one file over) and finding 1's three count phrases in `diagnostics.py`,
`runner.py` and `tests/test_cli.py`. The two it did find are real and correctly fixed, and the
`design-principles.md` clause it added is good. But a sweep that stops at its brief's table is the
failure the brief predicted.

**Task 14 — PASSES, with two corrections.** All nine entries were checked against the code, not
against the brief. All **five routed items are filed and all five describe real gaps**:
`PYTHON_DOTENV_DISABLED` (verified against the installed package), the dict-valued-parameter report
(reproduced), `main`'s unredacted stderr handler (verified by reading `cli.py:2846`), the
`min_items`/`max_items` rendering gap (verified — `Param.comment()`'s `list` branch returns only
`f"list of {…}"`), and the pre-existing positional reference (verified present). Owners are named by
**role or slice**, never by task — `apparatus_probe` being "H7b task 13's" appears in body prose, not
in an Owner line. Two reasons are wrong, and a filing's reason is what justifies leaving it open:
findings 5 and 6 above. Neither changes a filed severity.

---

## What I checked and found clean

- **`CLAUDE.md` invariants.** `parameter_spec` remains the single source of truth: `requires_env`
  lives on `Param`, is rendered by `Param.comment()` (the only caller is `materialize.py:86`), and is
  enforced by `validate`. The constraint table does not list it, and `reference.md:1584` and
  `param.py`'s docstring both say why. No new import: `__init__.py` is byte-identical to `478c1f3`,
  matching decision 8. No new command, flag, or selector. The `CLAUDE.md` edit (task 9) is true —
  `field_convention` is declared in `templates/base.py` and `builtin/generic.py`, named in
  `generators/template.py`'s comment, and read nowhere — and the row was strengthened rather than
  weakened, since it now names why the other two survivors are unavailable. The one invariant this
  slice does dent is the no-behavior-changing-env-var rule, via the dependency — finding 5.
- **The two redaction boundaries.** Enumerated every `Collector()` construction (7, all in `cli.py`
  plus `validate`'s) and every `print(..., file=sys.stderr)`. `warn_c`, `dirty_c` and `io_c` carry no
  user-exception text; `aggregate_c` and `drift_c` are given `credentials`. The only sites outside a
  populated boundary are rows 7 and 8 of finding 1's table — one filed, one is finding 3.
- **The `.env` load sites.** `validate` and `command_run`, both idempotent, `override=False` pinned
  by a test that would fail on a one-word flip. `tests/conftest.py`'s autouse `_restore_environ`
  fixture is real and snapshot-based, which is the right shape: `load_dotenv` writes past
  `monkeypatch`.
- **The leak suite.** Four tests, each with something that must *report* before it sweeps for
  absence, each filtering the file list rather than the output. The union fixture is the three-choice
  one decision 6 specifies, with the third choice's requirement deliberately non-empty — and both
  mutations against it fail tests.
