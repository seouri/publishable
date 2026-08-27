# W3 scoping — the plugin scaffold's tree and its output

Read-only measurement against `main` at `9d3fadf`, on 2026-08-27. Every path, line and
`git ls-files` result below was run against that tree, never remembered. Spec claims and
build facts are labelled separately throughout.

Chartered by [`spec-defects.md`](spec-defects.md)'s entry *the plugin scaffold writes neither
`uv.lock`, an example config, nor a README region*, filed 2026-08-27 and amended the same day
to five discrepancies. `W1` and `W2` are the sibling slices, both merged.

**Verdict: 7 tasks, and the deliverable is one test.** Five documented lines disagree with what
`scaffold_plugin` writes; a sixth was found by this measurement; and the reason all six were
possible is that **the layout lives in two places with nothing comparing them**. So the fix is
the pair `reference.md` § CLI reference already has for commands — parse the document, observe
the code, keep no third copy — and the edits are whatever it takes to make that pair pass.
Every one of the six then becomes a test failure rather than a reading.

**Baseline at `9d3fadf`:** `uv run pytest -q` → **3469 passed, 1 skipped, 2 xfailed**, 367 s.

---

## 0. The sixth discrepancy, and why it decides the shape of the fix

**`examples/<stem>/` is not in the scaffold's own commit.** `scaffold_plugin` does
`(root / "examples" / stem).mkdir(parents=True, exist_ok=True)` and writes nothing into it, then
`git add .` and commits. Git tracks no empty directory, so:

```
$ git -C publishable-my-assay ls-files
.gitignore
CITATION.cff
LICENSE
README.md
pyproject.toml
src/publishable_my_assay/__init__.py
src/publishable_my_assay/probes/__init__.py
src/publishable_my_assay/probes/instrument.py
src/publishable_my_assay/resolvers/__init__.py
src/publishable_my_assay/resolvers/units.py
src/publishable_my_assay/templates/__init__.py
src/publishable_my_assay/templates/my_assay.py
src/publishable_my_assay/writers/__init__.py
src/publishable_my_assay/writers/artifact.py
tests/test_my_assay.py
```

No `examples/`. `git status --porcelain --ignored` reports nothing either — an empty directory is
invisible to git in both directions — so the author sees the folder, a clone does not, and
**nothing anywhere reports the difference.** That is the same class as the five in the filing and
it was found the same way: by diffing the document against the output rather than by reading
either.

Six of six were possible because the layout is written twice — once in § Creating a plugin's
fenced tree, once in `plugin_scaffold.py` — with nothing comparing them. `reference.md` § CLI
reference has had the answer for commands since H9: *"The list of commands lives in the document
and in `cli.NOT_BUILT_COMMANDS`, nowhere else — this module parses the first and observes the
second through `main`, rather than keeping a third copy, since a third copy is the defect being
prevented."* (`tests/test_cli.py:9436`.) The layout deserves the same pair, and it is the only
part of this slice that stops the seventh discrepancy.

---

## 1. Every documented line, measured, with its verdict

`plugin new publishable-my-assay`, compared line by line against § Creating a plugin's tree:

| Documented line | Written? | Verdict |
|---|---|---|
| `README.md  # generated, with a parameter table derived from the spec` | a README, **no parameter table and no managed region** | **narrow the document** |
| `LICENSE`, `CITATION.cff`, `pyproject.toml`, `.git/` | yes | agree |
| `uv.lock` | **no** | **annotate the document** |
| `src/publishable_my_assay/templates/my_assay.py`, `resolvers/`, `probes/`, `writers/` | yes, each with a module | agree |
| `steps/  # optional reusable BaseStep subclasses` | **no** | **write it** |
| `tests/test_my_assay.py` | yes | agree |
| `examples/my_assay/config.yaml  # a filled-in config, generated from the spec` | directory created, **empty, and untracked** (§ 0) | **write a `.gitkeep`, annotate the document** |
| *(absent from the tree)* `.gitignore` | **written** | **add the line** |

### The README's parameter table — the document narrows, and the argument is W1's

§ Creating a plugin shows the plugin README carrying
`<!-- publishable:begin templates -->` with *"a parameter table generated from `parameter_spec`
itself"*, closing: *"Add a parameter and run `publishable docs` — the table, the example config,
and newly-initialized configs all update together."*

Two grounds for narrowing rather than building, and the second is the decisive one:

- **`docs` cannot fill it.** Rendering a plugin's own parameter table means reading an
  **installed** template's `parameter_spec`, which this build refuses outright —
  `E-TEMPLATE-INSTALLED-UNSUPPORTED`, the surviving member of the `-UNSUPPORTED` family. That
  capability is a slice of its own with its own design questions; it is not a scaffold fix.
- **A table generated at `plugin new` time documents a placeholder.** The spec the scaffold
  writes is `{stem}.threshold` with the help text *"TODO: replace with this experiment type's own
  parameters"*. A table rendered from it is stale the moment the author does the first thing the
  scaffold tells them to do — **the same argument that decided W1's `TEST_PY`**, where a test
  enumerating the placeholder spec would have gone red on the author's first edit.

**What the scaffold ships instead is better on the project's own terms**, which is why this is a
narrowing and not a concession. Its README carries a table of *registered names* — template,
resolver, probe, writer/reader — every one derived from the distribution's stem, the same
substitution the entry points come from. **It cannot drift**, because a rename changes both sides
at once. *Documentation that can't drift is the only kind worth generating* is satisfied by the
registry table and not by a parameter table nobody can regenerate.

The `docs` payoff sentence is then scoped to a **project**, where it is true and where its
readers actually are: a project's README does declare the four managed regions, and
`publishable docs` rewrote all four in a real run (`README.md: rewrote overview, credentials,
experiments, templates`).

