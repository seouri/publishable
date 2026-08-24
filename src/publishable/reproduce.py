# src/publishable/reproduce.py
"""`reproduce`. docs/reference.md § Reproducing on another device.

**Ruling Y.** `reproduce` takes a path and nothing else, and it does not
resolve a target device: *"reproducing on another device"* names where the
user is, not an argument. There is no `--into`, no host, no user, no key and no
behaviour-changing environment variable — `reproduce` runs **on** the other
device against a record it is given. What remains is *which* path, and that is
what this module's first half answers.

**Nothing here writes to disk.** The destination derivation, the clone and the
environment restoration arrive with their own tasks; this module opens with
the reader so that a bad operand is refused before anything is created.

See `docs/superpowers/specs/2026-08-24-reproduce-design.md` § Decision 1 for
the five verdicts and the grounds each rests on.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from publishable.diagnostics import EXIT_EXTERNAL, EXIT_WRONG, Collector
from publishable.errors import ContractError
from publishable.hashes import code_hash_of, hashed_files
from publishable.lineage import read_record_file
from publishable.provenance import find_repo_root, unignored_under_hashed_trees


@dataclass(frozen=True)
class Record:
    """An accepted run record — the run-directory form or the bundle form.

    `path` is kept beside `doc` because the two accepted record forms differ in
    what sits *beside* the file, not in the file itself: `environment/uv.lock`
    is reachable next to a run directory's `run.yaml` and is a dangling
    reference from a bundle member (design § 0.6). A later step probes for it,
    and it needs the path this record was read from to do that.
    """

    doc: dict[str, Any]
    path: Path


@dataclass(frozen=True)
class ConfigOperand:
    """An accepted config file — § Reproducing's steps 4 onward.

    No `doc`: the config form re-reads the file through the same path `run`
    takes, rather than carrying a parse this module made for discrimination
    only. Carrying it would create a second source of truth for what the
    config says, which is the shape Decision 11 refuses for the byte copy.
    """

    path: Path


Operand = Record | ConfigOperand


def _refuse_operand(path: Path, c: Collector, what: str) -> None:
    """`E-REPRODUCE-OPERAND`, always naming what a usable operand would be.

    One helper rather than five call sites spelling the remedy five ways: the
    remedy is the same sentence in every branch — a run record file or a config
    file — and only `what` (the fault this operand has) differs.
    """
    c.error(
        "E-REPRODUCE-OPERAND",
        str(path),
        f"{what} — `reproduce` takes a run record file (a run directory's own "
        "`run.yaml`, or a bundle member such as `main.run.yaml`) or a config file",
    )


def classify_operand(path: Path, c: Collector) -> Operand | None:
    """One YAML parse, then three structural questions. Design Decision 1.

    **NOT by basename.** A bundle member is `main.run.yaml`, not `run.yaml`
    (measured: the bundle `study add` writes holds `study.yaml` and
    `main.run.yaml` and no directory), so `endswith("run.yaml")` is the
    reserved-name proxy this repo has already paid for at a `report_by`
    stratum — a name standing in for a structural fact. The structural facts
    are: a mapping holding `run_id` is a record; a mapping holding `runs` is a
    bundle root; a mapping holding `provenance` or `results` and no `run_id` is
    an **edited** record; a mapping holding `experiment_type` and none of the
    above is a config.

    **`runs` is the bundle root's key**, read out of `study.py` rather than
    guessed from § Building one's documented example: `study_new` writes
    `{"title", "authors", "runs"}` and `study_add` adds `runs[<name>] =
    {"file", "run_id"}` plus an optional `code` block. Neither `study` nor
    `members` appears anywhere in that module, and the member NAMES are
    `runs`'s keys.

    **Every refusal is appended to `c`, never raised.** `main`'s
    `except PublishableError` handler applies no redaction pass (measured by
    H9b), so a refusal raised out of here would reach a reader un-redacted;
    the caller owns a `Collector` carrying the credential values core read, and
    `render` is where redaction happens. `read_record_file`'s own three
    refusals are caught and re-reported through `c` **with their own codes
    intact** — H9c is that reader's fifth caller and mints no refusal of its
    own for the parse.

    Returns `None` exactly when something was appended to `c`.
    """
    if path.is_dir():
        # `resume` is the one command that takes a run DIRECTORY, and giving
        # `reproduce` the same operand for the opposite action is precisely
        # the confusion this refuses. The message supplies the one path
        # component the user is missing, which is what makes the refusal
        # cheap rather than obstructive.
        _refuse_operand(
            path,
            c,
            f"is a directory, not a file — `resume` takes a run directory and "
            f"`reproduce` takes the record inside one, so this is most likely "
            f"{path / 'run.yaml'}",
        )
        return None

    try:
        text = path.read_text()
        doc = yaml.safe_load(text)
    except (OSError, yaml.YAMLError) as exc:
        # `E-IO-FAILED`, joining `diff`'s and `resume`'s precedent rather than
        # minting a code of this slice's own: a path that cannot be read or
        # parsed is not a statement about `reproduce` at all. A missing path
        # reaches this branch too, and deliberately does not reach
        # `read_record_file`'s `E-UPSTREAM-RECORD-MISSING` — that code names a
        # run whose record is missing, and here we do not yet know the operand
        # was meant to be a record.
        c.error("E-IO-FAILED", str(path), f"could not be read as YAML: {exc}")
        return None

    if not isinstance(doc, dict):
        _refuse_operand(path, c, f"parsed to {type(doc).__name__}, not a mapping")
        return None

    if "runs" in doc:
        runs = doc.get("runs") or {}
        names = sorted(runs) if isinstance(runs, dict) else []
        # The members are LISTED, not counted. A count tells a reader how many
        # paths exist and none of what to type; the list is the remedy. And
        # `study new` writes `runs: {}`, so the empty bundle is its own
        # sentence rather than a list that reads as naming the first member.
        held = (
            "it holds " + ", ".join(f"`{name}.run.yaml`" for name in names)
            if names
            else "it holds no runs yet — add one with `study add`"
        )
        c.error(
            "E-REPRODUCE-BUNDLE",
            str(path),
            f"is a study bundle's own `study.yaml`, not a run record; {held}. "
            "Give `reproduce` the member you want",
        )
        return None

    if "run_id" in doc:
        try:
            return Record(read_record_file(path), path)
        except ContractError as exc:
            c.error(exc.code or "E-IO-FAILED", str(path), str(exc))
            return None

    if "provenance" in doc or "results" in doc:
        # An edited record, and it is refused rather than READ AS A CONFIG. A
        # record with its `run_id` removed has no `experiment_type` either, so
        # the fall-through would refuse it anyway — but it would refuse it as
        # "not a config", which sends the reader to the wrong file. The two
        # readings are genuinely different and this branch is what separates
        # them.
        _refuse_operand(
            path,
            c,
            "carries a run record's `provenance`/`results` but no `run_id`, so it is "
            "a record that was edited or truncated rather than a config",
        )
        return None

    if "experiment_type" in doc:
        return ConfigOperand(path)

    _refuse_operand(path, c, "is neither a run record nor a config")
    return None


# --------------------------------------------------------------------------
# The destination, and the clone. Design Decisions 7, 8 and 9, plus the
# thirteenth code (plan correction 26).
# --------------------------------------------------------------------------


_CLONE_CONFIG = ("-c", "core.autocrlf=false")
"""ONE flag, measured, and it is passed at BOTH placements.

