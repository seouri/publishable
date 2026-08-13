import pytest

from publishable import ContractError
from publishable.replication import (
    LABEL_JOIN,
    RepeatMember,
    cross_levels,
    fold_members_for,
    realize_order,
    resolve_repeats,
)
from publishable.units import Unit


def cfg(repeats):
    return {"replication": {"repeats": repeats}}


def _u(key):
    return Unit(key=key, paths=(), attributes={})


def test_no_replication_block_yields_one_anonymous_seed_level():
    levels = resolve_repeats({}, "d")
    assert len(levels) == 1
    assert levels[0].kind == "seed"
    assert levels[0].n == 1
    assert levels[0].members[0].label == ""


def test_a_single_seed_level_resolves_as_before():
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "d")
    assert len(levels) == 1
    assert levels[0].kind == "seed"
    assert levels[0].n == 3
    assert all(m.label.startswith("seed") for m in levels[0].members)
    assert len({m.seed for m in levels[0].members}) == 3
    assert len({m.label for m in levels[0].members}) == 3


def test_a_batch_level_labels_positionally_from_one():
    levels = resolve_repeats(cfg([{"kind": "batch", "n": 3}]), "d")
    assert [m.label for m in levels[0].members] == ["batch01", "batch02", "batch03"]


def test_two_levels_resolve_outer_to_inner():
    levels = resolve_repeats(cfg([{"kind": "batch", "n": 3}, {"kind": "seed", "n": 2}]), "d")
    assert [lv.kind for lv in levels] == ["batch", "seed"]
    assert [lv.n for lv in levels] == [3, 2]


def test_members_are_not_mutable_through_the_level():
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 2}]), "d")
    with pytest.raises((AttributeError, TypeError)):
        levels[0].members.append(RepeatMember(label="x", seed=1))


def test_two_levels_may_share_a_seed_across_levels(monkeypatch):
    """A batch varies nothing, so the same seed re-run later is the point — the
    collision check must be scoped per level, not across the whole leaf list.

    Using the real digest here would only collide by a ~2**-32 coincidence, which
    would pass identically against the OLD spanning-all-levels check too — proving
    nothing. So `_seed_for` is patched to depend on `index` alone, dropping the
    digest/kind prefix `_seed_members` folds into its first argument. That forces
    batch member i and seed member i to derive the identical seed on purpose: under
    the old check (one collision scan over the flattened leaves) this would raise
    `E-REPL-SEED-COLLISION`; under the per-level check it must resolve cleanly.
    """
    import publishable.replication as replication

    monkeypatch.setattr(replication, "_seed_for", lambda digest, index: index)
    levels = resolve_repeats(cfg([{"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}]), "d")
    outer = [m.seed for m in levels[0].members]
    inner = [m.seed for m in levels[1].members]
    assert outer == inner == [0, 1]  # identical ACROSS levels — what the old check forbade
    assert len(set(outer)) == 2  # still distinct WITHIN each level
    assert len(set(inner)) == 2


def test_five_seed_repeats_resolve_to_five_labelled_members():
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 5}]), "sha256:abc")
    assert levels[0].n == 5
    assert levels[0].kind == "seed"
    assert len({m.label for m in levels[0].members}) == 5
    assert all(m.label.startswith("seed") for m in levels[0].members)


def test_labels_and_seeds_are_stable_for_one_digest():
    a = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "sha256:abc")
    b = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "sha256:abc")
    assert [m.label for m in a[0].members] == [m.label for m in b[0].members]
    assert [m.seed for m in a[0].members] == [m.seed for m in b[0].members]


def test_seeds_move_with_the_design_digest_not_with_parameters():
    a = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "sha256:abc")
    b = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "sha256:def")
    assert [m.seed for m in a[0].members] != [m.seed for m in b[0].members]


def test_no_replication_block_means_one_unlabelled_repeat():
    levels = resolve_repeats({}, "sha256:abc")
    assert levels[0].n == 1
    assert levels[0].members[0].label == ""


@pytest.mark.parametrize(
    "kind,pointer",
    [
        ("bootstrap", "statistics.resample"),
        ("permutation", "statistics.null_test"),
        ("technical", "data.units.measurements"),
        ("biological", "unit table"),
        ("holdout", "data.units.holdout"),
    ],
)
def test_rejected_kinds_are_refused_by_name_with_a_pointer(kind, pointer):
    with pytest.raises(ContractError) as e:
        resolve_repeats(cfg([{"kind": kind, "n": 3}]), "sha256:abc")
    assert e.value.code == "E-REPL-KIND"
    assert pointer in str(e.value)


