# H7d scoping — the apparatus

Read-only measurement against `main` at `0faa2e31456d052ec63d3f58c0d6d872213371dd`, on
2026-08-19, the commit that merged H4d. **No tracked file was edited; this document is the whole
deliverable.** Every build claim below was produced by running something — a `validate_config`
call, an end-to-end `run`, a decorator-level mutation, or a `grep` whose control was checked —
and each says which. Where a claim comes from reading a document rather than from running, it
says *read*.

This **re-measures** `H7-SCOPING.md` § 4 (*The apparatus: how much is specification with nothing
underneath*), taken against `cb96c7d` before H7a, H7b Parts A and B, H7c and the whole H4 family
landed. Where this document contradicts that one it says so and shows the measurement.

**Verdict: 22 tasks**, against the charter's 14 and the old scoping's 14. **It should split, on
the observe-and-record / gate-and-stop seam, at 13 / 9.**

**Baseline at this commit:** `uv run pytest -q` → **2363 passed, 1 skipped, 2 xfailed**, 138 s.
`uv run publishable dry-run|freeze|diff …` each print *"specified but not built in this
version"* — measured, not read.

---

## 0. Executive summary

1. **The old scoping's headline claim is dead.** It said the apparatus is *"all of it except two
   inert class attributes."* Five surfaces it recorded as absent now exist: `register_probe`, the
   `PROBES` registry, the `publishable.probes` entry-point group and its metadata scan,
   `plugin new`'s probe scaffold, and `validate._check_probe` with `E-PROBE-UNKNOWN`. The unbuilt
   set is genuinely narrower, and the slice's first task is no longer a registry.
2. **The false `apparatus: null` is live, and I reproduced it end to end** — not from an emit
   site. A project-local template declaring `apparatus_probe = "llm_deployment"`, with a real
   installed distribution registering that name, **validates clean, runs to `status: completed`,
   exits 0, writes `provenance.apparatus: null`, creates no `apparatus/` directory, and never
   calls the probe** (the probe would have raised).
3. **Exit code 5 does not exist in this build.** `diagnostics.py` defines `EXIT_OK`=0,
   `EXIT_WRONG`=1, `EXIT_INVOCATION`=2, `EXIT_PARTIAL`=3, `EXIT_FAILED`=4 and nothing else.
   `reference.md` specifies an unreachable apparatus as `status: partial` **plus exit 5, winning
   the precedence contest against 3**. H7d is the first slice that can emit it, and the charter's
   14 tasks name none of that.
4. **Nothing in the record distinguishes a truncated plan from a complete one.**
   `status = run_status(results)` is `cli.py`'s sole determination (one call site, measured), the
   plan is never compared against `len(results)` after `execute_plan` returns, and
   `assemble_run_yaml` is not handed the plan at all — so a run the gate truncates with everything
   that ran having completed records `completed`. `run_status` is a fold over the statuses that
   exist (`run_status([completed, completed])` → `completed`), which is the shape of the problem
   rather than proof of it; the proof is that no length comparison reaches `status`. That is a
   contract change, not a wiring task, and no charter names it.
5. **`CLAUDE.md`'s "sole remaining example" is false.** `apparatus_facts` is *not* the sole unbuilt
   reader of a shipped surface: `field_convention` is declarable on a shipped class and read by
   nothing either, and its owner is explicitly *unassigned* in `spec-defects.md`.
6. **H7d moves neither count.** Six configs with no remaining core-side blocker, three executable —
   both unchanged. The nine configs do not reach the apparatus at all; the *plugin they are designed
   around* does, which is a different and more useful sentence. See § 7.

---

## 1. Method

Two harnesses, both under the scratchpad, neither in the repo:

- `measure9.py`, the harness H7b Part B task 33 built and every entry in the feasibility
  analysis's § Executability has used since: a real scaffolded project, a real installed
  distribution registering `patient_trajectory`, and each of the nine configs'
  `data`/`statistics` blocks through `validate_config`. Re-run at this commit; its can-fail
  control (`holdout.frac → 0` ⇒ `E-DATA-HOLDOUT-FRAC`) fired.
