# tests/test_artifacts.py
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from publishable import ArtifactError, ArtifactExistsError, ContractError
from publishable.artifacts import StepIO, allocation_hash, build_allocation_document, write_atomic
from publishable.units import Unit, UnitList, assignment_for


def _u(key: str) -> Unit:
    return Unit(key=key)


@pytest.fixture
def io(tmp_path: Path) -> StepIO:
    step_dir = tmp_path / "run" / "shared" / "step01"
    step_dir.mkdir(parents=True)
    (tmp_path / "input").mkdir()
    return StepIO(step_dir=step_dir, input_dir=tmp_path / "input", run_dir=tmp_path / "run")


def make_io(
    tmp_path: Path,
    *,
    scope: str = "repeat",
    units: "UnitList | None" = None,
    conditions: list[tuple[int, str]] | None = None,
    repeats: list[str] | None = None,
    step_scopes: dict[str, str] | None = None,
    condition_index: int | None = None,
    condition_label: str | None = None,
    repeat_label: str | None = None,
) -> StepIO:
    step_dir = tmp_path / "run" / "step"
    step_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "input").mkdir(exist_ok=True)
    return StepIO(
        step_dir=step_dir,
        input_dir=tmp_path / "input",
        run_dir=tmp_path / "run",
        units=units,
        scope=scope,
        conditions=conditions,
        repeats=repeats,
        step_scopes=step_scopes,
        condition_index=condition_index,
        condition_label=condition_label,
        repeat_label=repeat_label,
    )


def test_write_dispatches_on_the_longest_registered_suffix(io: StepIO):
    io.write("a.json", {"x": 1})
    io.write("b.yaml", {"y": 2})
    io.write("c.jsonl", [{"i": 1}, {"i": 2}])
    io.write("d.csv", [{"k": "p1", "v": 1}])
    assert (io.step_dir / "a.json").read_text().strip() == '{"x": 1}'
    assert "y: 2" in (io.step_dir / "b.yaml").read_text()
    assert (io.step_dir / "c.jsonl").read_text().count("\n") == 2
    assert "k,v" in (io.step_dir / "d.csv").read_text()


def test_an_unregistered_extension_takes_bytes_or_str_verbatim(io: StepIO):
    io.write("model.pkl", b"\x80\x04")
    assert (io.step_dir / "model.pkl").read_bytes() == b"\x80\x04"
    with pytest.raises(ArtifactError) as e:
        io.write("model2.pkl", {"not": "bytes"})
    assert e.value.code == "E-ARTIFACT-UNWRITABLE"


def test_nothing_is_ever_overwritten(io: StepIO):
    io.write("a.json", {"x": 1})
    with pytest.raises(ArtifactExistsError) as e:
        io.write("a.json", {"x": 2})
    assert e.value.code == "E-ARTIFACT-EXISTS"
    assert io.exists("a.json")


def test_path_is_existence_checked_in_the_write_direction(io: StepIO):
    assert io.path("fig.png").parent.exists()
    io.write("fig.png", b"\x89PNG")
    with pytest.raises(ArtifactExistsError):
        io.path("fig.png")


def test_a_name_is_a_relative_path_and_intermediate_dirs_are_created(io: StepIO):
    io.write("figures/roc.png", b"\x89PNG")
    assert (io.step_dir / "figures" / "roc.png").is_file()


def test_escaping_the_step_directory_is_rejected(io: StepIO):
    for bad in ("/etc/passwd", "../escape.json", "figures/../../escape.json"):
        with pytest.raises(ArtifactError) as e:
            io.write(bad, {"x": 1})
        assert e.value.code == "E-ARTIFACT-NAME"


def test_a_symlink_leading_outside_the_step_directory_is_rejected(io: StepIO, tmp_path: Path):
    outside = tmp_path / "outside"
    outside.mkdir()
    link = io.step_dir / "escape_dir"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ArtifactError) as e:
        io.write("escape_dir/leak.json", {"x": 1})
    assert e.value.code == "E-ARTIFACT-NAME"
    assert not (outside / "leak.json").exists()


def test_the_last_path_component_alone_decides_the_extension(io: StepIO):
    # The dot inside "gpt-4.1" must not be mistaken for the extension separator.
    io.write("programs/gpt-4.1__seed29.json", {"x": 1})
    assert (io.step_dir / "programs" / "gpt-4.1__seed29.json").read_text().strip() == '{"x": 1}'


def test_compound_extension_dispatches_on_the_longer_registered_suffix(io: StepIO, tmp_path):
    from publishable.artifacts import READERS, WRITERS

    WRITERS[".fastq.gz"] = lambda obj: obj if isinstance(obj, bytes) else obj.encode()
    READERS[".fastq.gz"] = lambda data: data
    try:
        target = io.write("reads.fastq.gz", b"seqdata")
        assert target.name == "reads.fastq.gz"
        assert target.read_bytes() == b"seqdata"

        # The write side and the read side must agree on the longest-suffix rule.
        (io.step_dir / "upstream.fastq.gz").write_bytes(b"more seqdata")
        assert io.read_upstream("step01", "upstream.fastq.gz") == b"more seqdata"
    finally:
        del WRITERS[".fastq.gz"]
        del READERS[".fastq.gz"]


def test_encode_csv_with_differing_keys_and_empty_rows():
    from publishable.artifacts import _encode_csv

    out = _encode_csv([{"a": 1, "b": 2}, {"a": 3, "c": 4}])
    text = out.decode()
    header = text.splitlines()[0]
    assert header == "a,b,c"

    empty = _encode_csv([])
    assert empty.decode().strip() == ""


def test_append_is_jsonl_only(io: StepIO):
    io.append("log.jsonl", {"event": "start"})
    io.append("log.jsonl", {"event": "stop"})
    assert (io.step_dir / "log.jsonl").read_text().count("\n") == 2
    with pytest.raises(ArtifactError) as e:
        io.append("log.txt", {"event": "x"})
    assert e.value.code == "E-ARTIFACT-APPEND"


