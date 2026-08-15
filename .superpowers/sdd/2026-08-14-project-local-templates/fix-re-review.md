# Fix re-review — H7a, project-local templates

Scope: the fix diff only, `6468842..c0df967`, 6 commits, 7 files, +292/−32. Read against
`whole-branch-review.md` (the findings), `whole-branch-fix-report.md` (the fixer's account),
and the tree at `c0df967`.

**Verdict: merge-ready.** All three Importants and all five Minors are closed, each verified
by mutation or by an independent measurement rather than by reading. Nothing behavioural is
outstanding. Two Minor prose items are recorded at the end — one-clause docstring edits, neither
blocking, both worth making because the standing rule about over-claiming is absolute.

**Commit-count reconciliation.** The fix report opens "five commits on top of `6468842`" and its
Commit→Finding table lists five; the diff carries **six**. The unlisted one is `c0df967`, the
tip: it closes no review finding. It trims a clause this same round introduced — `8403a6b`'s M3
comment and test docstring ended "and it would be left for whatever drains next", naming a
downstream inheritor the code does not have. So the round produced an over-claim and then
self-corrected it, which is CLAUDE.md's recorded shape ("three overreaching claims inside a
single commit that was itself fixing overreaching claims"). The self-correction is right and the
tree is better for it; the report should say so rather than leaving one of six commits unmapped.
See Minor B for the one clause the trim stopped short of.

Tree left as found: clean at `c0df967`, **1689 passed + 2 xfailed**, `ruff check` and `mypy`
clean. `ruff format --check` not raised (pre-existing, out of scope).

---

## I1 — one discovery per `validate`

**Closed.** Verified two independent ways, neither of which trusts a patch target.

**Measured by side effect, not by patch.** A `templates/cohort_local.py` whose top level appends
a line to a counter file, driven end-to-end through the real `validate_config` and
`generate_experiment`:

| Path | Top-level executions |
|---|---|
| `validate_config`, resolvable name | 1 |
| `validate_config`, unknown name | 1 |
| `generate_experiment`, resolvable name | 1 |
| `generate_experiment`, unknown name | 1 |

The review's finding was 2 on the unknown-name path and the identical pair in
`generators/experiment.py`; both now read 1. **The probe was proved able to report 2**:
restoring `template_names(repo_root)` at `validate`'s message call site moved that one cell to
2 and left the other three at 1 — so the number is measured, not assumed.

**Both new tests fail under that same mutation, each on the assertion it exists for.**

- `test_one_validate_discovers_local_templates_once_on_the_unknown_name_path` — fails at
  `assert len(calls) == 1` with `assert 2 == 1`. This also proves the patch target
  (`registry.discover_local`, the name `registry` imported) actually fires; a patch on
  `discovery.discover_local` would have counted 0 under both trees.
- `test_a_template_whose_import_is_not_idempotent_survives_an_unknown_name` — fails with
  `ContractError · E-TEMPLATE-LOAD` escaping `validate_config`, which is precisely the contract
  break the finding named.

Reverted by editing back; `validate.py` diffed byte-identical to a pre-mutation copy and both
tests re-run green.

**Single-source property survives, and it survives on the dimension the refactor newly opened.**
The refactor moved `known` from being computed inside `unknown_template_message` to being
supplied by each caller — so the two surfaces can now diverge on the *list* as well as on the
*wording*. The fixer's own mutation (trailing space) only exercises the wording. Checked the
other dimension directly: mutating `generate_experiment` to pass `template_names(None)` instead
of `known` makes `test_generate_experiments_unknown_template_message_matches_validates` fail —

```
- s (known: cohort_local, generic)
+ s (known: generic)
```

— because that fixture's repo carries a local `cohort_local.py`. The equality test is therefore
live on both dimensions, and the fixer's Concern 4 is genuinely unreachable through the two
existing call sites. Reverted; test green.

**No second silent no-op monkeypatch.** `grep`ped every `monkeypatch.setattr` in `tests/`
touching a template symbol: the only registry-lookup patch in the suite is
`test_a_template_cross_field_rule_is_reported`'s, now repointed to `resolve_template`. Proved it
still bites: `RuleBreaker.validate` → `[]` fails the test at `assert 'E-TEMPLATE-RULE' in set()`.
Reverted; test green.

**No third message-builder.** `unknown_template_message` is the only site producing that wording
in `src/`, and both emitters read it. `get_template`/`template_names` remain, and no remaining
`src/` site pairs them the way the defect did.

## I2 — a load fault preempts the collision verdict

**Closed, and the replacement prose does not over-claim.**

**Every site now says something true**, and the preemption is what the code does — measured at
`c0df967` rather than carried over from the earlier review:

| Fixture | Result |
|---|---|
| `a.py` broken + `b.py`/`c.py` claiming one name | `E-TEMPLATE-LOAD` (no collision) |
| `b.py`/`c.py` only | `E-TEMPLATE-COLLISION` |
| `a.py` broken + a local shadow of `generic` (through `registry._merged`) | `E-TEMPLATE-LOAD` |
| the shadow alone | `E-TEMPLATE-COLLISION` |

So the new `E-TEMPLATE-COLLISION` clause ("a file in the same directory that fails to load
preempts this code") is true for *both* halves that code covers — the two-local case and the
shadow-of-`generic` case raised one level up in `_merged` — which is more than the clause had to
survive.

**No fifth site.** Swept every tracked file (filtering the file list, never the output) for
`masked`, `is still found`, `both are found`, `files that did/do load`: the only surviving
`masked` is `tests/test_validate.py:6571`, an unrelated sweep-refusal docstring. The fourth site
the fixer found on its own — `discover_local`'s "Import order therefore never decides which
template wins; both are found and the collision is named" — is genuinely a fourth instance the
review missed, and is qualified now.

**The fixer's rejection of the review's proposed wording is right.** "The collision is still
computed over a complete set of claims" would have been false in the same direction: `claims` is
populated and then never read, so under a load fault no collision verdict is computed at all.
The text now separates what eagerness buys (no well-formed template silently skipped) from what
the ordering costs (no collision reported until the directory loads clean), which is what the
code does.

## I3 — two ordering guarantees, now falsifiable

**Closed.** All four mutations run in `discover_local` (where the behaviour lives),
`__pycache__` cleared before each, each confirmed **failing on the intended assertion** rather
than merely turning the suite red:

| Mutation | Test | Failure |
|---|---|---|
| `sorted(claims)` → `list(claims)` | `test_the_colliding_name_reported_is_the_first_in_name_order` | reports `zzz`, expected `aaa` |
| `sorted(claims)` → `reversed(list(claims))` | same | reports `mmm`, expected `aaa` |
| `glob("*.py")` sort → `reverse=True` | `test_the_broken_file_reported_is_the_first_in_the_sorted_walk` | reports `zzz_broken.py`, expected `aaa_broken.py` |
| `raise load_faults[0]` → `load_faults[-1]` | same | reports `zzz_broken.py`, expected `aaa_broken.py` |

The three-name fixture is doing exactly the work claimed: `zzz`/`mmm`/`aaa` are three *distinct*
observed answers, so one fixture kills both mutants. The fixer's account of why two were
insufficient is confirmed by the arrangement itself. Reverted by editing back (file
byte-identical to a pre-mutation copy), verified by behaviour — both tests green.

## Minors

- **M1** — verified against `hashes.py` before accepting the prose: `_SKIP_DIRS` contains
  `__pycache__`, `_SKIP_SUFFIXES` contains `.pyc`/`.pyo`, both applied unconditionally, and
  `code_hash`'s own docstring says it reads the working tree. The scaffolded `.gitignore`
  (`scaffold.py:13-14`) carries `__pycache__/` and `*.py[cod]`. The two mechanisms are now
  separate sentences and the follow-on says the hand-assembled repo goes dirty *while its
  `code_hash` is unchanged*. Accurate, and no private symbol named in normative prose.
- **M2** — `| Template is installed |` → `| Template resolves |`; no survivor of the old string
  in any tracked file. No row was inserted or removed by this diff, so no count phrase or
  sibling reference moved.
- **M3 — the fixer's correction to the review's diagnosis holds.** `drain_pending` has exactly
  two consumers in `src/`: `_import_file` (after `exec_module`) and `discover_local` (top of
  function, plus the two `except` branches). `_import_file` is only ever reached from inside
  `discover_local`'s loop, i.e. after that function's own drain. So the review's stated harm —
  "a stale registration queued for the *next* repo's discovery to inherit and misattribute" — is
  unreachable under either the pre-fix or post-fix arrangement, because the next `discover_local`
  drains before its loop either way. The real defect was the unconditional promise over a
  conditional path, and asserting the buffer directly is the right shape: mutation (drain moved
  back below the `is_dir` return) fails the new test at
  `assert [('stale', <Stale>)] == []`. Reverted; test green.
- **M4** — the scoping is right by construction: `sys.path[:] = before_path` sits in
  `_import_file`'s `finally`, so the path is restored before `_import_file` returns and therefore
  before any method of the registered class can be called.
- **M5** — the added clause is accurate at both consequences it names: a class defined under
  `src/**` is never stamped (`_is_local` asks where the *defining* module sits), so
  `materialize.py:93` writes the ` v{TEMPLATE_VERSION}` header clause for it and
  `validate.py:720` does not take the local early return. Written as what the predicate does and
  which way it fails, not as a claim it is the right answer.

## Mechanical pass

`docs/reference.md` is the only edited `*.md`. Over the four documents, fenced blocks skipped:
every relative link and `#anchor` resolves (with a slugger that preserves underscores — a naive
one reports false positives on `derive_seed`/`reuse_from` anchors), no duplicate heading anchor,
every table row matches its header's column count with `\|` accounted for, no trailing
whitespace, tab, or invisible unicode, no `x` used as multiplication. The two rewritten error
rows and the rewritten § Templates paragraph are all in-place edits — no row moved, so nothing
positional needed rechecking.

## Minor findings from this re-review

Neither changes behaviour; both are single-clause edits in comments the two relevant commits
were themselves rewriting. Recorded as findings rather than observations because the standing
rule — a fix that introduces a new over-claim is worse than the original — is stated absolutely,
and both clauses sit in the commits whose job was to remove over-claims.

**A — `discover_local`'s rewritten first paragraph strengthens the claim it replaced**
(`b4941e6`, the I2 commit). Old: "both are found and the collision is named." New: "so both
claimants are found, and **both are named**." Under stacked decorators on one class the message
names one provider plus "twice by the same class" — verified by probe. The counter-reading is
real and I weighed it: the sentence's own preceding clause scopes it to "a collision between two
local templates", the stacked case is one file, and two identical `path::ClassName` strings are
one claimant rather than two — so within its stated scope the clause is true, which is why this
does not block. It is still a strengthening made inside an over-claim fix, and the wording that
is unambiguously true costs one word: **"every distinct claimant is named"**. The same
docstring's final paragraph already carries that precise version ("naming every provider that
claimed it"), as does `LocalTemplate`'s docstring.

**B — `c0df967`'s trim stopped one clause short.** The comment it edited still opens: "A repo
with no `templates/` is the case that **inherits without discarding**". Nothing inherits on that
path — `discover_local` returns `{}` without reading the buffer, and no later call inherits
either, which is the very reasoning `c0df967`'s message gives for deleting the clause after it.
The residual "inherits" is the last word of the wrong diagnosis the commit set out to remove.
The accurate statement is the one the rest of the comment already makes: the drain is this
function's contract on a shared module-level buffer, so it must hold on every path out. The
sibling test docstring was trimmed cleanly and needs nothing.

## Cross-document classes

Vacuous for this diff, stated rather than assumed: no worked-example value, no `config.yaml`
field, no enum comment, no schema field named in prose, no declared-versus-derived passage and
no version number is touched. `docs/reference.md`'s three edits are two in-place error-table row
rewrites and one § Templates paragraph, all describing behaviour this branch already shipped.

## Method notes

Mutations were run where the behaviour lives, `__pycache__` cleared before each run, and each
failure attributed to a named assertion before being counted. Reverts were by editing the file
back from a copy taken before mutating — never `git checkout` — and each was verified **by
behaviour** (the named tests re-run green) and then by a byte-identical diff against the
pre-mutation copy. Sweeps filtered the file list, never the output. I1 was additionally measured
by a side effect the code under test writes, so the count does not depend on any patch target
being correct. Tree left clean at `c0df967`.
