# G1 — the growth-chart feasibility gaps: design

Written against [`G1-SCOPING.md`](../G1-SCOPING.md), which measured the seven filed gaps against
`main` at `84e6802` on 2026-08-28 and returned four real code gaps, two documentation-only, and one
retraction. **Read the scoping first**; this file decides, it does not measure.

Every decision below carries its grounds, and two of them record an option they refuse.

---

## Decision 1 (the one the scoping routed here) — gap 2 closes as a **documented limitation**, not as a mechanism

**A correction family does not cross a run, and § Studies says so in its own voice.**

The two closures the scoping costed are not the same kind of thing. A mechanism — a `study.yaml`
block declaring a family over named members, with `report` rendering the adjusted level — would give
a bundle its first computed field. What decides against it is not the cost but *what it would be
computing over*: within a run, `family_shape` counts members **core itself built** from
`vs_baseline` and `statistics.contrasts`, which is what makes `family_size` a number a reader can
re-derive from the record. Across runs the members are whatever a person listed, so the bundle would
correct at an asserted family size and render a level that looks core-computed and is not. That is
the one fault this project's whole correction story exists to avoid — *a number that looks handled
and isn't*.

So § Studies gains a paragraph stating the limit, its reason, and the route: a family spanning runs
is the author's to correct, declared in the manuscript, and each member's own record continues to
carry the within-run family it really was corrected at. The analysis's own case is the worked
example — `{E5a–d}` is four rosters and therefore four runs.

**Refused, and recorded: closing it by making a roster variant a condition.** The other way to make
those four arms one family is to make them one run, which means letting `data.units` vary by
condition. `data.units` is one roster per run, and a roster that varied by condition would make the
conditions incomparable — the resolver's own `cfg` is a `scope: "run"` view for exactly that reason.
This is not a trade, it is the invariant.

**What a reader loses, stated rather than discovered**: the property that a declared family is
checkable against the record stops at the run boundary, and a researcher's family does not. The
paragraph says that, because a limitation a reader has to discover is the same failure as an
undocumented one.

---

## Decision 2 — gap 7 closes as `compare: {to: constant}`, a third form of an existing field

**Not a new field, and not a fourth `evaluate_on` value.**

The claim is *"AUROC exceeds chance"*: a metric against a fixed reference. Three shapes were
available and two are wrong:

| Shape | Why not |
|---|---|
| A new top-level `against_constant:` key | A second spelling for what `compare` already means — *both sides of the comparison* — and `compare`'s own documentation says it "names both sides, not one" |
| Reusing `threshold` with `compare` absent | `threshold` is the decision boundary, not the reference. Overloading it makes "exceeds 0.5 by at least 0.02" unwritable, and that is the ordinary claim |
| **`compare: {to: constant, value: 0.5}`** | `compare` keeps its meaning — it says *what it is measured against* — and the existing `E-HYPOTHESIS-FORM` gate is widened rather than replaced |

**The verdict records what it rested on.** A constant-referenced hypothesis is core-computed from
the metric's own interval, so it is `verdict_rests_on: computed` and it **joins** the hypothesis
family — unlike the `summary`-step `Estimate` route it replaces, which is `reported` and outside the
family. That is the whole gain: the analysis's E2 and E6 claims currently buy their expressibility
by leaving the family, and this puts them back in it.

**`evaluate_on` is unchanged**, and that is load-bearing: `ci95_lower` against a constant is exactly
the superiority claim, `ci95_upper` exactly the non-inferiority one, and both already mean what they
need to mean.

**What it does not do:** it does not make a `summary`-scoped metric take a `compare`. A summary
metric is one value per run, and comparing it against a constant is a claim about a number core did
not compute, which stays `reported`.

---

## Decision 3 — gap 3 is a **warning**, `W-SWEEP-CONDITION-DUPLICATE`, over resolved `values` rather than over baselines

**The check asks the direct question, and the direct question is not about baselines.**

A rule phrased as *"a `baseline` may not fix a path the `grid` lists"* would be a proxy: it names
one route to the fault and would miss the others, and it would refuse a shape that is legitimate
whenever the baseline's value is **not** among the grid's. The fault is *two conditions resolving to
the same `values` over the same units*, which is a property of `expand`'s output and is checkable
whatever mode produced it.

**Warning, not error**, on three grounds. The design is expensive and confusing rather than
unexpressible; a refusal would be a new way for a config that validated yesterday to stop; and the
existing group-axis refusals (`E-SWEEP-LEVEL-DUPLICATE`, `E-SWEEP-BASELINE-GROUP`) stay exactly as
they are, so the sharp cases keep their sharp answers and this catches the soft one they do not
reach.

**The message names the working spelling**, which § Expansion modes already gives and
`W-SWEEP-BASELINE-CONFOUNDED`'s message already quotes: *fix the axis you are measuring and leave
the ones you are stratifying over free, and each cell gets its own baseline.* Two warnings sharing a
remedy sentence is right — they are two symptoms of one mistake about baselines.

**It does not deduplicate.** Core reports; the config decides. Silently dropping a condition would
change what executed without the record saying so, which is the opposite of this project.

---

## Decision 4 — gap 1 keeps the two-segment constraint and gives it a code, a row, and a sentence

**Making the materializer general was considered and refused.**

`reference.md` § Templates says *"There is no `dict` type: a mapping is what nesting the dotted path
already expresses"*, which reads as permitting any depth — so the two available closures are to make
the code match that sentence, or to narrow the sentence.

Narrowing wins, on evidence rather than on cost. Every template in this repository and in both
feasibility analyses is two-level; a three-level namespace has never been wanted; and a general
materializer would have to decide how a three-level path renders its inline comment and its
`# REQUIRED` marker, which is design work for a shape nobody has asked for. **The constraint is
real and defensible — what is wrong is that it is invisible until it crashes.**

So: `E-TEMPLATE-PARAM-PATH`, raised as a `ContractError` where the `ValueError` is today, at template
load rather than at `generate experiment` — a spec whose paths are malformed is malformed for
`list-templates` and `validate` too, not only for the one command that happened to materialize it.
§ Templates states the constraint beside the three-states table, and the `Param` constraint table
gains nothing, because a path is not a constraint on a value.

**The single-segment case is the one a reader will hit**, and the message says so: the analysis's own
workaround renamed `reference_frame` to `frame.reference`, which is the remedy in one word.

---

## Decision 5 — gaps 5 and 6 are sentences, and they go where the type is already documented

`fold.stratify_by` is `str | None`, singular and deliberate — a fold balances on one attribute. The
type is stated in § Repeat kinds' own field table, beside `k`, because that is where a kind's fields
live and the reason § The one config file does not carry it is that its `replication` block shows
what `init` writes.

`measurements.collapse` applies to **every** carried column, which is why the per-column map is the
ordinary case rather than the exception. That sentence goes in § The one config file beside the
inline comment that is currently the only place `by` and `collapse` are named, and § Validation's
rows already carry the refusals it implies.

**Neither is a code change, and neither is optional.** A declared behaviour with no sentence behind
it is the mirror of this repo's oldest misreading — a documented rule with no code — and it cost the
analysis a wrong config each time.

---

## What this design refuses, restated so no task re-litigates it

- **Mixed-effects models, Cochran's Q, conditional logistic regression, the DeLong test, and the
  shortcut reliance index stay refused.** They are `summary`-step `Estimate`s, by
  `design-principles.md`, and nine of the fifteen runs are supposed to route through one.
- **Gap 4 is not a defect.** Batch A corrects the filing; nothing in `src/` moves for it.
- **No condition is ever silently dropped, renamed, or merged** by Decision 3.