def test_a_crash_mid_write_leaves_nothing(tmp_path: Path, monkeypatch):
    """The rename is the only moment the target appears. Break it and nothing lands.

    Note the failure is injected INSIDE write_atomic — passing an expression that
    raises would be evaluated before the call and would test nothing.
    """
    target = tmp_path / "out.bin"

    def boom(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("publishable.artifacts.os.replace", boom)
    with pytest.raises(OSError):
        write_atomic(target, b"real bytes that never land")
    assert not target.exists()
    assert list(tmp_path.iterdir()) == [], "no .partial- temp file may survive either"


def test_write_of_an_unwritable_object_leaves_nothing_behind(io: StepIO):
    with pytest.raises(ArtifactError):
        io.write("bad.pkl", object())
    assert not io.exists("bad.pkl")
    assert list(io.step_dir.iterdir()) == []


def test_read_input_reaches_the_input_dir_read_only(io: StepIO, tmp_path: Path):
    (tmp_path / "input" / "index.csv").write_text("patient_id\np1\n")
    rows = io.read_input("index.csv")
    assert rows == [{"patient_id": "p1"}]


@pytest.mark.parametrize(
    ("name", "written", "expected"),
    [
        ("out.json", {"x": 1, "y": [1, 2]}, {"x": 1, "y": [1, 2]}),
        ("out.yaml", {"x": 1, "y": [1, 2]}, {"x": 1, "y": [1, 2]}),
        ("out.jsonl", [{"i": 1}, {"i": 2}], [{"i": 1}, {"i": 2}]),
        ("out.csv", [{"k": "p1", "v": "1"}], [{"k": "p1", "v": "1"}]),
    ],
)
def test_read_upstream_inverts_what_write_wrote_for_every_registered_extension(
    io: StepIO, name: object, written: object, expected: object
):
    io.write(str(name), written)
    assert io.read_upstream("step01", str(name)) == expected


def test_read_upstream_of_an_unregistered_extension_round_trips_as_bytes(io: StepIO):
    io.write("model.pkl", b"\x80\x04binarydata")
    assert io.read_upstream("step01", "model.pkl") == b"\x80\x04binarydata"


def test_units_raises_when_no_roster_was_declared(io: StepIO):
    with pytest.raises(ContractError) as e:
        _ = io.units
    assert e.value.code == "E-STEP-UNITS-UNAVAILABLE"


def test_a_repeat_step_sees_only_its_folds_test_partition(tmp_path):
    io = make_io(
        tmp_path,
        scope="repeat",
        units=UnitList([_u("u1")], train=UnitList([_u("u2"), _u("u3")])),
    )
    assert [u.key for u in io.units] == ["u1"]
    assert [u.key for u in io.units.train] == ["u2", "u3"]


def test_units_raises_at_condition_scope_under_a_fold(tmp_path):
    io = make_io(tmp_path, scope="condition", units=None)
    with pytest.raises(ContractError) as exc:
        _ = io.units
    assert exc.value.code == "E-STEP-UNITS-UNAVAILABLE"


def test_train_raises_at_run_scope_under_a_fold(tmp_path):
    io = make_io(tmp_path, scope="run", units=None)
    with pytest.raises(ContractError) as exc:
        _ = io.units.train
    assert exc.value.code == "E-STEP-UNITS-UNAVAILABLE"


def test_there_is_no_train_of_a_train(tmp_path):
    io = make_io(
        tmp_path,
        scope="repeat",
        units=UnitList([_u("u1")], train=UnitList([_u("u2")])),
    )
    with pytest.raises(ContractError):
        _ = io.units.train.train


def test_record_and_skip_accumulate_by_key(tmp_path: Path):
    from publishable.units import Unit, UnitList

    roster = UnitList([Unit(key=f"p{i}") for i in range(3)])
    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run", units=roster)
    assert len(io.units) == 3
    io.record("p0", {"pred": 0.5, "truth": 1})
    io.skip("p1", "no baseline visit")
    assert io.recorded_keys == {"p0"}
    assert io.skipped == {"p1": "no baseline visit"}


def test_a_second_record_under_one_key_is_discarded_first_write_wins(tmp_path: Path):
    from publishable.units import Unit, UnitList

    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        units=UnitList([Unit(key="p0")]),
    )
    io.record("p0", {"v": 1})
    io.record("p0", {"v": 2})
    assert io.rows() == [{"unit": "p0", "v": 1}]


def test_recording_a_key_not_in_the_roster_is_refused(tmp_path: Path):
    from publishable.units import Unit, UnitList

    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        units=UnitList([Unit(key="p0")]),
    )
    with pytest.raises(ContractError) as e:
        io.record("ghost", {"v": 1})
    assert e.value.code == "E-STEP-UNIT-UNKNOWN"


def test_a_unit_cannot_be_both_recorded_and_skipped(tmp_path: Path):
    from publishable.units import Unit, UnitList

    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        units=UnitList([Unit(key="p0")]),
    )
    io.record("p0", {"v": 1})
    with pytest.raises(ContractError) as e:
        io.skip("p0", "changed my mind")
    assert e.value.code == "E-STEP-UNIT-SETTLED"


def test_recording_a_column_named_unit_is_a_key_collision(tmp_path: Path):
    from publishable.units import Unit, UnitList

    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        units=UnitList([Unit(key="p0")]),
    )
    with pytest.raises(ContractError) as e:
        io.record("p0", {"unit": "IMPOSTER"})
    assert e.value.code == "E-STEP-KEY-COLLISION"
    assert "unit" in str(e.value)


def test_recording_a_column_matching_a_declared_attribute_is_a_key_collision(
    tmp_path: Path,
):
    from publishable.units import Unit, UnitList

    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    roster = UnitList([Unit(key="p0", attributes={"site": "A"})])
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run", units=roster)
    with pytest.raises(ContractError) as e:
        io.record("p0", {"site": "x"})
    assert e.value.code == "E-STEP-KEY-COLLISION"
    assert "site" in str(e.value)
    io.record("p0", {"pred": 1})
    assert io.rows() == [{"unit": "p0", "pred": 1}]


def test_two_measurements_of_one_unit_are_both_kept(tmp_path: Path):
    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        measurements={"by": "read_id", "collapse": "mean"},
    )
    io.record("p1", {"score": 10}, measurement="r1")
    io.record("p1", {"score": 20}, measurement="r2")
    assert io.measurement_rows() == [
        {"unit": "p1", "measurement": "r1", "score": 10},
        {"unit": "p1", "measurement": "r2", "score": 20},
    ]


def test_two_records_without_a_measurement_are_first_write_wins(tmp_path: Path):
    """The retry path, unchanged. This is the behaviour `measurement=` exists
    to be distinguishable from."""
    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        measurements={"by": "read_id", "collapse": "mean"},
    )
    io.record("p1", {"score": 10})
    io.record("p1", {"score": 20})
    assert io.rows() == [{"unit": "p1", "score": 10}]
    assert io.measurement_rows() == []


def test_a_measurement_without_the_declaration_raises(tmp_path: Path):
    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run")
    with pytest.raises(ContractError) as e:
        io.record("p1", {"score": 10}, measurement="r1")
    assert e.value.code == "E-STEP-MEASUREMENT-UNDECLARED"


def test_a_record_without_a_measurement_is_untouched_by_the_undeclared_check(
    tmp_path: Path,
):
    """Control for the previous test: an undeclared `data.units.measurements`
    must not block the ordinary, non-`measurement=` path — only the raise
    itself is new behaviour."""
    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run")
    io.record("p1", {"score": 10})
    assert io.rows() == [{"unit": "p1", "score": 10}]