- `h7d_probe.py`, new here: a scaffolded project, a **project-local** template declaring
  `apparatus_probe`, a synthetic installed distribution whose `publishable.probes` entry point
  names a module whose probe **writes a flag file and then raises**. That is the mutation — a
  probe core calls cannot be silent about it — rather than a read of call sites.

---

## 2. What the specification requires — enumerated by reading, then confirmed by grep

Read from `reference.md` § The apparatus core can only observe, § The apparatus files, § The
importable surface, § Package layout, § What status means and when a run keeps going, § Exit
codes and diagnostics, § Reproducing on another device, § Creating a plugin, § A `batch` says
*when*, not *what*; `design-principles.md` (four passages); `experimental-designs.md`. The grep
confirming each is `grep -rn "apparatus\|probe" src/publishable --include="*.py"`.

| Specified | State at this commit | How measured |
|---|---|---|
| `register_probe` decorator, exported from `publishable` | **built** | in `plugins.py`; in `__init__.py`'s `__all__`; § The importable surface row already says `built` |
| `publishable.probes` entry-point group, metadata-only scan | **built** | `plugins.GROUPS`; `names("publishable.probes")` |
| `PROBES` registry filled by the decorator | **built, read by nothing** | grep: one write site, no read. Filed |
| `validate` checks the declared probe **is registered**, never calls it | **built** | `_check_probe` → `E-PROBE-UNKNOWN`; probe-raises mutation confirms no call (§ 4) |
| `plugin new` scaffolds a probe module and its entry point | **built** | `plugin_scaffold.PROBE_PY`, `"publishable.probes"` in its group table |
| `Apparatus` construct — `probe(cfg) -> Apparatus`, carrying `facts` | **absent** | not in `__init__.py`; § The importable surface row still `not yet built` |
| `apparatus.py` (§ Package layout: per-condition facts, the change gate, `Apparatus`) | **absent** | no such file under `src/publishable/` |
| Probe invocation at run start | **absent** | no call site; end-to-end run never called it |
| Probe invocation before **every** execution | **absent** | same |
| `apparatus/probes.jsonl`, append-only, UTC + phase + condition, nulls included | **absent** | no `apparatus/` directory in a completed run |
| `provenance.apparatus.probe` / `.ledger` / `.hash` / `.facts` / `.unobserved` | **absent — `cli.py` writes the literal `None`** | § 3 |
| `apparatus_facts` projection (every declared key must come back; a missing key is the one error) | **absent — the attribute has no reader** | grep: two declarations, one generator comment, two test assertions |
| The credential-leak check on returned fact values | **absent** | no call site to check from |
| Null semantics: value / declared-absence / missing key; `null ↔ value` never fails | **absent** | no comparison exists |
| The per-condition, per-fact change gate against the first *answered* observation | **absent** | no comparison exists |
| A probe **may** read a swept parameter (the inverse of the resolver rule) | **not exercisable** | the rule is stated in two § Errors rows and § The apparatus core can only observe; nothing calls a probe, so nothing tests it |
| `status: partial` + **exit 5** on a probe that stops responding | **absent, and 5 is undefined** | `diagnostics.py` defines 0–4 |
| `apparatus.expected.json` written by `reproduce` | absent — `reproduce` is unbuilt | `publishable reproduce` prints *not built* |
| `diff`'s `apparatus DIFFERS` row; `freeze`'s re-probe; `report study.yaml` cross-checking `provenance.apparatus.hash` | absent — all three commands unbuilt | measured by invoking each |
| `E-` codes in the family | **exactly one: `E-PROBE-UNKNOWN`**, one emit site | grep over `docs/*.md`, `src/`, `tests/` for `E-APPARATUS`/`E-PROBE` |

---

## 3. `cli.py` writes `"apparatus": None` unconditionally — characterized, and reproduced

`cli.command_run`'s provenance document has one `apparatus` key and no branch reading a
template's `apparatus_probe` at all. That is what `spec-defects.md` § *a run whose template
declares an installed probe records a false `apparatus: null`* filed, owned by H7d. The filing's
claims about the code are **still true**, and this is the first measurement of it end to end
rather than from the emit site:

```
validate findings: []                      # local template declares apparatus_probe: llm_deployment,
probe called during validate? False        #   an installed distribution registers it
run exit: 0                                # only W-ENV-UNLOCKED printed, from the scratch project
probe called during run? False             #   having no uv.lock — unrelated to the apparatus
provenance.apparatus: None
'apparatus' in provenance: True
apparatus/ dir exists: False
status: completed
```

