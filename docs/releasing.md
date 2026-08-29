# Releasing

**Non-normative.** This is the maintainer's runbook for putting a version on PyPI and in the Homebrew tap. It describes an operation, not the tool — nothing here is authoritative over [the four documents](../CLAUDE.md#the-documents).

Everything below was measured while doing the 0.1.0 release on 2026-08-26, and the things that cost a round are written down as the reason rather than the step, because a step without its reason is the first thing a later release quietly drops.

## The one thing to understand first

**A green test suite says nothing about the distribution.** `[tool.pytest.ini_options]` sets `pythonpath = ["."]`, so all 3574 tests import from `src/`. A wheel that dropped `readme_templates/*.tmpl` would pass every one of them and then fail on the first `publishable new` a stranger ran. So the release gate is not `pytest`; it is building the artifacts and driving the **installed console script from outside this repository**.

## Order

The sequence matters, and each step's output is the next step's input.

| # | Step | Why here |
|---|---|---|
| 1 | Land every change on `main`, through a pull request | The published metadata's URLs point at `main`; they should resolve to a tree that contains what they describe |
| 2 | Build and verify the artifacts | Everything after this consumes the exact bytes verified here |
| 3 | TestPyPI, and install from it — **optional**, see below | A real upload against a real index. `verify` covers the rest, so this earns its place only for a new name, a metadata change, or a README change |
| 4 | Tag and cut the GitHub release | Tag the tree that gets uploaded, before uploading it |
| 5 | Publishing the release triggers `release.yml`, which verifies and uploads to PyPI | The workflow is the uploader; there is no token |
| 6 | Point the Homebrew formula at the published sdist, verify, push the tap | The formula's `url` cannot exist until step 5 |
| 7 | Add the install routes to README and to the release notes | They are false until step 6 |

Step 7 is last on purpose. A documented route with nothing behind it is this repository's most-repeated defect, and an install line is the version of it that lands on the page a new user reads first.

## Version sites

Six files carry `publishable`'s own version, and `CLAUDE.md` § Versions is the rule. They move together:

- `pyproject.toml`
- `CITATION.cff` — its `date-released` moves too, and went three weeks stale before 0.1.0
- `src/publishable/__init__.py`
- `docs/reference.md`'s worked `publishable_version` value
- README's `v0.x` notice, when the major or the phase changes
- `uv.lock` — the one nobody edits: the project is an editable member of its own lock, so the first `uv run` or `uv build` after the bump rewrites that entry by itself. It was omitted from this list until 0.1.3, where it surfaced as an unexplained sixth modified file at commit time. Let `uv` write it and commit it with the rest, rather than hand-editing it or leaving it to appear in the next unrelated commit

**Three sites carry `0.1.0` and must NOT move**: `scaffold.py` and `plugin_scaffold.py` write the *scaffolded project's* version, and `tests/test_cli.py`'s fixtures do the same. Two real pins assert `provenance.publishable_version`, and they move only when the package version does. Enumerate these; never `sed` the version across the tree.

## 1. Land, through a pull request

**`main` takes no direct pushes.** Since 2026-08-29 a ruleset requires a pull
request and a passing `suite` check, with no bypass for anyone — the repo admin
included. So the version bump is a branch like any other change:

```bash
git checkout -b release-<v>
# ... move the six version sites (§ Version sites) ...
git push -u origin release-<v>      # .githooks/pre-push runs the four checks here
gh pr create --base main --title "publishable <v>"
gh pr merge --squash --delete-branch # once `suite` is green
git checkout main && git pull --ff-only origin main
```

The four checks still run, in three places now rather than one: `pre-push` on
the branch push, `tests.yml` on the pull request, and `release.yml`'s `verify`
before anything reaches PyPI. Run them by hand first if you would rather not
spend a push on a formatting slip.

