# G3 design — a run's findings reach its record

**Scoping:** [`G3-SCOPING.md`](../G3-SCOPING.md), measured 2026-08-28 against `d8c268b`.

The defect: core discloses at run time and the record keeps none of it. The fix has to answer four
questions — where it lands, what shape it takes, how it is collected without missing a site, and what
it may not contain.

## Decision 1 — it goes in `run.yaml`, not a side file

A `findings.jsonl` beside `executions.jsonl` is the obvious shape and is **refused**, on one ground
that outweighs its advantages: **`study add` copies `run.yaml` and nothing else.** A study bundle is
what sits beside a manuscript, so a disclosure in a side file never reaches the reviewer — which is
one of the three readers the defect is about.

The side file's advantages are real and are given up knowingly: it would leave the record byte-stable,
need no oracle update, and survive a crash that loses `run.yaml`. The last is worth least: a run that
never wrote `run.yaml` produced no results to explain.

Against it, `diff` is measured to be unaffected either way (§ Two claims), so the usual objection to
growing the record does not apply here.

## Decision 2 — `findings:`, not `warnings:`, and every level

A record **can** be written beside errors, and this is measured rather than assumed: `E-INPUT-CHANGED`
sets `status = "failed"`, renders an error through a collector, and the run goes on to write
`run.yaml`. A block named `warnings` would have to either drop that — the most consequential
disclosure a failing run makes — or lie about its own name. The block is `findings:`, each entry `{level, code, path, message}`, which is
`Diagnostic`'s own shape.

**Absent when empty**, never `findings: []` — the rule `weighted_by` and `unevaluable` already follow.
A clean run's record gains nothing, which also keeps the common case byte-identical to today.

## Decision 3 — one helper at 12 sites, and a test that no site is missed

Every run-path finding is already printed through `Collector.render()`. The change is to replace
`print(c.render())` with `_disclose(c, prepared)`, which prints exactly what it prints today and
appends the same findings — redacted — to a list the run already carries.

**The list rides on `Prepared`**, the dataclass `_prepare_run` already returns and `_execute_prepared`
already receives. No new parameter is threaded and no new seam is opened: the two functions are
coupled by that object today, so the findings travel where everything else about the run travels.

**The redaction lives in `Collector`, beside `render`.** A `disclosed()` method returns the same
findings with `redact(message, self.credentials)` applied — so exactly one place knows how a
credential is removed from a message, and the screen and the record cannot drift apart. `_disclose` is
then one call at each site rather than a print plus an append, which matters because two calls are
half-doable and one is not.

The hazard is a missed site: a warning that prints and is not recorded is invisible, and no assertion
about the record can see it. So the pin is **source-level** — a test asserting that `_prepare_run` and
`_execute_prepared` contain no bare `print(<collector>.render())`. That is the same shape as the
wiring pin the growth-chart pipeline needed, and it is the only shape that can fail here.

## Decision 4 — no persisted message may contain a host path

Two run-path messages interpolate a path, and only one is a problem. `E-INPUT-CHANGED` names the
files that moved, and `verify_manifest` returns **relative** paths — nothing host-identifying, so it
stands as written. `W-ENV-UNLOCKED` is the only message that interpolates a host path. It stops interpolating
`repo_root`; the reader is standing in the repository. After that, the invariant is total and testable:
no message core persists names a host path.

This is *prevent rather than redact*, the shape `apparatus.py` already uses for a moved credential.
The alternative — teaching `study add` to redact host values out of prose — is fuzzy string matching
over messages, and it would have to be re-checked every time any message changed.

## Decision 5 — redaction lives in one place, not two

`Collector.disclosed()` applies `redact(message, self.credentials)` — the same call `render` makes,
in the same class, on the same field. A collector that redacts nothing on screen redacts nothing in
the record, and that is structural rather than maintained: there is one implementation, and both
surfaces read it.

Two facts from the scoping make that sufficient rather than hopeful: `secrets.py` is the only reader
of `os.environ`, and the four run-path collectors without `credentials` are all rendered *before*
`credential_values()` is called. A value core has not yet read cannot appear in a message.

## Decision 6 — `report` renders the block, or the record carries it for nobody

The defect names three readers: the co-author, the reviewer, and the author months later. Two of them
read the record through `publishable report`, not by opening `run.yaml` in an editor. A record that
carries findings while `report` silently drops them fixes the storage and not the disclosure.

`report` already builds typed rows behind a `kind` discriminator — `metric_n`, `execution`,
`provenance_units` — so a `finding` row is the idiom already there rather than a new surface. That is
what keeps this inside the slice instead of being a second one: it is one row kind and one render arm.

## What this does not do

- It does not persist `validate`'s findings. They belong to a command that writes no record, and the
  run directory holds the `config.yaml` they were derived from.
- It does not persist findings from `report`, `freeze`, `study`, `diff`, `docs` or `reproduce`.
- It does not add a *new* diagnostic. Every finding it persists is one core already reports.
- It does not make a run fail, warn differently, or change any verdict. Every number in `run.yaml` is
  unchanged; the record gains one optional block.

## The cost, stated

The bit-stability oracle over the correction machinery pins the whole normalized `run.yaml`. Its
fixture emits warnings, so the literal moves once. **That is the oracle working** — a record change it
did not catch would be the defect. It is updated deliberately, in its own task, with the diff read
rather than regenerated.
