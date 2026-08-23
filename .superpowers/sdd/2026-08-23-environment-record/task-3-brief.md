## Task 3: THE WRITE — `os`, `hostname` and `hardware` in one dict literal

> **Bindings that reach this task:** **Rulings O and Q** and design Decisions 6–9, all restated below.
> **This task is arm P's SOLE AUTHORIZED EDITOR**, and its post-edit state was written in task 1 before
> anything moved.

**RULING O, restated:** `hardware` is `{"cpu_count": os.cpu_count()}` — a **mapping**, one key, **no
`gpu`**. A GPU is an apparatus fact.

**RULING Q, restated (it binds this task by what it forbids):** `os` and `hardware` are **NOT** redacted
by `study add`; `hostname` **is**. So this task **writes all three plainly** and touches
`study.py`'s `_redact` **not at all** — the wiring for `hostname` already exists and was written
against a key nobody wrote. Task 4 owns the reason and the pin.

**Decision 6 — `os` is the composed form.** `f"{platform.system()}-{platform.release()}-{platform.machine()}"`,
**not `platform.platform()`**. Measured on the design's machine: `platform.platform()` returns
`'macOS-26.5.2-arm64-arm-64bit-Mach-O'` — the marketing name and version rather than the kernel the
same module's `uname()` reports (`Darwin`, `25.5.0`) — and its component count differs per platform
(`-with-glibc2.35` on Linux). `platform.platform(terse=True)` returns `'macOS-26.5.2'`, dropping the
architecture entirely. The composed form yields exactly three components everywhere and is the shape
§ The two files shows (`os: "Linux-6.8.0-x86_64"`).

**Decision 7 — `hostname` is `socket.gethostname()`.** **The sibling that already got it right is the
first place to look**: `src/publishable/run_identity.py` already writes
`json.dump({"host": socket.gethostname(), "pid": os.getpid()}, fh)` into the run lock. Using
`platform.uname().node` would be a second spelling of one fact, which is what `report`'s `repo_root`
row rejects by name (*"two sources for one fact is how the two drift"*).

**Decision 8 — `cpu_count` is `os.cpu_count()` and `None` is written through.** Not `or 1`, not `or 0`.
`os.cpu_count()` is documented to return `None` when the count is indeterminable, and this format
already spells never-captured as `null` (`apparatus: null`, `uv_lock: null`, `units: null`).
`len(os.sched_getaffinity(0))` is **absent on the design's platform** (measured), so it cannot be the
source, and a present-or-fallback scheme would make the key mean two things on two machines.
`os.process_cpu_count()` is 3.13+ and this project targets ≥ 3.11.

**Decision 9 — the key order is § The two files' own.** `manager`, `python_version`, `os`, `hostname`,
`uv_lock`, `uv_lock_hash`, `hardware`.

**The code.** `cli.py` imports **none** of `os`, `platform` or `socket` today — grepped at `2b18435`
for `\bos\.`, `\bplatform\.`, `\bsocket\.` and `import os\b`: **zero hits**. Add the three to the
stdlib block, keeping it alphabetical (`dataclasses`, `importlib`, `importlib.metadata`, `json`, `os`,
`platform`, `socket`, `sys`).

The `environment` value in `command_run`'s `provenance` mapping becomes:

```python
            "environment": {
                "manager": "uv",
                "python_version": ".".join(str(v) for v in sys.version_info[:3]),
                # NOT `platform.platform()`: measured, it reports the marketing
                # name and version (`macOS-26.5.2-arm64-arm-64bit-Mach-O`) rather
                # than the kernel `uname` names (`Darwin`, `25.5.0`), and its
                # component count differs per platform. The composed form yields
                # exactly three components everywhere, which is the shape
                # `reference.md` § The two files shows.
                "os": f"{platform.system()}-{platform.release()}-{platform.machine()}",
                # `socket.gethostname()` and not `platform.uname().node`, which
                # returns the same fact: `run_identity` already answers "what
                # machine is this" this way for the run lock, and two spellings of
                # one fact is how the two drift. Redacted by `study add`.
                "hostname": socket.gethostname(),
                "uv_lock": "environment/uv.lock" if lock_path is not None else None,
                "uv_lock_hash": lock_hash,
                # `cpu_count` alone. A GPU is not universal and core cannot probe
                # one without a dependency or a subprocess, so it is an apparatus
                # fact — `reference.md` § The apparatus core can only observe.
                # `None` is `os.cpu_count()`'s own documented answer for
                # indeterminable and is written through rather than substituted:
                # this format already spells never-captured as `null`.
                "hardware": {"cpu_count": os.cpu_count()},
            },
```