def test_a_resumed_measurement_is_idempotent_first_write_wins(tmp_path: Path):
    """The declaration's other half: a resumed *measurement* deduplicates by
    `(unit, measurement)` exactly as a resumed plain record deduplicates by
    unit — same rule, different key."""
    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        measurements={"by": "read_id", "collapse": "mean"},
    )
    io.record("p1", {"score": 10}, measurement="r1")
    io.record("p1", {"score": 99}, measurement="r1")
    assert io.measurement_rows() == [{"unit": "p1", "measurement": "r1", "score": 10}]


def test_a_measurement_row_may_not_name_a_column_unit_or_measurement(tmp_path: Path):
    """`unit` and `measurement` are the measurement row's own structural columns —
    reserved for the same reason `record`'s plain path already reserves `unit`."""
    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        measurements={"by": "read_id", "collapse": "mean"},
    )
    with pytest.raises(ContractError) as e:
        io.record("p1", {"unit": "IMPOSTER"}, measurement="r1")
    assert e.value.code == "E-STEP-KEY-COLLISION"
    with pytest.raises(ContractError) as e:
        io.record("p1", {"measurement": "IMPOSTER"}, measurement="r1")
    assert e.value.code == "E-STEP-KEY-COLLISION"


def test_measuring_a_key_not_in_the_roster_is_refused(tmp_path: Path):
    """Control: the plain path already refuses this (`E-STEP-UNIT-UNKNOWN`); the
    measurement path must not bypass the roster just because it skips the rest
    of `_settle`."""
    from publishable.units import Unit, UnitList

    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        units=UnitList([Unit(key="p0")]),
        measurements={"by": "read_id", "collapse": "mean"},
    )
    with pytest.raises(ContractError) as e:
        io.record("ghost", {"score": 1}, measurement="r1")
    assert e.value.code == "E-STEP-UNIT-UNKNOWN"


def test_measuring_a_skipped_unit_is_settled(tmp_path: Path):
    """A `skip`ped unit is ineligible by design; a later measurement re-entering
    it as a completed result is exactly the accounting failure `ineligible`
    exists to prevent, so this must raise even though a second measurement of
    an *unskipped* unit (the next test) must not."""
    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        measurements={"by": "read_id", "collapse": "mean"},
    )
    io.skip("p1", "no baseline visit")
    with pytest.raises(ContractError) as e:
        io.record("p1", {"score": 10}, measurement="r1")
    assert e.value.code == "E-STEP-UNIT-SETTLED"
    assert io.measurement_rows() == []


def test_a_second_measurement_of_an_unskipped_unit_is_not_settled(tmp_path: Path):
    """Control for the previous test: a unit that was neither skipped nor
    plain-recorded must still accept a second, *different* measurement — the
    whole point of `measurement=`."""
    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        measurements={"by": "read_id", "collapse": "mean"},
    )
    io.record("p1", {"score": 10}, measurement="r1")
    io.record("p1", {"score": 20}, measurement="r2")
    assert len(io.measurement_rows()) == 2


def test_skipping_a_measured_unit_is_settled(tmp_path: Path):
    """The mirror of `test_measuring_a_skipped_unit_is_settled`: a unit already
    carrying a measurement row must not then be skipped, or it would be counted
    `ineligible` and produce a result once task 5 collapses it — the same rule,
    the other call order."""
    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        measurements={"by": "read_id", "collapse": "mean"},
    )
    io.record("p1", {"score": 1}, measurement="r1")
    with pytest.raises(ContractError) as e:
        io.skip("p1", "reason")
    assert e.value.code == "E-STEP-UNIT-SETTLED"
    assert io.skipped == {}


def test_skipping_an_unmeasured_unit_still_succeeds(tmp_path: Path):
    """Control for the previous test: a unit that was never measured must still
    be skippable — the new check must not block the ordinary case."""
    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        measurements={"by": "read_id", "collapse": "mean"},
    )
    io.skip("p1", "reason")
    assert io.skipped == {"p1": "reason"}


def test_a_measurement_column_matching_a_declared_attribute_is_a_key_collision(
    tmp_path: Path,
):
    """Control: the plain path already refuses this for `site`; the measurement
    path must refuse it identically rather than folding a shadowed attribute
    into a row task 5 will later merge against the same unit's `site`."""
    from publishable.units import Unit, UnitList

    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    roster = UnitList([Unit(key="p0", attributes={"site": "A"})])
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        units=roster,
        measurements={"by": "read_id", "collapse": "mean"},
    )
    with pytest.raises(ContractError) as e:
        io.record("p0", {"site": "x"}, measurement="r1")
    assert e.value.code == "E-STEP-KEY-COLLISION"
    assert "site" in str(e.value)
    io.record("p0", {"score": 1}, measurement="r1")
    assert io.measurement_rows() == [{"unit": "p0", "measurement": "r1", "score": 1}]


def _measuring_io(tmp_path: Path, collapse: Any = "mean", **kwargs: Any) -> StepIO:
    """A `StepIO` whose `data.units.measurements` is declared, for the collapse tests."""
    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True, exist_ok=True)
    (tmp_path / "in").mkdir(exist_ok=True)
    return StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        measurements={"by": "read_id", "collapse": collapse},
        **kwargs,
    )


def _read_parquet(path: Path) -> Any:
    from publishable.artifacts import _decode_parquet

    return _decode_parquet(path.read_bytes())


def test_measurement_rows_collapse_into_one_unit_row(tmp_path: Path):
    """Three asymmetric values, so `mean` and `median` cannot agree by accident —
    a two-row 10/20 case collapses to 15.0 under either rule and would report a
    pass for a collapse that ignored the declared rule entirely."""
    io = _measuring_io(tmp_path)
    io.record("p1", {"score": 10}, measurement="r1")
    io.record("p1", {"score": 20}, measurement="r2")
    io.record("p1", {"score": 60}, measurement="r3")
    io.finalize()
    assert _read_parquet(io.step_dir / "units.parquet") == [{"unit": "p1", "score": 30.0}]


def test_a_measured_only_unit_is_completed_not_failed(tmp_path: Path):
    """The central obligation: `completed` is "how many distinct unit keys reached
    `io.record`" (`reference.md` § The unit table is the inference base), and the
    runner derives `failed` by subtraction — so a measured unit missing from
    `recorded_keys` is silently counted as a failure."""
    io = _measuring_io(tmp_path)
    io.record("p1", {"score": 10}, measurement="r1")
    io.record("p1", {"score": 20}, measurement="r2")
    io.record("p2", {"score": 5})  # the control: the plain path, already counted
    io.finalize()
    assert io.recorded_keys == {"p1", "p2"}


def test_measurements_parquet_holds_the_uncollapsed_rows(tmp_path: Path):
    io = _measuring_io(tmp_path)
    io.record("p1", {"score": 10}, measurement="r1")
    io.record("p1", {"score": 20}, measurement="r2")
    io.finalize()
    assert _read_parquet(io.step_dir / "measurements.parquet") == [
        {"unit": "p1", "measurement": "r1", "score": 10},
        {"unit": "p1", "measurement": "r2", "score": 20},
    ]


