# H6b batch 5 — tasks 8, 9, 10, 11 — report

Written incrementally as each task landed, so a stall leaves the finished tasks documented. **A commit
message is not a report** — batch 4 shipped without one and the reviewer re-derived every claim.

Gates before this batch started: `ruff check` clean, `ruff format --check` clean (93 files), `mypy`
clean (52 source files), `uv run pytest` **2971 passed, 1 skipped, 2 xfailed** in 207.84 s. Run in the
foreground, read directly. No monitor, no poll, no background job.

---

## Task 8 — `spec-defects.md`: one entry closed, four rows struck, two filings — commit `2a62bbe`

### The count, re-derived from the entry's own table before the number was written

Not carried from the brief and not from the ruling. The nine, as the table lists them:
`E-GIT-NO-REPO`, `E-GIT-NO-COMMIT`, `E-CODE-DIRTY`, `E-INPUT-CHANGED`, `E-RUN-LOCKED`,
`E-RUN-ID-EXHAUSTED`, `E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS`, `E-EXPERIMENT-UNKNOWN`.

| Step | Closed by | Left |
|---|---|---|
| filed | — | 9 |
| `E-CODE-DIRTY` | H6a batch 4, `4c79905` | 8 |
| `E-EXPERIMENT-UNKNOWN` | H8c task 16, `c794029` | 7 |
| `E-GIT-NO-REPO`, `E-GIT-NO-COMMIT` | H6b task 5 (Ruling N) | **5** |

`E-STEP-EXISTS` is **not** one of the nine — it is not in the table, and the entry's own prose calls it
*"the one sibling that is documented, and only partially."* It is recorded beside the five as a separate
observation.

**The derivation is now checkable from the file rather than from prose.** Four rows are struck with
their closing commits, so counting unstruck rows gives exactly five:

```
python3 -c "
s=open('docs/superpowers/spec-defects.md').read().split(chr(10))
i=[n for n,l in enumerate(s) if l.startswith('## Five undocumented')][0]
rows=[l for l in s[i:i+40] if l.startswith('| \`') or l.startswith('| ~~\`')]
print(len(rows), len([l for l in rows if not l.startswith('| ~~')]))"
```

→ `9 5`. If the heading ever says five while the table shows nine live rows, that command says so.
H6a's *"now eight"* note is kept: it was true on its date and is a way-point in the chain, not a
contradiction.

### Filings and closures, each with where it landed and its reproduce command

**1. CLOSED — "Six `provenance` and `results` keys in the `run.yaml` example that no code writes."**
Heading struck, two remaining table rows struck, closure appended at the end of the entry.
Verified at HEAD, not from the amendments:

```
python3 - <<'PY'
import re
src = open('src/publishable/cli.py').read()
i = src.index('provenance: dict[str, Any] = {')
for line in src[i:i + 6000].split('\n'):
    m = re.match(r'^(\s+)"([a-z_]+)":', line)
    if m: print(len(m.group(1)), m.group(2))
PY
```

Output carries, at indent 16 under `environment`: `manager python_version os hostname uv_lock
uv_lock_hash hardware`; and at indent 12: `… allocation allocation_hash upstream`. All three routed
rows are written.

**2. Recorded, not filed — `diff` gains no sixth row and `report` renders neither key** (Decision 14).
Stated once inside that closure, so a later reader does not file it as a gap. § What `diff` compares
says *five rows* in its own prose and the shape is deliberate, so no owner is invented.

