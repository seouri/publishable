# H7b Part A — plugin registries and entry points — design

**Goal:** a plugin installed on the machine can register a template, a resolver, a probe and a
writer, and `validate` resolves any of their names **without importing the package**. The collision
matrix over those names is decided at load and reported, not left to install order.

**What it delivers, stated honestly.** **No refusal retired and no experiment newly executing.**
`E-DATA-RESOLVER-UNSUPPORTED` stays alive across this whole slice and is retired by Part B, whose
task also lands the dispatch that makes a resolver run. What Part A delivers is every registry and
every load-time refusal the resolver will need, plus the documentation debt this area has carried
since H1 — and it delivers them where the wholesale refusal still stands, so nothing half-built can
execute.

**What it is not.** Not the resolver's dispatch, not the read-only resolver `io`, not attribute
projection, not `provenance.plugin_versions` — all Part B. Not `io.reuse_from`, unbuilt and unowned
by any H7 sub-slice. Not the apparatus itself — H7d.

---

## The measurement this rests on

`docs/superpowers/H7b-SCOPING-2.md`, taken 2026-08-16 against `main` at `ff51864`, **after H7c
merged**. It re-measures `H7b-SCOPING.md` of the same date, pinned one slice back, and **seven of
that document's conclusions did not survive** — including its headline finding that the feasibility
analysis's own plugin could not be written, which H7c fixed.

The charter's **17** became **27**, and now **29**, of which this slice is the first **20**.

---

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | Ship 29 tasks as one slice or two | **Two, seamed at 20/21** | 29 is well past this repo's band — H3c-1 shipped 20, H3d 19, H7c 14 — and the seam is the one `H7-SCOPING` named and both later scopings adopted. It keeps the wholesale refusal alive across the boundary, which is what H3d's seam bought: **shape checked before values honoured.** Part A touches no `units.py` and needs no roster; Part B touches `units.py`, `artifacts.py`, `cli.py` and `validate.py`'s skip |
| 2 | The missing `publishable.readers` entry-point group | **Mint the fifth group** | `io.write` dispatches on the longest registered suffix and `_read` **inverts the same table** — its own docstring says so. The asymmetry is what produces a bare `KeyError` for a third-party writer today. `CLAUDE.md`'s invariant that *each core writer takes exactly what its reader gives back* presumes a reader exists for every writer; a "stated convention" would leave the invariant true of core and false of plugins |
| 3 | `PartialLoadError` for the entry-point half | **Document the residual; do not reach for `.load()`** | H7c's payload carries partially-loaded classes so a load-time refusal can still redact. The entry-point scan is **metadata-only and structurally cannot carry a class**, so a plugin-side collision can never be redacted the same way. The natural repair — calling `.load()` — destroys the exact invariant entry points exist for, that `validate` resolves a name *without importing a line*. A named residual beats a silently weaker guarantee |
| 4 | A `data.units.from` declaring both `glob` and `resolver` | **Mutual exclusion, minted here** | It validates as a resolver (`_check_unimplemented` tests `"resolver" in source`) and would resolve as a glob (`resolve_units` tests `"glob"` first) — two answers to one declaration. Unreachable today and **reachable the moment Part B's dispatch lands**, so the refusal belongs in the slice that closes the envelope, not the one that opens the path |
| 5 | `--plugin` on `generate experiment` | **Mark it honestly first, then build it — both in Part A** | § Creation commands marks `generate` built *with* `--plugin`, and § Plugins says it runs `uv add`. Probed: it exits 0, writes `plugin: null`, installs nothing. The `Status` column is the repo's own device for this distinction, so the row is corrected before the feature lands rather than after |
| 6 | The test environment | **The suite gains a real installed distribution, and the collision matrix needs two** | An entry-point *metadata* scan cannot be exercised by a fixture that only writes files. Neither prior document drew this consequence — one wrote "test fixture: a real installed distribution" in a cell and stopped. It is a build-infrastructure cost and it is named here so no task discovers it |
| 7 | What Part A may assert about the wholesale refusal | **Every test asserts its finding appears *alongside* `E-DATA-RESOLVER-UNSUPPORTED`, never instead of it** | `validate` collects, so every resolver-adjacent config in Part A carries that code. Part B's task 24 retires it, and this form makes the retirement a **one-line deletion rather than a rewrite** — the discipline H3d proved and whose payoff was four tests found vacuous the moment the companion was removed |

---

## What the re-scoping overturned