`reference.md` § The apparatus core can only observe defines `apparatus: null` as *"no probe
declared"*. This run declared one. The record is false in the specification's own words, and the
run is publishable-looking while nothing pinned the server.

**Control for the same harness**, so the clean `validate` above is not vacuous: renaming the
template's declared probe to a name nothing registers earns `E-PROBE-UNKNOWN` and nothing else
changes.

---

## 4. The `_check_probe` boundary, measured with a mutation

`_check_probe` reads `getattr(template, "apparatus_probe", None)` against
`plugins.names("publishable.probes")` — the **entry-point metadata scan**. It is a reader for the
declared *name*. It is not a reader for the `PROBES` mapping the decorator fills, and it never
imports the providing module.

Measured rather than read: the probe registered in the harness **writes a flag file and raises**.
After `validate_config`, the flag is absent and no exception escaped. The existing suite's
honouring test points the same way from the other side — its entry point targets `no_one:probe`,
a module that does not exist, and the check passes — but **no test asserts that a validate path
does not call a probe**, and the charter's task 3 asking for one is still owed.

**Two sources of truth for "is this probe registered", and H7d must reconcile them.** A probe
registered in-process by `@register_probe` with **no** entry point is in `PROBES` and invisible to
`_check_probe`; a probe with an entry point and no decorator resolves at `validate` and is absent
from `PROBES` until loaded. That is the same shape H7b Part B settled for resolvers —
`load_entry_point` + `check_registration` + `declared_names`, all three built and now with
production callers — so H7d's probe dispatch should be that function's sibling rather than a new
mechanism.

---

## 5. The `batch` wire — run, not read

`CLAUDE.md` § Invariants defines `batch` as *"the state of the apparatus it measures through"*.
The old scoping said nothing connects the two in code, with `W-REPL-DETERMINISTIC` as the one
live wire. **Re-measured by running both arms**, on one config differing only in whether the
scaffolded step declares `nondeterministic`:

| Arm | Codes |
|---|---|
| `batch` level, every step deterministic | `W-REPL-DETERMINISTIC` |
| `batch` level, one step `nondeterministic = True` | *(none)* |
| Either arm | probe never called |

So the wire is real, it reads **step declarations** and not the apparatus, and it discriminates.
The old scoping's conclusion survives and is now measured: **H7d owes `batch` no change**, and
should ship the test asserting the independence so nobody later "connects" them. That is task 21.

---

## 6. Ownership — the split re-checked, and the one place it no longer holds

The old scoping's table said four of six apparatus-consuming surfaces belong to H8/H9. **The
structural half survives**: `dry-run`, `draft`, `resume`, `demo`, `docs`, `reproduce` are H9's and
`freeze`, `diff`, `report`, `study` are H8's per the spine design § The hardening slices, and all
of them are still unbuilt (measured by invoking each).

**The half that does not survive is where the *checks* live.** § The apparatus core can only
observe sites the declared-keys check, the credential-value check and the null-fact warning **at
`dry-run`** — H9's. But the same section runs the probe at **run start and before every
execution**, which are H7d's. Taking the old table literally ships a slice that calls user code N
times per run and never checks that a declared key came back, with the enforcing check parked
behind an unbuilt command. **H7d must build the fact projection and the credential check as
phase-independent functions invoked wherever a probe runs**, and `reference.md` § The apparatus
core can only observe needs a sentence saying so — the document changes first. That is task 4 plus
a documentation task, and it is the one routing claim in the old charter I would not carry.

**What H7d should refuse.** The old charter's tasks 12 and 13 deliver `resume`/`dry-run`/`freeze`
hooks *"as callables with tests, not as commands."* Decline. This repo has filed the
shipped-but-unread family three times in four commits (`PROBES`, `load_entry_point`,
`declared_names`, `template_provenance`), and manufacturing three more callables with no
production caller is that filing again by choice. The calling slice builds its own call site
against `apparatus.py`'s public functions. Say it as a decision in the design, not as a discovery.

**Filings, swept for stale owners** (the H4d re-ownering problem):