**3. APPENDED — the nine-codes entry**, heading nine → five, chain table, the five enumerated, their
re-swept states, owner unassigned with the reason (no remaining chartered slice has `run_identity.py`,
the manifest path or `generators/`/`scaffold.py` as its surface; H9 is
`reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`, H3c-3's 14 are folds and holdouts inside cells).

**4. FILED — `validate_config`'s bare `except ContractError` around `find_repo_root` is wider than its
comment claims.** New OPEN entry, sited immediately after the nine-codes entry. Owner: unassigned, with
the reason. Reproduce, by reading the two catch sites rather than perturbing either:

```
grep -n "find_repo_root" src/publishable/validate.py
```

→ three hits: the import, `validate_config`'s call, `_check_data`'s call. `_check_data` catches
`except ContractError as exc:` then `if exc.code == "E-GIT-NO-REPO": return` / `raise`;
`validate_config` catches `except ContractError:` with no code test. **The sibling that already got it
right is in the same file.**

**5. AMENDED — "`E-GIT-NO-REPO` is named in two normative § Errors cells … with no row of its own."**
Heading marked PARTLY CLOSED with the closed clause struck; amendment appended. The half task 5 closed
is closed for **both** of that entry's claims — the row exists, and it describes the two uncaught call
sites at their own source. What is amended rather than left is the **"Why unassigned"** paragraph,
which said *"H6 owns hashes and provenance proper (not the registry question of which codes get
rows)"* — false as of task 5, and a reader trusts a reasoning paragraph more than a headline. The
prose-only family (`E-PROJECT-EXISTS`, `E-STEP-EXISTS`, `E-TEMPLATE-EXISTS`, `E-EXPERIMENT-EXISTS`)
stays OPEN, owner unchanged. No inbound reference to the old heading exists:
`grep -rn "named in two normative" . --include="*.md"` returns only `spec-defects.md` itself.

### The sweeps: exact command, file list, can-fail proof

**Sweep 1 — the five codes' documentation states, over the four documents named individually.**

```
for c in E-INPUT-CHANGED E-RUN-LOCKED E-RUN-ID-EXHAUSTED E-PROJECT-EXISTS E-EXPERIMENT-EXISTS \
         E-STEP-EXISTS E-TEMPLATE-EXISTS E-CODE-DIRTY E-EXPERIMENT-UNKNOWN \
         E-GIT-NO-REPO E-GIT-NO-COMMIT; do
  echo "=== $c"; grep -c "$c" README.md docs/design-principles.md \
    docs/experimental-designs.md docs/reference.md; done
```

**The file list is named; the output is not filtered.** Results: `E-INPUT-CHANGED`, `E-RUN-LOCKED`,
`E-RUN-ID-EXHAUSTED` → 0 in all four. `E-PROJECT-EXISTS` → 1 (reference only), `E-STEP-EXISTS` → 1,
`E-TEMPLATE-EXISTS` → 1, `E-EXPERIMENT-EXISTS` → 2, `E-EXPERIMENT-UNKNOWN` → 1, `E-CODE-DIRTY` → 4,
`E-GIT-NO-REPO` → 3, `E-GIT-NO-COMMIT` → 1. Each nonzero hit was then **read** to decide row versus
mention — a count alone cannot tell them apart, which is this entry's own heading.

**Can-fail control:** `grep -c "E-PARAM-MISSING" docs/reference.md` → **1**. *This is the number the
command printed.* The amendment first said **2**; the control was run before the sentence shipped and
the file was corrected. That is the family's recurring miscount shape, caught in advance rather than by a reviewer.

**Sweep 2 — when did the § Exit codes sentence gain `E-EXPERIMENT-EXISTS`.**

```
git log --oneline -S 'generate experiment` reports `E-EXPERIMENT-EXISTS' -- docs/reference.md
```

→ `075455e` (2026-08-14). **Can-fail proof, both directions run:** substituting `E-NOT-A-CODE` for
`E-EXPERIMENT-EXISTS` in the same `-S` string returns nothing, while the `E-STEP-EXISTS` spelling of
the same sentence returns the same `075455e` — so the sweep discriminates rather than always
answering.

**Sweep 3 — mechanical pass over the edited file**, `/tmp/mechpass.py` (throwaway, not kept):
trailing whitespace, tabs, invisible unicode, table column counts, fenced blocks skipped.
`python3 /tmp/mechpass.py docs/superpowers/spec-defects.md` → **0 findings**. **Proven able to fail** on
four planted controls: a trailing space → `trailing-ws`; a tab → `tab`; a two-column row under a
three-column header → `table-col-mismatch [2, 3]`; and a separate U+200B file → `invisible 0x200b`.

