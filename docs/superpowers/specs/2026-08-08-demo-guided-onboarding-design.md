# `demo` as guided onboarding

**Status:** approved.
**Deliverable:** documentation only. This repository is specification, not implementation
— there is no `src/`, no `pyproject.toml`, and no installed CLI, so nothing here is built.
The change is edits to `README.md`, `docs/reference.md`, and `docs/design-principles.md`.
The behavior below is what those documents will then specify, for whoever writes the code
later.

## The problem

`publishable demo` currently builds a worked example and runs it, end to end, in one
uninterrupted burst. A first-time user watches a repo, a dataset, a config, and a
results table scroll past and learns nothing about the commands that produced them —
the transcript in `README.md` § Try it shows `demo` doing the work, not the user.

The one thing `demo` genuinely saves a newcomer is *data in the right format*, which is
the hardest input to come by. Everything after that is the CLI the user has to learn
anyway. So `demo` should hand over the data and then walk the user through the real
commands, one at a time, the way a mobile app walks someone through first launch.

## The shape

`demo` becomes a six-stop guided sequence. Stops 3 through 5 — the ones that execute
something — have the same beat:

1. Print the next **real** command, exactly as the user would type it.
2. Wait — `[Enter]` to run it, `q` to stop.
3. Run it, showing its own output unmodified.
4. Explain the output in two or three lines, then move to the next stop.

| Stop | Command run | What the stop teaches |
|---|---|---|
| 1 | *(none — `demo` does this itself)* | **Data in the right format.** Writes 240 synthetic units to `~/publishable-demo-data/input/`, scaffolds `src/correlation_pilot/` and `configs/correlation-pilot/config.yaml`, then `git init` and a first commit. Explains why the data sits outside the repo |
| 2 | *(none — `demo` prints a file)* | **The config is the whole description of the run.** Shows the `conditions` and `replication` blocks of `config.yaml` verbatim. Invites a look, not an edit |
| 3 | `publishable validate configs/correlation-pilot/config.yaml` | Reads the config and the input, creates nothing, reaches nothing off the machine |
| 4 | `publishable dry-run configs/correlation-pilot/config.yaml` | 3 conditions × 5 repeats = 15 executions, and every artifact path that *would* be written. Still creates nothing |
| 5 | `publishable run configs/correlation-pilot/config.yaml` | The results table — estimates, intervals over units, paired deltas against the baseline |
| 6 | *(none — `demo` prints the `reproduce` invocation)* | `run.yaml` is the deliverable. Closes by pointing at `publishable new` |

Stop 6 is the one stop that prints without executing. `reproduce` reads
`provenance.git.remote` and clones it; the demo repo has one local commit and no remote,
so running it would fail on its first step in the last thing a new user sees. Printing it
is also the truer lesson — `reproduce` is what someone else runs, elsewhere.

Stop 2 is deliberately a **config** beat and not a **source** beat. `code_hash` covers
`src/**` and `templates/**`, so inviting an edit to a step would dirty the tree and make
stop 5 refuse — turning the first `run` a user ever issues into an error message. A
config edit is free: `parameters_hash` changes, nothing is blocked.

### The rule that makes the pauses legal

**A pause may never alter the config.** No stop asks which method to sweep, how many
repeats to use, or where the output should go. Every prompt is Enter-or-quit, and the
config `demo` wrote at stop 1 is the config `run` executes at stop 5. Guided is not
parameterized: if a prompt could change what runs, the file would stop being the only
description of the run, and § Everything is in the file would be false in the first
thing a new user touches.

This is also the clause that belongs in `design-principles.md` — the rest of the change
is CLI surface, but this one sentence is a rule, and rules live in the normative
document with their reason attached.

### Headless

