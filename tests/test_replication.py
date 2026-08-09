import pytest

from publishable import ContractError
from publishable.replication import resolve_repeats


def cfg(repeats):
    return {"replication": {"repeats": repeats}}


def test_five_seed_repeats_resolve_to_five_labelled_repeats():
    reps = resolve_repeats(cfg([{"kind": "seed", "n": 5}]), "sha256:abc")
    assert len(reps) == 5
    assert all(r.kind == "seed" for r in reps)
    assert len({r.label for r in reps}) == 5
    assert all(r.label.startswith("seed") for r in reps)


def test_labels_and_seeds_are_stable_for_one_digest():
    a = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "sha256:abc")
    b = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "sha256:abc")
    assert [r.label for r in a] == [r.label for r in b]
    assert [r.seed for r in a] == [r.seed for r in b]


def test_seeds_move_with_the_design_digest_not_with_parameters():
    a = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "sha256:abc")
    b = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "sha256:def")
    assert [r.seed for r in a] != [r.seed for r in b]


def test_no_replication_block_means_one_unlabelled_repeat():
    reps = resolve_repeats({}, "sha256:abc")
    assert len(reps) == 1
    assert reps[0].label == ""


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


def test_s1_does_not_yet_implement_batch_or_fold():
    with pytest.raises(ContractError) as e:
        resolve_repeats(cfg([{"kind": "fold", "k": 10}]), "sha256:abc")
    assert e.value.code == "E-REPL-KIND-UNSUPPORTED"
