# H8b — `diff` and `freeze` — ledger

Design: `docs/superpowers/specs/2026-08-20-diff-freeze-design.md` (**15 decisions**). Plan:
`docs/superpowers/plans/2026-08-20-diff-freeze.md` (**14 tasks**, seven batches, **ten corrections**).
Baseline at `0a636af`: **2513 passed, 1 skipped, 2 xfailed.**

## Both of the scoping's contradictions are ruled

**`diff` exits 0 whenever it rendered; 1 only when it could not.** The `1` row's `diff` clause generalized
from `resume`, where a moved hash blocks an **action** — `diff` takes none — and both README and
`design-principles.md` make `parameters_hash DIFFERS` *"the comparison to aim for"*, which a non-zero exit
makes unscriptable. `report` of a `partial` run exiting 0 is the named precedent. **Cost if wrong is
bounded one way and unbounded the other:** a script keying on `DIFFERS` versus `|| true` swallowing the
unreadable-record case.

**`diff` takes exactly two paths, no flags, form by path shape, and a config supplies exactly one of the
five rows.** The other four print `not comparable` **with reasons**, because computing
`code_hash`/`uv_lock_hash` from the config's repo answers **the tree now, not the tree then** — § Answering
a question with a proxy — the manifest needs a resolved roster, and `diff` is not one of the four places a
probe runs.

## The controller ruling on Decision 7, and why it is not the Part B case

`run` starts writing `<run_dir>/config.yaml` and `environment/repo_root.txt` so `freeze` can work at all.
**Approved**, on measured ground: `get_template` skips `discover_local` when `repo_root is None`, so
without it a project-local template's `apparatus_probe` is unreachable and `freeze` would fail on exactly
the templates H7a made possible.

**This is a behaviour change to a shipped command, and it is distinguishable from the one I refused on
H7d Part B.** That one changed **what an existing key reports** — observable by every existing consumer.
This one is **additive**: no existing artifact changes, no verdict, status or exit code moves. The
requirements attached: additive-only pinned in two directions, § Artifact layout gains rows, **§ The two
files checked because its framing is *"`config.yaml` and `run.yaml`"* and this puts a third file named
`config.yaml` in the run directory**, and the document task **precedes** the code task.

## The plan measured the pin impact rather than assuming it

**No existing pin moves on content.** Nothing in `tests/` enumerates the run-directory root or
`environment/`; the one `iterdir` equality is over `results_dir`, one level up, and every `rglob`
assertion filters to directories. No hash moves and no `provenance` key is added, so **H8a's guard-pin
arm B holds untouched.** One pin's **scope** widens — `_files_under(results_dir)` sweeps every file for a
credential sentinel, and the two new artifacts join that set; the plan runs every caller by name, noting
that *reasoning* a config holds only a variable's name **is right and is still not the measurement.**

## Two task-reshaping corrections, and one correction of mine that was wrong

**A prescribed mutation was BLIND and the plan proved it:** `yaml.safe_dump(yaml.safe_load(x)) == x` is
True for the config `run_a_project` writes, so a byte copy and a re-dump are **byte-identical** and the
mutation could never fail. Rebuilt on raw-text editing with a `b"#"` control.

**And the two `Status` flips cannot live in the documents task** — `_dispatch` checks built branches
*before* `NOT_BUILT_COMMANDS`, and the CLI-table test asserts **both** directions, so arm, key and cell
must land in one commit per command.

**Correction 4 is itself false and is overruled.** It claims `CLAUDE.md`'s `EXIT_EXTERNAL` clause is false
and self-contradicting. The clause reads *"`EXIT_EXTERNAL` **was** the same fault outside `BaseTemplate`
**until** H7d Part B task 8 gave it its reader"* — past tense, and consistent with the sentence naming
`field_convention` as the **sole remaining** example. **Deleting it would remove the row's own evidence
that it retires entries as readers land**, which is the property that makes it self-maintaining. **A plan
correction is a claim too**, and this one was not checked against the text it quotes.
