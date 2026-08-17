## Task 14: `register_writer`, and the refusal of a core-suffix claim

**Files:** Modify `src/publishable/plugins.py`, `src/publishable/artifacts.py`,
`src/publishable/__init__.py`, `docs/reference.md`, `tests/test_plugins.py`.

**Interfaces:**
- Consumes: `artifacts.WRITERS`, a module dict whose keys are `.json`, `.yaml`, `.jsonl`, `.csv`,
  `.parquet`; `artifacts._suffix_for(name: str) -> str | None`, which lower-cases the name's last
  path component and returns the **longest** registered suffix of it, iterating `WRITERS`;
  `artifacts.StepIO.write(self, name, obj) -> Path`, which calls `WRITERS[suffix](obj)` when
  `_suffix_for` answers.
- Produces: `artifacts.CORE_SUFFIXES: frozenset[str]`, snapshotted at import;
  `plugins.register_writer(suffix: str) -> Callable[[F], F]`, exported, writing straight into
  `artifacts.WRITERS`; a `ContractError` · `E-PLUGIN-COLLISION` for a suffix core itself writes.

**One table, not two.** `register_writer` writes into `artifacts.WRITERS` rather than keeping a
mapping of its own, because `io.write` dispatches through `_suffix_for`, which iterates `WRITERS`,
and a second table would be a second source of truth for "what suffix does core know" — the
defaults-file problem in a dict. `plugins.py` importing `artifacts` introduces no cycle:
`artifacts` imports `coercion`, `errors` and `sweep`, none of which reaches back.

**The key space here is an extension, not a name**, which is why the refusal is a *shadow* check
rather than a *duplicate* check. Two distributions claiming one extension is task 8's
`E-PLUGIN-COLLISION` over the `publishable.writers` group, decided from metadata and reported by
`validate`; a plugin claiming an extension **core** writes is decided here, at registration, because
core's own table is not in anyone's metadata. **One code, two decision points, deliberately** —
§ Creating a plugin's "A name is claimed once" paragraph puts both in one sentence, and splitting
the code would make a reader grep two.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_plugins.py`:

```python
def test_a_third_party_suffix_reaches_io_write_s_dispatch(registries, tmp_path):
    """Registration is only real if `io.write` finds it, so the assertion is over
    the dispatch rather than over the dict — `_suffix_for` is what decides, and
    it iterates `WRITERS`."""
    from publishable import artifacts
    from publishable.plugins import register_writer

    @register_writer(".fastq.gz")
    def write_fastq(rows):
        return b"@read\n"

    assert artifacts._suffix_for("sample.fastq.gz") == ".fastq.gz"
    assert artifacts.WRITERS[".fastq.gz"] is write_fastq

    # The longest registered suffix still wins, which is what a compound
    # extension is registered for: `.gz` alone must not claim this name.
    @register_writer(".gz")
    def write_gz(rows):
        return b""

    assert artifacts._suffix_for("sample.fastq.gz") == ".fastq.gz"


def test_a_writer_may_not_claim_a_suffix_core_writes(registries):
    """A plugin that could redefine `.csv` could change what an artifact means
    without changing the step that wrote it."""
    from publishable.errors import ContractError
    from publishable.plugins import register_writer

    with pytest.raises(ContractError) as excinfo:

        @register_writer(".csv")
        def write_csv(rows):
            return b""

    assert excinfo.value.code == "E-PLUGIN-COLLISION"
    message = str(excinfo.value)
    assert ".csv" in message
    assert "core" in message


def test_a_suffix_core_does_not_write_is_accepted(registries):
    """THE CONTROL, and the honouring: a refusal that fired for every suffix
    would pass the test above. Paired here rather than left implicit."""
    from publishable import artifacts
    from publishable.plugins import register_writer

    @register_writer(".fastq")
    def write_fastq(rows):
        return b""

    assert ".fastq" in artifacts.WRITERS
```

- [ ] **Step 2: Run and see them fail.** `ImportError: cannot import name 'register_writer'`.

- [ ] **Step 3: Implement.** In `src/publishable/artifacts.py`, immediately beneath the `READERS`
      dict:

```python
CORE_SUFFIXES = frozenset(WRITERS)
"""The suffixes core itself writes, fixed at import.

Snapshotted rather than read live, because `plugins.register_writer` adds to
`WRITERS` and a shadow check reading the live table would start refusing one
plugin's suffix on behalf of another's. What a plugin may not claim is what
*core* writes, which is a property of this file and not of what is installed.
"""
```

      In `src/publishable/plugins.py`, add `from publishable.artifacts import CORE_SUFFIXES, WRITERS`
      and `from publishable.errors import ContractError`, then:

```python
def register_writer(suffix: str) -> Callable[[F], F]:
    """Record a writer for `suffix` in the table `io.write` dispatches through.

    One table rather than a registry of its own: `io.write` finds a writer with
    `_suffix_for`, which iterates `artifacts.WRITERS`, and a second mapping would
    be a second answer to "what suffix does core know".

    A suffix core itself writes is refused here rather than resolved by import
    order — `reference.md` § Creating a plugin — because a plugin that could
    redefine `.csv` could change what an artifact means without changing the step
    that wrote it. Two *plugins* claiming one suffix is the other half of the same
    rule and is decided from entry-point metadata by `validate`, since core's own
    table appears in nobody's metadata and an installed pair appears in no table.
    """

    def decorator(fn: F) -> F:
        if suffix in CORE_SUFFIXES:
            raise ContractError(
                f"a writer claims `{suffix}`, which core itself writes — a plugin that "
                "could redefine a core suffix could change what an artifact means "
                "without changing the step that wrote it. Claim a suffix of your own",
                code="E-PLUGIN-COLLISION",
            )
        WRITERS[suffix] = fn
        return fn

    return decorator
