# H7d Part A, batch 1 (tasks 18, 1, 2, 3) — review

**Reviewed at `58d62e1`** on branch `h7d-apparatus-part-a`. Everything below marked *verified by
running* was run in this working tree; everything else is marked *read*.

## Verdicts

**Spec compliance: PASS with exceptions.** Decisions 1, 5, 7, 11 and 13's batch-1 obligations are
honoured in the code and in the documents, and the three edited sites read consistently with each
other and with § The apparatus files. Two exceptions, both in the sweep the design's own § The
consistency sweep this slice owes required and task 1's brief under-scoped: the claim task 1 removed
from `reference.md` **survives as a paraphrase in the feasibility analysis, attributed to the very
sentence that was rewritten** (Major 1), and task 2's `built` row **falsifies an undated build claim
in the same file** (Major 2). No command was invented; no sentence claims a config was unblocked; the
worked example is untouched; Decision 12's prohibition is not violated anywhere in the new prose.

**Task quality: PASS with one Major gap.** All four gates reproduce exactly as reported. The guard
pin discriminates on both of its arms, verified by two independent mutations, and it covers what
tasks 8, 11 and 12 will move. One documented guarantee ships unpinned — the fail-open that
`_probe_for`'s docstring exists to argue against survives the entire suite (Major 3) — and two
docstring sentences assert § Errors rows that do not exist (Minor 1). Those two are the "zero
disagreements" report's weakest point: both were carried from the brief's prose rather than checked
against the document they cite.

### Gates — verified by running

- `uv run ruff check .` → All checks passed
- `uv run ruff format --check .` → 82 files already formatted
- `uv run mypy` → **46 source files**, no issues
- `uv run pytest -q` → **2370 passed, 1 skipped, 2 xfailed** (138.29 s)

The reported baseline arithmetic is internally consistent: 7 new tests (1 + 1 + 2 + 3, and
`tests/test_apparatus.py` collects exactly 5) against 2363. The 2363 baseline itself was read, not
re-run.

### The guard pin — verified by running, both arms

`tests/test_cli.py:12850`. It asserts the full 12-key `provenance` list, `apparatus is None`, and
`not (run_dir / "apparatus").exists()`.

1. Prescribed mutation, `src/publishable/cli.py:3455` `"apparatus": None,` →
   `"apparatus": {"probe": None},`: FAILS at `tests/test_cli.py:12883` with
   `AssertionError: assert {'probe': None} is None` — an assertion on the value, not a crash and not
   a string comparison. Reverted by rewriting the line; re-ran green.
2. Second mutation, mine, aimed at what **task 8/11** will move: `(run_dir / "apparatus").mkdir()`
   added beside `manifest`'s in `command_run`. FAILS at `tests/test_cli.py:12884` on the `exists`
   assertion. Reverted; re-ran green.

So the pin covers all three surfaces later tasks move — the block's value (task 11), the key list (a
sibling key, e.g. task 12's hash escaping the block), and the ledger directory (task 8). Tree
confirmed clean by `git status` and by `diff` against a pre-mutation copy after each revert.

### The `__post_init__` question (review item 3) — resolved, and there is no contradiction

`Apparatus` **has no `__post_init__` at all** (`src/publishable/apparatus.py:19-35`): a frozen
dataclass with one field and no validation. The report's mutation *added* one, which is the correct
mutation for a test whose property is "this shape is accepted here". Decision 5, plan correction 11
and the code agree, and the split is documented where a reader looks — in `Apparatus`'s own
docstring, naming `Unit` / `units._from_resolver` / `E-RESOLVER-YIELD` as the precedent. **Verified
by reading** `units.py:75-96` (`Unit.__post_init__` freezes and validates nothing) and
`units.py:353-360` (`E-RESOLVER-YIELD` raised in `_from_resolver`). No shape-versus-value split
exists to document: nothing at all is checked in `Apparatus`.

### The "zero disagreements" claim — four brief claims re-verified independently

All four held (**verified by reading the named source at HEAD**):

- `plugins.py` holds `PROBES` (:116), `register_probe` (:139), `"publishable.probes"` in `GROUPS`
  (:46) and in `_registry_for` (:213); `check_registration`, `load_entry_point`, `scan_group` and
  `declared_names` all exist and all have a production caller through `units._resolver_for`
  (`units.py:293-307`).
