# Task 15 — controller additions

These are requirements, with the same force as the brief file they accompany.

## Follow the existing hashes; do not invent a shape

`provenance.py` already builds `code_hash`, `parameters_hash`, `input_manifest_hash` and the `uv.lock`
hash. Read how one of those is constructed and covered before writing `allocation_hash`. `reference.md`
§ Three hashes says these are `sha256` over a canonical JSON rendering — the same canonicalisation, not
a second one that happens to agree today.

**`allocation_hash` is not a fourth identity hash.** § Allocation says its job precisely: *"a file
edited after the run no longer matches what that run reported."* It covers `allocation.json` — the
artifact task 14 writes — so that a copy changed afterwards is detectable. Hash the file's bytes or its
canonical rendering, and say which and why in the docstring; they are not the same claim, and a reader
checking the file by hand needs to know which one they are reproducing.

## `null` when absent, and check what the config example already promises

`reference.md` § The one config file carries the line

```
  allocation: null                             # "allocation.json" and its hash, when an arm
```

so the **absent** case is already documented as `null` rather than an omitted key — read the full line
and the block it sits in before choosing. That is the opposite of the choice task 14 faces for the
`holdout` key *inside* `allocation.json`, and the two are not in tension: one is a provenance slot that
always exists, the other is a key of an artifact. If your reading differs from mine, follow the document
and say so.

## The three assertions and why the middle one is weak

Present with an assignment; **absent without**; and changing an arm changes the hash.

The **absent** assertion is the vacuous one: `provenance.get("allocation") is None` passes for a run that
failed early, for a wrong path, for a `provenance` block that was never populated. Pair it with a
positive assertion on the same run — another provenance hash present and non-empty — and state in the
docstring what makes it discriminate.

The **changes** assertion must move an arm without moving anything else. Reassigning one unit from
`control` to `treatment` in the input table changes the roster's contents, so a hash covering the roster
would move for the wrong reason and the test would pass while proving nothing. **Swap two units between
arms** — the roster is byte-identical in every other column, the multiset of arm values is unchanged, and
only the membership moved. State that reasoning in the test.

## The rule with no reader — state it, do not test it

§ Resuming says `allocation.json` is *"read rather than re-drawn"* on resume. **There is no `resume`
command in this build** — `OPERATION_COMMANDS = {"validate", "run"}` — so that rule has no reader. Write
it into the artifact's docstring as the contract a future `resume` must honour, and **say plainly in your
report that it is unimplemented and untested**. Do not write a test that appears to cover it. This is one
of the two gaps task 18 records; your report is where its wording comes from.

## Documentation

**Never write a phrase locating a table row by position.** Tasks 9, 10 and 11 did it five times and were
wrong twice, once in a row the diff did not touch. Name what a sibling row *does*; when you insert a row,
check every row your insertion **moved**.


## Corrections from the pre-flight audit — these override what is written above

**1. `provenance.py` builds no hashes at all.** It is `GitInfo`, `_git`, `resolves_inside_repo`,
`find_repo_root`, `git_provenance` — 86 lines, no hash construction. The precedents are elsewhere:
`code_hash`, `parameters_hash`, `design_digest` and `_canonical` are in `hashes.py`;
`input_manifest_hash` is `manifest.manifest_hash`; the `uv.lock` hash is `uv_support.uv_lock_info`; and
the `provenance` **dict** is assembled inline in `cli.py`. Decide where `allocation_hash` belongs from
that, and say why in the docstring.

**2. "The same canonicalisation" names no single existing thing.** § How the three are computed says
`code_hash` is `sha256` over the **sorted list of (path, file-sha256) pairs**, explicitly *not* a git
tree hash, and `input_manifest_hash` is over the manifest. Only `parameters_hash` uses `_canonical`. So
pick a precedent by name and follow that one.

**3. The `allocation: null` line I quoted is not in § The one config file.** It is in **§ The two files**,
inside the `run.yaml` example's `provenance:` block, beside `units_hash` — which is the right place for
it and the opposite of what my pointer implied. **Do not add an `allocation` key to the config schema.**

## RESCOPED — task 14 absorbed most of this task, and four items remain

Read this section first; it replaces the task's shape, not its standards.

Task 14 shipped `artifacts.allocation_hash`, wired `provenance.allocation` and
`provenance.allocation_hash` in `cli.py`, and its review verified each part: the hash mirrors
`manifest.manifest_hash` by name (canonical JSON, `"sha256:"` prefix), the absent case is `null` per the
`run.yaml` provenance block rather than a config key, and the absent test carries a positive control on
the same run. **Do not rebuild any of that.** Read it, then do these four.

### 1. The swap-two-units assertion, in its discriminating form

The only content-sensitivity test today mutates a document key to `"c9"` — the weaker form this addendum
named and the reviewer flagged as missing. **Write the real one: swap two units between arms in the
input table.** The roster is then byte-identical in every other column, the multiset of arm values is
unchanged, and *only the membership moved* — so a hash that happened to cover the roster rather than the
assignment would not move, and the test would catch it. Reassigning a single unit does not have this
property, which is why it is not the test.

The property is known to hold — the reviewer measured `bf077b6d…` → `74e5df03…` on the swap — so a test
that fails is a real regression, not a discovery. State the two units and both digests' provenance in
the docstring.

### 2. Correct or confirm the bytes-vs-canonical statement

Task 14's fix round was told to fix a docstring claiming the hash is "derived from exactly the bytes
written". It is not — it is over the canonical form, and the reviewer measured two different digests for
the same document (`sha256:2e77fae5…` for the file bytes, `sha256:887307da…` canonical, the canonical
form also reordering the keys). **Verify that fix landed and says the right thing**, since a reader
reproducing the hash by hand needs the correct instruction and the two are not interchangeable.

### 3. State the rule that has no reader — and do not test it

§ Resuming and § `allocation.json` — who went where both say the file is *"read rather than re-drawn"*
on resume. **There is no `resume` command in this build** — `OPERATION_COMMANDS = {"validate", "run"}`,
confirmed. Neither the docstring nor task 14's report says the rule is unimplemented and untested.

Write it into the artifact's docstring as the contract a future `resume` must honour, and **say plainly
in your report that it has no reader**. Do not write a test that appears to cover it. Task 18's gap
entry is drafted from your report's wording, so write that sentence as if it will be quoted, because it
will be.

### 4. Say why `allocation_hash` lives where it does

It is in `artifacts.py`; `hashes.py` holds `code_hash`, `parameters_hash` and `design_digest`;
`manifest.py` holds `manifest_hash`; `uv_support.py` holds the lockfile's. Task 14's docstring justifies
the *construction* but not the *placement*. One or two sentences: what makes this a property of the
artifact rather than a fourth entry in `hashes.py`, and what a future reader adding H3d's `holdout` half
should conclude from that. If you think the placement is wrong, say so — but do not move it without
saying why in the report, since three modules already hash things and a fourth home needs a reason.

## What still applies from the original addendum

The three-assertions discipline, the vacuity warning about the **absent** case, and the note that the
`allocation: null` line lives in § The two files' `run.yaml` provenance block — **not** § The one config
file, and no `allocation` key belongs in the config schema. The corrections section below the original
text supersedes the claim that `provenance.py` builds hashes: it does not, it is 86 lines of git helpers.
