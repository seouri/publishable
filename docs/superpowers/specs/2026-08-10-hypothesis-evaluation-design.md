# Hypothesis evaluation (S5b) design

**Goal:** a run evaluates each declared hypothesis against its results and records the verdict —
including which number it compared and who computed that number.

**Why it closes S5:** the spine's exit criterion is that the worked example's `h1` renders its
verdict. After this slice the reference implementation is complete, and the documented checkpoint
follows.

## Scope

Everything `E-HYPOTHESIS-UNSUPPORTED` currently refuses, in one slice.

| In | Deliberately not here |
|---|---|
| All three `compare` forms: `{condition, to}`, `{contrast: id}`, and a summary metric with no `compare` | `report` rendering confirmatory findings versus labelled exploration |
| `evaluate_on`: `observed`, `ci95_lower`, `ci95_upper` | `study add`'s redaction rules |
| `declared_in`, `observed`, `supported`, `verdict_evaluated_on`, `verdict_rests_on` | `statistics.null_test`, still refused, so no `p_value_corrected` reaches a verdict |
| The hypothesis correction family: `family_size`, `family: {hypotheses: N}` | |
| `kind: confirmatory \| exploratory`, and what each means for the family | |
| Six documented `validate` rules, plus a `_check_shape` nested guard | |
| The carried `Estimate.ci95` shape rules from S5a | |

**One slice, not three.** Every split considered would leave `validate` accepting a form nothing
evaluates. That is the defect class this project has shipped three times — S4b un-refused declared
contrasts a slice before anything computed them, S4c retired a refusal whose feature landed in the
same slice only because review caught the gap, and the pattern is expensive enough to be worth a
larger slice instead.

## Architecture

**One new pure module, `src/publishable/hypotheses.py`** — no filesystem, no runtime import of
`config`, `artifacts`, `runner` or `cli`, matching `contrasts.py`, `correction.py` and `strata.py`.

It receives the assembled results and the config, and returns the verdict entries. `cli.py` calls
it after `vs_baseline`, `results.contrasts` and `results.summary` all exist, because a hypothesis
may name any of the three.

### Resolution: three arms, one required `metric`

`metric` is `step.metric` in every form. `reference.md`: "`compare` says *where* and never *what*" —
a contrast reports one value per step metric exactly as a condition does, so a `compare` alone
leaves the quantity under test unnamed.

| `compare` | Resolves against | `observed` shape | `verdict_rests_on` |
|---|---|---|---|
| `{condition: <label>, to: baseline}` | that condition's `vs_baseline.<step>.<metric>` | `{delta, ci95, ci95_corrected}` | `computed` |
| `{contrast: <id>}` | that entry in `results.contrasts` | `{delta, ci95, ci95_corrected}` | `computed` |
| absent | `results.summary.<step>.<metric>` — a reported `Estimate` | `{value, ci95, method}` | `reported` |

`verdict_rests_on` is not a fourth thing to derive: it falls out of which arm resolved. The two
`observed` shapes match the two worked examples in `reference.md` § Pre-registration and § A
hypothesis may name a summary metric.

### `evaluate_on` picks the number; `verdict_evaluated_on` records which

The comparison is `direction` (`greater` / `less`) against `threshold`, applied to one of three
numbers: the point estimate, the interval's lower bound, or its upper bound.

The two field names differ on purpose. `reference.md`: `verdict_evaluated_on` is "spelled out
rather than echoing the config's `evaluate_on`, since a record field one letter from a config field
is a typo waiting to be read as agreement." A reader must be able to see which question was asked
without reconstructing it from the config plus a correction rule.

`reference.md` is equally explicit about why the bound forms are not a refinement of the point
form: "`evaluate_on: ci95_upper` is what an equivalence or non-inferiority gate is, and there is no
way to spell one against a point estimate."

### The correction family, generalized rather than duplicated