- `validate._check_probe` (:953-985) reports `E-PROBE-UNKNOWN` from a metadata scan
  (`names("publishable.probes")`), so the dual-surface claim is true of the code.
- `cli.py` writes `"apparatus": None` at exactly one site (:3455), unconditionally.
- The two strings task 1's pin asserts absent were **present at `4508ea6`** and are absent at HEAD
  (`git show 4508ea6:docs/reference.md | grep -c 'warning at \`dry-run\`'` → 1, at HEAD → 0; same for
  the `experimental-designs.md` sibling). That is also the sweep's can-fail proof.

## Findings

### Major 1 — the removed `dry-run` siting survives as a paraphrase in the feasibility analysis

**`docs/feasibility-llm-growth-studies.md:940`** (§ Gaps this analysis found in the specification —
nearest heading verified, line 936, an **undated** section) and **:823** (§ The apparatus probe is
the sharpest fit, and it is also the operational risk — heading verified, line 795). Verified by
running an unfiltered `grep -n "dry-run"` over the four documents, `CLAUDE.md` and the feasibility
analysis, and reading all 34 hits.

- :940 — "*Resolved* in `reference.md` § The apparatus core can only observe: … declaring the fact
  buys a `dry-run` warning plus an `unobserved` count." This **attributes the siting to the sentence
  task 1 rewrote**, so the file now quotes `reference.md` as saying something it deliberately no
  longer says. That misattribution is the stronger half of this finding.
- :823 — "What declaring it buys … is the `dry-run` warning and the `unobserved` count." A narrowing
  rather than a falsehood (`dry-run` remains one of the places the warning fires), but it is the same
  claim the slice ruled must stop being sited there.

The design's § The consistency sweep this slice owes requires, after removing a string, a grep over
"the four documents, `CLAUDE.md` and the feasibility analysis"; **task 1's brief step 4 named only
the four documents**, and the implementer's sweep followed the brief. This is exactly the shape the
batch was told to hunt — a deleted claim surviving as a paraphrase — and it is in the one file the
sweep that ran could not reach. Fix by deleting the `dry-run` siting from both (a deletion, not a
rewrite). If it is routed to task 16 instead, that task's sweep step must be extended to name this
claim, because today it sweeps for **identifiers** only.

### Major 2 — task 2 falsified an undated build claim in the feasibility analysis

**`docs/feasibility-llm-growth-studies.md:825`**: "there is no `Apparatus` type, no `register_probe`,
and no probe execution anywhere in the package." Verified by running: the nearest preceding heading
is line 795, `### The apparatus probe is the sharpest fit…` — **body prose, not one of that file's
dated `### Measured on <date> against commit <sha>` sections** (the nearest of those begins at line
946 and the most recent at 1322), so procedure step 10 is genuinely broken here rather than merely
appearing to be. `Apparatus` is exported at HEAD and § The importable surface's row now says `built`.
Two clauses of the same sentence were **already** false at `main` — `register_probe` ships in
`plugins.py:139` from H7b Part A, and "`apparatus_probe` … read by nothing" one clause earlier was
falsified by `validate._check_probe`.

Two distinct remedies, and the batch owes the first: correct or delete the body sentence, which is
undated and now wrong. The dated re-measurement — a new `### Measured on 2026-08-19 … — after H7d
Part A` entry in § Executability on this build, on the precedent of the eight entries already there —
belongs at the end of the slice, not to this batch.

### Major 3 — `_probe_for`'s central reconciliation claim is unpinned, and a fail-open passes the suite

**`src/publishable/apparatus.py:60-66`** (the "Two sources of truth" paragraph) and **:72**. The
docstring's ground — and Decision 11's — is that reading `PROBES` alone "would resolve a
decorator-only registration `validate` refused". **Verified by running**: I inserted, at the top of
`_probe_for`,

```python
from publishable.plugins import PROBES

if name in PROBES:
    return PROBES[name]
```

`uv run pytest tests/test_apparatus.py -q` → **5 passed**. `grep -rn "_probe_for" src/ tests/` shows
the function has no caller outside `tests/test_apparatus.py`, so no other test can see the mutation
either: the whole suite is blind to it. Reverted from a saved copy; re-ran, 5 passed, `git status`
clean.

