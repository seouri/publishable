from publishable.envelope import LEAF_TYPES, check_envelope


def test_a_wrong_typed_scalar_leaf_is_reported() -> None:
    findings = check_envelope({"metadata": {"name": ["a", "b"]}})

    assert [(f[0], f[1]) for f in findings] == [("E-CONFIG-TYPE", "metadata.name")]


def test_a_numeric_string_is_refused_rather_than_coerced() -> None:
    """`n: "5"` is a typo YAML can express, and silent coercion is how
    `limits.max_executions: "5"` skips its budget check today."""
    findings = check_envelope({"limits": {"max_executions": "5"}})

    assert [f[1] for f in findings] == ["limits.max_executions"]


def test_a_well_typed_config_reports_nothing() -> None:
    doc = {
        "schema_version": "1.0",
        "metadata": {"name": "cohort-pilot", "authors": ["a"]},
        "data": {"input_dir": "/in", "output_dir": "/out"},
        "limits": {"max_executions": 15, "max_failed_fraction": 0.1},
    }

    assert check_envelope(doc) == []


def test_the_envelope_declares_nothing_under_parameters() -> None:
    """`parameter_spec` is the single source of truth there. A second authority
    over the same keys is the defaults-file problem."""
    under_parameters = [
        path for path in LEAF_TYPES if path == "parameters" or path.startswith("parameters.")
    ]
    assert not under_parameters


def test_a_parameters_leaf_of_any_type_is_left_alone() -> None:
    assert check_envelope({"parameters": {"analysis": {"method": ["not", "a", "string"]}}}) == []


def test_an_absent_leaf_is_not_a_finding() -> None:
    """An absent key is a missing-key question its own check owns, and a
    `null` is treated as absent, matching the rest of validate."""
    assert check_envelope({"metadata": {}}) == []
    assert check_envelope({"metadata": {"name": None}}) == []


def test_a_bool_is_not_accepted_where_an_int_is_declared() -> None:
    """`bool` is a subclass of `int` in Python, so a naive isinstance passes
    `max_executions: true` — which is not a budget."""
    findings = check_envelope({"limits": {"max_executions": True}})

    assert [f[1] for f in findings] == ["limits.max_executions"]


def test_an_unknown_top_level_key_is_reported() -> None:
    findings = check_envelope({"sweeep": {"grid": {}}})

    assert [(f[0], f[1]) for f in findings] == [("E-CONFIG-KEY-UNKNOWN", "sweeep")]


def test_an_unknown_nested_key_is_reported() -> None:
    findings = check_envelope({"metadata": {"athors": ["x"]}})

    assert [f[1] for f in findings] == ["metadata.athors"]


def test_parameters_is_exempt_from_the_closure() -> None:
    """`parameter_spec` owns that namespace and reports E-PARAM-UNKNOWN with a
    difflib hint. A second authority would double-report and could disagree."""
    assert check_envelope({"parameters": {"anything": {"at": "all"}}}) == []


def test_sweeps_modes_are_exempt_from_the_closure() -> None:
    """`_check_sweep` owns the mode list and reports E-SWEEP-KEY-UNKNOWN."""
    assert check_envelope({"sweep": {"whatever": {}}}) == []


def test_a_non_string_top_level_key_is_reported_not_raised() -> None:
    """A YAML mapping key need not be a string — `1: oops` parses to an `int`
    key. `load_document` only rejects an unhashable key before this runs, so a
    hashable non-string key reaches `check_envelope` directly. It can never
    equal a `LEAF_TYPES` path (all strings), so it is certainly not a key this
    schema declares — reported, not silently skipped."""
    findings = check_envelope({1: "oops"})

    assert [(f[0], f[1]) for f in findings] == [("E-CONFIG-KEY-UNKNOWN", "1")]


def test_a_non_string_nested_key_is_reported_not_raised() -> None:
    findings = check_envelope({"metadata": {1: "oops"}})

    assert [(f[0], f[1]) for f in findings] == [("E-CONFIG-KEY-UNKNOWN", "metadata.1")]


def test_a_misspelled_resample_key_is_reported_rather_than_ignored() -> None:
    """`statistics.resample` is now both a leaf and a container, the same
    arrangement `data.units.measurements` has: typed a mapping by the loop in
    `check_envelope`, and descended into by `_check_unknown_keys`, which checks
    containers before leaves. Without the three child paths the closure stops at
    the leaf and `stratifyy_by` is reached by no check in this build."""
    findings = check_envelope(
        {"statistics": {"resample": {"method": "bootstrap", "n": 2000, "stratifyy_by": ["a"]}}}
    )
    by_code = [(code, path) for code, path, _ in findings]
    assert ("E-CONFIG-KEY-UNKNOWN", "statistics.resample.stratifyy_by") in by_code
    assert any(
        path == "statistics.resample.stratifyy_by" and "stratify_by" in msg
        for code, path, msg in findings
        if code == "E-CONFIG-KEY-UNKNOWN"
    )
    # The positive companion: the three real keys are NOT reported, so the test
    # cannot pass by the closure rejecting everything under the block.
    assert not any(
        path.startswith("statistics.resample.") and path.endswith(("method", "n", "stratify_by"))
        for _, path in by_code
    )


def test_the_three_resample_leaves_are_typed() -> None:
    """A wrong-typed child now gets a REPORTED `E-CONFIG-TYPE` finding instead
    of being silently ignored — this pass never raises and never stops a
    reader downstream from being reached with the still-malformed value, since
    `validate.py` treats a leaf fault as deliberately non-fatal to the pass
    (see e.g. `_check_metadata`'s guard on `metadata.name`). Task 4's
    `_check_resample` still has to guard before it reads `n` for comparison,
    the same way that guard does for `name`."""
    findings = check_envelope(
        {"statistics": {"resample": {"method": 3, "n": "many", "stratify_by": 7}}}
    )
    paths = {path for code, path, _ in findings if code == "E-CONFIG-TYPE"}
    assert paths == {
        "statistics.resample.method",
        "statistics.resample.n",
        "statistics.resample.stratify_by",
    }


def test_a_bare_string_stratify_by_is_accepted_by_the_envelope() -> None:
    """`units.stratum_names` reads a bare `stratify_by: site` as one name, the
    same as `[site]`. Typing this `list` alone would make the two readings
    disagree — `E-CONFIG-TYPE` here while the draw balances on it there."""
    findings = check_envelope({"statistics": {"resample": {"stratify_by": "site"}}})
    assert not [f for f in findings if f[1].startswith("statistics.resample")]
