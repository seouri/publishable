# Summary `Estimate` (S5a) design

**Goal:** a `summary` step can return an interval it computed itself, and the record says who
computed it.

**Why it matters more than its size suggests:** the interval was already returnable as a bare dict.
What was missing is the marking. `reference.md` § `Estimate`: before this, a core-derived interval
and an author's own model output "looked identical to every tool and to every reader, which was
the worse of the two situations."

## Scope

| In | Out (S5b) |
|---|---|
| `publishable.Estimate` — the type and its export | Hypothesis evaluation, all three forms |
| The `summary`-scope exemption in `coerce_scalars`, including the Estimate's own fields | `evaluate_on`, `verdict_evaluated_on`, `verdict_rests_on` |
| `E-STEP-ESTIMATE-SCOPE`, `E-STEP-ESTIMATE-METHOD`, `W-STEP-ESTIMATE-N` | The hypothesis correction family and `declared_in` |
| `results.summary.<step>.<key>` carrying `reported: true` | Retiring `E-HYPOTHESIS-UNSUPPORTED` |

S5 is cut here because `Estimate` is a prerequisite for exactly one of S5b's three hypothesis
forms — a hypothesis naming a summary metric — while the other two read numbers that already
exist. Building it first means S5b never has to accept a form it cannot evaluate. That is the
silent-no-op class this project has shipped twice: S4b un-refused declared contrasts a slice
before anything computed them, and S4c retired a refusal whose feature landed in the same slice
only because the gap was caught in review.

## The type

**One new module, `src/publishable/estimate.py`**, exported from `publishable/__init__.py`.
`reference.md` § The importable surface already enumerates `Estimate` as a construct — "an interval
a `summary` step computed itself" — so the export is required by the document rather than chosen
here, and no document changes in this slice.

```python
@dataclass(frozen=True)
class Estimate:
    value: float
    ci95: list[float] | None = None
    n: int | None = None
    method: str | None = None
```

**No `__post_init__` validation.** Every rule about an `Estimate` is a diagnostic core emits, not
an exception user code trips over. A `ValueError` raised inside a plugin's `run` surfaces as a bare
traceback carrying no identifier, and this repo's whole error contract is that a failure prints a
stable `E-` code a reader can grep, suppress in a checklist, or cite. Constructing freely also lets
a step build an `Estimate` incrementally, which validation-at-construction would forbid for no gain.

`ci95` is a `list`, matching how `reference.md`'s example constructs one and how the record dumps
it. That makes the frozen dataclass unhashable; nothing keys on it.

## The one exception, and where it lives

`CLAUDE.md` states the invariant: a step's `run` and a template's `aggregate` return a flat mapping
of scalars, "with a NumPy scalar coerced, anything structural a `ContractError`, and an `Estimate`
at `summary` scope the one exception." That sentence *is* `coerce_scalars`' contract, so the
exception belongs there rather than being special-cased upstream in `runner.py` — one place decides
what a step's return may contain.

`coerce_scalars` gains a scope-aware parameter; the runner passes what it already knows. An
`Estimate` at any other scope raises **`E-STEP-ESTIMATE-SCOPE`** rather than the generic structural
refusal, because a message should say what is wrong and not merely that something is.
`reference.md` gives the reason for the restriction: elsewhere an `Estimate` "would be a way to
attach an interval to a per-execution return value, and `per_repeat` is *exactly what the step
returned*."

### The Estimate's own fields are coerced too

This is the half a narrower reading would miss. `coerce_scalars` exists because "a per-unit value a
model hands back is a `numpy.float64` at least as often as a derived metric is, and uncoerced it
reaches `yaml.safe_dump` and raises `RepresenterError` while writing `run.yaml` — a traceback
rather than a diagnostic." A mixed model is *more* likely to hand back NumPy scalars, not less, so
`Estimate(value=np.float64(0.031), ci95=[np.float64(0.008), np.float64(0.055)], n=np.int64(612))`
is the ordinary case. Passing the `Estimate` through untouched would reintroduce at one level of
nesting exactly the traceback S4a removed at the top level.

So the exemption coerces `value`, each element of `ci95`, and `n`, returning a new `Estimate`
(it is frozen). Anything structural *inside* those fields is refused as it would be anywhere else.

## The three rules

| Rule | Diagnostic | Where |
|---|---|---|
| `ci95` present without `method` | `E-STEP-ESTIMATE-METHOD` | `coerce_scalars` |
| `Estimate` outside `scope: "summary"` | `E-STEP-ESTIMATE-SCOPE` | `coerce_scalars` |
| `ci95` present with no `n` | `W-STEP-ESTIMATE-N` | the record site |