| Filing | Owner | Claims still true? |
|---|---|---|
| *a run whose template declares an installed probe records a false `apparatus: null`* | H7d | **Yes** — reproduced end to end, § 3 |
| *`PROBES` and `RESOLVERS` are written by their decorators and read by nothing* | `PROBES` → H7d (the rest re-owned to H7b Part B and closed) | **Yes** — grep: one write, no read |
| *`BaseTemplate.field_convention` is declarable and read by nothing* | **unassigned** | **Yes**, and it is why `CLAUDE.md`'s "sole remaining example" is wrong (§ 8) |
| *two specified readers of `required_env` belong to unbuilt commands* | `reproduce`'s and `dry-run`'s slices | Yes; not H7d's, and named so it is not folded in |
| *`io.reuse_from` is unbuilt and unowned* | unassigned | Yes; not apparatus, but it is what keeps six configs non-executable |

**No apparatus filing points at a closed slice for unbuilt work.** The one sentence that reads
that way — *"`apparatus_probe` is H7b task 13's"* — names work that **shipped**, so it is a
history note, not a live pointer. This is the check H4d's five re-owned filings failed and this
family passes.

---

## 7. What H7d unblocks — measured

`measure9.py` re-run at this commit, all nine configs through `validate_config`:

```
E1..E6, C1..C3: ['W-DATA-CLUSTER-UNDECLARED']   (every one; no errors)
E1 CONTROL (holdout.frac=0): ['E-DATA-HOLDOUT-FRAC', 'W-DATA-CLUSTER-UNDECLARED']
```

**Both counts stay exactly where H4b-1 left them: six with no remaining core-side blocker, three
executable.** H7d moves neither, and the reason is not that a refusal it retires goes unhit — it
retires no refusal at all. No config in the analysis declares anything the apparatus reads; the
declaration is a **template** attribute, and the substituted template is `generic`, which declares
none.

**The distinction the old charter collapsed, and both halves are true.** *As measured*, the nine
configs need nothing from H7d. *As designed*, the analysis's `publishable-llm` plugin ships
`llm_screen` with `apparatus_probe = "llm_deployment"` and five `apparatus_facts`, and § 3 shows
what a run of that template does today: a false `apparatus: null`, no ledger, no gate, and the
probe never called. So the honest sentence is **"H7d moves no count and is what makes a run of
these designs honest,"** not "H7d unblocks configs."

One direction worth stating because it is the opposite of an unblock: once the fact projection is
built, a probe that fails to yield a declared key becomes a **new** error such a run can hit. H7d
can only lower a config-level executable count, never raise it.

---

## 8. What did not survive from `H7-SCOPING.md` and `CLAUDE.md`

| Claim, and where | Verdict |
|---|---|
| *"The apparatus is all of it except two inert class attributes"* (§ 4) | **Dead.** `register_probe`, `PROBES`, the `publishable.probes` group and its scan, `plugin new`'s probe scaffold, and `_check_probe`/`E-PROBE-UNKNOWN` all exist |
| *"`apparatus_probe`, `apparatus_facts` — confirmed inert. Nothing reads either"* (§ 1) | **Half dead.** `apparatus_probe` has a reader at `validate`; `apparatus_facts` still has none |
| *"`register_probe` — absent, and so is everything downstream of it"* (§ 2) | **Dead** for the decorator; **survives** for everything downstream |
| *`plugin new` / `plugin_scaffold.py` — "one unowned residual, named rather than absorbed", chartered into H7b as task 17* (§ 10) | **Resolved without re-ownering.** Both ship, and the scaffold writes a probe module and its `publishable.probes` entry point — so H7d inherits a working way to produce a plugin to test against |
| The H8/H9 routing table (§ 4) | **Survives structurally; its check-placement half does not** — see § 6 |
| *"H7 owes no change to `batch`"* (§ 4) | **Survives**, and is now measured rather than read (§ 5) |
| *"H7b makes those nine configs validate and H7d is what makes a run of them honest"* (§ 9) | **Survives**, and § 3 is the first end-to-end demonstration of the second half |
| The 14-task count (§ 8) | **Undercounted by 8.** It names no exit code 5, no `run_status` contract change, no `hash` sub-key computation, no document rows, no `PROBES`/entry-point reconciliation |
| `CLAUDE.md` § Misreadings: *"`apparatus_facts` is now the sole remaining example"* of an unbuilt reader of a shipped surface | **False.** `field_convention` is declarable on a shipped class and read by nothing (`grep -rn field_convention src/ tests/` → two declarations, one generator comment, two test assertions, no reader), and `spec-defects.md` says the family is both. `PROBES` is a third member of the wider shape |

