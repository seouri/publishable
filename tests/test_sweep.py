import pytest

from publishable.sweep import (
    AXIS_MODES,
    NON_AXIS_MODES,
    SWEEP_MODES,
    Condition,
    _axes,
    axis_modes_present,
    expand,
)


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


def test_grid_axes_vary_the_last_declared_axis_fastest() -> None:
    """`itertools.product` varies its last argument fastest, which is the
    declared-order nesting § Expansion modes asks for. The refactor moves this
    loop, so pin the order it produces before moving it."""
    conditions = expand(
        {"sweep": {"grid": {"a.x": [1, 2], "b.y": ["p", "q"]}}}
    )

    assert [dict(c.values) for c in conditions] == [
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


def test_paired_is_one_axis_not_a_product_of_its_keys() -> None:
    """§ Expansion modes' own example: grid × paired = 2 × 2 = 4, not 2 × 2 × 2.
    A paired entry sets several paths at once and counts once."""
    conditions = expand(
        {
            "sweep": {
                "grid": {"analysis.method": ["pearson", "spearman"]},
                "paired": [
                    {"analysis.min_samples": 30, "analysis.confidence": 0.95},
                    {"analysis.min_samples": 50, "analysis.confidence": 0.99},
                ],
            }
        }
    )

    assert len(conditions) == 4
    assert dict(conditions[0].values) == {
        "analysis.method": "pearson",
        "analysis.min_samples": 30,
        "analysis.confidence": 0.95,
    }
    # `_swept_paths` now carries `paired`'s paths alongside `grid`'s, so
    # `label_for` disambiguates all three — none is a shared leaf, so each
    # keeps its shortest suffix.
    assert [c.label for c in conditions] == [
        "method=pearson__min_samples=30__confidence=0.95",
        "method=pearson__min_samples=50__confidence=0.99",
        "method=spearman__min_samples=30__confidence=0.95",
        "method=spearman__min_samples=50__confidence=0.99",
    ]


def test_swept_paths_lists_a_paired_path_once_even_when_every_entry_names_it():
    """Every `paired` entry here names both `min_samples` and `confidence`; a
    naive walk would append each twice, and a duplicate path would make
    `_keys_for` compare a path against itself (trivially "unique") instead of
    against every other swept path."""
    from publishable.sweep import _swept_paths
    paths = _swept_paths(
        {
            "grid": {"analysis.method": ["pearson", "spearman"]},
            "paired": [
                {"analysis.min_samples": 30, "analysis.confidence": 0.95},
                {"analysis.min_samples": 50, "analysis.confidence": 0.99},
            ],
        }
    )
    assert paths == ["analysis.method", "analysis.min_samples", "analysis.confidence"]


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


def test_sample_draws_are_deterministic_given_the_config() -> None:
    """§ Expansion modes: "Sampling is deterministic given its seed", and the
    seed is derived from the design digest — so one config always expands to
    the same conditions, which is what makes `reproduce` regenerate them."""
    config = {
        "sweep": {
            "sample": {
                "n": 8,
                "method": "random",
                "seed": "auto",
                "ranges": {"analysis.confidence": {"uniform": [0.80, 0.99]}},
            }
        }
    }

    first = [dict(c.values) for c in expand(config)]
    second = [dict(c.values) for c in expand(config)]

    assert first == second
    assert len(first) == 8
    assert all(0.80 <= row["analysis.confidence"] <= 0.99 for row in first)


def _sample_config(**sample):
    base = {
        "n": 16,
        "method": "random",
        "seed": "auto",
        "ranges": {"analysis.confidence": {"uniform": [0.80, 0.99]}},
    }
    base.update(sample)
    return {"sweep": {"sample": base}}


@pytest.mark.parametrize("method", ("sobol", "latin_hypercube", "random"))
def test_two_configs_the_digest_can_tell_apart_draw_differently(method) -> None:
    """The discriminating half of determinism. `design_digest` reads `data.units`
    and `sweep.groups`, so two configs differing in `data.units` derive different
    sample seeds and must not draw the same conditions — a constant seed would
    pass the same-config test above while ignoring the config entirely.

    Every method, not just one: an unscrambled `qmc.Sobol` ignores its seed and
    returns the same points for every config, which is exactly this failure
    reached through the sampler rather than through the derivation."""
    one = _sample_config(method=method)
    one["data"] = {"units": {"from": "cohort.csv", "key": "patient_id"}}
    other = _sample_config(method=method)
    other["data"] = {"units": {"from": "other.csv", "key": "patient_id"}}

    assert [dict(c.values) for c in expand(one)] != [dict(c.values) for c in expand(other)]


def test_each_method_draws_its_own_points() -> None:
    """The `method` parameter is not decorative: `sobol`, `latin_hypercube` and
    `random` are three different constructions, and a sampler whose method
    argument does nothing is the silent-no-op class this slice exists to avoid."""
    drawn = {
        method: [dict(c.values) for c in expand(_sample_config(method=method))]
        for method in ("sobol", "latin_hypercube", "random")
    }

    assert drawn["sobol"] != drawn["random"]
    assert drawn["latin_hypercube"] != drawn["random"]
    assert drawn["sobol"] != drawn["latin_hypercube"]
    for rows in drawn.values():
        assert len(rows) == 16
        assert all(0.80 <= row["analysis.confidence"] <= 0.99 for row in rows)


def test_sobol_accepts_an_n_that_is_not_a_power_of_two() -> None:
    """`n` is the condition count — it is billed against `limits.max_executions`
    and printed by `dry-run` — so it is drawn exactly. scipy warns that Sobol's
    balance properties need a power of two; that warning is about the sequence's
    uniformity, not about correctness, and rounding `n` would change the declared
    design and its cost."""
    conditions = expand(_sample_config(method="sobol", n=50))
    assert len(conditions) == 50


def test_uniform_scales_linearly_into_the_declared_interval() -> None:
    rows = [dict(c.values) for c in expand(_sample_config(n=64))]
    values = [row["analysis.confidence"] for row in rows]
    assert all(isinstance(v, float) for v in values)
    assert all(0.80 <= v <= 0.99 for v in values)
    # A linear map of 64 uniform draws fills its interval: both halves are hit,
    # which a mis-scaled map (into [0,1], or into half the interval) would not do.
    assert any(v < 0.895 for v in values) and any(v > 0.895 for v in values)


def test_int_uniform_draws_integers_inclusive_of_both_endpoints() -> None:
    rows = [
        dict(c.values)
        for c in expand(
            _sample_config(n=256, ranges={"analysis.min_samples": {"int_uniform": [10, 12]}})
        )
    ]
    values = [row["analysis.min_samples"] for row in rows]
    assert all(isinstance(v, int) and not isinstance(v, bool) for v in values)
    assert set(values) == {10, 11, 12}


def test_log_uniform_is_uniform_in_the_log_of_the_interval() -> None:
    """Half the draws fall below the geometric mean, not the arithmetic one —
    which is the whole difference between `log_uniform` and `uniform`."""
    import math

    rows = [
        dict(c.values)
        for c in expand(
            _sample_config(n=512, ranges={"learning.rate": {"log_uniform": [0.0001, 1.0]}})
        )
    ]
    values = [row["learning.rate"] for row in rows]
    assert all(0.0001 <= v <= 1.0 for v in values)
    geometric_mean = math.sqrt(0.0001 * 1.0)
    below = sum(1 for v in values if v < geometric_mean)
    assert 0.4 < below / len(values) < 0.6
    arithmetic_mean = (0.0001 + 1.0) / 2
    assert sum(1 for v in values if v < arithmetic_mean) / len(values) > 0.9


def test_a_sample_axis_multiplies_with_grid() -> None:
    """§ Expansion modes: the condition set is the product of every axis-shaped
    mode present — `sample` is one axis of realized draws, not a mode of its own."""
    config = _sample_config(
        n=3,
        ranges={
            "analysis.confidence": {"uniform": [0.80, 0.99]},
            "analysis.min_samples": {"int_uniform": [10, 200]},
        },
    )
    config["sweep"]["grid"] = {"analysis.method": ["pearson", "spearman"]}
    conditions = expand(config)

    # Two sampled paths and `n: 3` is 3 draws, not 3 × 3 points: a draw is one
    # point in the space, so its coordinates are one cell rather than two axes.
    assert len(conditions) == 6
    assert all(
        {"analysis.method", "analysis.confidence", "analysis.min_samples"} == set(c.values)
        for c in conditions
    )
    assert [c.label.split("__")[0] for c in conditions] == [
        "method=pearson", "method=pearson", "method=pearson",
        "method=spearman", "method=spearman", "method=spearman",
    ]


def test_swept_paths_carries_the_sample_ranges() -> None:
    """`label_for` shortens a path against the whole swept set, so a path a mode
    sweeps but `_swept_paths` omits produces a silently ambiguous label."""
    from publishable.sweep import _swept_paths
    paths = _swept_paths(
        {
            "grid": {"analysis.method": ["pearson"]},
            "sample": {"n": 2, "ranges": {"analysis.confidence": {"uniform": [0.8, 0.99]}}},
        }
    )
    assert paths == ["analysis.method", "analysis.confidence"]


def test_the_drawn_values_are_plain_python_scalars() -> None:
    """`sweep.yaml` is written with `yaml.safe_dump`, which refuses a NumPy scalar."""
    import yaml

    rows = [dict(c.values) for c in expand(_sample_config(n=4))]
    assert yaml.safe_load(yaml.safe_dump(rows)) == rows


def test_a_malformed_sample_raises_a_coded_error_rather_than_crashing() -> None:
    """Every fault `expand` can hit inside `sweep.sample` arrives as one
    `ContractError` carrying `E-SWEEP-SAMPLE-INVALID`, never as a bare
    `AttributeError`/`TypeError`/`KeyError` from the drawing code — `validate`
    swallows expansion crashes on the premise that `_check_sweep` reports them."""
    from publishable.errors import ContractError

    malformed = [
        {"ranges": {"a.b": {"uniform": [0, 1]}}},                       # no `n`
        {"n": 0, "ranges": {"a.b": {"uniform": [0, 1]}}},               # n below 1
        {"n": "8", "ranges": {"a.b": {"uniform": [0, 1]}}},             # n not an int
        {"n": True, "ranges": {"a.b": {"uniform": [0, 1]}}},            # a bool is not an n
        {"n": 4},                                                        # no `ranges`
        {"n": 4, "ranges": {}},                                          # empty `ranges`
        {"n": 4, "ranges": []},                                          # ranges not a mapping
        {"n": 4, "ranges": {123: {"uniform": [0, 1]}}},                  # non-string path
        {"n": 4, "ranges": {"a.b": "uniform"}},                          # entry not a mapping
        {"n": 4, "ranges": {"a.b": {}}},                                 # no form
        {"n": 4, "ranges": {"a.b": {"uniform": [0, 1], "int_uniform": [0, 1]}}},  # two forms
        {"n": 4, "ranges": {"a.b": {123: [0, 1]}}},                      # non-string form
        {"n": 4, "ranges": {"a.b": {"gaussian": [0, 1]}}},               # unknown form
        {"n": 4, "ranges": {"a.b": {"uniform": 0.5}}},                   # bounds not a list
        {"n": 4, "ranges": {"a.b": {"uniform": [0, 1, 2]}}},             # three bounds
        {"n": 4, "ranges": {"a.b": {"uniform": ["0", "1"]}}},            # bounds not numbers
        {"n": 4, "ranges": {"a.b": {"uniform": [True, False]}}},         # bools are not bounds
        {"n": 4, "ranges": {"a.b": {"uniform": [1, 0]}}},                # lower above upper
        {"n": 4, "ranges": {"a.b": {"uniform": [1, 1]}}},                # empty interval
        {"n": 4, "ranges": {"a.b": {"log_uniform": [0, 1]}}},            # log of zero
        {"n": 4, "ranges": {"a.b": {"int_uniform": [1.5, 3.5]}}},        # non-integer bounds
        {"n": 4, "method": "gaussian", "ranges": {"a.b": {"uniform": [0, 1]}}},   # method
        {"n": 4, "method": 5, "ranges": {"a.b": {"uniform": [0, 1]}}},   # method not a string
        {"n": 4, "seed": "17", "ranges": {"a.b": {"uniform": [0, 1]}}},  # a seed is auto or an int
        {"n": 4, "seed": True, "ranges": {"a.b": {"uniform": [0, 1]}}},  # a bool is not a seed
        "notamapping",
        ["notamapping"],
    ]
    for sample in malformed:
        with pytest.raises(ContractError) as excinfo:
            expand({"sweep": {"sample": sample}})
        assert excinfo.value.code == "E-SWEEP-SAMPLE-INVALID", sample


def test_a_yaml_date_under_data_units_does_not_crash_expansion() -> None:
    """`design_digest` json-dumps `data.units`, which is arbitrary user YAML: a
    bare date (`enrolled: 2026-08-12`) parses as `datetime.date` and is not JSON
    serializable. `expand` is public and documented to raise `PublishableError`,
    so it converts rather than leaking a `TypeError` from a hashing helper its
    caller never called.

    This is `expand`'s own contract, **not** the user-visible route: `cli`
    computes the same digest at phase 5 before `expand` runs, so on the run path
    that date raises there first — for any config, `sample` or not. That
    pre-existing crash is recorded in `docs/superpowers/spec-defects.md` rather
    than papered over here."""
    import datetime

    from publishable.errors import ContractError

    config = _sample_config()
    config["data"] = {"units": {"from": "cohort.csv", "enrolled": datetime.date(2026, 8, 12)}}
    with pytest.raises(ContractError) as excinfo:
        expand(config)
    assert excinfo.value.code == "E-SWEEP-SAMPLE-INVALID"


def test_the_sample_seed_is_recorded_in_the_sweep_document() -> None:
    """§ "`sweep.yaml` — the resolved plan": a `sample` sweep adds the drawn
    values per condition and the seed they came from. The values are already the
    conditions' own; the seed is the addition, and is absent when nothing drew."""
    from publishable.replication import Repeat, RepeatLevel, RepeatMember
    from publishable.sweep import sample_seed_for, sweep_document

    config = _sample_config(n=2)
    seed = sample_seed_for(config)
    assert isinstance(seed, int)
    assert sample_seed_for({"sweep": {"grid": {"a.x": [1]}}}) is None

    levels = [RepeatLevel("seed", (RepeatMember("seed01", 1),))]
    doc = sweep_document(expand(config), levels, [Repeat("seed", "seed01", 1)], "sha256:d",
                         "as_declared", [(0, "seed01")], sample_seed=seed)
    assert doc["sample_seed"] == seed
    assert [c["values"]["analysis.confidence"] for c in doc["conditions"]] == [
        dict(c.values)["analysis.confidence"] for c in expand(config)
    ]

    without = sweep_document(expand({"sweep": {"grid": {"a.x": [1]}}}), levels,
                             [Repeat("seed", "seed01", 1)], "sha256:d",
                             "as_declared", [(0, "seed01")])
    assert "sample_seed" not in without


def test_a_pinned_integer_seed_overrides_the_derivation() -> None:
    """§ What `auto` derives from: "an omitted `seed` is `auto`, not an error …
    pinning an integer is the deliberate act, and the one to take for anything
    you intend to cite". So two configs the design digest tells apart draw
    identically once both pin the same seed — the pin is what a citation rests
    on, and a derivation that ignored it would move the draws under it."""
    from publishable.sweep import sample_seed_for

    one = _sample_config(seed=7)
    one["data"] = {"units": {"from": "cohort.csv", "key": "patient_id"}}
    other = _sample_config(seed=7)
    other["data"] = {"units": {"from": "other.csv", "key": "patient_id"}}

    assert sample_seed_for(one) == 7
    assert [dict(c.values) for c in expand(one)] == [dict(c.values) for c in expand(other)]
    # And it is a different design from the derived one, which is the half that
    # says the pin was read rather than merely accepted.
    assert [dict(c.values) for c in expand(one)] != [
        dict(c.values) for c in expand(_sample_config())
    ]


def test_ablate_emits_one_baseline_and_one_condition_per_removal() -> None:
    """§ Expansion modes: 1 + n conditions, not 2^n, and the baseline appears
    exactly once — read, not re-emitted."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {
                    "features.demographics": True,
                    "features.labs": True,
                    "features.notes": True,
                },
                "ablate": {
                    "from": "baseline",
                    "remove": ["features.demographics", "features.labs", "features.notes"],
                },
            }
        }
    )

    assert len(conditions) == 4
    assert conditions[0].is_baseline
    assert [c.is_baseline for c in conditions[1:]] == [False, False, False]
    assert dict(conditions[1].values)["features.demographics"] is False
    assert dict(conditions[1].values)["features.labs"] is True


def test_an_ablation_is_labelled_by_its_one_change_not_by_what_it_inherited() -> None:
    """§ Expansion modes labels an ablation `labs=false` (in the `groups` example,
    `01_cohort=derivation__labs=false`) — the change alone. An ablate row carries
    the whole baseline in `values` because it must *run* as the baseline with one
    thing different, but a label restating every inherited value would name the
    condition by what it did not vary, and a label is also a selector."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"features.labs": True, "features.notes": True},
                "ablate": {"from": "baseline", "remove": ["features.labs", "features.notes"]},
            }
        }
    )

    assert [c.label for c in conditions] == ["baseline", "labs=false", "notes=false"]


