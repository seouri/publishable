"""H9c — `reproduce`. Fixture S, the operand discrimination (design § 9).

Every literal here is either computed in the test or read back out of the
artifact the fixture built. The two `run`-driven fixtures come from
`tests.test_cli`'s `run_a_project`, the one end-to-end driver this suite has —
re-inventing the scaffold-and-commit dance is how a fixture drifts from what
`run` actually writes.
"""

import subprocess
from pathlib import Path

import pytest
import yaml
from tests.test_cli import run_a_project

import publishable.reproduce as reproduce_module
from publishable.cli import main
from publishable.diagnostics import EXIT_EXTERNAL, EXIT_OK, EXIT_WRONG, Collector
from publishable.hashes import code_hash_of, hashed_files
from publishable.provenance import unignored_under_hashed_trees
from publishable.reproduce import (
    _CLONE_CONFIG,
    Checkout,
    ConfigOperand,
    Record,
    Refused,
    classify_operand,
    destination_for,
    prepare_checkout,
)
from publishable.study import study_add, study_new


def _a_run(tmp_path: Path) -> dict:
    return run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 1}]}, units=10)


def _classify(path: Path, credentials: dict[str, str] | None = None):
    """Classify, and hand back the collector so a test can assert on findings.

    The collector is built fresh per call and carries credentials when the test
    gives it any — design correction 21: `main`'s `except PublishableError`
    handler applies NO redaction pass, so a refusal that travelled as an
    exception would reach a reader un-redacted. Every arm below therefore
    asserts on `c.findings`, and the arms assert that nothing was RAISED by
    reaching that assertion at all.
    """
    c = Collector(credentials=dict(credentials or {}))
    return classify_operand(path, c), c


def _codes(c: Collector) -> list[str]:
    return [f.code for f in c.findings]


def _messages(c: Collector) -> str:
    return "\n".join(f.message for f in c.findings)


# --- The honouring, first. Three accepted forms. ---------------------------
# `Testing the refusal, never the honouring` is a shape this repo has paid for
# more than once, and a discrimination test made only of refusals cannot tell
# a working reader from one that refuses everything.


def test_a_run_directorys_own_run_yaml_is_accepted_as_a_record(tmp_path: Path):
    doc = _a_run(tmp_path)
    operand, c = _classify(doc["run_dir"] / "run.yaml")
    assert isinstance(operand, Record)
    assert c.findings == []
    assert (
        operand.doc["run_id"] == yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())["run_id"]
    )
    assert operand.path == doc["run_dir"] / "run.yaml"


def test_a_bundle_member_named_main_run_yaml_is_accepted_as_a_record(tmp_path: Path):
    """Ruling Y's cost-if-wrong, as a test rather than a sentence.

    A bundle member is `main.run.yaml`. This is the arm the basename mutation
    (`endswith("run.yaml")`) fails, and it is the form a reader holding a
    published bundle — the case `study` exists to serve — actually has.
    """
    doc = _a_run(tmp_path)
    bundle = tmp_path / "study"
    study_new(bundle, "Fixture S")
    study_add(bundle, doc["run_dir"] / "run.yaml", "main")
    member = bundle / "main.run.yaml"
    assert member.name != "run.yaml", member.name

    operand, c = _classify(member)
    assert isinstance(operand, Record)
    assert c.findings == []
    assert operand.doc["run_id"] == yaml.safe_load(member.read_text())["run_id"]


def test_a_config_file_is_accepted_as_a_config_operand(tmp_path: Path):
    doc = _a_run(tmp_path)
    operand, c = _classify(doc["cfg"])
    assert isinstance(operand, ConfigOperand)
    assert c.findings == []
    assert operand.path == doc["cfg"]


# --- Fixture S: the five refusals. ----------------------------------------


