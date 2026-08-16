## Task 12: The no-leak test, the redaction, and decision 4a's boundary

**Files:** Modify `src/publishable/diagnostics.py`, `src/publishable/runner.py`,
`src/publishable/cli.py`, `src/publishable/validate.py`, `tests/test_cli.py`, `docs/reference.md`.

**Interfaces:**
- Consumes: `redact(text: str | None, values: Mapping[str, str]) -> str | None` and
  `credential_values(names: Iterable[str]) -> dict[str, str]` from task 7;
  `runner.execute_plan(*, plan, run_dir, input_dir, cfgs, repeats, digest, units=None,
  max_failed_fraction=None, fold_members=None, arm_members=None, holdout_train=None,
  measurements=None) -> list[ExecutionResult]` — read from `src/publishable/runner.py`;
  `ExecutionResult.error: str | None`; `Collector` — a `@dataclass` in
  `src/publishable/diagnostics.py` whose only field is `findings: list[Diagnostic]`, with
  `error`/`warn`/`has_errors`/`exit_code`/`render` and **no other state**.
- Produces: `execute_plan(..., credentials: dict[str, str] | None = None)`; a redacted step `error`
  string; `Collector.credentials: dict[str, str]` and a `render()` that redacts every message
  through it.

**Where the redaction goes — spec correction 1, and it supersedes an earlier reading of decision 3.**
Decision 3 says "redact by exact value at the two record-writing sites". An earlier draft of this
task located those sites by `grep -rn "\.error\b" src/publishable/*.py`, concluded there was **one**
exception-text construction, and was **wrong**: that grep finds assignments to an `.error`
*attribute*, not constructions of exception text. The correct measurement is

```
$ grep -rn 'type(exc).__name__' src/publishable/*.py
runner.py:688     the step-error text
cli.py:1937       W-STATS-AGGREGATE-FAILED — a template's `aggregate` raised
cli.py:2022       W-STATS-AGGREGATE-FAILED — the resample retry raised
cli.py:2369       W-STATS-AGGREGATE-FAILED — a `report_by` stratum's compute raised
validate.py:566   E-ENTRYPOINT-IMPORT — the user package raised at import
```

**Five constructions, not one.** The four beyond `runner.py` carry a *template's* or a *user
package's* exception, and none of them reaches `run.yaml` — `run_record.py` has no diagnostics
channel, and `cli.py`'s own comment at the `aggregate_c` print says so. **But this task's leak sweep
covers stdout and stderr**, so all four are leaks by this slice's own definition.

**The ruling: redact at the two serialization boundaries, not at any construction site.**

| Boundary | Covers |
|---|---|
| `Collector.render()` in `src/publishable/diagnostics.py` — the one method every diagnostic's text passes through on its way to stdout or stderr, called from **seven** sites in `cli.py` | `cli.py:1937`, `cli.py:2022`, `cli.py:2369`, `validate.py:566`, and every diagnostic minted after them |
| The step-error path in `runner.execute_plan` | `runner.py:688`, and through it both `executions.jsonl` and `run.yaml` |

Two edits cover all five and cannot diverge as a sixth construction is added; five edits at
construction are five places for the next one to be forgotten. Same argument that put
`holdout_values_fault` behind one authority in H3d.

**Read `diagnostics.py` before writing the edit — `render()` is on `Collector`, not on
`Diagnostic`.** `Diagnostic` is a frozen four-field dataclass (`level`, `code`, `path`, `message`)
with no methods at all; `Collector` holds `findings` and does the rendering. Redacting per-`Diagnostic`
would need the values at construction, which is exactly what this ruling avoids.

**Decision 4a is a document-only deliverable and it belongs here**, not between tasks 8 and 12:
core redacts only values it read for a **declared** variable, and a step that reaches
`os.environ` for a name no `required_env` or `requires_env` declares holds a value core never saw
and cannot match. Saying so is the difference between a guarantee and an overreaching claim in the
one document whose job is to prevent them.