The three shipped tests cover a *misspelled* name (registered nowhere at all), so the case the
docstring argues about — registered **by decorator only**, no entry point — is a seam named in prose
and instantiated by no fixture. The fixture that closes it: import a module calling
`@register_probe("llm_deployment")` with **no** `installed(...)` entry point, and assert
`_probe_for("llm_deployment")` raises `E-PROBE-UNKNOWN`.

Mitigating, and why this is not Critical: `units._resolver_for` has the identical hole (no test
registers a resolver by decorator only and asserts `E-RESOLVER-UNKNOWN`), so this is a **copied** gap
rather than a new class, and the property itself holds in the code today.

### Minor 1 — two docstrings assert § Errors rows that do not exist

- `src/publishable/apparatus.py:26-29`: "would be reported as `E-APPARATUS-RAISED`, a code whose
  § Errors row describes a different fault." Verified by running
  `grep -rn "E-APPARATUS" docs/*.md README.md src/` — the only occurrence of that identifier anywhere
  is this docstring. There is no row, and no code.
- `src/publishable/apparatus.py:47-49`: "§ Errors carries one row for both." Verified by reading
  `docs/reference.md:551`: the `E-PROBE-UNKNOWN` row describes the `validate` surface only; task 16
  is what makes it dual-surface.

Both are present-tense claims about documents, in the class `CLAUDE.md` lists first among habits that
cost work, and task 1's own brief forbade the document-side equivalent ("a code named in two places
before it exists is a second source of truth for build state"). Prefer **deleting** the "§ Errors
row" clauses; the substantive argument — a probe-body raise is indistinguishable from any other —
survives without them.

### Minor 2 — the new enumeration disagrees with the bolded sentence directly above it

`docs/reference.md:3063` (unchanged) reads "**It runs at `dry-run`, at run start, and before every
execution — never at `validate`.**" while the new :3065 enumerates four places including `freeze`,
and § The apparatus files (:943) also lists `freeze` among the ledger's phases. Read, not run. The
edit did not create the omission but it placed a three-place claim immediately above a four-place
one. Cheapest repair: add `freeze` at :3063, or drop it from :3065's tail and let :943 carry it.

### Minor 3 — one `dry-run` hit the report classified but did not name

`docs/reference.md:346`: "whether the [apparatus] is reachable is checked by `dry-run`." Read. Its
contrast is `validate`-versus-`dry-run`, and reachability is not one of Decision 1's three yield
checks, so keeping it is defensible — but it states a place a probe runs as *the* place, and it is
not among the three hits the report's keep-list names. Worth a sentence in the batch record either
way.

### Minor 4 — the document pin's `experimental-designs.md` arm asserts only an absence

`tests/test_validate.py:14214-14228`. The `reference.md` arm is paired with a presence assertion
(`"wherever a probe runs" in reference`); the designs arm asserts absence alone, so it passes
identically if that row's widening were reverted to any other wording. Add
`assert "warns, wherever a probe runs" in designs`.

### Minor 5 — `Apparatus` does not freeze `facts`, while its docstring cites `Unit`'s freezing

`src/publishable/apparatus.py:19-35`. `frozen=True` stops rebinding the field; the mapping itself
stays mutable, so a probe can mutate the dict it handed back. Decision 5 asks only for a frozen
construct, so this is within spec — but the docstring's precedent sentence ("it freezes its
attributes and validates nothing") invites a reader to assume the freezing came across too. Either
wrap as `Unit` does, or say plainly that only the field is frozen.

## Checked, no charge

- **No probe is called anywhere in production code.** `grep -rn "_probe_for" src/ tests/` returns
  only `apparatus.py`'s definition and `tests/test_apparatus.py` — B1's "nothing in it calls a probe"
  seam holds exactly.
- **Decision 12 is not violated.** `git diff main..HEAD -- src/ tests/ | grep -in
  "cannot|never stops|mid-plan|truncat|status: partial|EXIT_EXTERNAL"` returns two hits, both
  unrelated ("cannot be told from any other probe raise"; "cannot make it pass vacuously"). No
  comment, docstring or test name claims an unreachable probe cannot stop a run mid-plan.