def test_no_measurements_parquet_when_no_step_measured(tmp_path: Path):
    """Decision 5: the file holds what the run measured, not what the input carried.
    The declaration is present here — an input-path run carries it in every
    execution — so guarding the write on the declaration rather than on the rows
    would produce the file for every such run."""
    io = _measuring_io(tmp_path)
    io.record("p1", {"score": 10})
    io.finalize()
    assert not (io.step_dir / "measurements.parquet").exists()
    assert _read_parquet(io.step_dir / "units.parquet") == [{"unit": "p1", "score": 10}]


def test_a_numeric_rule_coerces_a_recorded_string_before_applying(tmp_path: Path):
    """`coerce_scalars` guarantees a scalar, not a number: a step recording `"10"`
    reaches the collapse as a `str`, where `mean` would return the string `"10"`
    through `apply_rule`'s constant-column shortcut. `coerce_for_rule` is what closes
    it, the same call the input path makes."""
    io = _measuring_io(tmp_path)
    io.record("p1", {"score": "10"}, measurement="r1")
    io.record("p1", {"score": "20"}, measurement="r2")
    io.finalize()
    assert _read_parquet(io.step_dir / "units.parquet") == [{"unit": "p1", "score": 15.0}]


def test_measurement_rows_need_not_agree_on_columns(tmp_path: Path):
    """`reference.md` § The per-unit tables: a column absent from a row reads as
    null. A per-column rule is used so the two columns cannot pass by sharing one."""
    io = _measuring_io(tmp_path, collapse={"score": "mean", "note": "first"})
    io.record("p1", {"score": 10}, measurement="r1")
    io.record("p1", {"score": 20, "note": "late"}, measurement="r2")
    io.finalize()
    assert _read_parquet(io.step_dir / "units.parquet") == [
        {"unit": "p1", "score": 15.0, "note": "late"}
    ]
    assert _read_parquet(io.step_dir / "measurements.parquet") == [
        {"unit": "p1", "measurement": "r1", "score": 10, "note": None},
        {"unit": "p1", "measurement": "r2", "score": 20, "note": "late"},
    ]


def test_an_unnamed_column_falls_back_to_first(tmp_path: Path):
    """`rule_for`'s documented fallback, reached through the step path: a column
    the map does not name carries its first value rather than a guessed statistic."""
    io = _measuring_io(tmp_path, collapse={"score": "mean"})
    io.record("p1", {"score": 10, "site": "A"}, measurement="r1")
    io.record("p1", {"score": 20, "site": "B"}, measurement="r2")
    io.finalize()
    assert _read_parquet(io.step_dir / "units.parquet") == [
        {"unit": "p1", "score": 15.0, "site": "A"}
    ]


def test_a_collapsed_unit_row_carries_its_declared_attributes(tmp_path: Path):
    """Collapsing into `_rows` rather than into a parallel table is what gets the
    declared-attribute merge `units.parquet` already does — for free and by the
    same code, so the two kinds of unit row cannot come to differ in shape."""
    roster = UnitList([Unit(key="p1", attributes={"site": "A"})])
    io = _measuring_io(tmp_path, units=roster)
    io.record("p1", {"score": 10}, measurement="r1")
    io.record("p1", {"score": 20}, measurement="r2")
    io.finalize()
    assert _read_parquet(io.step_dir / "units.parquet") == [
        {"unit": "p1", "site": "A", "score": 15.0}
    ]


def test_measuring_a_plain_recorded_unit_is_settled(tmp_path: Path):
    """A unit may arrive by one path or the other, never both. Defining a winner
    instead would make the declared `collapse` rule apply or not depending on the
    order two calls happened to be made in, inside one step."""
    io = _measuring_io(tmp_path)
    io.record("p1", {"score": 1})
    with pytest.raises(ContractError) as e:
        io.record("p1", {"score": 2}, measurement="r1")
    assert e.value.code == "E-STEP-UNIT-SETTLED"
    assert io.measurement_rows() == []


def test_plain_recording_a_measured_unit_is_settled(tmp_path: Path):
    """The same rule, the other call order — and the one that cannot be reached
    through `_rows` first-write-wins, since a measured unit is not in `_rows` yet."""
    io = _measuring_io(tmp_path)
    io.record("p1", {"score": 1}, measurement="r1")
    with pytest.raises(ContractError) as e:
        io.record("p1", {"score": 2})
    assert e.value.code == "E-STEP-UNIT-SETTLED"
    assert io.rows() == []


def test_a_different_unit_may_be_plain_recorded_alongside_a_measured_one(
    tmp_path: Path,
):
    """Control for the two above: the refusal is per unit, not a ban on a step
    that both measures and records.

    A collapsed unit lands after every plain one whatever order the step recorded
    them in, because the collapse runs at `finalize`. No document pins
    `units.parquet`'s row order, and every reader keys by unit — but it is
    behaviour, so it is asserted rather than left to be discovered.
    """
    io = _measuring_io(tmp_path)
    io.record("p1", {"score": 1}, measurement="r1")
    io.record("p2", {"score": 2})
    io.finalize()
    assert _read_parquet(io.step_dir / "units.parquet") == [
        {"unit": "p2", "score": 2.0},
        {"unit": "p1", "score": 1.0},
    ]


def test_recorded_keys_skipped_and_rows_are_not_live_handles(tmp_path: Path):
    from publishable.units import Unit, UnitList

    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        units=UnitList([Unit(key="p0"), Unit(key="p1")]),
    )
    io.record("p0", {"v": 1})
    io.skip("p1", "n/a")

    keys = io.recorded_keys
    keys.add("ghost")
    assert io.recorded_keys == {"p0"}

    skipped = io.skipped
    skipped["x"] = "hack"
    assert io.skipped == {"p1": "n/a"}

    rows = io.rows()
    rows.append({"unit": "ghost", "v": 99})
    assert io.rows() == [{"unit": "p0", "v": 1}]


def test_finalize_writes_a_parquet_table_and_an_ineligible_ledger(tmp_path: Path):
    from publishable.units import Unit, UnitList

    roster = UnitList([Unit(key=f"p{i}", attributes={"site": "a"}) for i in range(3)])
    sd = tmp_path / "run" / "shared" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run", units=roster)
    io.record("p0", {"pred": 0.5})
    io.record("p1", {"pred": 0.7, "extra": 9})
    io.skip("p2", "no baseline visit")
    io.finalize()
    rows = io.read_upstream("s", "units.parquet")
    assert [r["unit"] for r in rows] == ["p0", "p1"]
    assert rows[0]["extra"] is None, "a column absent from a row reads as null"
    lines = (sd / "ineligible.jsonl").read_text().splitlines()
    assert json.loads(lines[0]) == {"unit": "p2", "reason": "no baseline visit"}


