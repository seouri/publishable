# H7b Part B — whole-branch **re-review** (scoped to the fix round)

Reviewed 2026-08-17, branch `h7b-resolvers` at `4f0415e` ("fix: close whole-branch review findings").
Scope: **only** whether `whole-branch-review.md`'s findings were closed, and whether closing them
introduced anything new. The whole-branch review is not repeated.

Gates at HEAD, foreground: `uv run pytest` → **2109 passed, 1 skipped, 2 xfailed**; `ruff check`,
`ruff format --check`, `mypy` clean. Every mutation below was applied by editing the file, reverted by
copying a scratchpad backup over it, and the revert confirmed by `git diff` being empty **and** by
re-running the suite — never `git checkout --`.

**Verdict: NOT READY TO MERGE.** The Critical is genuinely closed *in behaviour* — verified through the
real console script for six exception shapes at both commands, including the `cli.py` handler the fix
agent's own verification never actually reached. But **three of the fix round's four code changes are
pinned by no test at all** (one combined mutation leaves the suite at 2109 passed, unchanged), **one new
normative § Errors clause is false**, and **the false comment I1 named was rewritten rather than deleted
while the commit message asserts it was deleted**. Each is cheap; none is a re-design.

---

## Findings closed / not closed

| Finding | Status |
|---|---|
| **C1** — `sys.exit()`/`BaseException` leaking a credential at both commands | **CLOSED in behaviour, NOT pinned.** No leak in any shape at either command (matrix below), including through `cli.py`'s own arm. But the widening is unpinned — see N1 |
| **I1** — `E-RESOLVER-RAISED` for table/glob faults under a false comment | **PARTIALLY CLOSED.** The recode works and the row exists; but the new identifier is unpinned (N1), the comment was **rewritten, not deleted** (N3), and the new row carries a false clause (N2) |
| **I2** — the `cli.py` `cfg`-threading obligation | **CLOSED, and genuinely discriminating.** Re-ran the mutation; it reddens exactly one test, the new one |
| **I3** — two "merged" assertions | **CLOSED.** Both now read "is complete on its branch"; neither invents a merge commit. See N5 for what the commit pin now carries |
| **M0** — four rows missing a dual-surface note | **CLOSED.** Notes on `E-RESOLVER-SWEPT-PARAM`, `E-UNITS-ATTR-MISSING`, `E-UNITS-EMPTY`, `E-UNITS-KEY-DUPLICATE`. `E-RESOLVER-RAISED` still has exactly **one** row (`grep -c` = 1) |
| **M1** — the impossible remedy in `E-RESOLVER-SWEPT-PARAM` | **HALF CLOSED.** The impossible remedy is gone; the **ungrammatical interpolation the finding also named survives**, the fix is unpinned, and the new comment overclaims. See N6 |
| **M2** — `ResolverIO` docstring pointing at task 31 | **CLOSED.** Now states the decision |
| **M3** — `_resolve_resolver` does not exist | **CLOSED** by an appended dated correction naming `_resolver_for`, not by a rewrite |
| **M4** — reopened ledger closure | **CLOSED** by an appended `CORRECTION` in `progress.md`; the original line is left standing, per this repo's rule |
| **M5** — asymmetric "not settled" caveat | **CLOSED.** The caveat now cuts both ways for E1/E2/E5 |

---

## C1 — the probe matrix

One real installed `leaky-1.0.dist-info` on `PYTHONPATH`, a real `publishable.resolvers` entry point
running real resolver code, one real project, driven through the `publishable` console script as a
**subprocess**. The resolver module is rewritten between rows and its `__pycache__` removed, so each
row is that row's body. `MY_KEY=SENTINEL-sk-abc123` is a **declared** credential (`required_env` on a
project-local template). Scripts: `scratchpad/rr_probe.py`, `rr_probe2.py`, `rr_probe3.py`.