### Disagreements with the brief — reported as a list, never as a count of zero

1. **The brief's *"Record that `environment` is now the one sub-block whose key order matches the
   example exactly"* is FALSE.** `git`'s six keys (`repo_root`, `commit`, `branch`, `remote`,
   `code_dirty`, `config_committed`) also match § The two files, and did before H6b. Measured with the
   extraction above, against the example at `docs/reference.md` § The two files. The closure says what
   is true instead: `environment` matches, `git` matches too, and the divergence the key-order note
   records is at `provenance`'s **top level** — `cli.py` builds `publishable_version` and
   `plugin_versions` before `units`/`units_hash`/`allocation`/`allocation_hash`/`upstream`, where the
   example shows them after.
2. **The brief's *"Its `provenance.allocation`/`.allocation_hash` row was struck at H3c1 task 14"* is
   FALSE.** That row was **amended and left unstruck** — only `provenance.upstream` carried a strike.
   That is *why* the entry still read as three open rows two slices later, and it is the same
   carried-versus-derived shape this task exists to correct. Struck here, dated 2026-08-23, with the
   original closure date preserved in the cell.
3. **Design Decision 16 says the guard pin has "Four … no authorized editor"; the ledger, the dispatch
   and batch 1's review all say FIVE** (arms Q, R, S, T, U). Six arms, one editor (arm P, task 3's), so
   five is right. **Not retro-edited** — a spec records what was decided when it was written. Reported
   for the batch-5 review.
4. **The 2026-08-22 sweep inside the nine-codes entry misclassified `E-EXPERIMENT-EXISTS`** on its own
   date, per sweep 2 above. Recorded in the amendment as the second instance of that entry's
   heading-distinction going stale.

No guard-pin arm was opened. No test moved: **2971 passed, 1 skipped, 2 xfailed**, delta 0.

---

## Task 9 — `CLAUDE.md`: the order line and the slice entry — commit `49c8a33`

**The order line.** *"Order of the slices that remain: H6b, H9, then H3c-3's remaining 14"* →
*"Order of the slices that remain: H9, then H3c-3's remaining 14"*.

**Every count phrase and every H6 mention near it was checked, not left.** Sweep, file list named,
output unfiltered:

```
for f in CLAUDE.md README.md docs/design-principles.md docs/experimental-designs.md \
         docs/reference.md docs/feasibility-llm-growth-studies.md; do
  echo "== $f"; grep -n "H6b\|H6a\|H6 " $f; done
```

Six hits in `CLAUDE.md`, three in the feasibility analysis (all inside the H6a § Executability entry,
which is append-only and correct), none in the other four documents. Three edits followed, two of which
the brief does not name:

1. **`"the H4, H5, H7 and H8 families are all complete"` gains H6** — an implied edit, since removing
   H6b from the order line without this leaves H6 in neither list.
2. **`"H6a's appended correction … narrows the verdict in one direction, H6 before H9"` goes to the past
   tense**, with a clause saying the ordering is settled now that H6 is complete and H9 is next.
3. **`"The spine design's own nine-row charter table was never amended for either H8's three-way split
   or H5's two-way one … an appended amendment dated 2026-08-22 now records both"` was under-stating.**
   The spine's § Correction, 2026-08-22 (appended as H6a completes) records **H6's two-way split** as
   its own fourth item. So the omission ran to **three** splits, not two. **No new number was minted**:
   *fourteen* is named as the spine's own figure, written before H6's split reached that table, and
   flagged as a figure to quote rather than re-derive. The spine design itself was **not** retro-edited.

**One stale string left deliberately, and reported instead of fixed.** `CLAUDE.md`'s H6a entry says the
*"only machine-dependent input left"* claim was *"struck rather than narrowed — filed, owner H6b."*
Decision 12 declined that filing and re-owned it unassigned, so *owner H6b* is now historical. **Left
standing** because it was true on its date and the H6b entry directly above it states the decline; a
reader meets the decline first.