def test_an_ablated_path_is_disambiguated_against_every_other_ablated_path() -> None:
    """`_keys_for` can only shorten a path unambiguously when it is shown every
    path in the run. `features.notes` and `clinical.notes` share a leaf, so
    ablated paths must reach the labelling set — otherwise both render as
    `notes=false` and two conditions share one label, which is also a selector
    and a directory name."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"features.notes": True, "clinical.notes": True},
                "ablate": {"from": "baseline", "remove": ["features.notes", "clinical.notes"]},
            }
        }
    )

    assert [c.label for c in conditions] == [
        "baseline",
        "features.notes=false",
        "clinical.notes=false",
    ]


def test_ablated_paths_are_not_axis_shaped_paths() -> None:
    """`_swept_paths` is the axis-shaped modes' set, and `_baseline_cells` reads it
    (through `_axes`' cells) to ask which axis a baseline leaves free. `ablate` is
    not an axis and has no cells to expand a baseline over, so its paths are
    carried separately — `expand` and `cli` union the two where labelling and
    scope-readability need the whole set."""
    from publishable.sweep import _swept_paths, ablated_paths

    sweep = {
        "grid": {"analysis.method": ["pearson"]},
        "baseline": {"features.labs": True},
        "ablate": {
            "from": "baseline",
            "remove": ["features.labs"],
            "override": [{"analysis.min_samples": 10}, {"analysis.min_samples": 20}],
        },
    }

    assert _swept_paths(sweep) == ["analysis.method"]
    assert ablated_paths(sweep) == ["features.labs", "analysis.min_samples"]


def test_override_is_the_non_boolean_one_at_a_time_form() -> None:
    """§ Expansion modes: "Use `override` for non-boolean one-at-a-time
    variation". Each entry is one condition, one change from the baseline, and
    the baseline's other values come with it."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson", "analysis.min_samples": 30},
                "ablate": {
                    "override": [
                        {"analysis.method": "spearman"},
                        {"analysis.min_samples": 10},
                    ]
                },
            }
        }
    )

    assert len(conditions) == 3
    assert dict(conditions[1].values) == {
        "analysis.method": "spearman",
        "analysis.min_samples": 30,
    }
    assert dict(conditions[2].values) == {
        "analysis.method": "pearson",
        "analysis.min_samples": 10,
    }
    assert [c.label for c in conditions] == ["baseline", "method=spearman", "min_samples=10"]