| Resolver body | `validate` | `run` |
|---|---|---|
| `sys.exit(msg)` | exit 1 · `E-RESOLVER-RAISED` · `<redacted:MY_KEY>` · **no leak** | same · **no leak** |
| `raise SystemExit(msg)` | exit 1 · `E-RESOLVER-RAISED` · **no leak** | same · **no leak** |
| `raise KeyboardInterrupt(msg)` | exit 130 · `KeyboardInterrupt` traceback, **no message** · **no leak** | same · **no leak** |
| `raise Boom(msg)`, `Boom(BaseException)` | exit 1 · `E-RESOLVER-RAISED` · **no leak** | same · **no leak** |
| `raise GeneratorExit(msg)` | exit 1 · `E-RESOLVER-RAISED` · **no leak** | same · **no leak** |
| `raise ValueError(msg)` — **`Exception` control** | exit 1 · `E-RESOLVER-RAISED` · **no leak** | same · **no leak** |
| module-scope `sys.exit(msg)` at import | exit 1 · **`E-PLUGIN-LOAD`** · **no leak** | same · **no leak** |
| real **SIGINT** to the process group mid-resolver (`time.sleep(60)`) | exit 130 · `KeyboardInterrupt` · no `E-RESOLVER-RAISED` | same |

Every row asserts the **positive companion** (`<redacted:MY_KEY>` present, or the expected code
present) alongside the sentinel's absence, so a row that never raised could not pass.

**The fix agent's "at both commands" verification did not reach `cli.py`'s handler, and I checked it
separately — the commit message's "at both commands" answers *which command was invoked* rather than
*which handler ran*, which is `CLAUDE.md` § Answering a question with a proxy in its verification
form.** At `run`, `command_run` calls `validate_config` first, so a resolver that raises on
*every* call is contained by `validate.py`'s arm — the `run` rows above print `resolution raised …`,
which is `validate.py`'s message format, and the `KeyboardInterrupt` traceback names
`validate.py:1379`. `cli.py`'s arm is reachable only by a resolver that behaves differently on its
second call. Probed exactly that (`rr_probe2.py`, bodies raising only when `_calls["n"] >= 2`):

| 2nd-call body | `run` |
|---|---|
| `sys.exit(msg)` | exit 1 · `E-RESOLVER-RAISED` · `<redacted:MY_KEY>` · **no leak** |
| `raise KeyboardInterrupt(msg)` | exit 130 · traceback naming **`cli.py:1373`** · no message · **no leak** |
| `raise Boom(msg)` | exit 1 · `E-RESOLVER-RAISED` · **no leak** |
| `raise ValueError(msg)` — control | exit 1 · `E-RESOLVER-RAISED` · **no leak** |

So both handlers are independently exercised and neither leaks.

**Ctrl-C still works.** A real SIGINT during a sleeping resolver gives exit 130 with a
`KeyboardInterrupt` traceback at both commands, no finding, no code, nothing swallowed. The
`from None` chain suppression hides only the resolver's own exception object — for a *real* Ctrl-C
there is nothing to hide (`str()` is empty and `args` is `()`), and for a constructed one the message
is exactly what must not be shown. Nothing a user needs is lost: the frame where the interrupt was
taken is still in the traceback.

### What a resolver can still do that no `except` reaches

Genuinely out of reach, and correctly so:

- `os._exit()` / `os.kill(os.getpid(), SIGKILL)` / a `ctypes` segfault — the process ends without
  unwinding, so no handler runs at all.
- a raise inside `__del__` during GC — the interpreter prints `Exception ignored in: …` to stderr from
  outside every frame core owns.
- a raise on a thread the resolver spawned — `threading.excepthook`, same reason.
- the resolver simply `print`ing or logging the credential itself.

The honest bound is **core redacts what core renders**; it cannot redact what user code writes, or what
the interpreter prints outside a frame core owns. None of these is a defect of this fix. But see N4:
one *documented* claim now overreaches by one exception type inside the reachable set.

---

## New findings

### N1 — Important, **blocks merge**. Three of the fix round's four code changes are pinned by no test