Under an ambient `core.autocrlf = true`, a plain clone of a commit whose blobs
hold LF checks the working tree out with CRLF, so the file *contents*
`code_hash` folds over are different bytes and a faithful clone reports a
`code_hash` that does not match the record. `-c core.autocrlf=false` restores
the recorded digest; `-c core.eol=lf` alone does not change it at all. H6a
Ruling M's precedent is ONE ARM PER FLAG, so `core.eol=lf` is dropped rather
than passed: a flag with no arm is a flag nobody can prove is doing anything.

**The ground for neutralizing at all is H6a Ruling F's own**: a rule that does
not travel with the tree cannot define the tree's identity. Ruling M declined
to neutralize `core.autocrlf` FOR THE DIRTY GATE, and the H6a ledger states
the distinction in as many words — a gate answers "may this run proceed here",
which is local by nature; a hash answers "is this the same code", which is
not. `reproduce` is not a gate.

**NOT neutralized:** `core.excludesFile`, because the `.gitignore` files that
decide `code_hash` are TRACKED and travel with the commit, so a fresh clone has
no untracked exclude rule for the flag to reach; and a tracked `.gitattributes`,
which is out of reach BY RULING (design Decision 7) and is one of the
`code_hash` difference's enumerated candidate causes instead.

**`provenance.py`'s `_NEUTRALIZED_CONFIG_ARGS` is deliberately not shared.**
That tuple belongs to the dirty gate and the hash predicate and answers a
different question — which files does git consider — and reusing it here
because it happens to contain a `-c` would be the copied-recipe fault.
"""


@dataclass(frozen=True)
class Checkout:
    """A prepared checkout: the destination that now holds the recorded tree."""

    dest: Path


@dataclass(frozen=True)
class Refused:
    """A refusal already reported into the caller's `Collector`."""

    exit_code: int


