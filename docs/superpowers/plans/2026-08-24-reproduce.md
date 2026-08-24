# H9c — `reproduce` — the plan

**Fifteen tasks in seven batches, every batch reviewed.** The design is
[`docs/superpowers/specs/2026-08-24-reproduce-design.md`](../specs/2026-08-24-reproduce-design.md);
its § numbers are cited, never its line numbers. Four controller rulings bind this slice — **Y**, **Z**,
**AA**, **BB** — and **each is restated inside every task section it binds**, because the ledger reaches
the controller and the reviewers and reaches no implementer. A ruling you find only in the design is a
ruling somebody will re-derive.

**Read before your task:** the design's § 0 (what was measured), § Corrections against the code below in
full, and the § 8 guard-pin row for any arm your task is allowed to touch. **If your task is not named as
an arm's sole authorized editor, you may not edit that arm — leave the branch red and say so.**

**Every task:**
- runs `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`, `uv run mypy` before reporting;
- reports **full-suite** mutation counts and says they are full-suite;
- greps every claim it makes about other code or other tests, **newline-insensitively**, and reports what
  it grepped and what each hit was, rather than a count. **Do not report zero disagreements** — six
  consecutive slices did and all six were wrong, and every one hid in a claim about *other* tests or
  *other* rows that a brief supplied as established fact.

---

## § Corrections against the code

Twenty-five, each measured at `a628707` and each with the method named. **A brief-supplied figure that
disagrees with one of these is wrong; grep before you trust either.**

1. **The scoping's H9c task 5 says "one git operation."** It is **two**: `git … clone` then
   `git -C <dest> checkout --detach <commit>`. § Reproducing on another device's *"The only git
   operation"* is about what the *user* typed, and the design keeps that reading while stating the count.
2. **`core.eol=lf` is not load-bearing and must not be passed.** Measured: under an ambient
   `core.autocrlf = true`, `core.autocrlf=false` alone gives the recorded `0cc6ddd`; `core.eol=lf` alone
   gives `d37416e`. H6a Ruling M's precedent is one arm per flag.
3. **A faithful clone's `code_hash` depends on `core.autocrlf`.** `d37416e` versus `0cc6ddd` on the
   identical commit. Stated in no document, no filing and no scoping.
4. **A tracked `.gitattributes` carrying `* text eol=crlf` makes it depend on how the working tree was
   materialized** — the clone hashes `d37416e` while the never-re-materialized original hashes
   `0cc6ddd`. **Out of reach by ruling** (design Decision 7) and filed.
5. **`provenance.environment` names `uv_lock` and no `pyproject.toml`**, though `run` writes
   `environment/pyproject.toml`. Decision 3 step 4 finds it by convention, not by record.
6. **A bundle member's `provenance.environment.uv_lock` is a dangling `environment/uv.lock`** — the path
   survives `study add` unredacted while the directory it points into is not in the bundle.
7. **The reader is `lineage.read_record_file`, never `read_run_record`.** The second takes a *directory*
   and appends `run.yaml`; a bundle member is `main.run.yaml` and is unaddressable that way. The first
   function's own docstring says this is why it exists.
8. **`templates.registry.get_template` returns `None` for an installed template.** `_claims` attaches
   `cls=None` to an entry-point claim and `_merged` keeps only claims with a class. A plugin is also not
   installed in `reproduce`'s interpreter — `uv sync` installs it into the clone's. So step 6's
   `required_env` list is unbuildable in-process for the plugin case.
9. **`hashes.covered_config` excludes `metadata`, `data.input_dir` and `data.output_dir`.** So a config
   written back with both paths blanked has the recorded `parameters_hash` **exactly**, which is what
   makes Decision 11's write-back self-checkable.
10. **`apparatus.Observations.record` followed by `.changed` already *is* the gate** — per condition,
    first-*answered*, tolerant of `null` in both directions, reflexivity-safe for `nan`. Do not write a
    comparison. `apparatus.replay_ledger` is the shipped precedent for reconstituting one from a file.
11. **Seeding the run's OWN `Observations` from the expectation is a defect, not a shortcut.** `record`
    bumps `_total_counts` and `_null_counts`, which feed `provenance.apparatus.unobserved` and
    `W-APPARATUS-UNANSWERED`, so the reproduction's record would claim probe calls it never made. Use a
    **second** `Observations`, asked only for `changed`.
12. **`STOP_CODES` and `APPARATUS_CODES` take opposite answers and both are pinned.**
    `E-APPARATUS-CHANGED` is in the first and **deliberately not** in the second, with the reason in
    `apparatus.py`'s own docstring. Copying either way without deciding is the copied-recipe fault.
13. **§ Reproducing on another device's *"it can't collide with an existing checkout"* is false.** A
    second `reproduce` of one record derives the same name. Decision 9 narrows the sentence.
14. **`provenance.git.remote: null` is the scaffold default, not an edge case.** Measured on a
    `publishable new` project with one local commit: `remote: null`, run exit `0`.
15. **`.env.example` is tracked**, so a clone already holds it — step 6's "copies `.env.example`" means
    `cp .env.example .env`, which is § The generated README's own setup line.
16. **`secrets.missing_env` treats an empty value as missing** and a bare key parses to `None` and is
    skipped, so a blank `.env` cannot turn a missing credential into a present one.
17. **`OPERATION_COMMANDS` has no shared count literal.** The arity arm is per-command: `resume` has
    three tests (no path, two paths, a flag) plus a `resume new` pin. `reproduce` needs its own four, as
    **additions**, and the flag test is the one the `len` half alone cannot cover.
18. **`_dispatch` evaluates the built branches before the `NOT_BUILT_COMMANDS` lookups**, which is the
    only reason adding a name to `OPERATION_COMMANDS` is safe — and **that order is filed as unpinned**
    (hoisting the lookups leaves the suite green). Do not rest a claim on it; assert the outcome.
19. **`hashes.code_hash(root, include)` does not hand back the file list.** Decision 2 prints the count
    and the list, so use `hashed_files(...)` then `code_hash_of(...)` — the pair form `code_hash_of` was
    extracted for exactly this.
20. **The `("reproduce", "NOT BUILT")` line in `test_reference_cli_tables_are_parsed_at_all` is a
    *marked row-presence probe*, placed there by H9b task 15 on purpose.** Flipping it to `built` without
    adding a probe for another `NOT BUILT` row deletes coverage the comment beside it names. Guard-pin
    arm B's post-edit state covers both halves.
