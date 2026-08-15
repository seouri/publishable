# H1 Validation — scoping measurement

Read-only measurement, 2026-08-11, against `docs/reference.md` § Validation and
`src/publishable/validate.py` at commit `88bb6a0` (branch `s4b-contrasts`). No source file
was changed. The question this answers: is **H1 Validation** — spec'd in
`docs/superpowers/specs/2026-08-08-implementation-spine-design.md` § The hardening slices as
"the full ~85-check engine; `validate`'s type envelope over scalar leaves; the diagnostic
ordering and the import-path envelope" — one slice of work or two.

## Method, and the fifth verdict class

§ Validation is not one table. It contains three, plus prose:

| Block | Lines | Rows | Whose job |
|---|---|---|---|
| The main check table | 204–290 | 87 | `validate` |
| "Checked as a step runs" | 302–311 | 9 | `ContractError` at execution — ¶313 says so explicitly |
| § Warnings core reports | 327–343 | 17 | mixed; each row's own condition text says validate-time or run-time |
| ¶296 — six checks *deliberately absent* | 296 | 6 | `run`, `resume`, `dry-run` |
| ¶298, ¶317 — prose-stated checks | 298, 317 | 2 | one `validate` (entrypoint import), one `dry-run` |

Only the 87-row main table plus ¶298 are `validate`'s work. The other 25 stated checks get a
fifth verdict, **NOT-VALIDATE (by design)** — they are not MISSING, and folding them into that
count would inflate H1 by roughly a quarter of the section. The eight validate-time rows of
§ Warnings core reports are not counted separately: each is the warning half of a main-table
row already classified below.

**Rule used for IMPLEMENTED.** A check `validate` reaches through a callee whose
`ContractError` it converts into a finding under the *same* identifier counts as IMPLEMENTED.
`_check_units` does this for everything `units.resolve_units` raises, and `_check_replication`
does it for the ten codes in `REPL_DECLARATION_CODES`. Verified by reading both conversion
sites, not assumed.

## Summary

### The 87-row main table, plus ¶298