Prepared = Checkout | Refused


def destination_for(record: dict[str, Any], *, cwd: Path) -> Path:
    """The derived destination: `<remote's last component>_<run_id>`, under `cwd`.

    § Reproducing on another device's own worked example is
    `my-study_run_2026-08-06T14-02-11Z_8e21ab3/`, and it is created **relative
    to the working directory**, which is where the user is.

    **`provenance.git.repo_root` is not an input.** It is
    `<redacted by study add>` in a bundle member, so a derivation reading it
    would work in the run-directory form and produce the redaction marker as a
    directory name in the bundle form. The remote is the only name that travels
    in both.

    The last component is taken by splitting on `/`, which is correct for an
    `https://` URL, for a `git@host:owner/name.git` scp-style remote, and for a
    filesystem path alike, and a single trailing `.git` is removed. A remote
    holding no `/` at all is used whole rather than being refused: it is a
    named git remote alias, and a derived name of `""` would be worse than an
    unusual one.
    """
    remote = str(record["provenance"]["git"]["remote"]).rstrip("/")
    last = remote.rsplit("/", 1)[-1]
    if last.endswith(".git"):
        last = last[: -len(".git")]
    return cwd / f"{last}_{record['run_id']}"


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    """One place the subprocess convention lives: capture both streams, never
    check, and let the caller read `returncode` and report the message git
    actually produced. A `check=True` here would raise into `main`, which
    applies no redaction pass."""
    return subprocess.run(args, capture_output=True, text=True)