21. **`main`'s `except PublishableError` handler uses no `Collector`**, so anything raised into it is
    printed **without the redaction pass** (measured by H9b's correction C3). Every refusal `reproduce`
    decides is printed through a fresh credential-bearing `Collector`, never raised into `main` — H9b's
    Decision 13, applied here.
22. **`uv lock` still fails in a scaffolded project**, re-measured 2026-08-24: *"Because publishable was
    not found in the package registry."* Decision 5's constraint is live, so **no fixture recipe may run
    `uv lock`** — a fixture's lockfile is written, not resolved.
23. **`identity.json` is not `reproduce`'s operand and must not be read.** It is a run-directory
    artifact for a *mid-run* reader; `run.yaml` carries all three figures, and a bundle has no
    `identity.json` at all, so using it would make the bundle form impossible.
24. **The run directory's `config.yaml` byte copy is not in a bundle either**, which is the second reason
    Decision 11 re-serializes from the record rather than copying it.
25. **`run.yaml`'s `config` is the parsed dict**, so a write-back loses every inline comment `init`
    wrote. Disclosed in the transcript with where the comments still live, rather than worked around.

---

## Task 1

**The guard pin, captured before anything else moves.** Build the seven arms of the design's § 8 exactly
as that table specifies, including the two re-authorizations, and prove **every** arm able to fail by a
mutation in **production** code.

**You are the only task in batch 1, and no later task may capture a pin.** Arms whose post-edit state the
design writes in advance (**B**, **C**) are captured **at their pre-edit state** here; you do not make
those edits.

Arms, and what to build versus cite:

- **A** — *cite, do not re-capture.* H9a arms A and B and H9b arm A already hold a completed `run`'s
  `run.yaml` leaf by leaf, its tree path by path, and its stdout. Name them by test function in your
  report. **Re-capturing would recreate H8a's *same list pinned twice*, which a later task then edited
  in both places.** Editor: **NONE**.
- **B** — the existing `assert ("reproduce", "NOT BUILT") in tables["Command"]`. **Do not edit it.**
  Record in your report that its sole authorized editor is **plan task 11** and that the post-edit state
  is `("reproduce", "built")` **plus** a new `assert ("list-templates", "NOT BUILT") in tables["Command"]`
  line (correction 20).
- **C** — `apparatus.STOP_CODES`'s set-equality assertion. **Do not edit it.** Sole authorized editor:
  **plan task 9**; post-edit set
  `{"E-APPARATUS-RAISED", "E-APPARATUS-CHANGED", "E-APPARATUS-UNEXPECTED"}`.
- **D** — the two shipped `APPARATUS_CODES` membership assertions. Editor **NONE**. Record that task 9
  may **add** a sibling assertion beside them and that adding one is not editing one.
- **E** — **build this one.** A whole-tree `{path → sha256}` map of (i) the run directory, (ii) the
  operand's own tree and (iii) the source repository, captured before and after a `reproduce`
  invocation, asserting ADDED/REMOVED/CHANGED all empty over each. Today `reproduce` is `NOT BUILT`, so
  capture it against the `NOT BUILT` invocation and **state in the docstring that task 11 makes it
  meaningful and that it must keep passing then** — that is the arm's whole job. Editor **NONE**.
  **Established by snapshotting, never by reading for absent `mkdir` calls** — H9a's `dry-run` arm is the
  precedent and *if a comment says nothing is created, make it create something* is the rule.
- **F** — **build this one if it does not exist; grep first.** The shipped assertion on
  `W-ENV-UNLOCKED`'s message containing *"`reproduce` will not be able to restore it"* is in
  `tests/test_cli.py`. If it exists, **cite it**; if the phrase is asserted only as a substring of a
  longer literal, add an arm that asserts *that clause* on its own. Editor **NONE** — Decision 5 affirms
  the warning, and this arm is what stops a later slice promoting it quietly.
- **G** — *cite, do not re-capture*, and list each cited test by name.

**Mutations required, each full-suite:** delete the write of `config.yaml` from `_execute_prepared`
(arm A's cited arms); remove `reproduce` from `NOT_BUILT_COMMANDS` (arm B); delete `E-APPARATUS-RAISED`
from `STOP_CODES` (arm C); add `E-APPARATUS-CHANGED` to `APPARATUS_CODES` (arm D); make the `NOT BUILT`
path `mkdir` one directory under the operand's parent (arm E); change `W-ENV-UNLOCKED`'s message text
(arm F).

**Must not touch:** `src/` except to mutate and revert; any test file's existing assertions; the four
documents. **Never `git checkout -- <file>` to revert a mutation** — keep a copy and verify the revert by
**behaviour**, not by `git status`.

---

## Task 2

**Ruling Y, and the operand reader.** Build `src/publishable/reproduce.py` with the operand
discrimination and its refusals, and nothing else. Nothing is written to disk by this task.

> **RULING Y (binding, restated here):** `reproduce` takes a path and nothing else, and it does **not**
> resolve a target device. *"Reproducing on another device"* names where the user is, not an argument, so
> `reproduce` runs **on** the other device against a record it is given. No `--into`, no host, no user, no
> key, no behaviour-changing environment variable. **Cost if wrong:** a user with a bundle cannot
> reproduce from it, which is the case `study` exists to serve — so the bundle-member form is a
> first-class arm, not a note.

The discrimination is **structural, never by basename** (design Decision 1). A bundle member is
`main.run.yaml`, so `endswith("run.yaml")` is the reserved-name proxy this repo has already paid for at a
`report_by` stratum:

```python
def classify_operand(path: Path, c: Collector) -> "Operand | None":
    """One YAML parse, then three structural questions. See the design's
    Decision 1.

    NOT by basename: a bundle member is `main.run.yaml` (measured — the
    bundle `study add` writes holds `study.yaml` and `main.run.yaml` and no
    directory), so a basename test refuses the form Ruling Y exists for.
    """
    if path.is_dir():
        # E-REPRODUCE-OPERAND, naming `<path>/run.yaml`. `resume` is the one
        # command that takes a directory, and giving `reproduce` the same
        # operand for the opposite action is the confusion this refuses.
        ...
    doc = <parse; a read or parse failure is E-IO-FAILED, `diff`'s and
           `resume`'s precedent, not a code of this slice's own>
    if not isinstance(doc, dict):
        ...  # E-REPRODUCE-OPERAND
    if "study" in doc or "members" in doc:   # read study.py for the real key
        ...  # E-REPRODUCE-BUNDLE, LISTING the member names
    if "run_id" in doc:
        return Record(read_record_file(path), path)   # correction 7
    if "provenance" in doc or "results" in doc:
        ...  # E-REPRODUCE-OPERAND — an edited record, NOT read as a config
    if "experiment_type" in doc:
        return ConfigOperand(path)
    ...  # E-REPRODUCE-OPERAND
```

**Read `src/publishable/study.py` for the bundle root's actual key set before writing the
`E-REPRODUCE-BUNDLE` branch** — do not guess it from `study.yaml`'s documented example, and report what
you read.

**Every refusal goes through a fresh credential-bearing `Collector`, never raised into `main`**
(correction 21, H9b Decision 13): `main`'s handler applies no redaction pass.

**Fixture S**, five arms — a run directory, a `study.yaml` (a bundle with **two** members, because a
one-member bundle cannot distinguish *lists members* from *names the first*), a `run.yaml` with `run_id`
deleted, a YAML list, a missing path.

**Mutations:** discriminate by basename (caught by a bundle-member arm — build a minimal one here and
hand the full Fixture F to task 3's batch); read a `run_id`-less mapping as a config (Fixture S arm 3 —
its file has `provenance` and `results`, so the two readings genuinely differ); print the member
**count** instead of the names (Fixture S arm 2 — two members, so a count and a list differ).

**Must not touch:** `cli.py`'s dispatch (task 11), `lineage.py`, any guard-pin arm, the four documents.

---

## Task 3

**Rulings Y and Z, and the clone.** The destination derivation, its two refusals, and the two git
invocations.

> **RULING Y** as restated in task 2 — the destination is **derived**, never given. **RULING Z
> (binding, restated here):** a hash that differs must say **which input moved**, never guess **why**.
> Every verdict `reproduce` prints must be derivable from what it compared; if it cannot tell two causes
> apart, it **says so**. **Cost if wrong:** a confident wrong diagnosis is worse than an honest unknown,
> and this repo has shipped four sentences that invented a cause.

Destination: the remote URL's last component with a trailing `.git` removed, then `_`, then `run_id` —
`my-study_run_2026-08-06T14-02-11Z_8e21ab3/`, § Reproducing on another device's own worked example —
created relative to the working directory. **`provenance.git.repo_root` is not an input**: it is
`<redacted by study add>` in a bundle (correction 6's sibling measurement), and the remote is the only
name that travels in both forms.

Two refusals (Decision 9): `E-REPRODUCE-DEST-EXISTS` if it exists; `E-REPRODUCE-DEST-IN-REPO` if it
resolves inside a git repository, the walk-up being `find_repo_root` **from the destination's parent**.
`E-REPRODUCE-NO-REMOTE` at exit `1` when `provenance.git.remote` is `null` — correction 14 says that is
the scaffold default, and the message must name the recorded `git.commit` so a reader who has the
repository can check it out themselves. **Exit `1`, not `5`**: `5`'s row is *"a clone or `uv sync` that
**failed**"* — a clone that was attempted — and keeping `1` here preserves `5` as the retry class.

```python
_CLONE_CONFIG = ("-c", "core.autocrlf=false")
# ONE flag, measured (§ Corrections 2 and 3): under an ambient
# `core.autocrlf = true`, `core.autocrlf=false` alone gives the recorded
# `0cc6ddd` and `core.eol=lf` alone gives `d37416e`. H6a Ruling M's
# precedent is ONE ARM PER FLAG, so a second flag with no arm is a flag
# nobody can prove is doing anything.
#
# The ground for neutralizing at all is H6a Ruling F's own: a rule that
# does not travel with the tree cannot define the tree's identity. Ruling M
# declined to neutralize `core.autocrlf` FOR THE DIRTY GATE, and the H6a
# ledger states the distinction in as many words -- a gate answers "may
# this run proceed here", which is local by nature; a hash answers "is this
# the same code", which is not. `reproduce` is not a gate.
#
# NOT neutralized: `core.excludesFile` (the `.gitignore` files that decide
# `code_hash` are TRACKED and travel with the commit -- measured: 6 files,
# the same six, on both sides), and a tracked `.gitattributes`, which is out
# of reach BY RULING (design Decision 7) and is one of Decision 2's
# enumerated candidate causes instead.
subprocess.run(["git", *_CLONE_CONFIG, "clone", *_CLONE_CONFIG, remote, str(dest)], ...)
subprocess.run(["git", "-C", str(dest), "checkout", "--detach", commit], ...)
```

**Both placements, and each has its own job** (correction 1): the leading `git -c` fixes the **initial**
checkout, where the conversion happens; `clone -c` **persists** it into the new repo's `.git/config` so a
later `git checkout` in the prepared tree does not re-convert. Measured: `clone -c` alone stored `false`
and still produced CRLF.

A failed clone is exit **`5`** — `EXIT_EXTERNAL` gaining its first reader for that half of code `5`'s
documented meaning.

**Fixtures A, C, E, K, T.** Fixture A's remote is a **local bare repo** (`git clone --bare`, then
`git remote add origin <path>`): a fixture that reaches the network fails on a build machine, and `git
clone` treats a path and a URL identically. **Fixture A's `uv.lock` is written, not resolved**
(correction 22).

**Mutations:** drop `-c core.autocrlf=false` from the clone (Fixture E arm 1 — `0cc6ddd` → `d37416e`);
drop it from the leading `git -c` only (arm 2 — measured to still produce CRLF); add `core.eol=lf`
(arm 3, which asserts the **flag list**, because § 0.4 shows the flag changes nothing so a hash assertion
would be blind); walk up from the operand rather than the destination's parent (Fixture T arm 2, whose two
paths are in **different** repositories by construction). **Named blind in advance:** neutralizing
`core.excludesFile` — a fresh clone has no untracked exclude rule for the flag to reach. **Owed
replacement:** arm 3's structural assertion that the invocation's flag list is exactly `_CLONE_CONFIG`.

**Must not touch:** `provenance.py`'s `_NEUTRALIZED_CONFIG_ARGS` — it belongs to the gate and the hash
predicate, answers a different question, and sharing it would be the copied-recipe fault. `hashes.py`.

---

## Task 4

**Ruling Z, and `code_hash` in the checkout.**

> **RULING Z (binding, restated here):** a hash that differs must say **which input moved**, never guess
> **why**. The scoping measured that this step would report an H6a-boundary difference as *"a rewritten or
> force-pushed history"* — a cause invented from a symptom. H6a's Ruling C already pays for it: `uv.lock`
> is the carrier and a core upgrade moves `code_hash` for identical code. **Every verdict must be
> derivable from what was compared; if two causes cannot be told apart, say so.** **No marker may be
> minted** — H6a Ruling C, and the scoping's § 12 names it.

Recompute with **exactly** `command_run`'s predicate, in the pair form so the file list is available
(correction 19):

```python
pairs = hashes.hashed_files(dest, lambda cands: unignored_under_hashed_trees(dest, cands))
computed = hashes.code_hash_of(pairs)
```

Equal → one line, with the file count. Different → `E-REPRODUCE-CODE-HASH` at exit `1`, **the checkout
kept**, and the output carries: the recorded digest, the computed digest, the file count, the file list,
the checkout path, and **this closed enumeration of causes it cannot separate** —

- the code at that commit really is different: a rewritten or force-pushed history;
- the record predates H6a's redefinition of which files are hashed, which **no key in `run.yaml` can
  date** (`schema_version` was deliberately not bumped, and a scaffolded project's `uv_lock_hash` is
  `null`, so the carrier may be absent);
- this machine's git materialized the tree differently — `core.autocrlf`, which the clone neutralizes,
  or a tracked `.gitattributes`, which it may not.

**Naming a closed candidate set is not a verdict; picking one is.** The output must not contain a
sentence asserting a single cause.

**`draft: true` declines rather than fails** (Decision 10): print *"this record is a draft: its code was
not committed, so `code_hash` is not verified"* and continue — the posture § Reproducing already takes for
the config form, which *"cannot verify a `code_hash` and says so, rather than reporting a match it never
made."* **This is the one cause `reproduce` names, and it is named because the record names it.**

**Fixtures C, D**, plus a `draft` arm on Fixture B. **Fixture C's literal is computed by calling
`code_hash_of` in the test, never hard-coded** — a commit SHA and everything derived from it cannot be a
stable literal, and H9a's self-caught defect was an arm compared against its own read-back.

**Mutations:** compare with `include=None` instead of the git-aware predicate — caught by a **Fixture C
arm carrying a git-ignored file under `src/`**, where the two predicates give `0cc6ddd` and `bdf2ce9`;
**without that ignored file the two agree and the mutation is blind**, which is exactly how a fixture
whose numbers agree with the bug happens. Report the single-cause phrase (Fixture D asserts the
enumeration is present **and** that a single-cause sentence is **absent** — an assertion on the code alone
passes under both wordings). Refuse a draft instead of declining (the draft arm: one path exits `1` before
the closing transcript, the other reaches it at `0`).

**Must not touch:** `hashes.py`, `provenance.py`, `run_record.py`, `reference.md`.

---

## Task 5

**Ruling AA, and the lockfile ranking.**

> **RULING AA (binding, restated here):** the two lockfile sources are **both real** and `reproduce` must
> not prefer silently. Measured: a run records an **untracked** `uv.lock` into `environment/uv.lock`
> while `git clone` of the recorded commit has **none** — the dirty gate's pathspec is the hashed trees
> only. Decide which it restores from, and **make the other one's absence or disagreement a reported fact
> rather than a silence.** **Cost if wrong:** an environment restored from the wrong lockfile reproduces
> numbers nobody can trace.

Design Decision 3's ranking, in order, each step printing what it found:

1. `uv_lock_hash` is `null` → `E-REPRODUCE-UNLOCKED`, exit `1`, **checkout kept** (task 6 owns the
   ruling; this task owns the branch).
2. The byte copy is reachable — `environment/uv.lock` **beside the operand**, i.e. the run-directory form
   → check its sha256 against `uv_lock_hash` (`E-REPRODUCE-LOCKFILE-EDITED` if it fails), copy it into
   the checkout, and report the clone's own lockfile as *absent* / *identical* / *DIFFERS*. **Never
   overwrite without the line.**
3. Unreachable — the bundle form (correction 6: the recorded path is a **dangling** reference) → the
   clone's committed `uv.lock` is used **iff** its sha256 equals `uv_lock_hash`, and the line says so.
   Otherwise `E-REPRODUCE-LOCKFILE-UNREACHABLE`, exit `1`, checkout kept, the message naming **both**
   the recorded digest and what the clone holds.
4. `environment/pyproject.toml`, where reachable, compared against the clone's byte for byte and reported
   *identical* / *DIFFERS* — **before** `uv sync`. It is **not copied in** (it is a tracked file at the
   recorded commit, and overwriting the commit's own manifest with an uncommitted edit would make the
   checkout a tree that exists nowhere) and it **does not refuse**: it is the input that explains a
   `uv sync --locked` failure a reader would otherwise guess at. Correction 5: `provenance.environment`
   names no `pyproject.toml`, so this file is found by convention, not by record.
5. `uv sync --locked` in the checkout. Failure → exit **`5`**.

**Fixtures G, H, I, J, L.** **Fixture H is not optional**: without a bundle whose lockfile *is* committed,
Fixture G proves only that something refused, and *"a bundle can never sync"* and *"a bundle syncs when
the lockfile travels with the commit"* stay indistinguishable. **Fixture I's two lockfiles differ by
construction**, which the single-lockfile fixtures cannot supply. **Fixture J asserts the `DIFFERS` line
AND its position before the `uv sync` line** — the ordering is the whole point of step 4.

**Mutations:** prefer the clone's lockfile over the byte copy (Fixture I); use the byte copy without
checking its digest (a Fixture I arm with the copy edited after the run); accept the clone's lockfile in
the bundle form without comparing digests (Fixture G, with H as the success control); skip the
`pyproject.toml` comparison (Fixture J).

**Must not touch:** `uv_support.py`'s `uv_lock_info` (it answers *what does this repo hold now*, which is
a different question), `run_record.py`, guard-pin arm F.

