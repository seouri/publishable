# tests/test_artifacts.py
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml

from publishable import ArtifactError, ArtifactExistsError, ContractError, artifacts
from publishable.artifacts import (
    ReportIO,
    StepIO,
    allocation_hash,
    build_allocation_document,
    derive_step_scopes_and_repeats,
    write_atomic,
)
from publishable.lineage import UpstreamLedger, UpstreamResolver
from publishable.run_record import SCHEMA_VERSION
from publishable.units import ArmPlan, HoldoutPlan, Unit, UnitList, assignment_for


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


def test_h5a_step2_control_the_unregistered_suffix_message_is_not_prefixed(
    io: StepIO,
):
    """Task 9 step 2's control (§ Corrections, correction 3): this raise
    sits in `io.write`'s own `else` branch, outside the `WRITERS[suffix](obj)`
    dispatch the new `except ContractError` wraps, so it must not gain a
    second copy of the artifact name. The design's own wording — "not
    prefixed" — is unassertable as written, because this message already
    contains the name (`"{name} has no registered writer …"`); asserted
    instead as `msg.count(name) == 1` and `not msg.startswith(f"{name}:")`.
    """
    with pytest.raises(ArtifactError) as e:
        io.write("model3.pkl", {"not": "bytes"})
    msg = str(e.value)
    assert msg.count("model3.pkl") == 1
    assert not msg.startswith("model3.pkl:")


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


# Task 7 — Fixture M, design Decision 9. Measured at `d2caacf`: the plain branch
# used to accept a `measurement` key and write it into `units.parquet`, while the
# `measurement=` branch refused the identical key three lines away. Three arms:
# the plain branch now refuses it (arm 1), the `measurement=` branch already did
# and still does (arm 2 — kept so the symmetry is what the test asserts, not just
# arm 1 in isolation), and a plain record naming the *plural* `measurements` still
# writes (arm 3 — the control that stops a substring/prefix guard from passing).
def test_fixture_m_plain_record_refuses_a_measurement_column(tmp_path: Path):
    """Arm 1: the asymmetry this task closes."""
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
        io.record("p0", {"measurement": "HIJACK"})
    assert e.value.code == "E-STEP-KEY-COLLISION"
    assert "measurement" in str(e.value)


def test_fixture_m_measurement_branch_still_refuses_the_same_key(tmp_path: Path):
    """Arm 2: already passing today, kept so the test asserts the symmetry
    rather than only the new branch."""
    io = _measuring_io(tmp_path)
    with pytest.raises(ContractError) as e:
        io.record("p0", {"measurement": "HIJACK"}, measurement="r1")
    assert e.value.code == "E-STEP-KEY-COLLISION"


def test_fixture_m_a_plural_measurements_column_still_writes(tmp_path: Path):
    """Arm 3, the control: `measurements` (plural) is a different name from
    `measurement` and must keep writing — a guard written as a substring or
    prefix test over the key would swallow this too."""
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
    io.record("p0", {"measurements": 3})
    io.finalize()
    assert _read_parquet(io.step_dir / "units.parquet") == [{"unit": "p0", "measurements": 3}]


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


# Task 5 step 6 — the arms § Corrections correction 1 exists for. A recorded
# `by` column is legal by design (design Decision 4: the refusal removes one
# PRODUCER of a `by` column, an attribute declaration, never the possibility
# of one), and `RESERVED_COLUMNS` must have exactly one reader for that to
# stay true. Without these two pins, a later slice pointing `record`'s
# collision guards or `_collapse_measurements`' structural-column exclusion
# at the constant would refuse or silently drop a legally recorded `by`
# column, with the suite green.
def test_a_plain_recorded_by_column_survives_into_units_parquet(tmp_path: Path) -> None:
    """Arm (a): a PLAIN `io.record` payload naming `by` reaches `units.parquet`
    with its value. `RESERVED_COLUMNS` is not consulted by `record`'s
    collision guards at all — only `unit` and `measurement` are, by literal —
    so `by` is neither of the two names those guards refuse.

    Brief step 6(a)'s second clause — that a real `run` also draws
    `W-STATS-STRATUM-SHADOWED` for this column — is deliberately NOT asserted
    here: a bare `StepIO` has no `run` around it to draw a warning from, and
    that warning is `cli.py`'s, not `artifacts.py`'s. It is covered end to end
    by the pre-existing `tests/test_cli.py::
    test_a_recorded_column_named_by_keeps_its_metric_and_warns`, which runs a
    real `run` recording `by` and asserts both the warning and the column's
    own value and interval survive. This arm's job is narrower: only the
    plain-record-reaches-`units.parquet` half, at the artifact layer."""
    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run")
    io.record("p1", {"by": 2.0, "score": 10})
    io.finalize()
    assert _read_parquet(io.step_dir / "units.parquet") == [{"unit": "p1", "by": 2.0, "score": 10}]


def test_a_measured_by_column_survives_the_collapse_into_units_parquet(tmp_path: Path) -> None:
    """Arm (b): a `measurement=`-recorded column named `by` survives
    `_collapse_measurements`. `collapse: "first"` is declared explicitly
    (rather than leaving `by` a numeric value) because `_collapse_measurements`
    calls `rule_for("by", collapse)` then `coerce_for_rule` — under a NUMERIC
    rule a string `by` value would refuse before this arm could observe
    survival at all, which is a fixture that fires for the wrong reason. Under
    `first`, `coerce_for_rule` is a no-op and the earliest-recorded string
    value survives untouched — which is also why `by`'s value here is a
    string ("north") rather than a number: a numeric value under `first`
    would pass even if `_collapse_measurements`' structural-column exclusion
    HAD been re-pointed at `RESERVED_COLUMNS`, since `coerce_for_rule` would
    silently produce a number either way. A string value is what makes this
    arm distinguish "the column is excluded" from "the column collapsed"."""
    io = _measuring_io(tmp_path, collapse="first")
    io.record("p1", {"by": "north", "score": 10}, measurement="r1")
    io.record("p1", {"by": "north", "score": 20}, measurement="r2")
    io.finalize()
    assert _read_parquet(io.step_dir / "units.parquet") == [
        {"unit": "p1", "by": "north", "score": 10}
    ]


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


# Task 8 — Fixture D, design Decision 10, plan § Corrections correction 5.
#
# `finalize`'s `columns = ["unit", *attribute_names, *recorded]` can hold
# `"unit"` twice when a directly constructed `Unit` carries an attribute named
# `unit` — `recorded` excludes `"unit"` but `attribute_names` does not. The
# per-row dict comprehension `finalize` builds already collapses a duplicate
# column NAME (a Python dict cannot hold the same key twice), so an assertion
# on the written parquet's column order passes identically whether or not the
# list itself is deduped — measured, and why this fixture does not read the
# file. The claim is about the LIST `finalize` builds, so the assertion is on
# that list.
#
# `finalize`'s own signature is unchanged, so the list is reached by spying on
# the module-level helper it now calls, `_finalize_columns` — chosen over
# inlining the dedupe, per the brief, because a spy on a call `finalize` makes
# is what catches BOTH ways this could regress: the helper's own body losing
# the dedupe (the spy's return still holds the duplicate), and `finalize`
# reverting to building the list inline without calling the helper at all (the
# spy is never invoked). A test that only unit-tests `_finalize_columns` in
# isolation would miss the second — "a mutation applied to a proxy" — because
# nothing would ever call `finalize` through the helper in that test.
def test_fixture_d_finalize_columns_is_deduped_by_name(tmp_path: Path, monkeypatch):
    from publishable.units import Unit, UnitList

    calls: list[tuple[list[str], list[str]]] = []
    returned: list[list[str]] = []
    real = artifacts._finalize_columns

    def spy(attribute_names: list[str], recorded: list[str]) -> list[str]:
        calls.append((list(attribute_names), list(recorded)))
        result = real(attribute_names, recorded)
        returned.append(result)
        return result

    monkeypatch.setattr(artifacts, "_finalize_columns", spy)

    sd = tmp_path / "run" / "s"
    sd.mkdir(parents=True)
    (tmp_path / "in").mkdir()
    # A Unit built directly (not through resolve_units), carrying an attribute
    # named `unit` — the shape task 5's E-UNITS-ATTR-COLUMN refuses for a
    # config but cannot reach here, since `Unit` is on § The importable
    # surface and this call constructs one by hand.
    roster = UnitList([Unit(key="p0", attributes={"unit": "HIJACK", "site": "a"})])
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run", units=roster)
    io.record("p0", {"score": 1})
    io.finalize()

    # The call-site half: `finalize` must actually route through the helper,
    # or the spy — and the dedupe it wraps — is never exercised at all.
    assert len(calls) == 1
    attribute_names, recorded = calls[0]
    assert attribute_names == ["unit", "site"]
    assert recorded == ["score"]

    # The list half: the helper's return, as `finalize` actually used it, has
    # `"unit"` exactly once, in first-seen (leading) position.
    columns = returned[0]
    assert columns.count("unit") == 1
    assert columns == ["unit", "site", "score"]

    # Documents the residual correction 5 names: the dedupe fixes the LIST,
    # not the VALUE. The attribute merge still overwrites `merged["unit"]`
    # with the attribute's value, so the published row's `unit` column carries
    # the attribute's "HIJACK", not the real key "p0" — unchanged by this
    # task, and not asserted as a passing behaviour here, only recorded as the
    # open residual (filed by task 12 for a direct caller; no guard is built
    # for it in this task).
    rows = _read_parquet(io.step_dir / "units.parquet")
    assert rows == [{"unit": "HIJACK", "site": "a", "score": 1}]


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