def test_a_fold_level_resolves_to_k_members():
    levels = resolve_repeats(cfg([{"kind": "fold", "k": 5}]), "d", fold_basis=240)
    assert levels[0].kind == "fold"
    assert [m.label for m in levels[0].members] == [
        "fold01", "fold02", "fold03", "fold04", "fold05"
    ]


def test_k_all_resolves_against_the_roster():
    levels = resolve_repeats(cfg([{"kind": "fold", "k": "all"}]), "d", fold_basis=7)
    assert levels[0].n == 7


def test_k_larger_than_the_roster_is_refused():
    with pytest.raises(ContractError) as exc:
        resolve_repeats(cfg([{"kind": "fold", "k": 300}]), "d", fold_basis=240)
    assert exc.value.code == "E-REPL-FOLD-K-TOO-LARGE"


def test_k_below_two_is_refused():
    with pytest.raises(ContractError) as exc:
        resolve_repeats(cfg([{"kind": "fold", "k": 1}]), "d", fold_basis=240)
    assert exc.value.code == "E-REPL-FOLD-K"


def _clustered_cfg(repeats, cluster_by="animal_id"):
    """The same `replication` block, under a config declaring `cluster_by`.

    Only the *noun* comes from here: `resolve_repeats` reads `cluster_by` to say
    which things it counted, and the count itself is `fold_basis`, resolved by the
    caller from the roster. That is what keeps the two from disagreeing.
    """
    return {
        "data": {"units": {"from": "index.csv", "key": "id", "cluster_by": cluster_by}},
        "replication": {"repeats": repeats},
    }


def test_k_above_the_cluster_count_is_refused():
    """§ Validation, *Folds fit inside the clusters*: `{kind: fold, k: 10}` with
    `cluster_by: animal_id` over 6 animals. `fold_basis=6` is the cluster count the
    caller resolved; the unit count behind it is larger and irrelevant, which is
    the whole point."""
    with pytest.raises(ContractError) as exc:
        resolve_repeats(_clustered_cfg([{"kind": "fold", "k": 10}]), "d", fold_basis=6)
    assert exc.value.code == "E-REPL-FOLD-K-TOO-LARGE"
    assert "6 clusters of `animal_id`" in str(exc.value)


def test_the_same_k_is_accepted_when_nothing_is_clustered():
    """The control that must report: `k: 10` against a basis of 15 is a legal fold
    count, so the refusal above is the clustering and not the `k`."""
    levels = resolve_repeats(cfg([{"kind": "fold", "k": 10}]), "d", fold_basis=15)
    assert levels[0].n == 10


def test_k_all_is_leave_one_cluster_out():
    """§ Validation, *Leave-one-out is affordable*: under `cluster_by`, `k: all`
    stops meaning one unit per fold. 5 clusters over the 15-unit roster
    `units.fold_basis` counted, so 5 folds — not 15."""
    levels = resolve_repeats(_clustered_cfg([{"kind": "fold", "k": "all"}]), "d", fold_basis=5)
    assert levels[0].n == 5
    assert [m.label for m in levels[0].members] == [
        "fold01", "fold02", "fold03", "fold04", "fold05"
    ]


def test_k_all_is_leave_one_unit_out_when_nothing_is_clustered():
    """The unclustered control: the same 15-unit roster with no `cluster_by` gives
    a basis of 15, so `k: all` is 15 folds. Uneven clusters are what make the two
    numbers different — one unit per cluster and neither behaviour is visible."""
    levels = resolve_repeats(cfg([{"kind": "fold", "k": "all"}]), "d", fold_basis=15)
    assert levels[0].n == 15


def test_k_all_over_a_single_cluster_reports_the_illegal_count_it_resolved_to():
    """One cluster leaves nothing to hold out against, so `k: all` resolves to 1
    and falls into the `k >= 2` refusal — reported by number rather than by the
    word `all`, which is what says the count was resolved and found illegal rather
    than unreadable. A diagnostic, never a traceback."""
    with pytest.raises(ContractError) as exc:
        resolve_repeats(_clustered_cfg([{"kind": "fold", "k": "all"}]), "d", fold_basis=1)
    assert exc.value.code == "E-REPL-FOLD-K"
    assert "k: 1" in str(exc.value)