def test_remove_sets_false_for_a_boolean_and_null_for_anything_else() -> None:
    """§ Expansion modes: "`remove` sets a boolean parameter to `false` or a
    nullable one to `null`". This module is pure and has no `parameter_spec` to
    consult, so the baseline's own value — the value the ablation is defined
    against — is what says which of the two a path takes."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"features.labs": True, "analysis.cutoff": 0.5},
                "ablate": {"from": "baseline", "remove": ["features.labs", "analysis.cutoff"]},
            }
        }
    )

    assert dict(conditions[1].values)["features.labs"] is False
    assert dict(conditions[2].values)["analysis.cutoff"] is None


def test_ablate_declares_its_conditions_in_the_order_it_writes_them() -> None:
    """`remove` and `override` are read in the order the `ablate` mapping declares
    them, so the condition numbering matches what the user wrote."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"features.labs": True, "analysis.method": "pearson"},
                "ablate": {
                    "override": [{"analysis.method": "spearman"}],
                    "remove": ["features.labs"],
                },
            }
        }
    )

    assert [c.label for c in conditions] == ["baseline", "method=spearman", "labs=false"]


def test_the_mode_vocabulary_is_partitioned_into_axis_and_non_axis() -> None:
    """`SWEEP_MODES` is what `validate` refuses an unrecognised `sweep` key
    against, which makes it the vocabulary's choke point: a seventh mode is
    unusable until it appears there. It appears there only by being classified —
    `SWEEP_MODES` *is* `AXIS_MODES + NON_AXIS_MODES` — so `E-SWEEP-ABLATE-CROSSED`
    cannot be left behind by a mode someone added to `_axes` alone.

    Pinned here against § Expansion modes' literal six, because the derivation
    guarantees the partition and only a document can say which six they are."""
    assert set(AXIS_MODES) | set(NON_AXIS_MODES) == set(SWEEP_MODES)
    assert set(AXIS_MODES).isdisjoint(NON_AXIS_MODES)
    assert set(SWEEP_MODES) == {
        "baseline",
        "grid",
        "paired",
        "ablate",
        "sample",
        "groups",
    }
    declarations = {
        "grid": {"analysis.method": ["pearson", "spearman"]},
        "paired": [{"analysis.method": "pearson"}, {"analysis.method": "spearman"}],
        "sample": {
            "n": 2,
            "seed": 7,
            "ranges": {"analysis.confidence": {"uniform": [0.9, 0.99]}},
        },
    }
    # And the classification is the true one: every axis mode really does
    # contribute an axis to the product, and no non-axis mode does.
    assert set(AXIS_MODES) == set(declarations)
    for mode, declaration in declarations.items():
        sweep = {mode: declaration}
        assert _axes(sweep, sample_seed=7), mode
        assert axis_modes_present(sweep) == [mode]
    for mode in NON_AXIS_MODES:
        assert not _axes({mode: {"analysis.method": "pearson"}}, sample_seed=7)
        assert axis_modes_present({mode: {"analysis.method": "pearson"}}) == []


