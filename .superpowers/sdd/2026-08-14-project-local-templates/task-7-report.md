# Task 7 report: collision and shadow are refused, naming both providers

## What shipped

`E-TEMPLATE-COLLISION` is minted, raised as `ContractError`, and reported by `validate`.

**Two refusals, two places, and the split is forced.**

- **local × local** — `discovery.discover_local`. It is the only place that holds a claiming
  file's path, and it holds every claim because discovery is eager. Raised after every file
  has been imported, and colliding names are scanned in **name order**, not in the order the
  files were read: the refusal exists because import order is a property of a machine, so
  import order may not decide which fault gets reported either.
- **local shadows `generic`** — `registry._merged`. `registry` imports `discovery` at module
  level, so a module-level `_BUILTIN` import in `discovery` is a cycle (the parent's
  constraint 1). Of the three permitted routes — deferred import, relocate `_BUILTIN`, or put
  the check at the merge — the merge is the one with an argument behind it rather than a
  workaround: `_merged` is the first place that holds both sides, the interim merge-order
  docstring being retired lives in that same module, and the refusal is of the **repo** rather
  than of one lookup, so `template_names(root)` and `get_template("something_else", root)` are
  refused too. After the check there is no overlap left for a merge order to express, which is
  what makes the retirement real rather than cosmetic.

**The return shape changed:** `discover_local(repo_root) -> dict[str, LocalTemplate]`, where
`LocalTemplate` is a `NamedTuple` of `cls` and `provider`. The parent called the old signature
reviewed; the path could not be threaded any other way (constraint 3 — task 6's `sys.modules`
restore deletes the module, so `inspect.getfile(cls)` raises), and the shadow check needs the
local path to name the provider a user can actually rename. A `NamedTuple` rather than a bare
tuple so the two existing call sites in the tests read `found["alpha"].cls` rather than `[0]`.

**A provider is `<path>::<ClassName>`, not a path.** Two `@register_template` calls in one file
are a local × local collision that `drain_pending` hands over as two claims; a message built
from paths alone would print one path twice and name no second provider at all. Core's own
claimant is named as its dotted class path (`publishable.templates.builtin.generic.GenericTemplate`),
there being no file in the user's repo to rename.

**`validate` reports rather than raises.** `validate_config` wraps `get_template` in
`except ContractError` and reports under `exc.code` — the raise's own code, so the two surfaces
stay one fault — then returns `None`, since which template a name means is exactly what a
collision leaves unanswered. Every other command meets the raise and prints the same identifier
through `main`'s `except PublishableError`.

## Tests

Five added, `tests/test_templates.py`; two existing assertions updated for the new return shape.

| Test | What it pins |
|---|---|
| `test_two_local_files_claiming_one_name_are_refused_naming_both` | Both providers named; **a third file claiming a different name is asserted absent from the message** |
| `test_one_file_claiming_one_name_twice_names_both_classes` | The degenerate collision names two classes, not one path twice |
| `test_a_local_template_may_not_shadow_a_core_name` | Local path and core's class both named |
| `test_the_shadow_is_refused_however_the_registry_is_asked` | The repo is refused, not one lookup: `template_names`, an unrelated name, and `discover_local` alone still accepting the file |
| `test_validate_reports_a_collision_rather_than_raising` | Finding, not exception; control: the same config without the file reports neither this code nor `E-TEMPLATE-UNKNOWN` |

**The control** the brief names — two files claiming *different* names resolving cleanly — is
the existing `test_discovery_imports_every_file_not_only_the_named_one`, which every mutation
below left passing.