def test_no_files_are_written_when_nothing_was_recorded_or_skipped(tmp_path: Path):
    from publishable.units import Unit, UnitList

    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        units=UnitList([Unit(key="p0")]),
    )
    io.finalize()
    assert not (sd / "units.parquet").exists()
    assert not (sd / "ineligible.jsonl").exists()


def test_parquet_round_trips_through_the_registered_reader(tmp_path: Path):
    sd = tmp_path / "run" / "shared" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run")
    io.write("t.parquet", [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])
    assert io.read_upstream("s", "t.parquet") == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]


def test_the_writer_and_reader_tables_stay_in_step():
    from publishable.artifacts import READERS, WRITERS

    assert sorted(WRITERS) == sorted(READERS)
    assert ".parquet" in WRITERS


def test_a_mixed_int_and_float_column_promotes_to_float_deliberately():
    """Numeric promotion within a column is columnar-format behavior, not a defect.

    A per-unit metric that is whole for some units and fractional for others is
    ordinary (a score, a rate, a duration); requiring a step to pre-float its own
    values to dodge a spurious error would be worse. The promoted column is a
    truthful representation of the values it holds, and the next task collapses
    such columns to floats before any interval is computed anyway — see
    docs/superpowers/spec-defects.md.
    """
    from publishable.artifacts import _decode_parquet, _encode_parquet

    encoded = _encode_parquet([{"v": 1}, {"v": 1.5}])
    decoded = _decode_parquet(encoded)
    assert decoded == [{"v": 1.0}, {"v": 1.5}]
    assert all(isinstance(row["v"], float) for row in decoded)


def test_a_bool_and_int_column_clash_raises_rather_than_coercing():
    """A bool/int mix is a real type confusion, not ordinary numeric variation —
    silently unifying it would hide a bug, so it must surface as a diagnosable
    ContractError naming the column and both types, not a bare pyarrow exception."""
    from publishable.artifacts import _encode_parquet

    with pytest.raises(ContractError) as e:
        _encode_parquet([{"v": True}, {"v": 1}])
    assert e.value.code == "E-STEP-RETURN-TYPE"
    assert "'v'" in str(e.value)
    assert "bool" in str(e.value)
    assert "int" in str(e.value)


def test_a_str_and_int_column_clash_raises_rather_than_coercing():
    """Same boundary as the bool/int case: a string/int mix is a type confusion that
    must surface as a named, diagnosable ContractError, not silently become strings."""
    from publishable.artifacts import _encode_parquet

    with pytest.raises(ContractError) as e:
        _encode_parquet([{"v": "x"}, {"v": 1}])
    assert e.value.code == "E-STEP-RETURN-TYPE"
    assert "'v'" in str(e.value)
    assert "str" in str(e.value)
    assert "int" in str(e.value)


def test_io_record_coerces_a_numpy_value(tmp_path: Path):
    io = make_io(tmp_path, units=UnitList([_u("u1")]))
    io.record("u1", {"score": np.float64(1.5)})
    row = io.rows()[0]
    assert type(row["score"]) is float


def test_io_record_refuses_a_structural_value(tmp_path: Path):
    io = make_io(tmp_path, units=UnitList([_u("u1")]))
    with pytest.raises(ContractError) as exc:
        io.record("u1", {"score": {"nested": 1}})
    assert exc.value.code == "E-STEP-RETURN-TYPE"


def test_rows_returns_deep_enough_copies_that_mutating_a_row_does_not_corrupt_state(
    tmp_path: Path,
):
    from publishable.units import Unit, UnitList

    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(
        step_dir=sd,
        input_dir=tmp_path / "in",
        run_dir=tmp_path / "run",
        units=UnitList([Unit(key="p0")]),
    )
    io.record("p0", {"v": 1})
    rows = io.rows()
    rows[0]["v"] = 999
    assert io.rows() == [{"unit": "p0", "v": 1}]


def test_conditions_and_read_condition_are_summary_only(tmp_path: Path):
    io = make_io(tmp_path, scope="repeat", conditions=[(0, "baseline")])
    for call in (lambda: io.conditions, lambda: io.read_condition(0, "s", "a.json")):
        with pytest.raises(ContractError) as e:
            call()
        assert e.value.code == "E-STEP-SCOPE-ONLY"


def test_repeats_is_summary_only(tmp_path: Path):
    io = make_io(tmp_path, scope="condition", repeats=["seed17"])
    with pytest.raises(ContractError) as e:
        _ = io.repeats
    assert e.value.code == "E-STEP-SCOPE-ONLY"


def test_conditions_and_read_condition_raise_at_run_scope(tmp_path: Path):
    io = make_io(tmp_path, scope="run", conditions=[(0, "baseline")])
    with pytest.raises(ContractError) as e:
        _ = io.conditions
    assert e.value.code == "E-STEP-SCOPE-ONLY"


def test_a_summary_step_can_list_conditions_and_repeats(tmp_path: Path):
    io = make_io(
        tmp_path,
        scope="summary",
        conditions=[(0, "baseline"), (1, "method=spearman")],
        repeats=["seed17"],
    )
    assert io.conditions == [(0, "baseline"), (1, "method=spearman")]
    assert io.repeats == ["seed17"]


def test_a_wider_step_cannot_read_a_narrower_one(tmp_path: Path):
    io = make_io(tmp_path, scope="condition", step_scopes={"analyze": "repeat"})
    with pytest.raises(ContractError) as e:
        io.read_upstream("analyze", "units.parquet")
    assert e.value.code == "E-STEP-READ-DIRECTION"
    assert "condition" in str(e.value) and "repeat" in str(e.value)


def test_a_narrower_step_reads_a_wider_one_normally(tmp_path: Path):
    io = make_io(tmp_path, scope="repeat", step_scopes={"load": "run"})
    (io.run_dir / "shared" / "load").mkdir(parents=True)
    (io.run_dir / "shared" / "load" / "a.json").write_text('{"x": 1}\n')
    assert io.read_upstream("load", "a.json") == {"x": 1}


def test_a_repeat_step_reads_a_condition_scoped_step(tmp_path: Path):
    """The case that fails today: `shared/` is where run-scoped steps write, and a
    condition-scoped step writes under its own condition directory."""
    io = make_io(
        tmp_path,
        scope="repeat",
        condition_index=0,
        condition_label="baseline",
        step_scopes={"fit": "condition"},
    )
    cond = io.run_dir / "conditions" / "00_baseline" / "fit"
    cond.mkdir(parents=True)
    (cond / "model.json").write_text('{"m": 1}\n')
    assert io.read_upstream("fit", "model.json") == {"m": 1}


def test_a_condition_step_still_reads_a_run_scoped_step(tmp_path: Path):
    io = make_io(
        tmp_path,
        scope="condition",
        condition_index=0,
        condition_label="baseline",
        step_scopes={"load": "run"},
    )
    shared = io.run_dir / "shared" / "load"
    shared.mkdir(parents=True)
    (shared / "cohort.json").write_text('{"n": 3}\n')
    assert io.read_upstream("load", "cohort.json") == {"n": 3}


