## Task 15: `WRITERS`/`READERS` symmetry, made an enforced invariant

**Files:** Modify `src/publishable/plugins.py`, `src/publishable/artifacts.py`,
`src/publishable/__init__.py`, `docs/reference.md`, `docs/superpowers/spec-defects.md`,
`tests/test_plugins.py`, `tests/test_artifacts.py`.

**Interfaces:**
- Consumes: `artifacts.StepIO._read(path: Path) -> Any`, a `@staticmethod` whose body is
  `suffix = _suffix_for(path.name)` / `if suffix is not None: return READERS[suffix](path.read_bytes())`
  / `return path.read_bytes()`, and whose docstring reads "Inverts the same table `write` dispatches
  through — see `WRITERS`/`READERS`"; `artifacts.READERS`, the five-key inverse;
  `errors.ArtifactError(message, *, code)`.
- Produces: `plugins.register_reader(suffix: str) -> Callable[[F], F]`, exported, writing into
  `artifacts.READERS`; `_read` raising `ArtifactError` · `E-ARTIFACT-UNREADABLE` for a suffix
  `WRITERS` holds and `READERS` does not; `_read`'s docstring corrected; the `spec-defects.md` entry
  task 3 filed, struck.

**The defect, proved by mutation rather than by reading.** The re-scoping's § 5(a) probed it live:
adding `.fastq` to `WRITERS` alone and calling `StepIO._read(Path('a.fastq'))` raised a bare
`KeyError('.fastq')`; deleting the key restored `b'x'`. `_read`'s docstring says it inverts the
table `write` dispatches through, and it does not — it *dispatches* on `WRITERS` and *indexes*
`READERS`, which is true only by the coincidence that the two hold the same keys. § Steps and
artifacts' promise that "what a writer takes is what its reader gives back" is the thing that breaks.

**The mutation that can fail is adding a key to one dict only.** Swapping a *value* between the two
cannot fail — they hold the same keys, so the two branches cannot differ. This is stated in the
scoping and repeated here because it is the exact shape of a blind mutation.

**`E-ARTIFACT-UNREADABLE` is minted here**, in § Errors core raises, beside the `ArtifactError`
family's existing three codes. It is not an `-UNSUPPORTED` refusal and it carries a row.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_artifacts.py`:

```python
def test_a_suffix_with_a_writer_and_no_reader_is_a_coded_refusal(registries, tmp_path):
    """The bare `KeyError` § Steps and artifacts' promise breaks on.

    The mutation that can fail is adding a key to ONE dict — swapping a value
    between them cannot, since both hold the same keys.
    """
    from publishable import artifacts
    from publishable.errors import ArtifactError

    artifacts.WRITERS[".fastq"] = lambda rows: b"x"
    target = tmp_path / "a.fastq"
    target.write_bytes(b"x")

    with pytest.raises(ArtifactError) as excinfo:
        artifacts.StepIO._read(target)
    assert excinfo.value.code == "E-ARTIFACT-UNREADABLE"
    assert ".fastq" in str(excinfo.value)

    # THE CONTROL, produced by the code under test: with the reader supplied,
    # the same path reads. Without this the assertion above would pass for a
    # `_read` that refused every unknown suffix, including the ones it is
    # supposed to hand back as raw bytes.
    artifacts.READERS[".fastq"] = lambda data: {"read": data.decode()}
    assert artifacts.StepIO._read(target) == {"read": "x"}


def test_a_suffix_neither_table_knows_is_still_raw_bytes(tmp_path):
    """The behaviour that must survive the refusal above: an unregistered suffix
    is bytes, and always was."""
    from publishable import artifacts

    target = tmp_path / "a.bin"
    target.write_bytes(b"\x00\x01")
    assert artifacts.StepIO._read(target) == b"\x00\x01"
```

      and to `tests/test_plugins.py`:

```python
def test_register_reader_completes_the_pair_io_read_upstream_needs(registries, tmp_path):
    """Registering both halves is what a plugin does, and the pair is what makes
    the round trip real — asserted as a round trip rather than as two dict
    entries, since two entries is what the broken state also looks like."""
    from publishable import artifacts
    from publishable.plugins import register_reader, register_writer

    @register_writer(".fastq")
    def write_fastq(rows):
        return "|".join(rows).encode()

    @register_reader(".fastq")
    def read_fastq(data):
        return data.decode().split("|")

    target = tmp_path / "a.fastq"
    target.write_bytes(artifacts.WRITERS[".fastq"](["a", "b"]))
    assert artifacts.StepIO._read(target) == ["a", "b"]


def test_a_reader_may_not_claim_a_suffix_core_reads(registries):
    from publishable.errors import ContractError
    from publishable.plugins import register_reader

    with pytest.raises(ContractError) as excinfo:

        @register_reader(".csv")
        def read_csv(data):
            return []

    assert excinfo.value.code == "E-PLUGIN-COLLISION"
```

      `tests/test_artifacts.py` needs the `registries` fixture, which task 12 already put in
      `tests/conftest.py` for exactly this reason — request it by name and add nothing. Confirm it
      is there before writing the test; if it is in `tests/test_plugins.py` instead, task 12 was
      implemented against a stale brief and moving it is this task's first step.

- [ ] **Step 2: Run and see them fail.** The artifacts test fails with `KeyError: '.fastq'` — the
      defect itself, reproduced — and the plugins tests on `ImportError`.

- [ ] **Step 3: Implement.** In `src/publishable/artifacts.py`, replace `_read` whole:

```python
    @staticmethod
    def _read(path: Path) -> Any:
        """Reads back what `write` wrote, through the inverse of the table it
        dispatched on.

        Two tables and one dispatch: `_suffix_for` decides from `WRITERS`, and
        the reader is then looked up in `READERS`. That is an inversion only
        while the two hold the same keys, which core's own five do and a plugin's
        pair need not — so the gap is a coded refusal rather than the bare
        `KeyError` it was, and § Steps and artifacts' promise that what a writer
        takes is what its reader gives back is stated where it can be enforced.
        A suffix *neither* table knows is not a fault at all: it is the raw-bytes
        case `write` already accepts.
        """
        suffix = _suffix_for(path.name)
        if suffix is None:
            return path.read_bytes()
        reader = READERS.get(suffix)
        if reader is None:
            raise ArtifactError(
                f"`{path.name}` claims the suffix `{suffix}`, which has a registered "
                "writer and no reader — a writer and its reader are registered as a "
                "pair, and core cannot invert one it was never given",
                code="E-ARTIFACT-UNREADABLE",
            )
        return reader(path.read_bytes())
```

      `ArtifactError` is already imported in that module. In `src/publishable/plugins.py`, add
      `READERS` to the `artifacts` import and:

```python
def register_reader(suffix: str) -> Callable[[F], F]:
    """Record a reader for `suffix`, the inverse `io.read_upstream` dispatches to.

    Refuses a core suffix for the reason `register_writer` does, and under the
    same code: the pair is one claim on one extension, so redefining half of it
    is redefining it.
    """

    def decorator(fn: F) -> F:
        if suffix in CORE_SUFFIXES:
            raise ContractError(
                f"a reader claims `{suffix}`, which core itself reads — a plugin that "
                "could redefine a core suffix could change what an artifact means "
                "without changing the step that wrote it. Claim a suffix of your own",
                code="E-PLUGIN-COLLISION",
            )
        READERS[suffix] = fn
        return fn

    return decorator
```

      Export it and add `"register_reader"` to `__all__` in sorted position.

- [ ] **Step 4: Document it.** Add a row to § Errors core raises' table, beside the row that reports
      an extension **no writer claims** handed a non-`bytes` object — name that sibling by what it
      does:

```
| [Reading](#steps-and-artifacts) a name whose suffix has a registered writer and no reader. A writer and its reader are [registered as a pair](#creating-a-plugin-publishable-plugin-new), through two entry-point groups, because `io.write` dispatches on the writer table and `io.read_upstream` looks up the reader table — an inversion only while the two hold the same keys. A suffix *neither* table knows is not this fault: that is the raw-bytes case `io.write` already accepts, and it reads back as bytes | `ArtifactError` · `E-ARTIFACT-UNREADABLE` |
```

      Move § The importable surface's `register_reader` `Status` cell to `built`.

- [ ] **Step 5: Strike the defects entry.** Read the `## STRUCK 2026-08-16 — publishable.readers had
      no entry-point group` entry task 3 wrote and confirm every claim in it is now true — the group
      is documented, the decorator exists, and the refusal is coded. If any is not, fix the code
      rather than the entry.

- [ ] **Step 6: Run and see them pass**, then the whole suite. Expected: predecessor's count **+ 4**.
      **`tests/test_artifacts.py` in full is the regression surface** — every `io.write`/`_read`
      round trip for the five core suffixes must be untouched, since `READERS.get` returns the same
      callables `READERS[...]` did for every key that exists.

- [ ] **Step 7: Mutate — three.**

  **(a) Restore the bare index.** Change `reader = READERS.get(suffix)` / the `None` guard back to
  `return READERS[suffix](path.read_bytes())`.
  `test_a_suffix_with_a_writer_and_no_reader_is_a_coded_refusal` must FAIL with `KeyError` raised
  where `ArtifactError` was expected. **Checked against the body:** the test adds `.fastq` to
  `WRITERS` **only**, which is the one arrangement in which the two branches differ. A test that
  swapped a value between the dicts would pass under both.

  **(b) Refuse the raw-bytes case too.** Change `if suffix is None: return path.read_bytes()` to
  raise the same `ArtifactError`. `test_a_suffix_neither_table_knows_is_still_raw_bytes` must FAIL,
  and so must several pre-existing `tests/test_artifacts.py` round trips over unregistered
  extensions. **Checked against the body:** the test writes `a.bin`, whose suffix is in neither
  table, and asserts the bytes come back. This is the mutation that keeps the refusal narrow.

  **(c) Let a reader claim a core suffix.** Delete `register_reader`'s `CORE_SUFFIXES` raise.
  `test_a_reader_may_not_claim_a_suffix_core_reads` must FAIL with `DID NOT RAISE`.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green.

- [ ] **Step 8: Which deliverable no mutation reaches.** **The invariant is enforced at the read,
      not at registration** — a plugin that registers a writer and never a reader is refused only
      when something reads that suffix, and no test asserts that `register_writer` alone leaves the
      tables asymmetric, because asserting that would pin the absence of a check this task
      deliberately did not add. Registering the pair is the plugin author's obligation and the
      diagnostic names it; a registration-time check would have to know whether the reader is
      merely registered *later in the same module*, which it cannot. Stated as a design consequence,
      not a gap: **nothing closes it and nothing should.**

- [ ] **Step 9: Verify and commit.** All four commands.
      `feat: register_reader, and a suffix with no reader is a coded refusal rather than a KeyError`

---