def test_fixture_s_arm_1_a_run_directory_is_refused_and_names_its_run_yaml(tmp_path: Path):
    """Arm 1. `resume` takes a directory; `reproduce` takes the file in it, and
    the message supplies the component the user is missing."""
    doc = _a_run(tmp_path)
    operand, c = _classify(doc["run_dir"])
    assert operand is None
    assert _codes(c) == ["E-REPRODUCE-OPERAND"]
    assert str(doc["run_dir"] / "run.yaml") in _messages(c)


def test_fixture_s_arm_2_a_study_yaml_is_refused_listing_both_members(tmp_path: Path):
    """Arm 2. TWO members, on purpose: a one-member bundle cannot distinguish
    *lists the members* from *names the first*, so the count-instead-of-names
    mutation would pass against one.

    The two names are asserted individually AND the count `2` is asserted
    absent from the message, because a message reading "2 members" would
    otherwise satisfy an `in` check on neither name.
    """
    first = _a_run(tmp_path / "a")
    second = _a_run(tmp_path / "b")
    bundle = tmp_path / "study"
    study_new(bundle, "Fixture S")
    study_add(bundle, first["run_dir"] / "run.yaml", "main")
    study_add(bundle, second["run_dir"] / "run.yaml", "sensitivity")
    assert sorted(yaml.safe_load((bundle / "study.yaml").read_text())["runs"]) == [
        "main",
        "sensitivity",
    ]

    operand, c = _classify(bundle / "study.yaml")
    assert operand is None
    assert _codes(c) == ["E-REPRODUCE-BUNDLE"]
    message = _messages(c)
    assert "`main.run.yaml`" in message, message
    assert "`sensitivity.run.yaml`" in message, message
    assert "2" not in message, message


def test_fixture_s_arm_2b_a_freshly_created_empty_bundle_says_it_holds_none(tmp_path: Path):
    """Arm 2's other end, which the two-member arm cannot reach: `study new`
    writes `runs: {}`, and an empty list rendered as a list reads as naming
    nothing at all rather than as an answer."""
    bundle = tmp_path / "study"
    study_new(bundle, "Fixture S")
    operand, c = _classify(bundle / "study.yaml")
    assert operand is None
    assert _codes(c) == ["E-REPRODUCE-BUNDLE"]
    assert "holds no runs yet" in _messages(c)


def test_fixture_s_arm_3_a_record_with_run_id_deleted_is_not_read_as_a_config(tmp_path: Path):
    """Arm 3, and it is the arm the *read a `run_id`-less mapping as a config*
    mutation fails.

    The file keeps `provenance` and `results` and loses only `run_id`, so the
    two readings genuinely differ: refused as an edited record, or read as a
    config. It carries no `experiment_type`, so the message is what separates
    them — a reader sent to "this is not a config" would go and look at the
    wrong file.
    """
    doc = _a_run(tmp_path)
    record = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert "provenance" in record and "results" in record
    del record["run_id"]
    edited = tmp_path / "edited.run.yaml"
    edited.write_text(yaml.safe_dump(record, sort_keys=False))

    operand, c = _classify(edited)
    assert operand is None
    assert _codes(c) == ["E-REPRODUCE-OPERAND"]
    message = _messages(c)
    assert "no `run_id`" in message, message
    assert "edited or truncated" in message, message


def test_fixture_s_arm_4_a_yaml_list_is_refused_as_an_operand(tmp_path: Path):
    path = tmp_path / "list.yaml"
    path.write_text("- one\n- two\n")
    operand, c = _classify(path)
    assert operand is None
    assert _codes(c) == ["E-REPRODUCE-OPERAND"]
    assert "list, not a mapping" in _messages(c)


def test_fixture_s_arm_5_a_missing_path_is_e_io_failed(tmp_path: Path):
    """Arm 5. `E-IO-FAILED`, `diff`'s and `resume`'s precedent, and NOT
    `read_record_file`'s `E-UPSTREAM-RECORD-MISSING`: at this point nothing has
    established that the operand was meant to be a record at all."""
    operand, c = _classify(tmp_path / "nowhere.yaml")
    assert operand is None
    assert _codes(c) == ["E-IO-FAILED"]