def test_a_baseline_fixing_some_axes_expands_over_the_rest() -> None:
    """§ Expansion modes' second row: a baseline that fixes `analysis.method`
    and leaves `data.sex` free gives one baseline per level of `sex`, each
    carrying its own cell as well as the fixed value. The rule underneath is
    that the baseline expands over whichever axes it doesn't fix."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {
                    "analysis.method": ["pearson", "spearman"],
                    "data.sex": ["f", "m"],
                },
            }
        }
    )

    baselines = [c for c in conditions if c.is_baseline]
    assert len(baselines) == 2
    assert {dict(c.values)["data.sex"] for c in baselines} == {"f", "m"}
    assert all(dict(c.values)["analysis.method"] == "pearson" for c in baselines)
    # The rest of the run is the product, unchanged and following them.
    assert [c.index for c in conditions] == list(range(6))
    assert [c.is_baseline for c in conditions] == [True, True, False, False, False, False]


def test_a_per_cell_baseline_label_carries_its_cell() -> None:
    """§ Expansion modes shows `00_cohort=derivation__baseline` — the cell, then
    the literal. A label is a directory name and a selector, so two baselines
    that differ only in their cell must not both be `baseline`."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {
                    "analysis.method": ["pearson", "spearman"],
                    "data.sex": ["f", "m"],
                },
            }
        }
    )

    assert [c.label for c in conditions] == [
        "sex=f__baseline",
        "sex=m__baseline",
        "method=pearson__sex=f",
        "method=pearson__sex=m",
        "method=spearman__sex=f",
        "method=spearman__sex=m",
    ]
    assert len({c.label for c in conditions}) == len(conditions)