---

## Task 6

**Ruling AA's two remaining questions, decided.** Q1 (the missing lockfile) and Q3 (`uv_lock: null`) —
design Decisions 5 and 6. This is a decision-and-documents task with one branch of code.

> **RULING AA** as restated in task 5. Q1 and Q3 are the two questions the spine's charter row said this
> slice exists to decide, and the scoping's § 3 named them.

**Q1: affirm `W-ENV-UNLOCKED`, do not promote it.** Re-measured 2026-08-24 and you must re-measure it
again yourself and report the output: `uv lock` inside a `publishable new` project fails — *"Because
publishable was not found in the package registry"* — so promoting the warning would refuse **every run
of every scaffolded project**. The constraint is a bootstrapping fact about this repository's publication
state, not a principle.

`docs/design-principles.md` § Design goals gains the footnote **the filing itself proposes**: *"not
optional" describes `reproduce`'s obligation, not `run`'s.* That sentence becomes true only because of
Q3's answer, so write them together.

**Q3: `uv_lock_hash: null` → `E-REPRODUCE-UNLOCKED`, exit `1`, after the clone, checkout kept**, closing
transcript printed with the `uv sync` line replaced by the stated gap. Exit `1` because nothing outside
the machine refused and `5`'s class is the one you retry. The checkout is kept because a stop that
discards its own artifacts is the fault H9b closed at exit `4` — H7d Part B's *a stop must be legible from
the artifacts*.