| Verdict | Count |
|---|---|
| IMPLEMENTED | **37** (36 table rows + ¶298's entrypoint-import rule) |
| PARTIAL | **7** |
| MISSING — buildable now | **2** |
| MISSING — blocked on another slice | **42** |
| UNCLASSIFIABLE | **0** (two rows are ambiguous in *owner* only; see below) |

### The 42 blocked, by owning slice

| Blocking slice | Rows | Currently refused by |
|---|---|---|
| **H3 Units** | 25 | `E-DATA-{HOLDOUT,ASSIGN,CLUSTER,WEIGHT,MEASUREMENTS}-UNSUPPORTED`, `E-DATA-ALLOCATION-UNSUPPORTED`, `E-REPL-FOLD-STRATIFY-UNSUPPORTED` |
| **H7 Plugins and the apparatus** | 7 | `E-DATA-RESOLVER-UNSUPPORTED`; credentials/probe checks have no config path at all yet |
| **H2 Sweeps** | 6 | `E-SWEEP-{ABLATE,SAMPLE,GROUPS}-UNSUPPORTED` |
| **H4 Statistics** | 4 | `E-STATS-{RESAMPLE,NULLTEST}-UNSUPPORTED` |

Every blocked row is blocked in the strong sense: **no config can reach the state the row
describes**, because the block that would produce it is refused wholesale today. These are not
42 unwritten checks someone must write under H1 — they are 42 checks each of the four owning
slices must write as part of un-refusing its own block. Counting them against H1 would
roughly triple its apparent size.

### The rest of § Validation

| Verdict | Count |
|---|---|
| NOT-VALIDATE (by design) — step-runtime table | 9 |
| NOT-VALIDATE (by design) — run-time warnings | 9 |
| NOT-VALIDATE (by design) — ¶296's six | 6 |
| NOT-VALIDATE (by design) — ¶317 `dry-run` | 1 |

Total stated checks read: 87 + 1 + 25 = **113**, consistent with the brief's "roughly 115".

## Row-by-row classification

Line numbers are `docs/reference.md` as read. "Settled by" names the function and the
identifier reaching the user.

### Main table (204–290)

| # | Row | Verdict | Settled by |
|---|---|---|---|
| 204 | Required fields present | IMPLEMENTED | `_check_metadata` `E-META-REQUIRED`; `_check_data` `E-DATA-REQUIRED`/`E-DATA-POLICY`; `_check_entrypoint` `E-ENTRYPOINT-REQUIRED`; `_check_parameters` `E-PARAM-MISSING` |
| 205 | Types | **PARTIAL** | `_check_parameters` → `Param.check` → `E-PARAM-VALUE`, for `parameters.*` **only**. No leaf outside `parameters` has a declared type. See Q1 |
| 206 | Ranges | IMPLEMENTED | `Param.check` `E-PARAM-VALUE` |
| 207 | Choices | IMPLEMENTED | `Param.check` `E-PARAM-VALUE` |
| 208 | Unknown keys | **PARTIAL** | `_check_parameters` `E-PARAM-UNKNOWN` (with difflib hint) covers `parameters.*`; `_check_sweep` `E-SWEEP-KEY-UNKNOWN` covers `sweep`'s top-level modes. **Nothing else is closed.** Probed: a top-level `sweeep:`, a `metadata.athors:`, and a `limits.max_execution:` all validate clean |
| 209 | Naming convention | IMPLEMENTED | `_check_metadata` `E-NAME-PATTERN` |
| 210 | Name matches its directory | IMPLEMENTED | `_check_metadata` `E-NAME-DIR` |
| 211 | Template is installed | **PARTIAL** | `validate_config` `E-TEMPLATE-UNKNOWN` lists known templates; the row's `plugin`-field hint ("should come from `someuser/publishable-llm`") is absent — H7 owns the registry |
| 212 | Template version moved | **PARTIAL** | `_check_versions` `W-TEMPLATE-VERSION` compares against the module constant `materialize.TEMPLATE_VERSION`, not the installed template's own reported version (`BaseTemplate` declares no `version`); the row's second half — "`request.timeout` is new and unset" — is not reported at all |
| 213 | Replication floor | IMPLEMENTED | `_check_replication` `W-REPL-FLOOR` |
| 214 | Sweep paths resolve | IMPLEMENTED | `_check_sweep._path_resolves` `E-SWEEP-PATH-UNKNOWN` |
| 215 | Swept values legal | IMPLEMENTED | `_check_sweep._value_checks` `E-PARAM-VALUE` |
| 216 | Ablation targets | MISSING — blocked **H2** | `sweep.ablate` refused by `E-SWEEP-ABLATE-UNSUPPORTED` |
| 217 | Ablation needs a baseline | MISSING — blocked **H2** | same |
| 218 | Ablation doesn't compose with a parameter axis | MISSING — blocked **H2** | same |
| 219 | Ablation baseline isn't a group level | MISSING — blocked **H2** | same, plus `E-SWEEP-GROUPS-UNSUPPORTED` |
| 220 | Sample ranges | MISSING — blocked **H2** | `E-SWEEP-SAMPLE-UNSUPPORTED` |
| 221 | Baseline is a valid condition | IMPLEMENTED | `_check_sweep` baseline loop, `E-SWEEP-PATH-UNKNOWN` / `E-PARAM-VALUE` |
| 222 | Swept values are nameable | IMPLEMENTED | `_check_sweep._value_checks` → `sweep.check_swept_value` → `E-SWEEP-VALUE-UNNAMEABLE`. **Note for the spine:** H2's line item "wiring `check_swept_value` into `validate`'s call path" is already done (`validate.py:909`) |
| 223 | Repeat kind coherence (`bootstrap`) | IMPLEMENTED | `replication.REJECTED_KINDS` → `E-REPL-KIND`, translated by `_check_replication` |
| 224 | Batch has something to measure | IMPLEMENTED | `_check_replication` `W-REPL-DETERMINISTIC`, reading `nondeterministic` off imported step classes |
| 225 | Batch takes no fields | **PARTIAL** | `replication._check_count_field` `E-REPL-LEVEL-FIELD` refuses only `k` on a non-fold level. The row says "`n` is the only field it accepts" — `{kind: batch, n: 5, stratify_by: x}` is accepted silently |
| 226 | Each kind takes its own count | IMPLEMENTED | `_check_count_field` `E-REPL-LEVEL-FIELD` |
| 227 | Null test coherence | MISSING — blocked **H4** | `E-STATS-NULLTEST-UNSUPPORTED` |
| 228 | Shuffle level is unambiguous | MISSING — blocked **H4** | same |
| 229 | Clusters enough to resample | MISSING — blocked **H4** | `E-STATS-RESAMPLE-UNSUPPORTED`; also needs `cluster_by` (H3). Owner ambiguous between H4 and H3; blocked either way |
| 230 | Technical replicates | IMPLEMENTED | `REJECTED_KINDS["technical"]` → `E-REPL-KIND` |
| 231 | Collapse rule fits the column | MISSING — blocked **H3** | `E-DATA-MEASUREMENTS-UNSUPPORTED` |
| 232 | Grid size sane | IMPLEMENTED | `_check_sweep` `W-EXEC-BUDGET`, over `expand(doc)` × `_repeat_total`. Narrow in one respect: guarded by `isinstance(budget, int)`, so a string `max_executions` **silently skips** the check — an envelope defect, see Q1. Classified IMPLEMENTED rather than PARTIAL, and row 205 PARTIAL, on a uniform rule: 232's check performs exactly what its row states whenever the value is well-typed, so its defect belongs to the envelope; 205 *is* the type check, and outside `parameters.*` it does not exist at all |
| 233 | Leave-one-out is affordable | IMPLEMENTED | `_repeat_total` resolves `{kind: fold, k: all}` against the roster; `W-EXEC-BUDGET` |
| 234 | Credentials present | MISSING — blocked **H7** | `requires_env`/secrets unbuilt; spine § Out of scope, to hardening |
| 235 | Credentials a swept value needs | MISSING — blocked **H7** | same |
| 236 | `requires_env` covers its choices | MISSING — blocked **H7** | same |
| 237 | Probe is installed | MISSING — blocked **H7** | apparatus probe registry unbuilt |
| 238 | Data outside repo | IMPLEMENTED | `_check_data` `E-DATA-IN-REPO` via `provenance.resolves_inside_repo` |
| 239 | Manifest readable | IMPLEMENTED | `_check_data` `E-DATA-UNREADABLE` |
| 240 | Unit keys unique | IMPLEMENTED | `units.resolve_units` `E-UNITS-KEY-DUPLICATE`, translated by `_check_units` |
| 241 | Attribute names aren't reserved | IMPLEMENTED | `units._from_table` `E-UNITS-ATTR-RESERVED` |
| 242 | Resolver is installed | MISSING — blocked **H7** | `E-DATA-RESOLVER-UNSUPPORTED` |
| 243 | Resolver supplies the attributes | MISSING — blocked **H7** | same |
| 244 | Attributes have a source | **PARTIAL** | `units._from_table` `E-UNITS-ATTR-MISSING` covers the *table* source. The row's own example is the **glob** source, and `_from_glob` builds every `Unit` with `attributes={}` without reading `decl["attributes"]` at all — so `from: {glob: "*.dcm"}` with declared attributes validates clean and yields empty attributes. Buildable now |
| 245 | Resolver supplies the measurement field | MISSING — blocked **H3** (and H7) | `E-DATA-MEASUREMENTS-UNSUPPORTED` + `E-DATA-RESOLVER-UNSUPPORTED` |
| 246 | Resolver is condition-independent | MISSING — blocked **H7** | `E-DATA-RESOLVER-UNSUPPORTED` |
| 247 | Stratification attribute exists | MISSING — blocked **H3** | Row does not say *which* `stratify_by`. All three candidates are refused today: `fold.stratify_by` (`E-REPL-FOLD-STRATIFY-UNSUPPORTED`), `assign.*.stratify_by` (`E-DATA-ASSIGN-UNSUPPORTED`), `resample.stratify_by` (row 282, H4). Verdict stable regardless of which is meant |
| 248 | Repeat kind needs units | IMPLEMENTED | `_check_replication` `E-REPL-FOLD-NO-UNITS` |
| 249 | Holdout isn't a repeat kind | IMPLEMENTED | `REJECTED_KINDS["holdout"]` → `E-REPL-KIND` |
| 250 | One evaluation split, not two | MISSING — blocked **H3** | `E-DATA-HOLDOUT-UNSUPPORTED` |
| 251 | Holdout is resolvable | MISSING — blocked **H3** | same |
| 252 | Holdout strata survive clustering | MISSING — blocked **H3** | same + `E-DATA-CLUSTER-UNSUPPORTED` |
| 253 | Biological replicates are units | IMPLEMENTED | `REJECTED_KINDS["biological"]` → `E-REPL-KIND` |
| 254 | Allocation needs arms | MISSING — blocked **H3** | `E-DATA-ALLOCATION-UNSUPPORTED` |
| 255 | Every axis is assigned | MISSING — blocked **H3** | `E-DATA-ASSIGN-UNSUPPORTED` |
| 256 | Every assignment names an axis | MISSING — blocked **H3** | same |
| 257 | Axis names are distinct | MISSING — blocked **H2** | `E-SWEEP-GROUPS-UNSUPPORTED` |
| 258 | Stratification is forward-only | MISSING — blocked **H3** | `E-DATA-ASSIGN-UNSUPPORTED` |
| 259 | Cells are populated | MISSING — blocked **H3** | same; also has no `W-` identifier anywhere (see § Unnamed warnings) |
| 260 | Arms need allocation | MISSING — blocked **H3** | `E-DATA-ALLOCATION-UNSUPPORTED` |
| 261 | Ratio names levels | MISSING — blocked **H3** | `E-DATA-ASSIGN-UNSUPPORTED` |
| 262 | Block size fills the arms | MISSING — blocked **H3** | same |
| 263 | Attribute assignment resolves | MISSING — blocked **H3** | same |
| 264 | Allocation is coherent | MISSING — blocked **H3** | `E-DATA-ALLOCATION-UNSUPPORTED`; no `W-` identifier |
| 265 | Allocation strata exist | MISSING — blocked **H3** | `E-DATA-ASSIGN-UNSUPPORTED` |
| 266 | Clustering looks undeclared | MISSING — blocked **H3** | `E-DATA-CLUSTER-UNSUPPORTED` — the warning would advise declaring a field that is refused; no `W-` identifier |
| 267 | Folds fit inside the clusters | MISSING — blocked **H3** | `E-DATA-CLUSTER-UNSUPPORTED` |
| 268 | Folds fit inside the cells | MISSING — blocked **H3** | `E-DATA-ALLOCATION-UNSUPPORTED` |
| 269 | Fold count is legal | IMPLEMENTED | `replication._fold_k` `E-REPL-FOLD-K` |
| 270 | Fold strata survive clustering | MISSING — blocked **H3** | `E-REPL-FOLD-STRATIFY-UNSUPPORTED` + `E-DATA-CLUSTER-UNSUPPORTED` |
| 271 | Baseline leaves contrasts confounded | **MISSING — buildable now** | `confounded` is computed only at run time (`cli.py:348`, `differs_on > 1`). A ≥2-axis `grid` with a fully-fixed `baseline` is a supported design today, so this warning is writable against `expand(doc)` alone. Has no `W-` identifier |
| 272 | Contrast names a condition | IMPLEMENTED | `_check_contrasts` `E-STATS-CONTRAST-UNKNOWN` |
| 273 | Contrast has two distinct sides | IMPLEMENTED | `_check_contrasts` `E-STATS-CONTRAST-SAME-SIDES` |
| 274 | Contrast has units in common | MISSING — blocked **H3** | Under the only supported `allocation: within`, every condition shares one roster, so the intersection is never empty. Needs `between` (`E-DATA-ALLOCATION-UNSUPPORTED`) |
| 275 | Contrast stratum is an attribute | IMPLEMENTED | `_check_contrasts` `E-STATS-CONTRAST-WITHIN` |
| 276 | Contrast stratum is populated | **MISSING — buildable now** | `W-STATS-CONTRAST-THIN` exists but is emitted at run time only (`cli.py:471`, over `n_paired`). § Validation lists it as a validate-time check against the roster — the exact `W-STATS-REPORTBY-THIN` / `W-STATS-STRATUM-THIN` split ¶296 draws for `report_by`, which has no counterpart for `within` |
| 277 | Reporting stratum is an attribute | IMPLEMENTED | `_check_report_by` `E-STATS-REPORTBY-UNKNOWN` |
| 278 | Reporting stratum is populated | IMPLEMENTED | `_check_report_by` `W-STATS-REPORTBY-THIN` via `strata.levels_for` |
| 279 | Weight attribute exists | MISSING — blocked **H3** | `E-DATA-WEIGHT-UNSUPPORTED` |
| 280 | Weights are usable | MISSING — blocked **H3** | same |
| 281 | Weighting looks undeclared | MISSING — blocked **H3** | same; no `W-` identifier |
| 282 | Resample strata exist | MISSING — blocked **H4** | `E-STATS-RESAMPLE-UNSUPPORTED` |
| 283 | Correction declared for a family | IMPLEMENTED | `_check_sweep` `W-STATS-FAMILY`, sized by `resolve_contrasts`. Doc-internal tension worth noting: this row says "6 conditions × 3 metrics produce a family of 15", the § Warnings row says "comparisons **per metric**" — the code follows the warnings row |
| 284 | Correction can be applied | **PARTIAL** | `_check_sweep` `W-STATS-CORRECTION-INAPPLICABLE` fires whenever `correction == "fdr_bh"` and the family is non-empty — it never tests whether `null_test` is declared or reaches members. Correct by accident today (`null_test` is refused); becomes over-broad the moment H4 lands |
| 285 | Hypothesis needs baseline | IMPLEMENTED | `_check_hypotheses` `E-HYPOTHESIS-BASELINE` |
| 286 | Hypothesis bound exists | IMPLEMENTED | `_check_hypotheses` `E-HYPOTHESIS-BOUND` |
| 287 | Hypothesis names a real contrast | IMPLEMENTED | `_check_hypotheses` `E-HYPOTHESIS-CONTRAST` |
| 288 | Hypothesis names a metric | IMPLEMENTED | `_check_hypotheses` `E-HYPOTHESIS-METRIC` |
| 289 | Hypothesis form matches its metric | IMPLEMENTED | `_check_hypotheses` `E-HYPOTHESIS-FORM` |
| 290 | Hypothesis has an inference base | IMPLEMENTED | `_check_hypotheses` `W-HYPOTHESIS-INFERENCE-BASE` |

### Prose-stated checks in § Validation

| Line | Stated check | Verdict |
|---|---|---|
| 292 | "the schema is closed and `validate` checks every key against it" | **PARTIAL** — restatement of row 208; closure holds for `parameters.*` and `sweep`'s modes only |
| 294 | "Every threshold in that table lives in `limits`" | Not a check — a design constraint. Holds: `limits.max_executions` and `limits.min_reported_n` are the two thresholds `validate` reads, both from the config |
| 296 | Six deliberately-absent checks | NOT-VALIDATE ×6 (`max_failed_fraction`, `max_ineligible_fraction`, `W-STATS-STRATUM-THIN`, `W-STATS-CORRECTED-THIN`, lockfile drift at `resume`, apparatus reachability at `dry-run`) |
| 298 | "a package that won't import is a `validate` failure" | IMPLEMENTED — `validate_config` `E-ENTRYPOINT-IMPORT`, including the `SystemExit` path |
| 302–311 | The nine step-runtime rows | NOT-VALIDATE ×9 — ¶313 makes this explicit |
| 317 | `dry-run` does more | NOT-VALIDATE — H9 |

### § Warnings core reports (327–343)

Eight rows fire at `validate` and are all IMPLEMENTED (each already counted above):
`W-EXEC-BUDGET` (232/233), `W-HYPOTHESIS-INFERENCE-BASE` (290), `W-REPL-DETERMINISTIC` (224),
`W-REPL-FLOOR` (213), `W-STATS-CORRECTION-INAPPLICABLE` (284, partial), `W-STATS-FAMILY` (283),
`W-STATS-REPORTBY-THIN` (278), `W-TEMPLATE-VERSION` (212, partial).

Nine fire at `run`: `W-DATA-INELIGIBLE`, `W-ENV-UNLOCKED`, `W-STATS-AGGREGATE-FAILED`,
`W-STATS-CONTRAST-THIN`, `W-STATS-CORRECTED-THIN`, `W-STATS-RESAMPLE-THIN`,
`W-STATS-STRATUM-SHADOWED`, `W-STATS-STRATUM-THIN`, `W-STEP-ESTIMATE-N`. All are emitted
somewhere in `src/**` (all 17 documented `W-` codes exist in the source).

### Unnamed warnings — a spec defect H1 must close first

Six warning rows in the main table have **no `W-` identifier** anywhere in the four documents,
though § Warnings core reports presents itself as the register ("it carries a stable `W-`
identifier for the same reason an error carries an `E-` one"): rows **229, 259, 264, 266, 271,
281**. Row 271 is one of the two buildable-now MISSING checks, so H1 cannot implement it
without minting an identifier — and per CLAUDE.md the document changes first.

## Reverse direction: codes `validate` surfaces with no § Validation row

`validate` surfaces **41** identifiers that no main-table row describes. None is a wrong
identifier. Two different findings are separated here, because they have different remedies:
**rule undocumented** (a document must state the check) and **rule stated, identifier unnamed**
(only the `E-` string is missing). Identifier-absence was measured by set-diff; rule-presence
was measured by reading § Expansion modes (1386–1546), § Repeat kinds (1546–1805), § Where
units come from, § Contrasts, § Pre-registration and § The one config file directly.

| Code(s) | Verdict |
|---|---|
| `E-CONFIG-PARSE` | **Rule undocumented.** No document states that an unparseable config or a non-mapping top level is a `validate` finding |
| `E-CONFIG-SHAPE` | **Rule undocumented.** The rule it enforces (each top-level block's container type) is implied by § The one config file's example but stated nowhere |
| `E-SWEEP-{PAIRED,ABLATE,SAMPLE,GROUPS}-UNSUPPORTED`, `E-DATA-{RESOLVER,ALLOCATION,ASSIGN,CLUSTER,WEIGHT,MEASUREMENTS,HOLDOUT}-UNSUPPORTED`, `E-STATS-{RESAMPLE,NULLTEST}-UNSUPPORTED`, `E-REPL-FOLD-STRATIFY-UNSUPPORTED` (14) | **Documented as a family.** § The one config file: "a config declaring either is refused today, naming the `-UNSUPPORTED` code its slice will retire". Only `resample`/`null_test` are named individually; the other twelve are covered by the general rule only |
| `E-SWEEP-BASELINE-PARTIAL` | **Rule inverted.** Read § Expansion modes 1415–1422 directly: a baseline fixing "a value on some axes" is specified as a *supported* design giving one baseline per cell, and the section says "prefer the second row whenever the levels are peers". That this build refuses it outright is documented nowhere — the strongest doc-vs-code divergence this measurement found |
| `E-SWEEP-KEY-UNKNOWN` | **Identifier unnamed.** Implied by ¶292's closed-schema claim; no row |
| `E-SWEEP-AXIS-EMPTY`, `E-SWEEP-EXPANDS-EMPTY` | **Rule undocumented.** Read § Expansion modes in full: it describes how each mode expands and never states that an axis with no values, or a sweep expanding to zero conditions, is refused |
| `E-STATS-CORRECTION-UNKNOWN` | **Identifier unnamed.** Enum documented (§ The one config file, `none \| bonferroni \| holm \| fdr_bh`); that an out-of-enum value is refused is not stated, though it follows from "Choices" (row 207) |
| `E-STATS-CONTRAST-SHAPE`, `E-STATS-CONTRAST-NESTED` | **Identifiers unnamed.** Rules documented — § Contrasts for `id`/`of`/`against`, and both `reference.md` and `design-principles.md` for "contrasts do not nest" |
| `E-REPL-ORDER` | **Identifier unnamed.** Enum documented (§ The one config file, `as_declared \| randomized`) |
| `E-REPL-N` | **Rule undocumented.** § Repeat kinds gives `seed`/`batch` the field `n` and never states a floor; the string "at least 1" appears in no document |
| `E-REPL-LEVEL-{DUPLICATE,DEPTH,BATCH-INNER}` | **Identifiers unnamed.** § Repeat kinds and § A `batch` says *when*, not *what* state all three rules (one level per kind, two deep, batch outermost) |
| `E-REPL-FOLD-K-TOO-LARGE` | **Rule undocumented.** § Repeat kinds documents `k` as "an integer ≥ 2, or `all`" — the `k` ≥ 2 half is row 269's rule, but `k` > roster size is stated nowhere; rows 267/268 cover only the cluster and cell variants |
| `E-REPL-SEED-COLLISION` | § Randomness. **The identifier is documented** — one of only eight `validate` codes that appear in the four documents |
| `E-UNITS-{SOURCE-MISSING,KEY-MISSING}` | **Identifiers unnamed.** § Where units come from documents `from` and `key` and what each must name |
| `E-UNITS-EMPTY` | **Rule undocumented.** That a roster resolving to zero units is refused is stated in no document |
| `E-HYPOTHESIS-{KIND,DIRECTION,THRESHOLD,EVALUATE-ON}` | § Pre-registration and § The one config file document the fields. `KIND`, `DIRECTION`, `EVALUATE-ON`, `THRESHOLD` all appear as identifiers in the documents. `direction` has **no named enum** anywhere in the four documents — `validate.py`'s own docstring says so, and this measurement confirms it |
| `E-HYPOTHESIS-{COMPARE-TO,CONDITION}` | § Pre-registration writes `to: baseline` and `compare.condition`; neither the closed-vocabulary rule for `to` nor the label-resolution rule for `condition` has a row |
| `E-TEMPLATE-RULE` | § Templates — a template's `validate` returns messages. Identifier undocumented |
| `E-ENTRYPOINT-{REQUIRED,IMPORT}` | ¶298 states the import rule in prose. `REQUIRED` is implied by § The one config file |
| `E-DATA-NOT-ABSOLUTE` | § The one config file requires absolute `input_dir`/`output_dir`. Identifier undocumented |

Three identifiers appear in `validate.py` **only inside docstrings** and are never emitted
there — `E-STATS-CONTRASTS-UNSUPPORTED` (retired), `E-GIT-NO-REPO` (compared against, raised by
`provenance`), and `W-STATS-STRATUM-THIN` (a cross-reference at line 1630, emitted by `cli.py`).
This is exactly the 9-vs-8 discrepancy in the warning counts below, and the same class of
artifact as the prior "18 warning codes" error.

## Question 1 — is `E-CONFIG-SHAPE`'s coverage a type envelope?

**No. It is a container-shape check, and the missing piece is a systematic schema, not a
handful of leaf guards.**

`_check_shape` checks exactly two things, both about *containers*:

1. Each top-level block is the right container kind — seven mappings (`metadata`, `data`,
   `parameters`, `sweep`, `replication`, `statistics`, `limits`), one list (`hypotheses`),
   five strings (`schema_version`, `experiment_type`, `template_version`, `entrypoint`,
   `plugin`).
2. Eight hand-enumerated nested containers a later check indexes into: `data.units`,
   `data.units.attributes`, `sweep.baseline`, `sweep.grid`, each `sweep.grid.<axis>`,
   `replication.repeats`, each `replication.repeats[i]`, `statistics.contrasts`,
   `statistics.report_by`.

It checks **zero scalar leaf types**. The only leaf-type authority in the codebase is
`Param.check`, driven by `parameter_spec`, and `parameter_spec` covers `parameters.*` and
nothing else. `limits` is emitted by `materialize.py` as a hardcoded string block
(`materialize.py:147–153`) with no spec object behind it, so there is no table to hang a
`limits.max_executions: int` assertion on.

Two probes, run against a scratch config outside the project:

- `metadata.name: [a, b]` → `validate_config` raises a bare **`TypeError: expected string or
  bytes-like object, got 'list'`** out of `re.match(template.naming_pattern, name)`. The known
  defect, reproduced.
- `limits.max_executions: "5"` with a 3-condition × 5-repeat design (15 executions) → **no
  finding at all.** `_check_sweep`'s `isinstance(budget, int)` guard silently skips
  `W-EXEC-BUDGET`. `limits.min_reported_n: "10"` behaves the same way in `_check_report_by`.

The silent-skip failure mode is worse than the crash and is not confined to one site: every
core scalar leaf is either read unguarded (crash) or read behind an `isinstance` guard that
turns a typo into a disabled check. Additionally, closure is absent outside `parameters.*` —
probed, a top-level `sweeep:`, a `metadata.athors:`, and a `limits.max_execution:` all
validate clean, which directly contradicts ¶292.

**Conclusion:** the fix is a declarative schema for the non-`parameters` config — a leaf-type
and closed-key table for `metadata`, `data` (including `data.units.*`), `replication`,
`statistics`, `limits`, `hypotheses[*]`, and the five top-level strings — plus wiring
`_check_shape` to walk it. That is a sub-slice-sized deliverable, not a task, and it is
strictly larger than the checks left in H1.

## Question 2 — MISSING split, buildable versus blocked

**Buildable now: 2.** Row 271 (baseline leaves contrasts confounded) and row 276 (contrast
stratum is populated, at `validate` against the roster). Row 271 additionally needs a `W-`
identifier minted in `reference.md` first.

**Blocked: 42**, owned as tabulated above — H3 Units 25, H7 Plugins 7, H2 Sweeps 6,
H4 Statistics 4. Every one is currently refused wholesale by an `-UNSUPPORTED` code, so no
config can reach the state the row describes; none of them is H1's work.

The 7 PARTIALs are all buildable now and all small, except that three of them (205 Types, 208
Unknown keys, and the narrowness noted on 232) are the type envelope by another name.

## Identifier counts

Pattern used, on the raw text of each file:

```
\b[EW]-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*\b
```

Word-boundary anchored at both ends, requiring a letter after the `E-`/`W-` and at least one
character per segment. Every resulting string was eyeballed; all are real identifiers, and the
docs↔src set-diff found **no** doc code absent from the source (which is what would have
surfaced a truncation artifact such as the prior `E-FAILED`).

Three different questions, three different numbers — the distinction matters, because
`validate.py` reaches roughly a third of its identifiers through loop tables and translated
`exc.code`, which an AST walk over literal first arguments misses:

| Question | `E-` | `W-` |
|---|---|---|
| (a) Distinct codes `src/**` emits — every identifier reachable as a value, including tuple-table and translated ones | **114** | **17** |
| (a′) Distinct codes whose literal *appears* anywhere in `src/**` (text count) | 115 | 17 |
| (b) Distinct codes `validate.py` emits as a value (literals + the three `(…, code, …)` loop tables) | **67** | **8** |
| (b′) Distinct codes `validate.py` **surfaces to a user** — (b) plus the 10 translated `REPL_DECLARATION_CODES` and the 6 `resolve_units` codes it converts under the callee's own identifier | **72** | **8** |
| (c) Distinct codes appearing anywhere in the four documents | **41** | **17** |

Notes on each number:

- **(a) 114 vs (a′) 115.** The single-code gap is `E-STATS-CONTRASTS-UNSUPPORTED`, retired when
  `_check_contrasts` replaced the wholesale refusal and now surviving only in a `validate.py`
  docstring. Every other identifier in the text count is reachable. This number was measured by
  walking every non-docstring `ast.Constant` in `src/**`, not just first-argument literals — a
  first-argument-only walk reports 103, missing the 11 `-UNSUPPORTED` codes that live as tuple
  elements and reach `c.error` through a loop variable.
- **(b) 67 vs (b′) 72.** The five-code difference is the callee-translation path. The number a
  scoping estimate needs is **72**.
- **`W-` in `validate.py` is 8, not 9.** The ninth literal, `W-STATS-STRATUM-THIN`, appears only
  in `_check_report_by`'s docstring at line 1630, cross-referencing the run-time warning. Stated
  explicitly here given the prior 18-vs-17 miscount in this project.
- **(c) 41 `E-` codes in the documents, of which only 8 are ones `validate` surfaces**:
  `E-PARAM-UNKNOWN`, `E-REPL-SEED-COLLISION`, and the six
  `E-HYPOTHESIS-{DIRECTION,EVALUATE-ON,FORM,KIND,METRIC,THRESHOLD}`. The remaining 33 documented
  `E-` codes are `E-STEP-*`, `E-ARTIFACT-*`, `E-RUN-*`, `E-IO-FAILED`, `E-UNIT-IMMUTABLE`,
  `E-REPL-ORDER-UNRESOLVED` — run-time contracts. **64 of `validate`'s 72 identifiers are named
  in no document.** All 17 documented `W-` codes exist in the source, and no document names a
  code the source lacks.

## What could not be classified, and what would settle it

No row was left UNCLASSIFIABLE. Two are ambiguous in *owner* but not in verdict:

- **Row 247** ("Stratification attribute exists") does not say which `stratify_by` it means —
  `fold`, `assign`, or `resample`. All three are refused today, so the row is blocked either
  way; naming the field in `reference.md` would settle which of H3/H4 owns it.
- **Row 229** ("Clusters enough to resample") needs both `statistics.resample` (H4) and
  `cluster_by` (H3). H4 is the natural owner since the threshold is `limits.min_clusters` and
  the subject is the resample; H3 must land first regardless.

One doc-defect question to settle in `reference.md`, not by more reading: **row 276** is
classified MISSING because `W-STATS-CONTRAST-THIN` exists and fires — just at `run`, over
`n_paired`, not at `validate` over the roster. ¶296 explicitly splits `report_by`'s thinness
into a validate-time code and a run-time code; `within` has only one. Either § Validation's row
276 should move to the run-time list, or a second identifier is owed. Whichever way it goes,
H1's buildable-now count is 2 or 1 and the slice verdict is unchanged.

## Judgement

**H1 is one slice. Build the envelope first.**

Of the 87 main-table rows, 36 are already implemented, 42 belong to H2/H3/H4/H7 and are
unreachable today, 7 are narrow-but-working, and 2 are genuinely absent. The spine's
"~85-check engine" should read **~45**: the other 42 rows are each owning slice's own work,
inseparable from un-refusing the block they describe.

H1's remaining content is: the type-and-key envelope (Q1 — a declarative leaf-type and
closed-key schema for every non-`parameters` block, the single largest item and the only one
that is a new subsystem), 7 PARTIAL corrections, 2 new checks, 6 `W-` identifiers to mint in
`reference.md` first, plus the diagnostic-ordering and import-path items the spine already
names. Splitting that gives one slice holding the envelope and one holding a nine-item task
list — and the spine's own rule is that "a slice minted to hold exactly one ledger entry is a
description wearing a name." Three of the seven PARTIALs (205, 208, and 232's narrowness) are
the envelope by another name, so they fold into it rather than into a second slice.

Two side findings for the spine's ledger, both suggesting a small correction to the table
rather than to H1's size: H2's line item "wiring `check_swept_value` into `validate`'s call
path" is already done (`validate.py:909`), and H1 should absorb the six unnamed warning
identifiers as a documentation prerequisite before any of them can be implemented.