def test_an_empty_cluster_by_does_not_rename_the_units_the_refusal_counted():
    """An empty `cluster_by` changes no behavior and is reported elsewhere
    (`E-DATA-CLUSTER-UNKNOWN`); the basis it produces is the unit count, so the
    refusal must not describe those units as clusters of ``."""
    with pytest.raises(ContractError) as exc:
        resolve_repeats(_clustered_cfg([{"kind": "fold", "k": 300}], ""), "d", fold_basis=240)
    assert exc.value.code == "E-REPL-FOLD-K-TOO-LARGE"
    assert "240 resolved units" in str(exc.value)


def test_k_all_without_a_roster_is_refused():
    with pytest.raises(ContractError) as exc:
        resolve_repeats(cfg([{"kind": "fold", "k": "all"}]), "d")
    assert exc.value.code == "E-REPL-FOLD-K"


def test_stratify_by_is_refused():
    with pytest.raises(ContractError) as exc:
        resolve_repeats(
            cfg([{"kind": "fold", "k": 5, "stratify_by": "site"}]), "d", fold_basis=240
        )
    assert exc.value.code == "E-REPL-FOLD-STRATIFY-UNSUPPORTED"


def test_fold_outside_seed_composes_labels_outer_to_inner():
    levels = resolve_repeats(
        cfg([{"kind": "fold", "k": 2}, {"kind": "seed", "n": 2}]), "d", fold_basis=10
    )
    labels = [lf.label for lf in cross_levels(levels)]
    assert labels[0].startswith("fold01" + LABEL_JOIN)
    assert len(labels) == 4


def test_batch_is_now_supported():
    levels = resolve_repeats(cfg([{"kind": "batch", "n": 3}]), "sha256:abc")
    assert levels[0].kind == "batch"
    assert levels[0].n == 3


def test_more_than_two_levels_is_refused():
    with pytest.raises(ContractError) as e:
        resolve_repeats(
            cfg(
                [
                    {"kind": "batch", "n": 2},
                    {"kind": "seed", "n": 2},
                    {"kind": "seed", "n": 2},
                ]
            ),
            "sha256:abc",
        )
    assert e.value.code == "E-REPL-LEVEL-DEPTH"


def test_two_levels_of_the_same_kind_are_refused():
    with pytest.raises(ContractError) as e:
        resolve_repeats(cfg([{"kind": "seed", "n": 2}, {"kind": "seed", "n": 3}]), "sha256:abc")
    assert e.value.code == "E-REPL-LEVEL-DUPLICATE"


def test_a_batch_declared_inside_another_level_is_refused():
    # Nested the other way round the outer level varies nothing but a directory
    # name: every leaf takes the batch member's seed, and batch seeds do not
    # depend on the outer member. Six executions, three RNG streams.
    with pytest.raises(ContractError) as e:
        resolve_repeats(cfg([{"kind": "seed", "n": 2}, {"kind": "batch", "n": 3}]), "sha256:abc")
    assert e.value.code == "E-REPL-LEVEL-BATCH-INNER"
    assert "outermost" in str(e.value)


def test_a_batch_declared_outermost_is_accepted():
    levels = resolve_repeats(
        cfg([{"kind": "batch", "n": 3}, {"kind": "seed", "n": 2}]), "sha256:abc"
    )
    assert [lv.kind for lv in levels] == ["batch", "seed"]


def test_colliding_seeds_are_refused_rather_than_silently_perturbed(monkeypatch):
    import publishable.replication as replication

    monkeypatch.setattr(replication, "_seed_for", lambda digest, index: 42)
    with pytest.raises(ContractError) as e:
        replication.resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "sha256:abc")
    assert e.value.code == "E-REPL-SEED-COLLISION"
    assert "42" in str(e.value)


def test_five_seed_repeats_have_no_collisions_on_a_real_digest():
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 5}]), "sha256:abc")
    members = levels[0].members
    assert len(members) == 5
    assert len({m.seed for m in members}) == 5
    assert len({m.label for m in members}) == 5
    for m in members:
        assert m.label[:4] == "seed"
        assert m.label[4:].isdigit()