**The strongest available ground, and you must cite it rather than re-argue it:** `W-ENV-UNLOCKED`'s
shipped message already reads *"`reproduce` will not be able to restore it"*, and it is asserted in
`tests/test_cli.py`. Decision 6 is that sentence coming true. **Guard-pin arm F pins it and you may not
edit arm F.**

**`spec-defects.md`:** strike *Whether a missing `uv.lock` should refuse the run instead of warning is
unresolved* — the oldest H9-owned entry — with the decision and its date. **Leave the sibling entry open**
(*a scaffolded project cannot resolve a lockfile until `publishable` is published*): its retirement
condition is a release, not a slice. **Task 14 owns every other filing; this one is yours because the
decision and the filing are one act.**

**Fixture L**: asserts the code, exit `1`, **and that the destination exists and holds the checked-out
tree**. A refusal arm asserting only the code would pass identically if the checkout were discarded, which
is the behaviour this decision exists to specify.

**Mutation:** discard the checkout on `E-REPRODUCE-UNLOCKED` (Fixture L — the existence assertion is what
sees it).

**Must not touch:** `W-ENV-UNLOCKED`'s message or condition, guard-pin arm F, `reference.md` § Warnings
core reports.

---

## Task 7

**The config write-back.** Design Decision 11.

Write `configs/<name>/config.yaml` in the checkout by **re-serializing the record's embedded config**,
with `data.input_dir` and `data.output_dir` blanked and each marked
`# REQUIRED: set to your local copy`.

