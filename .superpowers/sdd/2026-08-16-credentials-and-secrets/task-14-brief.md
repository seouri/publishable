## Task 14: `spec-defects.md` filings, and decision 7's routing correction

**Files:** Modify `docs/superpowers/spec-defects.md`.

**Interfaces:** none.

**A ledger line saying "filed" is not a filing.** `CLAUDE.md` records a gap registered "against
\<owner\>" that existed only in a ledger and never in the defects file. Every entry below goes into
`spec-defects.md` itself, with a heading, the measurement, and a named owner. And **re-owner a
deferral when the slice that filed it finishes**: an entry naming its owner as "whichever slice does
X" points at a closed slice once X lands.

**This family has zero entries today** — `grep -n "required_env\|requires_env\|secret\|credential\|\.env"`
over `spec-defects.md` returns five hits, all `provenance.environment` or `.env.example`-in-a-scaffold
prose, and `grep -n "H7c"` returns nothing. Re-run both before writing, since six slices have landed
since the scoping.

- [ ] **Step 1: Re-measure before filing.** Run both greps above. For each entry below, confirm the
      gap is still open by checking the code, not by trusting this brief.

- [ ] **Step 2: File the README `credentials` region, with the routing correction.** Append to
      `docs/superpowers/spec-defects.md`:

```markdown
## OPEN — the generated README's `credentials` region does not exist, so nothing can merge into it

`reference.md` § The generated README shows a scaffolded README carrying a
`<!-- publishable:begin credentials -->` region with a *"(none yet — added as experiments declare
them)"* placeholder row, and a `cp .env.example .env` setup line above it. **Neither is emitted.**
Measured at `d86290c` and re-confirmed for this filing: a freshly scaffolded `README.md` grepped for
`publishable:begin` returns `overview` and `experiments` and nothing else, and `scaffold.py`'s
`README` constant holds no credentials block and no `cp` line. The control — the same grep for the
two regions that do exist — hits both.

Three consequences, in the order they bite. `reference.md` § Generators already marks *"merging any
new `required_env` into the credentials table"* **NOT BUILT** and says in the same paragraph that
`required_env` "compounds that gap rather than merely sharing it" — that half of the sentence is
now stale, since H7c gave the attribute a reader at `validate`; what remains unbuilt is the merge,
not the reader. `publishable docs`, which § The generated README says regenerates every managed
region, is in `cli.NOT_BUILT_COMMANDS`. And a merge built against an absent region would have
nothing to merge into, which is why H7c refused the charter item rather than absorbing it.

**Routing, and it corrects `H7b-SCOPING.md` § 11.** That document routes "the README managed
regions — `credentials`, a parameter-table region, `generate experiment`'s merge" wholesale to
**`docs`**. It is right about the merge and wrong about the region: the *static* `credentials`
region and the `cp .env.example .env` line are written by **`new`**, i.e. `scaffold.py`'s `README`
constant, and `docs` has nothing to populate until they exist.

**Owner:** whichever slice next edits `new`'s README emission owns the region and the setup line;
`docs`'s slice owns regenerating it; `generate experiment`'s merge follows both. Not H7c, and not
H7b.
```

- [ ] **Step 3: File the two unbuilt readers of `required_env`, each with its owning slice.**

```markdown
## OPEN — two specified readers of `required_env` belong to unbuilt commands

H7c made `BaseTemplate.required_env` readable and gave it its first reader, at `validate`. Two more
readers are specified and cannot be built here, because each belongs to a command in
`cli.NOT_BUILT_COMMANDS`. Filed so neither is folded into a slice that has no business with it.

| Specified | Owner |
|---|---|
| `reference.md` § Reproducing on another device, step 6 — `reproduce` *"copies `.env.example` and lists the `required_env` variables that need values"*, and the consequence stated beneath it | **`reproduce`'s slice** |
| `reference.md` § Metering — `dry-run` *"needs what a run needs minus the compute … which means real credentials"* | **`dry-run`'s slice**, which inherits H7c's load site and its two checks without change |

H7c owes only that the attribute is readable, which it now is.
```

- [ ] **Step 4: File `field_convention`, the remaining unread member.**

