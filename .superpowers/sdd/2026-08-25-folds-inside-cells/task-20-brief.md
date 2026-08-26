## Task 20

**Corrections that bind this task: C1.** **This task is where "no slice follows" is written down.**

Three things.

**(a) Strike the closed filing.** `spec-defects.md`'s `## OPEN — an evaluation split cannot be drawn
within a cell` is closed by this slice: strike it in place, this file being the one exception to the
never-retro-edit rule, and name the slice that closed it.

**(b) Sweep every entry whose `unassigned` reason enumerates *"H3c-3's remaining 14"*.** `grep -c
"H3c-3" docs/superpowers/spec-defects.md` → **56 lines** at `3d72910`; 57 headings begin `## OPEN`.
That phrase becomes **false** the day this slice merges. Rewrite each occurrence to the form the file
requires: **`unassigned`, with the reason stated as a fact — *no slice follows this one*** — not as a
deferral and never as *"whichever slice next touches X"*, the form this file rejects by name.

**(c) File the three gaps this slice declines**, each with the no-later-slice sentence:

1. **A cluster spanning two cells** (design Decision 13). Legal under `by_attribute`, impossible under
   `random` (which allocates whole clusters). Breaks the between-sides independence H4c's
   `welch_t_over_units_clustered` and `unpaired_percentile_over_units_clustered` assume, each side
   contributing `G_s − 1` to a Welch-Satterthwaite df while a spanning cluster is counted twice. The
   check that would close it is a constant-cluster-within-arm rule, `stratum_varies_within_cluster`'s
   shape one declaration over. **Owner: `unassigned`. Reason: no slice follows.** Note that C1's own
   measured fixture has one.
2. **`limits.min_clusters` under cells** (design Decision 4). The denominator stays roster-wide;
   H3d already found it *"wrong in the direction of NOT firing"*. **Owner: `unassigned`. Reason: no
   slice follows.**
3. **The per-stratum fold bound** (task 19). **Owner: `unassigned`. Reason: no slice follows.**

And **re-read every filing whose text describes code this slice changed** — a filing's claims about
the code go stale like any other comment.

**Must not touch:** any `src/` file. **A ledger line saying "filed" is not a filing:** the entry must
exist in `spec-defects.md`, and the report must quote its heading.

---

# Batch F — documents and end to end