def test_a_baseline_fixing_every_axis_is_still_one_condition_labelled_baseline() -> None:
    """The table's first row, pinned against the second: nothing expands, the
    label gains no cell, and the baseline is condition `00`."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson", "data.sex": "f"},
                "grid": {"analysis.method": ["pearson", "spearman"], "data.sex": ["f", "m"]},
            }
        }
    )

    assert [c.is_baseline for c in conditions] == [True, False, False, False, False]
    assert conditions[0].index == 0
    assert conditions[0].label == "baseline"
    assert dict(conditions[0].values) == {"analysis.method": "pearson", "data.sex": "f"}


def test_a_baseline_expands_over_an_unfixed_paired_axis_as_one_cell() -> None:
    """A `paired` entry is one cell that sets several paths, so a baseline that
    fixes none of them expands over the entries — not over their keys crossed."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["pearson", "spearman"]},
                "paired": [
                    {"analysis.min_samples": 30, "analysis.confidence": 0.95},
                    {"analysis.min_samples": 50, "analysis.confidence": 0.99},
                ],
            }
        }
    )

    baselines = [c for c in conditions if c.is_baseline]
    assert [c.label for c in baselines] == [
        "min_samples=30__confidence=0.95__baseline",
        "min_samples=50__confidence=0.99__baseline",
    ]
    assert [dict(c.values) for c in baselines] == [
        {"analysis.min_samples": 30, "analysis.confidence": 0.95, "analysis.method": "pearson"},
        {"analysis.min_samples": 50, "analysis.confidence": 0.99, "analysis.method": "pearson"},
    ]


