"""H9c — `reproduce`. Fixture S, the operand discrimination (design § 9).

Every literal here is either computed in the test or read back out of the
artifact the fixture built. The two `run`-driven fixtures come from
`tests.test_cli`'s `run_a_project`, the one end-to-end driver this suite has —
re-inventing the scaffold-and-commit dance is how a fixture drifts from what
`run` actually writes.
"""

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from tests.test_cli import run_a_project

import publishable.reproduce as reproduce_module
from publishable.cli import main
from publishable.diagnostics import EXIT_EXTERNAL, EXIT_OK, EXIT_WRONG, Collector
from publishable.generators.experiment import generate_experiment
from publishable.hashes import code_hash, code_hash_of, hashed_files, parameters_hash
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
    prepare_env,
    restore_environment,
    verify_code_hash,
    write_config,
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


def _fixture_a(
    tmp_path: Path,
    *,
    working_lock: bytes | None = _A_LOCKFILE,
    committed_lock: bytes | None = None,
    edit_pyproject: bool = False,
) -> dict:
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
    if committed_lock is not None:
        # COMMITTED at the recorded commit, which is what makes the clone carry
        # one — the bare remote below is made after this, so its HEAD is this
        # commit and the second run records it.
        (root / "uv.lock").write_bytes(committed_lock)
        subprocess.run(["git", "-C", str(root), "add", "uv.lock"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "-c",
                "user.email=t@e.com",
                "-c",
                "user.name=t",
                "commit",
                "-qm",
                "lockfile",
            ],
            check=True,
        )
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "clone", "--bare", "-q", str(root), str(bare)], check=True)
    subprocess.run(["git", "-C", str(root), "remote", "add", "origin", str(bare)], check=True)
    if working_lock is not None:
        # Written LAST, so it can differ from the committed one by
        # construction: this is the shape Fixture I needs and no
        # single-lockfile fixture can supply. An uncommitted change to a
        # tracked `uv.lock` does not make the tree dirty to `run`'s gate, which
        # reads `git status --porcelain -- src templates`.
        (root / "uv.lock").write_bytes(working_lock)
    elif committed_lock is None:
        (root / "uv.lock").unlink(missing_ok=True)
    if edit_pyproject:
        # § 0.7's recipe: an UNCOMMITTED edit, so the run records a copy the
        # commit does not hold.
        pyproject = root / "pyproject.toml"
        pyproject.write_bytes(pyproject.read_bytes() + b"\n# h9c fixture J\n")

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
        "results_dir": doc["results_dir"],
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


# ==========================================================================
# `code_hash` in the checkout — Fixtures C (the match), D1, D2, and the draft
# arm on Fixture B. Design Decisions 2 and 10, Ruling Z.
# ==========================================================================


def _verify(record: dict, dest: Path, credentials: dict[str, str] | None = None):
    c = Collector(credentials=dict(credentials or {}))
    lines, code = verify_code_hash(Record(record, dest / "run.yaml"), dest, c)
    # What a reader sees is the diagnostic AND the transcript lines: the file
    # list and the candidate causes are lines rather than one nine-line
    # diagnostic message, because `Collector.render` indents exactly one
    # continuation line per finding. Every arm below asserts on the two
    # together, which is the text that actually reaches a terminal.
    seen = "\n".join(lines) + ("\n" + c.render() if c.findings else "")
    return lines, code, c, seen


def _prepared_checkout(tmp_path: Path, fx: dict) -> Path:
    prepared, c = _prepare(fx["record"], tmp_path / "cwd")
    assert isinstance(prepared, Checkout), c.render()
    return prepared.dest


def _ignored_file_under_src(dest: Path) -> Path:
    """Drop an untracked, git-ignored file under `src/**` into a checkout, and
    assert git really excludes it.

    The scaffold's own `.gitignore` opens with `.env`, which is the rule § 0.3
    used. **A TRACKED file cannot serve here**, measured: `git check-ignore`
    without `--no-index` — which is what `unignored_under_hashed_trees` runs —
    reports nothing for a tracked path, so a force-added ignored file is
    included by BOTH predicates and the two branches could not differ.
    """
    pkg = next(p for p in (dest / "src").iterdir() if p.is_dir())
    victim = pkg / ".env"
    victim.write_text("H9C_TASK4=1\n")
    candidates = [rel for rel, _ in hashed_files(dest, None)]
    assert victim.relative_to(dest).as_posix() in candidates
    kept = unignored_under_hashed_trees(dest, candidates)
    assert victim.relative_to(dest).as_posix() not in kept, (
        "git does not exclude this file, so the two predicates agree and the arm is blind"
    )
    return victim


def test_fixture_c_a_matching_code_hash_prints_one_line_with_the_file_count(tmp_path: Path):
    """Fixture C's own reported fact. The count is read off the same predicate
    the production code uses rather than hard-coded — a commit SHA and
    everything derived from it cannot be a stable literal."""
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    expected = len(hashed_files(dest, lambda cands: unignored_under_hashed_trees(dest, cands)))
    assert expected > 0

    lines, code, c, seen = _verify(fx["record"], dest)
    assert code is None
    assert c.findings == []
    assert lines == [
        f"code_hash: matches the record over {expected} files ({fx['record']['code_hash']})"
    ]


def test_the_git_aware_predicate_is_what_is_compared_not_every_file_in_the_trees(
    tmp_path: Path,
):
    """The `include=None` mutation, and the fixture that separates the two
    readings — with the design's own claim about it CORRECTED.

    The design says a *Fixture C arm carrying a git-ignored file under `src/`*
    separates them. Measured, that cannot happen in a clone at all: a fresh
    clone holds only TRACKED files, and `git check-ignore` (without
    `--no-index`, which is what core runs) never reports a tracked path as
    ignored — so end to end the two predicates agree on every checkout
    `reproduce` can produce, and the mutation would be blind. The divergence is
    therefore built where it is reachable: the ignored file is dropped into the
    checkout before the comparison, which is exactly the state a later
    `reproduce` step could create.

    Both branches are computed here, so the arm cannot agree with the bug: the
    git-aware digest and the every-file digest are asserted DIFFERENT before
    either is compared against the record.
    """
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    _ignored_file_under_src(dest)

    git_aware = code_hash_of(
        hashed_files(dest, lambda cands: unignored_under_hashed_trees(dest, cands))
    )
    every_file = code_hash_of(hashed_files(dest, None))
    assert git_aware != every_file
    assert git_aware == fx["record"]["code_hash"]

    lines, code, c, seen = _verify(fx["record"], dest)
    assert code is None, seen
    assert c.findings == []


