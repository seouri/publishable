## Task 16

> **AMENDED AGAIN 2026-08-23 by the controller, after task 13 made the loss real.** With the apparatus
> baseline replayed, **a resume whose apparatus moved while the run was down exits `1` with no `run.yaml`
> and repeats identically for as long as the fact stays moved — every completed execution unpublishable.**
> Measured and pinned by task 13. **That is a record loss and this task must close it, not justify it.**
>
> The precedent decides the shape: H7d Part B ruled that a changed fact fails the run **and the ledger
> keeps the moving observation so a stop is legible from the artifacts.** *Every execution paid for, the
> record lost* is the most expensive defect class in this repository's own habits list, and a stop that
> discards work already done is worse than the change it is protecting against. **So a resume that stops
> on a moved apparatus must still write the run record**, with the status and the moving observation in
> it, and exit non-zero — the exit code says the run did not finish; the record says what it did. Decide
> `EXIT_EXTERNAL` versus `EXIT_WRONG` on H7d Part B's own grounds and say which.
>
> If closing it turns out to need surface this task does not own, **file it as a record-loss gap with an
> owner that is a fact with a reason** — but *justifying* the loss is not an option, and the two corrected
> code comments pointing at it are not a routing.

> **AMENDED 2026-08-23 by the controller, after batches 3-4's review found two OWED items reaching no live
> section.** Both are yours: **(a)** `E-RESUME-LEDGER-UNREADABLE`'s § Errors row is **narrower than its
> code** — Decision 17's row was grepped and covers two of its three faults — so widen it to cover every
> fault the code raises it for, checking the table's own **scope sentence**; and **(b)** the
> zero-new-results **apparatus stop** on a resume, which was owed to *"whichever task reaches it first"* —
> an owner that names no one. Measured: it exits 5 and writes no `run.yaml`, but the ledger and step
> artifacts survive and a second `resume` completes at exit 0, **so it is not a record loss today** — the
> defect is the branch's own justification for it, and it **becomes a real loss for `apparatus_changed`
> once task 13 lands.** Fix the justification, and either close the loss or file it with a reason.

**Pointer: Ruling X binds this task (design Decision 3). Read § Errors core raises' lead paragraph AND
§ Errors `validate` reports' lead paragraph before you place a single row.**

Wire the fourteen refusals and write their rows.

**Ruling X: one row per code covering EVERY emit site, and check each table's own SCOPE SENTENCE, not
a design's instruction.** H6a's batch 4 put a row in a table whose scope did not admit it and its
review settled the question by citing the design; H9a then found **thirteen rows narrower than their
code and one wider**. **Quote each table's lead sentence in your report and say why each row is where
it is.**

- **§ Errors core raises** takes `E-RUN-LOCKED` and `E-RUN-ID-EXHAUSTED`. Both are genuine
  `ContractError` raises, so neither needs the `Type`-cell qualification that section's own paragraph
  gives its two non-raise rows. **`E-RUN-LOCKED`'s row must say where it is REACHABLE**, because from
  `run` and `draft` it is not — `allocate_run_dir`'s `mkdir` **is** the claim, so a lock file cannot
  pre-exist a directory those two just created, and `dry-run` takes no lock. `resume` is the only
  command from which it is reachable. Sites: the raise in `RunLock.__enter__`, the two raises in the
  takeover, the report in `cli.main`, and the report through `resume`'s own `Collector`.
  `E-RUN-ID-EXHAUSTED`'s row names `run` and `draft` only (correction 20).
- **§ Errors `validate` reports** takes the thirteen `E-RESUME-*` codes and `E-FREEZE-CONFIG-EDITED`,
  beside the `E-FREEZE-*` rows that are the shipped precedent for a command's own refusals — its lead
  says *"these are the codes a **command** reports."*
- `E-FREEZE-CONFIG-EDITED`'s row **must state that an absent `identity.json` is not this fault** — a
  run directory from a build that predates the artifact has nothing to compare, and `freeze` behaves
  exactly as today. Without that sentence the next reader files the silence as a defect.

**Decision 13: one reporting mechanism for every refusal `resume` decides.** A **fresh**
credential-bearing `Collector`, whose `credentials` is the set `_prepare_run` already resolved — never
a second derivation — printed to stderr. Nothing `resume` decides reaches `cli.main`'s un-redacted
printer. **This is the fifth instance of *copying a recipe's calls without its containment***:
`_prepare_run`'s roster wrapper already has the shape (`except BaseException`, `KeyboardInterrupt`
re-raised fresh and argument-less, a fresh credential-bearing `Collector`) — copy **where it sits**,
not only what it calls.

Also build `freeze`'s `parameters_hash` comparison over the copy it already loads (Decision 15), and
reuse the shipped `E-IO-FAILED` for a `resume` path that does not exist — `diff`'s precedent, exit `1`.

**Must not touch:** § Exit codes' table (task 17's); `E-INPUT-CHANGED`'s absent row; any arm.

**Mutations:** report one refusal by raising into `main` instead of through the `Collector` (caught by
the credential positive control, whose credential is **declared** through `Param(requires_env=)` and
set in the environment — an undeclared one passes vacuously); make each of the fourteen fixtures'
perturbation a no-op in turn and confirm the matching code stops firing.

---

