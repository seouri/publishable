# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status: specification only, no implementation

`git ls-files` returns six files. There is no `src/`, no `pyproject.toml`, no `tests/`, and no installed CLI — the entire repo is `README.md` plus `docs/*.md`.

**There are no build, lint, or test commands.** Do not invent them, and do not run `publishable <anything>`: the binary does not exist here. The commands described throughout the docs are the CLI this project *specifies*, not commands available in this working tree. Likewise, `docs/reference.md:1256` ("Package layout") is a *planned* source tree — those files do not exist yet.

Work in this repo is therefore documentation work: refining the design, keeping the three docs consistent with each other and with the README.

## The documents

| File | Role |
|---|---|
| `README.md` | The pitch and the whole arc, for someone deciding whether to use it |
| `docs/design-principles.md` | **Normative.** Why each rule is what it is |
| `docs/experimental-designs.md` | How each experimental design is expressed; what core prevents and refuses |
| `docs/reference.md` | Config schema, CLI, `io` API, templates, sweeps, artifact layout |

`design-principles.md` is the tiebreaker. Read it before proposing a change to any rule — if a rule looks arbitrary, that file explains it, and if it doesn't, that gap is itself worth fixing.

## Invariants a change must not quietly break

These are load-bearing across all four documents; contradicting one in a single section creates a real inconsistency, not a wording nit.

- **Operation commands take paths and nothing else.** No parameter flags, no selectors, no behavior-changing env vars. Modes get their own command names (`dry-run`, `draft`, `resume`) rather than `--dry-run`/`--allow-dirty`. Only creation commands (`new`, `plugin new`, `generate`/`init`, `study new|add`) take arguments beyond a path. (`design-principles.md` § Everything is in the file)
- **Three hashes, split on purpose.** `code_hash` covers `src/**` only, separate from `parameters_hash` and `input_manifest_hash`. That split is what makes "same code, different parameters" provable across unrelated commits.
- **`input_dir`/`output_dir` may never resolve inside the git repo**, checked at generate, validate, and run.
- **Condition vs. repeat.** A condition is a difference being measured; a repeat is a difference being averaged over. Statistics aggregate *within* a condition and compare *across* conditions — never the reverse.
- **`parameter_spec` is the single source of truth** for what `init` writes, what its inline comments say, and what `validate` enforces. There is deliberately no separate defaults file.
- **Core vs. plugin test:** would it be identical for a wet-lab assay, a simulation sweep, and an LLM benchmark? If not, it's a plugin. Core ships exactly one template, `generic`.
- **Greenfield only** — no `adopt` command, ever. Core validates *declarations* and verifies *effects*; it never inspects the body of user Python.
- **`uv` and git are mandatory**, not optional paths.

The stated non-promises — adaptive/sequential designs, per-condition pipeline variation, factorial main effects and interactions, bit-identical reruns, scientific validity — are deliberate refusals with reasons attached, not gaps waiting to be filled. Treat a request to add one as a design change requiring an argument against `design-principles.md`, not a feature request.

## Documentation conventions

- Filenames are kebab-case, matching the doc's title.
- Cross-references between the four documents are dense and anchor-based. Renaming a heading breaks links elsewhere — grep the other files for the old anchor.
- `<!-- publishable:begin ... -->` / `publishable:end` regions in the docs are examples of *machine-managed* README regions in generated projects, rewritten by `publishable docs`. Text outside them is hand-written.
- Prose style is declarative and reason-giving: state the rule, then why it exists. Tables carry the dense material.
