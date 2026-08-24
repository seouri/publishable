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