```markdown
## OPEN — `BaseTemplate.field_convention` is declarable and read by nothing

Measured at `478c1f3`: `grep -rn "field_convention" src/publishable/` returns two declarations
(`templates/base.py`, `templates/builtin/generic.py`) and one comment in `generators/template.py`
saying the `generate template` stub omits it. Nothing reads it. `reference.md` § Naming conventions
& repeat defaults specifies what it means — a naming pattern and a repeat floor per convention
class — and `naming_pattern` and `default_repeats` are both read while the class that groups them
is not.

This is `CLAUDE.md`'s *unbuilt reader of a shipped surface*, and it is now that row's worked
example: H7c retired `required_env` from that role by giving it a reader, and of the three
remaining members `apparatus_probe` is **H7b task 13's** and `apparatus_facts` is **H7d's**, which
leaves this one unowned.

**Owner:** unassigned. Whichever slice next touches § Naming conventions & repeat defaults should
either give it a reader or state in `reference.md` that it is declarative only.
```

- [ ] **Step 5: File `io.reuse_from`.** The spec names it as "unbuilt and unowned by any H7
      sub-slice, which is a gap this slice files rather than closes". **Check first** whether an
      entry already exists — `grep -n "reuse_from" docs/superpowers/spec-defects.md` — and if one
      does, do not file a second; instead check whether its owner still exists and re-owner it if it
      names a closed slice. If none exists, file one naming the `reference.md` section that
      specifies it and marking the owner unassigned.

- [ ] **Step 6: Re-owner anything pointing at "the secrets slice".**

```
grep -n "secrets slice\|H7c\|the credentials slice" docs/superpowers/spec-defects.md
```

Any entry whose owner is "whichever slice does credentials" now points at a **closed** slice. Rewrite
each to name what is actually left and who holds it, or strike it if H7c closed it. **This is the
step that stops an entry reading as live work nobody holds.**

- [ ] **Step 7: Discharge task 6's deferred obligation.** Run
      `git diff 478c1f3 -- src/publishable/__init__.py` and confirm it is **empty** — decision 8's
      claim that this slice exports nothing. Record the result in the commit message.

- [ ] **Step 8: Mechanical pass** over `spec-defects.md`: table column counts, no empty rows, no
      trailing whitespace, no tab, no invisible unicode, hyphen not en dash in anything that becomes
      an anchor, and **no two headings producing the same anchor** — this file is long and heading
      collisions are its most likely mechanical fault. Note that the cross-document pass does
      **not** apply here; `spec-defects.md` is development record, and the one place where a closed
      gap is struck rather than left to mislead.

- [ ] **Step 9: Mutation.** Document-only; **no mutation reaches it**, as with tasks 1, 2, 5 and 6.
      The verification is step 1's re-measurement and step 6's grep. **Do not file an entry you did
      not re-measure**, and say in the task report which measurements were re-run and what each
      returned.

- [ ] **Step 10: Verify and commit.** All four commands (nothing here should move a test, so the
      suite must land exactly where task 12 left it).
      `docs: spec-defects filings for the credential family, with H7b-SCOPING § 11's routing corrected`

---

## Self-review

### Spec coverage — the eight decisions