`correction.py` already holds the ranking statistic, the Holm and Bonferroni level arithmetic, and
the interval-at-a-smaller-α construction. The hypothesis family differs from the sweep's in exactly
one respect, which `reference.md` states directly: it "counts the confirmatory hypotheses whose
observations core computed, where a sweep's family counts comparisons × metrics" — it "multiplies
nothing".

So `correction.py` gains a function taking an explicit family size and breakout. `corrected_fields`
becomes a thin caller passing `family_shape(members)`; `hypotheses.py` passes
`(n, {"hypotheses": n})`. `rank_family`, `_evidence_ratio`, `_level_for` and `_corrected_bounds`
are reused untouched — `_level_for(method, family_size, rank)` is already parameterized by the one
thing that varies.

### Counted-iff-corrected decides everything else

`reference.md`: "Core's hypothesis family is the confirmatory hypotheses whose observations it
computed." Two exclusions follow, and neither is a special case bolted on — both are the rule the
sweep family already follows:

- **An exploratory hypothesis is not counted**, therefore not corrected, therefore a bound test
  reads the **raw** bound.
- **A hypothesis resting on a reported `Estimate` is not counted**, because core "never computed
  it, so it has nothing to correct and no standing to say the correction was applied". Its bound is
  the one the step supplied, and `verdict_rests_on: reported` says so.

A verdict outside the family carries no `family_size` and no `family`, exactly as a comparison
under `correction: none` carries no corrected fields.

### The carried `Estimate.ci95` rules

