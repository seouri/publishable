import pytest

from publishable.sweep import Condition, expand


def test_no_sweep_block_is_one_unlabelled_condition():
    """label None is what keeps the `conditions/` level out of the tree."""
    conds = expand({})
    assert conds == [Condition(index=0, label=None, values={}, is_baseline=False)]


def test_a_bare_baseline_is_one_condition_but_labelled():
    """Declared, not count: a sweep with one condition still gets the tree level."""
    conds = expand({"sweep": {"baseline": {"analysis.method": "pearson"}}})
    assert len(conds) == 1
    assert conds[0].label == "baseline"
    assert conds[0].is_baseline is True
    assert conds[0].values == {"analysis.method": "pearson"}


def test_baseline_plus_grid_prepends_the_baseline():
    conds = expand({
        "sweep": {
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman", "kendall"]},
        }
    })
    assert [c.index for c in conds] == [0, 1, 2]
    assert [c.label for c in conds] == ["baseline", "method=spearman", "method=kendall"]
    assert [c.is_baseline for c in conds] == [True, False, False]
    assert conds[1].values == {"analysis.method": "spearman"}


def test_grid_without_a_baseline_starts_at_zero():
    conds = expand({"sweep": {"grid": {"analysis.method": ["pearson", "spearman"]}}})
    assert [c.index for c in conds] == [0, 1]
    assert not any(c.is_baseline for c in conds)


def test_the_last_declared_axis_varies_fastest():
    """Numbering reads like nested loops written in declaration order."""
    conds = expand({
        "sweep": {"grid": {"a.x": [1, 2], "b.y": ["p", "q"]}}
    })
    assert [c.values for c in conds] == [
        {"a.x": 1, "b.y": "p"},
        {"a.x": 1, "b.y": "q"},
        {"a.x": 2, "b.y": "p"},
        {"a.x": 2, "b.y": "q"},
    ]


def test_an_empty_grid_axis_still_expands_to_nothing_here():
    """`expand` is pure and reports what the declaration says; `validate` is what
    refuses it (E-SWEEP-AXIS-EMPTY, Task 4). Pinned so the refusal has something
    to refuse and so nobody later reads the empty list as acceptable output."""
    assert expand({"sweep": {"grid": {"a.x": []}}}) == []


def test_condition_values_are_immutable():
    conds = expand({"sweep": {"baseline": {"analysis.method": "pearson"}}})
    assert conds[0].values["analysis.method"] == "pearson"
    with pytest.raises(TypeError):
        conds[0].values["x"] = 1


def test_condition_values_are_copied_not_aliased():
    source = {"analysis.method": "pearson"}
    conds = expand({"sweep": {"baseline": source}})
    source["analysis.method"] = "spearman"
    assert conds[0].values["analysis.method"] == "pearson"


def test_conditions_are_frozen():
    c = expand({"sweep": {"grid": {"a.x": [1]}}})[0]
    with pytest.raises(Exception):  # noqa: B017 — frozen dataclass raises FrozenInstanceError
        c.index = 5  # type: ignore[misc]


def test_a_single_axis_uses_the_shortest_suffix():
    conds = expand({"sweep": {"grid": {"analysis.method": ["spearman"]}}})
    assert conds[0].label == "method=spearman"


def test_a_shared_leaf_forces_both_keys_to_keep_a_segment():
    """The rule is shortest UNIQUE suffix, not shortest suffix."""
    conds = expand({
        "sweep": {"grid": {"analysis.method": ["pearson"], "scoring.method": ["auc"]}}
    })
    assert conds[0].label == "analysis.method=pearson__scoring.method=auc"


def test_a_three_segment_path_disambiguates_only_as_far_as_needed():
    conds = expand({
        "sweep": {"grid": {"a.b.method": ["x"], "c.d.method": ["y"]}}
    })
    assert conds[0].label == "b.method=x__d.method=y"


def test_axes_appear_in_declaration_order_never_sorted():
    conds = expand({"sweep": {"grid": {"z.one": ["a"], "a.two": ["b"]}}})
    assert conds[0].label == "one=a__two=b"


def test_booleans_and_floats_render_readably():
    conds = expand({"sweep": {"grid": {"f.flag": [True, False], "g.rate": [0.5]}}})
    assert [c.label for c in conds] == ["flag=true__rate=0.5", "flag=false__rate=0.5"]


def test_a_value_rendering_the_axis_separator_is_refused():
    from publishable.sweep import check_swept_value
    message = check_swept_value("a__b")
    assert message is not None
    assert "a__b" in message
    assert "__" in message


def test_a_single_underscore_is_still_accepted():
    """Narrowing the pattern to exclude `_` entirely would be over-correction —
    only the two-character separator sequence is the conflict."""
    from publishable.sweep import check_swept_value
    assert check_swept_value("a_b") is None