**The scoping's stated mutation is not one.** It says "the mutation: a step that raises with the
sentinel in its exception text". That is the **fixture** — changing the test's own step source
cannot fail the unmutated test, because it *is* the test. Writing it as the mutation would ship the
fifth blind mutation in three slices, in the slice whose stated purpose is replacing a test that
cannot fail. The mutation is **deleting the redaction call**.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_cli.py`. `_LEAKY_STEP` and
      `_SENTINEL` are free names in that module:

```python
_SENTINEL = "sk-h7c-sentinel-9f3a1c"

_LEAKY_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
import os

from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        token = os.environ["PUBLISHABLE_TEST_TOKEN"]
        # A client library interpolating a key into a URL in its error message is
        # ordinary, and this is the one surface on which that value can reach a
        # record: `runner` writes a failed execution's exception text into both
        # `executions.jsonl` and `run.yaml`.
        raise RuntimeError("POST https://api.example/v1?key=" + token + " returned 401")
"""

_SECRET_USING_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
import os

from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        token = os.environ["PUBLISHABLE_TEST_TOKEN"]
        for unit in io.units:
            io.record(unit.key, {{"present": True}})
        return {{"token_len": len(token)}}
"""


def _files_under(results_dir):
    """Every file a run wrote, as a list of paths — the FILE LIST is what gets
    filtered, never the sweep's output. Filtering the output of a search for a
    string is how this repo lost a true hit once already.

    Globbed rather than enumerated: `allocation.json` exists only under an
    assignment or a holdout, and a fixture that declares neither would make a
    named-file assertion vacuous or wrong.
    """
    return [p for p in sorted(results_dir.rglob("*")) if p.is_file()]


def test_a_credential_value_reaches_no_artifact_and_the_redaction_says_so(
    tmp_path, monkeypatch, capsys
):
    """The one accident this slice must survive: a step whose exception text
    carries the value core read.

    Three assertions, and the first is the one that makes the other two mean
    something — a sweep for absence passes identically if nothing ran.
    """
    import publishable.generators.experiment as experiment_gen

    monkeypatch.delenv("PUBLISHABLE_TEST_TOKEN", raising=False)
    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _LEAKY_STEP)
    monkeypatch.setattr(
        "publishable.templates.builtin.generic.GenericTemplate.required_env",
        ["PUBLISHABLE_TEST_TOKEN"],
    )

    doc = run_a_project(
        tmp_path,
        units=4,
        _env_file=f"PUBLISHABLE_TEST_TOKEN={_SENTINEL}\n",
        expect_exit=EXIT_PARTIAL,
        capsys=capsys,
    )
    run_dir = doc["run_dir"]
    run = yaml.safe_load((run_dir / "run.yaml").read_text())

    # 1. SOMETHING THAT MUST REPORT. The execution failed, its error was recorded,
    #    and the redaction announced itself by naming the variable.
    ledger = [
        json.loads(line)
        for line in (run_dir / "executions.jsonl").read_text().splitlines()
        if line.strip()
    ]
    errors = [e["error"] for e in ledger if e["error"]]
    assert errors, "no execution failed — the sweep below would be vacuous"
    assert all("<redacted:PUBLISHABLE_TEST_TOKEN>" in e for e in errors), errors
    # The surrounding text SURVIVES: scrubbing the whole message destroys the
    # debugging the record exists for.
    assert all("RuntimeError" in e and "returned 401" in e for e in errors), errors

    # 2. The same, as `run.yaml` arranges it — a second surface, not a rephrasing
    #    of the first.
    recorded = json.dumps(run)
    assert "<redacted:PUBLISHABLE_TEST_TOKEN>" in recorded

    # 3. The sweep. The FILE LIST is filtered, never the output.
    swept = _files_under(doc["results_dir"])
    assert swept, "no artifacts were written — the sweep would be vacuous"
    for path in swept:
        assert _SENTINEL not in path.read_bytes().decode("utf-8", "replace"), path
    # stdout/stderr, captured by the helper because `capsys` was passed.
    assert _SENTINEL not in (doc["stdout"] or "")
    assert _SENTINEL not in (doc["stderr"] or "")