# --- Two properties the five arms do not cover on their own. ---------------


def test_a_record_whose_schema_version_this_build_cannot_read_keeps_its_own_code(tmp_path: Path):
    """`read_record_file`'s refusals are re-reported through the collector WITH
    THEIR OWN CODES, rather than being flattened into
    `E-REPRODUCE-OPERAND` — H9c is that reader's fifth caller and mints no
    refusal of its own for the parse."""
    doc = _a_run(tmp_path)
    record = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    record["schema_version"] = "9.9"
    path = tmp_path / "future.run.yaml"
    path.write_text(yaml.safe_dump(record, sort_keys=False))

    operand, c = _classify(path)
    assert operand is None
    assert _codes(c) == ["E-UPSTREAM-RECORD-VERSION"]


def test_a_refusal_is_rendered_through_a_credential_bearing_collector(tmp_path: Path):
    """The redaction pass is `Collector.render`'s, and it is reachable here
    only because the refusal is APPENDED rather than raised — `main`'s
    `except PublishableError` handler applies no redaction pass at all
    (measured by H9b), so a raise would print this value verbatim.

    The credential reaches the message through the YAML parse error, which
    quotes the offending line. That is a real route, not a contrivance: a
    `.env`-style value pasted into a config is exactly how a secret lands in a
    file core is asked to read.
    """
    secret = "sk-h9c-task2-not-a-real-key"
    path = tmp_path / "broken.yaml"
    # The secret must sit ON the offending line, not merely in the file:
    # `yaml`'s error quotes one line, and the first draft of this fixture put
    # the secret on line 1 with the fault on line 2 — its own control caught
    # that, which is what a fixture-as-a-claim assertion is for.
    path.write_text(f"token: {secret}: trailing\n")

    operand, c = _classify(path, credentials={"H9C_TOKEN": secret})
    assert operand is None
    assert _codes(c) == ["E-IO-FAILED"]
    assert secret in _messages(c), "the fixture must actually carry the value it redacts"
    rendered = c.render()
    assert secret not in rendered, rendered
    assert "<redacted:H9C_TOKEN>" in rendered, rendered


@pytest.mark.parametrize(
    "text",
    ["", "null\n", "42\n", "a string\n"],
)
def test_a_document_that_is_not_a_mapping_never_raises(tmp_path: Path, text: str):
    """Reaching the assertion at all is the claim: nothing in this module
    raises into `main`, including the empty-file case, where `safe_load`
    returns `None` rather than failing."""
    path = tmp_path / "odd.yaml"
    path.write_text(text)
    operand, c = _classify(path)
    assert operand is None
    assert _codes(c) == ["E-REPRODUCE-OPERAND"]


# ==========================================================================
# Fixtures A, C, E, K, T and the commit-unreachable fixture — the destination
# and the clone (design Decisions 7, 8, 9; plan correction 26).
# ==========================================================================


_A_LOCKFILE = b'version = 1\nrequires-python = ">=3.11"\n\n[[package]]\nname = "h9c"\n'
"""A lockfile's BYTES, written and never resolved.

`uv lock` inside a `publishable new` project fails outright — *"Because
publishable was not found in the package registry"* — so no fixture recipe in
this slice may run it (plan correction 22). What a written lockfile buys is a
non-null `uv_lock_hash` and a real `environment/uv.lock` byte copy; what it
cannot buy is a lockfile a real `uv sync --locked` would accept, and no arm
here claims one.
"""