- **The paraphrase sweep, unfiltered.** `grep -n "dry-run"` over `README.md`,
  `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`, `CLAUDE.md` and
  the feasibility analysis — 3 + 2 + 1 + 20 + 2 + 6 hits, every one read, **filtering the file list
  and never the output**. Outside the two feasibility hits in Major 1, nothing sites the yield checks
  at `dry-run` alone. § The apparatus core can only observe and § The apparatus files were then read
  end to end, because a sweep for the token cannot find a paraphrase that omits it: no such
  paraphrase is there, and the two edited sentences read consistently with each other, with :943's
  phase list and with the `experimental-designs.md` row.
- **§ Package layout's row** (`docs/reference.md:3988`) now reads without `— not yet built`. True
  under the tree's own stated semantics — :4000 says *Modules marked `— not yet built` are specified
  and unbuilt*, and the tree "is a map of what core's source will hold" — so a row describing a
  change gate Part B owns is not a false build claim. The design's consistency sweep ruled exactly
  this edit.
- **§ The importable surface's enumeration** gained `Apparatus` as a `construct` / `built` row among
  the constructs, and `__init__.py` gained both the import and the `__all__` entry in sorted
  position. The self-maintaining "A row marked `not yet built` is a promise" sentence was correctly
  left alone.
- **No command invented.** `freeze` is `docs/reference.md:3490`'s existing `NOT BUILT` CLI row and
  was already named as a ledger phase at :943.
- **No count moved.** `git diff main..HEAD | grep -n "unblock\|executable\|no remaining core-side"`
  returns nothing.
- **Task 3's prescribed mutation** (deleting `check_registration(...)`) — verified by running:
  `test_a_probe_whose_module_declares_a_different_name_is_E_PLUGIN_DECORATOR` fails with `DID NOT
  RAISE ContractError`. Reverted from a saved copy; 5 passed; `git status` clean.
- **`_probe_for` is a faithful sibling** of `units._resolver_for` step for step, including the
  first-claimant tie-break and the collision deferral, which `validate.py:824-834` does report over
  the complete claim set from metadata in sorted provider order.
- **`spec-defects.md` is untouched, correctly.** The `PROBES … read by nothing` entry still reads
  OPEN with owner H7d; task 3 made its claim stale in fact and **task 17 owns the strike**, so the
  deferral is live rather than abandoned.
- **Mechanical pass** on the two edited documents — verified by running a throwaway script: no
  trailing whitespace, no tabs, no invisible unicode, no colliding heading anchors, the edited table
  row keeps its column count, and the edited link's `#the-apparatus-core-can-only-observe` target
  exists. (An anchor sweep flagged only `&` / `·` headings my slugger renders wrongly — false
  positives, checked by hand.) No `x`-for-`×` and no positional locator was introduced.
- **Three not charged.** `PROBE_GROUP` is a third copy of `"publishable.probes"` beside
  `plugins.GROUPS` and `plugins._registry_for` — `units.RESOLVER_GROUP` is the shipped precedent and
  task 3's brief prescribed the constant. `pytest.raises(Exception)` at `tests/test_apparatus.py:13`
  is weaker than `FrozenInstanceError` but is briefed verbatim. `docs/design-principles.md:154` says
  "the four `register_*` decorators" where the table enumerates five — verified present at `main`,
  so pre-existing and outside this batch.

## Could not check

- **The 2363 baseline** was not re-run on `main` (≈2.3 min); it is consistent with 2370 minus the
  7 tests this batch adds, and that is the whole of my evidence for it.
- **The report's claim that task 18's literals were captured by a real run *before* the assertion was
  written.** Unfalsifiable after the fact. What is verifiable and true: the literals match a real
  run's output today, and both discriminating arms fail under mutation.
- **Whether `E-PROBE-UNKNOWN`'s two messages will stay in agreement.** Both sites hardcode the group
  name in their prose and nothing compares them; that is task 16's row work, and the
  `E-TEMPLATE-UNKNOWN` trap `CLAUDE.md` records is worth naming there.

**Tree state: clean.** Every mutation was reverted by rewriting the file (never `git checkout --`),
each revert verified by re-running the affected test, and `git status --short` is empty apart from
this review file.