def test_values_already_refused_by_the_pattern_are_still_refused():
    """The separator check is on top of the pattern check, not instead of it."""
    from publishable.sweep import check_swept_value
    assert check_swept_value("a b") is not None
    assert check_swept_value("a/b") is not None


def test_every_generated_label_body_matches_the_selector_pattern():
    import re

    from publishable.sweep import SWEPT_VALUE_PATTERN
    conds = expand({
        "sweep": {"baseline": {"analysis.method": "pearson"},
                  "grid": {"analysis.method": ["spearman", "kendall"]}}
    })
    for c in conds:
        for part in c.label.split("__"):
            value = part.split("=")[-1]
            assert re.match(SWEPT_VALUE_PATTERN, value), part


def test_the_sweep_document_records_the_resolved_plan():
    """Matches `docs/reference.md` § "`sweep.yaml` — the resolved plan" exactly:
    `repeats` groups by kind with resolved `seeds`, `labels` is the separate
    composed-label list, `order` is the scalar mode, and `execution_order` is
    the realized `{condition, repeat}` sequence — never re-derived."""
    from publishable.replication import Repeat, RepeatLevel, RepeatMember
    from publishable.sweep import expand, sweep_document

    conds = expand({"sweep": {"baseline": {"analysis.method": "pearson"},
                              "grid": {"analysis.method": ["spearman"]}}})
    repeats = [Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)]
    levels = [RepeatLevel("seed", (RepeatMember("seed17", 17), RepeatMember("seed42", 42)))]
    execution_order = [(0, "seed17"), (0, "seed42"), (1, "seed17"), (1, "seed42")]
    doc = sweep_document(conds, levels, repeats, "sha256:abc", "as_declared", execution_order)

    assert doc["design_digest"] == "sha256:abc"
    assert doc["conditions"] == [
        {"index": 0, "label": "baseline", "values": {"analysis.method": "pearson"},
         "is_baseline": True},
        {"index": 1, "label": "method=spearman", "values": {"analysis.method": "spearman"},
         "is_baseline": False},
    ]
    assert doc["repeats"] == [{"kind": "seed", "seeds": [17, 42]}]
    assert doc["labels"] == ["seed17", "seed42"]
    assert doc["order"] == "as_declared"
    assert "order_seed" not in doc
    assert doc["execution_order"] == [
        {"condition": 0, "repeat": "seed17"},
        {"condition": 0, "repeat": "seed42"},
        {"condition": 1, "repeat": "seed17"},
        {"condition": 1, "repeat": "seed42"},
    ]


def test_a_randomized_order_records_its_seed():
    """`order_seed` is present only under `order: randomized` — its absence
    under `as_declared` says nothing was shuffled, not that a seed is missing."""
    from publishable.replication import Repeat, RepeatLevel, RepeatMember
    from publishable.sweep import expand, sweep_document

    conds = expand({"sweep": {"grid": {"a.x": [1]}}})
    levels = [RepeatLevel("seed", (RepeatMember("seed01", 1),))]
    doc = sweep_document(conds, levels, [Repeat("seed", "seed01", 1)], "sha256:r",
                         "randomized", [(0, "seed01")], order_seed=4417029)

    assert doc["order"] == "randomized"
    assert doc["order_seed"] == 4417029


def test_the_document_is_plain_yaml_safe_data():
    """It is written with the artifact writer, so it must hold no custom types."""
    import yaml

    from publishable.replication import Repeat, RepeatLevel, RepeatMember
    from publishable.sweep import expand, sweep_document

    doc = sweep_document(expand({"sweep": {"grid": {"a.x": [1]}}}),
                         [RepeatLevel("seed", (RepeatMember("seed01", 1),))],
                         [Repeat("seed", "seed01", 1)], "sha256:d",
                         "as_declared", [(0, "seed01")])
    assert yaml.safe_load(yaml.safe_dump(doc)) == doc


def test_the_document_round_trips_a_float_and_a_boolean_condition_value():
    """The failure mode this artifact cannot afford: a value that serializes
    to something that doesn't parse back, or parses back to a different type.
    Also exercises the new nesting — `repeats`/`labels`/`execution_order` —
    not just the top-level keys."""
    import yaml

    from publishable.replication import Repeat, RepeatLevel, RepeatMember
    from publishable.sweep import expand, sweep_document

    conds = expand({"sweep": {"grid": {"analysis.threshold": [0.5], "analysis.strict": [True]}}})
    repeats = [Repeat("seed", "seed01", 1), Repeat("seed", "seed02", 2)]
    levels = [RepeatLevel("seed", (RepeatMember("seed01", 1), RepeatMember("seed02", 2)))]
    doc = sweep_document(conds, levels, repeats, "sha256:e", "as_declared",
                         [(0, "seed01"), (0, "seed02")])
    round_tripped = yaml.safe_load(yaml.safe_dump(doc))

    assert round_tripped == doc
    values = round_tripped["conditions"][0]["values"]
    assert values["analysis.threshold"] == 0.5
    assert isinstance(values["analysis.threshold"], float)
    assert values["analysis.strict"] is True
    assert isinstance(values["analysis.strict"], bool)

    seeds = round_tripped["repeats"][0]["seeds"]
    assert seeds == [1, 2]
    assert all(isinstance(s, int) for s in seeds)
    assert round_tripped["labels"] == ["seed01", "seed02"]
    assert round_tripped["execution_order"] == [
        {"condition": 0, "repeat": "seed01"},
        {"condition": 0, "repeat": "seed02"},
    ]