```bash
uv run pytest        # 3571 passed, 1 skipped, 2 xfailed — 2026-08-29, at 0.2.4
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

**That last `git pull` is not tidiness, and skipping it can cost a version
number.** A squash merge writes a NEW commit: PR #3's branch head was
`a2ae4da` and what landed on `main` was `5e594d4`, measured on 2026-08-29.
Everything downstream — the build at step 2, the tag at step 4 — has to come
from the commit that is on `main`, not from the branch head that is not. Tag
the branch head and the immutable release you cannot recut points at a commit
`main` does not contain.

## 2. Build and verify the artifacts

```bash
rm -rf dist && uv build
uvx twine check dist/*
tar tzf dist/publishable-<v>.tar.gz | sed 's|^publishable-<v>/||' | sort
unzip -l dist/publishable-<v>-py3-none-any.whl
```

Read both listings rather than trusting `[tool.hatch.build.targets.*]`. Two things the config is doing, and why:

**The wheel's `artifacts` list is not decoration.** `readme_templates/*.tmpl` and `py.typed` are declared there because they are read at runtime and are not modules. Any new non-`.py` payload under `src/publishable/` has to be added, and the way to find out is `find src/publishable -type f ! -name "*.py"`, not memory.

**The sdist has an explicit `include` because the default swept 1160 files** — `.claude/settings.local.json`, the whole `.superpowers/sdd/` ledger, `docs/superpowers/` and `standards/`. It is 70 files now.

**`tests/` is deliberately not in the sdist**, and that was measured rather than assumed. Re-measured on 2026-08-29 at 0.2.4, by adding `tests` to the `include`, building, unpacking outside any repository and running: **2 failed, 3566 passed, 4 skipped**. Both failures attributed rather than counted:

| Failure | Cause |
|---|---|
| 1 command test | `E-GIT-NO-REPO` — an unpacked sdist is not a git repository |
| 1 `.parquet` golden digest | a fresh resolve is not this repo's `uv.lock` |

Both are properties of the unpacked tarball rather than of the code, which is the same finding the first measurement recorded as **2 failed, 3442 passed**.

**It read 5 failed for part of 2026-08-29**, and the three extra were `test_scaffold.py`'s tutorial pins hitting `FileNotFoundError` on `docs/tutorial-writing-a-plugin.md` — a file the `include` above deliberately does not carry, shipping the three normative documents and not the tutorial. Those three now skip when the tutorial is absent **and** the tree is not a git checkout, so they are three of the four skips above. The second half of that condition is what keeps the skip from failing open: delete the tutorial in a checkout and they still run, and still fail. A suite that fails on unpack is worse than no suite.

Then drive it. Install the **wheel** into a throwaway venv outside the repository and walk the arc:

```bash
uv venv .venv && uv pip install --python .venv/bin/python <path>/dist/publishable-<v>-py3-none-any.whl
./.venv/bin/publishable list-templates      # resolves `generic`
./.venv/bin/publishable new my-study        # proves readme_templates survived
cd my-study
cat >> pyproject.toml <<'EOF'                # WITHOUT THIS THE REST TESTS THE PUBLISHED VERSION
[tool.uv.sources]
publishable = { path = "<path>/dist/publishable-<v>-py3-none-any.whl" }
EOF
uv sync && uv run python -c "import publishable; print(publishable.__version__)"   # must print <v>
# then: generate experiment -> validate -> run -> report
```

**Everything after `new` runs in the scaffolded project's OWN environment, not the venv you just installed into**, and a scaffolded `pyproject.toml` declares a bare `dependencies = ["publishable"]`. So `uv run publishable validate|run|report` resolves core **from PyPI** — the *previous* release — and the whole arc goes green while saying nothing about the artifact under test. Measured on 2026-08-28 cutting 0.2.1: the project environment reported `0.2.0` until it was repointed at the wheel. This is the *answering a question with a proxy* shape from `CLAUDE.md`, aimed at the release gate itself: the arc that proves the candidate works was proving the last one did. Repoint with `[tool.uv.sources]`, then read the version back before believing anything downstream of it, and confirm the finished record carries `publishable_version: <v>`.

`run` reaching `status: completed` and writing a readable `units.parquet` is the check that matters, because it is the only one that exercises `pyarrow`. Note that `publishable --help` is *not* a smoke test: operation commands take paths and no flags, so it prints `unknown command`. Two more things the arc needs and the scaffold does not supply: `metadata.description` and `metadata.authors` are required and materialize empty, and `data.units.key` defaults to `patient_id` against a roster file that must be named `index.csv` — three diagnostics to walk through before `validate` passes, none of them a defect.

## 3. TestPyPI

**Optional since 0.1.2, and worth knowing when it stops being optional.** The rehearsal this step exists for is now done by `release.yml`'s `verify` job on every release — the same build, the same `twine check`, the same installed-console-script arc, on Linux. What TestPyPI adds beyond that is a real *upload* against a real index, which matters in exactly three cases:

- **A first upload of a new project name.** There is no trusted publisher yet and no project to scope a token to; rehearsing the upload is the only way to find a metadata rejection before it costs the real name's first version.
- **A change to packaging metadata** — `pyproject.toml`'s `[project]` table, a new `classifier`, a `license` spelling. `twine check` validates locally, but PyPI's own validator is stricter and is what actually rejects.
- **A change to how the README renders**, since the project page is built from the long description and cannot be re-uploaded for a version.

For an ordinary release that changes only code, skip it: `verify` covers the same ground and a failed upload no longer costs anything, because nothing uploads until `verify` is green.

When you do run it, TestPyPI is a separate site with a separate account and separate tokens; pypi.org credentials do not work there.

```bash
UV_PUBLISH_TOKEN=<test-token> uv publish --publish-url https://test.pypi.org/legacy/ \
  dist/publishable-<v>.tar.gz dist/publishable-<v>-py3-none-any.whl
```

Name the two files. `uv publish` defaults to `dist/*`, and `dist/` carries a `.gitignore`.

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
git checkout main && git pull --ff-only origin main   # tag what is ON main
git tag -a v<v> -m "publishable <v>

..."
git push origin v<v>
gh release create v<v> --title "publishable <v>" --notes-file <notes> \
  dist/publishable-<v>.tar.gz dist/publishable-<v>-py3-none-any.whl
```

**The ruleset does not touch tags**, which is worth knowing here rather than
discovering at the one step where a mistake costs a version number: it targets
branches and its condition is `~DEFAULT_BRANCH`, so `git push origin v<v>`
needs no pull request. Probed on 2026-08-29 with a throwaway tag, which pushed
and was then deleted — not read off the configuration.

Two smaller consequences of the same setup. `pre-push` fires on a tag push
too, so the suite runs again here; that is a couple of minutes, not a problem,
but it is not instant. And `.githooks/reference-transaction` reports nothing
for a tag push, because it watches `refs/remotes/*` and a tag push updates no
tracking ref — so `--no-verify` on a tag is silent, unlike on a branch.

**Publishing the release is what triggers the upload** — see step 5. Attach both artifacts here — releases on this repository are immutable, so nothing can add them afterwards — and write the notes **without install instructions** — they are not true yet. The install block goes in at step 7 with `gh release edit`, which keeps the URL.

**A version number is single-use, and a failed release costs it.** Releases on this repository are immutable, which retires the tag name the moment a release publishes against it — *permanently*, and deleting the release does not give it back:

```
remote: - Cannot create ref due to creations being restricted.
```

Measured on 2026-08-27, when `release.yml`'s first run failed at `verify` and `v0.1.1` could not be re-tagged after its release was deleted. **So there is no retry.** If a release's pipeline fails, the fix goes on `main` — through a pull request like everything else, which is a few minutes of CI before you can cut the next number — and the next release takes the next number.

Which is why a change that could plausibly fail on CI should be proven from a throwaway branch first, on a workflow generated **from** `release.yml` rather than hand-written to resemble it — same jobs, only the trigger changed. That costs a CI run and no version number.

**The tag does not track `main` afterwards.** It marks the tree that was uploaded; step 7's commit makes claims that only became true once the upload existed. For 0.1.0 the tag is at `e39d2dc` while `main` moved on, and that is correct — do not "fix" it.

## 5. PyPI

**Publishing is automated and there is no token.** Publishing a GitHub release triggers `.github/workflows/release.yml`, which authenticates to PyPI over [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) — PyPI trusts an OIDC token minted by that specific workflow file, so nothing long-lived exists to leak or rotate. Step 4's `gh release create` is what starts it.

The workflow has two jobs, in order:

| Job | What it does | Why it is separate |
|---|---|---|
| `verify` | ruff, mypy, the full suite, `uv build`, `twine check`, the tag-matches-version check, then the installed console script driven through `new` → `generate experiment` → `validate` → `run` → `report` outside the repository | Nothing is uploaded until this passes. It is the only place the *artifact* is exercised |
| `publish` | `uv publish` with `id-token: write`, in the `pypi` environment | The environment is the human gate — add a required reviewer there to hold every upload for approval |

**There is no job that attaches artifacts to the release, and the reason is a measurement.** Releases on this repository are immutable: `gh release upload` against one returns `HTTP 422: Cannot upload assets to an immutable release`. A job that tried it shipped and could never have succeeded. Create the release **with** its artifacts — step 4 — and the bit-reproducible build is what makes them the same bytes the workflow publishes.

**The workflow filename is part of PyPI's authorization.** Renaming `release.yml` breaks publishing until the publisher is updated at pypi.org → Manage → Publishing.

**The `verify` job's gate was shown to fail before it was trusted.** A wheel built with `readme_templates/*.tmpl` removed — the exact payload the `artifacts` list exists to keep — makes it exit 1 at `publishable new` with `E-IO-FAILED`, while the full suite stays green on that same wheel.

### Publishing by hand

Still the route for a first-ever upload of a **new project name**, because a trusted publisher has to be attached to something. PyPI supports a *pending* publisher for exactly this; a token works too:

```bash
UV_PUBLISH_TOKEN=<token> uv publish dist/publishable-<v>.tar.gz dist/publishable-<v>-py3-none-any.whl
```

A brand-new name cannot use a scoped token, because scoping needs a project that exists — so the first upload needs an **Entire account** token. Delete it immediately afterward. A token that has been pasted into a terminal, a chat, or a shell history is spent; rotate it rather than reasoning about who saw it.

Then confirm what landed is what was verified:

```bash
shasum -a 256 dist/publishable-<v>.tar.gz
curl -s https://pypi.org/pypi/publishable/<v>/json | python3 -c \
  "import json,sys; print([u['digests']['sha256'] for u in json.load(sys.stdin)['urls']])"
```

They should be equal. **The build is bit-reproducible from the tag, across platforms**, and both halves of that were measured. On 2026-08-26 a rebuild in a detached worktree at `v0.1.0` reproduced both published digests on the same machine. On 2026-08-27 the stronger form held: 0.1.2 was built by `verify` on `ubuntu-latest` and published from there, and both digests match a local macOS `uv build` of the same tag exactly. That is what makes the artifacts attached at step 4 the same bytes the workflow publishes, and it means anyone can check a published artifact against the tag on any machine. It held a third time on 2026-08-27 for 0.1.3: both digests published by `verify` on `ubuntu-latest` equal a local macOS `uv build` of `v0.1.3`.

## 6. Homebrew

The tap is [`seouri/homebrew-tap`](https://github.com/seouri/homebrew-tap), and `packaging/homebrew/publishable.rb` is a staging copy of the same formula. **Edit both** — they are byte-identical below the staging header, and `diff` is how you know.

**The installable name is `seouri/tap/publishable`, not `publishable`.** A bare name resolves only in homebrew-core, whose bar is >=75 stars, >=30 forks or >=30 watchers plus a public repository with an immutable tagged release.

For a version bump, `url` and `sha256` change and the resources usually do too. Then:

```bash
brew style seouri/tap
brew audit --strict --formula seouri/tap/publishable
brew uninstall publishable; brew install seouri/tap/publishable
brew test seouri/tap/publishable
```

A formula that audits clean against a `file://` sdist has not been audited against the one people download, so re-run all four after the URL is real. And verify along the path a user takes — `brew untap seouri/tap && brew tap seouri/tap` — rather than the one you already have set up.

Five things this formula knows that are easy to lose:

| Fact | Why |
|---|---|
| `numpy` and `scipy` are `depends_on`, not resources | Both are bottled formulae; building either in the virtualenv costs minutes and buys nothing |
| `pyarrow` is a **pinned** resource | No formula exists, so it compiles against Homebrew's `apache-arrow`, and the binding and Arrow C++ must match. When `apache-arrow` bumps, this pin moves with it |
| `rust` is a build dependency | `pyarrow`'s build pulls `libcst`, which fails with `error: can't find Rust compiler`. Found by building; homebrew-core's `harlequin` declares it for the same reason |
| `uv` is a runtime dependency, git via `uses_from_macos` | `run` pins the environment through `uv.lock` and refuses outside a git repository, so omitting them ships a binary that refuses the first real command |
| The `test do` block asserts a scaffolded **file** | `readme_templates/*.tmpl` is the one payload a wheel can silently drop, and an exit code would not see it |

**`no_autobump!` is rejected in third-party taps** — measured, not assumed: `Error: ... can only be used in official Homebrew taps`. That is why the `brew bump` workflow is disabled at the tap level instead: its PR moves `url` and `sha256` and never the resources, so for this formula it would be incomplete every time.

**The tap's own `tests.yml` — not this repository's — does not build the formula except on a pull request.** Its only build step, `brew test-bot --only-formulae`, is gated on `github.event_name == 'pull_request'`, so a push to `main` runs tap-syntax and compiles nothing. `formula-still-builds.yml` is the separate weekly workflow that does build, and it exists as a tripwire for the `pyarrow`/`apache-arrow` pin — nothing else in the tap fires when homebrew-core bumps Arrow. **Dispatch it after a version bump and read which step failed.** On 2026-08-27 it went red for 0.1.3 with the build and the formula's own test block both green: its reporting step reached into `Cellar/publishable/0.1.0/libexec/bin/python`, a path that spells a version, so a release is what broke it rather than the pairing it watches. It now reports through `brew --prefix publishable`, the opt link, which names no version.

**`brew untap` and `brew tap` reset the tap's `origin` to HTTPS**, and pushing a workflow file over the `gh` OAuth token then fails with *"refusing to allow an OAuth App to create or update workflow ... without `workflow` scope"*. Set the remote back to SSH.

## 7. The install routes

README's install block and the release notes both gain the routes now that they exist. `gh release edit v<v> --notes-file <notes>` keeps the release URL.

**Known and accepted drift:** the PyPI project page renders the README as it was when the sdist was built, and PyPI will not accept a re-upload of a version. So a README edit made after the upload — such as adding the Homebrew line — never reaches the PyPI page for that version. It corrects itself on the next release, and it is not worth a patch version.

## Checklist

- [ ] `pytest`, `ruff check`, `ruff format --check`, `mypy` clean
- [ ] Version moved at all six sites — `uv.lock` being the one `uv` writes; the three scaffold/fixture sites untouched
- [ ] `CITATION.cff` `date-released` is the actual release date
- [ ] `uv build`; `twine check`; both archive listings read
- [ ] Wheel installed outside the repo and driven to `status: completed` with a readable `units.parquet` — with the scaffolded project repointed at the wheel, and `publishable_version: <v>` read back out of the finished `run.yaml`
- [ ] TestPyPI upload and install — only for a new project name, a packaging-metadata change, or a README change; `verify` covers an ordinary release
- [ ] Pull request merged into `main` with `suite` green; local `main` pulled so the tag lands on the squashed commit
- [ ] Tag pushed; GitHub release created, no install block yet
- [ ] `release.yml` green through `verify` and `publish`; uploaded sha256 equals the local one
- [ ] Formula repointed in **both** copies; style, audit, untap/tap, install, test
- [ ] Tap pushed; `formula-still-builds.yml` green
- [ ] README install block and release notes updated last