---

## 9. Decomposition — 22 tasks, split 13 / 9

The seam is **observe-and-record versus gate-and-stop**. It is real rather than convenient: Part A
closes the false-`apparatus: null` filing on its own, needs no comparison between two observations,
and cannot stop a run. Part B is where the refusal, the truncation, and the new exit code live —
and where every "a mutation is a claim too" risk in the slice sits.

### Part A — observe and record · 13 tasks · retires no refusal, stops no run

1. `Apparatus` construct + export from `publishable`; § The importable surface row `not yet built` → `built`; § Package layout's `apparatus.py` marker retired.
2. `apparatus.py`: probe resolution as `_resolver_for`'s sibling — `scan_group` → `load_entry_point` → `check_registration`/`declared_names` — giving `PROBES` its first reader and closing that filing's H7d half.
3. Probe invocation: `probe(cfg)`, and **which `cfg` is a decision H7d must make rather than inherit.** `runner.resolve_condition_cfg` overlays this condition's swept values; `runner.resolve_wide_cfg` replaces every swept leaf with a `SweptAway` marker that raises `E-STEP-SWEPT-PARAM` on read. § The apparatus core can only observe says a probe *may* read a swept parameter and usually must, which points at the condition cfg — and if that is the choice, **the "a probe may read a swept parameter" test is vacuous**, since no marker is present to raise. Decide it explicitly and say what the test then proves, or the test is unfalsifiable.
4. `apparatus_facts` projection: every declared key must come back, a missing key is the one error. **Phase-independent, not `dry-run`-only** — § 6. New code. Gives `apparatus_facts` its first reader.
5. The credential-leak check on returned fact values, through H7c's existing `secrets` collector and the redacting diagnostic path H7b Part B built. New code.
6. Null semantics: value / declared absence / absent key, and the per-fact `unobserved` counts (`null_probes`, `total_probes`).
7. `apparatus/probes.jsonl`: append-only, UTC, `phase`, `condition`, `probe`, `facts` with nulls included; § Artifact layout row.
8. Probe at run start.
9. Probe before **every** execution, inside `execute_plan`'s loop; N calls for an N-execution plan, stated in the design because `dry-run` (H9) must be able to print the number.
10. `provenance.apparatus`'s five sub-keys replacing `cli.py`'s hardcoded `None`, `probe: null` staying the honest record for a template declaring none. **Closes the OPEN filing.**
11. `provenance.apparatus.hash` over the resolved condition → facts mapping — its own computation, explicitly **not** a fourth hash and **not** an extension of `HASHED_TREES`.
12. A test that the recorded block is publishable as-is — no credential value, and `study add` has nothing to redact from it.
13. § Errors `validate` reports, § Errors core raises, § Validation and § Artifact layout rows for every code minted above. The family has **one** code today; that is the documentation debt's whole size, measured.

### Part B — gate and stop · 9 tasks

14. The gate: per condition, per fact, against the first **answered** observation. `value → value` fails; `null → value` and `value → null` do not. The fixture must separate all three, since a two-observation fixture cannot.
15. No policy knob — a test that nothing under `limits` can permit a changed fact.
16. Run-stops-here placement, on `max_failed_fraction`'s existing `break` precedent in `execute_plan`.
17. **`run_status`'s contract**: nothing downstream of `execute_plan` compares `len(results)` against the plan, and `assemble_run_yaml` never sees the plan, so a truncated all-completed plan records `completed`. A stop reason (or the plan's own length) has to reach the status determination, or `status` lies about a gated run. Both existing truncation paths hide this — `max_failed_fraction`'s `break` is only reachable once failures have accumulated, so its results list is never all-completed, which is why no test has ever separated the two.
18. `EXIT_EXTERNAL = 5` in `diagnostics.py` — the first code beyond 0–4 — with the documented precedence: 5 wins over 3 and 4.
19. The unreachable-probe path distinguished from the moved-fact path: unreachable ⇒ `partial` + 5; moved ⇒ the run fails, on the same line as a dirty tree.
20. The ledger keeps both observations across a gate failure, so the evaluable earlier period is still reportable — asserted on the file, not on the in-memory mapping.
21. The test asserting `batch` and the apparatus stay independent (§ 5).
22. The test asserting **no `validate` path calls a probe**, by the probe-raises mutation of § 4 — the charter's task 3, still owed, and the one guard that keeps `validate` inside "may not reach anything outside the machine".