def test_the_document_records_one_repeats_entry_per_level():
    """The level structure is what `sweep.yaml` records, not the crossed leaves.

    Handed the leaves, this grouped them by `r.kind` — and every leaf carries the
    *inner* level's kind, so a `batch` × `seed` run recorded no `batch` entry at
    all and a `seeds:` list with each seed repeated once per batch. The level
    survived only inside `labels:`, recoverable only by splitting label strings,
    which is the derived-by-parsing the level model exists to eliminate.
    """
    from publishable.replication import RepeatLevel, RepeatMember, cross_levels
    from publishable.sweep import expand, sweep_document

    levels = [
        RepeatLevel("batch", tuple(RepeatMember(f"batch{i:02d}", 900 + i) for i in (1, 2, 3))),
        RepeatLevel("seed", (RepeatMember("seed17", 17), RepeatMember("seed42", 42))),
    ]
    leaves = cross_levels(levels)
    conds = expand({"sweep": {"grid": {"a.x": [1]}}})
    doc = sweep_document(conds, levels, leaves, "sha256:n", "as_declared",
                         [(0, lf.label) for lf in leaves])

    assert doc["repeats"] == [
        {"kind": "batch", "n": 3},                 # `n` alone — a batch has no parameter
        {"kind": "seed", "seeds": [17, 42]},       # its own two, not one per execution
    ]
    assert doc["labels"] == [
        "batch01_seed17", "batch01_seed42",
        "batch02_seed17", "batch02_seed42",
        "batch03_seed17", "batch03_seed42",
    ]


def test_a_fold_level_records_its_partitions():
    from tests.test_replication import _u, cfg

    from publishable.replication import cross_levels, resolve_repeats
    from publishable.sweep import expand, sweep_document

    levels = resolve_repeats(cfg([{"kind": "fold", "k": 2}]), "d", unit_count=4)
    parts = [[_u("a"), _u("b")], [_u("c"), _u("d")]]
    doc = sweep_document(expand({}), levels, cross_levels(levels), "sha256:x",
                         "as_declared", [], None, partitions=parts)
    assert doc["partitions"] == [
        {"fold": "fold01", "test": ["a", "b"], "train": ["c", "d"]},
        {"fold": "fold02", "test": ["c", "d"], "train": ["a", "b"]},
    ]


def test_no_fold_level_records_no_partitions_key():
    """Absent, not empty — an empty list would read as `no folds were drawn`."""
    from tests.test_replication import cfg

    from publishable.replication import cross_levels, resolve_repeats
    from publishable.sweep import expand, sweep_document

    levels = resolve_repeats(cfg([{"kind": "seed", "n": 2}]), "d")
    doc = sweep_document(expand({}), levels, cross_levels(levels), "sha256:x",
                         "as_declared", [], None)
    assert "partitions" not in doc


def test_partitions_with_no_fold_level_raise_a_coded_error_rather_than_asserting():
    """Core's resolved state disagreeing with itself: partitions were drawn, but
    no `fold` level exists to supply the member labels they pair with.
    Unreachable through `command_run` — `partitions` is built only when a fold
    level was found — but guarded with a `ContractError` rather than an `assert`,
    because an `assert` disappears under `python -O` and this is the only guard
    on the condition (`reference.md` § Errors). Without it the failure is
    `AttributeError` on `None.members`, carrying no code at all."""
    import pytest
    from tests.test_replication import _u, cfg

    from publishable.errors import ContractError
    from publishable.replication import cross_levels, resolve_repeats
    from publishable.sweep import expand, sweep_document

    levels = resolve_repeats(cfg([{"kind": "seed", "n": 2}]), "d")
    with pytest.raises(ContractError) as excinfo:
        sweep_document(expand({}), levels, cross_levels(levels), "sha256:x",
                       "as_declared", [], None, partitions=[[_u("a")], [_u("b")]])
    assert excinfo.value.code == "E-RUN-FOLD-UNRESOLVED"
