# Releasing

**Non-normative.** This is the maintainer's runbook for putting a version on PyPI and
in the Homebrew tap. It describes an operation, not the tool — nothing here is
authoritative over [the four documents](../CLAUDE.md#the-documents).

Everything below was measured while doing the 0.1.0 release on 2026-08-26, and the
things that cost a round are written down as the reason rather than the step, because
a step without its reason is the first thing a later release quietly drops.

## The one thing to understand first

**A green test suite says nothing about the distribution.** `[tool.pytest.ini_options]`
sets `pythonpath = ["."]`, so all 3444 tests import from `src/`. A wheel that dropped
`readme_templates/*.tmpl` would pass every one of them and then fail on the first
`publishable new` a stranger ran. So the release gate is not `pytest`; it is building
the artifacts and driving the **installed console script from outside this
repository**.

## Order

The sequence matters, and each step's output is the next step's input.

| # | Step | Why here |
|---|---|---|
| 1 | Land every change on `main` and push | The published metadata's URLs point at `main`; they should resolve to a tree that contains what they describe |
| 2 | Build and verify the artifacts | Everything after this consumes the exact bytes verified here |
| 3 | TestPyPI, and install from it | The only rehearsal available — a PyPI version number can be yanked but never re-uploaded |
| 4 | Tag and cut the GitHub release | Tag the tree that gets uploaded, before uploading it |
| 5 | Upload to PyPI | |
| 6 | Point the Homebrew formula at the published sdist, verify, push the tap | The formula's `url` cannot exist until step 5 |
| 7 | Add the install routes to README and to the release notes | They are false until step 6 |

Step 7 is last on purpose. A documented route with nothing behind it is this
repository's most-repeated defect, and an install line is the version of it that lands
on the page a new user reads first.

## Version sites

Five files carry `publishable`'s own version, and `CLAUDE.md` § Versions is the rule.
They move together:

- `pyproject.toml`
- `CITATION.cff` — its `date-released` moves too, and went three weeks stale before 0.1.0
- `src/publishable/__init__.py`
- `docs/reference.md`'s worked `publishable_version` value
- README's `v0.x` notice, when the major or the phase changes

**Three sites carry `0.1.0` and must NOT move**: `scaffold.py` and `plugin_scaffold.py`
write the *scaffolded project's* version, and `tests/test_cli.py`'s fixtures do the
same. Two real pins assert `provenance.publishable_version`, and they move only when
the package version does. Enumerate these; never `sed` the version across the tree.

## 1. Land and push

```bash
uv run pytest        # 3444 passed, 1 skipped, 2 xfailed as of 0.1.0
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

## 2. Build and verify the artifacts

```bash
rm -rf dist && uv build
uvx twine check dist/*
tar tzf dist/publishable-<v>.tar.gz | sed 's|^publishable-<v>/||' | sort
unzip -l dist/publishable-<v>-py3-none-any.whl
```

Read both listings rather than trusting `[tool.hatch.build.targets.*]`. Two things the
config is doing, and why:

**The wheel's `artifacts` list is not decoration.** `readme_templates/*.tmpl` and
`py.typed` are declared there because they are read at runtime and are not modules.
Any new non-`.py` payload under `src/publishable/` has to be added, and the way to find
out is `find src/publishable -type f ! -name "*.py"`, not memory.

**The sdist has an explicit `include` because the default swept 1160 files** —
`.claude/settings.local.json`, the whole `.superpowers/sdd/` ledger, `docs/superpowers/`
and `standards/`. It is 70 files now.

**`tests/` is deliberately not in the sdist**, and that was measured rather than
assumed: with the suite included, the tarball unpacked outside any repository and run
gave **2 failed, 3442 passed**. Both failures are properties of the unpacked tarball —
one command test reaches `E-GIT-NO-REPO` because an unpacked sdist is not a git
repository, and one `.parquet` golden digest moves because a fresh resolve is not this
repo's `uv.lock`. A suite that fails on unpack is worse than no suite.

Then drive it. Install the **wheel** into a throwaway venv outside the repository and
walk the arc:

```bash
uv venv .venv && uv pip install --python .venv/bin/python <path>/dist/publishable-<v>-py3-none-any.whl
./.venv/bin/publishable list-templates      # resolves `generic`
./.venv/bin/publishable new my-study        # proves readme_templates survived
# then: generate experiment -> validate -> run -> report
```

`run` reaching `status: completed` and writing a readable `units.parquet` is the check
that matters, because it is the only one that exercises `pyarrow`. Note that
`publishable --help` is *not* a smoke test: operation commands take paths and no flags,
so it prints `unknown command`.

## 3. TestPyPI

TestPyPI is a separate site with a separate account and separate tokens; pypi.org
credentials do not work there.

```bash
UV_PUBLISH_TOKEN=<test-token> uv publish --publish-url https://test.pypi.org/legacy/ \
  dist/publishable-<v>.tar.gz dist/publishable-<v>-py3-none-any.whl
```

Name the two files. `uv publish` defaults to `dist/*`, and `dist/` carries a
`.gitignore`.

Installing from TestPyPI needs real PyPI for the dependencies, which are not mirrored:

```bash
uv pip install --python .venv/bin/python \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  --index-strategy unsafe-best-match publishable
```

Then walk the same arc as step 2.

## 4. Tag and release

```bash
git tag -a v<v> -m "publishable <v>

..."
git push origin v<v>
gh release create v<v> --title "publishable <v>" --notes-file <notes> \
  dist/publishable-<v>.tar.gz dist/publishable-<v>-py3-none-any.whl
```

Attach both artifacts, and write the notes **without install instructions** — they
are not true yet. The install block goes in at step 7 with `gh release edit`, which
keeps the URL.

**The tag does not track `main` afterwards.** It marks the tree that was uploaded;
step 7's commit makes claims that only became true once the upload existed. For 0.1.0
the tag is at `e39d2dc` while `main` moved on, and that is correct — do not "fix" it.

## 5. PyPI

```bash
UV_PUBLISH_TOKEN=<token> uv publish dist/publishable-<v>.tar.gz dist/publishable-<v>-py3-none-any.whl
```

**Tokens.** A brand-new project name cannot be scoped, because scoping needs a project
that exists — so the first upload of a name needs an **Entire account** token. Delete
it immediately afterward and create one scoped to `publishable`. A token that has been
pasted into a terminal, a chat, or a shell history is spent; rotate it rather than
reasoning about who saw it.

Then confirm what landed is what was verified:

```bash
shasum -a 256 dist/publishable-<v>.tar.gz
curl -s https://pypi.org/pypi/publishable/<v>/json | python3 -c \
  "import json,sys; print([u['digests']['sha256'] for u in json.load(sys.stdin)['urls']])"
```

They should be equal. That equality is what lets the Homebrew formula claim it builds
the tree that was checked rather than one that merely shares a version number.

**Trusted Publishing** removes the token entirely — PyPI trusts a named GitHub Actions
workflow over OIDC. It is the better end state and `uv publish` supports it; it cannot
do the local TestPyPI rehearsal above, which is why 0.1.0 used tokens.

## 6. Homebrew

The tap is [`seouri/homebrew-tap`](https://github.com/seouri/homebrew-tap), and
`packaging/homebrew/publishable.rb` is a staging copy of the same formula. **Edit both**
— they are byte-identical below the staging header, and `diff` is how you know.

**The installable name is `seouri/tap/publishable`, not `publishable`.** A bare name
resolves only in homebrew-core, whose bar is >=75 stars, >=30 forks or >=30 watchers
plus a public repository with an immutable tagged release.

For a version bump, `url` and `sha256` change and the resources usually do too. Then:

```bash
brew style seouri/tap
brew audit --strict --formula seouri/tap/publishable
brew uninstall publishable; brew install seouri/tap/publishable
brew test seouri/tap/publishable
```

A formula that audits clean against a `file://` sdist has not been audited against the
one people download, so re-run all four after the URL is real. And verify along the
path a user takes — `brew untap seouri/tap && brew tap seouri/tap` — rather than the
one you already have set up.

Five things this formula knows that are easy to lose:

| Fact | Why |
|---|---|
| `numpy` and `scipy` are `depends_on`, not resources | Both are bottled formulae; building either in the virtualenv costs minutes and buys nothing |
| `pyarrow` is a **pinned** resource | No formula exists, so it compiles against Homebrew's `apache-arrow`, and the binding and Arrow C++ must match. When `apache-arrow` bumps, this pin moves with it |
| `rust` is a build dependency | `pyarrow`'s build pulls `libcst`, which fails with `error: can't find Rust compiler`. Found by building; homebrew-core's `harlequin` declares it for the same reason |
| `uv` is a runtime dependency, git via `uses_from_macos` | `run` pins the environment through `uv.lock` and refuses outside a git repository, so omitting them ships a binary that refuses the first real command |
| The `test do` block asserts a scaffolded **file** | `readme_templates/*.tmpl` is the one payload a wheel can silently drop, and an exit code would not see it |

**`no_autobump!` is rejected in third-party taps** — measured, not assumed:
`Error: ... can only be used in official Homebrew taps`. That is why the `brew bump`
workflow is disabled at the tap level instead: its PR moves `url` and `sha256` and
never the resources, so for this formula it would be incomplete every time.

**`tests.yml` does not build the formula except on a pull request.** Its only build
step, `brew test-bot --only-formulae`, is gated on
`github.event_name == 'pull_request'`, so a push to `main` runs tap-syntax and compiles
nothing. `formula-still-builds.yml` is the separate weekly workflow that does build,
and it exists as a tripwire for the `pyarrow`/`apache-arrow` pin — nothing else in the
tap fires when homebrew-core bumps Arrow.

**`brew untap` and `brew tap` reset the tap's `origin` to HTTPS**, and pushing a
workflow file over the `gh` OAuth token then fails with *"refusing to allow an OAuth
App to create or update workflow ... without `workflow` scope"*. Set the remote back to
SSH.

## 7. The install routes

README's install block and the release notes both gain the routes now that they exist.
`gh release edit v<v> --notes-file <notes>` keeps the release URL.

**Known and accepted drift:** the PyPI project page renders the README as it was when
the sdist was built, and PyPI will not accept a re-upload of a version. So a README
edit made after the upload — such as adding the Homebrew line — never reaches the PyPI
page for that version. It corrects itself on the next release, and it is not worth a
patch version.

## Checklist

- [ ] `pytest`, `ruff check`, `ruff format --check`, `mypy` clean
- [ ] Version moved at all five sites; the three scaffold/fixture sites untouched
- [ ] `CITATION.cff` `date-released` is the actual release date
- [ ] `uv build`; `twine check`; both archive listings read
- [ ] Wheel installed outside the repo and driven to `status: completed` with a readable `units.parquet`
- [ ] TestPyPI upload, install from it, same arc
- [ ] `main` pushed; tag pushed; GitHub release created with both artifacts, no install block yet
- [ ] PyPI upload; uploaded sha256 equals the local one
- [ ] Account-wide token deleted, project-scoped token created, TestPyPI token rotated
- [ ] Formula repointed in **both** copies; style, audit, untap/tap, install, test
- [ ] Tap pushed; `formula-still-builds.yml` green
- [ ] README install block and release notes updated last