def test_fixture_d1_a_pre_redefinition_code_hash_is_refused_with_the_candidate_set(
    tmp_path: Path,
):
    """Fixture D1 (plan correction 26). The record's `code_hash` is the
    EVERY-FILE figure — what a record written before the redefinition of which
    files are hashed would carry — computed in the test by calling
    `code_hash(root, None)`, never transcribed.

    **Fixture D as the design wrote it was not constructible**: a commit SHA is
    a hash over its own tree, so a different tree cannot live at the same SHA;
    an amend produces a new SHA and leaves the original's tree untouched, so
    the recorded SHA still checks out to the recorded bytes and the comparison
    PASSES. A rewritten history is caught at the checkout instead, which is its
    own arm above.

    Ruling Z is what this arm pins: the output names WHICH input moved and
    enumerates the causes it cannot separate, and asserts that no sentence
    picks one.
    """
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    _ignored_file_under_src(dest)
    pre = code_hash(dest, None)
    assert pre != fx["record"]["code_hash"]

    record = dict(fx["record"])
    record["code_hash"] = pre

    lines, code, c, seen = _verify(record, dest)
    assert code == EXIT_WRONG
    assert [f.code for f in c.findings] == ["E-REPRODUCE-CODE-HASH"]
    assert (
        pre in seen
        and code_hash_of(
            hashed_files(dest, lambda cands: unignored_under_hashed_trees(dest, cands))
        )
        in seen
    )
    assert str(dest) in seen
    assert dest.is_dir(), "the checkout must be kept"

    # The candidate set is present, and NO sentence picks one of its members.
    for clause in (
        "cannot tell these apart",
        "rewritten or force-pushed",
        "predates the redefinition",
        "materialized the tree differently",
        "`core.autocrlf`",
        "`.gitattributes`",
    ):
        assert clause in seen, clause
    # The single-cause wording, asserted ABSENT. An assertion on the code alone
    # would pass under both wordings, which is what makes this half the arm.
    for verdict in (
        "this is a rewritten or force-pushed history",
        "the history was rewritten",
        "because the history was force-pushed",
    ):
        assert verdict not in seen, verdict


def test_fixture_d2_an_arbitrary_edited_code_hash_is_refused_the_same_way(tmp_path: Path):
    """Fixture D2 (plan correction 26): a `code_hash` edited to an arbitrary
    digest. Distinct from D1 in what it rules out — D1's figure is one a real
    record could genuinely carry, so an implementation special-casing "looks
    like a pre-redefinition digest" would still have to answer this one, and
    the two arms together show the refusal is about the COMPARISON rather than
    about recognizing a shape."""
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    record = dict(fx["record"])
    record["code_hash"] = "sha256:" + "0" * 64

    lines, code, c, seen = _verify(record, dest)
    assert code == EXIT_WRONG
    assert [f.code for f in c.findings] == ["E-REPRODUCE-CODE-HASH"]
    assert "sha256:" + "0" * 64 in seen
    assert "cannot tell these apart" in seen
    assert dest.is_dir()
    # The file LIST, not only the count: every hashed path appears.
    for rel, _ in hashed_files(dest, lambda cands: unignored_under_hashed_trees(dest, cands)):
        assert rel in seen, rel


def test_a_draft_record_declines_the_verification_rather_than_failing_it(tmp_path: Path):
    """Decision 10's draft arm, on Fixture B. Two halves, and the second is
    what separates *declines* from *refuses*: no finding is collected AND the
    returned exit code is `None`, so the caller continues to the closing
    transcript at exit `0`.

    The record's `code_hash` is left DELIBERATELY WRONG here. A draft arm whose
    hash happened to match would pass whether the draft branch existed or not —
    a fixture whose numbers agree with the bug.
    """
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    record = dict(fx["record"])
    record["draft"] = True
    record["code_hash"] = "sha256:" + "1" * 64

    lines, code, c, seen = _verify(record, dest)
    assert code is None
    assert c.findings == []
    assert any("this record is a draft" in line for line in lines), lines
    assert any("not verified" in line for line in lines), lines
    assert "cannot tell these apart" not in seen


def test_a_non_draft_record_is_not_given_the_draft_line(tmp_path: Path):
    """The negative control for the draft branch: `draft: false` is what every
    real record carries, and an arm asserting only the draft path would pass if
    the branch had swallowed both."""
    fx = _fixture_a(tmp_path)
    assert fx["record"]["draft"] is False
    dest = _prepared_checkout(tmp_path, fx)
    lines, code, c, seen = _verify(fx["record"], dest)
    assert code is None
    assert "draft" not in seen


# ==========================================================================
# The environment — Fixtures G, H, I, J, L. Design Decision 3 (Ruling AA).
# ==========================================================================


_I_COMMITTED_LOCK = b'version = 1\nrequires-python = ">=3.11"\n\n[[package]]\nname = "committed"\n'
"""A SECOND lockfile's bytes, differing from `_A_LOCKFILE` by construction.

Fixture I's whole claim is that the two candidate lockfiles can disagree and
that the disagreement is reported rather than resolved. A single-lockfile
fixture cannot supply that: the two branches would be byte-identical and no
assertion could tell *reported* from *silently used*.
"""


def _stub_sync(monkeypatch) -> list[tuple[str, ...]]:
    """Observe the `uv sync --locked` seam instead of running it, and say why.

    **No fixture in this slice can produce a lockfile a real `uv sync --locked`
    would accept.** `uv lock` inside a `publishable new` project fails outright
    — *"Because publishable was not found in the package registry"* — so plan
    correction 22 forbids any recipe from running it, and every fixture
    lockfile here is WRITTEN. A written lockfile cannot satisfy a real
    `--locked` resolve, so an arm that ran the sync would be asserting on
    `uv`'s refusal rather than on this module's ranking.

    So the design's *"step 3's success arm"* is armed as *reached the sync step
    with the right lockfile in place*, and never as *synced*. That is a
    narrowing of the design's wording, reported rather than quietly
    reinterpreted. The failure path is armed by letting the real call run,
    where failure is the expected outcome.
    """
    calls: list[tuple[str, ...]] = []

    def stub(dest: Path):
        calls.append(("uv", "sync", "--locked", str(dest)))
        return subprocess.CompletedProcess(["uv", "sync", "--locked"], 0, "", "")

    monkeypatch.setattr(reproduce_module, "_uv_sync", stub)
    return calls


def _restore(fx: dict, dest: Path, operand_path: Path | None = None):
    c = Collector()
    lines, code = restore_environment(
        Record(fx["record"], operand_path or fx["record_path"]), dest, c
    )
    seen = "\n".join(lines) + ("\n" + c.render() if c.findings else "")
    return lines, code, c, seen


def _bundle_member(tmp_path: Path, fx: dict, name: str = "main") -> Path:
    bundle = tmp_path / "bundle"
    study_new(bundle, "Ruling AA")
    study_add(bundle, fx["record_path"], name)
    member = bundle / f"{name}.run.yaml"
    # The measured degradation, asserted rather than assumed: the recorded
    # `uv_lock` path survives redaction while the directory it points into is
    # not in the bundle, so it is a DANGLING reference and only the digest
    # travels.
    copied = yaml.safe_load(member.read_text())
    assert copied["provenance"]["environment"]["uv_lock"] == "environment/uv.lock"
    assert not (member.parent / "environment").exists()
    assert copied["provenance"]["environment"]["uv_lock_hash"] is not None
    return member


