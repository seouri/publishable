# H8 scoping — studies and reporting

**Measured on 2026-08-20 against commit `a3461511a99147cefc732b5cfb8e34c006a6191a`** (`main` at HEAD,
clean tree). **Read-only**: nothing under `src/`, `tests/`, `docs/reference.md`, `README.md`,
`docs/design-principles.md`, `docs/experimental-designs.md` or
`docs/feasibility-llm-growth-studies.md` was edited by this pass; every config, roster and run
directory built for it lives under the session scratchpad. This document is the whole deliverable.

The charter is one row in `docs/superpowers/specs/2026-08-08-implementation-spine-design.md`
§ The hardening slices: **`study new`/`add`, `report`, `diff`, `freeze`, lineage and upstream
chains**, ordered *after H4*. H4 is complete (H4a–H4d) and so is H7 (H7a, H7b A/B, H7c, H7d A/B).

Follows `H7d-SCOPING.md`'s shape, including its habit of saying how each claim was measured, and
including that it carries a correction because one of its own claims was falsified within hours.

---

## 0. Executive summary

1. **The charter's five names are 30 tasks, not five rows, and H8 must split three ways.**
   H8a lineage · 10 · H8b `diff` + `freeze` · 8 · H8c `report` + `study` · 12. The seam is
   *step-facing lineage* against *CLI reporting*, and H8a ships first.
2. **H8a is the largest single count-mover left in the project.** `io.reuse_from` and
   `provenance.upstream` are H8's charter half of "lineage and upstream chains", they are the
   **sole named remaining core-side blocker for six of the nine** configs in the feasibility
   analysis, and `grep -rn "reuse_from" src/publishable/` returns **0 lines** at this commit.
3. **The record's "six with no remaining core-side blocker" does not survive.** The phrase is
   applied in two contradictory directions inside one table: E3/E4/E6 are counted *blocked* on
   `io.reuse_from` while C1/C2/C3 are counted *unblocked* with the identical single dependency
   named in the same cell. Under the standard H7b Part B set, the honest figure is **three, not
   six**, and it is the same three as the executable count.
4. **Zero `E-` codes exist in H8's family** — no `E-STUDY-*`, `E-REPORT-*`, `E-DIFF-*`,
   `E-FREEZE-*`, `E-UPSTREAM-*` or `E-LINEAGE-*` anywhere in the four documents, `src/` or
   `tests/` — while the specification already requires at least six distinct refusals. This is
   H4d's "one code for five faults" shape, in advance.
5. **Nothing in `src/` reads a `run.yaml`.** `report`, `diff`, `study add` and `freeze` all take
   one, and the reader they share does not exist.
6. **`freeze` cannot get a `cfg` from the run directory it is given**, measured: a run directory
   holds no copy of the config until `run.yaml` is written at the end, and `freeze` exists for
   runs in progress. The same hole is `resume`'s (H9's) and the document asserts the opposite.
7. **`diff`'s exit code is specified two contradictory ways** across three documents. Not resolved
   here; enumerated as a decision H8b's design owes.
8. **No part of H8 can stop or alter a run** — `freeze`'s single write is one appended ledger line,
   and `append_observation` is a module-level function callable from outside `command_run`
   (measured by calling it). H7d Part B's boundary holds.

---

## 1. Method

- Every command was **invoked**, not read: exit codes captured without a pipe.
- A **real end-to-end `run`** was performed against a scaffolded project and a 24-unit synthetic
  roster, and its run directory and `run.yaml` inspected key by key. That is the fixture item 7 is
  answered from.
- The nine feasibility configs' `data`/`statistics` blocks were extracted from
  `docs/feasibility-llm-growth-studies.md` by parsing its fenced YAML, transplanted onto a
  scaffolded `generic` config over a **240-row** synthetic roster carrying every attribute any of
  the nine names, and run through `validate_config` — the same method § Executability on this build
  uses — with a **can-fail control**.
- One **mutation**: `append_observation(phase="BOGUS_FIFTH_SPELLING")`, to test whether the closed
  phase vocabulary its docstring names is enforced.
- Where a claim rests on **reading**, it says so.
- Gates at this commit: `uv run pytest` → **2456 passed, 1 skipped, 2 xfailed** (run directly).

---

## 2. What the specification requires — enumerated by reading, then confirmed by grep

