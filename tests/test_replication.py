import pytest

from publishable import ContractError
from publishable.replication import RepeatMember, cross_levels, resolve_repeats


def cfg(repeats):
    return {"replication": {"repeats": repeats}}


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


def test_two_levels_may_share_a_seed_across_levels():
    """A batch varies nothing, so the same seed re-run later is the point —
    a collision check spanning levels would reject the design `batch` exists for."""
    levels = resolve_repeats(cfg([{"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}]), "d")
    outer = {m.seed for m in levels[0].members}
    inner = {m.seed for m in levels[1].members}
    assert len(outer) == 2 and len(inner) == 2  # distinct WITHIN each level


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


def test_fold_is_not_yet_implemented():
    with pytest.raises(ContractError) as e:
        resolve_repeats(cfg([{"kind": "fold", "k": 10}]), "sha256:abc")
    assert e.value.code == "E-REPL-FOLD-UNSUPPORTED"


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