def test_reading_a_narrower_step_is_still_refused(tmp_path: Path):
    io = make_io(
        tmp_path,
        scope="condition",
        condition_index=0,
        condition_label="baseline",
        step_scopes={"analyze": "repeat"},
    )
    with pytest.raises(ContractError) as exc:
        io.read_upstream("analyze", "scores.json")
    assert exc.value.code == "E-STEP-READ-DIRECTION"


def test_a_step_reads_another_step_at_its_own_scope(tmp_path: Path):
    io = make_io(
        tmp_path,
        scope="condition",
        step_scopes={"fit": "condition"},
        condition_index=0,
        condition_label="baseline",
    )
    fit_dir = io.run_dir / "conditions" / "00_baseline" / "fit"
    fit_dir.mkdir(parents=True)
    (fit_dir / "model.json").write_text('{"k": 1}\n')
    assert io.read_upstream("fit", "model.json") == {"k": 1}


def test_a_repeat_step_reads_another_repeat_step_at_its_own_scope(tmp_path: Path):
    """The fourth scope. `read_upstream` resolved `run`, `condition`, and `summary`;
    a `repeat`-scoped target fell into the condition branch with its repeat-label
    segment omitted, so an entirely ordinary pipeline — two repeat-scope steps, the
    second reading the first's artifact — crashed with a bare `FileNotFoundError`
    naming a path nothing writes. With exactly one repeat the directory collapses
    and it happened to work, so it appeared the day a user added a second seed.
    Two repeats here for that reason.
    """
    io = make_io(
        tmp_path,
        scope="repeat",
        step_scopes={"fit": "repeat"},
        conditions=[(0, "baseline")],
        repeats=["seed17", "seed42"],
        condition_index=0,
        condition_label="baseline",
        repeat_label="seed42",
    )
    fit_dir = io.run_dir / "conditions" / "00_baseline" / "seed42" / "fit"
    fit_dir.mkdir(parents=True)
    (fit_dir / "model.json").write_text('{"k": 2}\n')
    assert io.read_upstream("fit", "model.json") == {"k": 2}


def test_a_repeat_step_reading_a_condition_step_adds_no_repeat_segment(tmp_path: Path):
    """The segment is a property of the TARGET's scope, not the caller's: a
    condition-scoped artifact is written once per condition, above every repeat."""
    io = make_io(
        tmp_path,
        scope="repeat",
        step_scopes={"fit": "condition"},
        conditions=[(0, "baseline")],
        repeats=["seed17", "seed42"],
        condition_index=0,
        condition_label="baseline",
        repeat_label="seed42",
    )
    fit_dir = io.run_dir / "conditions" / "00_baseline" / "fit"
    fit_dir.mkdir(parents=True)
    (fit_dir / "model.json").write_text('{"k": 1}\n')
    assert io.read_upstream("fit", "model.json") == {"k": 1}


@pytest.mark.parametrize("target_scope", ["run", "condition", "repeat"])
def test_a_summary_step_reads_upstream_from_every_narrower_scope_in_a_no_sweep_run(
    tmp_path: Path, target_scope: str
):
    """`summary` sits above `run`, `condition`, and `repeat` alike — every one of
    them is a read of something wider, and none may raise E-STEP-READ-DIRECTION.
    `scope.py::build_plan` gives a real summary `Execution` no condition context
    at all (`condition_index=None, condition_label=None`), so this test doesn't
    inject any — that state is unreachable in production and a test that
    manufactures it proves nothing. With no sweep declared there is exactly one,
    unlabeled condition and no `conditions/` level, so `run_dir/step/name` (or
    `shared/`, for a run-scoped target) is genuinely where the target's writer
    left its output."""
    io = make_io(
        tmp_path,
        scope="summary",
        conditions=[(0, None)],
        step_scopes={"upstream": target_scope},
    )
    if target_scope == "run":
        upstream_dir = io.run_dir / "shared" / "upstream"
    else:
        upstream_dir = io.run_dir / "upstream"
    upstream_dir.mkdir(parents=True)
    (upstream_dir / "a.json").write_text('{"x": 1}\n')
    assert io.read_upstream("upstream", "a.json") == {"x": 1}


@pytest.mark.parametrize("target_scope", ["condition", "repeat"])
def test_a_summary_step_cannot_read_upstream_from_a_labeled_sweep(
    tmp_path: Path, target_scope: str
):
    """Once a sweep labels its conditions, `io.read_upstream` from `summary` scope
    has no single condition to resolve a condition- or repeat-scoped target to —
    that ambiguity is exactly what `io.read_condition` exists to resolve instead."""
    io = make_io(
        tmp_path,
        scope="summary",
        conditions=[(0, "baseline"), (1, "method=spearman")],
        step_scopes={"upstream": target_scope},
    )
    with pytest.raises(ContractError) as exc:
        io.read_upstream("upstream", "a.json")
    assert exc.value.code == "E-STEP-READ-AMBIGUOUS"


def test_a_summary_step_cannot_read_upstream_from_a_repeat_scoped_step_with_several_repeats(
    tmp_path: Path,
):
    """The sibling ambiguity one level down from the labeled-sweep case above: with
    no `sweep` block at all, a run can still resolve more than one repeat, and a
    `summary` step sits above every one of them. `read_upstream` has no single
    repeat to resolve a `repeat`-scoped target to, so it must refuse exactly as the
    labeled-condition case does, pointing at `io.read_condition(..., repeat=...)`
    instead."""
    io = make_io(
        tmp_path,
        scope="summary",
        conditions=[(0, None)],
        repeats=["seed1", "seed2"],
        step_scopes={"analyze": "repeat"},
    )
    with pytest.raises(ContractError) as exc:
        io.read_upstream("analyze", "a.json")
    assert exc.value.code == "E-STEP-READ-AMBIGUOUS"
    assert "io.read_condition" in str(exc.value)


def test_a_summary_step_reads_upstream_from_a_repeat_scoped_step_with_one_repeat(
    tmp_path: Path,
):
    """The case a careless fix breaks: with exactly one repeat the repeat directory
    collapses (`runner.step_dir_for` adds no segment), so `run_dir/step/name` is
    genuinely where the target wrote its output, and the read must still succeed."""
    io = make_io(
        tmp_path,
        scope="summary",
        conditions=[(0, None)],
        repeats=["seed1"],
        step_scopes={"analyze": "repeat"},
    )
    upstream_dir = io.run_dir / "analyze"
    upstream_dir.mkdir(parents=True)
    (upstream_dir / "a.json").write_text('{"x": 1}\n')
    assert io.read_upstream("analyze", "a.json") == {"x": 1}


