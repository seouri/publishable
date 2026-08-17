## Task 30: `provenance.plugin_versions`, and the dated *no production caller* notes

**Files:** Modify `src/publishable/plugins.py`, `src/publishable/cli.py`,
`docs/reference.md`, `docs/superpowers/spec-defects.md`, `tests/test_plugins.py`,
`tests/test_cli.py`.

**Interfaces:**
- Consumes: `plugins.provider_of(ep: EntryPoint) -> str`, which returns `f"{dist.name} {dist.version}"`
  — read in `src/publishable/plugins.py`; `plugins.scan_group`; the literal `"plugin_versions": {}`
  in `cli.py`'s provenance document, and `"publishable_version"` beside it, which is
  `importlib.metadata.version("publishable")`.
- Produces: `plugins.versions_for(group: str, name: str) -> dict[str, str]`;
  `provenance.plugin_versions` populated for a resolver-sourced run; the two dated
  *no production caller* notes in `plugins.py` retired; `spec-defects.md`'s shipped-but-unread
  filing amended for the four surfaces this slice reads.

**What it records, from the document.** § Where units come from: *"the resolver's plugin version in
`provenance.plugin_versions`"*, and `design-principles.md` § Whose git hash is this?: *"plugin
versions as `provenance.plugin_versions` — compatibility notes, never conflated with the code that
ran your experiment."* So it is a `{distribution: version}` mapping, and it is **not** part of
`code_hash`: a plugin is pinned by `uv.lock`, which is why nothing here may extend `HASHED_TREES`.

**Only what this run actually used.** A machine's whole installed set is not this run's provenance;
the resolver a config named is. An empty mapping stays the honest record for a run with no plugin
artifact, which is exactly what it records today by accident and will record by construction after
this task.

**The two `deaed2b`-dated notes this task retires** are `plugins.py`'s module docstring
(*"no command has yet been wired to call it"*) and `check_registration`'s (*"no command yet loads a
plugin, so this function has no production caller either"*). The two matching `reference.md` notes
were deleted in task 22 with the sentences that carried them; confirm by sweeping the file list:
`grep -rn "against commit .deaed2b." docs/reference.md src/` → empty after this task.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_plugins.py`:

```python
def test_versions_for_names_the_distribution_a_reader_would_pin(installed):
    """A distribution and its version, because that is what `uv.lock` pins and
    what a reader uninstalls — not a module path, which pins nothing."""
    from publishable.plugins import versions_for

    installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "no_one:resolve"}})
    assert versions_for("publishable.resolvers", "plate_wells") == {"dist-one": "1.0"}
    assert versions_for("publishable.resolvers", "not_registered") == {}
```

      and in `tests/test_cli.py`, an end-to-end assertion through `command_run` on a resolver-sourced
      config (the path is open now that task 26 landed) — model it on the file's existing
      `command_run` tests, and assert the recorded mapping **and** its control:

```python
def test_a_resolver_run_records_the_plugin_version_it_resolved_through(
    installed, registries, git_repo, tmp_path
):
    """`provenance.plugin_versions` — compatibility notes, never conflated with
    `code_hash`, which covers `src/**` and `templates/**` and not a wheel. The
    control is a table-sourced run in the same test: an empty mapping stays the
    honest record where no plugin artifact was used, so a version dict populated
    unconditionally would pass the first half alone."""
    ...  # build the two configs with the file's existing run helper
    assert resolver_run["provenance"]["plugin_versions"] == {"dist-one": "1.0"}
    assert table_run["provenance"]["plugin_versions"] == {}
```

- [ ] **Step 2: Run and see it fail.** `ImportError: cannot import name 'versions_for'`.

- [ ] **Step 3: Implement.** In `src/publishable/plugins.py`:

```python
def versions_for(group: str, name: str) -> dict[str, str]:
    """The distributions providing `name` in `group`, as `{name: version}`.

    A distribution rather than a module, for `provider_of`'s reason: a
    distribution is what a reader uninstalls or pins, and `provenance` exists to
    be reproduced from. Empty for a name nothing registers, which is the same
    answer a run using no plugin artifact records — an absence, not a guess.

    Every claimant, not the first: `validate._check_plugin_collisions` refuses a
    name two distributions claim, so more than one entry here means the record is
    describing a machine `validate` already refused. Recording both is what makes
    that visible in the artifact rather than only in the terminal.
    """
    return {
        ep.dist.name: ep.dist.version
        for ep in scan_group(group).get(name, [])
        if ep.dist is not None
    }
```

      and delete the two dated *no production caller* sentences from the module docstring and from
      `check_registration`'s docstring. **Delete rather than rewrite**: their claim expired, and a
      replacement sentence would be a new maintenance obligation nobody owns.

      In `src/publishable/cli.py`, replace the `"plugin_versions": {}` literal with a local computed
      beside the roster, so the mapping and the resolver that produced it cannot drift:

```python
    # Populated from the declaration this run actually resolved through, not from
    # the machine's installed set: a run's provenance is what it used. Empty stays
    # the honest record for a run with no plugin artifact.
    plugin_versions: dict[str, str] = {}
    _source = (units_decl or {}).get("from")
    if isinstance(_source, dict) and isinstance(_source.get("resolver"), str):
        plugin_versions = versions_for(RESOLVER_GROUP, _source["resolver"])
```

      In `docs/reference.md` § What `run.yaml` records, the `plugin_versions: {}` line in the fenced
      example stays `{}` — the worked example's `cohort-pilot` uses a table source, and changing it
      would break the shared worked example across three documents. Add one sentence to the prose
      naming what fills it.

      In `docs/superpowers/spec-defects.md`, amend
      `## OPEN — PROBES and RESOLVERS are written by their decorators and read by nothing` by
      **appending** an amendment (never retro-editing): `RESOLVERS`, `load_entry_point`,
      `check_registration` and `declared_names` now have production callers, naming the tasks;
      `PROBES` stays with H7d and `registry.template_provenance` stays with the unassigned
      installed-template entry. Amend
      `## OPEN — an installed template's name resolves but its class is never loaded` to record that
      one of its three preconditions — `provenance.plugin_versions` — is now built; **amend, do not
      close**, and leave its owner unassigned.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2088 + 2 = 2090 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/cli.py`, change the `plugin_versions` assignment back
      to `plugin_versions = {}` unconditionally.
      `tests/test_cli.py::test_a_resolver_run_records_the_plugin_version_it_resolved_through` must
      **FAIL** on the resolver half. **Checked against the test body:** the test asserts a populated
      mapping for the resolver run *and* an empty one for the table run, so the mutation cannot pass
      by making both empty — which the resolver-only assertion alone would not have caught in the
      other direction (a mapping populated unconditionally), and which is why the control is there.

      Second mutation: in `plugins.versions_for`, change `ep.dist.name` to `ep.value`.
      `tests/test_plugins.py::test_versions_for_names_the_distribution_a_reader_would_pin` must
      **FAIL** — the key becomes the module path, which pins nothing.

- [ ] **Step 6: Commit.** `provenance: record the plugin version a resolver run resolved through`

---