# --- The run-directory form: the byte copy wins, and the clone is reported. -


def test_the_byte_copy_is_restored_and_a_commit_with_no_lockfile_is_reported(
    tmp_path: Path, monkeypatch
):
    """Step 2, on § 0.1's measured shape: the run recorded an UNTRACKED
    `uv.lock` and the clone of the recorded commit has none.

    Three assertions and each is a different claim: the checkout's lockfile is
    byte-equal to the RECORDED copy; the clone's absence is a printed fact
    rather than a silence; and the sync was reached.
    """
    calls = _stub_sync(monkeypatch)
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    assert not (dest / "uv.lock").exists()

    lines, code, c, seen = _restore(fx, dest)
    assert code is None, seen
    assert c.findings == []
    assert (dest / "uv.lock").read_bytes() == _A_LOCKFILE
    assert (dest / "uv.lock").read_bytes() == (
        fx["run_dir"] / "environment" / "uv.lock"
    ).read_bytes()
    assert any("the commit carries none" in line for line in lines), lines
    assert calls == [("uv", "sync", "--locked", str(dest))]


def test_fixture_i_two_disagreeing_lockfiles_report_differs_and_restore_the_recorded_one(
    tmp_path: Path, monkeypatch
):
    """Fixture I. The commit carries one lockfile, the run used another, and the
    two differ BY CONSTRUCTION.

    The byte copy wins because it is what the run actually used;
    `uv_lock_hash` covers it, and the clone's committed copy is only a claim
    about the commit. The `DIFFERS` line naming the clone's digest is the arm
    that separates *reported* from *silently overwritten* — the bytes alone
    would look identical under both.
    """
    calls = _stub_sync(monkeypatch)
    fx = _fixture_a(tmp_path, committed_lock=_I_COMMITTED_LOCK, working_lock=_A_LOCKFILE)
    assert _I_COMMITTED_LOCK != _A_LOCKFILE
    dest = _prepared_checkout(tmp_path, fx)
    assert (dest / "uv.lock").read_bytes() == _I_COMMITTED_LOCK

    lines, code, c, seen = _restore(fx, dest)
    assert code is None, seen
    assert c.findings == []
    assert (dest / "uv.lock").read_bytes() == _A_LOCKFILE
    differs = [line for line in lines if "DIFFERS" in line and "uv.lock" in line]
    assert len(differs) == 1, lines
    committed_digest = "sha256:" + hashlib.sha256(_I_COMMITTED_LOCK).hexdigest()
    assert committed_digest in differs[0], differs
    assert fx["record"]["provenance"]["environment"]["uv_lock_hash"] in differs[0], differs
    assert calls


def test_a_commit_whose_lockfile_matches_the_record_is_reported_identical(
    tmp_path: Path, monkeypatch
):
    """Fixture I's third branch, and it is not decoration: with *absent* and
    *DIFFERS* both armed, an implementation could still print `DIFFERS`
    unconditionally whenever a lockfile exists. This is the arm that says
    otherwise."""
    _stub_sync(monkeypatch)
    fx = _fixture_a(tmp_path, committed_lock=_A_LOCKFILE, working_lock=_A_LOCKFILE)
    dest = _prepared_checkout(tmp_path, fx)
    lines, code, c, seen = _restore(fx, dest)
    assert code is None, seen
    assert any("identical to the run's" in line and "uv.lock" in line for line in lines), lines
    assert not any("DIFFERS" in line for line in lines), lines


def test_a_byte_copy_edited_after_the_run_is_lockfile_edited_and_is_not_used(
    tmp_path: Path, monkeypatch
):
    """The digest check is what makes correction 28's filesystem probe safe
    rather than a proxy: a copy that does not match the record is REFUSED, not
    used.

    The clone's own lockfile is asserted UNTOUCHED, because a build that
    refused after copying would satisfy a code-only assertion.
    """
    calls = _stub_sync(monkeypatch)
    fx = _fixture_a(tmp_path, committed_lock=_I_COMMITTED_LOCK, working_lock=_A_LOCKFILE)
    dest = _prepared_checkout(tmp_path, fx)
    (fx["run_dir"] / "environment" / "uv.lock").write_bytes(b"edited after the run\n")

    lines, code, c, seen = _restore(fx, dest)
    assert code == EXIT_WRONG
    assert [f.code for f in c.findings] == ["E-REPRODUCE-LOCKFILE-EDITED"]
    assert fx["record"]["provenance"]["environment"]["uv_lock_hash"] in seen
    assert (dest / "uv.lock").read_bytes() == _I_COMMITTED_LOCK
    assert dest.is_dir()
    assert calls == []


# --- The bundle form: Fixtures G and H, and H is not optional. -------------


def test_fixture_g_a_bundle_whose_lockfile_was_never_committed_is_unreachable(
    tmp_path: Path, monkeypatch
):
    """Fixture G. `E-REPRODUCE-LOCKFILE-UNREACHABLE`, and the message must name
    BOTH facts — the recorded digest and what the clone holds. A message
    asserting only the code would pass if it named neither."""
    calls = _stub_sync(monkeypatch)
    fx = _fixture_a(tmp_path)
    member = _bundle_member(tmp_path, fx)
    dest = _prepared_checkout(tmp_path, fx)
    assert not (dest / "uv.lock").exists()

    lines, code, c, seen = _restore(fx, dest, operand_path=member)
    assert code == EXIT_WRONG
    assert [f.code for f in c.findings] == ["E-REPRODUCE-LOCKFILE-UNREACHABLE"]
    assert fx["record"]["provenance"]["environment"]["uv_lock_hash"] in seen
    assert "no uv.lock at all" in seen
    assert dest.is_dir(), "the checkout is kept"
    assert calls == []


def test_fixture_h_a_bundle_whose_lockfile_is_committed_reaches_the_sync(
    tmp_path: Path, monkeypatch
):
    """Fixture H, AND IT IS NOT OPTIONAL. Without it Fixture G proves only that
    something refused, and *"a bundle can never sync"* and *"a bundle syncs when
    the lockfile travels with the commit"* stay indistinguishable.

    The lockfile is committed AND is the one the run used, so the recorded
    digest and the clone's agree. The sync step is REACHED — see `_stub_sync`
    for why *reached* is the honest claim rather than *synced*.
    """
    calls = _stub_sync(monkeypatch)
    fx = _fixture_a(tmp_path, committed_lock=_A_LOCKFILE, working_lock=_A_LOCKFILE)
    member = _bundle_member(tmp_path, fx)
    dest = _prepared_checkout(tmp_path, fx)

    lines, code, c, seen = _restore(fx, dest, operand_path=member)
    assert code is None, seen
    assert c.findings == []
    assert any("not reachable" in line for line in lines), lines
    assert any("the commit's own copy matches" in line for line in lines), lines
    assert calls == [("uv", "sync", "--locked", str(dest))]


