## Task 32: the credential leak, both halves, and the non-`PublishableError` containment

**Files:** Modify `src/publishable/validate.py`, `src/publishable/cli.py`,
`docs/reference.md`, `tests/test_validate.py`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: `secrets.redact(text: str | None, values: Mapping[str, str]) -> str | None` and its
  **two** call sites, `diagnostics.Collector.render` and `runner.execute_plan` — verified by reading
  both; `Collector.credentials: dict[str, str]`, whose own comment says *"Redaction happens at
  render, not at construction … so setting this after the fact still covers every finding already
  appended"*; `cli.main`'s handler, which prints `f"  error   {exc.code:<20} {exc}"` to stderr with
  **no collector in scope**; `cli.command_run`'s existing post-validate collectors `dirty_c`,
  `warn_c`, `drift_c`, each a **fresh** `Collector()` with `.credentials` assigned;
  `cli.declared_credential_names(doc, template, conditions)`; `validate._check_units`'s
  `except ContractError`.
- Produces: `credentials` computed in `command_run` **before** the roster resolves; the roster call
  wrapped, reporting through a fresh redacting collector; `_check_units` gaining a broad arm
  reporting `E-RESOLVER-RAISED`; a § Errors core raises row for `E-RESOLVER-RAISED`.

**Both halves, and the prior prescription was wrong.** Two documents said *"move the credential
computation, not wrap the call."* `redact` has exactly two call sites and `main`'s handler is
neither — it prints `{exc}` raw. **So moving the computation alone produces values nothing
applies.** The working remedy is both: compute the credential set before phase 5 *and* route the
resolver's raise through a redacting surface.

**A fresh collector, not `command_run`'s `c` — a spec-versus-code note.** Decision 2 says "route the
resolver's raise through `command_run`'s existing collector". Taken literally that double-renders:
`c` has already been printed by `if c.findings: print(c.render())` before phase 5, so appending and
re-rendering re-prints every warning and inflates the counts line. Taken as *"through a redacting
surface"* — which is what makes the fix work — a fresh `Collector()` with `.credentials = credentials`
satisfies it, and it is `command_run`'s own convention for a post-validate finding: `dirty_c`,
`warn_c` and `drift_c` all do exactly that. Take the fresh collector.

**Decision 3, and the placement it settles.** `_check_units` guards only `except ContractError`, so
a plugin resolver raising `KeyError` breaks the *"`validate` never raises"* contract (probe B). At
`run` such a raise **escapes `main` entirely as a traceback with the credential in it** (probe D) —
the one output no redacting surface sees. Contain it at both. The broad arm belongs at each command
rather than inside `units._from_resolver`, for a reason worth stating: a guard inside `resolve_units`
would be bypassed by any test that patches `resolve_units` itself, which is exactly how probes B and
D were run and how this task's tests can run *before* task 26 opens the resolver path at `validate`.

**Why the tests use a table source and a monkeypatched `resolve_units`.** This task must land before
task 26, and until 26 a `{resolver: ...}` config earns `E-DATA-RESOLVER-UNSUPPORTED`, which is an
error, so `command_run` returns `EXIT_WRONG` at the validate gate and never reaches phase 5. A
table-source config that validates clean, with the `resolve_units` **binding in each module**
monkeypatched to raise, exercises exactly the plumbing under test — which is what the scoping's four
probes did. Patch `publishable.validate.resolve_units` and `publishable.cli.resolve_units`; both
modules bind the name with `from publishable.units import ...`, so patching `publishable.units`
alone would not take.

**A leak test asserting only an absence passes identically when nothing raised.** Pair every
sentinel sweep with the control that proves the sentinel is reachable — the same arrangement the
scoping used, where probe A's redacted output is what makes probes C and D readable.

- [ ] **Step 1: Write the failing test.** In `tests/test_validate.py`:

```python
def test_a_resolvers_non_contract_raise_does_not_escape_validate(monkeypatch, write_config):
    """Probe B. `validate` is contracted never to raise; a plugin resolver raising
    `KeyError` is user code, and `_check_units` guarded only `ContractError`."""
    import publishable.validate as validate_module

    def _boom(*_args, **_kwargs):
        raise ValueError("resolver failed")

    monkeypatch.setattr(validate_module, "resolve_units", _boom)
    found = messages_by_code(write_config())
    assert "E-RESOLVER-RAISED" in found
    assert "ValueError" in found["E-RESOLVER-RAISED"]


def test_a_resolvers_raise_is_redacted_at_validate(monkeypatch, write_config, tmp_path, git_repo):
    """Probe A, kept as the CONTROL that makes the run-side tests readable: the
    identical exception from the identical function must come back redacted here,
    or a stderr sweep finding no sentinel proves nothing about redaction."""
    import publishable.validate as validate_module

    monkeypatch.setenv("MY_KEY", "SENTINEL-sk-abc123")
    (git_repo / "templates").mkdir(exist_ok=True)
    (git_repo / "templates" / "keyed.py").write_text(_TEMPLATE_REQUIRING_MY_KEY)

    def _boom(*_args, **_kwargs):
        raise ValueError("resolver failed: key=SENTINEL-sk-abc123")

    monkeypatch.setattr(validate_module, "resolve_units", _boom)
    c = Collector()
    validate_config(write_config({"experiment_type": "keyed", "template_version": _DELETE}), c)
    rendered = c.render()
    assert "SENTINEL-sk-abc123" not in rendered
    assert "<redacted:MY_KEY>" in rendered  # the positive companion
```

      (`_TEMPLATE_REQUIRING_MY_KEY` is a project-local template declaring
      `required_env = ["MY_KEY"]`; read `tests/test_validate.py` for an existing local-template
      fixture string before adding a new one, and reuse it if one exists.)

      In `tests/test_cli.py`:

```python
def test_a_resolvers_raise_at_run_is_redacted_rather_than_printed_whole(
    monkeypatch, capsys, ...
):
    """Probes C and D. C: a `ContractError` from resolution printed verbatim
    through `main`'s bare handler. D: a `ValueError` escaping `main` entirely as a
    traceback with the credential in it — the one output no redacting surface
    sees. Both are asserted with the positive companion (the diagnostic IS
    produced, with the marker in it), so a sweep finding no sentinel cannot pass
    on a run that never raised."""
    for exception in (ContractError("resolver failed: key=SENTINEL-sk-abc123", code="E-UNITS-SOURCE-MISSING"), ValueError("resolver failed: key=SENTINEL-sk-abc123")):
        ...
        assert exit_code == EXIT_WRONG                       # no traceback
        assert "SENTINEL-sk-abc123" not in captured
        assert "<redacted:MY_KEY>" in captured               # the positive companion


def test_a_run_whose_roster_resolves_cleanly_still_reports_nothing(...):
    """THE CONTROL for the pair above: the wrap must not turn a healthy run into a
    finding. Without it, a `try` that reported unconditionally would pass both."""
```

- [ ] **Step 2: Run and see it fail.** The `validate` test fails with the `ValueError` propagating
      out of `validate_config`; the `run` tests fail with the sentinel present in stderr (the
      `ContractError` arm) and with a traceback (the `ValueError` arm).

- [ ] **Step 3: Implement.** In `src/publishable/validate.py`, `_check_units`, add a second arm
      after the existing `except ContractError`:

```python
    except Exception as exc:
        # A resolver is user code, and `validate` is contracted never to raise —
        # so anything that is not already a coded refusal becomes one here. The
        # table and glob branches raise `ContractError` and nothing else, so this
        # arm is a resolver's by construction rather than a catch-all over core.
        # `SystemExit` is a `BaseException` and is `load_entry_point`'s to contain
        # at import; a resolver body calling `sys.exit()` mid-iteration is the
        # residual, named rather than swallowed.
        c.error(
            "E-RESOLVER-RAISED",
            "data.units",
            f"resolution raised {type(exc).__name__}: {exc}",
        )
        return None, None, frozenset()
```

      In `src/publishable/cli.py`, `command_run`: move the three lines that resolve the template and
      the credential set — `conditions = expand(doc)`, `run_template = get_template(...)`,
      `credentials = credential_values(declared_credential_names(doc, run_template, conditions))` —
      **above** the phase-5 roster block, keeping their existing comments with them, and leave a
      comment at the old site saying why they moved (the resolver's raise is the first thing in the
      command that can carry a credential into a message). Then wrap the roster call:

```python
    try:
        roster, technical_n, _columns = (
            resolve_units(units_decl, input_dir, cfg=..., resolver_io=resolver_io)
            if units_decl
            else (None, None, frozenset())
        )
    except Exception as exc:
        # `main`'s handler prints `{exc}` with no collector in scope, and a
        # non-`PublishableError` never reaches it at all — it ends the command in
        # a traceback. A resolver's message can carry a credential it read, so the
        # raise is turned into a diagnostic here, through a collector holding the
        # values `redact` answers from. A FRESH collector rather than `c`, which
        # has already been rendered and printed above: appending to it would
        # re-print every earlier finding and inflate the counts line.
        roster_c = Collector()
        roster_c.credentials = credentials
        code = exc.code if isinstance(exc, PublishableError) else "E-RESOLVER-RAISED"
        roster_c.error(code, "data.units", str(exc))
        print(roster_c.render(), file=sys.stderr)
        return EXIT_WRONG
```

      In `docs/reference.md` § Errors core raises, add a row for `E-RESOLVER-RAISED`: a resolver's
      own body raising something that is not a `PublishableError`, contained at `validate` and at
      `run` so it becomes a diagnostic rather than a traceback, since a traceback is the one output
      no redacting surface sees. Cross-reference § Secrets & credentials.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2092 + 5 = 2097 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** **The obvious mutation cannot fail, and it is replaced.** The prior
      documents prescribe *"a test that goes red when the two lines swap"* — `c.credentials` and
      `_check_units` in `validate_config`. Redaction happens at **render**, and `c.credentials`'s
      own comment says so, so swapping them changes nothing: probe A redacts because `c.render()`
      runs after both, not because one precedes the other. Two branches that cannot differ.

      **Mutation (a), the one that discriminates the run-side fix:** in `src/publishable/cli.py`,
      delete the `roster_c.credentials = credentials` line, leaving the ordering intact.
      `tests/test_cli.py::test_a_resolvers_raise_at_run_is_redacted_rather_than_printed_whole` must
      **FAIL** on `"SENTINEL-sk-abc123" not in captured`. **Checked against the test body:** the
      collector still renders and still prints, so the diagnostic exists and only the redaction is
      gone — which is exactly the claim under test, and which a mutation producing an
      `UnboundLocalError` would not have isolated.

      **Mutation (b), the ordering, kept for what it does prove:** move the roster block back above
      the `run_template = get_template(...)` line. The same test must **FAIL** — with
      `UnboundLocalError: credentials`. **Named honestly:** this is red for a mechanical reason
      rather than a redaction one, so it proves the ordering is load-bearing and proves nothing
      about redaction. Both mutations, not one.

      **Mutation (c), the validate-side containment:** change `_check_units`'s new
      `except Exception` to `except ContractError` (i.e. duplicate the existing arm).
      `tests/test_validate.py::test_a_resolvers_non_contract_raise_does_not_escape_validate` must
      **FAIL** with the `ValueError` propagating out of `validate_config`.

      **What no mutation here reaches:** `main`'s handler itself. This task does not close
      `main`'s un-redacted stderr path in general — that is filed OPEN and unowned by H7c, and Part
      B owes only that it does not *widen* the exposure. Say so in the commit message.

- [ ] **Step 6: Commit.** `cli: a resolver's raise becomes a redacted diagnostic, not a traceback`

---