S5a left `ci95`'s length and ordering unchecked because nothing indexed it. `evaluate_on:
ci95_lower` indexes it, so this slice closes the gap where S5a's other two `Estimate` rules already
live — at coercion, before anything reads a bound:

- A `ci95` that is not exactly two elements is refused.
- A `ci95` whose first element exceeds its second is refused.

Both are mechanically detectable and neither is a judgement about the statistics, which is the
standard `reference.md` already sets for requiring `method`. The document states no rule about
either, so this needs a `docs/superpowers/spec-defects.md` entry alongside the new identifier.

## What `validate` owes

Six rules, each already stated in `reference.md` § Validation:

| Rule | The mistake it catches |
|---|---|
| Hypothesis needs baseline | `compare.to: baseline` where `sweep.baseline` is not declared |
| Hypothesis bound exists | `evaluate_on` names a bound, but no metric this run computes could carry an interval |
| Hypothesis names a real contrast | `compare.contrast` names an id `statistics.contrasts` does not declare |
| Hypothesis names a metric | a `compare` with no `metric`, leaving the quantity under test unnamed |
| Hypothesis form matches its metric | a summary-step metric declaring `compare`, or a condition-step metric without one |
| Hypothesis has an inference base | every metric will be `basis: repeats` — reportable but not testable (**warning**) |

Plus `hypotheses` in `_check_shape`'s nested pass. That is not bookkeeping: S4c shipped two crashes
from a nested config value reaching a reader in a module whose hard contract is that it collects
findings and never raises.

**Identifiers are grepped before being minted.** S5a's plan asserted the documents named none of
its three codes; `reference.md` § Errors core raises named two. Every code here is checked against
the four documents first, and only what is genuinely unnamed gets a `spec-defects.md` entry.

**The refusal retires with the wiring, in the same task.** `E-HYPOTHESIS-UNSUPPORTED` stays while
`hypotheses.py` is built and unit-tested directly against assembled result structures, and while
`validate`'s six rules are added — a rule can be tested through `validate_config` even while the
blanket refusal also fires, since both findings appear together. It comes out only in the task that
makes `cli` evaluate, so the un-refused-but-unbuilt window is zero rather than merely short.

## Two things the documents do not settle

**An observation core cannot resolve.** A hypothesis may name a metric that no run produced — its
step failed, or every unit in a comparison was ineligible, so the entry carries `ci95: null` or is
absent entirely. The verdict then records `supported: null` with the `observed` block showing what
was found, rather than a boolean. A `false` there would be indistinguishable from a claim that was
tested and failed, which is the same confusion `verdict_evaluated_on` exists to prevent one level
up. Nothing in `reference.md` covers this, so it gets a `spec-defects.md` entry.

**`declared_in`'s format.** `reference.md` shows `declared_in: parameters_hash sha256:1a2b...` — a
string naming which hash it is, not a bare digest. The value is the run's own `parameters_hash`,
which is what makes "we predicted this all along" checkable: add a hypothesis after seeing results
and rerun, and the hash will not match the earlier run's.

## Testing

### The pair the document already pins

`reference.md` § Pre-registration states both verdicts for the worked example's `h1`, from one
number: the observed delta of 0.026 clears the declared threshold of 0.02, so it is `supported:
true` on `observed`; the same delta's interval [−0.007, 0.059] does not exclude zero, so the same
hypothesis written `evaluate_on: ci95_lower` comes back `supported: false`. The document calls the
divergence the point of the field: "Neither verdict is wrong; they answer different questions, and
a reader who can see which one was asked can decide what the run showed."

A test pinning both cannot pass against an implementation that ignores `evaluate_on`, which makes
it the sharpest single test in the slice.

### Mutations each test must kill

| Mutation | Caught by |
|---|---|
| Ignore `evaluate_on`, always compare the point estimate | the `h1` pair |
| Flip `direction` | a `less` hypothesis over the same data |
| Count exploratory hypotheses in the family | `family_size` on a run with one of each `kind` |
| Correct a hypothesis resting on a reported `Estimate` | that entry carrying no family and no corrected bound |
| Use the sweep's `family_size` for a hypothesis | a run where the two counts differ |
| Index `ci95` backwards | a `ci95_upper` equivalence test |
| Omit `verdict_evaluated_on` or `verdict_rests_on` | the record-shape assertion |

Every one is run, not reasoned about. Across S4b, S4c, S4d and S5a roughly twenty-five tests were
found that passed against wrong implementations, and in every case running the mutation is what
found them.

## Risks

- **A verdict that does not say what it compared.** `reference.md`: "A record that reported only
  `supported: true` would be the version worth distrusting." So a right boolean with a missing
  `verdict_evaluated_on` or `verdict_rests_on` is a defect, not a cosmetic gap.
- **The two families crossing** — a hypothesis corrected at the sweep's level, or counted in the
  sweep's family. Generalizing `correction.py` by size makes the level arithmetic shared and the
  count explicit at each call site, which is the point of that choice.
- **`validate` raising instead of collecting.** Two crashes of this exact shape shipped in S4c.
- **A silent no-op** — the refusal retired while some form still evaluates to nothing. The
  retirement is sequenced last for this reason.

## Task sequence

Ten tasks, each landing green.

1. `correction.py`: generalize by family size; `corrected_fields` becomes a thin caller.
2. `coercion.py`: the `Estimate.ci95` length and ordering rules, plus the spec-defects entry.
3. `hypotheses.py`: resolve a hypothesis to its `observed` block — all three arms.
4. `hypotheses.py`: the verdict — `direction`/`threshold`/`evaluate_on` to `supported`,
   `verdict_evaluated_on` and `verdict_rests_on`.
5. `hypotheses.py`: the family — who is counted, and the corrected bound for those who are.
6. `validate.py`: the `_check_shape` nested guard, plus the form and metric rules. The blanket
   refusal still fires alongside them; the tests assert the new codes are present, not that they
   are alone.
7. `validate.py`: the baseline, contrast and bound-exists rules, plus the inference-base warning.
8. `cli.py`: wire it — `results.hypotheses` with `declared_in` — **and retire
   `E-HYPOTHESIS-UNSUPPORTED` in the same task**, so nothing is accepted before it is evaluated.
9. Exploratory and reported-`Estimate` hypotheses end to end: evaluated, recorded, uncounted.
10. The acceptance test: the worked example's `h1` both ways, and the record shape in full.