def _fixture_a(tmp_path: Path, *, lockfile: bytes | None = _A_LOCKFILE) -> dict:
    """Fixture A: a real repository, a real remote, and a record that carries it.

    The remote is a **local bare repo** and never the network: a fixture that
    reaches the network is a fixture that fails on a build machine, and `git
    clone` treats a path and a URL identically.

    `run_a_project` scaffolds no `origin`, and `provenance.git.remote` is read
    at run time — so the project is run TWICE. The first run commits the tree
    and gives the bare clone something to be made from; the remote is then
    added and the project run again, and it is that second record which carries
    a real, cloneable remote. Patching the remote into a record after the fact
    was the alternative, and it was rejected: it produces a record no `run`
    ever wrote, which is the synthesized-fixture shape this slice is trying to
    avoid.

    Adding a remote does not dirty the tree — the gate reads
    `git status --porcelain -- src templates` — and neither does an untracked
    `uv.lock` at the repository root, which is § 0.1's measured shape exactly.
    """
    doc = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 1}]}, units=10)
    root = doc["root"]
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "clone", "--bare", "-q", str(root), str(bare)], check=True)
    subprocess.run(["git", "-C", str(root), "remote", "add", "origin", str(bare)], check=True)
    if lockfile is not None:
        (root / "uv.lock").write_bytes(lockfile)

    before = {p.name for p in doc["results_dir"].glob("run_*")}
    assert main(["run", str(doc["cfg"])]) == EXIT_OK
    fresh = [p for p in doc["results_dir"].glob("run_*") if p.name not in before]
    assert len(fresh) == 1, fresh
    run_dir = fresh[0]
    record = yaml.safe_load((run_dir / "run.yaml").read_text())
    assert record["provenance"]["git"]["remote"] == str(bare), record["provenance"]["git"]
    return {
        "root": root,
        "bare": bare,
        "cfg": doc["cfg"],
        "run_dir": run_dir,
        "record": record,
        "record_path": run_dir / "run.yaml",
    }


def _checkout_code_hash(dest: Path) -> str:
    """`command_run`'s own predicate, in the pair form. Never a hard-coded
    digest: a commit SHA and everything derived from it cannot be a stable
    literal, so every arm below compares a computed value against the record's
    own."""
    return code_hash_of(hashed_files(dest, lambda cands: unignored_under_hashed_trees(dest, cands)))


def _prepare(
    record: dict,
    cwd: Path,
    credentials: dict[str, str] | None = None,
    *,
    operand_path: Path | None = None,
):
    """`prepare_checkout` takes the `Record`, operand path included.

    `operand_path` defaults to a path that is NOT the one the destination guard
    reads, so a build that walked up from the operand would answer a different
    question — which is the mutation Fixture T arm 2 exists to catch.
    """
    cwd.mkdir(parents=True, exist_ok=True)
    c = Collector(credentials=dict(credentials or {}))
    path = operand_path if operand_path is not None else Path("/nonexistent/run.yaml")
    return prepare_checkout(Record(record, path), c, cwd=cwd), c