def test_h8a_arm_d_the_shipped_positive_read_upstream_read(tmp_path: Path):
    """Task 11 arm D — the shipped positive `read_upstream` read, pinned
    before H8a builds `io.reuse_from` beside it. `step01` writes `ok.json`
    under `shared/`, and a narrower step reads it back through the ordinary
    `run`-scoped path `test_a_narrower_step_reads_a_wider_one_normally`
    already exercises. See `docs/superpowers/plans/2026-08-20-lineage.md`
    task 11.
    """
    io = make_io(tmp_path, scope="repeat", step_scopes={"step01": "run"})
    (io.run_dir / "shared" / "step01").mkdir(parents=True)
    (io.run_dir / "shared" / "step01" / "ok.json").write_text('{"ok": true}\n')
    assert io.read_upstream("step01", "ok.json") == {"ok": True}


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


# ---------------------------------------------------------------------------
# H8c task 2 — `derive_step_scopes_and_repeats`, the derivation
# `lineage.resolve_step` does NOT perform (§ Corrections, correction 2), and
# `ReportIO`, the read half a `summary`-scope `StepIO` carries and nothing
# else (Decision 4). `ReportIO.read_condition` shares its traversal with
# `StepIO.read_condition` through the module-level `_resolve_condition_step_dir`
# / `_nest_repeat_segment` this task extracts — proved by the load-bearing
# mutation below, which fails a test of each.
# ---------------------------------------------------------------------------


def test_derive_step_scopes_and_repeats_reads_the_three_way_split(tmp_path: Path):
    """Every branch `run_record._execution_block` can write: a `run`-scoped
    step (`shared`), a `summary`-scoped one, a `condition`-scoped entry that
    holds `status` directly, and a `repeat`-scoped entry whose keys are
    repeat labels. Constructed by hand rather than through a real run — this
    pins the derivation in isolation from everything a real `execute_plan`
    would also produce.
    """
    execution = {
        "shared": {"load": {"status": "completed"}},
        "summary": {"compare": {"status": "completed"}},
        "conditions": [
            {
                "index": 0,
                "label": "baseline",
                "steps": {
                    "fit": {"status": "completed"},
                    "analyze": {
                        "seed1": {"status": "completed"},
                        "seed2": {"status": "completed"},
                    },
                },
            }
        ],
    }
    step_scopes, repeats = derive_step_scopes_and_repeats(execution)
    assert step_scopes == {
        "load": "run",
        "compare": "summary",
        "fit": "condition",
        "analyze": "repeat",
    }
    assert repeats == ["seed1", "seed2"]


def test_derive_step_scopes_and_repeats_at_one_repeat_still_reports_the_label(tmp_path: Path):
    """Measured (§ Corrections, correction 2): a repeat-scoped step's
    `execution` entry nests labels even when the run resolved exactly one —
    the record nests, the directory collapses. So `repeats` still comes back
    non-empty, and it is `len(repeats) > 1` — never the entry's own presence
    or absence of nesting — that later decides whether a path nests.
    """
    execution = {
        "shared": {},
        "summary": {},
        "conditions": [
            {
                "index": 0,
                "label": "baseline",
                "steps": {"analyze": {"seed1": {"status": "completed"}}},
            }
        ],
    }
    step_scopes, repeats = derive_step_scopes_and_repeats(execution)
    assert step_scopes == {"analyze": "repeat"}
    assert repeats == ["seed1"]


def test_derive_step_scopes_and_repeats_across_several_conditions_dedupes_labels(
    tmp_path: Path,
):
    """Two conditions, the same repeat-scoped step, the same labels — the
    labels are collected once, in first-seen order, not once per condition.
    """
    execution = {
        "shared": {},
        "summary": {},
        "conditions": [
            {
                "index": 0,
                "label": "baseline",
                "steps": {"analyze": {"seed1": {"status": "completed"}}},
            },
            {
                "index": 1,
                "label": "method=spearman",
                "steps": {"analyze": {"seed1": {"status": "completed"}}},
            },
        ],
    }
    _, repeats = derive_step_scopes_and_repeats(execution)
    assert repeats == ["seed1"]


def make_report_io(
    tmp_path: Path,
    *,
    conditions: list[tuple[int, str | None]],
    repeats: list[str] | None = None,
    step_scopes: dict[str, str] | None = None,
) -> ReportIO:
    (tmp_path / "run").mkdir(parents=True, exist_ok=True)
    (tmp_path / "input").mkdir(exist_ok=True)
    return ReportIO(
        run_dir=tmp_path / "run",
        input_dir=tmp_path / "input",
        conditions=conditions,
        repeats=repeats or [],
        step_scopes=step_scopes or {},
    )


def test_report_io_conditions_and_repeats_are_plain_properties(tmp_path: Path):
    """No `_summary_only` gate: a report has no scope, so both are always
    readable — unlike `StepIO`'s same-named properties, which refuse outside
    `summary` scope (`test_conditions_and_read_condition_are_summary_only`).
    """
    io = make_report_io(
        tmp_path, conditions=[(0, "baseline"), (1, "method=spearman")], repeats=["seed1", "seed2"]
    )
    assert io.conditions == [(0, "baseline"), (1, "method=spearman")]
    assert io.repeats == ["seed1", "seed2"]


def test_report_io_read_condition_resolves_a_null_label_condition(tmp_path: Path):
    io = make_report_io(tmp_path, conditions=[(0, None)], step_scopes={"fit": "run"})
    target = io.run_dir / "fit"
    target.mkdir(parents=True)
    (target / "model.json").write_text('{"m": 1}\n')
    assert io.read_condition(0, "fit", "model.json") == {"m": 1}


def test_report_io_read_condition_accepts_the_element_conditions_yields(tmp_path: Path):
    """The documented pattern, byte-identical to `StepIO`'s:
    `for condition in io.conditions: io.read_condition(condition, ...)`."""
    io = make_report_io(
        tmp_path,
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


def test_report_io_read_condition_resolves_a_named_repeat_when_the_run_has_several(
    tmp_path: Path,
):
    io = make_report_io(
        tmp_path,
        conditions=[(0, "baseline")],
        repeats=["seed1", "seed2"],
        step_scopes={"analyze": "repeat"},
    )
    target = io.run_dir / "conditions" / "00_baseline" / "seed2" / "analyze"
    target.mkdir(parents=True)
    (target / "scores.json").write_text('{"s": 2}\n')
    assert io.read_condition(0, "analyze", "scores.json", repeat="seed2") == {"s": 2}


def test_report_io_read_condition_collapses_the_repeat_directory_at_one_repeat(
    tmp_path: Path,
):
    """The discriminating case (§ Corrections, correction 2): one resolved
    repeat, so the directory carries no repeat-label segment even though the
    record's own entry would have nested one. Mirrors
    `test_read_condition_collapses_the_repeat_directory_when_the_run_has_only_one`
    on the `StepIO` side, over the SAME shared traversal function."""
    io = make_report_io(
        tmp_path,
        conditions=[(0, "baseline")],
        repeats=["seed1"],
        step_scopes={"analyze": "repeat"},
    )
    target = io.run_dir / "conditions" / "00_baseline" / "analyze"
    target.mkdir(parents=True)
    (target / "scores.json").write_text('{"s": 1}\n')
    assert io.read_condition(0, "analyze", "scores.json", repeat="seed1") == {"s": 1}


def test_report_io_read_condition_requires_a_repeat_for_a_repeat_scoped_step(tmp_path: Path):
    io = make_report_io(tmp_path, conditions=[(0, "baseline")], step_scopes={"analyze": "repeat"})
    with pytest.raises(ContractError) as e:
        io.read_condition(0, "analyze", "units.parquet")
    assert e.value.code == "E-STEP-READ-REPEAT-REQUIRED"


def test_report_io_read_condition_rejects_an_unresolved_condition_index(tmp_path: Path):
    io = make_report_io(tmp_path, conditions=[(0, "baseline")])
    with pytest.raises(ContractError) as e:
        io.read_condition(7, "s", "a.json")
    assert e.value.code == "E-STEP-READ-CONDITION-UNKNOWN"


def test_report_io_read_condition_name_containment_refuses_traversal(tmp_path: Path):
    io = make_report_io(tmp_path, conditions=[(0, "baseline")], step_scopes={"fit": "condition"})
    target = io.run_dir / "conditions" / "00_baseline" / "fit"
    target.mkdir(parents=True)
    (target / "model.json").write_text('{"m": 1}\n')
    with pytest.raises(ArtifactError) as e:
        io.read_condition(0, "fit", "../../escape.json")
    assert e.value.code == "E-ARTIFACT-NAME"


def test_report_io_read_input_reads_from_input_dir(tmp_path: Path):
    io = make_report_io(tmp_path, conditions=[(0, "baseline")])
    (io.input_dir / "roster.json").write_text('{"n": 10}\n')
    assert io.read_input("roster.json") == {"n": 10}


def test_report_io_has_no_write_half(tmp_path: Path):
    """The withheld half, asserted by name (task 2 step 4) — a positive arm
    cannot see this, which is *the control asserting only absences* run
    backwards: pair it with the tests above, where all four members work."""
    io = make_report_io(tmp_path, conditions=[(0, None)])
    for name in ("write", "record", "append", "finalize", "skip"):
        assert not hasattr(io, name)


# ---------------------------------------------------------------------------
# Task 12 — the shared `_contained` helper wired into `read_upstream` and
# `read_condition`. Fixture N's other two readers: `reuse_from` has its own
# containment test (grep `reuse_from_name_containment` in this file) — same
# construction, same code (`E-ARTIFACT-NAME`, the code `_resolve` already
# raises for these two readers, and not `E-UPSTREAM-NAME`, which is
# `reuse_from`'s own).
# `docs/superpowers/plans/2026-08-20-lineage.md` task 12.
# ---------------------------------------------------------------------------


def test_read_upstream_name_containment_refuses_traversal_absolute_path_and_symlink_escape(
    tmp_path: Path,
):
    """Fixture N's `read_upstream` refusal arms, each targeting a file
    that EXISTS and holds distinguishable content — so an unenforced check
    would return it rather than fail for an unrelated reason (the live probe
    at `28e311d` did exactly that for the `..` and absolute-outside arms)."""
    io = make_io(tmp_path, scope="repeat", step_scopes={"step01": "run"})
    step_dir = io.run_dir / "shared" / "step01"
    step_dir.mkdir(parents=True)

    # `..` traversal: a file that exists OUTSIDE the run entirely, reached by
    # a relative path with exactly enough `..` segments to escape `step_dir`.
    secret = tmp_path / "secret.json"
    secret.write_text('{"who": "SECRET_DOTDOT"}')
    escape_name = os.path.relpath(secret, step_dir)
    assert ".." in escape_name  # the fixture's own claim: this really escapes
    with pytest.raises(ArtifactError) as e:
        io.read_upstream("step01", escape_name)
    assert e.value.code == "E-ARTIFACT-NAME"

    # An absolute path, naming the same existing, distinguishable file.
    with pytest.raises(ArtifactError) as e:
        io.read_upstream("step01", str(secret))
    assert e.value.code == "E-ARTIFACT-NAME"

    # An absolute path pointing INSIDE the step directory itself — the two
    # arms above are each already refused by the `startswith` half of
    # `_contained`'s check (their target sits outside the resolved base), so
    # this is the arm refused ONLY by the absolute-path clause (batch 3's
    # "a refusal that fires for the wrong reason is not a pin").
    inside_absolute = step_dir / "ok.json"
    inside_absolute.write_text('{"who": "INSIDE_BUT_ABSOLUTE"}')
    with pytest.raises(ArtifactError) as e:
        io.read_upstream("step01", str(inside_absolute))
    assert e.value.code == "E-ARTIFACT-NAME"

    # A symlink inside the step directory leading outside it.
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "leak.json").write_text('{"who": "SECRET_SYMLINK"}')
    link = step_dir / "escape_dir"
    link.symlink_to(outside_dir, target_is_directory=True)
    with pytest.raises(ArtifactError) as e:
        io.read_upstream("step01", "escape_dir/leak.json")
    assert e.value.code == "E-ARTIFACT-NAME"