**A finding for the controller, outside every task's surface.** `spec-defects.md`'s root-`.gitignore`
entry still carries **`— **Owner: H6b**` in its heading** while its own 2026-08-23 amendment re-owns it
*unassigned with the reason*. The heading and the body now disagree about the owner. **Task 8 is
explicitly forbidden from touching that entry** (*"the two entries task 6 amends"*), and no other task
in this batch touches `spec-defects.md`, so it is reported rather than fixed. Reproduce:
`grep -n "uncommitted root \`.gitignore\` decides" docs/superpowers/spec-defects.md`, then read the
heading against the `AMENDED 2026-08-23, H6b task 6` paragraph in the same entry.

**The slice entry** states: the three keys and why each source beat the obvious one; the additive claim
as a measurement (`grep -n "hash(provenance\|hash(run_doc\|hash(record" src/publishable/*.py` → **no
output, exit 1**, re-run at this HEAD; two readers exist and neither iterates); **zero refusals retired,
ZERO configs unblocked**; § Executability does not move, **with the dependency named and no number
quoted**; Rulings O, Q, N and P; and Decision 12's decline with its reason.

**The four things worth carrying, and why these four.** (1) *the charter was stale in the same direction
again* — three of eight rows wrong plus one item that could not have been in the scoping, 8 → 11 tasks.
(2) *a pin that must move can be moved once, by a named editor, with its post-edit state written first*
— and its other half, a task leaving the branch red rather than self-authorizing arm S. (3) *a fixture
that recomputes the implementation cannot fail*, which is why `os` is pinned with sentinels. (4) *a
false enumeration was deleted rather than rewritten*, beside a **true** claim that was corrected rather
than deleted, because *deleting a true claim is not licensed by prefer-deletion*. **The fifth candidate,
*the sibling that already got it right*, was folded into the entry's `hostname` clause rather than given
a slot**: it is one call site with no rule attached beyond *two spellings of one fact is how the two
drift*, which the clause already says, and the other four each carry a rule this repo has paid for.

Mechanical pass on `CLAUDE.md`: **0 findings**, both checkers proven able to fail (see task 10).

---

## Task 10 — both consistency passes — commit `9b7cc54`

### The checkers, debugged before they were trusted

Two throwaway scripts, not kept in the repo: `/tmp/mechpass.py` (trailing whitespace, tabs, invisible
unicode, table column counts; fenced blocks skipped) and `/tmp/linkpass.py` (relative link targets,
`#anchor` resolution against a GitHub-style slugger, duplicate heading anchors).

**`mechpass.py` produced a false positive on its first run** — `CLAUDE.md` line 860, *table column
mismatch [3, 5]* — on § Checking consistency' **Enum comments** row, whose cell legitimately contains
`# a \| b \| c`. Fixed to count **unescaped** pipes only (`(?<!\\)\|`). **This is the third slice
running in which a checker could not be trusted until debugged**, and the disclosure is the point.

**Can-fail proof, all four mechanical classes and all three link classes:**

| Planted control | Fired as |
|---|---|
| a trailing space | `trailing-ws` |
| a tab | `tab` |
| a two-cell row under a three-cell header | `table-col-mismatch [2, 3]` |
| a U+200B in a line | `invisible 0x200b` |
| `## One` twice in one file | `DUPLICATE-ANCHOR one 2` |
| `[a](nope.md)` | `MISSING-FILE` |
| `[b](#no-such)` | `MISSING-ANCHOR` |

**And proven able to fail on the real file, not only on a toy**: two links appended to a copy of
`docs/reference.md` (`#no-such-anchor-here` and `docs/definitely-missing.md`) both fired, at lines 4213
and 4214, among the **941** in-file anchor links that all resolve. The feasibility analysis carries
**57** more, all resolving.

### Mechanical pass — file list, result, and the one finding

