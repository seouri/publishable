## Task 13: The owned prose sweep — named files

**Files:** Modify whichever of `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md` the sweep turns up. Possibly
`src/publishable/**` and `tests/**`.

**Interfaces:** none. This task reads and repairs.

**Name the files; `*.md` no longer means the four documents.** The development record under
`docs/superpowers/` is tracked, so a glob sweeps specs, plans, scopings and ledgers — which must
**not** be retro-edited. Every sweep below names its files explicitly.

**Prove each sweep can fail.** Before trusting a sweep that returns nothing, run it against a string
known to be present in the same file list (`publishable` works everywhere; `requires_env` works in
`reference.md` and `experimental-designs.md`) and confirm it hits. **Filter the file list, never the
output** — a reviewer checking this exact rule lost a true hit to `grep -v superpowers`, because the
matching line contained that path.

The four documents, as a reusable list:

```
README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md
```

- [ ] **Step 1: Sweep the four documents for every claim this slice moved.**

```
grep -n "required_env\|requires_env\|python-dotenv\|dotenv\|\.env\|credential\|secret" \
  README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md
```

Read **every** hit. The ones the scoping measured and their expected disposition:

| Site | Expected after this slice |
|---|---|
| `README.md` — the "your data, and your credentials" line in the four-step pitch | Unchanged. `reproduce` is unbuilt and this slice does not touch it |
| `README.md` — "Neither data nor credentials travel" | Unchanged, and still true |
| `README.md` — the tree line `└── .env  # credentials, never committed` | Unchanged; `scaffold.py` writes it |
| `design-principles.md` — "your data and your credentials, neither of which core transmits" | Unchanged |
| `design-principles.md` — "**Secrets are the one thing never captured.**" | **Re-read against task 12.** Still true, and now *enforced* rather than held by absence. Decide whether it earns a clause pointing at the redaction; if it does not, say so |
| `design-principles.md` — the plugin-boundary row naming "the secrets mechanism (`required_env` / `requires_env` + dotenv loading)" | Unchanged, and now describes something that exists |
| `design-principles.md` — "**Not credential transfer.**" | Unchanged. Still a stated non-promise |
| `experimental-designs.md` — "**Credentials in a shared config**" | Unchanged |
| `experimental-designs.md` — "**A credential missing for one arm of a sweep**" | **Re-read against task 10.** It already describes the union correctly; confirm its link anchor still resolves |
| `reference.md` § Secrets & credentials — "`validate` confirms each is set … without printing or logging it" | **Was aspirational; is now true.** Confirm it reads as a statement of what happens, and that "the second only for the conditions a sweep actually resolves" matches task 10's behaviour exactly |
| `reference.md` § Templates — "`Param` carries … any credential a chosen value requires" | Task 5's |
| `reference.md` § Package layout — `secrets.py` | Task 7 step 8's |
| `reference.md` § The generated README — the `credentials` region | **Do not build it.** Task 14 files it |
| `reference.md` § Reproducing — step 6's `.env.example` copy and `required_env` listing | Unchanged; `reproduce` is unbuilt. Task 14 files it |
| `reference.md` § Metering — `dry-run` "needs … real credentials" | Unchanged; `dry-run` is unbuilt. Task 14 files it |

- [ ] **Step 2: Sweep `src/` and `tests/` separately, and do not stop one file short.**
      `CLAUDE.md` records three sweeps in one slice that each stopped one file short — one covered
      `src/` and `docs/` but not `tests/`.

```
grep -rn "required_env\|requires_env\|dotenv\|\.env\b" src/publishable/
grep -rn "required_env\|requires_env\|dotenv" tests/
```

Read each hit. `src/publishable/generators/template.py`'s comment says the `generate template` stub
omits `required_env` deliberately — **re-read it now that the attribute has a reader** and decide
whether it still says something true. `tests/test_templates.py`'s assertion
`assert t.required_env == []` is fine and should stay.

- [ ] **Step 3: Sweep for the false guarantees `H7c-SCOPING.md` § 9 named**, one at a time, and
      confirm each is now either true or amended:

```
grep -n "constraint vocabulary is closed" src/publishable/param.py
grep -n "One constraint claims it" src/publishable/param.py
grep -n "never touches provenance" docs/reference.md src/publishable/secrets.py
```

Each must have been amended by task 3, 4 or 7. If any was missed, fix it here and say which task
should have.

- [ ] **Step 4: Sweep for `<redacted:` and `E-CRED-`** across the four documents plus `src/` plus
      `tests/`, and confirm every appearance is one this slice put there and that the marker string
      is spelled identically everywhere.

- [ ] **Step 5: Mechanical pass** over every document this task edited: links, anchors, table
      column counts, whitespace, tabs, invisible unicode, `×` for multiplication, hyphen not en
      dash. Skip fenced code blocks.

- [ ] **Step 6: Cross-document pass.** The four documents only. Check the classes that actually
      drift: the worked example (`cohort-pilot` — untouched by this slice, confirm), config
      completeness (no field added, confirm § The one config file's fenced example is unchanged),
      enum comments (task 5 step 4's check), schema fields in prose, declared-vs-derived, versions
      (`CITATION.cff` unchanged — this slice bumps nothing), prevented mistakes.

- [ ] **Step 7: Mutation — the sweeps themselves.** For each `grep` above, run it once against a
      string **known to be present** in the same file list and confirm it hits:

```
grep -n "publishable" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md | head -3
grep -rn "BaseTemplate" src/publishable/ | head -3
grep -rn "def test_" tests/ | head -3
```

A sweep that cannot hit is a sweep that proves nothing. **Record the three confirmations in the task
report.**

- [ ] **Step 8: Verify and commit.** All four commands.
      `docs: the owned prose sweep for the credential family, over named files`

---