def test_read_upstream_positive_control_a_forward_separator_and_an_interior_dot_still_read(
    tmp_path: Path,
):
    """Fixture N's positive control, not optional per controller ruling 1: a
    helper that refused every separator would pass the refusal arms above
    and still be the over-refusal the ruling forbids. `programs/a.json` — a
    forward separator, § Steps and artifacts' own worked shape — and
    `programs/gpt-4.1__seed29.json`, whose interior dot must still dispatch
    as `.json`, not as some suffix ending in `.1`.
    """
    io = make_io(tmp_path, scope="repeat", step_scopes={"step01": "run"})
    programs = io.run_dir / "shared" / "step01" / "programs"
    programs.mkdir(parents=True)
    (programs / "a.json").write_text('{"a": 1}')
    (programs / "gpt-4.1__seed29.json").write_text('{"b": 2}')
    assert io.read_upstream("step01", "programs/a.json") == {"a": 1}
    assert io.read_upstream("step01", "programs/gpt-4.1__seed29.json") == {"b": 2}


def test_read_condition_name_containment_refuses_traversal_absolute_path_and_symlink_escape(
    tmp_path: Path,
):
    """Fixture N's `read_condition` refusal arms — `read_condition` is
    `summary`-scope only, so the fixture needs a `StepIO` with `conditions`
    and `step_scopes` set, the shape
    `test_read_condition_resolves_a_non_repeat_scoped_step_without_a_repeat`
    already uses."""
    io = make_io(
        tmp_path,
        scope="summary",
        conditions=[(0, "baseline")],
        step_scopes={"fit": "condition"},
    )
    step_dir = io.run_dir / "conditions" / "00_baseline" / "fit"
    step_dir.mkdir(parents=True)

    secret = tmp_path / "secret.json"
    secret.write_text('{"who": "SECRET_DOTDOT"}')
    escape_name = os.path.relpath(secret, step_dir)
    assert ".." in escape_name
    with pytest.raises(ArtifactError) as e:
        io.read_condition(0, "fit", escape_name)
    assert e.value.code == "E-ARTIFACT-NAME"

    with pytest.raises(ArtifactError) as e:
        io.read_condition(0, "fit", str(secret))
    assert e.value.code == "E-ARTIFACT-NAME"

    inside_absolute = step_dir / "ok.json"
    inside_absolute.write_text('{"who": "INSIDE_BUT_ABSOLUTE"}')
    with pytest.raises(ArtifactError) as e:
        io.read_condition(0, "fit", str(inside_absolute))
    assert e.value.code == "E-ARTIFACT-NAME"

    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "leak.json").write_text('{"who": "SECRET_SYMLINK"}')
    link = step_dir / "escape_dir"
    link.symlink_to(outside_dir, target_is_directory=True)
    with pytest.raises(ArtifactError) as e:
        io.read_condition(0, "fit", "escape_dir/leak.json")
    assert e.value.code == "E-ARTIFACT-NAME"


def test_read_condition_positive_control_a_forward_separator_and_an_interior_dot_still_read(
    tmp_path: Path,
):
    """Fixture N's positive control for `read_condition`."""
    io = make_io(
        tmp_path,
        scope="summary",
        conditions=[(0, "baseline")],
        step_scopes={"fit": "condition"},
    )
    programs = io.run_dir / "conditions" / "00_baseline" / "fit" / "programs"
    programs.mkdir(parents=True)
    (programs / "a.json").write_text('{"a": 1}')
    (programs / "gpt-4.1__seed29.json").write_text('{"b": 2}')
    assert io.read_condition(0, "fit", "programs/a.json") == {"a": 1}
    assert io.read_condition(0, "fit", "programs/gpt-4.1__seed29.json") == {"b": 2}


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


def test_a_drawn_holdout_writes_its_own_seed_and_strata_inside_its_block():
    """§ `allocation.json`: the top-level `seed`/`strata` are keyed by AXIS and
    a holdout is not an axis, so its own two travel inside its block. `train`
    and `test` are unit keys, never row numbers — a roster that gains a unit
    renumbers rows and would silently repoint every membership claim."""
    plan = HoldoutPlan(train=("P2", "P7"), test=("P11", "P19"), seed=3310985422, strata=("label",))
    doc = build_allocation_document({}, plan)
    assert doc["holdout"] == {
        "train": ["P2", "P7"],
        "test": ["P11", "P19"],
        "seed": 3310985422,
        "strata": ["label"],
    }
    # The axis-keyed blocks stay present and empty, the shape § `allocation.json`
    # prints for a run whose every axis reads a column.
    assert doc["seed"] == {} and doc["strata"] == {} and doc["arms"] == {}


def test_a_read_holdout_records_neither_seed_nor_strata():
    """`ArmPlan`'s own convention for `by_attribute`, one declaration over:
    reading a partition the data already holds is not drawing one, so a `seed`
    would be a false record of a draw that never happened and a `strata` would
    describe how a draw was balanced when none was.

    Asserted as absent KEYS rather than as `null`, matching
    `manifest/input.json`'s "absent rather than null, so 'not hashed' can't be
    misread as 'hashed to nothing'"."""
    plan = HoldoutPlan(train=("P2",), test=("P11",), seed=None, strata=())
    doc = build_allocation_document({}, plan)
    assert doc["holdout"] == {"train": ["P2"], "test": ["P11"]}


def test_a_drawn_unstratified_holdout_records_its_seed_and_no_strata():
    """The third arm, which the two above cannot distinguish between: a drawn
    split with no `stratify_by` carries a seed and no strata, so `strata` is
    omitted for EMPTINESS rather than for the method."""
    plan = HoldoutPlan(train=("P2",), test=("P11",), seed=7, strata=())
    assert build_allocation_document({}, plan)["holdout"] == {
        "train": ["P2"],
        "test": ["P11"],
        "seed": 7,
    }