def test_a_summary_step_reads_another_summary_step(tmp_path: Path):
    """Direct coverage of the `target == "summary"` branch: a summary step reading
    an upstream step that is itself summary-scoped resolves under `summary/`, not
    `shared/` or a condition directory."""
    io = make_io(tmp_path, scope="summary", step_scopes={"earlier": "summary"})
    summary_dir = io.run_dir / "summary" / "earlier"
    summary_dir.mkdir(parents=True)
    (summary_dir / "a.json").write_text('{"x": 1}\n')
    assert io.read_upstream("earlier", "a.json") == {"x": 1}


def test_read_condition_requires_a_repeat_for_a_repeat_scoped_step(tmp_path: Path):
    io = make_io(
        tmp_path,
        scope="summary",
        conditions=[(0, "baseline")],
        step_scopes={"analyze": "repeat"},
    )
    with pytest.raises(ContractError) as e:
        io.read_condition(0, "analyze", "units.parquet")
    assert e.value.code == "E-STEP-READ-REPEAT-REQUIRED"


def test_read_condition_rejects_an_unresolved_condition_index(tmp_path: Path):
    io = make_io(tmp_path, scope="summary", conditions=[(0, "baseline")])
    with pytest.raises(ContractError) as e:
        io.read_condition(7, "s", "a.json")
    assert e.value.code == "E-STEP-READ-CONDITION-UNKNOWN"


def test_read_condition_succeeds_for_a_resolved_condition_with_a_null_label(tmp_path: Path):
    """The no-`sweep` case: `sweep.expand` resolves one condition, index 0 with
    `label=None`, meaning there is no `conditions/` level at all — not an absent
    index. `read_condition(0, ...)` must return the artifact, not raise
    E-STEP-READ-CONDITION-UNKNOWN, and the path must skip the `conditions/` nest."""
    io = make_io(tmp_path, scope="summary", conditions=[(0, None)], step_scopes={"fit": "run"})
    target = io.run_dir / "fit"
    target.mkdir(parents=True)
    (target / "model.json").write_text('{"m": 1}\n')
    assert io.read_condition(0, "fit", "model.json") == {"m": 1}
    assert not (io.run_dir / "conditions").exists()


def test_read_condition_resolves_a_non_repeat_scoped_step_without_a_repeat(tmp_path: Path):
    io = make_io(
        tmp_path,
        scope="summary",
        conditions=[(0, "baseline"), (1, "method=spearman")],
        step_scopes={"fit": "condition"},
    )
    target = io.run_dir / "conditions" / "01_method=spearman" / "fit"
    target.mkdir(parents=True)
    (target / "model.json").write_text('{"m": 1}\n')
    assert io.read_condition(1, "fit", "model.json") == {"m": 1}


def test_read_condition_accepts_the_element_io_conditions_yields(tmp_path: Path):
    """The documented pattern (reference.md around lines 1784, 1806, 2318):
    `for condition in io.conditions: io.read_condition(condition, ...)` — passing
    the (index, label) tuple straight through must work, not only a bare index."""
    io = make_io(
        tmp_path,
        scope="summary",
        conditions=[(0, "baseline"), (1, "method=spearman")],
        step_scopes={"fit": "condition"},
    )
    target = io.run_dir / "conditions" / "01_method=spearman" / "fit"
    target.mkdir(parents=True)
    (target / "model.json").write_text('{"m": 1}\n')
    results = {}
    for condition in io.conditions:
        if condition[0] == 1:
            results[condition] = io.read_condition(condition, "fit", "model.json")
    assert results[(1, "method=spearman")] == {"m": 1}


def test_read_condition_resolves_a_named_repeat_when_the_run_has_several(tmp_path: Path):
    io = make_io(
        tmp_path,
        scope="summary",
        conditions=[(0, "baseline")],
        repeats=["seed1", "seed2"],
        step_scopes={"analyze": "repeat"},
    )
    target = io.run_dir / "conditions" / "00_baseline" / "seed2" / "analyze"
    target.mkdir(parents=True)
    (target / "scores.json").write_text('{"s": 2}\n')
    assert io.read_condition(0, "analyze", "scores.json", repeat="seed2") == {"s": 2}


def test_read_condition_collapses_the_repeat_directory_when_the_run_has_only_one(
    tmp_path: Path,
):
    io = make_io(
        tmp_path,
        scope="summary",
        conditions=[(0, "baseline")],
        repeats=["seed1"],
        step_scopes={"analyze": "repeat"},
    )
    target = io.run_dir / "conditions" / "00_baseline" / "analyze"
    target.mkdir(parents=True)
    (target / "scores.json").write_text('{"s": 1}\n')
    assert io.read_condition(0, "analyze", "scores.json", repeat="seed1") == {"s": 1}


def _mixed_arm_roster():
    """4 `control` and 9 `treatment`, 13 total — every number in play (4, 9, 13)
    is distinct from the others and from every arm fixture already in the
    suite (`_arm_roster12`'s 7/5/12, `test_cli.py`'s 8/3/11), and no
    `cluster_by` attribute is declared, so this can't double as a cluster
    fixture. Keys are deliberately **not** in alphabetical or roster-grouped
    order within either arm — `c3, c0, c2, c1` and a shuffled 9-key
    treatment list — so a test reading `arms_of`'s output back can tell
    "the order `arms_of` resolved units in" from "sorted," which a
    same-length, same-membership check could not."""
    control_keys = ["c3", "c0", "c2", "c1"]
    treatment_keys = ["t5", "t1", "t8", "t0", "t3", "t7", "t2", "t6", "t4"]
    units = [Unit(key=k, attributes={"arm": "control"}) for k in control_keys]
    units += [Unit(key=k, attributes={"arm": "treatment"}) for k in treatment_keys]
    return UnitList(units), control_keys, treatment_keys


def _plans_for(roster):
    """The one `arm` axis of `_mixed_arm_roster`, realized through
    `units.assignment_for` — the single producer of an `ArmPlan`, and the only
    route by which membership reaches `build_allocation_document` now that it
    takes no roster and derives nothing. `block=None` takes `assignment_for`'s
    `by_attribute` path and resolves the column to the axis name, which is
    what this fixture's units carry."""
    return {"arm": assignment_for(roster, "arm", None, ["control", "treatment"], "digest")}


def test_build_allocation_document_returns_none_with_no_group_axes():
    """`group_axes` empty — no arm assignment resolved for this run — is the
    absent half of 'present when either is declared', and `command_run` reads
    `None` here as "write nothing.\""""
    assert build_allocation_document({}) is None