def test_a_baseline_naming_one_path_of_a_paired_entry_fixes_that_whole_axis() -> None:
    """An axis counts as fixed when the baseline names *any* path it varies.
    Expanding a half-fixed `paired` axis would have to discard either the
    baseline's declared `min_samples` or the cell's, so the declaration wins and
    the axis contributes no cells for the baseline to expand over.

    **This shape is open, not settled**, and the assertion below records what
    ships rather than what is wanted: the baseline row carries `min_samples` and
    lets `analysis.confidence` fall to the *base config's* value, which may be
    neither declared cell's — a `paired` combination the axis never produces, and
    `validate` reports nothing about it (verified: zero findings). It was
    unreachable until H2 task 7 retired `E-SWEEP-BASELINE-PARTIAL`, and it is
    left unrefused because refusing it needs a baseline resolved against actual
    cells. **Owner: the `groups` slice**, with the per-cell numbering question it
    shares that machinery with. See `docs/superpowers/spec-defects.md`, "Three
    baseline shapes per-cell expansion makes reachable"."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"analysis.min_samples": 30},
                "paired": [
                    {"analysis.min_samples": 30, "analysis.confidence": 0.95},
                    {"analysis.min_samples": 50, "analysis.confidence": 0.99},
                ],
            }
        }
    )

    baselines = [c for c in conditions if c.is_baseline]
    assert len(baselines) == 1
    assert baselines[0].label == "baseline"
    assert dict(baselines[0].values) == {"analysis.min_samples": 30}


def test_a_baseline_fixing_no_swept_path_expands_over_every_axis() -> None:
    """A truthy baseline naming only paths no axis sweeps leaves *every* axis
    unfixed, so it expands over all of them: a four-cell grid becomes four
    baselines beside four product rows.

    Pinned as the behaviour that ships rather than the behaviour that is wanted.
    It follows from the rule § Expansion modes states without a caveat — the
    baseline expands over whichever axes it doesn't fix — and the shape is a
    legitimate one when the fixed path is a real reference setting (a per-cell
    arm at `drop_missing: false`). It is degenerate when the fixed value equals
    the base config's own, which the second assertion below is: every baseline
    row then resolves to the same parameters as the product row in its cell, so
    the run pays twice for one answer and the correction family doubles.
    Recorded under `docs/superpowers/spec-defects.md`, "Three baseline shapes
    per-cell expansion makes reachable", not refused here — refusing it would
    also refuse the non-degenerate reading."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"analysis.drop_missing": True},
                "grid": {
                    "analysis.method": ["pearson", "spearman"],
                    "data.sex": ["f", "m"],
                },
            }
        }
    )

    assert [c.is_baseline for c in conditions] == [True] * 4 + [False] * 4
    # Cell for cell, the baseline row differs from its product row in the one
    # path the baseline names — and in nothing else.
    for baseline, product in zip(conditions[:4], conditions[4:], strict=True):
        assert dict(baseline.values) == dict(product.values) | {"analysis.drop_missing": True}


def test_an_empty_axis_leaves_no_conditions_even_under_a_baseline() -> None:
    """An axis with no cells carries no paths, so nothing can fix it and the
    product over it is empty — for the baseline's rows exactly as for the
    product's. `expand` returns nothing rather than a lone baseline row standing
    in for a design with no cells; `E-SWEEP-AXIS-EMPTY` is the refusal."""
    assert expand({"sweep": {"baseline": {"a.x": 1}, "grid": {"a.x": []}}}) == []
    assert expand({"sweep": {"baseline": {"b.y": 1}, "grid": {"a.x": []}}}) == []