`demo` detects whether it is attached to a TTY. Piped, redirected, or in CI, it runs the
identical sequence with no pauses and no prompts — same commands, same order, same
output. This is not a mode and takes no flag: the pause changes *presentation* only,
never what executes, so there is nothing for a mode name to distinguish. It also keeps
`demo` usable as the end-to-end acceptance test, which a command that blocks on a human
could not be.

### Quitting and resuming

`q` at any stop prints the remaining commands in order, so a user who leaves has the
whole path written down, and tells them that running `publishable demo` again from the
demo directory picks up where they stopped.

`validate` and `dry-run` create nothing, so the filesystem alone cannot distinguish stop
3 from stop 4. `demo` therefore records the last completed stop in `.demo-progress` in
the demo repo root, named in the generated `.gitignore`. Two properties matter and must
be stated wherever the marker is documented:

- it is **not** under `src/**` or `templates/**`, so it can never move `code_hash`;
- it is **gitignored**, so it can never make the tree dirty and can never push a user
  onto `draft`.

Re-invoking `demo` in a directory that holds a marker reprints the last stop's
explanation for context and continues from the next stop. `--into DIR` is unchanged; it
chooses which directory this applies to, and pointed at one that already holds a
`.demo-progress` it resumes there. Resuming is a property of the directory, not of how
it was named.

## Documentation changes

| File | Change |
|---|---|
| `README.md` § Try it | The single transcript becomes a staged one. Show stop 1 and one full stop beat (the `validate` stop, which is the shortest complete illustration of print → wait → run → explain), then the stop-5 results table as it stands today. Do not print all six stops in full — README is the pitch, not the reference |
| `README.md` § Commands | The `demo` row currently reads "Build and run a complete worked example, no setup required." It no longer builds *and runs* in one motion |
| `docs/reference.md` § CLI reference | The `demo` row under **Creation commands**. Arguments are unchanged (`*(none)*`, `[--into DIR]`) |
| `docs/reference.md` | A new short subsection carrying the semantics a table row cannot: the six stops, the no-pause-may-alter-the-config rule, TTY detection, `q`, and the progress marker with both of its properties. Anchor must use hyphens |
| `docs/design-principles.md` | The pause rule, seated next to § Everything is in the file — plus `demo` and `study new`/`study add` added to that section's creation-command enumeration, which listed only three of six. Nothing else in that document changes |

`docs/experimental-designs.md` has no `demo` reference and is not touched.

## What must not drift

The demo transcript carries numbers that `CLAUDE.md` pins and that were checked
numerically. Re-flowing one transcript into staged screens is exactly where an interval
gets silently re-rounded, so these carry through **unchanged**:

- 240 units, 228 completed, 12 failed
- r = 0.581 `[0.488, 0.661]` · 0.607 `[0.517, 0.683]` · 0.412 `[0.347, 0.477]`
- delta +0.026 `[−0.007, 0.059]` · −0.169 `[−0.213, −0.125]`
- `std 0.014` — a standard deviation, never written as a `±` interval
- code hash prefix `2f5c8d0`, run ID `run_2026-08-07T09-14-03Z_2f5c8d0`
- experiment `correlation_pilot`, config `correlation-pilot`
- "a three-step pipeline" — the demo is a *different* experiment from the four-step
  worked example, and three is correct

`~/publishable-demo-data/` living outside the created repo is not incidental. Under this
design it becomes the thing stop 1 explains, so it must stay where it is.

## Explicitly out of scope

- Any prompt that accepts a value. See the pause rule.
- Any new flag. `--into DIR` is the only argument `demo` takes.
- Widening `demo` to teach `study`, `report`, `diff`, or plugins. Six stops is the
  whole sequence; stop 6 hands off to `publishable new` rather than continuing.
- `CLAUDE.md`'s creation-command list omits `demo` where `reference.md` files it under
  Creation commands. Pre-existing and minor — noted, not fixed here. (The same omission
  in `design-principles.md` *is* fixed, because this change adds a `demo` paragraph to
  the very section that under-enumerated.)