def prepare_checkout(operand: Record, c: Collector, *, cwd: Path) -> Prepared:
    """Derive the destination, refuse it if it cannot be used, clone, check out.

    Takes the `Record` rather than its `doc`, because the record's own PATH is
    an input later steps need (the `environment/uv.lock` byte copy is reachable
    beside a run directory's `run.yaml` and dangling from a bundle member) and
    because it is the operand a wrong walk-up would reach for: the guard below
    walks up from the DESTINATION'S PARENT, and having the operand in scope is
    what makes that a decision rather than an accident of the signature.

    The order is: the remote must exist, the destination must not, the
    destination must not nest, then two git invocations. **Nothing is created
    before the last of the three refusals**, which is why Fixture K asserts the
    destination's absence rather than only the code — derive-then-refuse and
    refuse-then-derive are otherwise indistinguishable.

    **Two git invocations, and each `-c` placement has its own job**
    (design Decision 7, plan correction 1). Measured on git 2.50.1: the
    **`clone -c`** placement is the load-bearing one — it stores
    `core.autocrlf=false` into the new repo's `.git/config`, so the
    `checkout --detach` below and any later `git checkout` in the prepared tree
    do not re-convert; with the leading `git -c` alone the clone's config reads
    `true` and a re-materialized file comes back CRLF. The leading `git -c` is
    kept because it is what the design decided and because it costs nothing,
    but this build could not arm it by hash: on this git the initial checkout
    honours either placement on its own. That measurement disagrees with
    Decision 7's, is reported rather than papered over, and is why the arm on
    this pair asserts the stored config and the flag list rather than only a
    digest.

    **Exit codes.** `E-REPRODUCE-NO-REMOTE`, `E-REPRODUCE-DEST-EXISTS` and
    `E-REPRODUCE-DEST-IN-REPO` are exit `1`: nothing outside the machine
    refused, and § Exit codes' `5` is *"a clone or `uv sync` that failed"* — a
    clone that was **attempted**. Keeping `1` here is what preserves `5` as the
    retry class. A clone that fails, and a recorded commit the remote does not
    hold, are exit `5`.

    **A failed clone carries `E-IO-FAILED` and mints no code.** Decision 14's
    table gives a failed clone no row at all while Decision 7 promises it exit
    `5`, so this build follows Decision 14's own stated device — *"`E-IO-FAILED`
    covers an unreadable operand path, joining `diff`'s and `resume`'s
    precedent rather than getting a thirteenth code"* — and the shipped
    `EXIT_EXTERNAL` precedent, which is `command_run` returning `5` under the
    already-existing `E-APPARATUS-RAISED` rather than under a code minted for
    the exit. The count therefore stays at thirteen. Reported as a
    design-versus-code disagreement.
    """
    record = operand.doc
    git = record["provenance"]["git"]
    commit = git.get("commit")

    if git.get("remote") is None:
        # § 0.8: this is the ORDINARY state of a scaffolded project with one
        # local commit, not an edge case — so the message has to leave the
        # reader somewhere useful. It names the recorded commit, because a
        # reader who has the repository can check that out themselves, which
        # is the whole of what `reproduce`'s first step would have done.
        c.error(
            "E-REPRODUCE-NO-REMOTE",
            "provenance.git.remote",
            f"is null, so there is no repository to clone — this run was made in a "
            f"local-only repository. If you have that repository, "
            f"`git checkout --detach {commit}` in it is the tree this record was "
            f"made from",
        )
        return Refused(EXIT_WRONG)

    dest = destination_for(record, cwd=cwd)

    if dest.exists():
        # The creation-command family's rule — refusing is how one stays safe
        # to re-run — and it is also the sentence § Reproducing on another
        # device gets wrong: *"it can't collide with an existing checkout"* is
        # false, because a second `reproduce` of one record derives the same
        # name twice. Decision 9 narrows the claim to what is true.
        c.error(
            "E-REPRODUCE-DEST-EXISTS",
            str(dest),
            "already exists — `reproduce` derives its destination and never overwrites "
            "one, so a second reproduction of the same run refuses rather than "
            "replacing the first; move or remove it, or run from another directory",
        )
        return Refused(EXIT_WRONG)

    try:
        enclosing: Path | None = find_repo_root(dest.parent)
    except ContractError:
        # `find_repo_root` RAISES `E-GIT-NO-REPO` rather than returning `None`,
        # so the ordinary case — a destination outside any repository — is this
        # exception path. Written this way round on purpose: the alternative
        # reading, that a raise means "refuse", inverts the guard.
        enclosing = None

    if enclosing is not None:
        # The walk-up is from the DESTINATION'S PARENT, never from the operand:
        # the operand is a record that may live anywhere (a bundle beside a
        # manuscript, a run directory under `output_dir`), and what must not
        # nest is the checkout. Nesting a reproduction inside another
        # experiment's repository makes every walk-up question — which repo,
        # which `code_hash`, which dirty gate — answerable two ways, which is
        # what `CLAUDE.md`'s `input_dir`/`output_dir` invariant exists to
        # prevent.
        c.error(
            "E-REPRODUCE-DEST-IN-REPO",
            str(dest),
            f"would sit inside the git repository at {enclosing} — a reproduction is a "
            "checkout of its own and may never nest inside another repository, because "
            "every walk-up afterwards would have two answers; run `reproduce` from a "
            "directory outside any repository",
        )
        return Refused(EXIT_WRONG)

    clone = _git(["git", *_CLONE_CONFIG, "clone", *_CLONE_CONFIG, str(git["remote"]), str(dest)])
    if clone.returncode != 0:
        c.error(
            "E-IO-FAILED",
            str(git["remote"]),
            f"could not be cloned into {dest}: {clone.stderr.strip() or clone.stdout.strip()}",
        )
        return Refused(EXIT_EXTERNAL)

    checkout = _git(["git", "-C", str(dest), "checkout", "--detach", str(commit)])
    if checkout.returncode != 0:
        # A REWRITTEN OR FORCE-PUSHED HISTORY IS CAUGHT HERE, not by the hash
        # (plan correction 26): a commit SHA is a hash over its own tree, so a
        # different tree cannot live at the same SHA. What a rewrite actually
        # produces is a remote that no longer holds the recorded object, and
        # that is a failed checkout. The checkout is LEFT on disk: the clone
        # succeeded and its other refs are worth having.
        c.error(
            "E-REPRODUCE-COMMIT-UNREACHABLE",
            str(commit),
            f"is not reachable in the clone of {git['remote']} — the remote no longer "
            f"holds that commit, which is what a rewritten or force-pushed history "
            f"leaves behind. The clone is at {dest}; git said: "
            f"{checkout.stderr.strip() or checkout.stdout.strip()}",
        )
        return Refused(EXIT_EXTERNAL)

    return Checkout(dest)


