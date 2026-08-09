# tests/test_artifacts.py
from pathlib import Path

import pytest

from publishable import ArtifactError, ArtifactExistsError
from publishable.artifacts import StepIO, write_atomic


@pytest.fixture
def io(tmp_path: Path) -> StepIO:
    step_dir = tmp_path / "run" / "shared" / "step01"
    step_dir.mkdir(parents=True)
    (tmp_path / "input").mkdir()
    return StepIO(step_dir=step_dir, input_dir=tmp_path / "input", run_dir=tmp_path / "run")


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
    from publishable.artifacts import WRITERS

    WRITERS[".fastq.gz"] = lambda obj: obj if isinstance(obj, bytes) else obj.encode()
    try:
        target = io.write("reads.fastq.gz", b"seqdata")
        assert target.name == "reads.fastq.gz"
        assert target.read_bytes() == b"seqdata"
    finally:
        del WRITERS[".fastq.gz"]


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