**Steps**

- [ ] Add the three imports and the three keys, exactly as above, in exactly that order.
- [ ] **Edit arm P, and only as specified in task 1.** After `python_version` is popped, add exactly
      three pops and exactly three assertions:

```python
    os_value = environment.pop("os")
    hostname = environment.pop("hostname")
    hardware = environment.pop("hardware")
    assert environment == {"manager": "uv", "uv_lock": None, "uv_lock_hash": None}
    assert isinstance(python_version, str) and python_version
    assert isinstance(os_value, str) and os_value
    assert isinstance(hostname, str) and hostname
    assert isinstance(hardware, dict) and set(hardware) == {"cpu_count"}
```

      **The `assert environment == {...}` line is byte-identical to what task 1 captured.** Report the
      `git diff` for that test and confirm it: three pops added, three assertions added, nothing else.
      Editing the `==` literal, `python_version`'s pop, or any other assertion is a finding.
- [ ] **Fixture A — `os`, with installed sentinels.** Monkeypatch `platform.system` → `"Fixtureos"`,
      `platform.release` → `"9.9.9"`, `platform.machine` → `"fixarch"`; run a project end to end
      through `main(["run", …])`; assert `provenance.environment.os == "Fixtureos-9.9.9-fixarch"`.
      **Sentinels rather than recomputing the composition in the test**: a test that recomputes
      `f"{platform.system()}-…"` and compares is *a mutation whose two branches cannot differ* — it
      would pass against any implementation using the same three calls in any order.
- [ ] **Fixture B — `hostname`.** Monkeypatch `socket.gethostname` → `"pinhost.example.invalid"`;
      assert the record carries that string verbatim. Discriminating against the plausible wrong
      source: `platform.uname().node` is unaffected by this patch.
- [ ] **Fixture C — `hardware`, TWO arms.** Arm 1: monkeypatch `os.cpu_count` → `77`, assert
      `hardware == {"cpu_count": 77}`. Arm 2: monkeypatch it → `None`, assert
      `hardware == {"cpu_count": None}` — **the key present with a null value**, not the key absent.
      One arm cannot distinguish "writes the count" from "writes a constant"; arm 2 is what catches
      `os.cpu_count() or 1`.
- [ ] **Fixture D — the key order.** Assert
      `list(record["provenance"]["environment"]) == ["manager", "python_version", "os", "hostname",
      "uv_lock", "uv_lock_hash", "hardware"]`, read from `yaml.safe_load` of the raw file.
      **Enumerate the literals the list should contain** — never iterate the thing under test, which is
      how a vocabulary test once measured only that a set equals itself.
- [ ] **Run every mutation and report each result**, each against a **copy** of the file:
      **1** delete `"os"` → Fixtures A and D fail, arm P fails.
      **2** compute `os` as `platform.platform()` → Fixture A fails. *Checked in advance that the two
      branches can differ:* `platform.platform()` resolves `system`/`release`/`machine` through
      module-global lookup, so Fixture A's patches reach it, and it appends further components — and if
      its memo was warmed earlier it returns the machine's real string. Neither equals the sentinel
      composition.
      **3** read `hostname` from `platform.uname().node` → Fixture B fails on every machine.
      **4** write `hardware` as the bare int → Fixture C arm 1 and arm P fail.
      **5** write `os.cpu_count() or 1` → **only Fixture C arm 2** fails; arm 1 passes identically,
      which is why arm 2 exists.
      **6** swap `os` and `hostname`'s insertion order → **Fixture D fails and arm P passes**. Report
      both halves: if arm P also fails, this plan's claim that arm P is order-blind is wrong and that
      is a disagreement to report.
- [ ] **Run the installed console script end to end** on a project outside this repo and read
      `run.yaml` **key by key** against the block above. A direct call is not this step: the value is
      written by `command_run` and read by nothing, so only a real record proves it lands.
- [ ] Run arms Q, R, S and U and report that each passes **without an edit**.
- [ ] Four gates. **Delta: +5 tests** (Fixture A, B, C×2, D). Commit.

**What this task must NOT touch.** `study.py` — Ruling Q is task 4's, and `_redact` needs no change.
`docs/` — nothing. Arms Q, R, S, U: run, never edit. Arm P beyond the three pops and three assertions.
`secrets.py`'s docstring (task 7's, and it is false **today** rather than made false here).

---