### `uv.lock` — the document annotates, and the filing was narrower than the defect

Neither scaffold writes one. **§ Scaffolding's project tree carries the same `uv.lock` line and
`scaffold_project` does not write it either** — so this half of the filing is not plugin-specific,
which the filing did not say. Measured on a real `publishable new`: `uv.lock` is the **only** one
of that tree's thirteen lines missing, and every directory it names carries a `.gitkeep`, so the
project scaffold does not have § 0's vanishing-directory fault at all.

Measured: `uv run python -c "print('hi')"` inside a freshly scaffolded plugin creates `uv.lock`.
So the file appears on the author's first `uv` command without the scaffold doing anything.

**Not built, deliberately**: locking needs a resolver and a network, and a creation command that
fails without one is worse than a tree whose lockfile appears a moment later. `plugin new` runs
`git init` and nothing else; `generate experiment --plugin` does reach the network, and that is a
flag the user typed. The line stays in both trees with what it is written beside it.

### `steps/` — the code writes it

The four sibling directories each exist to hold a generated module, because each has an
entry-point group. `steps/` has none: a reusable `BaseStep` is imported by the consuming
project's own code, registered nowhere, so there is nothing to generate into it. That is an
argument for writing the **directory** and not a module — one line beside the four, with an
`__init__.py` like theirs. The fixed layout is a specification a reader of *any* plugin relies
on, and the repository's rule is that the documents lead and the code follows, the document
changing first only where the code **cannot** follow. Here it can, for one line.

### `examples/<stem>/` — both sides move

Generating the config needs the template **class**, and the scaffold has just written that file
without importing it; importing it would execute the placeholder it just wrote, and materializing
from a placeholder spec produces the stale artifact the README argument already rejects. So the
generated config is out.

What is left is a directory that **vanishes on clone** (§ 0), and `scaffold_project` already
answers exactly this: it writes a `.gitkeep` into each of its five directories. Following the
sibling that got it right costs one line and makes the tree true of a clone rather than only of
the author's disk.

---

## 2. The deliverable — one pair, two directions

A helper parses a fenced tree from a `reference.md` section into the set of paths it names.
Two agreement tests, one per scaffold, each asserting **both** directions:

- **Every path the document names exists** after scaffolding, as a file or a directory. This
  catches `uv.lock`, `steps/` and the example config today.
- **Every path the scaffold's own commit tracks is named by the document**, or sits under a
  directory the document names. This catches `.gitignore` today, and it is the direction nobody
  was checking: five of the six discrepancies are the document over-promising and the sixth is the
  code writing something unannounced.

`git ls-files` rather than a filesystem walk for the second direction, deliberately: the tree is
what a **reader of the repository** sees, and § 0's whole finding is that those two differ.

Three design constraints, each from a trap this repository has already hit:

| Constraint | Why |
|---|---|
| Compare **paths only**, never the trailing annotation | A test over the comment column is a transcript: the document must stay free to reword *"# generated, ready to ship"* without a test failing |
| The parser must be **proven able to fail** before its zeros are believed | Two of three sweeps written in one earlier batch were incapable of failing when first run. Assert the parse found the expected count on a known-good section, and run it against a deliberately wrong tree |
| Locate the tree by **the section heading**, never by position | *"the fenced block after the third paragraph"* is the row-position trap in a new currency |

---

## 3. Decomposition — 7 tasks

1. **The parser and the two agreement tests**, written first and **red** against today's tree —
   six failures, enumerated in the task so a reviewer can count them.
2. **`scaffold_plugin`**: `steps/` with an `__init__.py`, and `examples/<stem>/.gitkeep`. Both
   directions of task 1's test go green for these two.
3. **§ Creating a plugin's tree**: the README annotation loses the parameter table, `uv.lock` and
   `examples/` gain what they are, `.gitignore` gains its line.
4. **§ Scaffolding's project tree**: `uv.lock`'s annotation. **A confirmation for the rest, not a
   change**: every other line of that tree was checked against a real `publishable new` here, and
   `uv.lock` is the only one missing — the other twelve are all present, and all six of the
   directories it names carry the `.gitkeep` that puts them in the commit. Stated as measured so
   the task is not re-opened as an unknown.
5. **The `docs` payoff sentence** scoped to a project, with the two grounds from § 1 stated where
   a plugin author reads them, so the absence is disclosed rather than silent.
6. **`spec-defects.md`**: struck, with the sixth discrepancy and the project-tree half recorded —
   an entry that closes while its own amendment was still narrower than the defect is worth
   saying out loud.
7. **The tutorial's Route B**: its *"Five differences from the tree"* paragraph and its § Gaps
   entry both go, and the tutorial is then carrying **no open gap of the five it found** — which
   is worth one sentence rather than a silent deletion, since a reader who arrived through the
   filing needs to see where it went.

---

## 4. What is NOT in this slice

- **Loading an installed template's `parameter_spec`.** The blocker under the README region, and a
  slice of its own: `E-TEMPLATE-INSTALLED-UNSUPPORTED` is the last member of a family whose
  retirement is a design question about version reporting, collisions and `template_version`, not
  a scaffold fix.
- **Running `uv lock` in either scaffold.** Argued out in § 1: a creation command that needs a
  network is worse than a lockfile that appears on first use.
- **Generating an example config.** Argued out in § 1: it needs the class the scaffold just wrote
  and would render the placeholder.
- **Managed regions in a plugin README.** They cannot be filled while the point above stands, and
  an empty region is worse than none — `docs` refuses a README with no regions
  (`E-DOCS-NO-REGIONS`, exit `1`), which is the honest signal.
- **`Config.raw`'s missing reader**, filed by W2. Different surface, and its closer has a
  measurement to make first.