def test_a_bundle_whose_committed_lockfile_disagrees_with_the_record_is_unreachable(
    tmp_path: Path, monkeypatch
):
    """The third bundle branch: a lockfile IS committed and it is the wrong one.

    This is what separates *the clone's lockfile is used when one exists* from
    *when it matches the record* — Fixture G's clone holds none, so G alone
    cannot tell those two readings apart, and this is the mutation
    *accept the clone's lockfile in the bundle form without comparing digests*.
    """
    _stub_sync(monkeypatch)
    fx = _fixture_a(tmp_path, committed_lock=_I_COMMITTED_LOCK, working_lock=_A_LOCKFILE)
    member = _bundle_member(tmp_path, fx)
    dest = _prepared_checkout(tmp_path, fx)
    assert (dest / "uv.lock").read_bytes() == _I_COMMITTED_LOCK

    lines, code, c, seen = _restore(fx, dest, operand_path=member)
    assert code == EXIT_WRONG
    assert [f.code for f in c.findings] == ["E-REPRODUCE-LOCKFILE-UNREACHABLE"]
    committed_digest = "sha256:" + hashlib.sha256(_I_COMMITTED_LOCK).hexdigest()
    assert committed_digest in seen
    assert fx["record"]["provenance"]["environment"]["uv_lock_hash"] in seen


# --- Fixture J: `pyproject.toml`, and its POSITION. -----------------------


def test_fixture_j_a_moved_pyproject_is_reported_differs_before_the_uv_sync_line(
    tmp_path: Path, monkeypatch
):
    """Fixture J. § 0.7's recipe — an uncommitted edit to `pyproject.toml`, the
    run performed, then reproduced.

    **The ordering is the whole point of the row**, so the assertion is on the
    line AND on its position before the `uv sync` line: this file is what
    explains a `uv sync --locked` failure a reader would otherwise have to
    guess at, and after the failure it explains nothing. And it is NOT copied
    in — the commit's own manifest stays as committed, asserted here, because
    overwriting it with an uncommitted edit would make the checkout a tree that
    exists nowhere.
    """
    _stub_sync(monkeypatch)
    fx = _fixture_a(tmp_path, edit_pyproject=True)
    dest = _prepared_checkout(tmp_path, fx)
    committed = (dest / "pyproject.toml").read_bytes()
    recorded = (fx["run_dir"] / "environment" / "pyproject.toml").read_bytes()
    assert committed != recorded, "the fixture's two copies must differ by construction"

    lines, code, c, seen = _restore(fx, dest)
    assert code is None, seen
    assert c.findings == [], seen
    differs = [i for i, line in enumerate(lines) if line.startswith("pyproject.toml: DIFFERS")]
    sync = [i for i, line in enumerate(lines) if line.startswith("uv sync:")]
    assert len(differs) == 1 and len(sync) == 1, lines
    assert differs[0] < sync[0], lines
    assert (dest / "pyproject.toml").read_bytes() == committed


def test_an_unmoved_pyproject_is_reported_identical(tmp_path: Path, monkeypatch):
    """Fixture J's negative control. Without it, an implementation printing
    `DIFFERS` unconditionally would satisfy the arm above."""
    _stub_sync(monkeypatch)
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    lines, code, c, seen = _restore(fx, dest)
    assert code is None, seen
    assert any(line == "pyproject.toml: identical to the run's" for line in lines), lines


# --- Fixture L: `uv_lock_hash: null`. Decision 6, and task 6 owns the ruling.


def test_fixture_l_a_record_that_pinned_no_environment_refuses_and_keeps_the_checkout(
    tmp_path: Path, monkeypatch
):
    """Fixture L. `E-REPRODUCE-UNLOCKED` at exit `1`, **and the destination
    exists and holds the checked-out tree.**

    The existence assertion is the one that matters: a refusal arm asserting
    only the code would pass identically if the checkout were discarded, which
    is exactly the behaviour Decision 6 exists to specify — *a stop must be
    legible from the artifacts*.

    `uv sync` is asserted NOT reached, because the refusal is the point.
    """
    calls = _stub_sync(monkeypatch)
    fx = _fixture_a(tmp_path, working_lock=None)
    assert fx["record"]["provenance"]["environment"]["uv_lock_hash"] is None
    dest = _prepared_checkout(tmp_path, fx)

    lines, code, c, seen = _restore(fx, dest)
    assert code == EXIT_WRONG
    assert [f.code for f in c.findings] == ["E-REPRODUCE-UNLOCKED"]
    assert calls == []
    # The checkout is kept, and it holds the CHECKED-OUT TREE rather than merely
    # existing: an empty directory would satisfy `is_dir()` alone.
    assert dest.is_dir()
    assert (dest / "pyproject.toml").is_file()
    assert (dest / ".git").is_dir()
    assert (
        code_hash_of(hashed_files(dest, lambda cands: unignored_under_hashed_trees(dest, cands)))
        == fx["record"]["code_hash"]
    )
    # The closing transcript's `uv sync` line is replaced by the stated gap.
    assert any("uv sync: not run" in line for line in lines), lines


def test_a_real_uv_sync_failure_is_exit_five(tmp_path: Path):
    """The failure path, with the REAL `uv sync --locked` — the one arm that
    must not stub it, because failure is the expected outcome and a written
    lockfile guarantees it (`uv lock` cannot resolve in a scaffolded project,
    which is why no fixture lockfile is a real one).

    Exit `5` is § Exit codes' *"a clone or `uv sync` that failed"*, and this is
    that clause's second reader.
    """
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    lines, code, c, seen = _restore(fx, dest)
    assert code == EXIT_EXTERNAL, seen
    assert [f.code for f in c.findings] == ["E-IO-FAILED"]
    assert "uv sync --locked" in seen
    # Everything before the sync still ran and still reported.
    assert (dest / "uv.lock").read_bytes() == _A_LOCKFILE


# ==========================================================================
# Fixture M — the config write-back. Design Decision 11, task 7.
# ==========================================================================


def _write_config(fx: dict, dest: Path, operand_path: Path | None = None):
    c = Collector()
    lines, code = write_config(Record(fx["record"], operand_path or fx["record_path"]), dest, c)
    seen = "\n".join(lines) + ("\n" + c.render() if c.findings else "")
    return lines, code, c, seen