def test_a_holdout_drawn_within_cells_discloses_the_axes_it_was_drawn_inside():
    """**H3c-3 task 16, Decision 11.** `within` names the group axes the split
    was drawn inside, and it is present exactly when there are any.

    `train` and `test` stay **flat lists over the whole roster** — a per-cell
    holdout's union is still a partition of that roster — so `within` is the
    only thing in the file that says which question the split answered. The
    axis NAMES are asserted, in `group_axes`' own order: an assertion that only
    checked the key's presence passes under a `within` derived from the wrong
    mapping, and a two-axis document is what tells order from set.

    The can-fail half is the same holdout with **no** axes, one line down: the
    key is absent, not `[]`, because an empty list would claim a per-cell draw
    over no cells. `test_a_drawn_holdout_writes_its_own_seed_and_strata_inside_its_block`
    and its two siblings assert that block by equality and so report the same
    mutation from the other side.
    """
    axes = {
        "arm": ArmPlan(
            levels=("a", "b"), members={"a": ("P1",), "b": ("P2",)}, seed=None, strata=()
        ),
        "site": ArmPlan(
            levels=("n", "s"), members={"n": ("P1",), "s": ("P2",)}, seed=None, strata=()
        ),
    }
    plan = HoldoutPlan(train=("P1",), test=("P2",), seed=7, strata=())
    doc = build_allocation_document(axes, plan)
    assert doc is not None
    assert doc["holdout"] == {
        "train": ["P1"],
        "test": ["P2"],
        "seed": 7,
        "within": ["arm", "site"],
    }
    assert "within" not in build_allocation_document({}, plan)["holdout"]


def test_the_document_is_written_when_either_partition_is_declared():
    """§ The other files a run writes: "present when either is declared". The
    four combinations, because a gate reading only one of the two passes three
    of them."""
    arms = {
        "arm": ArmPlan(
            levels=("a", "b"), members={"a": ("P1",), "b": ("P2",)}, seed=None, strata=()
        )
    }
    plan = HoldoutPlan(train=("P1",), test=("P2",), seed=7, strata=())
    assert build_allocation_document({}, None) is None
    assert build_allocation_document(arms, None) is not None
    assert build_allocation_document({}, plan) is not None
    both = build_allocation_document(arms, plan)
    assert both is not None and "arms" in both and "holdout" in both


def test_the_allocation_hash_covers_the_holdout_block():
    """`allocation_hash` canonicalizes whatever document it is handed, so the
    holdout's membership is covered without a `holdout_hash` — which
    `allocation_hash`'s own docstring rules out.

    The positive companion is the inequality: two documents differing only in
    which units were held out must hash differently, or the coverage claim is
    empty."""
    a = build_allocation_document({}, HoldoutPlan(("P1",), ("P2",), 7, ()))
    b = build_allocation_document({}, HoldoutPlan(("P2",), ("P1",), 7, ()))
    assert allocation_hash(a) != allocation_hash(b)
    assert allocation_hash(a) == allocation_hash(
        build_allocation_document({}, HoldoutPlan(("P1",), ("P2",), 7, ()))
    )


def test_a_suffix_with_a_writer_and_no_reader_is_a_coded_refusal(registries, tmp_path):
    """The bare `KeyError` § Steps and artifacts' promise breaks on.

    The mutation that can fail is adding a key to ONE dict — swapping a value
    between them cannot, since both hold the same keys.
    """
    from publishable import artifacts
    from publishable.errors import ArtifactError

    artifacts.WRITERS[".fastq"] = lambda rows: b"x"
    target = tmp_path / "a.fastq"
    target.write_bytes(b"x")

    with pytest.raises(ArtifactError) as excinfo:
        artifacts.StepIO._read(target)
    assert excinfo.value.code == "E-ARTIFACT-UNREADABLE"
    assert ".fastq" in str(excinfo.value)

    # THE CONTROL, produced by the code under test: with the reader supplied,
    # the same path reads. Without this the assertion above would pass for a
    # `_read` that refused every unknown suffix, including the ones it is
    # supposed to hand back as raw bytes.
    artifacts.READERS[".fastq"] = lambda data: {"read": data.decode()}
    assert artifacts.StepIO._read(target) == {"read": "x"}


def test_a_suffix_neither_table_knows_is_still_raw_bytes(tmp_path):
    """The behaviour that must survive the refusal above: an unregistered suffix
    is bytes, and always was."""
    from publishable import artifacts

    target = tmp_path / "a.bin"
    target.write_bytes(b"\x00\x01")
    assert artifacts.StepIO._read(target) == b"\x00\x01"


def test_a_reader_with_no_writer_is_never_dispatched_to(registries, tmp_path):
    """The reverse of the refusal above, stated rather than left implicit:
    `_suffix_for` decides the suffix from `WRITERS` alone, so a suffix
    `READERS` holds and `WRITERS` does not never reaches that table at
    all — the registered reader is skipped, not consulted and rejected."""
    from publishable import artifacts

    read_calls = []
    artifacts.READERS[".fastq"] = lambda data: read_calls.append(data) or {"read": data}

    target = tmp_path / "a.fastq"
    target.write_bytes(b"raw")

    assert artifacts.StepIO._read(target) == b"raw"
    assert read_calls == []


def test_a_resolver_io_reads_the_input_and_nothing_else(tmp_path):
    """`reference.md` § Where units come from: read-only, `read_input` and
    nothing else. Structural rather than a raise per method — core cannot inspect
    the body of a resolver, so the method must not exist to be called."""
    from publishable.artifacts import ResolverIO

    (tmp_path / "layout.csv").write_text("barcode,well\nA1,h3\n")
    io = ResolverIO(tmp_path)

    assert io.read_input("layout.csv") == [{"barcode": "A1", "well": "h3"}]
    for forbidden in (
        "write",
        "append",
        "record",
        "skip",
        "read_upstream",
        "read_condition",
        "exists",
        "resumed",
        "units",
        "run_dir",
        "step_dir",
    ):
        assert not hasattr(io, forbidden), f"a resolver io must not expose {forbidden}"


def test_a_resolver_io_records_every_path_it_read_in_order(tmp_path):
    """`hash_index` names "the paths the resolver read"; this object is the only
    one that sees a read. Order and duplicate handling are asserted because the
    set task 31 builds is derived from this tuple."""
    from publishable.artifacts import ResolverIO

    (tmp_path / "layout.csv").write_text("barcode\nA1\n")
    (tmp_path / "extra.json").write_text('{"n": 1}')
    io = ResolverIO(tmp_path)

    assert io.read_paths == ()  # the control: nothing read, nothing recorded
    io.read_input("layout.csv")
    io.read_input("extra.json")
    io.read_input("layout.csv")
    assert io.read_paths == ("layout.csv", "extra.json", "layout.csv")


def test_a_resolver_io_reads_through_the_same_table_a_step_does(tmp_path, registries):
    """A plugin's registered reader serves a resolver too — one dispatch, not two.
    Without this, a resolver reading a plugin suffix would get raw bytes while a
    step reading the same file got the parsed object."""
    from publishable.artifacts import ResolverIO
    from publishable.plugins import register_reader, register_writer

    @register_writer(".fq")
    def _write(obj) -> bytes:
        return str(obj).encode()

    @register_reader(".fq")
    def _read(payload: bytes):
        return {"parsed": payload.decode()}

    (tmp_path / "reads.fq").write_bytes(b"ACGT")
    assert ResolverIO(tmp_path).read_input("reads.fq") == {"parsed": "ACGT"}


# ---------------------------------------------------------------------------
# Task 5 — io.reuse_from and the shared _contained helper.
# `docs/superpowers/plans/2026-08-20-lineage.md` task 5; Fixture N (the name
# rule, with its positive control) and Fixture R (a genuinely produced
# upstream).
# ---------------------------------------------------------------------------


def _write_upstream_run(run_dir: Path, run_id: str, *, step: str = "step01") -> None:
    """A synthesized upstream run whose `execution` block declares one
    `run`-scoped step, completed — enough for `resolve_step` to locate
    `shared/<step>/` without a real run behind it."""
    run_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "status": "completed",
        "execution": {
            "shared": {step: {"status": "completed"}},
            "summary": {},
            "conditions": [],
        },
    }
    (run_dir / "run.yaml").write_text(yaml.safe_dump(doc))


def _reuse_io(tmp_path: Path, *, output_dir: "Path | None" = None) -> StepIO:
    """A `StepIO` with a real `UpstreamResolver` injected — the only way
    `reuse_from` is reachable at all, per Decision 2's zero-field surface.
    `step_dir`/`input_dir`/`run_dir` are this (downstream) execution's own
    and play no part in `reuse_from`, which reads only through the resolver.
    """
    resolved_output_dir = output_dir if output_dir is not None else tmp_path / "output_dir"
    resolver = UpstreamResolver(
        output_dir=resolved_output_dir,
        repo_root=tmp_path / "unused_repo_root",
        ledger=UpstreamLedger(),
    )
    return StepIO(
        step_dir=tmp_path / "downstream_step",
        input_dir=tmp_path / "downstream_input",
        run_dir=tmp_path / "downstream_run",
        upstream=resolver,
    )


def test_reuse_from_with_no_upstream_injected_is_a_bare_assert_not_a_coded_refusal():
    """Step 1b: a missing resolver is core's own bug — `runner.py` always
    threads one from `command_run`, so no config or step can cause its
    absence. A bare `AssertionError`, not an `E-UPSTREAM-*` code: minting one
    here would also make task 3's wiring mutation blind (the mutant would
    then raise a code of its own)."""
    io = StepIO(step_dir=Path("/unused"), input_dir=Path("/unused"), run_dir=Path("/unused"))
    with pytest.raises(AssertionError):
        io.reuse_from("run_x", "step01", "out.json")


