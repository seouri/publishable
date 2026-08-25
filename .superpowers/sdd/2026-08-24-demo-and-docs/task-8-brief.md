## Task 8

**Binding corrections: 21, 22, 27, 30.**

**`list-templates`.** Takes no arguments; walks up from `Path.cwd()`; **catches `E-GIT-NO-REPO` by
type**, leaving `repo_root=None`, and **prints one line saying no repository was found so no
`templates/**` was searched.** A shorter list with no explanation is the *silently skipped* fault.

> **RULING FF (binding, restated here)** — see task 7 for the sentence. **And it rejects
> `H9-SCOPING.md` § 7.2's own preferred answer**, which is to narrow `list-templates` to the installed
> set and never a local template. **Do not build the narrower thing.** A project-local template is the
> case § Templates says path discovery exists for, and it is the case task 6's region needs.

**Output:** every claim `_claims(repo_root)` returns, in name order — name, provenance
(`core` | `local` | `installed`), provider — with the full `parameter_spec` for `core` and `local`.
**An `installed` name prints its provider and one line saying its spec is not readable in this build**
(correction 21), citing `E-TEMPLATE-INSTALLED-UNSUPPORTED`. **Do not import a plugin to read a spec**:
that would make this the one command in the build that loads what every other surface refuses to load.

`E-TEMPLATE-COLLISION` is **not** caught — it reaches `main`, the same answer `validate` gives.

**Fixture D (design § 9):** two local templates, `aaa_probe` and `zzz_probe`, **one on each side of
`generic` in sort order**, plus a fake installed entry point. Two on each side because *a decoy whose
sort position agrees with the bug* has been hit twice here, and because **two elements only ever
distinguish two orderings**.

**Mutations:** design § 10 rows 7, 8, 9. Row 7's assertion needs a **sentinel module that records its
own import**, not an absence of output.

**Also yours:** § Operation commands' `list-templates` row is narrowed to what this builds. Write the
replacement wording in your report; **task 14 makes the edit**, so the four documents move in one task.

---