```
python3 /tmp/mechpass.py README.md docs/design-principles.md docs/experimental-designs.md \
    docs/reference.md docs/feasibility-llm-growth-studies.md CLAUDE.md
python3 /tmp/linkpass.py <the same six files>
grep -nE "[0-9] x [0-9]" <the same six files>          # `x` for multiplication
grep -nE "^#{1,6} .*–" <the same six files>            # en dash in a heading
```

Final state: **0 findings from both checkers, no `x`, no en dash in any heading.** The last two greps
were proven able to fail against a two-line control containing `## Dose–response` and `3 x 5
conditions`; both matched.

**ONE real finding, and it is pre-existing on `main` rather than this branch's.**
`docs/feasibility-llm-growth-studies.md` § What core refuses' *Class-ratio* row **wrapped across two
source lines**, so GitHub rendered the continuation line as a bogus one-cell row — and the wrap carried
the same § Executability link **twice**, once bare and once parenthesized. Introduced by `bc20b13`
(2026-08-21), found by `mechpass.py` as `table-col-mismatch [3, 4]` at line 743.
**Fixed**: joined onto one line, and the duplicate parenthetical deleted — deleting one of two
**identical** links loses no claim, so this is a deletion rather than a rewrite. It is outside
§ Executability, which is task 11's, and it is the only deletion this branch makes in that file.

**An observation, not a finding, reported rather than fixed.** `## Cost and execution summary` sits at
line 1444, **between** § Executability's earlier and later entries, so every entry from the 2026-08-20
correction onward is structurally nested under it rather than under § Executability. Pre-existing on
`main`, not among the enumerated mechanical checks, and repairing it would move a heading the
`#executability-on-this-build` anchor is linked from in at least six places. Left for a ruling.

### Cross-document pass — the four documents only

**Only `docs/reference.md` of the four is edited by this branch** (`git diff --name-only main..HEAD`).

| Class | Result |
|---|---|
| **Schema fields in prose** | `os`, `hostname` and `hardware` are each named in prose and each present in § The two files' `run.yaml` example, and the reverse holds. `grep -n "cpu_count"` over the four plus the analysis → **exactly two hits**, the example line and its own prose paragraph, so there is one source for the block |
| **The shared worked example** | The only `cohort-pilot` change on this branch is the `hardware` line, `gpu` out and `cpu_count: 32` kept. `apparatus: null` and its *"no probe declared"* comment stand. **No interval, hash prefix, unit count, delta or `repeat_spread` moved** — checked by reading the whole `git diff main..HEAD -- docs/reference.md`, which is three insertions and one line changed |
| **Enum comments** | The `hardware` line carries **no** inline comment, so nothing enumerates a key core does not write |
| **Declared vs. derived** | None of `os`, `hostname`, `hardware`, `environment` appears anywhere in § The one config file (lines 44–213, counted programmatically) — all three are derived and none is shown as a settable input |
| **Versions** | `CITATION.cff` 0.1.0 · `pyproject.toml` 0.1.0 · the example's `publishable_version: "0.1.0"` · README's v0.x notice. Agree |
| **Config completeness** | No config field added or removed by this branch |
| **Prevented mistakes** | Untouched — nothing in § Mistakes core prevents depends on a `provenance` key |

### The deleted-claim sweep, run flattened, with the reason demonstrated

`gpu`, `A100`, `hms-gpu`, and the deleted `secrets.py` enumeration's phrasing
(`provenance\.?environment.{0,60}assembled from`, `os…hostname…hardware…uv\.?lock…alone`), plus
`never written today` and `ebf642a`, over a named list of twelve files (the four documents, `CLAUDE.md`,
the analysis, `secrets.py`, `study.py`, `cli.py`, `test_study.py`, `test_cli.py`, `test_provenance.py`).
**Whitespace flattened to a single space before matching.**

**Why flattening rather than `grep -F`, demonstrated on real content rather than asserted:** the phrase
*"A GPU, an instrument revision, or a hosted model deployment is not"* **is present in
`docs/reference.md`** and `probe in raw_text` is `False` while `probe in flattened` is `True`, because
it wraps. That is the exact mechanism by which two of one false sentence's five homes hid.

