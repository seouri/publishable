## Task 2: § Errors core raises + § Creating a plugin — the four load-time refusals with no identifier

**Files:** Modify `docs/reference.md`. No `src/` change, no test change.

**Interfaces:**
- Consumes: § Creating a plugin's paragraph beginning **"A name is claimed once, and a collision is
  refused rather than resolved"**, which enumerates the cases in prose and today closes with "The
  two local cases are the ones this build checks"; § Errors core raises' table row whose `Type ·
  code` cell is `ContractError · E-TEMPLATE-COLLISION`; § Errors `validate` reports' row for the
  same code, whose closing clause reads "A local name an **installed plugin** registers is the same
  fault and is not yet checked".
- Produces: § Errors core raises rows for `E-PLUGIN-COLLISION`, `E-PLUGIN-DECORATOR` and
  `E-PLUGIN-LOAD`; `E-TEMPLATE-COLLISION`'s two rows extended to the three plugin template cases;
  and the recorded decision that **neither** § Errors' five-code early-return count **nor**
  `validate.py`'s "two codes" comment moves.

**The decision this task exists to make, and it is a negative one.** The re-scoping's § 6 narrowed
this task to exactly one question: does a plugin-side load fault add a *code* to the set that can
reach `validate_config`'s `except ContractError` guard? **It does not.** A plugin-side **template**
collision is decided inside `_claims`, which `resolve_template` calls, so it arrives at that guard
as `E-TEMPLATE-COLLISION` — a code already counted. The three new codes are reported by checks that
do not raise into it: `E-PLUGIN-COLLISION` by the non-template collision check task 8 adds to
`validate_config`'s check list; `E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD` by helpers with no
production caller in Part A at all. So "Five faults" stays five and "two codes" stays two, and this
task writes the distinction down so the next reader does not increment a number that must not move.

**Why the four cases are not one code.** § Creating a plugin's paragraph puts five things in one
sentence: two installed plugins registering one name, a plugin registering `generic`, a plugin
claiming an extension core already writes, two local files registering one name, and a local file
taking an installed name. Three of those are **template** names and belong under
`E-TEMPLATE-COLLISION`, whose row already states the rule and the reason and whose message names
providers. The writer-suffix case is not a template name at all, and a reader who greps
`E-TEMPLATE-COLLISION` for a `.fastq.gz` fault finds a row about `templates/`. Hence
`E-PLUGIN-COLLISION` for the non-template groups.

- [ ] **Step 1: Read all three sites and confirm each still reads as measured.** § Creating a
      plugin's collision paragraph, § Errors core raises' `E-TEMPLATE-COLLISION` row, and § Errors
      `validate` reports' `E-TEMPLATE-COLLISION` row. Then read § Errors `validate` reports'
      early-return paragraph and count its enumerated faults — `E-CONFIG-PARSE`, container-shaped
      `E-CONFIG-SHAPE`, `E-TEMPLATE-LOAD`, `E-TEMPLATE-COLLISION`, `E-TEMPLATE-UNKNOWN` — five — and
      `validate.py`'s comment inside `validate_config`'s `except ContractError` guard, which reads
      "two codes". Confirm both, and change **neither**.

- [ ] **Step 2: Add three rows to § Errors core raises' table** (`| Raised by | Type · code |`).
      Place them after the row that reports **a project-local `templates/*.py` failing to load**,
      which is the nearest sibling by subject; name it that way and not by position.

```
| One entry-point key claimed by two installed distributions in [`publishable.resolvers`, `publishable.probes`, `publishable.writers` or `publishable.readers`](#creating-a-plugin-publishable-plugin-new), or a [writer](#steps-and-artifacts) claiming a suffix core itself writes. Decided over the **complete** claim set for the group and reported in **name order**, not in the order the metadata scan happened to walk one: install order is a property of a machine rather than of a design, so it may not decide which fault is reported either. The message names every distribution that claimed the key, as `<distribution> <version>`, which is what a reader uninstalls. The template groups' equivalent is `E-TEMPLATE-COLLISION` rather than this code, since a template name has a second home — [the project's own `templates/`](#templates-where-parameters-are-defined) — and one row cannot state both sets of providers | `ContractError` · `E-PLUGIN-COLLISION` |
| A [`@register_*` argument](#creating-a-plugin-publishable-plugin-new) disagreeing with the entry-point key that named it. The entry point is the registration and the decorator is a declaration checked against it, so two spellings of one name with no rule for which is canonical is refused rather than resolved — the [defaults-file argument](#there-is-no-separate-defaults-file) again. Reached only where the object behind a key is actually loaded, which is `run` and `dry-run`: `validate` answers a name from metadata and never holds the decorated object, so **`validate` cannot see this disagreement**, and that is a property of the guarantee rather than a gap in the check | `ContractError` · `E-PLUGIN-DECORATOR` |
| An entry point whose module raises while importing, or calls `sys.exit()` at module scope. `SystemExit` is a `BaseException` and so needs its own `except` — a plugin building an `argparse` parser at import would otherwise end the command with the plugin's own exit code and no diagnostic at all. Reached at the same two commands `E-PLUGIN-DECORATOR` is, and for the same reason: `validate` never imports a plugin. The fault names the entry point and the distribution rather than the module, since a distribution is what a reader uninstalls or pins | `ContractError` · `E-PLUGIN-LOAD` |
```

- [ ] **Step 3: Extend `E-TEMPLATE-COLLISION` to the three plugin cases, in both of its rows.** In
      § Errors core raises, replace the row's opening clause "A template name claimed twice as a
      repo's `templates/` is discovered and merged — two local registrations of one name, or a local
      registration of a name core itself registers" with:

```
| A template name claimed twice as core's own registry, an [installed distribution's](#creating-a-plugin-publishable-plugin-new) `publishable.templates` entry points, and a repo's [`templates/`](#templates-where-parameters-are-defined) are merged — two local registrations of one name, a local registration of a name core itself registers, two installed distributions registering one name, an installed distribution registering a name core itself registers, or a local registration of a name an installed distribution registers. Decided over the complete claim set from all three sources and reported in name order. An installed claimant is named as `<distribution> <version>`, a local one as `<path>::<ClassName>`, and core's own as its dotted class path — each being what a reader changes to resolve it. **An installed claimant is a name, never a class:** the claim is read from package metadata, so no plugin is imported to decide a collision, which is the guarantee [§ Creating a plugin](#creating-a-plugin-publishable-plugin-new) states and the reason a refused installed claim carries no credential to redact.
```

      In § Errors `validate` reports, **delete** the row's closing clause "A local name an
      **installed plugin** registers is the same fault and is not yet checked: no entry point is
      resolved in this build, so there is no second claimant for core to see" — the claim is now
      false and deleting it is preferred to rewriting it. Replace nothing; the row's opening, which
      task 8 amends, carries the cases.

- [ ] **Step 4: Amend § Creating a plugin's collision paragraph.** Its closing sentence reads "The
      two local cases are the ones this build checks, and `E-TEMPLATE-COLLISION` is the code all of
      them carry — the plugin cases arrive with entry-point resolution, and until then there is no
      installed template for a local one to collide with." Replace it with:

```
[`E-TEMPLATE-COLLISION`](#errors-validate-reports) is the code every **template** case carries and [`E-PLUGIN-COLLISION`](#errors-core-raises) is the code the other four groups carry, including a writer claiming a suffix core already writes: a template name has a second home in a project's own `templates/`, and one row cannot state both sets of providers.
```

      Do not add a build-state marker to that sentence: task 8 lands the check and task 5 owns the
      `NOT BUILT` sweep.

- [ ] **Step 5: Record that neither count moves.** In § Errors `validate` reports' early-return
      paragraph, immediately after the sentence beginning "That is five *codes*", add:

```
A plugin-side collision adds no sixth: an installed distribution's template claim is decided in the same merge a local one is, so it arrives here as `E-TEMPLATE-COLLISION` — a code already counted. The identifiers a plugin registry mints for its other groups ([`E-PLUGIN-COLLISION`](#errors-core-raises), `E-PLUGIN-DECORATOR`, `E-PLUGIN-LOAD`) are reported by checks that do not return early, so none of them reaches this list either.
```

- [ ] **Step 6: Mechanical pass** over every edited region: anchors resolve, table rows have exactly
      two cells, no trailing whitespace, no tab, no invisible unicode. Skip fenced blocks. Then
      **sweep the four documents by name** for `is not yet checked` and read each surviving hit —
      the ones this task did not delete belong to task 5.

- [ ] **Step 7: Verify.** `uv run pytest` → **1999 passed, 2 xfailed**. `uv run ruff format --check .`
      → 76 files, 0 to reformat.

- [ ] **Step 8: Mutation — none reaches this task, and the reason is worth stating.** Both count
      phrases are unpinnable: nothing in the suite reads `validate.py`'s comment text or
      `reference.md`'s "Five faults" sentence, so changing either number leaves all 1999 tests
      green. Do **not** manufacture a test that greps a document for a number. The three new rows
      are closed later — **`E-PLUGIN-COLLISION` by tasks 8 and 14**, which pin its message by
      fragment. **`E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD` are pinned by tasks 16 and 17 at the unit
      level only**, since neither has a production caller in Part A; no task in this slice reaches
      them end to end, and that is stated in those tasks rather than hidden here. The verification
      available here is step 1's re-read.

- [ ] **Step 9: Commit.** `docs: the four load-time refusals get identifiers, and neither count phrase moves`

---

