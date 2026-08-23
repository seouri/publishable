## Task 10

**Design Decisions 6, 7, 14 and 15 bind this task, and Decision 14 is the one that has already cost
this repo a credential leak.**

**Decision 14 — the recipe is its calls PLUS where they sit.** Copy `cli.py`'s probe-dispatch wrapper
(~2522–2548) **with its `try`**: `except BaseException`, `KeyboardInterrupt` re-raised fresh and
argument-less, a **fresh credential-bearing `Collector`**, rendered to stderr. The same containment
covers `observe_once`, where the probe body actually runs. H8c's `report` lifted `freeze`'s calls and
left the `try` behind, and a declared credential reached stderr in a case § Secrets promises to
redact. **The file you are copying from already has it right.**

**Decision 6 — do not construct an `Observer`.** Measured: `Observer.__init__` requires `run_dir:
Path` and `_observe_one` calls `append_observation` unconditionally. Call the shipped pieces instead —
`apparatus.observe_once` → `apparatus.check_facts` → `Observations.record` →
`Observations.warn_unanswered` — once per resolved condition, under that condition's own cfg from
`prepared.cfgs`, never the wide one. **Defaulting `run_dir=None` on `Observer` is rejected**: it is a
fail-open shape on a class whose whole guarantee is that the append happens first.

**`check_changed` is omitted, and the ground is measured rather than argued.** `Observations.record`
fills `_first_answered` from the facts it is handed; `changed` compares the *next* facts against that
entry. With one round per condition, the value the gate would compare against is the value it was just
given, so it can only return `None`. Do not call it, and put that reason in the code, not "there is no
baseline".

**Decision 7 — append nothing, and `replay_ledger`'s filter does not widen.** `PHASE_DRY_RUN` keeps
its constant and gains no call site; the **document** is what changes (task 13). Do not touch
`apparatus.PHASES`, and do not touch `replay_ledger`: `dry_run` is load-bearing in two shipped
fixtures as the phase the filter must **exclude** (`tests/test_apparatus.py` ~1113,
`tests/test_freeze.py` ~357), and deleting it would collapse two distinct exclusion reasons into one.

**Decision 15 — the cost ordering is the behaviour.** validate → manifest → probe, stopping at the
first failure: a config with an error exits `1` **without the probe being called**, and only a config
that validates reaches `5`. § Exit codes' own paragraph states this and has no reader; you are it.
Mint no code.

**Fixtures.** **V** — a project-local probe, called once per resolved condition (the probe counts its
own calls into a file **outside `output_dir`**, so the count is evidence and task 11's arm stays
true); `W-APPARATUS-UNANSWERED` fires for a declared fact it did not answer; exit `5` when it is
unreachable. **W** — the credential positive control: a probe raising with a **declared** credential
(through `Param(requires_env=)`, with the variable actually set, so the value set is real and the
redaction is not vacuous) in its message → `<redacted:…>` on stderr. **X** — cost ordering: a config
with a validation error exits `1` and **the probe's entry file does not exist**. An exit-code-only
assertion would pass with the ordering reversed.

**Mutations.** Remove the `try` → W must fail. Reorder so the probe precedes validation → X must fail.
Add `append_observation` → task 11's Fixture Y must fail. Each has two branches that differ; check
before believing.

**Must not touch:** `apparatus.py`, `freeze.py`, `runner.py`, any `*.md`.

---