Read first: `reference.md` § Studies: what a paper reports (and § Why not in the repo, § Building
one, § What `study add` redacts), § Lineage between runs (and § `reuse_from` addresses an artifact,
not the design that produced it), § CLI reference (§ Creation commands, § Operation commands,
§ Exit codes and diagnostics, § Draft runs), § Generators (and § A report override renders one
experiment's own figures), § The importable surface, § The two files, § The other files a run
writes, § The apparatus core can only observe, § Reproducing on another device, § Package layout,
§ Validation; `README.md` step 6 and § The loop you'll actually live in; `design-principles.md`
§ Same code, different parameters and § Everything is in the file;
`experimental-designs.md` § What core will not do for you. Then grepped.

| Specified | State at this commit | How measured |
|---|---|---|
| `publishable study new <bundle> --title` | **absent** | invoked → *specified but not built*, exit 2 |
| `publishable study add <bundle> <run.yaml> --as <name>` | **absent** | invoked → same, exit 2 |
| `publishable report <run.yaml \| study.yaml>` | **absent** | invoked → same, exit 2 |
| `publishable diff <two paths>` | **absent** | invoked → same, exit 2 |
| `publishable freeze <run dir>` | **absent** | invoked → same, exit 2 |
| Bare `publishable study` (no subcommand) | **absent, and routed** | invoked → *specified but not built … § Creation commands*, exit 2, via `cli.py`'s `any(n.startswith(f"{command} "))` arm |
| `study.yaml`: `title`, `authors`, `code.{remote,commit}`, `runs.<name>.{file,run_id}` | **absent** | no `study.py`; `ls src/publishable/` |
| `code.commit` = the run added `--as main`, else the first added | **absent** | same |
| `study add` refuses a name already in the bundle | **absent, and no code minted** | grep for `E-STUDY` over `docs/*.md`, `src/`, `tests/` → 0 |
| `study add` prints a notice when a run's commit ≠ `code.commit` | **absent** | same |
| `study add` redacts `data.input_dir`, `data.output_dir`, `provenance.git.repo_root`, `provenance.environment.hostname`, `provenance.input_manifest`, each replaced by a marker distinguishing *redacted* from *never captured* | **absent** — and two of the five **are never written today** | run.yaml inspection: `provenance.environment` = `{manager, python_version, uv_lock, uv_lock_hash}`; no `hostname` (H6's) |
| `study add` prompts on any reported metric below `limits.min_reported_n`, over three shapes (`basis: units` `n.completed`, `basis: repeats` repeat count, a reported `Estimate`'s declared `n`) and lists an `Estimate` with no `n` | **absent**; the *validate*-side halves ship (`W-STATS-CONTRAST-THIN`, `W-STATS-REPORTBY-THIN`, `W-STATS-STRATUM-THIN`, `W-STEP-ESTIMATE-N`) | grep `min_reported_n` over `docs/reference.md`, `src/` |
| Whether a bundle may ever carry `allocation.json` — **left open in writing** for "whichever slice builds `study.py`" | **open** | § What `study add` redacts, last paragraph |
| `report` renders Markdown/HTML from one run **or** a whole study | **absent** | invoked |
| `report`'s standard sections: condition table, deltas, hypothesis verdicts, attrition | **absent** | § A report override |
| `report study.yaml` cross-checks that runs claiming the same code share a `code_hash`, **and the same for `provenance.apparatus.hash`**, flags draft runs, collects every hypothesis into one table | **absent**; both inputs exist (`code_hash` in `run.yaml`; `apparatus.hash` assembled by `apparatus.apparatus_hash`) | run.yaml inspection; `grep -n apparatus_hash src/publishable/apparatus.py` |
| `report` of a `partial` run **exits 0** | **absent, and it is the one exit code § Exit codes disambiguates for `report`** | § Exit codes and diagnostics |
| `report` refuses to render a **draft** as a final result | **absent** | § Draft runs |
| `BaseReport`, `sections(self, run, io)` a generator, `format` written by the generator | **absent** | not in `publishable.__all__` (measured: 15 names, no `BaseReport`); § The importable surface row still `not yet built` |
| Override discovery of `src/<pkg>/report.py` | **absent** | no `report.py` under `src/publishable/` |
| `generate report <exp> --format html\|markdown` | **absent** | `NOT_BUILT_GENERATORS`; `publishable g report` → not built |
| `diff` prints each hash identical/differing, then the specific parameter deltas | **absent** | invoked |
| `diff`'s row set and order — `code_hash`, `input_manifest`, `uv.lock`, [`apparatus`], `parameters_hash` — with the row **labels** as shown (`input_manifest`, not `input_manifest_hash`) | **absent** | three worked outputs: `reference.md` § The apparatus core can only observe, `design-principles.md` § Same code different parameters, `README.md` § The loop. All three agree on set and order |
| `diff`'s `apparatus DIFFERS` row with per-fact `old → new` lines | **absent** | invoked; and `H7-SCOPING.md` § 4's routing table routes the row here |
| `diff` labels a draft run | **absent** | § Draft runs |
| `diff` "can tell you two runs differ only because their upstreams did" | **absent, and doubly so** — needs both `diff` and `provenance.upstream` | § Lineage between runs |
| `diff` takes **two config or run paths** (so a config-vs-run mix is admitted by the wording) | **absent, and unspecified** | § Operation commands |
| `freeze` re-reads the environment and re-probes the apparatus mid-run, executing nothing | **absent** | invoked |
| `freeze` reports a moved apparatus as a **failure**, does not decide, does not change a run's status | **absent** | § Operation commands, the `freeze` paragraph |
| `freeze` appends one ledger line and that is the **only** thing it writes | **absent; the append primitive ships** | `apparatus.append_observation(run_dir, *, phase, condition, probe, facts)`, module-level, called successfully from outside `command_run` |
| `freeze` is the one command safe to point at a run **holding its own lock** | **absent**; `RunLock` ships in `run_identity.py` | grep `class RunLock` |
| `phase="freeze"` as one of a closed vocabulary of four | **the name exists; the closure does not** | mutation: `append_observation(phase="BOGUS_FIFTH_SPELLING")` wrote that string verbatim to `probes.jsonl` |
| A ledger **reader** — `freeze` must compare against the first *answered* observation, which lives on disk in another process's run | **absent** | grep `probes.jsonl` in `src/`: one write site (`append_observation`), one string in `Observer.block()`, **no read**. `Observations` is in-memory, built during a run |
| `io.reuse_from(run_id, step, name)` | **absent** | `grep -rn "reuse_from" src/publishable/` → **0** |
| The `run_id` → path rule: `<output_dir>/<run_id>/`, or an absolute run-directory path whose `run_id` is **read back from that run.yaml** | **absent, and the inputs are not on `io`** | `ArtifactIO.__init__` takes `step_dir`, `input_dir`, `run_dir`, … and **no `output_dir`**; `_step_scopes` is *this* run's map |
| `provenance.upstream`: per upstream `run_id`, `code_hash`, `parameters_hash`, `used: [...]` | **absent — and the key is not written at all** | real run's `run.yaml`: `provenance` = `git, environment, apparatus, input_manifest, input_manifest_hash, input_manifest_changed, publishable_version, plugin_versions, units, units_hash, allocation, allocation_hash`. `"upstream" in provenance` → **False**. Unlike `apparatus`/`allocation`, which are written `None` |
| "Lineage is recorded, not resolved" — an unreachable ancestor is reported, never recomputed | **absent** | § Lineage between runs |
| `reuse_from` has **no** condition or repeat selector, by design | **absent** | § `reuse_from` addresses an artifact |
| `lineage.py` — "upstream run recording and chain verification — not yet built" | **absent** | `ls src/publishable/` |
| `study.py` — "study new/add: bundle assembly, redaction, cross-run report — not yet built" | **absent** | same |
| `report.py` — "BaseReport: standard sections, html/markdown, override discovery — not yet built" | **absent** | same |
| A module for `diff` | **not specified at all** — § Package layout names none | grep the tree block: `lineage.py`, `study.py`, `report.py`, `reproduce.py`, `docs.py` carry markers; no `diff` and no `freeze` |
| A module for `freeze` | **not specified at all** | same |
| A `run.yaml` **reader** | **absent** | `run_record.py`'s own first line: "Assemble run.yaml. Assembles only — computes nothing." `envelope.load_document` reads a *config*. No reader anywhere in `src/` |
| Any `E-` code in the family | **none exist** | `grep -n "E-STUDY\|E-REPORT\|E-DIFF\|E-FREEZE\|E-UPSTREAM\|E-LINEAGE" docs/*.md src/publishable/*.py` → 0 lines |

**Not H8's, named so it is not folded in.** `apparatus.expected.json` is written by **`reproduce`**
(`reference.md` § Reproducing on another device, step 5), and `H7-SCOPING.md` § 10, *What is NOT in H7*, routes it to
**H9**. See § 7.

---

## 3. `provenance.upstream` is absent, not null — and no document says what a run without one writes

Measured on a real completed run (24 units, `generic`, one condition, five `seed` repeats):

```
provenance keys: git, environment, apparatus, input_manifest, input_manifest_hash,
                 input_manifest_changed, publishable_version, plugin_versions,
                 units, units_hash, allocation, allocation_hash
'upstream' in provenance -> False
apparatus  -> None
allocation -> None
```

`apparatus`, `allocation` and `allocation_hash` are written `None` when the feature did not apply.
`upstream` is not written at all. `reference.md` § The two files' `run.yaml` example shows
`provenance.upstream` **populated with one entry** and says nothing about the no-upstream case — so
H8a inherits a decision with a two-way precedent inside the same block (`apparatus: null` /
`allocation: null` say *the feature did not apply*; `repeat_spread` is **omitted rather than
zeroed** where the figure would mislead, and § The two files argues that case explicitly). The
`spec-defects.md` entry *"Six `provenance` and `results` keys in the `run.yaml` example that no code
writes"* routes this key to H8 by feature and its claim is **still true at this commit** — verified
by the run above, not by re-reading the entry.

---

## 4. The `freeze` hole: a run directory carries no config

`reference.md` § Operation commands says `freeze` takes a **run directory** and re-probes the
apparatus. A probe is `probe(cfg) -> Apparatus` — it needs a config. Measured, on the real run
directory above:

```
run_<id>/
├── environment/pyproject.toml     # (uv.lock too, when there is one)
├── executions.jsonl
├── manifest/input.json
├── run.yaml                       # written ONCE, AT THE END
├── seed30/…  seed40/…  …
└── sweep.yaml                     # design_digest, conditions, repeats, labels,
                                   #   order, execution_order — and NO config
```

`sweep.yaml`'s six top-level keys were read programmatically; none is the config. `environment/`
holds `pyproject.toml` only. So **the config a run used is reachable from its run directory only
through `run.yaml`**, which § The two files states is "written once at the end of a run" — and
`freeze` exists precisely for a run that has not ended. On a run in progress there is nothing for
`freeze` to build a `cfg` from.

**The same hole is `resume`'s, and the document asserts the opposite of what is on disk.**
§ CLI reference: *"`resume` takes a run directory rather than a config path: resuming operates on a
run that already exists, and that run directory already contains the config it used."* Measured: it
does not, until the run ends — and § Resuming has `resume` **refuse** a run that already holds a
`run.yaml`, so every run `resume` exists for is one whose directory has no config in it. That half
is **H9's**; H8b inherits the identical problem and cannot wait for H9, because `freeze` is ordered
first. Three candidate resolutions, none picked here: write the embedded config into the run
directory at run start (a new artifact, and a change to § The other files a run writes); have
`freeze` take a config path (a change to § Operation commands and to the argument that a run
directory is one thing rather than two); or have `freeze` reconstruct `cfg` from `sweep.yaml` plus
something, which on inspection there is not enough there to do.

---

## 5. What `report` and `diff` can be tested against, and what they cannot

Both read artifacts that already ship, which is the good news and the whole cost argument.

| Surface | Testable from | Needs a real `run`? |
|---|---|---|
| `diff` — the five rows, the parameter deltas | **two fixture `run.yaml` files**, hand-written or produced once and committed | No |
| `diff`'s `apparatus DIFFERS` row | a fixture pair whose `provenance.apparatus.facts` differ; H7d's `Observer` can produce a real one | No |
| `diff` labelling a **draft** | a fixture with `draft: true` — the key is written today (measured: `draft: false` present) | No, but `draft` itself is **H9's**, so a *genuine* draft run cannot be produced |
| `report` of one run: condition table, deltas, hypothesis verdicts, attrition | a fixture `run.yaml`; a real run gives a richer one cheaply (the run above took under a second) | No |
| `report` of a `partial` run exiting 0 | a fixture with `status: partial` | No |
| `report study.yaml` cross-checks | a bundle of two fixture records, one pair sharing `code_hash` and one not | No |
| `study add` redaction | a fixture record — but **two of the five redacted fields are never written** (`provenance.environment.hostname`, and `provenance.git.repo_root` is written), so the redaction of `hostname` is untestable against real output until H6 lands. Test the marker rule over a synthesized record and **say so** | No |
| `study add`'s `min_reported_n` prompt | needs a record carrying all three metric shapes — `basis: units`, `basis: repeats`, and a reported `Estimate` with and without `n`. All three are producible today | One run, to get a real `Estimate` |
| `freeze` | **a run holding its own lock** — i.e. a second process mid-run, plus an installed probe plugin | **Yes**, and it is the only H8 surface that does |

**The asymmetry is the risk.** Everything in `report` and `diff` is a pure function of files that
already exist, so the trap is not reachability — it is the trap `CLAUDE.md` § Writing checks that
can fail names: *a fixture whose numbers agree with the bug*, and *a fixture with too few elements
to distinguish the candidate orderings*. `diff` has **five rows in a fixed order** and three worked
outputs in three documents; a two-row fixture cannot tell row order from dict order. Size the
fixture to five rows with all five distinguishable, and pin the labels (`input_manifest`, not
`input_manifest_hash`; `uv.lock`, not `uv_lock_hash`) against the documents' text rather than
against the implementation's own constant.

**Can any part of H8 stop or alter a run?** No, and it is worth stating with the same care H7d
Part B used. `freeze`'s only write is one appended ledger line, and the primitive is reachable:
`append_observation` is a module-level function in `apparatus.py` that takes a `run_dir` and was
called successfully from a throwaway directory in this pass. It takes no lock, and § Operation
commands is explicit that `freeze` "has no execution to fail and no business changing a run's
status" — the next execution's gate, built by H7d Part B, is what stops the run. `report`, `diff`,
`study new` and `study add` write nothing into a run directory at all. **The one thing to watch is
`freeze`'s probe: it spends quota against somebody else's meter**, on a run already spending it, so
its per-invocation cost is one probe per condition and that count belongs in its design.

---

## 6. What H8 unblocks — measured, and the record's own count does not survive

### 6.1 The measurement

Every one of the nine configs' `data`/`statistics` blocks was extracted from the analysis, given the
**table-roster substitution** (`from: index.csv` over a 240-row synthetic index carrying `truth`,
`sex`, `age_band`, `visit_density`, `span_days`, `dx_family`, `record_source`, `consensus_label`,
`count_stratum`, `sampling_weight`, `split`), and run through `validate_config`:

| Config | Errors | Warnings |
|---|---|---|
| E1, E2, E4, E5, E6 | *(none)* | `W-DATA-CLUSTER-UNDECLARED` |
| C1, C2, C3 | *(none)* | `W-DATA-CLUSTER-UNDECLARED` |
| **E1 with `holdout.frac: 0` (can-fail control)** | **`E-DATA-HOLDOUT-FRAC`** | `W-DATA-CLUSTER-UNDECLARED` |

`W-DATA-CLUSTER-UNDECLARED` on `age_band` is an artifact of the synthetic roster's three-band shape,
excluded for the reason every prior entry excludes it. **E3 was not transplanted**: it shows only
the blocks that differ from E1 and its section carries no `data`/`statistics` YAML, so the extractor
found none — said rather than filled in. **Narrowings**, in the same direction every prior entry
narrowed: `entrypoint`/`experiment_type` are the scaffolded `generic` demo, `sweep`/`parameters`/
`replication`/`hypotheses` were not carried over, and C2/C3's declared contrast sets were replaced
by one stand-in entry over the demo's `analysis.method` axis with a `baseline` + two-level `grid`
added so a comparison exists to resolve.

**No `E-` code in H8's family appears, and none can**: § 2 measured that the family is empty. **H8
builds nothing that runs at `validate`.** So the validate-time picture is unchanged, exactly as
expected, and the interesting number is elsewhere.

### 6.2 The record's "six with no remaining core-side blocker" does not survive

`CLAUDE.md` and the last five § Executability entries carry **six with no remaining core-side
blocker, three executable**. Read directly (not from the summary), the standard was set by the
2026-08-17 H7b Part B entry: a clean `validate` **plus** a read of the design's prose for other
unbuilt core-side dependencies. Under it, E3/E4/E6 were counted **blocked**, on `io.reuse_from`
alone.

H4b-1's entry then took the count 3 → 6 by admitting C1/C2/C3 — whose own row in that entry's table
reads *"No — blocked on `io.reuse_from`"*. Two entries later the same table renders it in one cell:

> `| C1 | *(none)* | No — blocked on io.reuse_from (no remaining core-side blocker either, per H4b-1) |`

**The identical dependency excludes three configs from the set and admits three others.** It is not
a wording slip: H4b-1's own prose states that C1–C3 additionally fail the standard's second clause
— *"'every field they declare is honoured' … is true of their `data.units` and `statistics.resample`
blocks and not of their `statistics.report_by`"* — and then increments the count anyway.

Both premises re-measured at this commit rather than carried:

- `grep -rn "reuse_from" src/publishable/` → **0 lines**.
- The `report_by`-under-`resample` gap is **live**: `cli.py`'s `report_by` level call
  (`level_summary = summarize_step(...)`, the one at the end of the `_condition_report_by_levels`
  loop) passes `derived`, `seed`, `resample`, `draws`, `beside_n`, `weights`, `clusters`, `strata`
  — and **no `resample_columns`**, read at the call site. Owner: H4 Statistics, filed.
- C1–C3's `io.reuse_from` dependency, which the 2026-08-16 entry left *"not settled"*, **is settled
  by the analysis's own prose**: § Shortcut: three runs — *"The confirmation run reads the fitted
  artifact with `io.reuse_from`, and core records the upstream run's ID and both its hashes in
  `provenance.upstream`"* — and § Executability's own preamble names all six: *"`io.reuse_from`,
  which E3, E4, and E6 use to read their frozen compiled program, E6's swept `program_id` resolves
  through, and the shortcut's confirmation run uses to read its fine-tuned artifact."*

**Six is not the answer to any consistent question, and that is the sharpest form of this
finding.** Two readings are internally consistent, and neither gives six:

| Reading | Figure |
|---|---|
| **Strict** — clean `validate` **plus** a prose read for other unbuilt core-side dependencies (H7b Part B's own standard) | **3** — E1, E2, E5 |
| **Loose** — no validate-time refusal remains | **9** — every transplanted config reported zero errors in § 6.1 |
| What the record carries | **6** |

So the escape hatch — "H4b-1 just meant the loose thing" — is closed: the loose reading gives nine,
not six. **The honest figure entering H8 under the standard the record itself set is three with no
remaining core-side blocker — E1, E2, E5 — the same three as the executable count**, and
`io.reuse_from` is the sole named remaining core-side blocker for the other **six**.

### 6.3 What H8 moves

The "after" column is a **projection, and it is labelled as one** — the fault § 6.2 documents is
exactly a projected figure printed as a measured one, so the warrant travels in the cell:

| | Before H8 (corrected, measured) | After H8a (projected) | After all of H8 (projected) |
|---|---|---|---|
| No remaining core-side blocker | **3 confirmed** (E1, E2, E5) | **6 — 3 confirmed, +3 pending the prose read H8a's design owes for E3, E4, E6** | same |
| Executable | **3 confirmed** | **6 — same qualification** | same |
| Blocked, and on what | E3/E4/E6 + C1/C2/C3 on `io.reuse_from`; C1–C3 also on `report_by`-under-`resample` (H4) | C1/C2/C3 on `report_by`-under-`resample` (H4) | same |

Both standing qualifications stay attached and neither is H8's to retire: **the `growth_screen` /
`growth_shortcut` plugin must be written and installed**, and a declared apparatus probe needs a
real plugin behind it. And the honest sentence about `study` itself: **`study` is what the paper
needs and no config's validation depends on it.** § Three repositories names the roster-variant runs
that exist *only* to be compared in a study, and § What core refuses routes the class-ratio axis to
"separate runs joined in a `study`" — a *design* needing a study is not a *config* failing to
validate, and H8c's `study` therefore unblocks **zero** configs while completing designs that are
otherwise expressible today. H8a is where the count moves.

---

## 7. Ownership — where the boundary runs

### Routed **to H8 by name** by an earlier document, and still H8's

| Routed here | By | Still H8's? |
|---|---|---|
| `freeze`'s re-probe | `H7-SCOPING.md` § 4 and § 10; both apparatus designs' § Out of scope | **Yes** |
| `diff`'s `apparatus DIFFERS` row | same | **Yes** |
| `report study.yaml` cross-checking `provenance.apparatus.hash` | apparatus Part A/B designs | **Yes** |
| `study add`'s redaction ("nothing to redact from `provenance.apparatus`, by design") | `H7-SCOPING.md` § 10 | **Yes**, and the by-design half is worth keeping: § The apparatus core can only observe makes a probe emit non-identifying facts precisely so that this table has no apparatus row |
| `provenance.upstream` (one of the "six unwritten `run.yaml` keys") | `spec-defects.md`, routed by feature | **Yes**, claim re-verified in § 3 |
| `BaseReport`'s **behaviour** | `H7a`/`H7b`/`H7b-2`-SCOPING, `spec-defects.md` | **Yes — and its *export* is H8's too now.** See below |
| `phase="freeze"` in `append_observation`'s vocabulary | apparatus Part A plan and design | **Yes**, and the docstring's claim that the closure prevents a fifth spelling is false (§ 8) |

### `BaseReport`: the filing's owner note does not hold

`spec-defects.md`'s entry, **corrected on 2026-08-20 at `993aeec` — a day old** — re-owners
`BaseReport` to *unassigned* with the note: *"H8 covers `freeze`/`diff`/`report`'s command shape
rather than a subclassable report class."* Three measured sites contradict it:

1. § Package layout: `report.py  # BaseReport: standard sections, html/markdown, override discovery`
   — the module `report` needs **is** `BaseReport`.
2. § A report override: `yield from super().sections(run, io)  # the standard blocks, in order` —
   `report`'s standard sections *are* `BaseReport.sections`. A `report` that renders the standard
   blocks without `BaseReport` would be a second implementation of them.
3. § The importable surface lists `BaseReport` with `sections(self, run, io)` in its "what core
   provides" table, and argues `format`'s absence from that column from `generate report`'s
   behaviour.

**`BaseReport` is H8's**, and the filing's suggested check ("whether `register_writer` already
covers the need") is answerable now: it does not — `register_writer` claims an artifact **suffix**
for `io.write`, and `BaseReport` is a renderer override discovered from `src/<pkg>/report.py`. Two
different mechanisms.

**And `generate report` is in nobody's charter.** It is in `NOT_BUILT_GENERATORS`, § Generators
marks it NOT BUILT, and it is not in H9's list. It writes the class `BaseReport` exists to be
subclassed from, so **H8c should claim it** — the alternative is a base class with no writer. If a
later reader would rather it went elsewhere, H8c drops to 11 and the total to 29.

### H9's, and precisely where the boundary runs

H9 owns `reproduce`, `dry-run`, `draft`, `resume`, `demo`, `docs`. Three places the boundary is
sharper than it looks:

- **`apparatus.expected.json` is H9's, not H8's.** `reference.md` § Reproducing on another device
  step 5 makes `reproduce` write it, and `H7-SCOPING.md` § 10, *What is NOT in H7*, routes it to
  **H9**. Nothing routes it to H8. (Restated because the brief this scoping answers asserts otherwise; see § 8.)
- **`diff` and `report` need nothing H9 builds** — both are pure readers of `run.yaml` and of the
  run directory. The two exceptions are *labels*: `diff` labels a draft and `report` refuses one,
  and `draft` is H9's. Both are testable today from a `draft: true` fixture (the key is written),
  so H8 can build and pin the behaviour and H9 makes it reachable. Say so in the design rather than
  discovering it: this is the *"an unbuilt reader of a shipped surface is a defect; of an unbuilt
  surface is specification"* line, and `draft: true` is shipped.
- **`freeze` and `resume` share the missing-config hole of § 4, and `freeze` comes first.** H8b
  therefore either resolves it or hands H9 a resolution. It should not be resolved *silently* by
  widening what a run writes — `CLAUDE.md` § Misreadings, on H7d Part B: *a document may not be made
  self-consistent by widening a behaviour change.*

### How the filings above were found

Not by `grep H8`, which would miss any entry naming a surface without naming an owner. The sweep was
`grep -in "publishable diff\|publishable report\|publishable freeze\|study\.yaml\|study add\|study new\|BaseReport\|upstream\|lineage\|reuse_from" docs/superpowers/spec-defects.md` — over the
**file**, never over a filtered output, per § Two mechanical traps. It surfaced nothing H8 owns
beyond the four entries above, and two things worth carrying rather than re-finding:

- **`io.read_upstream`'s bare `KeyError` for a suffix with a writer and no reader is CLOSED** (H7b
  Part A task 15): `StepIO._read` raises `ArtifactError` · `E-ARTIFACT-UNREADABLE`. `io.reuse_from`
  goes through the same `_read`, so **H8a inherits a coded refusal for an unregistered suffix** and
  should not mint a second one.
- Two older `read_upstream` scope filings (the `run`-scope-only reach, and a `summary` step reading
  a `repeat`-scoped step) are both **resolved**, by S3b and by the `E-STEP-READ-AMBIGUOUS` refusal.
  They are the nearest precedent for H8a task 9 and are not open work.

### Not H8's, named so it is not folded in

`io.reuse_from`'s **request for an owner** is answered here rather than asserted. The charter says
"lineage and upstream chains"; § Package layout glosses `lineage.py` as "upstream run **recording**
and chain **verification**" — the recording side, not the `io` method, which lives in `artifacts.py`,
a module that already ships. So the charter maps cleanly onto `lineage.py` and only arguably onto
`io.reuse_from`. **This scoping charters `io.reuse_from` into H8a**, on the grounds that
`provenance.upstream` cannot be recorded without the call that triggers it and no other remaining
slice claims either half; the 10-task H8a count includes it. If a later reader would rather it went
elsewhere, H8a drops to about 6 and **loses the entire count movement in § 6.3** — which is the
argument for keeping it. The `spec-defects.md` entry's **owner request** ("the next slice to touch
step-level artifact consumption should claim it, or the spine design should assign it explicitly
rather than leaving it to be rediscovered a third time") is what this paragraph answers.

Also not H8's: `report_by` under `resample` (**H4 Statistics**, filed, live on C1–C3);
`provenance.environment.os`/`.hostname`/`.hardware` (**H6**, and `study add`'s redaction table names
`hostname` — H8c redacts a field H6 writes, so H8c's redaction of it is testable only against a
synthesized record until then); `max_failed_fraction`'s truncation status (**unassigned**, filed by
H7d Part B, and it is a `run` semantics question that no H8 command can reach);
`BaseTemplate.field_convention` (**unassigned**, still the shape's live example).

---

## 8. What did not survive

| Claim, and where | Verdict |
|---|---|
| **The charter's five names as a five-row row** (spine design § The hardening slices) | **Undercounted, the same direction as every charter before it.** 30 tasks, three sub-slices. It names neither the `run.yaml` reader nothing in `src/` has, nor the ledger reader `freeze` needs, nor a single `E-` code, nor `BaseReport`, nor `generate report`, nor the document rows |
| *"H8 covers `freeze`/`diff`/`report`'s **command shape** rather than a subclassable report class"* (`spec-defects.md`, corrected 2026-08-20 at `993aeec`, one day old) | **False.** § Package layout, § A report override and § The importable surface all make `report`'s standard sections `BaseReport.sections`. `BaseReport` is H8's (§ 7) |
| *"H8 covers … `freeze`'s `apparatus.expected.json`"* (the brief this scoping answers) | **False.** That file is `reproduce`'s (§ Reproducing on another device, step 5) and `H7-SCOPING.md` § 10, *What is NOT in H7*, routes it to **H9**. `freeze` writes one ledger line and nothing else |
| **"Six with no remaining core-side blocker"** (`CLAUDE.md`; § Executability's last five entries) | **Does not survive as stated.** The phrase is applied in two contradictory directions in one table (§ 6.2), and **six answers no consistent question**: the strict reading the record itself set gives **3** (E1, E2, E5, the same three as the executable count) and the loose one — no validate-time refusal remains — gives **9**, since all eight transplanted configs reported zero errors in § 6.1 |
| *"Whether C1–C3 carry that same `io.reuse_from` dependency is not settled"* (§ Executability, 2026-08-16) | **Settled, in the affirmative, from the analysis's own prose** — § Shortcut: three runs and § Executability's preamble, neither of which needed a fresh measurement (§ 6.2) |
| *"`io.reuse_from` is unbuilt and **unowned**"* (`spec-defects.md`, re-confirmed 2026-08-17) | **The unbuilt half survives** (0 grep hits at this commit). **The unowned half is closed here**: chartered into H8a, with the fallback stated (§ 7) |
| The same filing's citation, *"`reference.md` § **Steps that consume an earlier run's artifacts** is where `reuse_from` is specified"* | **Stale.** No such heading exists in `reference.md` at this commit; `reuse_from` is specified in **§ Lineage between runs** and its § `reuse_from` addresses an artifact, and listed in § Steps and artifacts' `io` table. A filing's claims about the documents go stale like any other comment |
| *"`dry-run`, `draft`, `resume`, `study`, and `reproduce` each print `unknown command` and exit 2"* (§ Executability preamble, dated 2026-08-15 at `2fdc957`) | **False today, and no later entry corrects it.** All five print *"is specified but not built in this version — see docs/reference.md § …"* and exit 2 — `cli.py`'s `_report_not_built`, whose docstring argues at length that the two are *different news*. The exit code survives; the diagnostic does not. Properly dated, so this is a stale claim rather than an undated one — but it is the claim a reader of that section reaches first |
| *"§ CLI reference: … that run directory already contains the config it used"* (`reference.md`, about `resume`) | **False.** Measured: a run directory carries the config only inside `run.yaml`, written at the end, and `resume` refuses a run that has one. H9's to fix; H8b hits it first through `freeze` (§ 4) |
| `append_observation`'s *"`phase` is one of a closed vocabulary of four … named here so H8's and H9's callers do not mint a fifth spelling"* (H7d Part A) | **Half false.** The four names exist and are the right ones; the closure is **not enforced** — the mutation wrote `"BOGUS_FIFTH_SPELLING"` verbatim. The docstring describes a guarantee the code does not provide, which is `CLAUDE.md`'s most-repeated habit. H8b's task 13 |
| `H7-SCOPING.md` § 4's routing table (`freeze` → H8, `diff`'s apparatus row → H8, `apparatus.expected.json` → H9) | **Survives entirely**, and is now confirmed by invoking each command rather than read |
| § Package layout as a complete map of what core's source will hold | **Incomplete for H8.** `lineage.py`, `study.py` and `report.py` carry markers; **`diff` and `freeze` have no module at all.** Not litigated here — a document decision H8b's design owes, with `hashes.py` and `apparatus.py` the plausible hosts |

**Two contradictions to decide, not to resolve here.**

1. **`diff`'s exit code.** § Exit codes and diagnostics puts *"a `diff` of runs that don't share a
   hash"* under **`1`** — while `design-principles.md` § Same code, different parameters and
   `README.md` § The loop both show `parameters_hash DIFFERS` as *"the comparison to aim for"*.
   Candidate readings: 0 on any difference (a `diff` did what it was asked); 1 on any difference (as
   § Exit codes literally reads, which makes the advertised comparison a failure); 1 only when
   `code_hash` differs (the identity claim), with parameter deltas at 0. § Exit codes disambiguates
   **`report`** explicitly (*"`report` of a `partial` run exits `0`"*) and `diff` not at all, which
   is itself evidence the case was never decided.
2. **`diff` "takes two config or run paths."** A config carries no `code_hash`, no
   `input_manifest_hash` and no `uv_lock_hash`, so three of the five rows have no left-hand side in
   a config-vs-run comparison. § Reproducing on another device solves the analogous problem for
   `reproduce` by defining the config form explicitly and saying *"It cannot verify a `code_hash`
   and says so, rather than reporting a match it never made."* That sentence is the precedent, and
   `diff` has no equivalent.

---

## 9. Decomposition — 30 tasks, split 10 / 8 / 12

**H8 should split, three ways.** 30 is well past this repo's 9–20 band, and the seam is not
arbitrary: exactly one third of the work touches `io` and can move a count, and the other two thirds
are read-only commands over artifacts that already ship. A two-way split (lineage, then all
reporting at 20) is defensible; three is better because `report` and `study` share `BaseReport` and
a bundle format that `diff` and `freeze` need nothing of.

### H8a — lineage · 10 tasks · **the count mover, ships first**

Delivers alone: `io.reuse_from` works, `provenance.upstream` is recorded, and **E3, E4 and E6 gain
no remaining core-side blocker — three to six, and executable three to six** under the standing
plugin qualification. Retires no refusal (there is none in this family to retire) and **mints its
first**.

1. A **`run.yaml` reader** — `schema_version`, a malformed or absent record as a named refusal. Used
   by every later task in every sub-slice; built here because H8a needs an upstream's hashes first.
2. `lineage.py`: `run_id` → run directory, both forms — `<output_dir>/<run_id>/`, and an absolute
   run-directory path whose `run_id` is **read back from that run.yaml** rather than parsed from the
   path.
3. Getting `output_dir` onto `io`. Measured: `ArtifactIO.__init__` has `step_dir`, `input_dir`,
   `run_dir` and no `output_dir`. `run_dir.parent` is the tempting proxy and § Answering a question
   with a proxy is the section about exactly that move — the config's `data.output_dir` is the fact.
4. Locating `step` inside the upstream tree **without a scope selector**. `read_upstream` resolves
   `shared/` vs `summary/` vs a condition dir from `self._step_scopes`, which is *this* run's map;
   the upstream's scopes are in its own `run.yaml`'s `execution` block. This is the design decision
   the § `reuse_from` addresses an artifact rule creates and does not answer.
5. `io.reuse_from(run_id, step, name)` itself: the relative-path rules `io.write`/`read_upstream`
   already enforce (no absolute, no `..`, no symlink escape), reader dispatch by longest registered
   suffix through the machinery `_read` already has.
6. Upstream **accumulation**: `(run_id, code_hash, parameters_hash, used[])` gathered across every
   execution and threaded back from `io` to `command_run`. `used` is a set of names, ordered
   deterministically or the key is unstable across runs.
7. `provenance.upstream` assembly, **and the absent-vs-`null` decision of § 3**, with the `run.yaml`
   example's no-upstream shape written into § The two files.
8. Refusals + § Errors rows: upstream run directory missing; no readable `run.yaml` there;
   artifact absent in the upstream; `run_id` in the path form disagreeing with the record.
   "Lineage is recorded, not resolved" is the rule these encode — **an unreachable ancestor is
   reported, never recomputed.**
9. Read-direction and scope: § Lineage's example reads from a downstream step at **any** scope.
   Check against `scope.py`'s existing read-direction checks — `read_upstream` reads *wider* steps
   and `reuse_from` is not that relation at all.
10. Documents: § Package layout's `lineage.py` marker, § Steps and artifacts' `io` table row,
    § Lineage between runs, and the § Executability re-measurement with the corrected counts of § 6.

### H8b — `diff` and `freeze` · 8 tasks · read-only, and the boundary slice

Retires no refusal, unblocks zero configs, and the only direction it can move a count is down —
which is H7d Part B's shape and worth saying in its design for the same reason.

11. A **ledger reader**: reconstruct per-condition, per-fact **first *answered*** observations from
    `apparatus/probes.jsonl`. Nothing reads that file today; `Observations` is in-memory and belongs
    to another process. The reconstruction must reproduce H7d Part B's rule exactly, or `freeze` and
    the gate disagree about the same run.
12. `freeze`: run-directory argument, tolerant of a held lock, one probe per condition, append with
    `phase="freeze"`, report a moved apparatus as a **failure**, change no status and write nothing
    else. **Blocked on the § 4 decision** — resolve it here or hand H9 a resolution.
13. Enforce `append_observation`'s closed four-phase vocabulary, mutation-pinned. (Its docstring
    already claims this.)
14. `diff`: two paths, the five rows in the documented order with the documented labels, identical
    vs. DIFFERS, then the specific parameter deltas from the two embedded configs.
15. `diff`'s `apparatus DIFFERS` row and its per-fact `old → new` lines, on the same footing as the
    other four — the row `H7-SCOPING.md` routed here.
16. `diff`'s **exit code**, and the § Exit codes rows that settle it (§ 8, contradiction 1).
17. `diff`'s config-vs-run form (§ 8, contradiction 2) and its labelling of a draft.
18. Codes and homes: `E-DIFF-*` / `E-FREEZE-*` with § Errors rows, and § Package layout's missing
    module entries for both commands.

### H8c — `report` and `study` · 12 tasks

Unblocks zero configs and completes the designs the analysis routes *through* a study.

19. `BaseReport`, `sections(self, run, io)` as a generator, exported; § The importable surface row
    `not yet built` → `built`; the `spec-defects.md` entry struck.
20. Override discovery of `src/<pkg>/report.py`, and the rule that an override **adds and reorders
    sections and cannot change a number**.
21. `generate report <exp> --format`, and its removal from `NOT_BUILT_GENERATORS` (§ 7).
22. The standard sections: condition table, deltas, hypothesis verdicts, attrition.
23. Markdown and HTML renderers, and `format`'s "the class is the source of truth from then on".
24. `report <run.yaml>`: **exit 0 on a `partial` run**, with the failures shown.
25. `report` refusing to render a **draft** as a final result.
26. `report <study.yaml>`: bundle render, offline; the `code_hash` cross-check; the
    `provenance.apparatus.hash` cross-check; draft flagging; every hypothesis in one table.
27. `study new`: bundle creation outside any repo, `--title`, refusing an existing bundle in the
    `E-*-EXISTS` family § Exit codes already defines.
28. `study add`: copy the record, redact the five fields with markers distinguishing *redacted*
    from *never captured*, keep every hash, `code.commit`'s "the run added `--as main`, else the
    first" rule, a **notice** on a commit mismatch, and a **refusal** of a name already in the
    bundle.
29. `study add`'s `min_reported_n` prompt over all three metric shapes plus the `Estimate` with no
    `n` — and the § Everything is in the file constraint that a prompt is proceed-or-quit and **may
    never alter what executes**.
30. The `allocation.json` question § What `study add` redacts leaves open **in writing** for
    "whichever slice builds `study.py`", plus `E-STUDY-*` / `E-REPORT-*` codes and their § Errors
    rows.

**If `io.reuse_from` is chartered elsewhere**, H8a drops to about 6 and the total to about 26 — and
the count movement of § 6.3 goes with it. **If `generate report` is chartered elsewhere**, H8c drops
to 11 and the total to 29.

---

## 10. What could not be measured

- **Whether E3, E4 and E6 have any core-side dependency beyond `io.reuse_from`.** Same limit every
  prior entry names: a step-level call is invisible to `validate`, `growth_screen`'s steps do not
  exist, and the "no remaining core-side blocker" reading rests on reading each design's prose.
  § 6.3's "after H8a" column inherits that limit exactly as the "three executable" figure it
  corrects does.
- **E3's blocks were not transplanted** — its section shows only what differs from E1 and carries no
  `data`/`statistics` YAML. Said rather than filled in.
- **`freeze` against a run holding its own lock was not exercised.** It needs a second process
  mid-run *and* an installed probe plugin; nothing exists to invoke. Its testability claim in § 5 is
  therefore a **read** of § Operation commands plus a **measurement** that `append_observation` is
  callable from outside `command_run` — not a demonstration that `freeze` can be pointed at a locked
  run.
- **Whether `report`'s standard sections can be rendered from `run.yaml` alone**, or need the run
  directory too. § A report override hands the override *both* (`run` and `io`), which suggests the
  standard sections may not need `io` — but that is an inference from an argument about the
  override, not a measurement, and H8c's design owes it a reading of what each of the four standard
  sections actually requires.
- **Row counts and labels of `diff`'s output under an `apparatus` present but unchanged.** All three
  worked outputs show either a full DIFFERS block or no row at all; whether an identical apparatus
  prints `apparatus  identical` is stated nowhere and was not derivable.