def _autocrlf_true(tmp_path: Path, monkeypatch) -> None:
    """Install an ambient `core.autocrlf = true` through `GIT_CONFIG_GLOBAL`.

    The same instrument H6a's batch 1 used, and it must be this rather than the
    user's real config: a fixture that edits `~/.gitconfig` is a fixture that
    changes the machine.
    """
    gitconfig = tmp_path / "throwaway.gitconfig"
    gitconfig.write_text("[core]\n\tautocrlf = true\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(gitconfig))


# --- Fixture A / C: the plain clone, and the derived name. -----------------


def test_fixture_c_a_plain_clone_reproduces_the_recorded_code_hash(tmp_path: Path):
    """Fixture C, THE NEGATIVE CONTROL, and it must exist: an arm that only
    proves a mismatch is detected proves nothing about the success path.

    The digest is computed by calling `code_hash_of` over the checkout, and
    compared against the record's own — never against a literal.
    """
    fx = _fixture_a(tmp_path)
    prepared, c = _prepare(fx["record"], tmp_path / "cwd")
    assert isinstance(prepared, Checkout), c.render()
    assert c.findings == []
    assert _checkout_code_hash(prepared.dest) == fx["record"]["code_hash"]
    head = subprocess.run(
        ["git", "-C", str(prepared.dest), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert head.stdout.strip() == fx["record"]["provenance"]["git"]["commit"]


def test_the_destination_is_the_remotes_last_component_then_the_run_id(tmp_path: Path):
    """Decision 9's derivation, and it is asserted on the NAME rather than only
    on existence — `<name>_<run_id>` is § Reproducing's own worked example
    shape, and a derivation that produced any unique name at all would satisfy
    an existence check."""
    fx = _fixture_a(tmp_path)
    prepared, _ = _prepare(fx["record"], tmp_path / "cwd")
    assert isinstance(prepared, Checkout)
    assert prepared.dest.name == f"origin_{fx['record']['run_id']}"
    assert prepared.dest.parent == tmp_path / "cwd"


@pytest.mark.parametrize(
    ("remote", "expected"),
    [
        ("https://github.com/me/my-study.git", "my-study"),
        ("https://github.com/me/my-study", "my-study"),
        ("git@github.com:me/my-study.git", "my-study"),
        ("/srv/repos/my-study.git/", "my-study"),
        ("origin", "origin"),
    ],
)
def test_destination_for_strips_one_trailing_dot_git_from_any_remote_spelling(
    tmp_path: Path, remote: str, expected: str
):
    """The derivation alone, over the five remote spellings a real record can
    carry. `.git` is stripped ONCE — `my-study.git.git` is not a case anyone
    writes, and stripping repeatedly would eat a repository genuinely named
    `x.git`."""
    record = {"run_id": "run_X", "provenance": {"git": {"remote": remote}}}
    assert destination_for(record, cwd=tmp_path).name == f"{expected}_run_X"


# --- Fixture E: the `autocrlf` clone, three arms, one per claim. -----------


def test_fixture_e_arm_1_the_override_restores_the_recorded_digest(tmp_path: Path, monkeypatch):
    """Fixture E arm 1. Under an ambient `core.autocrlf = true` a plain clone
    materializes CRLF and hashes differently; `-c core.autocrlf=false` gives
    the recorded digest back.

    Both literals are computed by running rather than transcribed: the
    fixture's own digest comes out of its record, and the two clone digests are
    computed over the two trees. The control below it is what makes this arm
    non-vacuous — without it, an assertion that the digests agree would pass
    identically on a machine where `core.autocrlf` never mattered.

    Mutation: drop `-c core.autocrlf=false` from `_CLONE_CONFIG` (production
    code). Measured on git 2.50.1 — see the report.
    """
    fx = _fixture_a(tmp_path)
    _autocrlf_true(tmp_path, monkeypatch)

    prepared, c = _prepare(fx["record"], tmp_path / "cwd")
    assert isinstance(prepared, Checkout), c.render()
    assert _checkout_code_hash(prepared.dest) == fx["record"]["code_hash"]

    # The control, in the same test so the two digests are compared against
    # each other and not each against its own literal: a clone made the plain
    # way, under the identical ambient setting, must NOT hash to the record's.
    plain = tmp_path / "plain_clone"
    subprocess.run(["git", "clone", "-q", str(fx["bare"]), str(plain)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(plain),
            "checkout",
            "-q",
            "--detach",
            fx["record"]["provenance"]["git"]["commit"],
        ],
        check=True,
    )
    assert _checkout_code_hash(plain) != fx["record"]["code_hash"], (
        "the ambient core.autocrlf=true did not take effect, so this arm proves nothing"
    )


def test_fixture_e_arm_2_clone_c_persists_the_setting_into_the_new_repo(
    tmp_path: Path, monkeypatch
):
    """Fixture E arm 2, RE-AIMED, and the re-aiming is the finding.

    The design's arm 2 was *drop the leading `git -c` but keep `clone -c`, and
    the checkout is still CRLF*. Measured on git 2.50.1 that is **false**:
    `clone -c core.autocrlf=false` alone stores `false` AND materializes LF, so
    the prescribed mutation's two branches cannot differ and the arm would be
    blind. Reported blind in advance, with the version.

    What IS provable is the placement's stated job: `clone -c` **persists** the
    setting into the new repository's `.git/config`, so a later `git checkout`
    in the prepared tree does not re-convert. Measured the other way round too:
    with the leading `git -c` alone, the clone's config reads `true` and a
    re-materialized file comes back CRLF. This arm asserts the stored value and
    the re-materialization, and it is what fails when `clone -c` is dropped.
    """
    fx = _fixture_a(tmp_path)
    _autocrlf_true(tmp_path, monkeypatch)

    prepared, c = _prepare(fx["record"], tmp_path / "cwd")
    assert isinstance(prepared, Checkout), c.render()
    stored = subprocess.run(
        ["git", "-C", str(prepared.dest), "config", "core.autocrlf"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert stored.stdout.strip() == "false"

    # Re-materialize a hashed file the way any later `git checkout` in this
    # tree would, and it must come back with the recorded bytes rather than
    # converted ones. Asserted through the digest, which is the property that
    # actually matters, rather than through a byte inspection of one file.
    victim = next(p for _, p in hashed_files(prepared.dest, None) if p.suffix == ".py")
    victim.unlink()
    subprocess.run(["git", "-C", str(prepared.dest), "checkout", "--", str(victim)], check=True)
    assert _checkout_code_hash(prepared.dest) == fx["record"]["code_hash"]


def test_fixture_e_arm_3_the_flag_list_is_exactly_one_flag_at_both_placements(
    tmp_path: Path, monkeypatch
):
    """Fixture E arm 3, the STRUCTURAL arm, and it is the owed replacement for
    two mutations named blind in advance.

    `core.eol=lf` changes nothing measurable (measured: it alone leaves the
    CRLF digest), and `core.excludesFile` has nothing to reach in a fresh
    clone of a commit whose `.gitignore` files are tracked. So an assertion on
    a *hash* cannot see either flag being added, and the non-use has to be
    asserted on the invocation itself.

    Both placements are asserted, and the argv is captured from the real call
    rather than read off the constant — a test that iterates the thing under
    test measures only that it equals itself.
    """
    fx = _fixture_a(tmp_path)
    seen: list[list[str]] = []
    real = reproduce_module._git

    def recording(args: list[str]):
        seen.append(list(args))
        return real(args)

    monkeypatch.setattr(reproduce_module, "_git", recording)
    prepared, c = _prepare(fx["record"], tmp_path / "cwd")
    assert isinstance(prepared, Checkout), c.render()

    clone_argv = next(a for a in seen if "clone" in a)
    assert clone_argv[:2] == ["git", "-c"], clone_argv
    at = clone_argv.index("clone")
    assert clone_argv[1:at] == list(_CLONE_CONFIG), clone_argv
    assert clone_argv[at + 1 : at + 3] == list(_CLONE_CONFIG), clone_argv
    assert [a for a in clone_argv if a == "-c"] == ["-c", "-c"], clone_argv
    joined = " ".join(a for argv in seen for a in argv)
    for absent in ("core.eol", "core.excludesFile", "core.fileMode", "safe.directory"):
        assert absent not in joined, (absent, joined)


# --- Fixture K: `remote: null`. --------------------------------------------


def test_fixture_k_a_null_remote_refuses_naming_the_commit_and_creates_nothing(tmp_path: Path):
    """Fixture K. § 0.8's measured default state for a scaffolded project.

    Three assertions, and the third is the one a code-only arm would miss: NO
    DIRECTORY IS CREATED. Derive-then-refuse and refuse-then-derive are
    otherwise indistinguishable. The message must name the recorded commit —
    a refusal that tells the reader nothing is a refusal with no remedy.
    """
    doc = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 1}]}, units=10)
    record = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert record["provenance"]["git"]["remote"] is None

    cwd = tmp_path / "cwd"
    prepared, c = _prepare(record, cwd)
    assert isinstance(prepared, Refused)
    assert prepared.exit_code == EXIT_WRONG
    assert [f.code for f in c.findings] == ["E-REPRODUCE-NO-REMOTE"]
    assert record["provenance"]["git"]["commit"] in c.findings[0].message
    assert list(cwd.iterdir()) == []


# --- Fixture T: the destination guards. -----------------------------------


def test_fixture_t_arm_1_an_existing_destination_is_refused_and_left_alone(tmp_path: Path):
    """Fixture T arm 1. The refusal AND the non-overwrite: the pre-existing
    directory's own contents are asserted unchanged, because a build that
    refused after clobbering would satisfy a code-only assertion."""
    fx = _fixture_a(tmp_path)
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    dest = destination_for(fx["record"], cwd=cwd)
    dest.mkdir()
    (dest / "mine.txt").write_text("do not touch\n")

    prepared, c = _prepare(fx["record"], cwd)
    assert isinstance(prepared, Refused)
    assert prepared.exit_code == EXIT_WRONG
    assert [f.code for f in c.findings] == ["E-REPRODUCE-DEST-EXISTS"]
    assert sorted(p.name for p in dest.iterdir()) == ["mine.txt"]
    assert (dest / "mine.txt").read_text() == "do not touch\n"


def test_fixture_t_arm_2_a_destination_inside_a_repository_is_refused(tmp_path: Path):
    """Fixture T arm 2. The walk-up is from the DESTINATION'S PARENT and not
    from the operand, and the two live in DIFFERENT repositories by
    construction — a fixture with one repository cannot tell the two readings
    apart, since either walk-up would find the same root.

    The operand here sits inside Fixture A's own project repository (the record
    is copied there), while the working directory sits inside a second,
    unrelated repository. A build walking up from the operand names Fixture A's
    repo; the correct build names this one. The message carries the root, so
    the assertion can say WHICH.
    """
    fx = _fixture_a(tmp_path)
    operand_repo = fx["root"]
    inside = operand_repo / "a_record.run.yaml"
    inside.write_text(fx["record_path"].read_text())

    other = tmp_path / "other_repo"
    other.mkdir()
    subprocess.run(["git", "init", "-q", str(other)], check=True)
    cwd = other / "work"

    prepared, c = _prepare(fx["record"], cwd, operand_path=inside)
    assert isinstance(prepared, Refused)
    assert prepared.exit_code == EXIT_WRONG
    assert [f.code for f in c.findings] == ["E-REPRODUCE-DEST-IN-REPO"]
    message = c.findings[0].message
    assert str(other.resolve()) in message, message
    assert str(operand_repo.resolve()) not in message, message


def test_a_destination_outside_any_repository_proceeds(tmp_path: Path):
    """The negative control for arm 2, and it is not optional: `find_repo_root`
    RAISES when there is no repository, so the ordinary case travels the
    exception path. An arm asserting only the refusal would pass identically if
    that path had been wired to refuse as well."""
    fx = _fixture_a(tmp_path)
    prepared, c = _prepare(fx["record"], tmp_path / "no_repo_here")
    assert isinstance(prepared, Checkout), c.render()
    assert c.findings == []


# --- Correction 26's thirteenth code. -------------------------------------


def test_a_recorded_commit_the_remote_no_longer_holds_is_commit_unreachable(tmp_path: Path):
    """Plan correction 26's `E-REPRODUCE-COMMIT-UNREACHABLE`, at exit `5`.

    **A rewritten history is caught at the CHECKOUT, not by the hash.** A
    commit SHA is a hash over its own tree, so a different tree cannot live at
    the same SHA: an amend produces a NEW SHA and leaves the original's tree
    untouched, so the recorded SHA still checks out to the recorded bytes and a
    hash comparison passes. What a rewrite really leaves behind is a remote
    that no longer holds the recorded object.

    **The fixture trap, designed around rather than discovered:** `git clone`
    of a LOCAL PATH hardlinks the whole object database, unreachable objects
    included, so cloning Fixture A's local remote after the amend still finds
    the old commit and the checkout SUCCEEDS. The bare intermediate below is
    cloned with `--no-local`, which is what makes the object genuinely absent.
    The `assert` on the intermediate is the fixture asserting its own claim.

    **`reproduce` itself passes no `--no-local`** — that would break the
    legitimate local-remote case and slow every clone. The flag belongs to the
    fixture.
    """
    fx = _fixture_a(tmp_path)
    recorded = fx["record"]["provenance"]["git"]["commit"]

    target = next(p for _, p in hashed_files(fx["root"], None) if p.suffix == ".py")
    target.write_text(target.read_text() + "\n# rewritten\n")
    # `--amend`, and NOT a fresh commit on top: a second commit leaves the
    # recorded SHA reachable as its own parent, the bare repo keeps the object,
    # and `--no-local` carries it — the first draft of this fixture did exactly
    # that and its own control caught it.
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@e.com",
            "-c",
            "user.name=t",
            "commit",
            "--amend",
            "-qam",
            "amended",
        ],
        cwd=fx["root"],
        check=True,
    )
    # The intermediate is cloned from the AMENDED working repository with
    # `--no-local`, and both halves matter. `--no-local` forces the transport,
    # which sends only objects reachable from a ref — a local-path clone
    # HARDLINKS the whole object database, unreachable objects included, which
    # is correction 26's named trap and is why Fixture A's own bare remote
    # cannot be used here. Cloning from the amended repo rather than
    # force-pushing into Fixture A's remote keeps the construction to one git
    # operation whose reachability rule is the thing being relied on.
    detached = tmp_path / "detached.git"
    subprocess.run(
        ["git", "clone", "--no-local", "--bare", "-q", str(fx["root"]), str(detached)], check=True
    )
    probe = subprocess.run(
        ["git", "-C", str(detached), "cat-file", "-e", f"{recorded}^{{commit}}"],
        capture_output=True,
    )
    assert probe.returncode != 0, (
        "the bare intermediate still holds the recorded commit, so this fixture is "
        "testing the opposite state — see correction 26's named trap"
    )

    record = dict(fx["record"])
    record["provenance"] = dict(record["provenance"])
    record["provenance"]["git"] = dict(record["provenance"]["git"])
    record["provenance"]["git"]["remote"] = str(detached)

    prepared, c = _prepare(record, tmp_path / "cwd")
    assert isinstance(prepared, Refused)
    assert prepared.exit_code == EXIT_EXTERNAL
    assert [f.code for f in c.findings] == ["E-REPRODUCE-COMMIT-UNREACHABLE"]
    assert recorded in c.findings[0].message