```

      Export it from `publishable/__init__.py` and add `"register_writer"` to `__all__` in sorted
      position.

- [ ] **Step 4: Move the `Status` cell and correct one document claim.** In § The importable
      surface, task 3's row `` `register_writer` · `register_reader` `` must split so the two
      statuses differ; `register_writer` becomes `built`, `register_reader` stays `not yet built`
      until task 15:

```
| `register_writer` | decorator | built | The registry an artifact suffix's writer is claimed through — see [Steps and artifacts](#steps-and-artifacts) |
| `register_reader` | decorator | not yet built | Its inverse, which `io.read_upstream` dispatches through — see [Steps and artifacts](#steps-and-artifacts) |
```

      In § Errors core raises, the `E-PLUGIN-COLLISION` row task 2 wrote already names the
      core-suffix case; read it and confirm it does, and change nothing if so.

- [ ] **Step 5: Run and see them pass**, then the whole suite. **`tests/test_artifacts.py` is the
      regression surface** — `WRITERS` and `READERS` are module dicts and a test that leaks a key
      breaks unrelated dispatch. Run `uv run pytest tests/test_artifacts.py -q` on its own **and**
      then the whole suite in one process, and compare: a `registries` fixture that fails to restore
      shows as a pass alone and a failure together. Expected total: predecessor's count **+ 3**.

- [ ] **Step 6: Mutate — three.**

  **(a) Write into a private table.** Change `WRITERS[suffix] = fn` to a module-level
  `_PLUGIN_WRITERS[suffix] = fn`. `test_a_third_party_suffix_reaches_io_write_s_dispatch` must FAIL
  on its `_suffix_for` assertion. **Checked against the body:** the assertion is over the dispatch
  function, not over a dict this task controls, so a second table cannot satisfy it. **This is the
  mutation that pins "one table, not two"**, and the `WRITERS[".fastq.gz"] is write_fastq`
  assertion alone would not.

  **(b) Read the live table for the shadow check.** Change `if suffix in CORE_SUFFIXES:` to
  `if suffix in WRITERS:`. **Nothing in the suite goes red**, and that is worth knowing before it is
  believed: no test registers one plugin suffix and then a second plugin's identical one. **Add the
  fixture that discriminates** rather than accepting a blind mutation — append to
  `test_a_suffix_core_does_not_write_is_accepted`:

```python
    # A second plugin claiming the SAME suffix is not this check's refusal — it
    # is decided from entry-point metadata, where both claimants are visible.
    # Registering twice in one process is what a plugin's own test suite does,
    # and refusing it here would refuse that.
    @register_writer(".fastq")
    def write_fastq_again(rows):
        return b""

    assert artifacts.WRITERS[".fastq"] is write_fastq_again
```

  With that appended, mutation (b) makes the test FAIL on the second registration's raise. Run the
  mutation **after** adding the assertion, and record in the task report that the mutation was blind
  until the fixture was sized for it.

  **(c) Refuse nothing.** Delete the `if suffix in CORE_SUFFIXES:` raise.
  `test_a_writer_may_not_claim_a_suffix_core_writes` must FAIL with `DID NOT RAISE`. **Checked
  against the body:** it wraps the decoration in `pytest.raises`, so the absence of the raise is the
  failure. Note this mutation also leaves `.csv` overwritten in `WRITERS` — the `registries` fixture
  restores it, which is the fixture doing its job; if a later test in the same run fails on CSV
  encoding, the fixture is wrong and that is the finding.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green.

- [ ] **Step 7: Which deliverable no mutation reaches.** **`CORE_SUFFIXES`' membership** is a
      snapshot of a literal and a mutation adding a suffix to `WRITERS` above the snapshot line
      would change both together — unavoidable for a derived constant, and the reason the docstring
      states what it is rather than listing it. **`register_writer` has no production caller**: no
      plugin is imported in this slice, so `WRITERS` is only ever extended by a test. The reader for
      the *object* arrives when a plugin is loaded at `run`, which no task here owns; task 15 makes
      the *table's* invariant enforceable, which is the half that is closable now.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: register_writer feeds io.write's own table, and refuses a suffix core writes`

---