def _edit_the_committed_config(fx: dict, edit) -> dict:
    """Re-run Fixture A's project with an edit the recorded commit does not hold.

    Measured, and it is what makes Fixture M's second arm constructible at all:
    `provenance.git.config_committed` is answered by
    `git ls-files --error-unmatch`, so it reports whether the config is
    **tracked** — an edit made after the commit leaves it `true` while the
    commit's bytes are the pre-edit ones. Confirmed against a real run:
    `config_committed: True`, `code_dirty: False` (the gate reads
    `-- src templates`, and `configs/` is neither), and
    `git status --porcelain` reading ` M configs/cohort-pilot/config.yaml`.

    **`edit` must move a key `covered_config` COVERS**, and the first draft of
    this fixture did not: it edited `metadata.institution`, and
    `parameters_hash` excludes `metadata` wholesale, so the arm reported
    `identical` against an edited config and the DIFFERS branch was never
    reached. Caught by running it. The comparison is a *parameters* comparison
    by Decision 11's own words, so an edit to `metadata` alone reporting
    `identical` is correct behaviour and a useless fixture.
    """
    doc = yaml.safe_load(fx["cfg"].read_text())
    edit(doc)
    fx["cfg"].write_text(yaml.safe_dump(doc, sort_keys=False))
    before = {p.name for p in fx["results_dir"].glob("run_*")}
    assert main(["run", str(fx["cfg"])]) == EXIT_OK
    fresh = [p for p in fx["results_dir"].glob("run_*") if p.name not in before]
    assert len(fresh) == 1, fresh
    record = yaml.safe_load((fresh[0] / "run.yaml").read_text())
    return {**fx, "record": record, "run_dir": fresh[0], "record_path": fresh[0] / "run.yaml"}


def test_fixture_m_arm_1_the_written_config_hashes_to_the_recorded_parameters(tmp_path: Path):
    """The central assertion, and every literal is computed by calling the
    function rather than pinned: a `parameters_hash` derived from a commit SHA's
    tree cannot be a stable literal.

    Three things are asserted, not one — the hash, the blanked-plus-marked
    shape of both paths, and that everything else round-tripped. The hash alone
    is blind to the blanking by construction (`covered_config` drops both keys),
    which is exactly why the shape is asserted separately.
    """
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    lines, code, c, seen = _write_config(fx, dest)
    assert code is None, seen
    assert not c.findings, seen

    target = dest / "configs" / "cohort-pilot" / "config.yaml"
    assert target.is_file()
    written = yaml.safe_load(target.read_text())
    assert parameters_hash(written) == fx["record"]["parameters_hash"]

    # Blanked AND marked — the marker is on each of the two lines, and the
    # value parses back to the empty string rather than to `None`.
    assert written["data"]["input_dir"] == ""
    assert written["data"]["output_dir"] == ""
    text = target.read_text()
    for key in ("input_dir", "output_dir"):
        marked = [
            ln for ln in text.splitlines() if ln.strip().startswith(f"{key}:") and "REQUIRED" in ln
        ]
        assert marked == [f'  {key}: ""   # REQUIRED: set to your local copy'], text

    # Everything the record's config held, still held, with the same types.
    recorded = fx["record"]["config"]
    assert list(written) == list(recorded)
    for key in recorded:
        if key == "data":
            continue
        assert written[key] == recorded[key], key
    assert {k: v for k, v in written["data"].items() if k not in ("input_dir", "output_dir")} == {
        k: v for k, v in recorded["data"].items() if k not in ("input_dir", "output_dir")
    }
    assert any("parameters_hash matches the record" in ln for ln in lines), lines


def test_fixture_m_arm_1_the_committed_copy_is_reported_identical(tmp_path: Path):
    """The negative control for arm 2, and it is not optional: without it the
    two readings *"the comparison reports identical"* and *"the comparison is
    never made"* would be indistinguishable. `config_committed` is asserted
    into the line, so a build that printed the verdict without the record's
    own answer beside it fails here."""
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    lines, code, c, seen = _write_config(fx, dest)
    assert code is None, seen
    assert fx["record"]["provenance"]["git"]["config_committed"] is True
    identical = [ln for ln in lines if ln.startswith("config.yaml: the commit's own copy")]
    assert identical == [
        "config.yaml: the commit's own copy is identical to the record's parameters "
        "(config_committed: True)"
    ], lines
    assert not any("DIFFERS" in ln for ln in lines), lines


def test_fixture_m_arm_2_a_config_edited_after_the_commit_reports_differs(tmp_path: Path):
    """**The arm that makes the comparison non-vacuous.** With
    `config_committed: true` and no edit, `identical` is the answer whether the
    code compares anything or not — so this arm edits the config after the bare
    remote was made, runs again, and reproduces from that second record. The
    clone therefore holds the pre-edit config while the record holds the
    post-edit one.

    A `DIFFERS` under `config_committed: true` is a real fact about the record,
    not an impossible state, and both digests are named so a reader can check
    which side is which.
    """

    def edit(doc):
        doc["limits"]["max_executions"] = doc["limits"]["max_executions"] + 1
        doc["metadata"]["institution"] = "edited after the commit"

    fx = _edit_the_committed_config(_fixture_a(tmp_path), edit)
    assert fx["record"]["provenance"]["git"]["config_committed"] is True
    assert fx["record"]["config"]["metadata"]["institution"] == "edited after the commit"
    dest = _prepared_checkout(tmp_path, fx)

    committed = yaml.safe_load((dest / "configs" / "cohort-pilot" / "config.yaml").read_text())
    committed_hash = parameters_hash(committed)
    lines, code, c, seen = _write_config(fx, dest)
    # NOT a refusal — a reported fact.
    assert code is None, seen
    assert not c.findings, seen
    differs = [ln for ln in lines if "DIFFERS" in ln]
    assert len(differs) == 1, lines
    assert committed_hash in differs[0]
    assert fx["record"]["parameters_hash"] in differs[0]
    assert "config_committed: True" in differs[0]
    # And the RECORD's config is what landed.
    written = yaml.safe_load((dest / "configs" / "cohort-pilot" / "config.yaml").read_text())
    assert parameters_hash(written) == fx["record"]["parameters_hash"]
    assert written["metadata"]["institution"] == "edited after the commit"


def test_fixture_m_arm_3_a_lossy_round_trip_is_config_writeback(tmp_path: Path):
    """The `parameters_hash` self-check, armed. The record's `config` has one
    key **retyped** by the fixture — `limits.max_executions` from `int` to
    `str` — so the round trip is lossy on purpose while the file is still valid
    YAML and still holds every key.

    Measured before the check was written: that one retyping moves
    `parameters_hash`. It is `limits.max_executions` rather than a path,
    because `covered_config` drops `data.input_dir`/`output_dir` and a retyping
    there would be invisible to the check by construction — the mutation would
    then be blind, which is the shape this repo pays for most often.
    """
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    record = fx["record"]
    original = record["config"]["limits"]["max_executions"]
    assert isinstance(original, int)
    record["config"]["limits"]["max_executions"] = str(original)

    lines, code, c, seen = _write_config(fx, dest)
    assert code == EXIT_WRONG, seen
    assert [f.code for f in c.findings] == ["E-REPRODUCE-CONFIG-WRITEBACK"], seen
    assert record["parameters_hash"] in seen
    # The checkout is KEPT, and the file is left where a reader can look at it.
    assert (dest / "configs" / "cohort-pilot" / "config.yaml").is_file()
    assert dest.is_dir()


