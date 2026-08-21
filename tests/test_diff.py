"""H8b task 7: `covered_config`'s delta walk over `diff.py`. Task 8 adds
form detection, the per-side header, the four rows and `command_diff`
itself to this same module and this same test file.
"""

from publishable.diff import parameter_deltas

# ---------------------------------------------------------------------------
# Fixture M (task 7 step 4): metadata versus limits, the coverage pin.
# ---------------------------------------------------------------------------


def _m_base() -> dict:
    return {
        "experiment_type": "generic",
        "metadata": {"description": "one"},
        "data": {"input_dir": "/x", "output_dir": "/y", "input_manifest_policy": "hash_all"},
        "parameters": {"analysis": {"method": "pearson"}},
        "limits": {"max_failed_fraction": 0.2},
    }


def test_h8b_fixture_m_arm_one_metadata_only_edit_is_zero_delta_lines():
    """Fixture M arm one: two records differing only in `metadata.description`
    must print zero delta lines — the coverage pin's first half."""
    a = _m_base()
    b = {**a, "metadata": {"description": "a different one entirely"}}
    assert parameter_deltas(a, b) == []


def test_h8b_fixture_m_arm_two_limits_only_edit_is_exactly_one_line():
    """Fixture M arm two: two records differing only in
    `limits.max_failed_fraction` must print exactly one line, naming that
    path and both values — read back from the two configs, not typed."""
    a = _m_base()
    b = {**a, "limits": {"max_failed_fraction": 0.4}}
    lines = parameter_deltas(a, b)
    assert lines == [
        f"  limits.max_failed_fraction  {a['limits']['max_failed_fraction']} → "
        f"{b['limits']['max_failed_fraction']}"
    ]


def test_h8b_fixture_m_arm_three_a_reordered_list_is_one_line_not_indexed():
    """A leaf is anything that is not a `dict` — a list is a leaf, not a
    subtree. Reordering `sweep.grid`'s axis list with the same members must
    print exactly ONE line (the whole list moved), never one per position."""
    a = {
        "experiment_type": "generic",
        "sweep": {"grid": {"analysis.method": ["pearson", "spearman", "kendall"]}},
        "parameters": {},
    }
    b = {
        "experiment_type": "generic",
        "sweep": {"grid": {"analysis.method": ["spearman", "pearson", "kendall"]}},
        "parameters": {},
    }
    lines = parameter_deltas(a, b)
    assert len(lines) == 1
    assert lines[0].startswith("  sweep.grid.analysis.method  ")


def test_h8b_a_leaf_present_on_only_one_side_renders_absent_arrow_value():
    a = {"experiment_type": "generic", "parameters": {}}
    b = {"experiment_type": "generic", "parameters": {}, "statistics": {"contrasts": [{"a": 1}]}}
    lines = parameter_deltas(a, b)
    assert lines == ["  statistics.contrasts  (absent) → [{a: 1}]"]
    # And the reverse direction:
    reverse = parameter_deltas(b, a)
    assert reverse == ["  statistics.contrasts  [{a: 1}] → (absent)"]


def test_h8b_parameter_deltas_are_sorted_by_path():
    a = {"experiment_type": "generic", "parameters": {}}
    b = {
        "experiment_type": "generic",
        "parameters": {"z": {"late": 1}, "a": {"early": 1}},
    }
    lines = parameter_deltas(a, b)
    paths = [line.split()[0] for line in lines]
    assert paths == sorted(paths)
    assert paths == ["parameters.a.early", "parameters.z.late"]