| Decision | Task |
|---|---|
| 1 — two codes, not one | **1** (the two § Errors rows and the grounds), honoured by **9** and **10** emitting them separately |
| 2 — the totality check is `E-TEMPLATE-LOAD` and owes no row | **3** (the `ValueError` and its end-to-end confirmation), **2** (the count phrases that must not move) |
| 3 — redact by exact value, and say a redaction happened | **12**, at the **two serialization boundaries** per the spec's correction 1: `runner.execute_plan`'s step-error path and `Collector.render()`. `grep -rn 'type(exc).__name__' src/publishable/*.py` returns **five** constructions, four of which are diagnostics rather than records and reach the sweep through stdout |
| 4 — detect by exact value, never by pattern | **7** (`redact`'s implementation and its by-value test), **12** (the blind pattern mutation named as blind) |
| 4a — core redacts only what it read for a declared variable | **12** step 5, marked document-only |
| 5 — two load sites, and the reconciled sentence | **8**, with `draft`/`resume` recorded as unbuilt rather than stubbed |
| 6 — three choices, a sweep selecting two, a third deliberately unset | **10**, with the three readings tabulated and the deviation from `reference.md`'s `[]` example argued |
| 7 — the README region is filed, not built | **14** step 2, including the correction against `H7b-SCOPING.md` § 11 |
| 8 — this slice exports nothing | **6** (the document statement), **14** step 7 (the `git diff` that discharges it) |

### Scoping coverage — the 14

Tasks 1–14 of this plan are the scoping's § 8 tasks 1–14, in its order and its grain. None was
split, merged, or moved. Task 6's `secrets.py` marker retirement is *executed* in task 7's commit
because a build claim must not precede the build; the ownership stays with task 6 and both tasks say
so.

### Placeholder scan

No step says "similar to Task N" or "as above". Every code block is literal. Every type, function and
attribute a later task references is defined in an earlier one: `Param.requires_env` (3) → `comment()`
(4) → the union (10, 11) → `declared_credential_names` (12); `load_env`/`missing_env`/
`credential_values`/`redact` (7) → the load sites (8) → `_check_required_env` (9) →
`_check_requires_env` (10) → `execute_plan(credentials=)` (12); `run_a_project`'s `_env_file` and
`_local_template` (both added in 8) → used by 8 and 12 respectively;
`_UNION_TEMPLATE`/`_UNION_NAMES`/`_union_project` (10) → used by 11; `_findings_of` (11) is defined
where it is first used; `_SENTINEL` and `_files_under` (12) are defined before the three tests that
use them, and `_LEAKY_AZURE_STEP` is defined in 12 step 7 as a copy of `_LEAKY_STEP` from 12 step 1.
`declared_credential_names(doc, template, conditions)` (12) takes three arguments at its definition
and its one call site.

### Type consistency

`requires_env: dict[Any, list[str]] | None` (task 3) is read as `param.requires_env.get(value)` in
tasks 10 and 12, both guarded by `except TypeError` for an unhashable resolved value.
`credentials: dict[str, str] | None` (task 12) matches `credential_values`'s return (task 7).
`redact(text: str | None, values: Mapping[str, str]) -> str | None` (task 7) is called with
`credentials or {}`, so the `Mapping` is never `None`. `missing_env(names: Iterable[str])` is called
with a generator in task 9 and with a `dict` in task 10 — both are `Iterable[str]`.

### Names checked against their target files before use

`param.py`: `_joined` free (module holds `MISSING`, `_TYPE_NAMES`, `Param`); `_choice_label` is a new
method. `tests/test_param.py`: no module-level helpers exist; every new name is new.
`tests/test_validate.py`: `_CRED_TOTALITY_TEMPLATE`, `_REQUIRED_ENV_TEMPLATE`, `_UNION_TEMPLATE`,
`_ABLATABLE_TEMPLATE`, `_UNION_NAMES`, `_union_project`, `_findings_of` — none collides with
`base_config`, `write_config`, `write_config_nondet`, `write_config_broken`, `write_config_exits`,
`_DELETE`, `codes`, `messages_by_code`, `_validate_with`, `_error_codes`.
`tests/test_cli.py`: `_ENV_READING_STEP`, `_LEAKY_STEP`, `_LEAKY_AZURE_STEP`, `_SECRET_USING_STEP`,
`_LOCAL_CRED_TEMPLATE`, `_AGGREGATE_LEAKING_TEMPLATE`, `_SENTINEL`, `_files_under` — none collides
with `Ran`, `run_a_project`, `_AGGREGATE_STEP`, `_TRAIN_TOUCHING_STEP`. `diagnostics.py`:
`Collector.credentials` is a new field on a dataclass whose only field today is `findings`, so no
existing `Collector()` construction changes. `cli.py`: `declared_credential_names`,
`_flatten_parameters` and the `run_template` local are all to be confirmed absent by grep in task 12
step 3 — `template` is deliberately **not** reused, because `command_run` already binds that name
after `execute_plan`. `tests/test_secrets.py` is a new file.