The fix commit added **exactly one test** (`tests/test_cli.py`, +58 lines: I2's). Applying all three
remaining code changes' inverses at once and running the full suite in the foreground:

| Mutation | Result |
|---|---|
| `except BaseException as exc:` → `except Exception as exc:` at `cli.py:1348` **and** `validate.py:1360` | — |
| `code="E-UNITS-SOURCE-UNREADABLE"` → `code="E-RESOLVER-RAISED"` at both `units.py` raise sites | — |
| `subject = str(exc).split(";", 1)[0]` → `subject = str(exc)` in `_from_resolver` | — |
| **all three together** | **2109 passed, 1 skipped, 2 xfailed — identical to HEAD** |

The mutation was applied combined, so strictly it proves no test distinguishes all three inverses
jointly — **and therefore none distinguishes any of them**, since a green suite under every inverse at
once means no test touches any one of them. Re-running them separately would add nothing.

So the Critical's remedy, the new identifier, and the message fix are all invisible to the suite. The
review named the first two in writing (*"Needs beside the code: a test with a resolver calling
`sys.exit()` carrying a sentinel, asserting the sentinel is absent **and** `<redacted:...>` present …;
a test that Ctrl-C still propagates, **or the re-raise is unpinned**"*; and for I1, *"a new identifier
… which in this repo means a § Errors row **and a test** alongside the code change"*). Neither was
written. This is the shape `CLAUDE.md` § Writing checks that can fail exists for — sixteen such checks
in the two H3c slices, a dozen more in H7a — and here the checks do not merely fail to discriminate,
they do not exist.

Cheap to close: the fixtures already exist in the suite. `test_cli.py`'s
`test_a_resolvers_raise_at_run_is_redacted_rather_than_printed_whole` is parametrized over
`ContractError`/`ValueError` — adding a `SystemExit("… SENTINEL …")` arm and a `BaseException` arm
pins the widening at `run`; the sibling in `test_validate.py` does the same for `validate`. Ctrl-C
wants one test asserting `pytest.raises(KeyboardInterrupt)` with `args == ()` and an empty `str()`.
`E-UNITS-SOURCE-UNREADABLE` wants a mis-encoded-CSV fixture (three lines) and an absolute-glob one.

### N2 — Important, **blocks merge**. The new § Errors row makes a false claim, and the behaviour it mis-describes is a silent escape from `input_dir`

`reference.md:604`, the `E-UNITS-SOURCE-UNREADABLE` row, reads: *"a `glob` pattern outside `input_dir`
(an absolute path, **or one escaping it**), raising `NotImplementedError`/`ValueError` from
`Path.glob` rather than a `ContractError`."*

Probed rather than read (`scratchpad/i1probe.py`, `i1probe2.py`, Python 3.13.7), with a real
`outside.csv` in `input_dir`'s parent:

| `data.units.from.glob` | result |
|---|---|
| `/etc/*.conf` (absolute) | `E-UNITS-SOURCE-UNREADABLE` — the row's first clause is true |
| `/../*.csv` (absolute) | `E-UNITS-SOURCE-UNREADABLE` |
| `../*.csv` | **resolves a unit `../outside.csv`** — no raise, no refusal |
| `../outside.csv` | **resolves a unit `../outside.csv`** |
| `**/../*.csv` | **resolves a unit `../outside.csv`** |

The claim is precisely this narrow: a **relative** pattern escaping `input_dir` (`../*.csv`,
`../outside.csv`, `**/../*.csv`) neither raises nor is recoded — it resolves units from outside
`input_dir`. A pattern that is *both* absolute and escaping (`/../*.csv`) does hit the code, so the
row's wording is defensible for that case and false only for the relative one. That is still a false
clause **in a normative § Errors row** — `CLAUDE.md`'s first *Habits that cost real work* entry —
shipped by the round whose job was deleting a false claim of the same kind. The exact remedy: *"an
absolute path, or one escaping it"* → *"an absolute path"*.

**Not an artifact of one interpreter.** `pyproject.toml` sets `requires-python = ">=3.11"`, and
`Path(d).glob("../*.csv")` returns the outside match on **3.11.15, 3.12.13 and 3.13.7** alike, so the
row is false across the whole supported range rather than version-dependent.

Two things to separate. The **documentation defect** is this round's and blocks: delete the clause, or
narrow it to "an absolute path". The **behaviour** — a glob resolving units from outside `input_dir` —
is pre-existing (`_from_glob` has no containment check, which `ResolverIO`'s own docstring says of the
`IO` classes too) and is a candidate `spec-defects.md` entry rather than a fix here; note that
`hash_index` cannot hash such a unit's path either, since `build_manifest`'s `files` dict is keyed by
paths walked from **inside** `input_dir` — the same asymmetry task 31 already recorded for
`ResolverIO`. Filing it beside that entry would be the consistent move.

### N3 — Minor. The false comment was **rewritten**, not deleted, and the commit message says it was deleted

**`4f0415e`'s message asserts *"the false `this arm is a resolver's by construction` comment is
**deleted rather than rewritten**"* — and the clause is still there, verbatim.** `validate.py`'s arm
reads: *"… are recoded to `E-UNITS-SOURCE-UNREADABLE` inside `resolve_units` itself and so are already
`ContractError`s by the time they reach here — **this arm is a resolver's by construction**."* Same
concluding clause the review called false, new justification bolted on. I1's remedy was explicit:
*"The false comment should be **deleted rather than rewritten**, per this repo's own rule."*

Whether the *rewritten* sentence is also false is secondary and I did not settle it. The `try` also
evaluates `resolve_wide_cfg(doc, wide_swept_paths(doc.get("sweep") or {}))`, so a malformed `sweep`
beside a **table** source is the natural counterexample; five shapes all report `E-CONFIG-SHAPE` from
the envelope check and return before `_check_units` (`scratchpad/rr_probe3.py`). That is exactly why the
rule is to delete rather than restate: a deletion cannot come to be false, and this clause is a standing
absolute claim about a `try` body containing two calls, only one of which the sentence reasons about.
Delete the last clause; keep the true, useful sentence about where the table/glob recode happens.

### N4 — Minor. `E-RESOLVER-RAISED`'s § Errors row now overclaims by exactly one exception type, and the carve-out is in none of the four documents

The row: *"A resolver's own body raises something that is not a `ContractError` … `_check_units`
**contains it under a coded refusal of its own** rather than letting an arbitrary exception escape.
`command_run` contains the identical raise at `run` … rather than **letting it end the command in an
un-redacted traceback**."*

`KeyboardInterrupt` is such a raise, and it is deliberately *not* contained: it ends the command in a
traceback (exit 130), with the message stripped. The behaviour is right — the review argued for it and
I verified it — but the row now describes a guarantee with one unnamed exception, and
`grep -n "KeyboardInterrupt\|Ctrl-C" README.md docs/design-principles.md docs/experimental-designs.md
docs/reference.md` returns **nothing**: the carve-out exists only in two source comments. One clause in
the row ("except `KeyboardInterrupt`, which is re-raised so Ctrl-C still stops the command") makes it
true and gives the behaviour a documented home.

### N5 — Minor. `CLAUDE.md`'s new paragraph asserts the leak closed *at a commit where it was open*, and asserts "never a traceback"

`CLAUDE.md:59` is pinned to `f9d99148c3be5590420e7cff3a3598f2d529ecf2` and ends: *"and the credential
leak Part A left open — a resolver's raise now becomes a redacted diagnostic at both `validate` and
`run`, **never a traceback**."* Two problems:

1. At `f9d9914` that was **false** for `SystemExit`, `KeyboardInterrupt` and bare `BaseException` — the
   whole-branch review verified the leak at the real terminal at that commit. It became true at
   `4f0415e`, two commits later. The pin should move, or the closure sentence be separated from it.
2. "never a traceback" is still not literally true: a `KeyboardInterrupt` from a resolver body *is* a
   traceback (redacted of its message). Same clause as N4, in a second file.

The dated feasibility measurement's own pin to `f9d9914` is **correct** and should stay — a measurement
belongs to its date. I re-ran the nine-config harness at HEAD (`scratchpad/measure9.py`) and the table
reproduces exactly: E1–E6 clean, C1–C3 `E-DATA-WEIGHT-CONTRAST`, all nine `W-DATA-CLUSTER-UNDECLARED`,
and the `holdout.frac: 0` control still fires `E-DATA-HOLDOUT-FRAC` — so **three of nine survives the fix
round**, which was the one thing that could have moved.

### N6 — Minor. M1's remaining half, and a comment that overclaims about its own fix

The rendered message today (probed, not read):

> resolver `plate_wells` reads `parameters.analysis.method` **is varied by** `sweep`, so it has no
> single value at this scope. The unit table is one table for the whole run … Read a parameter the
> sweep leaves alone

The impossible remedy is gone. The **ungrammatical interpolation the finding also named is not** — M1
reported "two defects in one string" and one was fixed. The new comment says *"only the subject clause
(which path is swept) is reused"*, but `str(exc).split(";", 1)[0]` reuses the whole first independent
clause, not the subject — so the comment describes a narrower fix than the code makes. And the split
couples this message to the *step* message's punctuation: drop the semicolon in
`E-STEP-SWEPT-PARAM` and the impossible remedy silently returns, with nothing to catch it (N1).
Composing the sentence from the path alone — which `_from_resolver` already has — closes all of it.

---

## Confirmed not disturbed

- **Every `Exception`-derived shape still redacted at both commands** — the `ValueError` control row of
  both probe matrices, at `validate`, at `run` through `validate.py`'s arm, and at `run` through
  `cli.py`'s own arm. Not an absence-only sweep: each asserts `<redacted:MY_KEY>` present.
- **Task 31's `hash_index`** — untouched by the fix round (`manifest.py` and `units.index_names` have no
  diff in `4f0415e`), and its three "one call site" claims verified by grep: `_from_table`, `_from_glob`,
  `build_manifest` and `index_names` each have exactly one caller in `src/`.
- **The executable count is still honestly three of nine** — reproduced at HEAD with a discriminating
  control, above.
- **`main`'s un-redacted handler is still filed, not silently widened** — `cli.py:2877-2879` is
  unchanged (`print(f"  error   {exc.code:<20} {exc}")`, no collector), and
  `spec-defects.md:5957` still carries `## OPEN — main's last-resort stderr handler prints an exception
  un-redacted, by construction`.
- **Mechanical pass clean** over the four documents plus `CLAUDE.md` and the feasibility analysis:
  links, `#anchor`s, duplicate anchors, table column widths, empty rows, trailing whitespace, tabs,
  invisible unicode, fenced blocks skipped. **The checker was proved able to fail** by injecting a
  known-bad anchor into `CLAUDE.md` and watching it report, then restoring the file.
- **`E-RESOLVER-RAISED` still has exactly one § Errors row** covering both emit sites; the new
  `E-UNITS-SOURCE-UNREADABLE` row sits in § Errors `validate` reports beside `E-UNITS-EMPTY` and
  `E-UNITS-KEY-DUPLICATE`, which are raises reported there too — the consistent section.
- **`progress.md` and `spec-defects.md` were corrected by appending**, never by retro-editing, which is
  the development-record rule.

---

## What would make merging this a mistake

1. **N1** — shipping the slice's Critical fix, its new user-facing identifier, and its message fix with
   **no test between them**, in the repo whose own § Writing checks that can fail exists for this, when
   the review listed both tests as required beside the code and the fixtures already exist.
2. **N2** — a new false clause in a normative § Errors row, promising a refusal of a glob that escapes
   `input_dir` while such a glob silently resolves units from outside it.
3. **N3/N4/N5/N6** — one rewritten-not-deleted false comment (with a commit message asserting the
   opposite), one § Errors row and one `CLAUDE.md` sentence each overclaiming by the same
   `KeyboardInterrupt` carve-out, one commit pin that predates the closure it announces, and M1's
   surviving half. None blocks on its own; together they are the same class the slice already shipped
   two Criticals of.

Everything the whole-branch review verified sound is intact, C1's leak is genuinely and
comprehensively closed in behaviour at both handlers, and I2 is closed with a mutation that reddens
exactly one test. The gap is between the code and what pins and describes it.