The two errors live in `coerce_scalars`, which has both the value and the scope. The warning lives
where a `Collector` exists, as a two-line check (`ci95 is not None and n is None`) rather than a
flag threaded out of a pure function — S5's predecessor had to accept that shape once for
`corrected_fields`' `thin`, and there is no reason to repeat it where the caller can simply look.

`reference.md` names no identifier for any of the three, so all three need
`docs/superpowers/spec-defects.md` entries in the shape `E-STATS-CONTRAST-WITHIN`'s entry uses:
which sentence each implements and why the document names no code.

## The record

`results.summary.<step>.<key>` becomes:

```yaml
results:
  summary:
    step03_site_model:
      site_adjusted_delta:
        value: 0.031
        reported: true
        ci95: [0.008, 0.055]
        n: 612
        method: "mixed model, site random intercept, REML"
      converged: true
```

A bare value returned alongside stays bare — `converged: true` is not wrapped. `results.summary`
already exists and already records bare returns, so this adds a shape rather than a section.

**`reported: true` is the feature.** Not a field beside the feature: it is the only thing that
distinguishes an author's interval from one core derived from the unit table. A record that stored
the fields without it would be the state `reference.md` calls worse than not having the type.

`ci95`, `n` and `method` are written as `null` when absent rather than omitted, because a reader
comparing two summary blocks should not have to distinguish "no interval" from "interval whose key
I forgot to look for". This differs from the absent-not-empty rule the comparison blocks follow,
and deliberately: there, an absent key means no comparison was made; here, the entry exists and its
fields are simply unset.

## What comes free, and must be pinned before S5b leans on it

`reference.md`: core "never recomputes the value, never resamples it, never corrects it, and never
counts it in the family." The last already holds structurally — `correction.Member`s are built only
from comparisons, and a summary step produces none — and the whole-branch review of S4c confirmed
`Member(` appears at exactly one site tree-wide.

S5b's `verdict_rests_on: reported` depends on that guarantee, so this slice pins it with a test
that returns an `Estimate` from a summary step and asserts `family_size` is unmoved. A property
that holds by accident and a property that holds by test are the same until someone edits.

## Testing

### Mutations each test must kill

| Mutation | Caught by |
|---|---|
| Allow `Estimate` at any scope | an `Estimate` returned from a `repeat`-scoped step |
| Drop the field coercion | `Estimate(value=np.float64(...))` reaching `run.yaml` |
| Omit `reported: true` from the record | the record-shape assertion |
| Accept `ci95` without `method` | the method test |
| Skip the `n` warning | an `Estimate` with `ci95` and no `n` |
| Build a `Member` from a summary estimate | `family_size` unmoved when a summary step returns one |
| Wrap a bare value in the `Estimate` shape | `converged: true` staying a bare bool |

Every one is run, not reasoned about. Across S4b, S4c and S4d roughly twenty tests were found that
passed against wrong implementations, and in every case the mutation was what found them.

## Risks

- **A traceback where a diagnostic belongs.** The NumPy-inside-`Estimate` case. Prevented by
  coercing the fields rather than passing the object through.
- **The exemption widened past `summary`.** That would let a step attach an interval to a
  per-execution return, which is the refusal the rest of § `Estimate` rests on.
- **A silent no-op:** an `Estimate` accepted and stored without `reported: true`, which is the
  feature itself going missing while every test about the other fields still passes.
- **`validate` and `run` must not raise where they should collect.** The two errors here are
  `ContractError`s from a step's return, which is the existing mechanism — but the record-site
  warning must not become an exception on a malformed `Estimate`.

## Task sequence

Five tasks, each landing green. No document task: `Estimate` is already specified and already
enumerated in § The importable surface.

1. `estimate.py`: the frozen dataclass, exported from `publishable/__init__.py`.
2. `coercion.py`: the scope-aware exemption, coercion of the `Estimate`'s own fields, and **both**
   errors — `E-STEP-ESTIMATE-SCOPE` and `E-STEP-ESTIMATE-METHOD`. Coercion is touched once.
3. The record shape: `reported: true` and the five fields, with bare values left bare.
4. `W-STEP-ESTIMATE-N` at the record site, plus the three `spec-defects.md` entries.
5. The acceptance test end to end, including `family_size` unmoved and a bare value beside an
   `Estimate` in one return.

The warning comes after the record shape deliberately: it fires where the summary block is
assembled, so that site has to exist first. **Which site that is needs determining rather than
assuming** — `run_record.assemble_run_yaml` has no `Collector` in its signature, so the warning
most likely belongs in `cli.py` beside the collector the aggregate phase already warns into. The
implementer confirms this against the code rather than taking it from here.
