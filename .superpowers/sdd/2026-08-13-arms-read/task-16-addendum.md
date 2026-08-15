# Task 16 — controller additions

These are requirements, with the same force as the brief file they accompany.

## Task 1's decision, in the document, verbatim

§ What `auto` derives from now reads: the design digest is over *"`data.units` (**every field except
`assign.seed` itself**) and `sweep.groups`"*. **The document decided and the code follows** — exclude
`assign.seed` from `design_digest`. Do not reopen it; if you think the exclusion is wrong, say so in
your report and implement it anyway.

The reason is in the same section's next paragraph, and it is worth having in the docstring: an axis's
`assign.seed` *"mixes digest + the axis name + the resolved roster"*. A seed that is itself inside the
digest it is mixed with makes the derivation self-referential — pin the seed and the digest moves, so
the derivation the pinned seed was meant to fix moves with it. That is the defect, not an aesthetic
preference.

## The exclusion must be surgical, and the control is what proves it

`assign` is a mapping of **axis name → block**, so the exclusion is per-axis: drop `seed` from each
block, keep everything else. The brief's control (changing `data.units.key` **does** change the digest)
is necessary but not sufficient — it would still pass if you dropped the whole `assign` block, or the
whole `data.units.assign` subtree.

**Three more cases, each of which must change the digest:**

- `assign.arm.from` — a different attribute is a different partition
- `assign.arm.stratify_by` — different balancing is a different draw
- adding a second axis to `assign` at all

and one more that must **not**: `assign.arm.seed` on a *second* axis, so the exclusion is shown to be
per-block rather than "the first one found". Without these, "excluded `assign.seed`" and "excluded
`assign`" are indistinguishable, which is this project's dominant defect class — a check that cannot
fail — and it has appeared ten-plus times across three slices.

## Do not disturb the wholesale canonicalisation's other half

`design_digest` canonicalises `data.units` wholesale today, which is what made `assign.seed` land inside
it in the first place. Whatever mechanism you use to carve out one key, state in the docstring what it
does with a `data.units` shape it does not expect — a non-mapping `assign`, an axis whose block is not
a mapping, a `seed` key that is `None`. `design_digest` runs at run time on a **validated** config, but
`validate` itself calls it, so a malformed config reaches it first. It must not raise there.

## `sweep.yaml` and the recorded record

§ What `auto` derives from says the digest is *"recorded in `sweep.yaml` beside the values it produced so
`reproduce` regenerates the same partitions"*. Changing what the digest covers changes what a recorded
digest means. **Check whether any existing test pins a digest value literally** — if one does, it will
now be wrong, and updating the expected string without understanding why is how a hash test becomes
decorative. Say in your report what you found.

## Mutation

Reverting the exclusion must fail the `assign.seed` test and **not** the control. If it fails both, the
control is not independent of the thing being tested. Delete `__pycache__` between mutation and revert;
verify the revert by running the tests, never by `git status`.


## Correction from the pre-flight audit

My `validate`-exposure argument was right for the wrong reason. `validate` reaches `design_digest` only
indirectly — via `expand` → the `sample` seed derivation, and only when `sweep.sample` is declared with
an `auto` seed — and `sweep.py` **already** converts a `TypeError` there into `E-SWEEP-SAMPLE-INVALID`.
The requirement stands, but the live hazard is different and worth naming: a per-axis carve-out calling
`.items()` on a non-mapping `assign` raises **`AttributeError`**, which that existing `except TypeError`
does **not** catch. Handle the shape, not the exception type.

Verified clean in the same pass: § What `auto` derives from reads *"`data.units` (every field except
`assign.seed` itself) and `sweep.groups`"* verbatim; `design_digest` does canonicalise `data.units`
wholesale; and **no test pins a digest literal** — the three that touch digests compare them between
runs, so none needs an expected string updated.