def test_reuse_from_reads_the_named_artifact_through_the_registered_reader(tmp_path):
    """The positive path underlying every refusal arm below: an ordinary read
    through the resolver, the located step directory, and `_read`'s dispatch."""
    output_dir = tmp_path / "output_dir"
    run_id = "run_2020-01-01T00-00-00Z_sssssss"
    run_dir = output_dir / run_id
    _write_upstream_run(run_dir, run_id)
    (run_dir / "shared" / "step01").mkdir(parents=True)
    (run_dir / "shared" / "step01" / "out.json").write_text('{"x": 1}')
    io = _reuse_io(tmp_path, output_dir=output_dir)
    assert io.reuse_from(run_id, "step01", "out.json") == {"x": 1}


def test_reuse_from_missing_step_directory_and_missing_name_share_one_code(tmp_path):
    """Step 2: ONE code, `E-UPSTREAM-ARTIFACT-MISSING`, for both faults — the
    remedy is identical in each case: the upstream published no such name."""
    output_dir = tmp_path / "output_dir"
    run_id = "run_2020-01-01T00-00-00Z_ttttttt"
    run_dir = output_dir / run_id
    # Declared under `shared` but nothing was ever written to disk for it —
    # the missing-STEP-DIRECTORY half of the fault.
    _write_upstream_run(run_dir, run_id, step="step_never_wrote")
    io = _reuse_io(tmp_path, output_dir=output_dir)
    with pytest.raises(ArtifactError) as e:
        io.reuse_from(run_id, "step_never_wrote", "out.json")
    assert e.value.code == "E-UPSTREAM-ARTIFACT-MISSING"

    # The step directory exists, but not this name within it — the
    # missing-NAME half of the same fault.
    (run_dir / "shared" / "step_never_wrote").mkdir(parents=True)
    with pytest.raises(ArtifactError) as e:
        io.reuse_from(run_id, "step_never_wrote", "out.json")
    assert e.value.code == "E-UPSTREAM-ARTIFACT-MISSING"


def test_reuse_from_inherits_the_shipped_unreadable_suffix_refusal(tmp_path, registries):
    """§ Errors carries one row per code: a writer-without-reader suffix is
    already `E-ARTIFACT-UNREADABLE` (`_read`'s shipped refusal); H8a mints no
    second code for it. Reuses the shipped fixture's own shape."""
    from publishable import artifacts

    artifacts.WRITERS[".fastq"] = lambda rows: b"x"
    output_dir = tmp_path / "output_dir"
    run_id = "run_2020-01-01T00-00-00Z_uuuuuuu"
    run_dir = output_dir / run_id
    _write_upstream_run(run_dir, run_id)
    (run_dir / "shared" / "step01").mkdir(parents=True)
    (run_dir / "shared" / "step01" / "a.fastq").write_bytes(b"x")
    io = _reuse_io(tmp_path, output_dir=output_dir)
    with pytest.raises(ArtifactError) as e:
        io.reuse_from(run_id, "step01", "a.fastq")
    assert e.value.code == "E-ARTIFACT-UNREADABLE"


def test_reuse_from_a_read_that_raises_inside_read_leaves_the_ledger_untouched(
    tmp_path, registries
):
    """Whole-branch review Minor 1. The comment beside `ledger.record` in
    `reuse_from` claims a `_read` raise leaves the ledger untouched, but batch
    5's own mutation (Fixture F's second half, in `test_cli.py`) only tested
    the boundary one line UP from there: `target.exists()` being `False`,
    which raises `E-UPSTREAM-ARTIFACT-MISSING` before `_read` is ever
    reached. Moving `ledger.record` to run BEFORE `_read` rather than after
    it returns leaves that fixture green, because it never gets far enough
    to see the difference.

    This test targets the boundary the comment is actually about: the
    artifact IS there (`target.exists()` is `True`) and `_read` itself
    raises, on the shipped writer-without-reader refusal
    (`E-ARTIFACT-UNREADABLE`) the fixture immediately above already
    reaches. The ledger must hold nothing afterward."""
    from publishable import artifacts

    artifacts.WRITERS[".fastq"] = lambda rows: b"x"
    output_dir = tmp_path / "output_dir"
    run_id = "run_2020-01-01T00-00-00Z_vvvvvvv"
    run_dir = output_dir / run_id
    _write_upstream_run(run_dir, run_id)
    (run_dir / "shared" / "step01").mkdir(parents=True)
    (run_dir / "shared" / "step01" / "a.fastq").write_bytes(b"x")
    io = _reuse_io(tmp_path, output_dir=output_dir)
    with pytest.raises(ArtifactError) as e:
        io.reuse_from(run_id, "step01", "a.fastq")
    assert e.value.code == "E-ARTIFACT-UNREADABLE"
    assert io._upstream is not None
    assert io._upstream.ledger.entries() == []


def test_reuse_from_name_containment_refuses_traversal_absolute_path_and_symlink_escape(
    tmp_path,
):
    """Fixture N's `reuse_from` refusal arms, each targeting a file that
    EXISTS and holds distinguishable content — so an unenforced check would
    return it rather than fail for an unrelated reason (the live probe's own
    shape, `docs/superpowers/specs/2026-08-20-lineage-design.md` Fixture N).
    """
    output_dir = tmp_path / "output_dir"
    run_id = "run_2020-01-01T00-00-00Z_vvvvvvv"
    run_dir = output_dir / run_id
    _write_upstream_run(run_dir, run_id)
    step_dir = run_dir / "shared" / "step01"
    step_dir.mkdir(parents=True)
    io = _reuse_io(tmp_path, output_dir=output_dir)

    # `..` traversal: a file that exists OUTSIDE the run entirely, reached by
    # a relative path with exactly enough `..` segments to escape `step_dir`.
    secret = tmp_path / "secret.json"
    secret.write_text('{"who": "SECRET_DOTDOT"}')
    escape_name = os.path.relpath(secret, step_dir)
    assert ".." in escape_name  # the fixture's own claim: this really escapes
    with pytest.raises(ArtifactError) as e:
        io.reuse_from(run_id, "step01", escape_name)
    assert e.value.code == "E-UPSTREAM-NAME"

    # An absolute path, naming the same existing, distinguishable file.
    with pytest.raises(ArtifactError) as e:
        io.reuse_from(run_id, "step01", str(secret))
    assert e.value.code == "E-UPSTREAM-NAME"

    # Minor 1 (task-b3-review.md): an absolute path pointing INSIDE the step
    # directory itself. The `..` and outside-absolute arms above are each
    # already refused by the `startswith` half of `_contained`'s check
    # (their target sits outside `resolved_base`), so deleting
    # `Path(name).is_absolute() or` from `_contained` leaves them green —
    # this arm is refused ONLY by the absolute-path clause, since its
    # target exists inside the step directory and `startswith` alone would
    # happily return it.
    inside_absolute = step_dir / "ok.json"
    inside_absolute.write_text('{"who": "INSIDE_BUT_ABSOLUTE"}')
    with pytest.raises(ArtifactError) as e:
        io.reuse_from(run_id, "step01", str(inside_absolute))
    assert e.value.code == "E-UPSTREAM-NAME"

    # A symlink inside the step directory leading outside it.
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "leak.json").write_text('{"who": "SECRET_SYMLINK"}')
    link = step_dir / "escape_dir"
    link.symlink_to(outside_dir, target_is_directory=True)
    with pytest.raises(ArtifactError) as e:
        io.reuse_from(run_id, "step01", "escape_dir/leak.json")
    assert e.value.code == "E-UPSTREAM-NAME"
    assert not (outside_dir / "leak.json.reused").exists()  # nothing written back


def test_reuse_from_positive_control_a_forward_separator_and_an_interior_dot_still_read(
    tmp_path,
):
    """Fixture N's positive control, not optional per controller ruling 1: a
    helper that refused every separator would pass the three refusal arms
    above and still be the over-refusal the ruling forbids. Two legal names:
    `programs/a.json` (a forward separator, § Steps and artifacts' own worked
    shape) and `programs/gpt-4.1__seed29.json`, whose interior dot must still
    dispatch as `.json`, not as some suffix ending in `.1`.
    """
    output_dir = tmp_path / "output_dir"
    run_id = "run_2020-01-01T00-00-00Z_wwwwwww"
    run_dir = output_dir / run_id
    _write_upstream_run(run_dir, run_id)
    programs = run_dir / "shared" / "step01" / "programs"
    programs.mkdir(parents=True)
    (programs / "a.json").write_text('{"a": 1}')
    (programs / "gpt-4.1__seed29.json").write_text('{"b": 2}')
    io = _reuse_io(tmp_path, output_dir=output_dir)
    assert io.reuse_from(run_id, "step01", "programs/a.json") == {"a": 1}
    assert io.reuse_from(run_id, "step01", "programs/gpt-4.1__seed29.json") == {"b": 2}


# --- Fixture R: a genuinely produced upstream, read through reuse_from -------

_SUMMARY_PUBLISH_STEP = """\
# generated for the H8a task 5 Fixture R test
from publishable import BaseStep


class Step(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        io.write("programs/a.json", {{"program": "a"}})
        io.write("programs/b.json", {{"program": "b"}})
        io.write("programs/c.json", {{"program": "c"}})
        return {{}}
"""