**Why not one slice of 22.** Against this repo's own grain — H3a 12, H3b 13, H3c-1 20, H7b Part A 20 / Part B 9, H4d 13 — 22 is over the band that has worked here, and the two halves fail differently: Part A's risk is a **false record**, Part B's is a **run that stops when it should not**. The split argument is that Part A is shippable alone, closes an OPEN filing by itself, and improves every run's record the day it lands, while nothing in it can stop a run — so the review each half needs is a different review.

---

## 10. Cost and risk — what a metered probe does and does not constrain

`reference.md` is explicit that a probe costs **somebody else's** quota, and the old scoping read
that as a testing problem. It is not. **A probe is user code; core only ever needs a fake**, and
every task above is pinnable with a fixture: the projection, the credential check, the null
transitions, the gate, the ledger, the truncation, the exit code. The harness in § 3 already
registers a real installed distribution whose probe raises on call, which is the strongest fixture
shape the slice needs.

What quota actually constrains is **placement**, and it is three rules rather than a caveat:
`validate` must never call one (task 22 is the pin); an N-execution run makes N authenticated
calls, which is a number `dry-run` must be able to state before the run is scheduled (task 9); and
a gate failure must not retry, because a retry is another paid call against an apparatus already
known to have moved. Say this in the design so nobody later reads "probes cost money" as a licence
to leave the gate unpinned.

The one thing a fixture cannot stand in for is the behaviour the null rule exists for — a hosted
deployment that returns a revision fingerprint on most calls and omits it on some. That is why
`null` is a legal value rather than a failure, and it is also why an integration test against a
real deployment would be a worse pin than the fixture: it would pass or fail for reasons the code
does not control.

---

## 11. What could not be measured

- **Anything about `dry-run`, `freeze`, `diff`, `reproduce`, `resume`.** All five print *specified
  but not built*, so every claim here about where their checks live is a **spec claim**, read from
  `reference.md`, never a build fact.
- **Whether the gate composes with `resume`'s restart**, since `resume` does not exist. § Resuming
  says it refuses a changed apparatus; nothing can be run against that today.
- **The nine configs' actual plugin.** `publishable-llm`, `llm_screen` and `llm_deployment` are
  designs in the feasibility analysis, not code. § 3's measurement stands one in — a project-local
  template plus a synthetic installed distribution — which is the same substitution every
  § Executability entry has documented since 2026-08-16, and it is a substitution, not the thing.
- **A real metered probe.** Deliberately, per § 10.

---

## Correction, appended 2026-08-19 — § 0.3's exit-code claim is false

**This replaces § 0.3's finding that "exit code 5 does not exist in this build."** It does:
`EXIT_EXTERNAL = 5` is defined in `src/publishable/diagnostics.py` beside `EXIT_OK` through
`EXIT_FAILED`. Verified at `27e397e` by reading the definition and by grepping `src/` and `tests/` for
readers outside its own module — **there are none.**

Found by the Part A design while measuring the same surface a few hours later, which is the second time
on this project that **re-measuring a scoping the same week falsified one of its claims** —
`H7b-SCOPING-2.md` lost seven that way.

**Three consequences.** Part B's exit-code task is **narrower** than this document states: the constant
ships, so what is owed is a reader and the precedence rule, not the constant. It is a **fourth
shipped-but-unread member** of the family this scoping used to argue for declining the old charter's
tasks 12–13, which **strengthens** that recommendation rather than weakening it. And it was **unfiled** —
the Part A design's filings task closes that in `spec-defects.md`, which is where it belongs, not in a
ledger line.

**What did not change:** every other measurement here, including the task count, the 13/9 seam, and the
zero/six/three figures. The correction is confined to one claim.