def test_one_level_crosses_to_its_own_members():
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "d")
    leaves = cross_levels(levels)
    assert [lf.label for lf in leaves] == [m.label for m in levels[0].members]


def test_two_levels_cross_with_the_inner_varying_fastest():
    levels = resolve_repeats(cfg([{"kind": "batch", "n": 3}, {"kind": "seed", "n": 2}]), "d")
    leaves = cross_levels(levels)
    assert len(leaves) == 6
    inner = [m.label for m in levels[1].members]
    assert [lf.label for lf in leaves] == [
        f"batch01_{inner[0]}", f"batch01_{inner[1]}",
        f"batch02_{inner[0]}", f"batch02_{inner[1]}",
        f"batch03_{inner[0]}", f"batch03_{inner[1]}",
    ]


def test_a_leaf_takes_the_innermost_seed_and_kind():
    levels = resolve_repeats(cfg([{"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}]), "d")
    leaves = cross_levels(levels)
    inner = levels[1].members
    assert [lf.seed for lf in leaves] == [inner[0].seed, inner[1].seed] * 2
    assert {lf.kind for lf in leaves} == {"seed"}


def test_the_anonymous_single_repeat_keeps_its_empty_label():
    leaves = cross_levels(resolve_repeats({}, "d"))
    assert [lf.label for lf in leaves] == [""]


def test_as_declared_is_the_identity():
    # Six pairs, not two: with two, a mutant that shuffled unconditionally would
    # return the input order roughly half the time and pass.
    levels = resolve_repeats({"replication": {"repeats": [{"kind": "seed", "n": 3}]}}, "d")
    pairs = [(c, lf.label) for c in (0, 1) for lf in cross_levels(levels)]
    assert len(pairs) == 6
    assert realize_order(pairs, levels, "as_declared", 7) == pairs


def test_randomized_keeps_batches_in_declared_order():
    levels = resolve_repeats({"replication": {"repeats": [
        {"kind": "batch", "n": 3}, {"kind": "seed", "n": 2}]}}, "d")
    pairs = [(c, lf.label) for c in (0, 1) for lf in cross_levels(levels)]
    out = realize_order(pairs, levels, "randomized", 7)
    batches = [lb.split("_")[0] for _, lb in out]
    assert batches == sorted(batches), "batches must not be shuffled against each other"
    assert len(out) == len(pairs) and sorted(out) == sorted(pairs)


def test_randomized_shuffles_within_a_batch():
    levels = resolve_repeats({"replication": {"repeats": [
        {"kind": "batch", "n": 2}, {"kind": "seed", "n": 4}]}}, "d")
    pairs = [(c, lf.label) for c in (0, 1, 2) for lf in cross_levels(levels)]
    out = realize_order(pairs, levels, "randomized", 7)
    assert out != pairs, "some batch's interior must have been reordered"


def test_the_same_order_seed_reproduces_the_same_order():
    levels = resolve_repeats({"replication": {"repeats": [
        {"kind": "batch", "n": 2}, {"kind": "seed", "n": 3}]}}, "d")
    pairs = [(c, lf.label) for c in (0, 1) for lf in cross_levels(levels)]
    assert realize_order(pairs, levels, "randomized", 7) == \
           realize_order(pairs, levels, "randomized", 7)
    assert realize_order(pairs, levels, "randomized", 7) != \
           realize_order(pairs, levels, "randomized", 99)


def test_with_no_batch_level_the_whole_run_is_one_block():
    """The documents describe the shuffle only in terms of batches; the spec pins
    this case: no batch boundary means nothing bounds the shuffle."""
    levels = resolve_repeats({"replication": {"repeats": [{"kind": "seed", "n": 4}]}}, "d")
    pairs = [(c, lf.label) for c in (0, 1, 2) for lf in cross_levels(levels)]
    out = realize_order(pairs, levels, "randomized", 7)
    assert sorted(out) == sorted(pairs) and out != pairs


def test_a_pair_matching_no_resolved_batch_is_a_contract_error():
    levels = resolve_repeats({"replication": {"repeats": [
        {"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}]}}, "d")
    pairs = [(0, "no-such-batch_seed01")]
    with pytest.raises(ContractError) as excinfo:
        realize_order(pairs, levels, "randomized", 7)
    assert excinfo.value.code == "E-REPL-ORDER-UNRESOLVED"


def test_no_fold_level_yields_none():
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "d")
    assert fold_members_for(levels, []) is None


def test_a_fold_level_maps_each_label_to_its_partition():
    levels = resolve_repeats(cfg([{"kind": "fold", "k": 2}]), "d", fold_basis=4)
    parts = [[_u("a"), _u("b")], [_u("c"), _u("d")]]
    assert fold_members_for(levels, parts) == {
        "fold01": frozenset({"a", "b"}),
        "fold02": frozenset({"c", "d"}),
    }


def test_the_map_covers_every_unit_exactly_once():
    levels = resolve_repeats(cfg([{"kind": "fold", "k": 3}]), "d", fold_basis=9)
    parts = [[_u(f"u{i}") for i in grp] for grp in ([0, 1, 2], [3, 4, 5], [6, 7, 8])]
    members = fold_members_for(levels, parts)
    allk = [k for s in members.values() for k in s]
    assert len(allk) == 9 and len(set(allk)) == 9


def test_a_fold_in_non_outermost_position_is_still_found_by_kind():
    """`batch` is the only kind required to be outermost, so `[batch, fold]` is a
    legitimate design with fold at position 1. A selector that grabbed `levels[0]`
    would read the batch level's members here instead, and its labels
    (`batch01`/`batch02`) would not match — this is what proves the selection is
    by kind, not position."""
    levels = resolve_repeats(
        cfg([{"kind": "batch", "n": 2}, {"kind": "fold", "k": 2}]), "d", fold_basis=4
    )
    parts = [[_u("a"), _u("b")], [_u("c"), _u("d")]]
    assert fold_members_for(levels, parts) == {
        "fold01": frozenset({"a", "b"}),
        "fold02": frozenset({"c", "d"}),
    }


def test_a_batch_level_declaring_a_field_other_than_n_is_refused():
    """`reference.md` § Repeat kinds gives a `batch` `n` and "nothing else — a batch
    has no parameter of its own, which is the point", and § Validation's "Batch
    takes no fields" row says the same. `_check_count_field` refused only `k`, so
    `{kind: batch, n: 5, stratify_by: x}` resolved silently — a declaration that
    reads as a stratified batch and executes as an unstratified one."""
    with pytest.raises(ContractError) as e:
        resolve_repeats(cfg([{"kind": "batch", "n": 5, "stratify_by": "x"}]), "d")
    assert e.value.code == "E-REPL-LEVEL-FIELD"
    assert "stratify_by" in str(e.value)


def test_a_batch_declaring_k_still_reports_the_count_field_message():
    """The new key check runs after `_check_count_field`, so the documented
    `{kind: batch, k: 3}` case keeps the message naming `n` as its count rather
    than being absorbed into the generic unknown-key wording."""
    with pytest.raises(ContractError) as e:
        resolve_repeats(cfg([{"kind": "batch", "k": 3}]), "d")
    assert e.value.code == "E-REPL-LEVEL-FIELD"
    assert "its count is `n`" in str(e.value)


def test_the_key_closure_does_not_reach_a_seed_level():
    """The closure is `batch`-only. `seeds: [17, 42, …]` is a documented `seed`
    field (`reference.md` § Repeat kinds), so refusing it here would reject a
    declaration the document allows; a `fold` level's `stratify_by` reaches its
    own refusal (`E-REPL-FOLD-STRATIFY-UNSUPPORTED`) rather than this one."""
    try:
        resolve_repeats(cfg([{"kind": "seed", "n": 2, "seeds": [17, 42]}]), "d")
    except ContractError as exc:  # pragma: no cover — nothing raises here today
        # Asserted as a negative rather than as successful resolution: `seeds` is
        # read by nothing in this build, so a later slice may well refuse it under
        # a code of its own. What this test owns is only that the refusal is not
        # this one.
        assert exc.code != "E-REPL-LEVEL-FIELD"
    with pytest.raises(ContractError) as e:
        resolve_repeats(cfg([{"kind": "fold", "k": 2, "stratify_by": "label"}]), "d", fold_basis=4)
    assert e.value.code == "E-REPL-FOLD-STRATIFY-UNSUPPORTED"
