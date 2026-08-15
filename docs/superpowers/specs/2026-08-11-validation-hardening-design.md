# H1 Validation hardening design

**Goal:** `publishable validate` becomes a command that reports every fault it can find and
never dies, over a config schema that is actually closed — and every identifier it emits has a
seat in the documents.

**Why first:** H1 is ordered ahead of H2, H3, H4 and H7 because each of those adds checks, and
every one of them would otherwise guess at the same type envelope and mint identifiers into the
same absent registry.

## What the scoping measured

A row-by-row read of `docs/reference.md` § Validation against `src/publishable/validate.py`,
recorded in `docs/superpowers/H1-SCOPING.md`. Against 87 table rows plus one prose-stated check:

| Verdict | Count |
|---|---|
| Implemented | 37 |
| Missing, buildable now | **2** |
| Missing, blocked on another slice | **42** — H3 Units 25, H7 Plugins 7, H2 Sweeps 6, H4 Statistics 4 |
| Partial | 7 |
| Unclassifiable | 0 |
| Not `validate`'s job by design — step-runtime, run-time warnings, `dry-run` | 25 |

**The spine's "~85-check engine" framing is wrong, and correcting it is what makes this one
slice.** 42 of those rows describe checks over blocks refused wholesale by an `-UNSUPPORTED`
code, so no config can reach the state they describe; writing them here would mean writing
checks against features that do not exist. They belong to the slices that un-refuse them. H1's
engine work is 2 missing checks and 7 partials.

Identifier counts, pattern `\b[EW]-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*\b`: `src/**` emits 114 `E-` and
17 `W-`; `validate` **surfaces** 72 `E-` and 8 `W-` once the translated `REPL_DECLARATION_CODES`
and `resolve_units` codes are counted; the four documents name 41 `E-` and 17 `W-`. **Only 8 of
`validate`'s 72 are named in any document.**

## Scope

| In | Deliberately not here |
|---|---|
| The config-envelope type schema over every scalar leaf outside `parameters` | The 42 blocked checks — each lands with the slice that un-refuses its block |
| Closing the schema: an unknown key anywhere, not just in `parameters` and `sweep` | Anything `dry-run` reports (H9) |
| The validate-time `E-` registry — a table in § Validation | § Errors core raises, which is raise-time and stays so |
| `compare`'s grammar: the § Pre-registration sentence, then the check | The `E-SWEEP-BASELINE-PARTIAL` question (H2) |
| The 2 buildable-now missing checks and the 7 partials | Diagnostic ordering — **settled, see below** |
| The import-path envelope's remaining residual | |

## Three faults, one cause

The envelope is not a tidy-up. Three distinct user-visible failures share it:

- **A crash.** `metadata.name: [a, b]` and `data.input_dir: [x, y]` each end `publishable validate`
  in a bare `TypeError`. Reproduced at `HEAD`, end to end through the CLI, not inferred from the
  ledger. `validate`'s hard contract is that it collects findings and never raises.
- **A silent skip, which is worse.** `limits.max_executions: "5"` does not crash — the budget
  check is guarded by `isinstance(budget, int)`, so it is skipped, and a design that blows its
  budget validates clean. A crash is at least loud.
- **An open schema.** A top-level `sweeep:` and a `metadata.athors:` both validate clean.
  Reproduced. § Validation says "the schema is closed and `validate` checks every key against it";
  that holds for `parameters.*` and `sweep`'s top-level modes and nowhere else.

`_check_shape` covers container shapes over 8 top-level blocks and 8 hand-enumerated nested
containers, and **zero scalar leaves**. `parameter_spec` is the only leaf-type authority in the
codebase and covers `parameters.*` only — which is correct and must stay that way, because
`parameter_spec` being the single source of truth for `parameters` is a load-bearing invariant.

**So the envelope is the config's own fields, and only those.** It stops at `parameters`, where
`parameter_spec` takes over. That boundary is the design's central claim and every task respects it.

## Architecture

**A new pure module, `src/publishable/envelope.py`** — a declarative leaf-type schema plus a
checker that walks a config and returns findings. No filesystem, no imports of `config`,
`artifacts`, `runner` or `cli`, matching `contrasts.py`, `correction.py`, `strata.py` and
`hypotheses.py`. `validate.py` calls it; `validate.py` keeps collecting and never raising.

Declarative rather than per-field code, for the reason `parameter_spec` is declarative: a table
can be read against § Validation, and a hundred hand-written `isinstance` guards cannot.

**It subsumes `_check_shape` rather than sitting beside it.** Container shape and leaf type are
the same question asked at different depths, and two walks over one document is how the two
disagree. `_check_shape`'s existing behaviour and its `E-CONFIG-SHAPE` identifier are preserved —
this is a widening, not a replacement, and every existing `_check_shape` test must still pass
untouched.

**Closing the schema falls out of the same walk.** A key the schema does not declare is an
unknown key, and the walk already visits every one. `parameters` and `sweep` are excluded from
that closure — they have their own authorities, `parameter_spec` and `_check_sweep`'s mode list.

**Ordering is fatal-first, unchanged.** § Exit codes states that a fault making later checks
meaningless stops the pass. An envelope violation is exactly that class for the field it hits,
but not for the config — a wrong-typed `metadata.name` must not suppress a `data.input_dir`
finding. Findings stay grouped by check.

## Decisions

