# SDD ledger — plan: docs/superpowers/plans/2026-08-16-plugin-registries.md

Spec: docs/superpowers/specs/2026-08-16-plugin-registries-design.md
Branch: h7b-registries, from main at ba87aae. Baseline: 1999 passed + 2 xfailed; ruff check, ruff
format --check (76 files, 0 to reformat) and mypy (43 source files) all clean.

Standing authorization: plan, execute, merge AND push without stopping, and report to the user ONCE
after the push. No halfway report. Recorded because it changes what I stop for — nothing but the four
things the skill names (an irreversible operation, a security-sensitive action, an outward-facing side
effect beyond the merge and push already authorized, or a plan too broken to proceed on).

Ledger writes are committed BEFORE the dispatch that follows them. An H7c implementer correctly refused
an uncommitted line in this file as a possible prompt injection, and it was right to: from inside a
task, an uncommitted authorization in the working tree is indistinguishable from an injected one.

## Pre-flight conflict scan

| File | Tasks | Finding |
|---|---|---|
| `docs/reference.md` | 1, 2, 3, 4, 5, 6, 16, 17, 20 | **Nine tasks, the usual insertion risk.** Tasks 1-6 are the documentation debt and run first, so the rows tasks 16, 17 and 20 touch are already in place. Each of 1-6 owns a distinct section. Carried as an instruction rather than a ruling: any task inserting a row re-reads every count phrase near it, which is how H7c task 2 kept two counts honest |
| `src/publishable/plugins.py` | 7, 12, 13, 14, 15, 16, 17 | **Clean and strictly sequential.** Task 7 creates it; 12-17 each add one registry or check on top. No two tasks write the same function. 7 before all of them, which the plan sequences |
| `src/publishable/templates/registry.py` | 8, 9, 11, 20 | **The one pair worth a ruling.** Task 9 rewrites `_merged` to take a third source and make provenance three-valued; task 20 extends the `PartialLoadError` payload `_merged` builds. Task 20 must be written against task 9 s `_merged`, not today s. Plan order is 8 -> 9 -> 11 -> 20, so 20 is last and sees 9 s shape. **Ruling: no change needed, but task 20 s brief must say the payload line it edits is task 9 s, not `main` s** — the plan report already records that `local.values()` is a proxy task 9 makes wrong |
| `tests/test_plugins.py` | 7, 16, 17 | Clean. Task 7 creates it with the installed-distribution fixture; 16 and 17 append |
| `src/publishable/validate.py` | 8, 11, 19 | Clean. 8 (collision reporting), 11 (`E-TEMPLATE-UNKNOWN` hint), 19 (envelope closure + mutual exclusion) touch three unrelated regions |
| `src/publishable/__init__.py` | 12, 13 | Clean. Both add exports; 12 then 13. **Decision 8 of the H7c spec does not apply here** — this slice DOES move the import root, and § The importable surface s three-name row is task 3 s and 4 s to split |
| `src/publishable/artifacts.py` | 14, 15 | Clean, and the pair is the point: 14 adds `register_writer`, 15 makes `WRITERS`/`READERS` symmetry an enforced invariant over it. 15 must follow 14 |

**No conflict required a ruling beyond the `registry.py` note above.** Recorded with its rows rather
than as a verdict, because "the scan is clean" without the rows is not a scan that was run.

Also checked, per task: each task s tests are specified against the code that task specifies, and no
task touches a file a later task creates. Task 3 precedes task 7 because decision 2 s fifth group must
be settled before the scan enumerates groups — a reordering against the scoping s numbering that the
plan already carries.

Tasks 1-6: BATCHED (all document-only, all `reference.md`). Committed separately; b94029d..67d7219,
  plus bbfe9d7, a correction the implementer caught itself — task 1's four rows had split the
  `E-TEMPLATE-*` family.
Tasks 1-6: reviewed (opus), twelve verdicts. **Tasks 2 and 3 FAILED spec compliance**; the rest passed
  with reservations. One Critical, seven Important, five Minor.
  C1: task 3 wrote that a writer registered without its reader is refused **at load**, "the same breath"
  as a suffix collision. Task 15 builds it at the **READ**, under `E-ARTIFACT-UNREADABLE`, and its own
  step 8 says a registration-time check is something "nothing closes and nothing should". Wrong time,
  wrong code, and two distinct mechanisms glossed as one. That gloss is the shape that carried a real
  difference past its own check last slice.
  I1/I2/I4: three § Errors rows asserted things their tasks will not do — a message shape false of the
  arm the row explicitly covers, a code reported by `validate` with no row in the table whose preamble
  defines it as what commands report, and two codes asserting call sites **no task in Part A or Part B
  gives them**.
  Ruling on I2: a second row was added, matching how `E-DATA-HOLDOUT-VARIES` was handled in H3d — every
  other dual-surface code carries a row in both tables, and § Errors' one-row-per-code rule is about
  codes, not tables.
  Ruling on the marker asymmetry the implementer flagged: the reviewer falsified its PREMISE by counting
  (`grep -c "Not yet emitted"` is 3, and `E-PROBE-UNKNOWN` carries none), which makes the real line
  coherent — codes this slice emits go unmarked, codes only Part B emits are marked. The exception was
  I4's two, which are further from emission than the marked rows and asserted their call sites flatly.
  A report's framing of an inconsistency is a claim too.
  I3: three more stale count phrases, replaced by naming the set rather than by writing the new number —
  the fourth such replacement across three slices.
  Disclosure gap (a) closed here: `CLAUDE.md` said "keep the registered artifacts to the **four**
  registries" and task 3 minted a fifth. **`CLAUDE.md` names itself in the consistency sweep regardless
  of a brief's file list**, which is why this was task 3's rather than a later sweep's.