Results: the `secrets.py` enumeration is **gone from every file** in both spellings. `ebf642a` survives
in `study.py` twice (task 7's *corrected* claim, deliberate) and once in `CLAUDE.md` (my own entry
quoting it). `gpu`/`GPU`: two hits in `docs/reference.md` (`hms-gpu-node-04`, the hostname the example
has always carried, and the new *"A GPU"* prose), five in `CLAUDE.md` (all inside the new H6b entry),
one in `cli.py` (task 3's comment). `A100`: **zero** in the four documents. Outside the
development record — which carries it in `H6-SCOPING.md`, this slice's plan, its design and three of its
ledger/review files, none of them editable here — the only `A100` in the repo is
`tests/test_report.py`'s **apparatus** fixture, which is correct and untouched. Measured with
`grep -rln "A100"` over `*.py`/`*.md`, not asserted; the first draft of this sentence said *"the only
`A100` in the repo"* and the sweep contradicted it.

---

## Task 11 — § Executability: one dated entry, four rows unchanged — commit `4a3b9fc`

### The sha, and the executable tree it names

Header: **"Measured on 2026-08-23 against commit `9b7cc54`"** — task 10's commit, this branch's tip at
this task, on H6a's and H5b's precedent. `git log --oneline -1 -- src tests` → **`6497284`**, and

```
git diff --name-only 6497284..HEAD -- src tests
```

is **empty**, so `9b7cc54` carries the same executable tree the derivation was run against. Stated in
the entry itself.

### The re-derivation — done rather than repeated

**Row 1 counts configs validating with zero *errors*.** H6b writes three keys inside
`cli.command_run`'s `provenance` literal, gives two `provenance.py` codes their § Errors rows, corrects
three docstrings, and edits documents. **Documenting a code changes no behaviour** — both were
undocumented, not unraised.

```
grep -c "E-GIT-NO-REPO\|E-GIT-NO-COMMIT" src/publishable/validate.py    →  1
grep -n  "E-GIT-NO-REPO\|E-GIT-NO-COMMIT" src/publishable/validate.py   →  1223: if exc.code == "E-GIT-NO-REPO":
grep -c "E-PARAM-MISSING" src/publishable/validate.py                   →  3   (control)
```

**The one hit was READ, not counted.** It is `_check_data`'s pass branch — the line that returns quietly
when the config is outside every repository, which is *why* such a config prints `✓ config valid` and
refuses only at `run`. **Not an emit.** The control returns 3, so the sweep can find a code `validate`
does report. Both numbers are what the commands printed.

**Rows 2 and 3 name dependencies H6b does not touch** — `io.reuse_from`'s plugin-side call, and the
`report_by`-under-`resample` construction inside `summarize_step`. H6b's surface is
`cli.command_run`'s provenance assembly, `secrets.py`'s and `study.py`'s docstrings, and documents.
Confirmed by the branch's own file list: `cli.py`, `secrets.py`, `study.py`, three test files, and
documents. `stats.py` and `lineage.py` are not in it.

**Row 4 counts configs free of every core-side dependency this analysis can name.**
`provenance.environment` is written for every run regardless of config — no declaration opts in and none
opts out — **so no config gains or loses a dependency.** That is a different claim from *"the record
grew"*, and it is the one row 4 rests on.

**Neither documented code can fire for any of the nine.** Both are properties of a **repository** — none
at all, or one with no commit — and neither reads any declaration. Their raise sites are in
`provenance.py`, which **this branch does not modify at all**
(`git diff --name-only main..HEAD` does not list it), so they raise today exactly where they raised
before.

**Conclusion: the table does not move.** Derived, not assumed.

### The table, extracted rather than retyped

```
sed -n '1862,1867p' docs/feasibility-llm-growth-studies.md    # the H6a entry's table
```

diffed against an **independent programmatic extraction** of the same entry's table (walk from the
`### Measured on 2026-08-22 … f70499f` heading to the first `| Figure |` line and take the block) →
**`EXTRACTIONS AGREE`**, then appended verbatim. Re-extracted after the append and diffed against the
H6a original again → **diff empty**. **The plan's and the design's own reproductions of the table were
not used**, which is what both of this analysis' wrong figures were made from.