**Not from the byte copy, for three measured reasons** — it does not exist in the bundle form
(correction 24); locating two keys inside arbitrary YAML text to blank them is a text scan over a
structure, which is the proxy this repo keeps paying for; and where the record's config and a byte copy
disagree, the record is what produced the numbers. § Reproducing on another device says the paths are
*"blanked and **marked**"*, and core writing a comment means core is generating the YAML.

**The write is self-checked, and this is the task's central assertion.** `hashes.covered_config` excludes
`metadata`, `data.input_dir` and `data.output_dir` (correction 9), so:

```python
written = yaml.safe_load(target.read_text())
if hashes.parameters_hash(written) != record["parameters_hash"]:
    ...  # E-REPRODUCE-CONFIG-WRITEBACK, exit 1
```

**Blind to the blanking, sensitive to a lossy round trip** — a re-serialization that drops or retypes a
key moves the hash. That is the two branches that can differ, and it was checked in advance.

**Two reported facts, neither a refusal.** `parameters_hash` over the clone's own committed
`configs/<name>/config.yaml` (a pure function of the file — § CLI reference says so of `diff`), reported
*identical* or *DIFFERS* beside the recorded `provenance.git.config_committed`; a `DIFFERS` under
`config_committed: true` is a real fact about the record. And the comment loss (correction 25) is
disclosed, naming where the comments still live: the run directory's own `config.yaml` in the
run-directory form, and **nowhere** in the bundle form.

**Fixture M**, two arms. **The second arm is what makes the comparison non-vacuous**: with
`config_committed: true` and no edit, `identical` is the answer whether the code compares anything or not.

**Mutations:** write the config from the byte copy (Fixture F — the bundle form has none, so the mutation
cannot produce a config there at all); skip the `parameters_hash` check (a Fixture M arm whose record's
`config` has one key retyped by the fixture, so the round trip is lossy on purpose).

**Must not touch:** `hashes.py`, `run_record.py`, `validate.py`.

---

## Task 8

**Step 6, narrowed: `.env` and `required_env`.** Design Decision 12.

`.env.example` is **tracked** (correction 15), so the clone holds it: write `.env` from it **only when
`.env` does not exist**, never overwrite one, and say which happened. Safe by correction 16 —
`missing_env` treats an empty value as missing. When `.env.example` is absent, say that instead.

**`required_env` is listed only for a template this interpreter can construct** — core's `generic`, or a
project-local `templates/**` discovered by path **in the checkout**. Correction 8 is why: `get_template`
returns `None` for an installed template, and a plugin is installed into the **clone's** environment by
`uv sync`, not into this one. For a plugin-provided template the transcript **names the template and its
plugin and defers to the `validate` line it already prints** — `validate` in the prepared checkout
already reads `required_env` (H7c gave it that reader) in the interpreter where the plugin exists. **This
is a document narrowing and § Reproducing on another device's step 6 must say so** (task 13 owns the
prose; you own the measurement it rests on and must hand it over explicitly).

**Resolving a project-local template imports user code. The containment is copied WHERE IT SITS, not
what it calls.** `report`'s shipped credential leak came from lifting `freeze`'s calls without the `try`
they sit inside, and the sibling that already got it right is `report.render_with_override` — **read it
before writing this**. Two rules, both `CLAUDE.md` § Misreadings entries with this repo's scars on them:

- the whole resolution sits inside the credential-bearing `try`, so a template raising at import becomes
  a redacted diagnostic rather than reaching `main`'s un-redacted printer (correction 21);
- the `sys.path` entry is removed **by identity**, never `pop(0)` — user code runs inside that window by
  design, and an override doing its own `sys.path.insert(0, …)` makes a positional pop remove the wrong
  entry. The restoration is pinned **on the failure path**.

**Fixture R**, plus its `pop(0)` arm whose project-local template does its own `sys.path.insert(0, …)` at
import. **The credential is declared through `Param(requires_env=)` and set in the environment**, so the
redaction has a real value to match — an undeclared one passes vacuously. The positive control is the one
that caught the original: `validate` over the identical project printing `<redacted:…>`.

**Mutations:** copy the calls without the enclosing `try` (Fixture R — one path prints the credential
verbatim, the other `<redacted:…>`); remove the `sys.path` entry with `pop(0)` (the inserting-template
arm; **without that template the two are indistinguishable**, which is the fixture the shipped defect
lacked).

**Verify through the real console script.** A credential leak is invisible to a direct call that never
reaches `main` — *a probe proves the moment; a test proves tomorrow*, and both are required here.

**Must not touch:** `secrets.py`, `report.py`, `templates/discovery.py`, `templates/registry.py`.

---

## Task 9

**Ruling BB's second half: `run`'s first probe compares against `apparatus.expected.json`.** **This is
the behaviour change to a shipped command.** Guard-pin arm C's sole authorized editor is **this task**.

> **RULING BB (binding, restated here):** `apparatus.expected.json` is a **comparison, not a gate** — for
> `reproduce`. On another device the apparatus will differ, and that is expected rather than exceptional:
> a GPU model, a hostname, an OS. So **`reproduce` reports apparatus differences and does not refuse on
> them**, while **the run it then performs is an ordinary `run` under the ordinary gate**. **Cost if
> wrong:** either a reproduce that cannot run anywhere, or one whose numbers came through an apparatus
> nobody recorded. Task 10 owns `reproduce`'s half; **this task owns the ordinary gate's half**, which is
> where the comparison actually happens, and § Reproducing on another device is explicit that the first
> probe *"fails on any difference, at the same volume as a lockfile mismatch"*.

**Do not write a comparison** (correction 10). `Observations.record` followed by `.changed` **already is**
the gate — per condition, first-*answered*, `null → value` and `value → null` both passing,
reflexivity-safe for `nan` — and `apparatus.replay_ledger` is the shipped precedent for reconstituting one
from a file:

```python
def expectation_from(path: Path) -> apparatus.Observations:
    """The recorded facts as an `Observations`, so the SHIPPED gate is the
    comparison (§ Corrections 10). Never a `!=`: `null -> value` passing is
    what § Reproducing on another device calls "more evidence rather than
    less", and `_unchanged` is what keeps a constant `nan` from
    contradicting itself.

    A SECOND object, asked only for `changed`. Seeding the run's own
    `Observations` -- the shape `Resumed.baseline` uses, where the counts
    were real probes -- would bump `_total_counts`/`_null_counts` and make
    `provenance.apparatus.unobserved` and `W-APPARATUS-UNANSWERED` claim
    probe calls this run never made (§ Corrections 11). That is the mutation
    Fixture Q exists to catch, and it is what a naive implementation IS.
    """
```

**A distinct code, `E-APPARATUS-UNEXPECTED`, because the remedy is distinct.** `E-APPARATUS-CHANGED`
means *the apparatus moved during this run — stop*; this one means *this apparatus is not the recorded one
— accept that this is not a reproduction, or edit `apparatus.expected.json`, which § Reproducing says you
may*. One code covering both would be H4d's *one code, five faults* again.