Tasks 1-6: fix round. Commit 24a56ff. All thirteen closed. 2000 passed + 2 xfailed; gates clean.

Task 7: implemented at 9d28200 / e744b44 — the entry-point METADATA scan over five groups, and the
  installed-distribution fixture neither prior document budgeted. 2006 passed + 2 xfailed.
  The implementer confirmed the invariant by an independent script OUTSIDE pytest — snapshotting
  `sys.modules` around the scan and then calling `.load()` to show it would have imported. It also
  found brief mutation (c) NON-DISCRIMINATING (the fixture's values sort the same way its providers do)
  and reverted it rather than altering a verbatim test. Seventh blind mutation caught across four
  slices, and the first caught by an implementer rather than a reviewer.
Task 7: reviewed (opus). Both verdicts PASS after the reviewer closed two gaps in place. `plugins.py`
  itself was correct throughout — **the tests could not see it change.**
  **C1: `test_the_scan_imports_nothing` could not fail on the guarantee its own name states.** Its
  target was `no_such_module`, so it caught a load only if the exception ESCAPED — wrapping the scan's
  loop in `try: ep.load() except Exception: pass` left all six green. The test named the invariant and
  measured something adjacent to it. Closed: the target now genuinely imports, the assertion is its
  absence from `sys.modules`, and the trailing `.load()` became the positive control.
  I1 is sharper than the implementer's own finding: claimant order was pinned by NOTHING — **deleting
  the inner sort entirely also passed**, because `syspath_prepend` made walk order equal provider order.
  Ruling on where that belonged: closed in task 7, not routed to task 8. "Claimants in provider order"
  is `scan_group`'s own shipped docstring claim and `scan_group` is task 7's deliverable; task 8 asserts
  on message text and would not pin this list's order even incidentally. And "the tests are verbatim
  from the brief" is not a spec constraint — the brief's own mutation argued from a fixture property
  that does not hold, so repairing the fixture IS the brief's stated methodology. The implementer was
  right to refuse to change the CODE; changing the fixture cost nothing.
  The reviewer also attacked the no-import invariant against CPython 3.13.7 source rather than assuming:
  `load()` is the sole `import_module` site, `.dist` is stamped by `_for`, `.name`/`.value`/`.group` are
  instance vars, and `Distribution.name`/`.version` parse METADATA. No shipped path imports.
Task 7: complete at 46e62d2 / c909080. 2006 passed + 2 xfailed; gates clean.

Tasks 8-11: BATCHED (all build on task 7's scan, all touch `registry.py`/`validate.py`). Committed
  separately 0b5e909..69458c3. 2018 passed + 2 xfailed.
  FOUR brief/code disagreements, all caught before the tests were trusted. The one that mattered:
  **task 9's prescribed code called `_claims` a SECOND time**, breaking two pinned regressions — one of
  which exists to prove a second import can raise and destroy every finding. Reworked to one `_claims()`
  per `validate_config`, and a monkeypatch aimed at `resolve_template` was rerouted, which `validate.py`
  no longer imports.
Tasks 8-11: reviewed (opus), eight verdicts. **One CRITICAL blocked.**
  C1: `generate_experiment` still raised `E-TEMPLATE-UNKNOWN` for an installed-only name — the exact
  claim spec correction 1 calls FALSE — and the reviewer probed a message contradicting itself in one
  string: the name "which no template registers" listed among the known ones. Task 9 minted
  `E-TEMPLATE-INSTALLED-UNSUPPORTED` for this and closed only the `validate` surface.
  Ruling on the fix's shape: the second surface was closed by extracting a SHARED
  `installed_template_message`, not by duplicating the branch — the duplication is what produced the
  divergence in the first place. And `resolve_template` was DELETED rather than left with a docstring
  whose premise ("the two callers need both halves") had stopped being true.
  I1 and I2 were both "the reader is unpinned": reversing the provider sort left the full suite green,
  and reverting `type(template).version` to the module constant did too. Both closed with mutations.
  The fix agent caught its OWN non-discriminating mutation mid-round — `list(...)[::-1]` coincidentally
  equals sorted order for a two-element fixture — and switched to plain insertion order. That is the
  eighth blind mutation across four slices and the second caught by the agent proposing it.
  The no-import caveat was ACTED ON rather than filed: the guarantee had been pinned at `scan_group`
  only, and below that merely by fixture targets being unimportable — so tasks 13 or 15 making one
  importable would have silently retired it. Now asserted at `get_template` with a genuinely importable
  fixture.
Tasks 8-11: fix round. Commit 3f477de. All six closed. 2021 passed + 2 xfailed; gates clean.

Tasks 12-15: BATCHED (all add a registry to `plugins.py` plus its export). Committed separately
  433a29f..e3a1d96. 2034 passed + 2 xfailed. The implementer stalled once mid-batch waiting on a
  background suite run; I measured the state myself, told it the count, and told it not to background
  the suite again — it finished 14 and 15 without further stalls.
Tasks 12-15: reviewed (opus), eight verdicts. **One CRITICAL.**
  T13-A: `reference.md` still marked `register_probe` **not yet built** while task 13 exported it —
  task 13 touched no `reference.md` at all — which made the normative sentence *"Importing one raises
  `ImportError` today"* FALSE. And the test meant to guard it **could not catch it**: deleting the
  export left it green, because it asserted only `__all__` membership rather than importing the name.
  Ruling on T13-B, adopting the reviewer's: **`PROBES` is a fifth shipped-but-unread surface and the
  answer is a FILING, not a reader.** `_check_probe` reads the ATTRIBUTE against the metadata scan;
  that is a different fact from something reading the REGISTRY. A reader for `PROBES` means executing
  a probe — `Apparatus` + facts + ledger + change gate, all H7d. One entry now covers `PROBES` (H7d)
  and `RESOLVERS` (Part B), owners named as slices.
  T12-B is the shape this repo keeps finding: **the isolation fixture could not fail.** Replacing its
  whole restore loop with `_ = saved` left the full suite green — a fixture that restores nothing looks
  identical to one that works. Now pinned by a leak probe across two adjacent tests.
  T15-A: the reverse asymmetry was neither handled nor stated — a reader with no writer is never
  dispatched to and `_read` silently returns raw bytes, under prose reading symmetric at three sites.
  Ruling: STATE it rather than handle it. Symmetric dispatch needs a second dispatch keyed off
  `READERS`, out of proportion here. An unstated asymmetry under symmetric prose is the defect; the
  asymmetry itself is a choice.
  T14-A was the ninth blind-mutation shape: the compound-suffix assertion could not distinguish
  "longest wins" from "first-registered wins", because `.fastq.gz` was registered first. Fixed by
  reordering the fixture, not the assertion.
Tasks 12-15: fix round. Commit 9479e13. All eight closed, plus a stale "Not yet emitted" on
  `E-PLUGIN-COLLISION` that entered with tasks 1-6. 2040 passed + 2 xfailed; gates clean.

Tasks 16-20: BATCHED, the slice's last five. Committed separately baa8337..aa37916. 2054 passed,
  1 skipped, 2 xfailed.
Tasks 16-20: reviewed (opus), ten verdicts. One CRITICAL, three Important, four Minor.
  C1: `plugins.py`'s module docstring still said **"nothing here calls `EntryPoint.load()`, and nothing
  that calls this module may either"** — falsified by `load_entry_point`, which task 17 added. The file
  held two sentences that could not both hold, **and the false one was the argument justifying the whole
  mechanism.** Fixed by RE-ARGUING the paragraph rather than appending an exception clause, which is
  what the reviewer specifically asked for: resolving a name answers from metadata and imports nothing;
  loading the object is a separate named operation a caller performs deliberately, and `validate` is not
  such a caller. Both no-import assertions untouched.
  **C2 is the inversion this slice has now hit twice: a mutation's SILENCE read as confirmation.** Task
  20 emptied `_claims`' `partial_templates`, saw all 2054 tests stay green, and concluded no test could
  reach the payload. The reviewer built the discriminating test instead — `c.credentials` is a public,
  inspectable chain carrying `SHADOW_KEY` today. A mutation that changes nothing is evidence about the
  TESTS, not about the code.
  I2 is the same family from the other side: the report claimed brief mutation (a) FAILS, and it does
  not — moved below `_claims` the test still passes; it only fails when moved past the first disk write.
  So the ordering guarantee both the code comment and the test docstring name was pinned by nothing.
  Resolved by PINNING it, with a faked `uv_add` that writes a template as a side effect — so the test
  can only pass if the install really precedes name resolution.
  I1: `discover_local`'s pre-drain was not mirrored, and a stale `_pending` entry was inherited and
  misattributed onto an unrelated refusal while the docstring asserted the opposite.
  Ruling on the skipped test: KEPT, but made honest. `test_uv_add_really_installs`'s body was an
  unconditional `pytest.skip`, so it never ran under ANY invocation including `-m slow` — a test that
  does not exist wearing a marker. It is not the sole pin for task 18's headline (both CLI tests drive
  `main` unskipped and pin that `--plugin` is genuinely threaded), and no offline-installable
  `git+https://` dependency exists because a scaffolded project cannot resolve `uv add` at all. Now a
  decoration-level skip with a reason, and the residual — **no test executes `uv_add`'s body** — is
  written into the test file rather than left to be rediscovered.
Tasks 16-20: fix round. Commit cac8e1f. All eight closed. 2059 passed, 1 skipped, 2 xfailed.
ALL TWENTY TASKS COMPLETE. Whole-branch review next, then merge and push.
