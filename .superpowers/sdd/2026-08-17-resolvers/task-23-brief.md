## Task 23: the read-only resolver `io`

**Files:** Modify `src/publishable/artifacts.py`, `tests/test_artifacts.py`.

**Interfaces:**
- Consumes: `artifacts.StepIO._read(path: Path) -> Any`, a `@staticmethod` that dispatches through
  `_suffix_for`/`READERS` and raises `ArtifactError` · `E-ARTIFACT-UNREADABLE` for a suffix with a
  writer and no reader; `StepIO.read_input(relpath: str) -> Any`, which is
  `self._read(self.input_dir / relpath)`. `StepIO.__init__` requires keyword `step_dir`,
  `input_dir`, `run_dir` — read it in `artifacts.py`, `class StepIO`.
- Produces: `artifacts.ResolverIO`, constructed as `ResolverIO(input_dir: Path)`, exposing
  `read_input(relpath: str) -> Any` and the property `read_paths -> tuple[str, ...]`.

**Why a new class rather than a `StepIO` with three arguments defaulted.** § Where units come from:
*"The `io` a resolver receives is read-only: `io.read_input` and nothing else. There is no run
directory yet at validate time and no step yet at run time, so there is nothing for it to write
into."* A `StepIO` with `step_dir`/`run_dir` defaulted would carry `write`, `append`, `record`,
`read_upstream`, `read_condition`, `exists`, `resumed` and `skip` into a place where every one of
them either has no directory to act on or would let a resolver write into a run that has not
started. The refusal has to be structural — there is no method to call — rather than a raise per
method, because core cannot inspect the body of user Python.

**`read_paths` exists for `hash_index`, and task 31 is its only reader.** § Where units come from:
*"'the index and whatever it names' means the paths the resolver read plus the paths its units
name."* Recording is here rather than in task 31 because this is the one object that sees a read.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_artifacts.py`:

```python
def test_a_resolver_io_reads_the_input_and_nothing_else(tmp_path):
    """`reference.md` § Where units come from: read-only, `read_input` and
    nothing else. Structural rather than a raise per method — core cannot inspect
    the body of a resolver, so the method must not exist to be called."""
    from publishable.artifacts import ResolverIO

    (tmp_path / "layout.csv").write_text("barcode,well\nA1,h3\n")
    io = ResolverIO(tmp_path)

    assert io.read_input("layout.csv") == [{"barcode": "A1", "well": "h3"}]
    for forbidden in (
        "write",
        "append",
        "record",
        "skip",
        "read_upstream",
        "read_condition",
        "exists",
        "resumed",
        "units",
        "run_dir",
        "step_dir",
    ):
        assert not hasattr(io, forbidden), f"a resolver io must not expose {forbidden}"


def test_a_resolver_io_records_every_path_it_read_in_order(tmp_path):
    """`hash_index` names "the paths the resolver read"; this object is the only
    one that sees a read. Order and duplicate handling are asserted because the
    set task 31 builds is derived from this tuple."""
    from publishable.artifacts import ResolverIO

    (tmp_path / "layout.csv").write_text("barcode\nA1\n")
    (tmp_path / "extra.json").write_text('{"n": 1}')
    io = ResolverIO(tmp_path)

    assert io.read_paths == ()  # the control: nothing read, nothing recorded
    io.read_input("layout.csv")
    io.read_input("extra.json")
    io.read_input("layout.csv")
    assert io.read_paths == ("layout.csv", "extra.json", "layout.csv")


def test_a_resolver_io_reads_through_the_same_table_a_step_does(tmp_path, registries):
    """A plugin's registered reader serves a resolver too — one dispatch, not two.
    Without this, a resolver reading a plugin suffix would get raw bytes while a
    step reading the same file got the parsed object."""
    from publishable.artifacts import ResolverIO
    from publishable.plugins import register_reader, register_writer

    @register_writer(".fq")
    def _write(obj) -> bytes:
        return str(obj).encode()

    @register_reader(".fq")
    def _read(payload: bytes):
        return {"parsed": payload.decode()}

    (tmp_path / "reads.fq").write_bytes(b"ACGT")
    assert ResolverIO(tmp_path).read_input("reads.fq") == {"parsed": "ACGT"}
```

- [ ] **Step 2: Run and see it fail.** `ImportError: cannot import name 'ResolverIO'`.

- [ ] **Step 3: Implement.** In `src/publishable/artifacts.py`, immediately after `class StepIO`:

```python
class ResolverIO:
    """What a resolver receives: `read_input` and nothing else.

    `reference.md` § Where units come from — "The `io` a resolver receives is
    read-only: `io.read_input` and nothing else. There is no run directory yet at
    validate time and no step yet at run time, so there is nothing for it to write
    into." A `StepIO` with its directories defaulted would carry every write and
    every cross-scope read into a place where each either has no directory to act
    on or would let a resolver write into a run that has not started. Core cannot
    inspect the body of user Python, so the refusal is that the method does not
    exist rather than that it raises.

    Reads through `StepIO._read`, the one dispatch, so a plugin's registered
    reader serves a resolver exactly as it serves a step — two dispatches would be
    two answers to "what does this suffix mean".

    Records each relative path it was asked for, in the order it was asked, so
    `input_manifest_policy: hash_index` can name "the paths the resolver read"
    without a second walk that could disagree with what was actually opened.
    Duplicates are kept: this is a log of reads, and its one consumer builds a set
    from it.
    """

    __slots__ = ("input_dir", "_read_paths")

    def __init__(self, input_dir: Path) -> None:
        self.input_dir = input_dir
        self._read_paths: list[str] = []

    def read_input(self, relpath: str) -> Any:
        self._read_paths.append(relpath)
        return StepIO._read(self.input_dir / relpath)

    @property
    def read_paths(self) -> tuple[str, ...]:
        return tuple(self._read_paths)
```

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2067 + 3 = 2070 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/artifacts.py`, delete the
      `self._read_paths.append(relpath)` line from `ResolverIO.read_input`.
      `tests/test_artifacts.py::test_a_resolver_io_records_every_path_it_read_in_order` must
      **FAIL** — the tuple comes back `()` where three entries are asserted. **Checked against the
      test body:** the assertion is on the exact tuple, not on membership or truthiness, so it
      discriminates both the empty case and a de-duplicating one.

      Second mutation, because the first says nothing about the dispatch: change
      `StepIO._read(self.input_dir / relpath)` to `(self.input_dir / relpath).read_bytes()`.
      `test_a_resolver_io_reads_through_the_same_table_a_step_does` must **FAIL** (`b"ACGT"` is not
      `{"parsed": "ACGT"}`) and `test_a_resolver_io_reads_the_input_and_nothing_else` must **FAIL**
      too (raw bytes are not the parsed CSV rows).

      **What no mutation here reaches:** `__slots__`. Its effect — no attribute can be added to a
      `ResolverIO` after construction — is asserted by nothing. Recorded rather than covered; the
      `hasattr` sweep covers the names that matter.

- [ ] **Step 6: Commit.** `artifacts: a read-only ResolverIO — read_input, and the paths it read`

---