**Memberships, and they are opposite** (correction 12):

- `STOP_CODES` **gains** it → post-edit set `{"E-APPARATUS-RAISED", "E-APPARATUS-CHANGED",
  "E-APPARATUS-UNEXPECTED"}`. **This is guard-pin arm C and you are its sole authorized editor: one
  member added, none removed, nothing reordered, matching the design's advance spec byte for byte.**
- `APPARATUS_CODES` does **not** — the loop breaks on a `STOP_CODES` member before `command_run`'s
  containment filter is reached, which is `E-APPARATUS-CHANGED`'s own documented reason. **Arm D's two
  shipped assertions have editor NONE**; you may **add** a sibling
  `assert "E-APPARATUS-UNEXPECTED" not in APPARATUS_CODES`, and adding an assertion is not editing one.

**No exit code is minted:** `1` before the first execution, `4` once there are results, from
`run_status`'s shipped fold — the same derivation H9b recorded, not a choice.

**The file's location is `<config_dir>/apparatus.expected.json`**, which § Reproducing specifies. It sits
outside `src/**` and `templates/**`, so neither `code_hash` nor the dirty gate sees it — and the ground
is a **measurement**, not the pathspec: an untracked `uv.lock` at a repo root left
`git status --porcelain` reading `?? uv.lock` and the run exiting `0` (design § 0.1). Reasoning from the
pathspec alone would be answering with a proxy.

**Fixtures P and Q. Fixture P's four arms cannot be collapsed**: a moved value fails, `null → value`
passes, `value → null` passes, and a fact present for one condition and absent for the other is compared
per condition. **Three of the four are the tolerance § Reproducing calls *"more evidence rather than
less"***, and a fixture with only the failing arm leaves every tolerance untested. **Fixture Q is the arm
that catches this task's rejected alternative**: seeding the run's own `Observations` inflates
`unobserved.total_probes` while every arm of P stays green.

**Mutations:** compare with `!=` (P arms 2 and 3); compare against the whole `facts` rather than per
condition (P arm 4 — P has two conditions with **different** facts); reuse `E-APPARATUS-CHANGED` (P arm 1,
which asserts the identifier); add the code to `APPARATUS_CODES` (arm D's addition plus P arm 1); remove it
from `STOP_CODES` (P arm 1 — the run would finish `completed`); seed the run's own `Observations`
(Fixture Q).

**Must not touch:** `Observations.record`, `.changed`, `.facts_document`, `.unobserved`,
`.warn_unanswered`, `replay_ledger`, or `Observer`'s existing signature beyond one optional parameter.
Arm A's cited arms must stay green: **no run without the file may change in any way.**

---

## Task 10

**Ruling BB's first half: `reproduce` writes the expectation and refuses nothing on apparatus grounds.**

> **RULING BB** as restated in task 9. **This task's half is the writer.** `reproduce` **probes nothing,
> compares nothing and refuses nothing** on apparatus grounds — it is not one of the four places a probe
> runs, exactly as `diff` is not, and for the same reason: no config resolved against a plugin it does not
> have.

When `provenance.apparatus` is non-`null`, write `configs/<name>/apparatus.expected.json` — the recorded
`facts` mapping **verbatim**, condition key to fact mapping — **once**, refusing to overwrite an existing
one (`E-REPRODUCE-EXPECTED-EXISTS`) rather than replacing it, and print the block § Reproducing on another
device already specifies:

```
This run measured through an apparatus. Reproducing it needs:
  llm_deployment   model_revision  gpt-5.5-2026-06-11
                   api_version     2026-05-01
```

**`provenance.apparatus` gains no key naming the expectation**, and H6a Ruling C's refusal of a definition
marker is the precedent: the reproduction's record carries what it **observed**, and a key naming what it
was compared against is a second source of truth for a comparison the checkout's own file already holds.
Disclosure item 4.

**Fixture O.** The template is **project-local** with a real installed probe distribution, and
`provenance.apparatus.facts` **has two conditions with different facts** — one condition cannot tell a
per-condition write from a flattened one. Arm 2 is the second `reproduce` into a destination already
holding the file.

**Mutations:** overwrite an existing file (O arm 2); flatten the per-condition mapping (O arm 1, which
asserts mapping for mapping).

**Must not touch:** `apparatus.py`, `run_record.py`'s `provenance` assembly, guard-pin arm G's cited
`provenance` key-list arms.

---

## Task 11

**Dispatch.** `reproduce` joins `OPERATION_COMMANDS` and leaves `NOT_BUILT_COMMANDS`. **Guard-pin arm B's
sole authorized editor is this task.**

```python
OPERATION_COMMANDS = {"validate", "dry-run", "run", "draft", "resume", "reproduce", "freeze", "report"}
```

and `"reproduce": command_reproduce` in `handlers`, function-local-imported the way `command_freeze` and
`command_report` are.

**Arm B's edit, to the design's advance spec and no further:** the shipped
`assert ("reproduce", "NOT BUILT") in tables["Command"]` becomes `("reproduce", "built")`, **and** a new
line `assert ("list-templates", "NOT BUILT") in tables["Command"]` is added. Correction 20: that line is a
**marked row-presence probe**, so flipping it without adding another deletes coverage the comment beside it
names. The `set(NOT_BUILT_COMMANDS)` equalities are **self-maintaining and must not be edited**.

**Four arity tests, as additions** (correction 17) — no path, two paths, a flag, and `reproduce new`.
The flag test is the arm the `len` half alone cannot cover. `reproduce new` is **disclosure item 5** and
must be **pinned, not only disclosed**: `new` is a single token, so the arity arm is never reached and the
two-token `NOT_BUILT_COMMANDS` lookup never happens, so the call dispatches with `new` as its path and
prints `E-IO-FAILED` at exit **1** — **exit `2` → `1`, and the identifier is new.** H9a got the analogous
`draft new` claim wrong three ways and H9b then measured its own; **measure all four shapes through the
real console script, outside this repository, and correct the disclosure if any differs.**

**Do not rest anything on `_dispatch`'s branch order** (correction 18): the built branches precede the
`NOT_BUILT_COMMANDS` lookups, and that order is **filed as unpinned** — hoisting the lookups leaves the
suite green. Assert the outcome (the code and the identifier), not the order.

**Guard-pin arm E becomes meaningful here.** It was captured in task 1 against the `NOT BUILT`
invocation; re-run it against the dispatching command and report that ADDED/REMOVED/CHANGED are still
empty over all three trees. **You may not edit arm E** — if it fails, that is a finding.

**Must not touch:** `NOT_BUILT_COMMANDS`'s other three entries, the `set(...)` equalities, any other arm.

---

## Task 12

**The config-operand form.** Design Decision 13.

Given a config, steps 1–3 have no input and step 5 is moot. What runs: task 5's ranking against **the
repo the config sits in** — found by walk-up from the **config path**, never from the working directory,
which is `CLAUDE.md`'s invariant — then `uv sync --locked`, then task 8's `.env` and `required_env`, then
the same closing instructions.

**It names what it did not verify** — `code_hash`, the input manifest, **and** the apparatus — rather
than reporting a match it never made. That is § Reproducing's own sentence and `diff`'s own rule for a
config side, and the three are three separate printed lines.

No `apparatus.expected.json` is written (a config records no facts) and no destination is derived, so
tasks 3's and 9's refusals are unreachable from this form. **Say so in the docstring rather than leaving a
reader to wonder** — and say it as *unreachable from this form*, not as *cannot happen*, because a comment
claiming a guarantee the code does not provide is this repo's most-repeated habit.

**Fixture N.** Asserts no directory created, `uv sync` reached, and the **three** not-verified lines as
**positive assertions** — *a control asserting only absences passes identically if nothing ran*.

**Mutation:** print two of the three not-verified lines (Fixture N — each is asserted separately, so
dropping any one fails).

**Must not touch:** anything task 3 built (the clone is not reached from this form).

---

## Task 13

**The closing transcript, and the `run.yaml` form's end-to-end path.** Assemble the output § Reproducing
on another device specifies, in its order, and wire the whole command.

```
Prepared my-study_run_2026-08-06T14-02-11Z_8e21ab3/

Before running, edit:
  configs/cohort-pilot/config.yaml   data.input_dir, data.output_dir

Then:
  cd my-study_run_2026-08-06T14-02-11Z_8e21ab3
  uv run publishable validate configs/cohort-pilot/config.yaml
  uv run publishable dry-run  configs/cohort-pilot/config.yaml
  uv run publishable run      configs/cohort-pilot/config.yaml
```

Plus, when they apply: the apparatus block (task 10), a `.env` line when the template declares
`required_env` (task 8), and each comparison line from tasks 4, 5 and 7. **`reproduce` stops rather than
running**, because both remaining inputs need a person.

**Fixture F is this task's centre** — the bundle-member form end to end, and **the arm that makes Ruling
Y's cost-if-wrong a test rather than a sentence.** Assert the clone happened (the remote survives
redaction — measured), that `environment/uv.lock` was **not** reached, and that the lockfile line names
the recorded digest.