def test_a_remote_that_cannot_be_cloned_is_e_io_failed_at_exit_five(tmp_path: Path):
    """A clone that was ATTEMPTED and failed is exit `5` — `EXIT_EXTERNAL`'s
    *"a clone or `uv sync` that failed"* clause.

    The code is `E-IO-FAILED` and no code is minted: Decision 14's table gives
    a failed clone no row while Decision 7 promises it exit `5`, and the
    shipped `EXIT_EXTERNAL` precedent returns `5` under an existing code
    (`E-APPARATUS-RAISED`) rather than under one minted for the exit. Reported
    as a design-versus-code disagreement.

    Both halves are asserted, because exit `5` under the wrong code and the
    right code at the wrong exit are the two ways this row goes wrong.
    """
    fx = _fixture_a(tmp_path)
    record = dict(fx["record"])
    record["provenance"] = dict(record["provenance"])
    record["provenance"]["git"] = dict(record["provenance"]["git"])
    record["provenance"]["git"]["remote"] = str(tmp_path / "no_such_repo.git")

    prepared, c = _prepare(record, tmp_path / "cwd")
    assert isinstance(prepared, Refused)
    assert prepared.exit_code == EXIT_EXTERNAL
    assert [f.code for f in c.findings] == ["E-IO-FAILED"]