def test_the_bundle_form_writes_the_config_with_no_byte_copy_anywhere(tmp_path: Path):
    """Fixture F, and the mutation *write the config from the byte copy* is what
    it catches: a bundle member has no `config.yaml` beside it at all
    (plan correction 24), so that mutation cannot produce a config here.

    Asserted rather than assumed — the member's own directory is checked for
    the absence — and the write is then asserted to have happened anyway, since
    a control asserting only an absence passes identically if nothing ran.
    """
    fx = _fixture_a(tmp_path)
    member = _bundle_member(tmp_path, fx)
    assert not (member.parent / "config.yaml").exists()
    dest = _prepared_checkout(tmp_path, fx)
    lines, code, c, seen = _write_config(fx, dest, operand_path=member)
    assert code is None, seen
    target = dest / "configs" / "cohort-pilot" / "config.yaml"
    assert parameters_hash(yaml.safe_load(target.read_text())) == fx["record"]["parameters_hash"]
    # The comment-loss disclosure names NO file in this form, because there is
    # none — the run-directory form names the run's own copy.
    disclosure = [ln for ln in lines if "inline comments" in ln]
    assert len(disclosure) == 1, lines
    assert "no file reachable from this operand" in disclosure[0]


def test_the_run_directory_form_names_where_the_comments_still_live(tmp_path: Path):
    """The other half of correction 25's disclosure, and the arm that makes the
    bundle arm above non-vacuous: in the run-directory form the comments DO
    still live somewhere, and the transcript names the file."""
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    lines, code, c, seen = _write_config(fx, dest)
    assert code is None, seen
    byte_copy = fx["run_dir"] / "config.yaml"
    assert byte_copy.is_file()
    disclosure = [ln for ln in lines if "inline comments" in ln]
    assert len(disclosure) == 1, lines
    assert str(byte_copy) in disclosure[0]


def test_a_record_naming_no_experiment_is_refused_rather_than_traced_back(tmp_path: Path):
    """The containment guard's first shape. Both shapes below share one code
    and one remedy, and the message names which was found."""
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    del fx["record"]["config"]["metadata"]["name"]
    lines, code, c, seen = _write_config(fx, dest)
    assert code == EXIT_WRONG, seen
    assert [f.code for f in c.findings] == ["E-IO-FAILED"], seen
    assert "no `config.metadata.name`" in seen
    assert not (dest / "configs" / "cohort-pilot" / "config.yaml").read_text().startswith("schema")


def test_a_name_that_escapes_the_checkout_is_refused_and_writes_nothing(tmp_path: Path):
    """The containment guard, armed by a positive control on each side: the
    escaping name is refused **and nothing is written outside the
    destination**, while `test_fixture_m_arm_1_*` above is the arm proving an
    ordinary name still resolves. Containment ONLY — H8a's rule — so no
    statement is made about separators in a legal name."""
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    outside = dest.parent / "escaped"
    fx["record"]["config"]["metadata"]["name"] = f"../{outside.name}"
    lines, code, c, seen = _write_config(fx, dest)
    assert code == EXIT_WRONG, seen
    assert [f.code for f in c.findings] == ["E-IO-FAILED"], seen
    assert "resolves outside" in seen
    assert not outside.exists()


# ==========================================================================
# Step 6 — `.env` and `required_env`. Design Decision 12, task 8.
# Fixture R is the credential positive control.
# ==========================================================================


def _prepare_env(record: dict, dest: Path, operand_path: Path | None = None):
    c = Collector()
    lines, code = prepare_env(
        Record(record, operand_path or Path("/nonexistent/run.yaml")), dest, c
    )
    seen = "\n".join(lines) + ("\n" + c.render() if c.findings else "")
    return lines, code, c, seen


def test_dot_env_is_written_from_the_tracked_example(tmp_path: Path):
    """`.env.example` is TRACKED (correction 15), so the clone holds it — and
    that is asserted rather than assumed, because the whole step rests on it."""
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    assert (dest / ".env.example").is_file(), "the clone must carry the tracked example"
    assert not (dest / ".env").exists()
    lines, code, c, seen = _prepare_env(fx["record"], dest)
    assert code is None, seen
    assert (dest / ".env").read_bytes() == (dest / ".env.example").read_bytes()
    assert any(line.startswith(".env: written from") for line in lines), lines


def test_an_existing_dot_env_is_never_overwritten_and_the_line_says_so(tmp_path: Path):
    """The honouring AND the refusal, in one arm: the file's own bytes are
    asserted unchanged, which a line-only assertion could not see."""
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    (dest / ".env").write_text("H9C_ALREADY=mine\n")
    lines, code, c, seen = _prepare_env(fx["record"], dest)
    assert code is None, seen
    assert (dest / ".env").read_text() == "H9C_ALREADY=mine\n"
    assert any("already exists and was NOT overwritten" in line for line in lines), lines


def test_a_checkout_with_no_example_says_that_instead(tmp_path: Path):
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    (dest / ".env.example").unlink()
    lines, code, c, seen = _prepare_env(fx["record"], dest)
    assert code is None, seen
    assert not (dest / ".env").exists()
    assert any("carries no `.env.example`" in line for line in lines), lines


def test_a_core_template_declaring_no_required_env_says_none(tmp_path: Path):
    """Template `generic` resolves in THIS interpreter — it is core's — so the
    list is buildable and the answer is `none`. The negative control for the
    two branches below: without it, *"a list was printed"* and *"nothing was
    resolved"* would be indistinguishable."""
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    lines, code, c, seen = _prepare_env(fx["record"], dest)
    assert code is None, seen
    assert "required_env: template `generic` declares none" in lines, lines


# --- Fixture R: a project-local template, its credential, and the window. ---
#
# The checkout these arms are handed is a REAL `publishable new` scaffold —
# `.env.example`, `src/<pkg>/`, `templates/` and a real config, written by the
# generators rather than by hand — and the record is built from that project's
# OWN config file. `prepare_env` reads exactly three fields out of a record
# (`config.experiment_type`, `config.entrypoint`, `config.plugin`), and a
# scaffold whose template RAISES at import cannot be `run` at all, so there is
# no `run.yaml` to take them from: `validate` refuses first, which is the very
# fault these arms are about. Stated rather than left as an oddity.

_R_RAISING_TEMPLATE = """\
import os

from publishable import BaseTemplate, Param, register_template


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    parameter_spec = {
        "instrument.model": Param(
            str,
            default="m1",
            choices=["m1", "m2"],
            requires_env={"m1": ["H9C_R_TOKEN"], "m2": ["H9C_R_TOKEN"]},
        ),
    }


# AFTER the decorator on purpose: a class body finishes running before
# `@register_template` sees it, so the class is fully formed and its
# `requires_env` is readable off `PartialLoadError.partial_templates` even
# though the file is refused wholesale. That is what gives the redaction a
# declared name to match.
raise RuntimeError(
    "the assay could not reach its vault with " + os.environ["H9C_R_TOKEN"]
)
"""