Two were settled by the user; the rest are adjudicated here against `design-principles.md`.

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | Diagnostic ordering | **Not H1's work.** The spine's charter line is stale and has been amended | The checkpoint's decision 9 amended § Exit codes to *argue for* grouping by check. Implementing config-position ordering would reverse an argument the document makes — the defect shape this project has shipped before |
| 2 | `n: "5"` and other numeric strings | **Refused** | *Settled by the user.* YAML distinguishes `5` from `"5"`, so a quoted number is a typo the format can express. Silent coercion is exactly how `max_executions: "5"` skips its budget check today |
| 3 | `compare: {condition: X}` with no `to` and no baseline | **Refused** | *Settled by the user.* A `compare` naming one condition with nothing to compare against names no comparison. § Pre-registration gains the sentence **first**, per the document-leads rule, then the check follows it |
| 4 | Where the envelope lives | A new pure `envelope.py`, subsuming `_check_shape` | Two walks over one document is how container and leaf rules drift apart |
| 5 | The envelope's boundary | It stops at `parameters` | `parameter_spec` is the single source of truth there, and a second authority over the same keys is the defaults-file problem |
| 6 | Where the 72 validate-time `E-` codes live | A table in § Validation, beside the warnings table decision 1 of the checkpoint created | § Errors core raises scopes itself to "exactly the run-time surface, where there is a step to raise into", and states that everything a *command* reports is a diagnostic. A validate-time code is a diagnostic |

**Decision 6 also closes fifteen ledger entries at once.** Each has proposed, since S1, adding a
validate-time code to § Errors core raises — a fix that section cannot accept. H1 amends all
fifteen to name the new home rather than leaving fifteen restatements of an unlandable plan.

## A scoping claim this spec wrongly discounted

**CORRECTION, 2026-08-11 (made while scoping H2).** This section previously asserted that
`H1-SCOPING.md`'s "rule inverted" finding on `E-SWEEP-BASELINE-PARTIAL` rested on a fabricated
quotation, and instructed H1's tasks not to carry it forward. **That was wrong.** The quoted
sentence — "Prefer the second row whenever the levels are peers" — is real, at `reference.md`
§ Expansion modes. The controller's grep for it was case-sensitive against a sentence-initial
capital, so it could not have succeeded; the absence claim was established by a check that could
not fail, which is the exact defect this slice spent twelve tasks catching in others.

The finding stands and is stronger than "a possible divergence": § Expansion modes carries a
two-row table, the rule "the baseline expands over whichever axes it doesn't fix — group axes and
parameter axes alike", and an instruction to prefer the expanding row. `E-SWEEP-BASELINE-PARTIAL`
refuses that row, and its own message concedes the design is "specified but not implemented in
this build". **Owner: H2 Sweeps**, together with `W-SWEEP-BASELINE-CONFOUNDED`'s unreachable
remedy, which H1's task 10 deferred on exactly these grounds.

## Testing

Every check H1 adds needs a test producing its identifier — the project's standing rule, and the
reason the 42 blocked rows are excluded rather than stubbed.

Three tests carry the envelope, and each pins a different failure mode:

| Test | Pins |
|---|---|
| `metadata.name: [a, b]` through `validate_config` | The crash class: a finding, not a `TypeError` |
| `limits.max_executions: "5"` on a design that exceeds it | The silent-skip class: `W-EXEC-BUDGET` still fires |
| A top-level `sweeep:` and a `metadata.athors:` | The open-schema class: both reported |

The second is the one to write first. A test that only proves "no traceback" would pass against
an implementation that swallows the field and skips its check — which is the bug, not the fix.

**Mutations each must kill:** widening a leaf type to `Any`; skipping a field whose type is wrong
instead of reporting it; closing the schema over `parameters` too, which must break
`parameter_spec`'s own tests; and reporting an envelope violation as fatal to the whole pass.

## Risks

- **The envelope swallowing a check instead of guarding it.** The `max_executions` failure mode is
  already in the codebase: guard on `isinstance`, skip when it fails. An envelope that reports the
  type fault and *still* skips the check has moved the bug, not fixed it. Every check downstream of
  a refused leaf must be reachable in a test with that leaf well-typed.
- **A second authority over `parameters`.** Decision 5 is the guard; the mutation above is the test.
- **72 registry rows stating the wrong condition.** The checkpoint's task 3 found two of eleven rows
  described the wrong branch. At 72 the rate matters: every row cites its emit site and the reviewer
  checks the row against the code, not against the ledger.
- **Scope creep back into the 42.** They are named with owners; a task that starts writing one has
  left H1.

## Task sequence

1. `envelope.py`: the declarative leaf-type schema and its checker, unit-tested directly.
2. Wire it into `validate.py`, subsuming `_check_shape`; all existing shape tests pass untouched.
3. The three failure-mode tests end to end through `validate_config`, plus the numeric-string refusal.
4. Close the schema: unknown keys outside `parameters` and `sweep`.
5. § Validation gains the validate-time `E-` table; the 72 codes land with their conditions read
   from their emit sites.
6. Amend the fifteen ledger entries proposing the unlandable fix to name the new home.
7. § Pre-registration gains `compare`'s grammar sentence; then the check refusing the bare form.
8. The 2 buildable-now missing checks: row 271 (baseline leaves contrasts confounded) and row 276
   (contrast stratum populated at validate time).
9. The 7 partials, each narrowed or widened to what its row states.
10. The import-path envelope residual, and a consistency pass over § Validation.
