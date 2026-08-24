## Task 13

**Pointer: Decision 11 binds this task.**

The apparatus baseline is **replayed**, not re-probed.

- `apparatus.replay_ledger` gains a code parameter defaulting to `"E-FREEZE-LEDGER-UNREADABLE"`, so
  `freeze` stays byte-identical (correction 18). `resume` passes `"E-RESUME-PROBES-UNREADABLE"`. **Do
  not rename the shipped code**: a `FREEZE` code printed by a command that is not `freeze` is a lie
  about which command found the fault, and § Exit codes' own rule is that the identifier is the
  contract.
- Thread the replayed `Observations` into the `Observer` `_execute_prepared` builds, so a resumed
  execution is gated against the **original** run's first-answered facts.
- **An absent or empty baseline is legitimate for `resume` and mints no refusal.** `freeze`'s
  `E-FREEZE-LEDGER-MISSING` exists because probing then would pin a fact the run never adopted; for a
  resume, a run that crashed before its first probe is entitled to set one, exactly as the original
  run's first probe would have. **`freeze`'s refusal must not be inherited by copy.**

**The fixture must make the two readings differ.** A project-local probe whose answers are read from a
file the fixture rewrites **between** the crash and the resume, so the original baseline and the
resume's own first probe are different. Without that, the mutation removing the replay is blind — which
is exactly how H9a's Fixture Y failed, on three shipped arms that all drove a `generic` project with
`apparatus_probe = None`.

**Must not touch:** `freeze.py`; `Observations.record`; `apparatus.PHASES`; any `*.md`.

**Mutations:** drop the baseline and let the resume's first probe set it (the differing-probe fixture);
widen `replay_ledger`'s two-phase filter (caught by a fixture with a `freeze` line and a `dry_run` line
in the ledger, both of which must stay excluded — H9a Decision 7 ruled the filter does not widen and
`resume` is its second caller).

---