def test_a_step_reads_its_credential_and_the_value_still_reaches_no_artifact(
    tmp_path, monkeypatch, capsys
):
    """The success path, with something that must report: the step got the real
    value and returned its length. Without this, the sweep above proves only that
    a *failed* run leaks nothing."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.delenv("PUBLISHABLE_TEST_TOKEN", raising=False)
    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SECRET_USING_STEP)
    monkeypatch.setattr(
        "publishable.templates.builtin.generic.GenericTemplate.required_env",
        ["PUBLISHABLE_TEST_TOKEN"],
    )

    doc = run_a_project(
        tmp_path, units=4, _env_file=f"PUBLISHABLE_TEST_TOKEN={_SENTINEL}\n", capsys=capsys
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    # Pin ONE spelling, derived from the document rather than guessed: print
    # `run["results"]` once for this fixture, find where `token_len` lands, and
    # write that access path here. An `or` between two candidate spellings passes
    # if either happens to hold and proves nothing about which.
    assert json.dumps(run).count(f'"token_len": {len(_SENTINEL)}') >= 1, run["results"]
    swept = _files_under(doc["results_dir"])
    assert swept, "no artifacts were written — the sweep would be vacuous"
    for path in swept:
        assert _SENTINEL not in path.read_bytes().decode("utf-8", "replace"), path
    assert _SENTINEL not in (doc["stdout"] or "")
    assert _SENTINEL not in (doc["stderr"] or "")
```

**Three fixture facts to check before running, not after.** (i) `run_a_project`'s docstring says a
step whose `run` raises is *contained* — that execution lands `status: "failed"`, the rest of the
plan runs, `run_status` turns it into `partial` and so `EXIT_PARTIAL`; that is why the first test
passes `expect_exit=EXIT_PARTIAL` and the second does not. (ii) `_env_file` is task 8's addition to
`run_a_project`. (iii) **Do not assert on `allocation.json`** — it exists only under an assignment
or a holdout and this fixture declares neither. `_files_under` globs, which is the correct way to
say "every artifact".

- [ ] **Step 2: Run and see them fail.** The first fails on
      `"<redacted:PUBLISHABLE_TEST_TOKEN>" in e` and again on the sweep, with the sentinel present
      in `executions.jsonl` and `run.yaml`. The second should already pass **only if task 8 landed**
      — if it fails on `KeyError: 'PUBLISHABLE_TEST_TOKEN'`, the run-side load is missing.

- [ ] **Step 3a: Implement the `Collector.render()` boundary.** In
      `src/publishable/diagnostics.py` — which today imports only `dataclasses`, so
      `from publishable.secrets import redact` is acyclic (`secrets.py` imports `os`, `pathlib` and
      `dotenv` and nothing from this package). Add a field to `Collector` and redact in `render()`:

```python
@dataclass
class Collector:
    """`validate` collects rather than stops, so findings are appended, never raised."""

    findings: list[Diagnostic] = field(default_factory=list)
    credentials: dict[str, str] = field(default_factory=dict)
    """The credential values core read for a DECLARED variable, if any were.

    Set by whoever knows them — `validate_config`, which resolves the same two
    declarations it checks, and `command_run` for the collectors it builds after
    it. Redaction happens at `render`, the one place a finding's text becomes
    output, rather than at each of the five sites that build an exception string:
    a diagnostic carrying a template's or a user package's exception is minted in
    four places and a sixth is one commit away. `Diagnostic` stays a plain frozen
    record so a message is never rewritten before the collector that owns it
    decides to print.

    Empty is the default and the honest one: a collector nobody gave values to
    redacts nothing, because there is nothing it was told to look for.
    """
```

and, in `render()`, replace the message line:

```python
        for f in self.findings:
            lines.append(f"  {f.level:<7} {f.code:<20} {f.path}")
            # `or f.message` narrows `str | None` to `str` for the type checker;
            # `redact` returns its argument unchanged when there is nothing to do.
            lines.append(f"          {redact(f.message, self.credentials) or f.message}")
```

Then wire the two owners:

- In `validate.py`'s `validate_config`, immediately after `_check_requires_env(doc, template, c)`
  (task 10's call), set `c.credentials = credential_values(declared_credential_names_for(doc,
  template))` — **or**, if that would duplicate the collector task 12 step 3b writes into `cli.py`,
  hoist a single shared helper. **Decide by reading**: if `cli.declared_credential_names` and the
  validate-side collector would be the same function, put it in one module and import it, and say
  in the commit message which. Do not ship two.
- In `cli.py`'s `command_run`, after `credentials` is built (step 3b), set
  `aggregate_c.credentials = credentials` where `aggregate_c = Collector()` is constructed, and do
  the same for any other `Collector` built **after** that point whose `render()` can carry a
  user-supplied exception. **Enumerate them by reading**, not from this brief:
  `grep -n "\.render()" src/publishable/*.py` returns seven sites; decide for each whether its
  collector's messages are core-authored (a dirty tree, a manifest drift) or can carry foreign text.
  Setting it on all of them is harmless and is the safer default.

- [ ] **Step 3b: Implement the step-error boundary.** In `src/publishable/runner.py`:

Add `from publishable.secrets import redact` to the import block, add the parameter to
`execute_plan`'s keyword-only signature after `measurements`:

```python
    credentials: dict[str, str] | None = None,
```

document it in `execute_plan`'s docstring in the same register as its neighbours:

```
    `credentials` is `{variable: value}` for every credential core read for a
    *declared* variable — `required_env` and the `requires_env` union. A failed
    execution's exception text is the one surface on which such a value can enter
    a record, so each is replaced there by a marker naming its variable. By exact
    value, never by pattern: core knows what it read, and a pattern check fails
    open on a credential named `instrument_pw` and fails closed on a config value
    that happens to look random. A value a step read from `os.environ` for a name
    nothing declared is outside what core saw and is not matched — see
    `docs/reference.md` § Secrets & credentials.
```

and redact inside `except Exception`, where the step-error text is built:

```python
        except Exception as exc:  # a failed execution never stops the run
            code = getattr(exc, "code", None)
            prefix = f"{code} " if code else ""
            # Redacted where this string is BUILT rather than at each writer:
            # both records — `run.yaml` through `run_record` and
            # `executions.jsonl` below — read from it, so one edit covers both
            # and they cannot diverge. The *other* four places core interpolates
            # an exception are diagnostics, and `Collector.render` covers all of
            # them at once (`docs/reference.md` § Secrets & credentials).
            returned, status = {}, "failed"
            error = redact(f"{prefix}{type(exc).__name__}: {exc}", credentials or {})
```

In `src/publishable/cli.py`'s `command_run`, build the mapping and pass it. **Read these three facts
about that function before writing a line** — the first is a name that does not exist where you would
reach for it, and reaching for it wrongly disables this task's headline deliverable for exactly the
templates it exists to serve:

1. **There is no `template` local in scope before `execute_plan`.** `command_run` binds `template`
   exactly once, at its `get_template(doc.get("experiment_type", ""), repo_root)` call **inside the
   `if roster is not None:` block that runs *after* `execute_plan`**. You must resolve the template
   yourself, earlier.
2. **`get_template(name: str, repo_root: Path | None = None) -> BaseTemplate | None` resolves a
   project-local `templates/*.py` only when `repo_root` is passed** — it goes through
   `registry._merged(repo_root)`, which calls `discover_local`. **Calling it without `repo_root`
   returns `None` for every local template**, `declared_credential_names` then returns `[]`,
   `credentials` is empty, and `redact` becomes a silent no-op for the case this slice exists for.
   Pass `repo_root`. It is already a local by then.
3. **`conditions = expand(doc)` is already a local**, bound before `execute_plan`. Take it as an
   argument rather than expanding a second time — a second `expand` is a second derivation that can
   drift from the one the run actually executes.

Add, immediately after the existing `conditions = expand(doc)` line and before `execute_plan(`:

```python
    # Resolved here rather than read off the later `get_template` call, which is
    # bound after `execute_plan` and inside a roster guard. `repo_root` is passed
    # because without it `registry._merged` never runs `discover_local`, and every
    # project-local template resolves to `None` — which would empty `credentials`
    # and silently turn the redaction below into a no-op for exactly the templates
    # this check is for. Cannot raise: `validate_config` already made the same
    # call and returned without error, or `command_run` returned above.
    run_template = get_template(doc.get("experiment_type", ""), repo_root)
    # Every credential core read for a DECLARED variable — the template's own
    # `required_env`, plus the union its parameters' `requires_env` resolves to.
    # Held for this command only and written nowhere; its single consumer is the
    # redaction in `execute_plan`.
    credentials = credential_values(declared_credential_names(doc, run_template, conditions))
```

Named `run_template`, not `template`, so it cannot be confused with — or accidentally merged into —
the later binding, which this task leaves alone. That later call re-runs local discovery a second
time; the redundancy is pre-existing (`validate_config` already discovered once) and consolidating it
is **out of scope here**.

Add the collector beside `_wide_swept_paths` in `cli.py`:

```python
def declared_credential_names(
    doc: dict[str, Any], template: Any, conditions: "list[Condition]"
) -> list[str]:
    """Every environment variable this config's declarations name.

    The same two collectors `validate` checks — the template's `required_env` and
    the `requires_env` of every value a resolved condition selects — read here for
    their *values* rather than for their presence. Deliberately the same set: core
    redacts exactly what it was told to look for, which is what makes the answer a
    fact rather than a guess.

    Takes the already-expanded `conditions` rather than expanding again, so the
    set core redacts is derived from the same condition list the run executes.

    A `None` template yields the empty list, which is the honest answer for a name
    that resolves to nothing — but it is also indistinguishable from a template
    declaring no credentials, so the caller's job is to pass a template that was
    resolved WITH `repo_root`.
    """
    names: list[str] = list(getattr(template, "required_env", None) or [])
    spec = getattr(template, "parameter_spec", None) or {}
    declared = _flatten_parameters(doc.get("parameters"))
    for condition in conditions:
        resolved = dict(declared)
        for path, value in condition.values.items():
            if path not in condition.selectors:
                resolved[path] = value
        for path, param in spec.items():
            mapping = getattr(param, "requires_env", None)
            if not mapping:
                continue
            value = resolved.get(path, param.default)
            try:
                names.extend(mapping.get(value) or [])
            except TypeError:
                continue
    return names
```

**`_flatten_parameters` does not exist in `cli.py`** — confirm with
`grep -n "_flatten" src/publishable/cli.py` before naming it. Do **not** import `validate._flatten`,
which is private to that module; write the four-line flatten locally and say in its docstring that it
mirrors `validate._flatten` for one caller rather than reaching across a module boundary for a
private name.

**`Condition` is already imported into `cli.py` under `TYPE_CHECKING`** — `if TYPE_CHECKING:` holds
`from publishable.sweep import Condition` beside `Comparison` and `ExecutionResult`, and
`_baseline_comparisons` and `_declared_comparisons` both annotate it as the quoted
`"list[Condition]"`. **Quote the annotation the same way; do not add a runtime import.** `expand` is
already in `cli.py`'s `from publishable.sweep import (...)` block and `get_template` is already
imported from `publishable.templates.registry`. **Confirm all three before writing, and add only
`credential_values`/`redact` — which are genuinely missing.**

Finally pass it at the call: add `credentials=credentials,` to the `execute_plan(` keyword list.

- [ ] **Step 4: Run and see them pass.** Both new tests, then the full suite.

- [ ] **Step 4b: The `Collector.render()` boundary needs its own fixture — the step-error path does
      not reach it.** Both tests in step 1 go through `runner.py`'s construction. If step 3a were
      reverted wholesale they would stay green, and the second boundary would be pinned by
      **nothing** — the shape that shipped a headline deliverable unpinned last slice.

      **Reachability, verified rather than assumed.** `cli.py:1937` sits in the per-condition,
      per-recording-step loop that calls `template.aggregate(...)`; the template comes from the
      `get_template(..., repo_root)` call, so a **project-local** template's `aggregate` is the one
      invoked. `tests/test_cli.py` already has three tests asserting `"W-STATS-AGGREGATE-FAILED" in
      doc["stdout"]` (one of them patches `GenericTemplate.aggregate` to return a value whose
      resample fails), so the construction, the collector, the `print(aggregate_c.render())`, and
      `capsys` reaching `doc["stdout"]` are all live today. An `aggregate` that **raises** lands on
      `cli.py:1937` directly. Confirm this by running the test and reading the captured stdout
      before trusting the assertion.

      This test reuses task 12 step 7's `_local_template` keyword and the same project shape, so
      write it **after** step 7's helper lands or write step 7 first — the two are one fixture family
      and the order between them is free.

```python
_AGGREGATE_LEAKING_TEMPLATE = """\
import os

