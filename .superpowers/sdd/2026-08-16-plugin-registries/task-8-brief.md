## Task 8: The collision matrix, over metadata only

**Files:** Modify `src/publishable/templates/registry.py`, `src/publishable/validate.py`,
`docs/reference.md`, `tests/test_templates.py`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `plugins.scan_group`, `plugins.provider_of` (task 7);
  `registry._merged(repo_root: Path | None) -> dict[str, type[BaseTemplate]]`, which today builds
  `local = discover_local(repo_root)`, raises `PartialLoadError` for a local name in `_BUILTIN`, and
  returns `{name: found.cls for name, found in local.items()} | _BUILTIN`;
  `discovery.LocalTemplate(cls, provider)`; `discovery.PartialLoadError(message, *, code,
  partial_templates)`.
- Produces:
  - `registry.Claim` — a `NamedTuple` carrying `provider: str` and `cls: type[BaseTemplate] | None`.
    **`cls` is `None` for an installed claim and that is the point**, not an omission. **Task 9 adds
    a third field in front of these two**, so every construction here is written with keywords: a
    positional call would silently rebind when that field lands, and this is the cheapest place to
    make that impossible.
  - `registry._claims(repo_root: Path | None) -> dict[str, Claim]` — the merge, over all three
    sources, having decided every collision.
  - `_merged` rebuilt on `_claims`, still returning only the names whose claim carries a class.
  - `validate._check_plugin_collisions(c: Collector) -> None` — `E-PLUGIN-COLLISION` over the four
    non-template groups, called from `validate_config`.

**The matrix, and why two distributions.** The cases are entry-point × entry-point, × core, × local.
**One installed distribution cannot produce the first arm at all**, so the fixture proves the others
by accident if it has one — that is the trap this task is named in. Two distributions, in two
directories, per the fixture's own docstring.

**Name order, not discovery order.** Providers are named in the message and the *name* reported when
several collide is the first in name order. `discover_local` already establishes both properties for
the local-vs-local case and its comment says why; `_claims` takes the same shape rather than
inventing a second one. The re-scoping's probe is the live evidence that walk order is not name
order: `entry_points(group=…)` returned `dist-two` before `dist-one` for one arrangement.

**No `.load()`.** An installed claim is a name and a provider. Deciding a collision from metadata is
the whole reason the mechanism exists, and it is also why task 20's residual exists: a refused
installed claim carries no class, so nothing of its credentials can be redacted.

**Do not change `discover_local`.** Two local claims of one name still raise inside it, before
`_claims` sees anything, which is why every existing local-collision test stays green untouched.
Run those tests and observe them green rather than assuming it.

**Names already at module level in `tests/test_templates.py`:** `_modules_under`,
`_two_repos_each_holding_my_assay`, `ALPHA_TEMPLATE`, `BETA_TEMPLATE`, `REAL_ONE_TEMPLATE`,
`DUNDER_TEMPLATE`, `CLAIMS_DUPLICATED_A`, `CLAIMS_DUPLICATED_B`, `CLAIMS_TWICE_ON_ONE_CLASS`,
`CLAIMS_GENERIC`, `CLAIMS_TWICE_IN_ONE_FILE`, `RAISES_ON_IMPORT`, `REGISTERS_NOTHING`, plus the
`test_*` functions. `CLAIMS_MY_ASSAY` is free.

- [ ] **Step 1: Read the two existing shadow tests before touching the message.**
      `test_a_local_template_may_not_shadow_a_core_name` asserts three fragments of the raise's
      text — `"generic"`, `f"{templates / 'mine.py'}::LocalGeneric"`, and
      `"publishable.templates.builtin.generic.GenericTemplate"` — and
      `test_the_shadow_is_refused_however_the_registry_is_asked` asserts the code from three entry
      points. Any message you write must keep all three fragments. Read both bodies now; a message
      rewrite that drops one is the failure this step exists to prevent.

- [ ] **Step 2: Write the failing tests.** Append to `tests/test_templates.py`:

```python
CLAIMS_MY_ASSAY = """\
from publishable import BaseTemplate, register_template


@register_template("my_assay")
class LocalAssay(BaseTemplate):
    parameter_spec = {}
"""


def test_two_installed_distributions_claiming_one_template_name_are_refused(installed, tmp_path):
    """Entry-point × entry-point — the arm one distribution cannot produce.

    Both providers are named, as `<distribution> <version>`, which is what a
    reader uninstalls. Decided from metadata: neither module exists, so a
    verdict that reached for either class would raise `ModuleNotFoundError`
    instead of reporting.
    """
    installed("dist-two", "2.0", {"publishable.templates": {"my_assay": "no_two:T"}})
    installed("dist-one", "1.0", {"publishable.templates": {"my_assay": "no_one:T"}})

    with pytest.raises(ContractError) as excinfo:
        get_template("my_assay", tmp_path)
    assert excinfo.value.code == "E-TEMPLATE-COLLISION"
    message = str(excinfo.value)
    assert "my_assay" in message
    assert "dist-one 1.0" in message
    assert "dist-two 2.0" in message


def test_an_installed_distribution_may_not_shadow_a_core_name(installed, tmp_path):
    """Entry-point × core. Core's claimant is named as its dotted class path,
    there being no file to rename."""
    installed("dist-one", "1.0", {"publishable.templates": {"generic": "no_one:T"}})

    with pytest.raises(ContractError) as excinfo:
        get_template("generic", tmp_path)
    assert excinfo.value.code == "E-TEMPLATE-COLLISION"
    message = str(excinfo.value)
    assert "dist-one 1.0" in message
    assert "publishable.templates.builtin.generic.GenericTemplate" in message


def test_a_local_template_may_not_shadow_an_installed_one(installed, tmp_path):
    """Entry-point × local, and the case that needs both a repo and a
    distribution. Both providers are named in their own spelling — a path and a
    class for the local one, a distribution and a version for the installed."""
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "mine.py").write_text(CLAIMS_MY_ASSAY)
    installed("dist-one", "1.0", {"publishable.templates": {"my_assay": "no_one:T"}})

    with pytest.raises(ContractError) as excinfo:
        get_template("my_assay", tmp_path)
    assert excinfo.value.code == "E-TEMPLATE-COLLISION"
    message = str(excinfo.value)
    assert f"{templates / 'mine.py'}::LocalAssay" in message
    assert "dist-one 1.0" in message


def test_the_colliding_template_name_reported_is_the_first_in_name_order(installed, tmp_path):
    """Three colliding names, installed in an order that is neither sorted nor
    reverse-sorted, so neither candidate reading of "which one is reported"
    survives. Two names could not tell them apart.
    """
    claims = {"m_two": "no:T", "a_one": "no:T", "z_three": "no:T"}
    installed("dist-two", "2.0", {"publishable.templates": claims})
    installed("dist-one", "1.0", {"publishable.templates": claims})

    with pytest.raises(ContractError) as excinfo:
        get_template("a_one", tmp_path)
    assert "`a_one`" in str(excinfo.value)
    assert "m_two" not in str(excinfo.value)
    assert "z_three" not in str(excinfo.value)


def test_a_clean_installed_claim_is_not_a_collision(installed, tmp_path):
    """THE HONOURING, and the control that makes every refusal above about a
    collision rather than about installing anything at all: one distribution
    claiming a name nothing else claims raises nothing, and the name is known.
    """
    installed("dist-one", "1.0", {"publishable.templates": {"my_assay": "no_one:T"}})
    assert "my_assay" in template_names(tmp_path)
    assert get_template("my_assay", tmp_path) is None  # known, and not loaded — decision 3
```

      And append to `tests/test_validate.py`:

```python
def test_two_installed_distributions_claiming_one_resolver_name_are_reported(
    installed, write_config
):
    """`E-PLUGIN-COLLISION` over a non-template group, reported rather than
    raised, and reported for a repo whose config names no resolver at all — a
    registry core cannot make sense of is refused however it is asked.

    Asserted ALONGSIDE nothing: this config declares a table source, so
    `E-DATA-RESOLVER-UNSUPPORTED` is not in play. The resolver-adjacent
    companion is the second half of this test.
    """
    installed("dist-two", "2.0", {"publishable.resolvers": {"plate_wells": "no_two:r"}})
    installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "no_one:r"}})

    found = messages_by_code(write_config())
    message = found["E-PLUGIN-COLLISION"]
    assert "publishable.resolvers" in message
    assert "plate_wells" in message
    assert "dist-one 1.0" in message
    assert "dist-two 2.0" in message

    # Alongside, never instead of: a config that DOES name a resolver still
    # carries the wholesale refusal. Part B deletes this one line.
    both = codes(write_config({"data.units.from": {"resolver": "plate_wells"}}))
    assert "E-PLUGIN-COLLISION" in both
    assert "E-DATA-RESOLVER-UNSUPPORTED" in both


def test_one_distribution_per_plugin_name_reports_nothing(installed, write_config):
    """THE CONTROL. A check that reported unconditionally would pass the test
    above; this is what makes that one about a collision."""
    installed(
        "dist-one",
        "1.0",
        {
            "publishable.resolvers": {"plate_wells": "no_one:r"},
            "publishable.probes": {"assay_instrument": "no_one:p"},
        },
    )
    assert "E-PLUGIN-COLLISION" not in codes(write_config())
```

- [ ] **Step 3: Run and see them fail.** `uv run pytest tests/test_templates.py tests/test_validate.py -q`.
      The five template tests fail because no installed claim reaches the merge (four raise nothing;
      `test_a_clean_installed_claim_is_not_a_collision` fails on `template_names`). The two validate
      tests fail on `KeyError: 'E-PLUGIN-COLLISION'` and, for the control, pass already — a control
      that passes before the implementation is expected and is not evidence of anything until its
      sibling passes too.

- [ ] **Step 4: Implement the merge.** In `src/publishable/templates/registry.py`, add the import
      `from publishable.plugins import provider_of, scan_group`, add `NamedTuple` to the `typing`
      import, and replace `_merged` with:

```python
class Claim(NamedTuple):
    """One registration of one template name, and who made it.

    `cls` is `None` for an installed claim, and that is the mechanism rather than
    a gap: an entry point is resolved from package metadata, so core knows the
    name and the distribution without importing a line — see `plugins.py`. The
    consequences are that an installed name is *known* and not *resolvable* in
    this build, and that a refused installed claim carries no class whose
    declarations could be read.
    """

    provider: str
    cls: type[BaseTemplate] | None


def _claims(repo_root: Path | None) -> dict[str, Claim]:
    """Every claim on every template name, from all three sources, verdict reached.

    The three sources are core's own registry, the installed distributions'
    `publishable.templates` entry points, and — when a repo root is given — that
    repo's `templates/`. Collected in full before any verdict, on
    `discover_local`'s precedent and for its reason: a verdict reached while a
    claim set was still partial is a verdict over the wrong set. Reported in name
    order, and claimants within a name in provider order, because install order
    and import order are properties of a machine rather than of a design.

    Two local registrations of one name never reach here — `discover_local`
    refuses that pair itself, knowing what a repo declares — so this function
    sees at most one local claimant per name.
    """
    claims: dict[str, list[Claim]] = {}
    for name, core in _BUILTIN.items():
        claims.setdefault(name, []).append(
            Claim(provider=f"{core.__module__}.{core.__qualname__}", cls=core)
        )
    for name, entries in scan_group("publishable.templates").items():
        for ep in entries:
            claims.setdefault(name, []).append(Claim(provider=provider_of(ep), cls=None))
    local = discover_local(repo_root) if repo_root is not None else {}
    for name, found in local.items():
        claims.setdefault(name, []).append(Claim(provider=found.provider, cls=found.cls))
    for name in sorted(claims):
        if len(claims[name]) > 1:
            who = " and ".join(sorted(claim.provider for claim in claims[name]))
            raise PartialLoadError(
                f"the template name `{name}` is claimed more than once: {who} — a "
                "template that could redefine another's name could change what a "
                "config means without changing the config, which is what "
                "`parameters_hash` exists to make impossible. Install order and "
                "import order are the only tie-breaks available, and both are "
                "properties of a machine rather than of a design. Rename yours.",
                code="E-TEMPLATE-COLLISION",
                partial_templates=[
                    claim.cls
                    for these in claims.values()
                    for claim in these
                    if claim.cls is not None
                ],
            )
    return {name: these[0] for name, these in claims.items()}


def _merged(repo_root: Path | None) -> dict[str, type[BaseTemplate]]:
    """The names this build can hand back a class for: core's and this repo's.

    An installed name is in `_claims` and not here. `template_names` reads
    `_claims`, so the name is known; `get_template` reads this, so it is not
    resolved — see `Claim.cls`.
    """
    return {
        name: claim.cls for name, claim in _claims(repo_root).items() if claim.cls is not None
    }
```

      Then change `template_names` and `resolve_template`'s known-name list to read `_claims`:

```python
def template_names(repo_root: Path | None = None) -> list[str]:
    return sorted(_claims(repo_root))
```

      and in `resolve_template`, replace `merged = _merged(repo_root)` /
      `return (cls() if cls else None), sorted(merged)` with a single `_claims` call so the
      docstring's "one merge" promise still holds:

```python
    claims = _claims(repo_root)
    claim = claims.get(name)
    cls = claim.cls if claim is not None else None
    return (cls() if cls else None), sorted(claims)
```

      **`_claims` is called once per `resolve_template`, exactly as `_merged` was** — the
      docstring's argument is that asking for the two halves separately would import every
      `templates/*.py` twice, and that argument is unchanged.

- [ ] **Step 5: Implement the non-template check.** In `src/publishable/validate.py`, add
      `from publishable.plugins import provider_of, scan_group` and:

```python
def _check_plugin_collisions(c: Collector) -> None:
    """One entry-point key claimed by two installed distributions, outside templates.

    Templates are not here: a template name has a second home in a project's own
    `templates/`, so its verdict is reached at the merge that holds all three
    sources and is reported as `E-TEMPLATE-COLLISION`. These four groups have one
    source each, so the verdict is a property of the machine's installed set
    alone and is reported wherever it is noticed.

    Reported rather than raised, and reported for every config rather than only
    for one naming a colliding key: a registry core cannot make sense of is
    refused however it is asked, which is the same shape `_claims` takes for a
    `templates/` core cannot merge. Read from metadata, so no plugin is imported
    to reach a verdict.
    """
    for group in GROUPS:
        if group == "publishable.templates":
            continue
        for name, entries in scan_group(group).items():
            if len(entries) > 1:
                who = " and ".join(sorted(provider_of(ep) for ep in entries))
                c.error(
                    "E-PLUGIN-COLLISION",
                    "plugin",
                    f"key `{name}` in the `{group}` entry-point group is claimed by "
                    f"{who} — install order is the only tie-break available and it is "
                    "a property of a machine rather than of a design. Uninstall one",
                )
```

      Import `GROUPS` alongside `provider_of`/`scan_group` — and note that task 13 adds `names` to
      the same import line, so leave it as a parenthesized multi-name import that `ruff`'s `I` rule
      is happy to extend. Call it from `validate_config`
      immediately after `_check_entrypoint`, which is the nearest check that is also about what the
      machine supplies rather than what the config declares — name that neighbour in the commit
      message rather than a position.