**The dimension the first draft could not see** (the parent's "six checks that could not fail"):
a two-file test asserting both paths appear also passes an implementation that dumps every
globbed file into the message. The third file, asserted *absent*, is what closes it, and it is
the only assertion mutation 3 below kills.

## Mutations — applied, run, reverted, verified by behaviour

| Mutation | Result |
|---|---|
| Report only the first provider (`providers[0]`) | `..._naming_both` and `..._names_both_classes` FAIL; control PASS |
| Allow the shadow (`if False` at the `_BUILTIN` check) | the three shadow/validate tests FAIL; control PASS |
| Name every provider discovery saw, not the claimants | `..._naming_both` FAIL on the third-file assertion alone; control PASS |

Each reverted, `__pycache__` deleted, and the suite re-run green — verified by re-running the
tests, not by `git status`.

## Documents

- **§ Errors `validate` reports** — new `E-TEMPLATE-COLLISION` row in sort order, before
  `E-TEMPLATE-RULE`. The intro's *"Three faults return `validate_config` early, in this order"*
  is now **four**, with the collision third, and the paragraph that walks the consequences was
  rewritten: a collision reports this code exactly once and **not** `E-TEMPLATE-UNKNOWN`, since
  the call that would have resolved the name raised instead of answering it. No row moved by
  the insertion carries a positional phrase, and no phrase locating a row by position was added.
- **§ Validation** — *Template name is claimed once*, beside *Template is installed*.
- **§ Creating a plugin** — the enumerated collision list did not name either case this task
  refuses. It now names two local files, one file claiming twice, and a local shadowing
  `generic`, states the `<path>::<ClassName>` provider form, and says which cases this build
  checks and why the plugin ones wait on entry points.

## Concerns

1. **No row was added to § Errors core raises**, deliberately, and this is the one place I
   depart from advice I was given. That table's own intro scopes it to "the run-time surface,
   **where there is a step to raise into**", and the sibling table calls its own rows "the codes
   a *command* reports". A template collision has no step: it is raised while a command resolves
   a template, and every command turns it into a printed diagnostic. The dual-surface precedent
   (`E-DATA-CLUSTER-UNKNOWN`) is a code that genuinely raises into user step code, which this
   one never does. The validate row states the dual surface in prose instead. If a reviewer
   reads the raises table as "anything core raises", this is a one-row addition.
2. **Task 3's interim docstring is retired.** `registry.py`'s module docstring no longer
   describes a merge order that resolves a shadow silently; it describes the refusal and why it
   lives at the merge. The `{**locals, **_BUILTIN}` order survives only as the final dict
   construction, where it can no longer decide anything.
3. **A local shadowing an installed plugin is unbuilt and is named as unbuilt** in both the row
   and § Creating a plugin — H7b's, per the spec's decision 5.
4. **Same-file double registration is in scope and is refused**, which the brief did not name.
   It is local × local by any reading, and leaving it to be discovered would have shipped a
   message that names one provider twice.
5. `discover_local` alone still accepts a local `generic`. That is asserted, not incidental —
   it is the boundary that keeps the module free of core's name list — but it means a future
   caller of `discover_local` that bypasses `_merged` would bypass the shadow refusal. There is
   no such caller today.

---

## Review round 1 — three findings addressed

**1 (Important) — the stale count four lines from the one I checked.** `E-CONFIG-TYPE` and
`E-CONFIG-KEY-UNKNOWN` are found "before **either of the later two** returns is possible";
`check_envelope` runs inside `_check_shape`, so the returns after it are shape, collision, and
unknown. Now *"before any of the later three returns is possible"*. The finding is correct about
the process failure too: my count check was a grep for the phrase I had edited (`"Three faults"`,
`"all three have passed"`) rather than a read of the paragraph the insertion lands in. The
standing rule is that an insertion invalidates counts **near** it. Re-read as a paragraph, not
grepped: `"those same two envelope rows"` is still two, and `"those six"` in the raises table is
still six (five `E-RUN-*` plus `E-REPL-ORDER-UNRESOLVED`, none of which my row joins).

**2 (Important) — the row is now in § Errors core raises too.** My reconcile rested on the
intro's "where there is a step to raise into", and the evidence against it is decisive: the
table's own closing prose concedes the `E-RUN-*` six are not raised in an execution, and
`E-STEP-NAME-COLLISION`/`E-STEP-SCOPE-UNKNOWN` are raised as an experiment loads. Dual-surface
codes appear in both registries by convention. Added beside the load-time pair, and the three
prose claims the insertion falsified were fixed with it:

- the `E-RUN-` paragraph's *"unlike every row above, none of the six is raised inside an
  execution"* now names the load-time rows it was already wrong about, and is stated by code
  rather than by position;
- the closing *"the hierarchy above covers **exactly** the run-time surface"* now names the
  load-time surface as well and says why a code can sit in both;
- § Errors `validate` reports' own intro made the same "exactly the run-time surface" claim in
  the other direction, and was corrected to match.

No positional phrase was introduced: my first draft of the new row said "beside
`E-STEP-NAME-COLLISION` **above**", which is precisely the banned construction, and it is gone.

**3 (Minor) — stacked decorators no longer print one provider twice.** Two
`@register_template("dup")` on **one class** produce two claims with the same
`<path>::<ClassName>`, which is the failure the suffix exists to prevent. Providers are now
deduped for the message: with two distinct providers it reads `A and B … Rename one.`; with one,
`A, twice by the same class … Remove one.` — the remedy differs because deleting a line, not
renaming anything, is what fixes it. Still refused either way: a name claimed twice is refused
however it was claimed. Test:
`test_stacked_decorators_are_refused_without_naming_one_provider_twice`, which asserts the
provider appears exactly **once**. The suffix's justification in `reference.md` § Creating a
plugin, in the validate row, and in the `LocalTemplate` docstring was narrowed to "two classes in
one file" and now states this residue instead of claiming coverage of it.

**Mutations re-run against the changed message builder** (in-place `python3` replace both ways —
never a git-level revert on a file with uncommitted work, which is what cost a rewrite earlier):

| Mutation | Result |
|---|---|
| Join the raw `providers` (no dedupe) for every message | the stacked test FAILS; the two/three-file and shadow tests PASS |
| Name only `distinct[0]` | both naming tests FAIL; stacked and control PASS |

**Verification:** `uv run pytest` 1663 passed / 2 xfailed, `ruff check .` and `mypy` clean.
Mechanical pass re-run over the whole of `reference.md` (and every tracked `*.md` for whitespace,
tabs, and invisible unicode): every `#anchor` resolves, no duplicate heading anchors, all three
edited or inserted table rows carry exactly three pipes, and the only column-count mismatches are
the three pre-existing blocks whose cells contain escaped `\|` inside code spans — unchanged from
`main`.