from publishable import BaseTemplate, Param, register_template


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    required_env = ["PUBLISHABLE_TEST_AZURE"]
    parameter_spec = {}

    def aggregate(self, units, cfg):
        # A template's own exception reaches stdout through
        # `W-STATS-AGGREGATE-FAILED`, never through `run.yaml` — `run_record`
        # has no diagnostics channel. So this is a leak the step-error path
        # cannot see and the render boundary must catch.
        raise RuntimeError("upstream rejected key " + os.environ["PUBLISHABLE_TEST_AZURE"])
"""


def test_a_template_exception_printed_as_a_warning_is_redacted_too(tmp_path, monkeypatch, capsys):
    """The second serialization boundary, `Collector.render()`.

    `aggregate` raising is one of five places core builds a
    `f"...{type(exc).__name__}: {exc}"` string, and four of them are diagnostics
    rather than records. This one reaches stdout and nothing else, so the step
    tests above are blind to it — reverting `diagnostics.py` alone leaves all of
    them green and this one red, which is the whole reason it exists.
    """
    monkeypatch.delenv("PUBLISHABLE_TEST_AZURE", raising=False)

    doc = run_a_project(
        tmp_path,
        units=4,
        experiment_type="cred_assay",
        _local_template=_AGGREGATE_LEAKING_TEMPLATE,
        _env_file=f"PUBLISHABLE_TEST_AZURE={_SENTINEL}\n",
        capsys=capsys,
    )
    out = doc["stdout"] or ""
    # SOMETHING THAT MUST REPORT: the warning fired, and it announced the
    # redaction by naming the variable. Without the first assertion the two
    # below pass identically on a build where `aggregate` was never called.
    assert "W-STATS-AGGREGATE-FAILED" in out, out
    assert "<redacted:PUBLISHABLE_TEST_AZURE>" in out, out
    # The surrounding text survives — the warning is still diagnosable.
    assert "upstream rejected key" in out, out
    # And the value is nowhere: stdout, stderr, and every artifact.
    assert _SENTINEL not in out
    assert _SENTINEL not in (doc["stderr"] or "")
    swept = _files_under(doc["results_dir"])
    assert swept, "no artifacts were written — the sweep would be vacuous"
    for path in swept:
        assert _SENTINEL not in path.read_bytes().decode("utf-8", "replace"), path
```

      **Check before believing it:** the run must reach `EXIT_OK` (an `aggregate` that raises is
      contained — `cli.py`'s own comment says the warning is emitted "alone", without setting
      `status = "failed"`), and the scaffolded step must actually record a column, or `aggregate` is
      never called for any step and the first assertion fails. `run_a_project`'s default
      `STARTER_STEP` calls `io.record`, so it does — confirm by reading the captured stdout.

- [ ] **Step 5: Document decision 3 and decision 4a.** In `reference.md` § Secrets & credentials,
      after the sentence about `report` and `diff` being safe to send as-is, add:

```
**An exception's text can carry a value by accident, and it is refused rather than tolerated.** A client library that interpolates a key into a URL in its error message is ordinary, and core turns an exception into text a reader sees in two places: a failed execution's `error`, written into both `run.yaml` and `executions.jsonl`, and a [diagnostic](#exit-codes-and-diagnostics) printed to stdout or stderr — which is how a template's `aggregate` failure and an entrypoint that raises at import reach you. Core replaces each credential value it read with `<redacted:VARIABLE_NAME>` at both, and leaves the rest of the message intact, because the record exists to be debugged from — and it says a redaction happened rather than scrubbing silently, so a reader knows both what was removed and which variable to look at. The match is by **exact value, never by pattern**: core knows what it read out of the environment, so it answers the direct question instead of guessing from a name ending `_KEY` or from how random a string looks.

**The limit of that, stated rather than discovered.** Core redacts only values it read for a **declared** variable — one named in a template's `required_env`, or in the `requires_env` of a value a condition resolves. `io` hands a step no credential, so a step that reaches `os.environ` for a name no declaration mentions holds a value core never saw and cannot match. Declare it, and it is covered; don't, and the redaction is not a guarantee the code can provide.
```

Then run the mechanical pass over § Secrets & credentials.

- [ ] **Step 6: Mutate — one per boundary, plus one named as blind.** The pair is the point: each
      mutation must redden **its own** boundary's tests and leave the other boundary's **green**.
      Two boundaries that both went red under one mutation would mean one of them is doing nothing.

  **(a) Remove the step-error boundary.** In `runner.py`, change the `error = redact(...)` line back
  to `error = f"{prefix}{type(exc).__name__}: {exc}"`.
  `test_a_credential_value_reaches_no_artifact_and_the_redaction_says_so` must FAIL — on the
  `"<redacted:…>" in e` assertion first, and again on the file sweep — and so must step 7's
  `test_a_project_local_template_s_credentials_are_redacted_too`. **Checked against the test bodies:**
  each fixture's step raises with the sentinel in its message and passes
  `expect_exit=EXIT_PARTIAL`, which guarantees the run reaches the ledger, so the two branches
  genuinely differ. **Step 4b's `test_a_template_exception_printed_as_a_warning_is_redacted_too`
  must stay GREEN** — its sentinel never touches `ExecutionResult.error` at all. Confirm both halves.

  **(b) Remove the `Collector.render()` boundary — the retargeted 12b.** In `diagnostics.py`, change
  `render()`'s message line back to `lines.append(f"          {f.message}")`, leaving the
  `credentials` field in place so the mutation is one line.
  **`test_a_template_exception_printed_as_a_warning_is_redacted_too` must FAIL**, on
  `"<redacted:PUBLISHABLE_TEST_AZURE>" in out` and again on `_SENTINEL not in out`.
  **Checked against that test's body:** its sentinel reaches output *only* through
  `W-STATS-AGGREGATE-FAILED` → `aggregate_c.render()` → `print(...)` → `capsys` → `doc["stdout"]`,
  and the test asserts on `doc["stdout"]`, so the mutated and unmutated branches produce different
  strings. **Both step-1 tests and step 7's must stay GREEN** — `runner.py` still redacts, and their
  assertions are over `executions.jsonl`, `run.yaml` and the artifact sweep.

  This replaces an earlier mutation ("move the redaction into `run_record._execution_block`") which
  rested on the false premise that there was one construction site. Its *intent* — proving the test
  can see a boundary that was skipped — is what (b) now does, against a boundary that genuinely
  exists.

  **(c) Redact by pattern instead of by value.** Change `redact`'s loop to replace any
  `sk-`-prefixed token. Every test above would still pass — both sentinels start with `sk-`.
  **This mutation is BLIND and is named here so nobody proposes it as a check.** The pattern reading
  is refused in `tests/test_secrets.py`'s
  `test_redaction_replaces_the_exact_value_and_names_the_variable`, whose `sk-zzzzzz`-untouched
  assertion is the fixture that can tell by-value from by-pattern. **The property is covered there
  and needs nothing here.**

  Revert each by editing the file back in place; delete `__pycache__`; re-run; confirm green.
  **Never `git checkout --`.**

- [ ] **Step 7: The third test — a credential that arrives through a project-local template.**
      **Not optional, and not an accepted gap.** Both tests above patch `GenericTemplate`, a *core*
      template, which `get_template` resolves whether or not `repo_root` is passed. So both stay
      green under the exact wiring defect step 3 warns about: a `get_template` call missing its
      `repo_root` empties `credentials` for every project-local template and turns `redact` into a
      no-op, while every mutation above still discriminates. That is the shape this repo has shipped
      twice — a headline deliverable wired through a lookup that works for the fixture and fails open
      for the real case. The fixture must come the way a real one does.

      This also closes `declared_credential_names`'s **`requires_env` half**, which the two tests
      above do not reach at all.

      **`run_a_project` needs a second keyword, `_local_template`, and it lands in task 8 beside
      `_env_file`** — a `templates/` file must exist before `git add .` runs, or `run` refuses the
      tree as dirty (`E-CODE-DIRTY` covers `src/**` and `templates/**`). Add to task 8's signature:

```python
    _local_template: str | None = None,
```

and, in the same place `_env_file` is written (after `main(["new", str(root)])`):

```python
    if _local_template is not None:
        # Written before the commit below, because `code_hash` covers
        # `templates/**` and `run` refuses a dirty tree.
        (root / "templates").mkdir(exist_ok=True)
        (root / "templates" / "cred_assay.py").write_text(_local_template)
```

The config must then name it: pass `experiment_type="cred_assay"` through `**overrides`, which
`run_a_project` already merges onto the generated `config.yaml` as top-level keys.

Then the test:

```python
_LOCAL_CRED_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    required_env = ["PUBLISHABLE_TEST_TOKEN"]
    parameter_spec = {
        "llm.provider": Param(
            str,
            default="azure_openai",
            choices=["azure_openai", "openai"],
            requires_env={
                "azure_openai": ["PUBLISHABLE_TEST_AZURE"],
                "openai": ["PUBLISHABLE_TEST_OPENAI"],
            },
        )
    }
"""