def test_fixture_r_reuse_from_reads_a_genuinely_produced_summary_artifact(tmp_path):
    """Fixture R for task 5: a real end-to-end `run` (`run_a_project`) with a
    `summary`-scoped step that publishes `programs/{a,b,c}.json`; `reuse_from`
    (through the absolute locator form, Decision 1) reads one back. The step
    name is read from the upstream's own `execution.summary` block rather
    than hard-coded — `run_a_project` prefixes a generated step's name
    (Global Constraints correction 8), so a literal would be a guessed one.
    """
    from tests.test_cli import run_a_project

    project = run_a_project(
        tmp_path,
        replication={"repeats": [{"kind": "seed", "n": 1}]},
        units=8,
        extra_steps=["publish"],
        extra_step_source=_SUMMARY_PUBLISH_STEP,
    )
    run_dir = project["run_dir"]
    record = yaml.safe_load((run_dir / "run.yaml").read_text())
    summary_steps = record["execution"]["summary"]
    assert len(summary_steps) == 1  # the fixture's own claim: exactly the one we added
    step_name = next(iter(summary_steps))

    io = _reuse_io(tmp_path)  # output_dir is irrelevant: the absolute form ignores it
    assert io.reuse_from(str(run_dir), step_name, "programs/a.json") == {"program": "a"}


# ---------------------------------------------------------------------------
# H8c task 17: the guard pin, arm C — the artifact paths `read_condition`
# resolves, through a real `summary` step, at three repeats and again at
# one. Captured by running, at `7f04755`. NEVER MOVES IN THIS SLICE: task 2
# rewrites `read_condition`'s traversal (design Decision 4, plan correction
# 2), and this arm asserts on the VALUE READ, never on a constructed path,
# so it pins the answer rather than the construction that produces it.
# See `docs/superpowers/plans/2026-08-21-report-study.md` task 17.
# ---------------------------------------------------------------------------