def test_build_allocation_document_maps_axis_to_level_to_unit_keys_in_roster_order():
    """The mutation the brief names: writing row indices rather than keys must
    fail THIS assertion, not merely a length check — `["c3", "c0", "c2",
    "c1"]` and `[0, 1, 2, 3]` are both length 4, so only the exact key
    strings, in `arms_of`'s own resolved order, discriminate. `seed` and
    `strata` are asserted `{}` — the addendum's finding that a writer
    emitting a seed under `by_attribute` (nothing was drawn) looks correct
    against a fixture nobody checked the seed of — and `holdout` is asserted
    absent, since this build never declares one. Empty here because this
    document's only axis reads a column;
    `test_a_drawn_axis_records_its_seed_and_strata_and_a_read_one_records_neither`
    is the mixed document where one axis appears in both keys and the other in
    neither."""
    roster, control_keys, treatment_keys = _mixed_arm_roster()
    group_axes = _plans_for(roster)

    doc = build_allocation_document(group_axes)

    assert doc is not None
    assert set(doc.keys()) == {"seed", "arms", "strata"}
    assert doc["arms"] == {"arm": {"control": control_keys, "treatment": treatment_keys}}
    assert doc["seed"] == {}
    assert "arm" not in doc["seed"]
    assert doc["strata"] == {}
    assert "arm" not in doc["strata"]
    assert "holdout" not in doc


def test_a_drawn_axis_records_its_seed_and_strata_and_a_read_one_records_neither():
    """**The mixed case — one `by_attribute` axis beside one `random` axis, in
    one document.** § `allocation.json` prints `seed` and `strata` keyed by
    axis, and says a `by_attribute` axis "is left out of both": the record has
    to distinguish the two axes, not merely have the keys.

    A test with a drawn axis alone would pass with the `plan.seed is not None`
    and `plan.strata` filters deleted, since every axis in it qualifies; a test
    with a read axis alone is the one already above, which passes with the
    per-axis entries replaced by `{}`. Only the two together fail both
    mutations, so the assertions are exact mappings rather than membership.

    `cohort` is drawn nothing and reads a column; `arm` draws with a pinned
    `seed: 11` — pinned so the recorded value is a fact the test states rather
    than one it copies from the code that computed it — and stratifies on
    `site`, which is a declared attribute of every unit."""
    units = [
        Unit(
            key=f"u{i}",
            attributes={
                "cohort": "derivation" if i < 3 else "validation",
                "site": "S1" if i % 2 else "S2",
            },
        )
        for i in range(6)
    ]
    roster = UnitList(units)
    group_axes = {
        "cohort": assignment_for(
            roster, "cohort", {"method": "by_attribute"}, ["derivation", "validation"], "d"
        ),
        "arm": assignment_for(
            roster,
            "arm",
            {"method": "random", "seed": 11, "stratify_by": ["site"]},
            ["control", "treatment"],
            "d",
        ),
    }

    doc = build_allocation_document(group_axes)

    assert doc is not None
    assert doc["seed"] == {"arm": 11}
    assert doc["strata"] == {"arm": ["site"]}
    assert set(doc["arms"]) == {"cohort", "arm"}
    # The read axis is left out of both, and the drawn one is in both — stated
    # separately from the mappings above so a reader sees the claim § Manifest
    # makes, not only the shape.
    assert "cohort" not in doc["seed"]
    assert "cohort" not in doc["strata"]


def test_allocation_hash_is_deterministic_and_content_sensitive():
    """Mirrors `manifest.manifest_hash`'s own contract: same document, same
    hash; a document that differs by one unit key hashes differently — the
    property `provenance.allocation_hash` rests on to say a copy edited
    after the run no longer matches what that run reported."""
    roster, _, _ = _mixed_arm_roster()
    group_axes = _plans_for(roster)
    doc = build_allocation_document(group_axes)

    h1 = allocation_hash(doc)
    h2 = allocation_hash(build_allocation_document(group_axes))
    assert h1 == h2
    assert h1.startswith("sha256:")

    mutated = json.loads(json.dumps(doc))
    mutated["arms"]["arm"]["control"][0] = "c9"
    assert allocation_hash(mutated) != h1


def test_allocation_hash_changes_when_two_units_swap_arms_and_nothing_else_moves():
    """The discriminating form task 15's addendum asked for, in place of the
    weaker mutation above: that test edits a unit key inside the document
    (`"c3"` -> `"c9"`), which would also catch a hash that hashed something
    else entirely, but it says nothing about whether `allocation_hash`
    actually tracks *membership* rather than, say, the roster's contents.
    Reassigning a single unit changes the roster's own multiset of `arm`
    values (one fewer `control`, one more `treatment`), so a hash that
    happened to cover the roster instead of the assignment would *also* move
    and the test would pass while proving nothing about which one moved it.

    Swapping two units — one `control`, one `treatment` — between arms keeps
    the roster byte-identical in every column that isn't membership: same 13
    keys, same per-arm counts (4 `control`, 9 `treatment`), same multiset of
    `arm` values. Only which key sits in which arm changes. A hash sensitive
    to the roster's contents but not to `arms_of`'s partition would be blind
    to this and wrongly report no change.

    `c0` (`control`) and `t0` (`treatment`) are the two swapped. On this
    fixture the unswapped document hashes to
    `sha256:bf077b6dceea21f680dc12c7b050f04af5ee405be7326afe81c920c3e605d7d6`
    and the swapped one to
    `sha256:74e5df039ba6eaaca52d561a0e4bd04a4d1fa7334c4f4bdc2f42ec6ea069981d`
    (both recomputed directly against this build, not carried over from
    memory) — two different digests for a roster whose 13 keys, per-arm
    counts, and multiset of `arm` values are all unchanged; only which key
    sits in which arm moved.
    """
    roster, control_keys, treatment_keys = _mixed_arm_roster()
    doc = build_allocation_document(_plans_for(roster))
    h1 = allocation_hash(doc)
    assert h1 == "sha256:bf077b6dceea21f680dc12c7b050f04af5ee405be7326afe81c920c3e605d7d6"

    swapped_units = []
    for unit in roster:
        if unit.key == "c0":
            swapped_units.append(Unit(key=unit.key, attributes={"arm": "treatment"}))
        elif unit.key == "t0":
            swapped_units.append(Unit(key=unit.key, attributes={"arm": "control"}))
        else:
            swapped_units.append(unit)
    swapped_roster = UnitList(swapped_units)

    swapped_control = {*control_keys, "t0"} - {"c0"}
    swapped_treatment = {*treatment_keys, "c0"} - {"t0"}
    # Same per-arm sizes, same combined key set, same multiset of `arm`
    # values — only membership moved.
    assert len(swapped_control) == len(control_keys) == 4
    assert len(swapped_treatment) == len(treatment_keys) == 9
    assert swapped_control | swapped_treatment == set(control_keys) | set(treatment_keys)

    swapped_doc = build_allocation_document(_plans_for(swapped_roster))
    h2 = allocation_hash(swapped_doc)

    assert set(swapped_doc["arms"]["arm"]["control"]) == swapped_control
    assert set(swapped_doc["arms"]["arm"]["treatment"]) == swapped_treatment
    assert h2 == "sha256:74e5df039ba6eaaca52d561a0e4bd04a4d1fa7334c4f4bdc2f42ec6ea069981d"
    assert h2 != h1