def test_a_project_local_template_s_credentials_are_redacted_too(tmp_path, monkeypatch, capsys):
    """The case `get_template` answers wrongly when `repo_root` is not passed.

    Both tests above patch `GenericTemplate`, which resolves either way — so
    neither can see a `declared_credential_names` that got `None` back and
    returned `[]`. This one can: nothing here is a core template, and the value
    that must be redacted is the one `requires_env` names.
    """
    import publishable.generators.experiment as experiment_gen

    for name in ("PUBLISHABLE_TEST_TOKEN", "PUBLISHABLE_TEST_AZURE", "PUBLISHABLE_TEST_OPENAI"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _LEAKY_AZURE_STEP)

    doc = run_a_project(
        tmp_path,
        units=4,
        experiment_type="cred_assay",
        parameters={"llm": {"provider": "azure_openai"}},
        _local_template=_LOCAL_CRED_TEMPLATE,
        _env_file=(
            "PUBLISHABLE_TEST_TOKEN=irrelevant\n"
            f"PUBLISHABLE_TEST_AZURE={_SENTINEL}\n"
        ),
        expect_exit=EXIT_PARTIAL,
        capsys=capsys,
    )
    ledger = [
        json.loads(line)
        for line in (doc["run_dir"] / "executions.jsonl").read_text().splitlines()
        if line.strip()
    ]
    errors = [e["error"] for e in ledger if e["error"]]
    assert errors, "no execution failed — the sweep below would be vacuous"
    assert all("<redacted:PUBLISHABLE_TEST_AZURE>" in e for e in errors), errors

    swept = _files_under(doc["results_dir"])
    assert swept, "no artifacts were written — the sweep would be vacuous"
    for path in swept:
        assert _SENTINEL not in path.read_bytes().decode("utf-8", "replace"), path
```

with `_LEAKY_AZURE_STEP` a copy of `_LEAKY_STEP` reading `PUBLISHABLE_TEST_AZURE` instead. **Check
the config actually validates before believing the run**: a local template's `naming_pattern` must
accept `cohort-pilot` (declared above), and `run_a_project`'s generated config will carry a
`template_version` — confirm whether `_check_versions` skips it for a local template (it does, per
`is_local_template`) rather than assuming. If any unrelated finding appears, fix the fixture, not
the assertion.

**Mutation for this test, and it is the one that matters:** drop `repo_root` from step 3's
`get_template(doc.get("experiment_type", ""), repo_root)` call. This test must FAIL — the template
resolves to `None`, `credentials` is empty, the sentinel reaches `executions.jsonl` — while the two
`GenericTemplate` tests above stay **green**. Verify both halves of that; the green half is what
proves this test was needed.

**What remains unreached even so:** decision **4a's prose** is document-only by construction — it
describes what core *cannot* do, and there is no code to mutate. Named and accepted.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: redact credential values at the two serialization boundaries, and state the limit`

---