**The prior scoping's finding 1 is dead.** It said the feasibility analysis's own plugin could not
be written because `Param` rejected `requires_env`. H7c built it, and the re-scoping probed the
actual three-provider declaration at `ff51864`: it constructs and renders the comment `reference.md`
shows. **H7c as a prerequisite is satisfied history, not a live constraint.**

**Three blockers remain, not four** — `io.reuse_from`, the probe, and `plugin new`, each
re-verified unchanged.

**H7c's `PartialLoadError` constrains every load-time refusal this slice mints**, and `_merged`
builds its payload from `local.values()` — a proxy that decision 3's task makes wrong.

**Every `validate.py` line number in the prior scoping moved by roughly 242.** A spec written from
it would cite locations that no longer exist.

---

## The trap Part B inherits, recorded here because Part A creates the conditions

**H7b creates a credential leak, and Part B must close it.** `cli.command_run` computes its
credential set **182 lines after** `resolve_units`, with no enclosing `try` — verified at the call
site. The same `ContractError` is redacted at `validate` and printed whole through `main` at `run`.
Today nothing there holds a credential; **the moment Part B's dispatch runs user resolver code, one
can.** The remedy is to move the credential computation, **not** to wrap the call.

A second half: a **non**-`ContractError` from that site escapes `validate_config` entirely, because
`_check_units` guards only `except ContractError`. After Part B, a plugin resolver raising
`KeyError` breaks the *"`validate` never raises"* contract.

Part A must not narrow either fix's options.

---

## The traps

| Trap | The rule |
|---|---|
| Reading a metadata scan as a load | The whole argument for entry points is that `validate` resolves a name **without importing**. Any check that reaches for the object behind the name has changed the guarantee, whatever it returns |
| A collision fixture with one distribution | The matrix is entry-point × entry-point, × core, × local. **Two distributions**, or the first arm is untestable and the fixture proves the others by accident |
| Name order read as discovery order | Providers are named in the message; the order must be the **name's**, not the order the scan happened to walk. Two elements only ever distinguish two answers — count the orderings to rule out, then size the fixture |
| A grep for one spelling | H7c sited redaction by `grep 'type(exc).__name__'` and a site formatting a bare `{exc}` leaked a credential. Enumerate by **reading** where a thing happens, then confirm by grep |
| Inferring unreachability from a refusal | **`validate` collects rather than aborting.** A refusal elsewhere never makes a later check unreachable — two independent readers got this wrong in H7c and a reviewer disproved it by building the fixture |
| A shipped-but-unread export | `register_probe` exported bare would be the **fourth** such surface beside `field_convention`, `apparatus_probe` and `apparatus_facts`. Its task ships the *Probe is installed* check that reads it, or it does not ship |

---

## Task decomposition — 20

From the re-scoping's § 9 Part A, in its order.

1. § Validation ↔ § Errors — the resolver family's identifiers.
2. § Errors core raises + § Creating a plugin — the four load-time refusals with no identifier.
3. **Decision 2's fifth group**, settled and filed.
4. § Package layout + § The importable surface — a home for the shared scan.
5. The `NOT BUILT` markers and the enum comments.
6. **Decision 5's honest marking** of `--plugin`.
7. The entry-point **metadata** scan, four groups, no `.load()`. **Decision 6's fixture.**
8. The collision matrix over metadata only.
9. Template provenance becomes three-valued — `local`/`core`/`installed`.
10. `BaseTemplate.version` and `W-TEMPLATE-VERSION`.
11. `E-TEMPLATE-UNKNOWN`'s `plugin` hint.
12. `register_resolver`.
13. `register_probe` **and the check that reads it**.
14. `register_writer`, and the refusal of a core-suffix claim.
15. `WRITERS`/`READERS` symmetry as an enforced invariant.
16. The decorator-vs-key check at load.
17. Import-failure containment, `SystemExit` included.
18. **`--plugin` built** — `uv add`, and the `plugin` field written.
19. **Decision 4** — envelope closure of `data.units.from`, plus the mutual exclusion.
20. **Decision 3** — `PartialLoadError` semantics for the entry-point half, and its documented residual.

**Sequencing.** 1 before everything. 7 before 8, 9 and 20 — they all read the scan. 13 ships its
reader with its export. 19 and 20 are the two that Part B's first tasks build directly on.

---

## Out of scope, with the route

The resolver's dispatch, its read-only `io`, attribute projection, condition-independence,
`provenance.plugin_versions`, `plugin new`, and **the credential-leak fix** — all **H7b Part B**,
which also retires `E-DATA-RESOLVER-UNSUPPORTED`. `io.reuse_from` — unbuilt, unowned, filed. The
apparatus and its probe credential — **H7d**.