_R_INSERTING_TEMPLATE = """\
import sys

from publishable import BaseTemplate, Param, register_template

# An ordinary vendoring idiom. It is here to show what it does NOT do: this
# entry is visible during `exec_module` and gone afterwards, because
# `templates.discovery._import_file` snapshots `sys.path` and restores it
# wholesale around every template file it executes. See
# `test_a_templates_own_sys_path_insert_does_not_survive_discovery`.
sys.path.insert(0, "/h9c/vendored")


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    required_env = ["H9C_R_TOKEN"]
    parameter_spec = {
        "instrument.model": Param(str, default="m1", choices=["m1", "m2"]),
    }
"""

_R_SRC_IMPORTING_TEMPLATE = """\
from cohort_pilot.h9c_marker import MARKER

from publishable import BaseTemplate, Param, register_template


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    required_env = [MARKER]
    parameter_spec = {
        "instrument.model": Param(str, default="m1", choices=["m1", "m2"]),
    }
"""

_R_RAISING_AND_INSERTING_TEMPLATE = """\
import os
import sys

from publishable import BaseTemplate, Param, register_template

sys.path.insert(0, "/h9c/vendored")


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    parameter_spec = {
        "instrument.model": Param(
            str,
            default="m1",
            choices=["m1", "m2"],
            requires_env={"m1": ["H9C_R_TOKEN"], "m2": ["H9C_R_TOKEN"]},
        ),
    }


raise RuntimeError(
    "the assay could not reach its vault with " + os.environ["H9C_R_TOKEN"]
)
"""

_R_TOKEN = "sk-h9c-task8-do-not-print"


def _fixture_r(tmp_path: Path, template: str) -> dict:
    """A scaffolded project standing in for the checkout. See the note above.

    **`run_a_project` cannot build this one, and the reason is the fixture's
    own claim.** That helper writes `_local_template` BEFORE it calls
    `generate_experiment`, and `generate_experiment` resolves the template
    through the same registry — so a `templates/*.py` that raises at import
    raises inside the FIXTURE, before anything under test runs. Caught by
    running it. The scaffold and the config are still the real generators'
    output; only the order changes, with the raising file written after the
    config exists.
    """
    root = tmp_path / "proj"
    data = tmp_path / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "index.csv").write_text(
        "patient_id,cohort,arm\n" + "\n".join(f"p{i},a,x" for i in range(1, 11)) + "\n"
    )
    assert main(["new", str(root)]) == EXIT_OK
    cfg = generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(data),
        output_dir=str(tmp_path / "results"),
    )
    (root / "templates").mkdir(exist_ok=True)
    (root / "templates" / "cred_assay.py").write_text(template)
    config = yaml.safe_load(cfg.read_text())
    config["experiment_type"] = "cred_assay"
    config["parameters"] = {"instrument.model": "m1"}
    config["metadata"]["description"] = "a Fixture R checkout"
    config["metadata"]["authors"] = ["Kyungjoon Lee"]
    cfg.write_text(yaml.safe_dump(config, sort_keys=False))
    return {"dest": root, "cfg": cfg, "record": {"config": config}}


@pytest.fixture
def _r_sys_path():
    """Restore `sys.path` around every Fixture R arm — a template that inserts
    an entry is user code, and this suite must not carry its leak forward."""
    before = list(sys.path)
    yield
    sys.path[:] = before


def test_fixture_r_a_template_raising_at_import_is_a_redacted_diagnostic(
    tmp_path: Path, monkeypatch, _r_sys_path
):
    """**`report`'s own shipped leak, reproduced against `reproduce`.** The
    credential is declared through `Param(requires_env=)` and **set in the
    environment**, so the redaction has a real value to match — an undeclared
    one would pass vacuously, which is why the fixture asserts the raw message
    carries the token before asserting the rendered one does not.

    Mutation: copy Decision 12's calls without the enclosing `try`. The
    exception then escapes `prepare_env` and this arm fails on the raise. What
    an escape *costs* is plan correction 21, measured by H9b rather than
    re-measured here: `main`'s `except PublishableError` handler uses no
    `Collector` and prints `{exc}` verbatim. It cannot be re-measured through
    `reproduce` at this commit, because nothing dispatches the command yet —
    handed to the dispatch task, and stated rather than claimed.
    """
    monkeypatch.setenv("H9C_R_TOKEN", _R_TOKEN)
    fx = _fixture_r(tmp_path, _R_RAISING_TEMPLATE)
    lines, code, c, seen = _prepare_env(fx["record"], fx["dest"])
    assert code == EXIT_WRONG, seen
    assert [f.code for f in c.findings] == ["E-TEMPLATE-LOAD"], seen
    # The fixture must actually carry the value it redacts.
    assert _R_TOKEN in "\n".join(f.message for f in c.findings)
    rendered = c.render()
    assert _R_TOKEN not in rendered, rendered
    assert "<redacted:H9C_R_TOKEN>" in rendered, rendered
    # Step 6's first half still ran and still reported — a refusal in the
    # second half does not silently swallow the first.
    assert any(line.startswith(".env: written from") for line in lines), lines


def test_fixture_r_the_positive_control_validate_over_the_identical_project(
    tmp_path: Path, monkeypatch, capsys, _r_sys_path
):
    """The control that caught the original: `validate` over the identical
    project printing `<redacted:…>`. It reaches `main` — the surface a leak
    would land on — and it is what makes the arm above a comparison rather
    than a claim about one function."""
    monkeypatch.setenv("H9C_R_TOKEN", _R_TOKEN)
    fx = _fixture_r(tmp_path, _R_RAISING_TEMPLATE)
    capsys.readouterr()
    assert main(["validate", str(fx["cfg"])]) == EXIT_WRONG
    out = capsys.readouterr()
    both = out.out + out.err
    assert "E-TEMPLATE-LOAD" in both, both
    assert _R_TOKEN not in both, both
    assert "<redacted:H9C_R_TOKEN>" in both, both


def test_fixture_r_a_local_templates_required_env_is_listed(tmp_path: Path, _r_sys_path):
    """A project-local template DOES resolve in this interpreter, so its
    `required_env` is listed — the honouring half of Decision 12's narrowing,
    without which the two deferral branches below would be the only thing
    tested."""
    fx = _fixture_r(tmp_path, _R_INSERTING_TEMPLATE)
    lines, code, c, seen = _prepare_env(fx["record"], fx["dest"])
    assert code is None, seen
    assert (
        "required_env: template `cred_assay` declares H9C_R_TOKEN — each needs a value "
        "in `.env` or in the shell" in lines
    ), lines


