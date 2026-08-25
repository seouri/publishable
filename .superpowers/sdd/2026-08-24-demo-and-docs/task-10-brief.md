## Task 10

**Binding corrections: 1, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16.**

**`demo` stops 1–2.** Create `src/publishable/demo.py`. Stop 1 writes the data **outside** the created
repo, scaffolds the project, and commits. Stop 2 prints the config's `sweep` and `replication` blocks
verbatim.

> **RULING DD (binding, restated here):** `demo` **produces its own numbers**. It generates a real
> dataset, runs the real arc, and README's demo numbers become whatever `demo` actually prints.
> **`cohort-pilot`'s numbers must not move — not one digit.** Cost if wrong: README shows numbers no run
> produces, which is the *documented rule with no code behind it* defect on the one page a new user
> reads first.

What stop 1 creates:
- `~/publishable-demo-data/input/index.csv` — **240 rows**, columns `unit_id`, `x`, `y`, by design
  § 9's fixture-A recipe: `random.Random(<fixed literal>)`, `x = rng.gauss(0, 1)`,
  `y = ρ·x + sqrt(1 − ρ²)·rng.gauss(0, 1)`, **both rounded to six decimals**. The rounding is
  deliberate: it makes the CSV the artifact of record.
- `templates/correlation.py` — a **project-local** template registered `correlation`. **Not `generic`**
  (correction 1: `generic` derives nothing, so a demo naming it prints no `r`).
- `src/correlation_pilot/` — **three** steps: `step01_load_cohort` (`run`), `step02_fit_model`
  (`condition`), `step03_analyze` (`repeat`).
- `configs/correlation-pilot/config.yaml` — `experiment_type: correlation`, **no `template_version`**,
  `baseline: {analysis.method: pearson}` and `grid: {analysis.method: [spearman, kendall]}`, one
  `{kind: seed, n: 5}` repeat. **No `statistics.resample` block** (correction 9: a derived metric is
  bootstrapped without one, and stop 2 promises only `sweep` and `replication`).
- `.demo-progress`, and **an append to the demo repo's own `.gitignore`** — **not** to
  `scaffold.GITIGNORE` (correction 16, design Decision 9).
- `git init` and one commit, with the tree clean afterwards so stop 5's `run` is not pushed onto
  `draft`.

**`aggregate` reads RECORDED columns** (`units.pred`, `units.truth`), never declared attributes —
correction 10: the attribute route gives the paired contrast `0 of 2000` and a `null` interval, which
is README's headline number. **`step03_analyze` records `{"pred": …, "truth": …}` and skips twelve
named keys** (correction 13), and sets `nondeterministic = True`, drawing from `self.rng` — **which is
a `random.Random`, so `.gauss`, never `.normal`** (corrections 3 and 4; a step written from the
document raises).

**Mutations:** design § 10 rows 10 and 11. Row 10's assertion has **two halves that one assertion
cannot separate**: `.demo-progress` is ignored in the demo repo **and** absent from a plain
`publishable new` project's `.gitignore`.

**Must not touch:** `scaffold.GITIGNORE`; README; guard-pin arms.

---