def _h8c_arm_c_build_and_run(tmp_path: Path, n_repeats: int) -> dict:
    """One real project: a condition-scoped step `step02_fit` writes
    `model.json`; the generated (repeat-scoped) starter writes
    `units.parquet` via `io.record`, as every starter step does; a
    `summary`-scoped `step03_compare` reads both back through
    `io.read_condition` — the condition-scoped artifact without naming a
    repeat, the repeat-scoped one naming `io.repeats[0]`, exactly the
    documented pattern. Returns the run directory and the parsed record.
    """
    import subprocess

    from publishable.cli import main
    from publishable.generators.experiment import generate_experiment
    from publishable.generators.step import generate_step

    root = tmp_path / "proj"
    data = tmp_path / "data"
    results = tmp_path / "results"
    data.mkdir(parents=True)
    rows = "\n".join(f"p{i}" for i in range(10))
    (data / "index.csv").write_text(f"patient_id\n{rows}\n")
    assert main(["new", str(root)]) == 0
    cfg = generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(data),
        output_dir=str(results),
    )
    generate_step(repo_root=root, experiment="cohort-pilot", step_name="fit")
    (root / "src" / "cohort_pilot" / "steps" / "step02_fit.py").write_text(
        "from publishable import BaseStep\n\n\n"
        "class Step(BaseStep):\n"
        '    scope = "condition"\n\n'
        "    def run(self, cfg, io):\n"
        '        io.write("model.json", {"m": cfg.parameters.analysis.method})\n'
        "        return {}\n"
    )
    generate_step(repo_root=root, experiment="cohort-pilot", step_name="compare")
    (root / "src" / "cohort_pilot" / "steps" / "step03_compare.py").write_text(
        "from publishable import BaseStep\n\n\n"
        "class Step(BaseStep):\n"
        '    scope = "summary"\n\n'
        "    def run(self, cfg, io):\n"
        "        repeat = io.repeats[0]\n"
        '        model = io.read_condition(0, "step02_fit", "model.json")\n'
        "        units = io.read_condition(\n"
        '            0, "step01_summarize_units", "units.parquet", repeat=repeat\n'
        "        )\n"
        '        return {"model_m": model["m"], "n_rows": len(units)}\n'
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "H8c arm C"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    doc["replication"] = {"repeats": [{"kind": "seed", "n": n_repeats}]}
    cfg.write_text(yaml.safe_dump(doc))
    for args in (
        ["add", "."],
        ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "arm c"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)
    assert main(["run", str(cfg)]) == 0
    run_dir = next(results.glob("run_*"))
    record = yaml.safe_load((run_dir / "run.yaml").read_text())
    return {"run_dir": run_dir, "record": record}


def test_h8c_arm_c_read_condition_resolves_at_three_repeats_and_at_one(tmp_path: Path):
    """Arm C. Two real runs, identical but for the repeat count, each read
    back through the SAME `summary` step and the SAME two `io.read_condition`
    calls — one for a condition-scoped artifact (no `repeat=`), one for a
    repeat-scoped artifact (`repeat=io.repeats[0]`). The assertion is on the
    VALUE `step03_compare` returned into `results.summary`, never on a path
    either test constructs: `_nest_repeat`'s collapse at one repeat and its
    nesting at three are both exercised, by running, without this test
    needing to know which directory shape either one produces.
    """
    three = _h8c_arm_c_build_and_run(tmp_path / "three", 3)
    one = _h8c_arm_c_build_and_run(tmp_path / "one", 1)

    for built in (three, one):
        summary = built["record"]["results"]["summary"]["step03_compare"]
        assert summary == {"model_m": "pearson", "n_rows": 10}


# ---------------------------------------------------------------------------
# H5a task 13: the guard pin's arms B and C — both encoders' bytes through a
# real `StepIO.write`, and the two shipped type-clash refusals through that
# same real call rather than through `_encode_parquet` directly. Captured by
# running, at `804271c` (`main`, clean tree, before H5a's own first task).
# `docs/superpowers/plans/2026-08-21-artifacts-write-side.md` task 13;
# `docs/superpowers/specs/2026-08-21-artifacts-write-side-design.md`.
#
# Arm A (a real run's `units.parquet`) and arm D (the worked example's own
# text) live in `tests/test_cli.py`, because arm A needs a real `run` and
# arm D needs no artifact at all — this file's fixtures build a `StepIO`
# directly, which is the surface both arms below actually exercise.
# ---------------------------------------------------------------------------

_H5A_ARM_B_ROWS = [
    {"i": 1, "f": 1.5, "s": "hello", "b": True, "n": None},
    {"i": 2, "f": 2.5, "s": "world", "b": False, "n": None},
]


def test_h5a_arm_b1_the_csv_golden_bytes_never_move_in_this_slice(tmp_path: Path):
    """Arm B1 — `.csv` GOLDEN BYTES. NEVER MOVE IN THIS SLICE.

    One row set of Python scalars covering `int`, `float`, `str`, `bool` and
    `None`, written through a real `StepIO.write` and read back as bytes.
    Deterministic: `csv` is stdlib and no library version is in the path, so
    this is the same guarantee `test_a_mixed_int_and_float_column_promotes_to_float_deliberately`
    and its siblings already rest on, made a byte-level pin rather than a
    round-trip assertion.
    """
    io = make_io(tmp_path)
    path = io.write("golden.csv", _H5A_ARM_B_ROWS)
    assert path.read_bytes() == (b"i,f,s,b,n\n1,1.5,hello,True,\n2,2.5,world,False,\n")


def test_h5a_arm_b2_the_parquet_golden_sha256_is_a_tripwire(tmp_path: Path):
    """Arm B2 — `.parquet` GOLDEN sha256. A TRIPWIRE, edit conditions STATED
    IN ADVANCE and NOT left to judgement.

    This hex is coupled to the `pyarrow` `uv.lock` pins, not to this file's
    source. If it fails: arm A
    (`test_h5a_arm_a_a_real_runs_units_parquet_column_order_values_and_types`
    in `tests/test_cli.py`) is what tells you which fault you have — arm A
    green and this red means the library moved; both red means the coercion
    moved a legal artifact. It may be recaptured ONLY when `uv.lock`'s
    `pyarrow` entry changed in the same commit, and only with arm A green.
    NO TASK IN H5a MAY EDIT IT: no task in this slice touches `uv.lock`.
    """
    io = make_io(tmp_path)
    path = io.write("golden.parquet", _H5A_ARM_B_ROWS)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == "c003934b92fed035aa70dc8e8ea04b336a9c27aedfa64196cba4b440dabcea3e"


def test_h5a_arm_c_the_two_shipped_type_clashes_through_a_real_io_write(tmp_path: Path):
    """Arm C — the shapes that must keep raising, through a real `io.write`
    rather than through `_encode_parquet` directly.

    The bool/int and str/int refusals themselves are ALREADY pinned by
    `test_a_bool_and_int_column_clash_raises_rather_than_coercing` and
    `test_a_str_and_int_column_clash_raises_rather_than_coercing`
    (grepped, not assumed — both call `_encode_parquet` directly). What
    this arm adds: the same two shapes through `StepIO.write`, so a later
    `except ContractError` wrapper around `io.write`'s dispatch (task 9)
    cannot swallow or re-code them — and the assertions are on the code and
    on the column name and both type names as SUBSTRINGS, never on the whole
    message, `startswith`, or the surface clause `"io.record's values, a
    step's return, and a template's aggregate..."` — task 9 is authorized to
    delete that clause and to prefix the artifact name onto the message, and
    a golden literal here would fail an arm this plan gives no editor.
    """
    io_bool = make_io(tmp_path)
    with pytest.raises(ContractError) as e_bool:
        io_bool.write("clash.parquet", [{"v": True}, {"v": 1}])
    assert e_bool.value.code == "E-STEP-RETURN-TYPE"
    assert "'v'" in str(e_bool.value)
    assert "bool" in str(e_bool.value)
    assert "int" in str(e_bool.value)

    io_str = make_io(tmp_path)
    with pytest.raises(ContractError) as e_str:
        io_str.write("clash.parquet", [{"v": "x"}, {"v": 1}])
    assert e_str.value.code == "E-STEP-RETURN-TYPE"
    assert "'v'" in str(e_str.value)
    assert "str" in str(e_str.value)
    assert "int" in str(e_str.value)


# ---------------------------------------------------------------------------
# H5a task 13, arm E: added to the dispatch by the controller after this
# branch's brief was extracted, because it derives from the design's SECOND
# controller ruling ("Decision 5 is narrowed..."), which post-dates the plan
# the brief was cut from. The brief could not carry it — only the dispatch
# could, and it still had to be repeated as an explicit correction, which is
# itself worth carrying: a dispatch-only instruction competes with a brief
# and can lose. See the report's added note.
#
# Fix round 1, Major 1: the original single test was labelled "NO AUTHORIZED
# EDITOR" while its own docstring said task 9 IS authorized to change the
# `.csv` half — those two statements cannot both stand, and plan task 9 step
# 5 (Fixture S) builds exactly that refusal while step 8's expected-green
# list is A/B1/B2/C, arm E absent because the plan predates it. Split in two:
# arm E1 (`.parquet`, genuinely no editor) and arm E2 (`.csv`, task 9 named
# as its SOLE editor, with the post-edit state stated in advance — H8a arm
# B's precedent for a pin one task is allowed to move).
# ---------------------------------------------------------------------------


def test_h5a_arm_e1_parquet_keeps_a_structural_or_bytes_cell_intact(tmp_path: Path):
    """Arm E1 — `.parquet` round-trips a structural or `bytes` cell
    BYTE-FAITHFULLY, from the second controller ruling
    (`docs/superpowers/specs/2026-08-21-artifacts-write-side-design.md`):
    "`.parquet` accepts both, because it *can* return them, byte-faithfully.
    No refusal is added there." A capability this slice's design promises to
    KEEP, not merely leaves unbroken.

    NO AUTHORIZED EDITOR, for real this time: no task in H5a narrows what
    `.parquet` accepts. If either assertion below fires, that is a finding.

    Every assertion checks the returned value's TYPE as well as its value —
    `[1, 2] == [1.0, 2.0]` is already `True`, so the list cell's own element
    types are checked too (fix round 1, Minor 2: the first cut asserted only
    the outer `list`/`bytes` type, and a mutation promoting the list's
    elements from `int` to `float` left it green).
    """
    from publishable.artifacts import _decode_parquet

    io = make_io(tmp_path)

    pq_list = _decode_parquet(io.write("e_list.parquet", [{"v": [1, 2]}]).read_bytes())
    assert pq_list == [{"v": [1, 2]}]
    assert type(pq_list[0]["v"]) is list
    assert [type(x) for x in pq_list[0]["v"]] == [int, int]

    pq_bytes = _decode_parquet(io.write("e_bytes.parquet", [{"v": b"x"}]).read_bytes())
    assert pq_bytes == [{"v": b"x"}]
    assert type(pq_bytes[0]["v"]) is bytes


def test_h5a_arm_e2_csv_refuses_a_structural_or_bytes_cell(tmp_path: Path):
    """Arm E2 — POST-TASK-9 state, stated in advance by plan task 9 step 5
    (Fixture S) and now built: `.csv` cannot return a structural or `bytes`
    cell intact (the pre-task-9 state this test used to pin was `"[1, 2]"`
    and `"b'x'"` — silent corruption), so it now refuses instead, converting
    that corruption into a loud `ContractError` · `E-STEP-RETURN-TYPE`
    naming the column and the artifact — the same shape
    `test_h5a_arm_c_the_two_shipped_type_clashes_through_a_real_io_write`
    above already asserts by substring.

    TASK 9 WAS the sole authorized editor of this test; no other task may
    edit it further without a fresh ruling. A `.csv` write returning an
    actual `list` or `bytes` object, rather than raising, is a finding
    regardless of which task is running.
    """
    io_list = make_io(tmp_path)
    with pytest.raises(ContractError) as e_list:
        io_list.write("e_list.csv", [{"v": [1, 2]}])
    assert e_list.value.code == "E-STEP-RETURN-TYPE"
    assert "'v'" in str(e_list.value)
    assert "e_list.csv" in str(e_list.value)

    io_bytes = make_io(tmp_path)
    with pytest.raises(ContractError) as e_bytes:
        io_bytes.write("e_bytes.csv", [{"v": b"x"}])
    assert e_bytes.value.code == "E-STEP-RETURN-TYPE"
    assert "'v'" in str(e_bytes.value)
    assert "e_bytes.csv" in str(e_bytes.value)


def test_h5a_fixture_s_csv_refuses_a_structural_cell_on_either_side_of_the_row_set(
    tmp_path: Path,
):
    """Fixture S — `.csv` only: `.parquet`'s side of this fixture is arm E1
    above (no authorized editor; a structural cell keeps round-tripping
    there). A `[1, 2]` cell in the FIRST row of a three-row set, and one in
    the LAST row of another three-row set — the decoy-sort-position trap in
    its row-order form (`CLAUDE.md` § Writing checks that can fail): a check
    that stops at the first offending row, or one that only ever sees a
    first-row offender in its fixture, cannot tell "checks every row" from
    "checks the first row". Each arm asserts the refusal names the column,
    the row index, and the artifact.
    """
    io_first = make_io(tmp_path)
    with pytest.raises(ContractError) as e_first:
        io_first.write("s_first.csv", [{"v": [1, 2]}, {"v": 1}, {"v": 2}])
    assert e_first.value.code == "E-STEP-RETURN-TYPE"
    assert "'v'" in str(e_first.value)
    assert "row 0" in str(e_first.value)
    assert "s_first.csv" in str(e_first.value)

    io_last = make_io(tmp_path)
    with pytest.raises(ContractError) as e_last:
        io_last.write("s_last.csv", [{"v": 1}, {"v": 2}, {"v": [1, 2]}])
    assert e_last.value.code == "E-STEP-RETURN-TYPE"
    assert "'v'" in str(e_last.value)
    assert "row 2" in str(e_last.value)
    assert "s_last.csv" in str(e_last.value)


def test_h5a_fixture_n_a_non_mapping_row_refuses_with_the_documented_code(
    tmp_path: Path,
):
    """Fixture N — a row that is not a mapping, for both row-shaped
    writers. Before this task: a bare `AttributeError` out of `_encode_csv`
    and a bare `TypeError` out of `_encode_parquet` (measured at `d2caacf`).
    Now: `ArtifactError` · `E-ARTIFACT-UNWRITABLE`, which
    `docs/reference.md` § Steps and artifacts already promised for "handing
    a writer anything else". Asserting the exception CLASS (via
    `pytest.raises(ArtifactError)`, which does not catch a bare
    `AttributeError`/`TypeError`) is the claim, not merely the code.
    """
    for suffix in (".csv", ".parquet"):
        io_bad = make_io(tmp_path)
        with pytest.raises(ArtifactError) as e:
            io_bad.write(f"n_bad{suffix}", [{"v": 1.0}, "not a mapping"])
        assert e.value.code == "E-ARTIFACT-UNWRITABLE"


def test_h5a_fixture_n_control_the_same_rows_without_the_offender_write(
    tmp_path: Path,
):
    """Fixture N's control — without it, the refusal arm above would pass
    equally well if `io.write` silently wrote nothing at all. Same row set
    with the non-mapping element removed: the write must succeed and the
    artifact must exist, for both formats.
    """
    for suffix in (".csv", ".parquet"):
        io_good = make_io(tmp_path)
        path = io_good.write(f"n_good{suffix}", [{"v": 1.0}])
        assert path.exists()


def test_h5a_step7_local_pin_parquet_coerces_numpy_float64_beside_float(
    tmp_path: Path,
):
    """Local pin for task 9 step 7 mutation (i): with `_encode_parquet`'s
    call to `_coerced_rows` removed, `np.float64` beside a plain `float` in
    the same column raises `E-STEP-RETURN-TYPE` rather than writing — the
    spurious refusal Decision 5 retires (measured at `d2caacf`: that exact
    input raises today, and after this task it writes). Task 11's own
    Fixture W re-measures this across the whole cross-format matrix; this
    is THIS task's own commit pinned in the meantime, so a reviewer does
    not have to wait for a later task to know the mutation is caught.
    """
    from publishable.artifacts import _decode_parquet

    io_ = make_io(tmp_path)
    path = io_.write("w_local.parquet", [{"v": np.float64(1.5)}, {"v": 1.5}])
    rows = _decode_parquet(path.read_bytes())
    assert rows == [{"v": 1.5}, {"v": 1.5}]
    assert all(type(r["v"]) is float for r in rows)


# ---------------------------------------------------------------------------
# H5a task 11: Fixture W, Fixture E, Fixture B's cross-spelling arm, and the
# whole-branch mutation re-run (`docs/superpowers/plans/2026-08-21-artifacts-
# write-side.md` task 11). Nothing below is new production code — the only
# product of this task is pins, and the mutation re-run is reported in
# `.superpowers/sdd/2026-08-21-artifacts-write-side/task-11-report.md`.
#
# Both encoders were measured directly (not assumed) before writing any of
# this, at the commit this task started from:
#   - `.parquet` decodes to the INPUT ROWS AS COERCED (int/float promoted to
#     float via `_check_column_types`'s grouping plus pyarrow's own table
#     construction; a NumPy scalar unwrapped to its Python counterpart).
#   - `.csv` decodes every cell to `str(coerced_value)` — measured for every
#     arm below, including int-beside-float, which does NOT promote for
#     `.csv`: `_encode_csv` never calls `_check_column_types` at all
#     (§ Corrections, correction 8 — cross-row unification is a `.parquet`
#     rule only), so the two formats disagree on this arm for a second,
#     independent reason from correction 2's `str()` rule.
# ---------------------------------------------------------------------------

_H5A_FIXTURE_W_ARMS: dict[str, list[dict[str, Any]]] = {
    "homogeneous_float": [{"v": 1.5}, {"v": 2.5}],
    "np_float64_beside_float": [{"v": np.float64(1.5)}, {"v": 2.5}],
    "np_str_beside_str": [{"v": np.str_("a")}, {"v": "b"}],
    "np_bool_beside_bool": [{"v": np.bool_(True)}, {"v": False}],
}


def test_h5a_fixture_w_parquet_round_trip_per_arm(tmp_path: Path):
    """Fixture W, `.parquet` half. Rows built here, written through a real
    `StepIO.write`, read back through the registered reader, and compared to
    the INPUT ROWS AS COERCED — never to a hand-written expectation, so the
    claim is the round trip and not a literal someone typed. `coerce_scalars`
    is called directly on each arm's own rows to compute the expectation,
    which is the same coercion `_coerced_rows(keep_structural=True)` applies
    before handing rows to pyarrow.

    Four arms here share one rule (decoded == coerced, type for type); the
    fifth arm, int-beside-float, promotes and gets its own test below because
    the promoted value is no longer equal to the merely-coerced one.
    """
    from publishable.artifacts import _decode_parquet
    from publishable.coercion import coerce_scalars

    io_ = make_io(tmp_path)
    for name, rows in _H5A_FIXTURE_W_ARMS.items():
        path = io_.write(f"fixture_w_{name}.parquet", rows)
        decoded = _decode_parquet(path.read_bytes())
        expected = [coerce_scalars(dict(row), "fixture w") for row in rows]
        assert decoded == expected, name
        for d_row, e_row in zip(decoded, expected, strict=True):
            assert type(d_row["v"]) is type(e_row["v"]), name


def test_h5a_fixture_w_parquet_int_beside_float_promotes(tmp_path: Path):
    """Fixture W's fifth `.parquet` arm: `int` beside `float`. Every decoded
    value is asserted to be a `float` **by `isinstance` over the decoded
    rows** — the promotion, computed rather than written down as a literal —
    and the decoded values equal the coerced rows with each promoted to
    `float`, also computed rather than hand-typed.
    """
    from publishable.artifacts import _decode_parquet
    from publishable.coercion import coerce_scalars

    io_ = make_io(tmp_path)
    rows = [{"v": 1}, {"v": 2.5}]
    path = io_.write("fixture_w_int_beside_float.parquet", rows)
    decoded = _decode_parquet(path.read_bytes())
    coerced = [coerce_scalars(dict(row), "fixture w") for row in rows]
    promoted = [{"v": float(row["v"])} for row in coerced]
    assert decoded == promoted
    assert all(isinstance(row["v"], float) for row in decoded)


def test_h5a_fixture_w_csv_round_trip_compares_to_str_of_coerced(tmp_path: Path):
    """Fixture W, `.csv` half. **Correction 2**: `_decode_csv` returns a
    `str` for every value — measured: `[{"v": 1.0}]` reads back
    `[{'v': '1.0'}]` — so this compares each decoded cell to
    `str(coerced_value)`, never to the coerced value itself. Asserting
    equality with the coerced value would fail for every arm here, because
    `.csv`'s reader gives back a string regardless of what was written
    (`docs/reference.md` § Steps and artifacts' split `.csv`/`.parquet` row).

    This covers all FIVE arms, including int-beside-float: unlike
    `.parquet`, `.csv` never promotes — `_encode_csv` does not call
    `_check_column_types` — so `1` stays `str(1) == '1'` rather than
    `str(1.0) == '1.0'`, measured directly before writing this assertion.
    """
    from publishable.artifacts import _decode_csv
    from publishable.coercion import coerce_scalars

    arms = dict(_H5A_FIXTURE_W_ARMS)
    arms["int_beside_float"] = [{"v": 1}, {"v": 2.5}]

    io_ = make_io(tmp_path)
    for name, rows in arms.items():
        path = io_.write(f"fixture_w_{name}.csv", rows)
        decoded = _decode_csv(path.read_bytes())
        coerced = [coerce_scalars(dict(row), "fixture w") for row in rows]
        expected = [{"v": str(row["v"])} for row in coerced]
        assert decoded == expected, name


def test_h5a_fixture_b_cross_spelling_true_by_construction_not_a_pin(tmp_path: Path):
    """Fixture B — the NumPy-spelled and Python-spelled versions of one
    column, written to two artifacts, and the two files' **bytes** compared.
    Both formats.

    **Declared weak here, on purpose, because it is:** after coercion, the
    NumPy-spelled row set and the Python-spelled one become the SAME coerced
    rows, so byte equality between the two artifacts is true BY CONSTRUCTION
    — this arm can only fail if coercion is absent, which is exactly what
    Fixture W's own arms above already catch by a more direct route (a round
    trip against a real expectation, not a same-input-twice comparison). This
    arm discriminates *coercion present* from *coercion deleted* and nothing
    finer.

    **The claim "a legal run's artifacts are byte-identical" (controller
    requirement 2) is pinned by task 13's arms A, B1 and B2, and by NOTHING
    here.** Written down so this arm is never read as satisfying that
    requirement — `docs/superpowers/plans/2026-08-21-artifacts-write-side.md`
    § Corrections, correction 2, names task 13's arms as the only ones that
    capture bytes BEFORE this slice's change, which is the only thing that
    can pin a claim about what MOVED.
    """
    rows_np = [{"v": np.float64(1.5)}, {"v": np.float64(2.5)}]
    rows_py = [{"v": 1.5}, {"v": 2.5}]

    io_csv = make_io(tmp_path)
    p_np_csv = io_csv.write("fixture_b_np.csv", rows_np)
    p_py_csv = io_csv.write("fixture_b_py.csv", rows_py)
    assert p_np_csv.read_bytes() == p_py_csv.read_bytes()

    io_pq = make_io(tmp_path)
    p_np_pq = io_pq.write("fixture_b_np.parquet", rows_np)
    p_py_pq = io_pq.write("fixture_b_py.parquet", rows_py)
    assert p_np_pq.read_bytes() == p_py_pq.read_bytes()


def test_h5a_fixture_e_empty_row_list_writes_an_empty_table_and_raises_nothing(
    tmp_path: Path,
):
    """Fixture E, first arm: an empty row list writes an empty table and
    raises nothing. Both formats. This is one of the arms a coercion change
    is most likely to break silently — an empty sequence never reaches a
    single value-coercing branch, so a walk that assumed at least one row
    could raise on `rows[0]` or similar and this is the arm that would catch
    it. Asserted on the decoded rows.
    """
    from publishable.artifacts import _decode_csv, _decode_parquet

    io_ = make_io(tmp_path)
    csv_path = io_.write("fixture_e_empty.csv", [])
    assert _decode_csv(csv_path.read_bytes()) == []
    pq_path = io_.write("fixture_e_empty.parquet", [])
    assert _decode_parquet(pq_path.read_bytes()) == []


def test_h5a_fixture_e_all_none_column_parquet_round_trips_as_none(tmp_path: Path):
    """Fixture E, second arm, `.parquet` half: a column whose every value is
    `None` round-trips as `None` in every row, asserted on the decoded rows.
    """
    from publishable.artifacts import _decode_parquet

    io_ = make_io(tmp_path)
    rows = [{"v": None}, {"v": None}]
    path = io_.write("fixture_e_none.parquet", rows)
    assert _decode_parquet(path.read_bytes()) == [{"v": None}, {"v": None}]


def test_h5a_fixture_e_all_none_column_csv_round_trips_as_empty_string_not_none(
    tmp_path: Path,
):
    """Fixture E, second arm, `.csv` half — and a THIRD instance of
    correction 2's asymmetry, found by measuring rather than by trusting the
    design's own wording. § The discriminating fixtures' Fixture E says a
    `None` column "round-trips as `None` in every row. Both formats" — that
    is false of `.csv`, measured directly: `csv.DictWriter` writes a `None`
    cell as an empty string (not the text `"None"`, and not `None` itself),
    and `csv.DictReader` gives that empty string straight back. So the
    `.csv` decoded row is `{"v": ""}`, never `{"v": None}`. This is not
    `str()` of the coerced value either (`str(None) == "None"`, not `""`) —
    it is the `csv` module's own special-casing of `None`, a THIRD distinct
    `.csv` behaviour beyond correction 2's `str()` rule and correction 8's
    "no cross-row unification," found here because Fixture E's own claim was
    checked against the code rather than carried. Filed for task 12 to
    correct in the design/plan text; not edited here, since editing the
    development record is not this task's job.
    """
    from publishable.artifacts import _decode_csv

    io_ = make_io(tmp_path)
    rows = [{"v": None}, {"v": None}]
    path = io_.write("fixture_e_none.csv", rows)
    assert _decode_csv(path.read_bytes()) == [{"v": ""}, {"v": ""}]