# --------------------------------------------------------------------------
# `code_hash` in the checkout. Design Decisions 2 and 10, Ruling Z.
# --------------------------------------------------------------------------


_CODE_HASH_CAUSES = (
    "`reproduce` cannot tell these apart, and does not guess between them:",
    "  - the code at that commit really is different: a rewritten or force-pushed",
    "    history;",
    "  - the record predates the redefinition of WHICH files are hashed. No key in",
    "    `run.yaml` can date a record — `schema_version` was deliberately not bumped —",
    "    and `uv_lock_hash` is the only carrier, which a scaffolded project does not",
    "    have at all;",
    "  - this machine's git materialized the tree differently: `core.autocrlf`, which",
    "    the clone neutralizes, or a tracked `.gitattributes`, which it may not.",
)
"""The closed candidate set, and it is a set rather than a verdict.

**Ruling Z.** § Reproducing on another device says a `code_hash` mismatch
catches *"a rewritten or force-pushed history"*. That is measured false three
ways — across the redefinition of which files are hashed, under an ambient
`core.autocrlf`, and under a tracked `.gitattributes` — so printing it would be
a cause invented from a symptom. **Naming a closed candidate set is not a
verdict; picking one is**, and nothing here asserts a single cause.

**No marker is minted** to tell the first case from the second: H6a's Ruling C
refused a definition marker, and the scoping's § 12 lists it under what H9 may
not fold in. The honest consequence is that the two stay indistinguishable, and
saying so is the deliverable.
"""


def verify_code_hash(operand: Record, dest: Path, c: Collector) -> tuple[list[str], int | None]:
    """Recompute `code_hash` over the checkout and compare. Decisions 2 and 10.

    The predicate is **exactly** `command_run`'s, in the pair form — `hashed_files`
    then `code_hash_of` — rather than `code_hash(root, include)`, because Decision
    2 prints the file COUNT and the file LIST and only the pair form hands them
    back. That is what `code_hash_of` was extracted for.

    Returns `(transcript lines, exit code or None)`. A refusal's one-line
    summary goes into `c` and the file list and the candidate causes go into the
    lines, because `Collector.render` indents one continuation line per finding
    and a nine-line message rendered through it would be unreadable. What a
    reader sees is the two together, and that is what the arms assert on.

    **The checkout is KEPT on a refusal.** The deliverable of `reproduce` is a
    prepared checkout, and a stop that discards its own artifacts is the fault
    H9b closed at exit `4` — *a stop must be legible from the artifacts*.

    **A `draft` record declines the verification rather than failing it**
    (Decision 10). The record says the tree was never reachable from any
    commit, so the comparison has no operand worth reporting a verdict on.
    This is the ONE cause `reproduce` names, and it is named because the record
    names it — the same posture § Reproducing already takes for the config
    form, which *"cannot verify a `code_hash` and says so, rather than
    reporting a match it never made."*
    """
    record = operand.doc
    recorded = record.get("code_hash")

    if record.get("draft"):
        return (
            [
                "code_hash: this record is a draft: its code was not committed, so "
                "`code_hash` is not verified",
                f"           the checkout is at {dest}",
            ],
            None,
        )

    pairs = hashed_files(dest, lambda cands: unignored_under_hashed_trees(dest, cands))
    computed = code_hash_of(pairs)

    if computed == recorded:
        return ([f"code_hash: matches the record over {len(pairs)} files ({computed})"], None)

    c.error(
        "E-REPRODUCE-CODE-HASH",
        str(dest),
        f"does not reproduce the recorded code_hash: the record says {recorded}, this "
        f"checkout hashes {computed} over {len(pairs)} files. The checkout is kept",
    )
    lines = [f"code_hash: the {len(pairs)} files folded were:"]
    lines += [f"  {rel}" for rel, _ in pairs]
    lines += list(_CODE_HASH_CAUSES)
    return (lines, EXIT_WRONG)