**When you assert a substring, ask what else in the output could produce it.** `assert "draft" in out`
once passed because a member was named `draft_run`, and a `run` tag's pin once passed on a bundle header's
`##` heading. Assert whole lines here.

**Mutations:** print the `validate`/`dry-run`/`run` lines in the wrong order (assert the three as an
ordered triple); omit the apparatus block when `provenance.apparatus` is non-`null` (Fixture O's project).

**Must not touch:** any earlier task's refusal codes or their messages.

---

## Task 14

> **AMENDED 2026-08-24 by the controller, after batch 1 measured what Decision 14's table does not
> anticipate.** **A failed `git clone` and a failed `uv sync` both report `E-IO-FAILED` at exit `5`, and
> § Errors has a row for neither.** Minting a fourteenth code would contradict correction 29, so **the
> count stays at thirteen and `E-IO-FAILED`'s existing row must widen to cover both sites** — *one row per
> code covering EVERY emit site*, checked against the table's own **scope sentence**. That shape has
> produced a whole-branch Major on four sub-slices, and H9a alone found thirteen rows narrower than their
> code and one wider.

**`spec-defects.md`, and every filing this slice makes, closes or declines.** Design § 5. **Task 6 owns
the missing-lockfile entry; every other one is yours.**

- **AMEND** *two specified readers of `required_env` belong to unbuilt commands*: the `reproduce` half is
  discharged for the two template homes this interpreter can construct and **narrowed** for the third
  (task 8). Amend, do not strike — half of it survives as a narrowing.
- **FILE** *a tracked `.gitattributes` carrying a `text`/`eol` attribute makes `code_hash` a property of
  how a working tree was materialized rather than of the commit.* Reproduction recipe **inline**: commit
  `* text eol=crlf`, clone with `core.autocrlf=false`, the clone hashes `d37416e` where the
  never-re-materialized original hashes `0cc6ddd`. **Owner: unassigned, with the reason** — no remaining
  slice (H9d's three commands, H3c-3's folds) has `hashes.py` or § How the three are computed as its
  surface, and H6 is complete.
- **FILE** *a study bundle carries no lockfile.* Owner: **unassigned, with the reason** — `study add`'s
  bundle contents are H8c's surface and H8c is complete. **State the check its closer must make**: copy
  `environment/uv.lock` into the bundle, or redact `provenance.environment.uv_lock` in a member the way
  `input_manifest` already is, so the dangling reference is at least visible.
- **FILE** *`provenance.environment` names no `pyproject.toml`.* Owner: unassigned, with the reason.
- **DECLINE and RE-OWN** the `UpstreamLedger.record` `.get` filing: its ground — that `reproduce`
  *"walks a resolved `run_id` back through its own recorded ancestors"* — is **false**. Re-read
  § Reproducing on another device: its seven steps name `git`, `environment`, `config` and `apparatus`,
  and `provenance.upstream` in none of them. **Owner: unassigned, with the reason**, and secondarily
  H8b's `diff`, which the entry already names.

**Use the *fact with a reason* form, never *"whichever slice next touches X"*** — this file rejects that
form by name at its own `RE-OWNED 2026-08-19` entry, because it reads as covered while naming nobody and
resolves to a closed slice the moment X is touched.

**A ledger line saying "filed" is not a filing**, and neither is a dispatch line, nor a report's own
escalation. **Every item above must exist in `docs/superpowers/spec-defects.md` when you are done, and
your report must quote the heading of each.** And when you change code an entry describes, re-read the
entry: a filing's claims about the code go stale like any other comment.

**Must not touch:** any entry this slice does not own; the four documents (task 15); `CLAUDE.md` (task 15).

---

## Task 15

**The four documents, `CLAUDE.md`, § Executability, and both consistency passes.**

`reference.md`:
- § **Reproducing on another device** — step 2's *"can't collide"* narrowed (correction 13): the
  destination is derived so you do not name it, and a second `reproduce` of the same run **refuses**
  rather than overwriting. Step 3's *"catching a rewritten or force-pushed history"* replaced by Ruling
  Z's shape: the difference, the input, and the candidate causes it cannot separate. Step 4 gains the
  lockfile ranking. Step 5 gains the `parameters_hash` self-check and the comment-loss disclosure. Step 6
  **narrowed** to what Decision 12 builds, and it must say what it defers and to which command.
- § **CLI reference** — `reproduce`'s row from `NOT BUILT` to `built`, and its `Does` cell rewritten to
  what the command does.
- § **Errors core raises** — **twelve rows, one per code, each covering every site that raises *or*
  reports it.** § Errors carries one row per code and not per emit site: `E-TEMPLATE-UNKNOWN` had two
  sites and a task scoped by one helper's call site missed the second.
- § **Exit codes and diagnostics** — `5`'s *"a clone or `uv sync` that failed"* gains its first reader,
  and say so the way `3`/`4`'s `resume` sentence does.
- § **The apparatus core can only observe** — `E-APPARATUS-UNEXPECTED` beside the gate, on the gate's own
  terms, and **the third reading of one comparison named explicitly**: the gate tolerates `null → value`,
  `diff` flags it, and the expectation file sides with the **gate**. H8b ruled the first two are two
  questions rather than one contradiction; this is the third, stated so nobody folds it into either.

`design-principles.md` § Design goals — the *"not optional"* footnote (task 6 wrote the decision; you
write the sentence if task 6 did not, and **grep to find out which** rather than assuming).

`CLAUDE.md` — the H9c entry in the same shape as its siblings: what merged, what it retires (**nothing**),
what it unblocks (**zero configs**), the disclosure, and the four-or-five things worth carrying. **State
the behaviour change to `run` and the exit `2` → `1` change at `reproduce new`.** A wrong disclosure is
worse than no disclosure.

§ **Executability on this build** — one dated entry, and **derive the verdict rather than carrying it**:
`reproduce` does not run at `validate` and is not invoked from a step; none of the nine configs is a run
record or declares a `study`, so none is an operand it accepts; **none declares an `apparatus_probe`**, so
`E-APPARATUS-UNEXPECTED` is unreachable for all nine. **The four-row table is repeated character for
character**, by the two independent extraction methods the H8a and H9a entries describe, `diff`-ed to
empty, and its cells still name **H8a** — updating them is exactly how a repeated table stops being
repeated. **No fifth number.** Quote the table or name the dependency; never a single figure.

**Both consistency passes**, and the traps that have actually bitten:
- **Never filter the output of a sweep whose job is to find a string** — filter the file list. A reviewer
  checking this exact rule lost a true hit to `grep -v superpowers`. Prove each sweep can fail by running
  it against a string known to be present.
- **The development record is tracked**, so a sweep over the four documents must **name them
  individually**; `*.md` no longer means what it used to.
- **When you insert or remove a table row, check every row it moved and every sentence whose antecedent it
  displaced** — H9a's Major 1 was an insertion that made a § Warnings row contradict itself three clauses
  later.
- **Locate a row by what a sibling row *does*, never by position.** Seven instances, wrong twice.
- **`ruff format` does not touch `*.md`.** Two agents on two slices blamed it and both reverted files on
  that reading; measured both times as byte-identical. If bytes move, find the cause rather than
  restoring on a story.
- The **cross-document** pass governs the four documents only; a feasibility analysis is exempt from it
  and subject to the mechanical pass in full. **Neither pass governs the development record** — correct a
  spec or a scoping by **appending**, never by editing.

**Must not touch:** `spec-defects.md` (task 14), any guard-pin arm, `src/`.

---

## Corrections 26–29, appended 2026-08-24 before dispatch — two mechanisms, one fixture recipe, one count

The design's own [§ Appendix](../specs/2026-08-24-reproduce-design.md) carries these with their full
measurements. They are repeated here because **a correction that reaches only the design reaches no
implementer**, and each names the task section it amends.

26. **Fixture D was not constructible, and a rewritten history is caught at the CHECKOUT rather than by
    the hash — amends tasks 3 and 4.** A commit SHA is a hash over its own tree, so a different tree
    cannot live at the same SHA; measured, an amend produced a new SHA (`fcc45b7…` → `ff45afe…`) and left
    the original's tree untouched, so the recorded SHA still checks out to the recorded bytes and the
    comparison **passes**. **Task 4's Fixture D becomes two arms**: **D1**, the record's `code_hash` set
    to the pre-H6a figure computed in the test by `hashes.code_hash(root, None)` over a tree holding a
    git-ignored file under `src/` (`bdf2ce9` against `0cc6ddd`); and **D2**, a `code_hash` edited to an
    arbitrary digest. **Task 3 gains a thirteenth code**, `E-REPRODUCE-COMMIT-UNREACHABLE` at exit
    **`5`**, for a recorded commit the remote no longer holds — measured: after an amend,
    `git clone --no-local` of a bare intermediate does not carry the old object and
    `git checkout --detach <recorded-sha>` fails `fatal: unable to read tree`. Its message names the
    recorded commit and says the remote does not hold it.
    **And a fixture trap you must design around:** `git clone` of a **local path** hardlinks the whole
    object database, **unreachable objects included**, so Fixture A's local-path remote **cannot
    reproduce that state** — the checkout succeeded in the measurement. The recipe needs a bare
    intermediate cloned with **`--no-local`**. A fixture built the obvious way passes while testing the
    opposite state. **`reproduce` itself passes no `--no-local`**: that would break the legitimate
    local-remote case and slow every clone. The flag belongs to the fixture.
27. **Task 9's mechanism is `record(incoming)` THEN `changed(incoming)` on the seeded object, and the
    design's *"asked only for `changed`"* is false of the shipped class.** `Observations.changed`'s
    `assert` rests on a caller contract its own docstring states — *"`record` runs before `changed` for
    the same `facts`"* — which holds for a run's own object and **not** for one seeded from a foreign
    record. Measured on a seeded object, `changed` **alone** raises `AssertionError` for three cases: an
    extra incoming fact, a condition the expectation does not carry, and — **the one that matters** —
    **`null → value`**, which § Reproducing on another device requires to **pass** and calls *"more
    evidence rather than less"*. With `record(incoming)` first, **which is what `Observer` itself does**,
    all eight measured cases are right and there is still no new comparison function. **Task 9's mutation
    list gains a sibling: drop the `record` call and keep the `changed` call**, caught by Fixture P arm 2,
    which becomes the arm separating an `AssertionError` from a pass. Fixture Q's `total_probes` claim is
    unchanged — the seeded object's counts are its own and reach no record.
28. **Task 5's "reachable beside the operand" is a filesystem probe, and the docstring must say so.** The
    test is `(<operand>.parent / "environment" / "uv.lock").is_file()` — a probe for a file, not a
    structural fact about the operand. Correct for both measured forms, and **stated because a bundle
    placed inside a run directory would take the run-directory branch**. What makes it safe is the digest
    check: `E-REPRODUCE-LOCKFILE-EDITED` fires when the copy's sha256 does not match the record's
    `uv_lock_hash`, so a foreign copy is refused rather than used. **Write the reason, not just the
    probe** — that is the difference between a proxy and a guarded one.
29. **The count is thirteen, and it carries its noun — amends task 15.** Twelve `E-REPRODUCE-*` codes and
    one `E-APPARATUS-*` code: **thirteen codes, thirteen § Errors rows**, one row per code covering every
    site that raises *or* reports it. Anywhere this plan or the design says *twelve*, read **thirteen**.
    The § Executability verdict does not move and **no fifth number** is minted: a count of refusals says
    nothing about whether any of the nine configs can reach one, and none can. **Still no exit code is
    minted** — `5` gains a second reader here rather than a first, since the lockfile task already reads
    it for `uv sync`.