**Each cell's slice-specific prose is preserved unchanged, including the two cells that say `H8a`** — the
instinct to update that to `H6b` is exactly how a repeated table stops being repeated, and the entry says
so in prose instead. **No fifth number**, and no single figure quoted: the entry names the dependency —
`io.reuse_from`'s plugin-side call for six, the `report_by`-under-`resample` gap for seven, and 8 of 8
validating clean, the only figure `validate` can see.

### What newly stops and what newly warns: nothing, and `W-PARAM-UNSET` stays unknowable

Stated in prose, separately from the table, as a **derived** claim standing on the sweep above: H6b
mints no error and no warning, and the two codes it documents were already raised at every commit
before this branch.

**`W-PARAM-UNSET` is NOT re-opened and NOT guessed at.** The H6a entry records it as *unknowable, with
the reason* — it fires on `parameter_spec` paths that carry a default and that the config leaves unset,
and **neither `growth_screen` nor `publishable-llm` is installable in any build**, the same limit every
entry in this section since the H7b ones has recorded. Nothing H6b built changes what can be measured
there, so that answer is left standing. Guessing from the `parameters` blocks shown in the analysis
would measure the guess.

### Append-only, verified

`git diff main..HEAD -- docs/feasibility-llm-growth-studies.md | grep "^-"` shows **exactly two deleted
lines across the whole branch**, both task 10's one-line join of the wrapped *Class-ratio* row. **No
earlier § Executability entry is touched.** The new entry is a `###` at EOF, matching every predecessor,
so the `#executability-on-this-build` anchor — linked from at least six places — is unchanged.

Mechanical pass on the edited file: **0 findings**; no `x` for multiplication; no en dash in any
heading; all 57 of its anchor links resolve.

---

## Batch summary

| Task | Commit | Suite |
|---|---|---|
| 8 — `spec-defects.md` | `2a62bbe` | 2971 passed, 1 skipped, 2 xfailed |
| 9 — `CLAUDE.md` | `49c8a33` | 2971 passed, 1 skipped, 2 xfailed |
| 10 — the consistency passes | `9b7cc54` | 2971 passed, 1 skipped, 2 xfailed |
| 11 — § Executability | `4a3b9fc` | 2971 passed, 1 skipped, 2 xfailed |

**Delta: 0 tests, as specified.** All four gates run in the foreground after every task —
`uv run ruff check .`, `uv run ruff format --check .` (93 files), `uv run mypy` (52 source files),
`uv run pytest`. **No guard-pin arm was opened**; arms Q, R, S, T and U have no authorized editor and
none was touched. `.superpowers/sdd/.gitignore` was clobbered to a bare `*` by `task-brief` before this
batch, restored, and re-checked before this commit.

### Concerns, for the filing-and-sweep review

1. **`spec-defects.md`'s root-`.gitignore` entry heading still reads `**Owner: H6b**` while its own
   amendment re-owns it unassigned.** Out of every task's surface in this batch. Needs a follow-up.
2. **Design Decision 16 says the guard pin has "Four … no authorized editor"; the ledger, the dispatch
   and batch 1's review all say five.** Six arms, one editor, so five is right. The design is a spec and
   was **not** retro-edited.
3. **§ Executability's later entries are structurally nested under `## Cost and execution summary`.**
   Pre-existing, and repairing it would move the heading six links point at.
4. **The brief's two false claims about the six-unwritten-keys entry** — `environment` being the only
   matching sub-block, and the `allocation` row having been struck — are corrected in the entry itself
   and listed under task 8's disagreements. Both were caught by measuring rather than by reading.