- [ ] **Step 6: Update `reference.md`.** In § Errors `validate` reports' `E-TEMPLATE-COLLISION` row,
      replace the opening clause "A template name is claimed twice where this build can see both
      claimants: two [project-local `templates/*.py`](#templates-where-parameters-are-defined)
      registrations of one name — in two files, or twice in one file — or a local registration of a
      name core itself registers (`generic`)" with:

```
| A template name is claimed twice across core's own registry, the [installed distributions'](#creating-a-plugin-publishable-plugin-new) `publishable.templates` entry points, and this project's own [`templates/`](#templates-where-parameters-are-defined): two local registrations of one name — in two files, or twice in one file — a local registration of a name core registers, two installed distributions registering one name, an installed distribution registering a name core registers, or a local registration of a name an installed distribution registers.
```

      Leave the rest of the row — the eager-discovery paragraph, the `E-TEMPLATE-LOAD` preemption,
      the provider-naming rules — as it stands; task 2 already extended the § Errors core raises
      twin and deleted the "not yet checked" clause here.

- [ ] **Step 7: Run and see them pass.** `uv run pytest tests/test_templates.py tests/test_validate.py -q`,
      then the whole suite. **Every pre-existing collision and shadow test must still pass
      untouched** — run `uv run pytest tests/test_templates.py -q -k "shadow or claim or collision"`
      and read the list. Expected total: your predecessor's count **+ 7**.

- [ ] **Step 8: Mutate — four, each checked against the test body it must redden.**

  **(a) Skip the installed source.** Delete the `scan_group("publishable.templates")` loop from
  `_claims`. `test_two_installed_distributions_claiming_one_template_name_are_refused`,
  `test_an_installed_distribution_may_not_shadow_a_core_name`,
  `test_a_local_template_may_not_shadow_an_installed_one` and
  `test_a_clean_installed_claim_is_not_a_collision` must all FAIL. **Checked against the bodies:**
  the first three expect a raise the mutant does not make; the fourth asserts `"my_assay" in
  template_names(tmp_path)`, which the mutant cannot satisfy. This is the mutation that proves the
  third source is wired, and the fourth test is the one that proves it for the *non*-colliding case
  — without it, a `_claims` that raised unconditionally on any installed name would pass the first
  three.

  **(b) Verdict in walk order rather than name order.** Change `for name in sorted(claims):` to
  `for name in claims:`. `test_the_colliding_template_name_reported_is_the_first_in_name_order` must
  FAIL. **Checked against the body:** three names are declared in the order `m_two`, `a_one`,
  `z_three` within each distribution, so the mutant reports `m_two` and the test asserts `` `a_one` ``
  is named and `m_two` is not. Two names could not discriminate — with two, the reverse of
  declaration order is sorted order for one arrangement — which is why there are three.

  **(c) Name one claimant instead of all.** Change `who` to `claims[name][0].provider`.
  `test_two_installed_distributions_claiming_one_template_name_are_refused` must FAIL on its
  `"dist-two 2.0"` assertion, and `test_a_local_template_may_not_shadow_an_installed_one` on one of
  its two. **Checked against the bodies:** both assert two distinct provider strings and the mutant
  produces one. Note the pre-existing `test_a_local_template_may_not_shadow_a_core_name` also goes
  red, which is fine — a mutation must fail *at least* the named test.

  **(d) Reach for the class.** In `_claims`, change the installed branch to
  `Claim(provider_of(ep), ep.load())`. **`test_a_clean_installed_claim_is_not_a_collision` must FAIL
  with `ModuleNotFoundError`**, because its fixture's entry point names a module that does not
  exist. **Checked against the body:** the fixture deliberately points at `no_one:T`, so the failure
  is the load and not a assertion — read the traceback and confirm it is `ModuleNotFoundError` from
  `_claims`, not an `AssertionError`. **This is the mutation that pins decision 3**, and it is the
  only one that does; the other three would all pass with `.load()` in place.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green. **Never `git checkout --`.**

- [ ] **Step 9: Which deliverable no mutation reaches.** **`_check_plugin_collisions`' choice of
      reporting path (`"plugin"`) is unpinned** — both new validate tests read
      `messages_by_code`/`codes`, neither of which sees a finding's path, and adding a path
      assertion would pin a field no § Errors row states. Left deliberately; **nothing closes it.**
      **`Claim.provider` for core's own claimant is pinned only through the pre-existing shadow
      test's dotted-class-path fragment**, which is enough — that fragment cannot be produced any
      other way. **The `partial_templates` expression is knowingly still a proxy at this commit** —
      it names `claims.values()` rather than `local.values()`, which is already the right concept,
      but nothing distinguishes them until an installed claim carries a class, which Part A never
      makes it do. **Task 20 documents that residual**; no mutation in this slice reaches it, and
      task 20 says so again rather than claiming otherwise.

- [ ] **Step 10: Verify and commit.** All four commands.
      `feat: the template collision matrix over three sources, decided from metadata`

---