def test_a_templates_own_sys_path_insert_does_not_survive_discovery(tmp_path: Path, _r_sys_path):
    """**The prescribed `pop(0)` mutation is BLIND at this call site, and this
    arm is the measurement that says why.**

    `templates.discovery._import_file` snapshots `sys.path` and restores it
    **wholesale** (`sys.path[:] = before_path`) around every `templates/*.py`
    it executes. So a template's own `sys.path.insert(0, …)` is visible during
    `exec_module` and gone afterwards, and by the time `prepare_env`'s
    `finally` runs, `sys.path[0]` **is** `prepare_env`'s own entry — a `pop(0)`
    removes exactly what `remove(src_entry)` removes. Measured, both by a
    throwaway probe printing `sys.path[:3]` at three points and by this arm.

    The three arms that replace that mutation are the two below and
    `test_the_window_is_load_bearing_*`: the insert is load-bearing, the
    restoration is total on both paths, and the purge is load-bearing. Each of
    those can fail; this one cannot be made to.
    """
    fx = _fixture_r(tmp_path, _R_INSERTING_TEMPLATE)
    before = list(sys.path)
    lines, code, c, seen = _prepare_env(fx["record"], fx["dest"])
    assert code is None, seen
    # The template really did insert — the resolution succeeded, so its top
    # level ran — and the entry is nevertheless gone.
    assert any("declares H9C_R_TOKEN" in line for line in lines), lines
    assert "/h9c/vendored" not in sys.path
    assert sys.path == before


def test_the_window_is_load_bearing_a_template_may_import_from_the_checkouts_src(
    tmp_path: Path, _r_sys_path
):
    """**The arm that makes the `sys.path` window non-decorative.** A
    project-local template importing its own project's package at module scope
    resolves only because `<dest>/src` is on the path — `discover_local`
    imports templates by path and puts `<root>/src` on `sys.path` nowhere. With
    the insert removed this arm fails: the import raises
    `ModuleNotFoundError`, `E-TEMPLATE-LOAD` is reported and no `required_env`
    line is printed at all.

    The observable is the transcript line rather than the absence of an
    exception, because a control asserting only absences passes identically if
    nothing ran: the imported module supplies the very name the line prints.
    """
    fx = _fixture_r(tmp_path, _R_SRC_IMPORTING_TEMPLATE)
    (fx["dest"] / "src" / "cohort_pilot" / "h9c_marker.py").write_text('MARKER = "H9C_FROM_SRC"\n')
    before = list(sys.path)
    lines, code, c, seen = _prepare_env(fx["record"], fx["dest"])
    assert code is None, seen
    assert any("declares H9C_FROM_SRC" in line for line in lines), seen
    assert sys.path == before


def test_the_root_package_purge_is_load_bearing_across_two_checkouts(tmp_path: Path, _r_sys_path):
    """The purge, armed. Two checkouts, **the same package name** — `publishable
    new` derives it from the experiment name, so `cohort_pilot` is both — whose
    templates import `cohort_pilot.h9c_marker` for two different values.

    `_import_file`'s own `sys.modules` restore does not cover this: it
    un-imports only entries `_is_local` places under `templates/`, and a module
    imported out of `<dest>/src` is not one. Without the purge the second
    checkout's template is served the first's module and this arm reads
    `H9C_FIRST` where it must read `H9C_SECOND`.
    """
    first = _fixture_r(tmp_path / "one", _R_SRC_IMPORTING_TEMPLATE)
    (first["dest"] / "src" / "cohort_pilot" / "h9c_marker.py").write_text('MARKER = "H9C_FIRST"\n')
    second = _fixture_r(tmp_path / "two", _R_SRC_IMPORTING_TEMPLATE)
    (second["dest"] / "src" / "cohort_pilot" / "h9c_marker.py").write_text(
        'MARKER = "H9C_SECOND"\n'
    )

    lines, code, c, seen = _prepare_env(first["record"], first["dest"])
    assert code is None, seen
    assert any("declares H9C_FIRST" in line for line in lines), seen

    lines, code, c, seen = _prepare_env(second["record"], second["dest"])
    assert code is None, seen
    assert any("declares H9C_SECOND" in line for line in lines), seen
    assert not any("H9C_FIRST" in line for line in lines), lines


def test_the_sys_path_entry_is_removed_on_the_failure_path_too(
    tmp_path: Path, monkeypatch, _r_sys_path
):
    """The restoration is pinned on the FAILURE path — the half a `finally`
    buys and a trailing `sys.path.remove` would not. The template both inserts
    and raises, so a build restoring only on success leaks here."""
    monkeypatch.setenv("H9C_R_TOKEN", _R_TOKEN)
    fx = _fixture_r(tmp_path, _R_RAISING_AND_INSERTING_TEMPLATE)
    src_entry = str(fx["dest"] / "src")
    lines, code, c, seen = _prepare_env(fx["record"], fx["dest"])
    assert code == EXIT_WRONG, seen
    assert src_entry not in sys.path, sys.path[:5]
    assert _R_TOKEN not in c.render(), c.render()


def test_an_installed_template_names_its_plugin_and_defers_to_validate(
    installed, registries, tmp_path: Path
):
    """Correction 8, measured: `get_template` returns `None` for an installed
    template — the claim carries `cls=None` — and the plugin is installed in
    the CHECKOUT's environment by `uv sync`, not in this one. So the list is
    unbuildable in-process and the transcript names the template and its
    plugin instead. **This is the document narrowing task 13 owes prose for.**

    The template name is genuinely claimed by an installed distribution here,
    and `get_template` returning `None` for it is asserted directly, so the
    branch is reached for the documented reason rather than because the name
    was unknown — which the arm below is the control for.
    """
    installed("dist-h9c-r", "1.0", {"publishable.templates": {"llm_assay": "h9c_r_mod:Assay"}})
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    from publishable.templates.registry import get_template as _get
    from publishable.templates.registry import template_provenance as _prov

    assert _get("llm_assay", dest) is None
    assert _prov("llm_assay", dest) == "installed"

    fx["record"]["config"]["experiment_type"] = "llm_assay"
    fx["record"]["config"]["plugin"] = "someuser/publishable-llm@v1.2.0"
    lines, code, c, seen = _prepare_env(fx["record"], dest)
    assert code is None, seen
    deferred = [line for line in lines if line.startswith("required_env:")]
    assert len(deferred) == 1, lines
    assert "someuser/publishable-llm@v1.2.0" in deferred[0]
    assert "`validate` below reads its `required_env`" in deferred[0]


def test_a_name_no_template_claims_is_reported_as_such_rather_than_as_a_plugin(
    tmp_path: Path,
):
    """The control for the arm above: an unknown name and an installed name
    both make `get_template` return `None`, so a build branching on that alone
    would call every unknown name a plugin. `template_provenance` is what tells
    them apart, and this is the arm that proves it is consulted."""
    fx = _fixture_a(tmp_path)
    dest = _prepared_checkout(tmp_path, fx)
    fx["record"]["config"]["experiment_type"] = "no_such_template"
    lines, code, c, seen = _prepare_env(fx["record"], dest)
    assert code is None, seen
    assert "required_env: no template registers `no_such_template` in this interpreter, so "
    assert any("no template registers `no_such_template`" in line for line in lines), lines
    assert not any("plugin" in line for line in lines), lines
