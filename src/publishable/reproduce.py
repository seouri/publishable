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

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from textwrap import indent
from typing import Any

import yaml

from publishable.diagnostics import EXIT_EXTERNAL, EXIT_OK, EXIT_WRONG, Collector
from publishable.errors import ContractError, PublishableError
from publishable.hashes import code_hash_of, hashed_files, parameters_hash
from publishable.lineage import read_record_file
from publishable.provenance import find_repo_root, unignored_under_hashed_trees
from publishable.secrets import credential_values
from publishable.templates.registry import get_template, template_provenance
from publishable.validate import declared_credential_names_for


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


# --------------------------------------------------------------------------
# The environment. Design Decision 3 (Ruling AA) and Decision 6.
# --------------------------------------------------------------------------


def _sha256_of(path: Path) -> str:
    """`uv_support.uv_lock_info`'s own spelling of the digest, `sha256:` prefix
    included, so the two answers are comparable.

    `uv_lock_info` itself is deliberately NOT called: it answers *what does this
    repo hold now*, taking a repo root and looking for `uv.lock` beneath it,
    which is a different question from *what is the digest of this particular
    file* — and the two lockfiles this function is asked about live at two
    paths neither of which is a repo root's `uv.lock` in the sense that helper
    means.
    """
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def restore_environment(operand: Record, dest: Path, c: Collector) -> tuple[list[str], int | None]:
    """Decision 3's ranking, in order, each step printing what it found.

    **Ruling AA: the two lockfile sources are both real and neither is
    preferred silently.** Measured — a run records an **untracked** `uv.lock`
    into `environment/uv.lock` while `git clone` of the recorded commit has
    **none**, because the dirty gate's pathspec is the hashed trees only. The
    recorded `uv_lock_hash` is the authority; the run directory's byte copy is
    the preferred carrier, because it is what the run actually used, while the
    clone's committed lockfile is a claim about the commit. Where they
    disagree, the disagreement is the interesting fact and is **printed rather
    than resolved.**

    **"Reachable beside the operand" is a FILESYSTEM PROBE, and this says so**
    (plan correction 28). The test is
    `(<operand>.parent / "environment" / "uv.lock").is_file()` — a probe for a
    file, not a structural fact about which form the operand is. It is correct
    for both measured forms, and it is stated because a bundle placed *inside*
    a run directory would take the run-directory branch. What makes the probe
    safe rather than a proxy is the digest check that follows it:
    `E-REPRODUCE-LOCKFILE-EDITED` fires when the copy's sha256 does not match
    the record's `uv_lock_hash`, so a foreign copy is refused rather than used.

    **`pyproject.toml` is a third input** (§ 0.7), found **by convention and
    not by record** — `provenance.environment` names `uv_lock` and no
    `pyproject.toml` at all. It is compared and reported **before** `uv sync`
    speaks, because it is the input that explains a `uv sync --locked` failure
    a reader would otherwise have to guess at. It is **not copied in**: it is a
    tracked file at the recorded commit, and overwriting the commit's own
    manifest with an uncommitted edit would make the checkout a tree that
    exists nowhere. And it **does not refuse**.

    Returns `(transcript lines, exit code or None)`, the same contract
    `verify_code_hash` uses.
    """
    record = operand.doc
    env = (record.get("provenance") or {}).get("environment") or {}
    recorded_digest = env.get("uv_lock_hash")
    clone_lock = dest / "uv.lock"
    lines: list[str] = []

    if recorded_digest is None:
        # Decision 6 (Q3). The checkout is KEPT and the closing transcript is
        # printed with the `uv sync` line replaced by the stated gap: exit `1`
        # because nothing outside the machine refused — `5`'s class is the one
        # you retry — and the thing you asked about is genuinely wrong, since
        # you asked to reproduce a run whose environment was never pinned.
        # This is what `W-ENV-UNLOCKED`'s shipped message already promises:
        # *"`reproduce` will not be able to restore it"*.
        c.error(
            "E-REPRODUCE-UNLOCKED",
            "provenance.environment.uv_lock_hash",
            "is null: this run pinned no environment, so there is no lockfile to "
            "restore one from and `uv sync --locked` has nothing to check against. "
            f"The checkout is kept at {dest}; `uv sync` in it would resolve a NEW "
            "environment, which is not the one the recorded numbers came through",
        )
        lines.append("uv sync: not run — the record pinned no environment")
        return (lines, EXIT_WRONG)

    byte_copy = operand.path.parent / "environment" / "uv.lock"
    if byte_copy.is_file():
        copy_digest = _sha256_of(byte_copy)
        if copy_digest != recorded_digest:
            c.error(
                "E-REPRODUCE-LOCKFILE-EDITED",
                str(byte_copy),
                f"hashes {copy_digest}, and the record says {recorded_digest} — the "
                "run directory's own copy of the lockfile was edited after the run, so "
                f"it is not the environment these numbers came through. The checkout is "
                f"kept at {dest}",
            )
            return (lines, EXIT_WRONG)

        # The clone's own lockfile is REPORTED before it is overwritten. Never
        # silently replaced without the line: a reader whose commit carries a
        # different lockfile than the run used has learned something, and it is
        # the one fact this step is in a position to tell them.
        if not clone_lock.is_file():
            lines.append("uv.lock: the commit carries none; restored from the run's own copy")
        elif _sha256_of(clone_lock) == recorded_digest:
            lines.append("uv.lock: the commit's copy is identical to the run's")
        else:
            lines.append(
                f"uv.lock: DIFFERS — the commit carries {_sha256_of(clone_lock)} and the "
                f"run used {recorded_digest}; the run's own copy is what is restored"
            )
        clone_lock.write_bytes(byte_copy.read_bytes())
        lines.append(f"uv.lock: restored from {byte_copy}")
    else:
        # The bundle form. `provenance.environment.uv_lock` survives `study add`
        # unredacted while the directory it points into is not in the bundle, so
        # the recorded path is a DANGLING reference and only the digest travels.
        # The clone's committed lockfile is used if and only if it matches.
        lines.append(f"uv.lock: the run's own copy is not reachable from {operand.path}")
        if clone_lock.is_file() and _sha256_of(clone_lock) == recorded_digest:
            lines.append(
                f"uv.lock: the commit's own copy matches the recorded {recorded_digest}, "
                "so it is what the environment is restored from"
            )
        else:
            held = _sha256_of(clone_lock) if clone_lock.is_file() else "no uv.lock at all"
            c.error(
                "E-REPRODUCE-LOCKFILE-UNREACHABLE",
                str(dest),
                f"holds {held}, and the record's environment is {recorded_digest} — no "
                "lockfile matching the record is reachable, so the environment these "
                "numbers came through cannot be rebuilt. A bundle carries no lockfile of "
                f"its own; the checkout is kept at {dest}",
            )
            return (lines, EXIT_WRONG)

    # Step 4, and it happens BEFORE `uv sync` on purpose.
    recorded_pyproject = operand.path.parent / "environment" / "pyproject.toml"
    clone_pyproject = dest / "pyproject.toml"
    if recorded_pyproject.is_file() and clone_pyproject.is_file():
        if recorded_pyproject.read_bytes() == clone_pyproject.read_bytes():
            lines.append("pyproject.toml: identical to the run's")
        else:
            lines.append(
                "pyproject.toml: DIFFERS — the run's copy is not byte-identical to the "
                f"commit's. Not copied in ({clone_pyproject} is the commit's own "
                "manifest); this is the input to check first if `uv sync --locked` fails"
            )
    elif not recorded_pyproject.is_file():
        lines.append(
            f"pyproject.toml: the run's own copy is not reachable from {operand.path}, "
            "so it is not compared"
        )

    sync = _uv_sync(dest)
    if sync.returncode != 0:
        c.error(
            "E-IO-FAILED",
            str(dest),
            f"`uv sync --locked` failed: {sync.stderr.strip() or sync.stdout.strip()}",
        )
        return (lines, EXIT_EXTERNAL)
    lines.append("uv sync: --locked, against the restored lockfile")
    return (lines, None)


def _uv_sync(dest: Path) -> subprocess.CompletedProcess[str]:
    """`uv sync --locked` in the checkout, as its own function.

    Separate from `_git` and from `restore_environment` for one reason worth
    stating: it is the **only** seam in this module that reaches a network and
    resolves a real dependency tree, so it is the one an arm has to observe
    rather than perform. A fixture's lockfile is *written*, never resolved —
    `uv lock` inside a scaffolded project fails outright — so no fixture in
    this slice can produce a lockfile a real `--locked` sync would accept, and
    an arm that ran it would be asserting on `uv`'s refusal rather than on this
    module's behaviour. The success path is therefore armed by observing this
    call's argv and cwd; the failure path is armed by letting it really run,
    where failure is the expected outcome.
    """
    return subprocess.run(["uv", "sync", "--locked"], cwd=dest, capture_output=True, text=True)


# --------------------------------------------------------------------------
# The config write-back. Design Decision 11.
# --------------------------------------------------------------------------


_PATH_MARKER = "# REQUIRED: set to your local copy"
_BLANKED = ("input_dir", "output_dir")


def config_dir_in(operand: Record, dest: Path, c: Collector) -> Path | None:
    """`<dest>/configs/<name>/`, where `<name>` is the record's
    `config.metadata.name`. Tasks 7 and 10 both write here.

    **`config.metadata.name` is the one name that travels in both operand
    forms, and that is measured rather than assumed.** The alternative was
    `identity.json`'s `config_path`, which is the field `generate experiment`'s
    own `configs/<name>/config.yaml` derivation would suggest — and plan
    correction 23 rules it out twice over: it is a *mid-run* reader's artifact,
    and a bundle has no `identity.json` at all. Measured on a real bundle
    member: `config.metadata.name` survives `study add` unredacted
    (`_redact` reaches `data.input_dir`/`output_dir`, `git.repo_root`,
    `environment.hostname` and `provenance.input_manifest`, and no key under
    `config.metadata`), while `data.input_dir` beside it reads
    `<redacted by study add>`. So the derivation that works in the
    run-directory form works in the bundle form, which is Ruling Y's own
    cost-if-wrong.

    **The refusal is containment only, and the code is `E-IO-FAILED`.** A
    record is a file, and a hand-edited `config.metadata.name` of `../../etc`
    would resolve outside the destination this command created — the one shape
    H8a's containment rule exists for, whose guard *"may be narrower than the
    gap it closes"*. Nothing is minted for it: Decision 14's own sentence gives
    `E-IO-FAILED` an unreadable operand path on `diff`'s and `resume`'s
    precedent, and this is the same class of fault at the other end of the same
    record. Three shapes share the one code because they share the one remedy —
    the record's `config.metadata.name` is not usable as a directory name — and
    the message names which shape was found. **§ Errors' row for `E-IO-FAILED`
    owes this site a mention; task 14 owns the row.**
    """
    metadata = (operand.doc.get("config") or {}).get("metadata")
    name = metadata.get("name") if isinstance(metadata, dict) else None
    if not isinstance(name, str) or not name:
        c.error(
            "E-IO-FAILED",
            str(operand.path),
            "carries no `config.metadata.name`, so there is no `configs/<name>/` to "
            "write the config into — the record names no experiment",
        )
        return None
    configs = (dest / "configs").resolve()
    target = (configs / name).resolve()
    if target != configs and configs not in target.parents:
        c.error(
            "E-IO-FAILED",
            str(operand.path),
            f"has `config.metadata.name` of {name!r}, which resolves outside "
            f"{configs} — a config directory is a name, not a path out of the "
            "checkout",
        )
        return None
    return dest / "configs" / name


def _serialized_config(config: dict[str, Any]) -> str:
    """The record's embedded config, re-serialized, with `data.input_dir` and
    `data.output_dir` blanked and each marked.

    **Core generates this file; it does not patch one.** § Reproducing on
    another device says the two paths are *"blanked and **marked**
    `# REQUIRED: set to your local copy`"*, and a comment is something only a
    generator writes. The two marked lines below are emitted by this function
    rather than located inside somebody else's YAML text: locating two keys in
    arbitrary YAML to blank them is a text scan over a structure, which is the
    proxy this repo keeps paying for, and the byte copy that scan would run
    over does not exist in the bundle form at all (plan correction 24).

    Emitted key by key, in the record's own order, each piece through
    `yaml.safe_dump` and `data`'s sub-keys indented under it — so every value
    but the two blanked ones is serialized by the same library that parsed it,
    and the two blanked ones are literals this function owns. **Nothing here
    claims the assembly is faithful**: `write_config` re-reads the file and
    compares `parameters_hash` against the record's, which is the check that
    would catch a piece this loop dropped or retyped.

    **The comments `init` wrote are lost, and that is disclosed rather than
    worked around** (plan correction 25). `run.yaml`'s `config` is the parsed
    dict; no inline comment survives into it, so none can come back out.
    `write_config`'s transcript names where they still live.
    """
    out: list[str] = []
    for key, value in config.items():
        if key != "data" or not isinstance(value, dict):
            out.append(yaml.safe_dump({key: value}, sort_keys=False, allow_unicode=True))
            continue
        out.append("data:\n")
        for sub, sub_value in value.items():
            if sub in _BLANKED:
                out.append(f'  {sub}: ""   {_PATH_MARKER}\n')
                continue
            piece = yaml.safe_dump({sub: sub_value}, sort_keys=False, allow_unicode=True)
            out.append(indent(piece, "  "))
    return "".join(out)


def write_config(operand: Record, dest: Path, c: Collector) -> tuple[list[str], int | None]:
    """Write `configs/<name>/config.yaml` in the checkout. Decision 11.

    Returns `(transcript lines, exit code or None)`, the contract
    `verify_code_hash` and `restore_environment` already use.

    **The clone's own committed copy is hashed BEFORE it is overwritten**, and
    the ordering is the whole reason that comparison exists at all: the clone
    holds `configs/<name>/config.yaml` at the recorded commit, this function
    replaces it, and a comparison made afterwards would compare the file with
    itself. `parameters_hash` over a file is a pure function of the file, which
    is what § CLI reference already says of `diff`'s use of it.

    **`identical` or `DIFFERS`, beside `provenance.git.config_committed`, and
    neither is a refusal.** `config_committed` records whether the config was
    *tracked* at run time — measured: `git ls-files --error-unmatch` is what
    answers it, so an edit made after the commit leaves it `true` while the
    commit's bytes are the pre-edit ones. A `DIFFERS` under
    `config_committed: true` is therefore a real, reachable fact about the
    record rather than an impossible state, and it is reported because the
    reader has learned something: the numbers came through a config the
    recorded commit does not hold.

    **The write is self-checked, and this is the task's central assertion.**
    `hashes.covered_config` excludes `metadata`, `data.input_dir` and
    `data.output_dir` (plan correction 9, confirmed by measurement: the
    recorded `parameters_hash` is reproduced exactly by hashing the record's
    config with both paths blanked, and equally by deleting both keys), so the
    check below is **blind to the blanking and sensitive to a lossy round
    trip** — a re-serialization that drops or retypes a key moves the hash.
    Measured: retyping one `limits.max_executions` from `int` to `str` moves it
    from `sha256:4d1c41e…` to `sha256:e4fa612…`. That is the two branches that
    can differ, and it was checked before the check was written.

    **This function overwrites, and `write_expectation` beside it refuses to.
    The two policies are opposite on purpose.** A config is what `reproduce`
    is *for* — the clone's copy at the recorded commit is a claim about the
    commit and the record's is what produced the numbers, so the record wins
    and the fact is printed. `apparatus.expected.json` is a file
    § Reproducing on another device invites the reader to **edit**, so
    replacing one silently would discard a human decision. Neither policy is
    the other's precedent; do not make them agree.
    """
    record = operand.doc
    config = record.get("config")
    if not isinstance(config, dict):
        c.error(
            "E-IO-FAILED",
            str(operand.path),
            "carries no `config` mapping, so there is no config to write back",
        )
        return ([], EXIT_WRONG)

    config_dir = config_dir_in(operand, dest, c)
    if config_dir is None:
        return ([], EXIT_WRONG)
    target = config_dir / "config.yaml"
    lines: list[str] = []

    committed = record.get("provenance", {}).get("git", {}).get("config_committed")
    if target.is_file():
        # BEFORE the write below. See the docstring.
        try:
            existing = yaml.safe_load(target.read_text())
        except yaml.YAMLError:
            existing = None
        if isinstance(existing, dict):
            existing_hash = parameters_hash(existing)
            if existing_hash == record.get("parameters_hash"):
                lines.append(
                    "config.yaml: the commit's own copy is identical to the record's "
                    f"parameters (config_committed: {committed})"
                )
            else:
                lines.append(
                    f"config.yaml: DIFFERS — the commit's copy hashes {existing_hash} and "
                    f"the record's parameters are {record.get('parameters_hash')} "
                    f"(config_committed: {committed}); the RECORD's config is what is "
                    "written, since it is what produced the numbers"
                )
        else:
            lines.append(
                f"config.yaml: the commit's copy at {target} is not a YAML mapping, so it "
                "is not compared"
            )
    else:
        lines.append(
            f"config.yaml: the commit carries none at configs/{config_dir.name}/ "
            f"(config_committed: {committed})"
        )

    config_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(_serialized_config(config))

    written = yaml.safe_load(target.read_text())
    if not isinstance(written, dict) or parameters_hash(written) != record.get("parameters_hash"):
        got = parameters_hash(written) if isinstance(written, dict) else "not a YAML mapping"
        c.error(
            "E-REPRODUCE-CONFIG-WRITEBACK",
            str(target),
            f"was written from the record's own `config`, and hashes {got} against the "
            f"recorded parameters_hash of {record.get('parameters_hash')} — the "
            "re-serialization lost or retyped something, so this file is not the "
            f"declaration the run executed. The checkout is kept at {dest}",
        )
        return (lines, EXIT_WRONG)

    lines.append(f"config.yaml: written to {target}, parameters_hash matches the record")
    lines.append(
        f"config.yaml: `data.input_dir` and `data.output_dir` are blank and marked `{_PATH_MARKER}`"
    )
    # Plan correction 25, disclosed rather than worked around.
    comments_live = (
        f"{operand.path.parent / 'config.yaml'}"
        if (operand.path.parent / "config.yaml").is_file()
        else None
    )
    lines.append(
        "config.yaml: the inline comments `init` wrote are NOT restored — `run.yaml`'s "
        "`config` is the parsed mapping. They still live in "
        + (comments_live if comments_live else "no file reachable from this operand")
    )
    return (lines, None)


# --------------------------------------------------------------------------
# Step 6, narrowed: `.env` and `required_env`. Design Decision 12.
# --------------------------------------------------------------------------


def prepare_env(
    operand: Record, dest: Path, c: Collector
) -> tuple[list[str], int | None, list[str]]:
    """§ Reproducing on another device's step 6, in its narrowed form.
    Decision 12. Returns `(transcript lines, exit code or None)`.

    **`.env` is written from `.env.example` only when it does not exist.**
    `.env.example` is **tracked** (plan correction 15) — `scaffold.py` writes
    it and the scaffold's `.gitignore` opens with `.env`, not with the example —
    so the clone already holds it, and "copies `.env.example`" means
    `cp .env.example .env`, which is § The generated README's own setup line.
    An existing `.env` is never overwritten and the transcript says which of the
    three happened. The write is safe because `secrets.missing_env` treats an
    **empty** value as missing and a bare key parses to `None` and is skipped
    (plan correction 16), so a blank `.env` cannot turn a missing credential
    into a present one.

    **`required_env` is listed only for a template THIS interpreter can
    construct, and that is a document narrowing.** Plan correction 8, measured:
    `templates.registry.get_template` returns `None` for an installed
    template — `_claims` attaches `cls=None` to an entry-point claim and
    `_merged` keeps only claims with a class — and a plugin is not installed in
    `reproduce`'s interpreter at all, since `uv sync` installed it into the
    **clone's**. So for a plugin-provided template the list is unbuildable
    in-process, and this names the template and its plugin and **defers to the
    `validate` line the closing transcript already prints**: `validate` in the
    prepared checkout reads `required_env` itself (H7c gave it that reader) in
    the interpreter where the plugin exists. The reader is one step later and in
    the right place, which beats a subprocess this command would have to invent.
    **§ Reproducing on another device's step 6 must say so; task 13 owns the
    prose and this function is the measurement it rests on.**

    **Which names are listed, and which are not.** `required_env` only. The
    `Param(requires_env=)` names are per-choice and conditional, and `validate`
    in the checkout resolves them against the config's own values — so listing
    them here would be a second, weaker answer to a question the next command
    answers properly. They **are** collected for redaction below, which is a
    different use: redaction asks *what values did core read*, not *what must
    the reader supply*.

    **No name is reported as set or unset.** `missing_env` answers about *this*
    process's environment, and the run happens in another one; a verdict here
    would be a claim about a future process. The names are listed and the
    reader is pointed at `validate`, which asks the question where it can be
    answered.

    **Resolving a project-local template imports user code, and the
    containment is copied WHERE IT SITS.** The sibling that already got this
    right is `report.render_with_override` together with
    `command_report`'s guard around `get_template`, and `report`'s shipped
    credential leak came from lifting `freeze`'s calls without the `try` they
    sit inside. So:

    - the **whole** resolution — the `sys.modules` purge, the `sys.path`
      insert, the `get_template` call and the restoration — sits inside one
      `except BaseException` that reports through `c`, whose `credentials` is
      populated from the raised error's own `partial_templates` (a class body
      finishes running before `@register_template` sees it, so a file that
      raises *after* declaring one leaves that class fully formed and readable
      for its declarations). A template raising at import therefore becomes a
      **redacted** diagnostic instead of reaching `main`'s un-redacted printer
      (plan correction 21).
    - the `sys.path` entry is removed **by identity**, never `pop(0)`, and the
      restoration is in a `finally` so it is pinned on the **failure** path as
      well as the success one. `load_experiment` and `render_with_override` are
      the two sibling sites that fixed this exposure.
      **The identity-versus-position distinction is NOT exhibitable at THIS
      call site, and that is measured rather than assumed.**
      `templates.discovery._import_file` snapshots `sys.path` and restores it
      **wholesale** (`sys.path[:] = before_path`) around every `templates/*.py`
      it executes — measured with a template doing its own
      `sys.path.insert(0, "/h9c/vendored")`: the entry is visible during
      `exec_module` and gone afterwards, so when the `finally` below runs
      `sys.path[0]` **is** this function's own entry and a `pop(0)` removes
      exactly what `remove` would. The two branches cannot differ, so the
      prescribed mutation is blind and its replacements are three arms that can
      fail: the window is load-bearing (a template importing from the
      checkout's own `src/`), `sys.path` is byte-identical afterwards on both
      the success and the failure path, and the purge below is load-bearing.
      The identity form is kept anyway, because that snapshot is another
      module's promise rather than this function's, and it costs nothing.
    - the window is opened at all because `reproduce` resolves a template in a
      **foreign checkout**: a `templates/*.py` there may import its own
      project's package, and `discover_local` imports by path without putting
      `<root>/src` on `sys.path` itself. Measured: with the insert removed such
      a template raises `ModuleNotFoundError` and the whole resolution is
      refused.
    - the root package is purged first, and it is load-bearing here for a
      reason `_import_file`'s own restore does **not** cover: that restore
      un-imports only the entries `_is_local` places under `templates/`, so a
      module a template imported out of `<dest>/src` stays in `sys.modules` —
      and two checkouts in one process can declare the same package name
      (`publishable new` derives it from the experiment name). Without the
      purge, the second checkout's template is served the first's module.

    **`get_template` is called once on the ordinary path.** A second registry
    call re-imports every `templates/*.py`, executing every user top level
    twice, which is the cost `registry._claims`' own docstring names. So
    `template_provenance` is consulted **only** when the first call resolved no
    class at all — the path on which no user top level did anything useful
    anyway.
    """
    raw_config = operand.doc.get("config")
    doc: dict[str, Any] = raw_config if isinstance(raw_config, dict) else {}
    return env_and_required_env(doc, dest, c, origin="the recorded commit")


def env_and_required_env(
    doc: dict[str, Any], dest: Path, c: Collector, *, origin: str
) -> tuple[list[str], int | None, list[str]]:
    """The body of step 6, over a config document and a tree — whichever form
    supplied them. `prepare_env` above passes the record's embedded `config` and
    the checkout; the config-operand form passes the config file's own parsed
    document and the repository it sits in.

    Extracted rather than reimplemented, because the config form needs exactly
    this and *the sibling that already got it right is the first place to look*
    — a second `.env` writer and a second `get_template` window would be two
    answers to one question, and the containment above is the half a copy loses.

    `origin` is the only thing the two callers differ on, and it is a phrase
    rather than a flag: the tree is *the recorded commit* in the record form and
    *the repository* in the config form, and only the sentence changes.
    """
    lines: list[str] = []

    example = dest / ".env.example"
    dot_env = dest / ".env"
    if dot_env.exists():
        lines.append(f".env: {dot_env} already exists and was NOT overwritten")
    elif example.is_file():
        dot_env.write_bytes(example.read_bytes())
        lines.append(f".env: written from {example} — it carries NAMES, so fill in the values")
    else:
        lines.append(f".env: not written — {origin} carries no `.env.example` at {example}")

    raw_name = doc.get("experiment_type")
    name = raw_name if isinstance(raw_name, str) else ""
    entrypoint = doc.get("entrypoint")
    root_pkg = ""
    if isinstance(entrypoint, str) and entrypoint:
        root_pkg = entrypoint.partition(":")[0].split(".", 1)[0]
    src_entry = str(dest / "src")

    try:
        if root_pkg:
            for cached in [
                module
                for module in sys.modules
                if module == root_pkg or module.startswith(root_pkg + ".")
            ]:
                del sys.modules[cached]
        sys.path.insert(0, src_entry)
        try:
            template = get_template(name, dest)
        finally:
            # By IDENTITY, never `pop(0)` — see the docstring. `if` rather than
            # an unguarded `remove` because a template that removed our entry
            # itself must not turn this cleanup into a second exception.
            if src_entry in sys.path:
                sys.path.remove(src_entry)
    except KeyboardInterrupt:
        raise KeyboardInterrupt from None
    except BaseException as exc:
        code = exc.code if isinstance(exc, PublishableError) else "E-TEMPLATE-LOAD"
        partial = getattr(exc, "partial_templates", None) or []
        declared: list[str] = []
        for cls in partial:
            declared.extend(declared_credential_names_for(doc, cls))
        # MERGED, not replaced: whatever the caller already told this collector
        # to look for stays covered.
        c.credentials = {**c.credentials, **credential_values(declared)}
        c.error(
            code,
            str(dest),
            f"the checkout's template `{name}` could not be resolved: {exc}",
        )
        return (lines, EXIT_WRONG, [])

    if template is not None:
        required = getattr(template, "required_env", None)
        required = list(required) if isinstance(required, list) else []
        if required:
            lines.append(
                f"required_env: template `{name}` declares "
                + ", ".join(str(each) for each in required)
                + " — each needs a value in `.env` or in the shell"
            )
        else:
            lines.append(f"required_env: template `{name}` declares none")
        return (lines, None, [str(each) for each in required])

    provenance = template_provenance(name, dest)
    if provenance == "installed":
        plugin = doc.get("plugin")
        lines.append(
            f"required_env: template `{name}` comes from "
            + (f"plugin {plugin}" if plugin else "an installed plugin")
            + ", which is installed in the CHECKOUT's environment and not in this one — "
            "`validate` below reads its `required_env` where the plugin exists"
        )
    else:
        lines.append(
            f"required_env: no template registers `{name}` in this interpreter, so none is "
            "listed — `validate` below is what reports that"
        )
    return (lines, None, [])


# --------------------------------------------------------------------------
# The apparatus expectation. Design Decision 4 (Ruling BB), first half.
# --------------------------------------------------------------------------


EXPECTED_FILENAME = "apparatus.expected.json"


def _expectation_block(facts: dict[str, Any]) -> list[str]:
    """The block § Reproducing on another device already specifies, reproduced
    to its own spacing:

    ```
    This run measured through an apparatus. Reproducing it needs:
      llm_deployment   model_revision  gpt-5.5-2026-06-11
                       api_version     2026-05-01
    ```

    The condition key is printed **once**, on its first fact's row, which is
    what makes the block readable when a run has several conditions — and the
    continuation rows are blank in that column rather than repeating it. Column
    widths are computed from the data: the condition column is
    `max(len(key)) + 1` and the fact column `max(len(fact))`, joined by two
    spaces at each seam, which reproduces the document's own example exactly
    rather than approximating it.
    """
    if not facts:
        return []
    width_condition = max(len(key) for key in facts) + 1
    width_fact = max((len(fact) for entry in facts.values() for fact in entry), default=0)
    lines = ["This run measured through an apparatus. Reproducing it needs:"]
    for key, entry in facts.items():
        first = True
        for fact, value in entry.items():
            head = key if first else ""
            lines.append(f"  {head.ljust(width_condition)}  {fact.ljust(width_fact)}  {value}")
            first = False
    return lines


def write_expectation(operand: Record, dest: Path, c: Collector) -> tuple[list[str], int | None]:
    """Write `configs/<name>/apparatus.expected.json` and print the block.
    Decision 4's first half (Ruling BB). Returns `(lines, exit code or None)`.

    **`reproduce` probes nothing, compares nothing and refuses nothing on
    apparatus grounds.** It is not one of the four places a probe runs, exactly
    as `diff` is not, and the reason is the same: it has no config resolved
    against a plugin it does not have — `uv sync` has only just installed that
    plugin into the **clone's** environment, not into this one. The comparison
    happens at the next `run`'s first probe, through
    `apparatus.expectation_from` and the shipped gate (task 9). On another
    device the apparatus **will** differ — a GPU model, a hostname, an OS — and
    that is expected rather than exceptional, which is Ruling BB entire.

    **The recorded `facts` mapping, verbatim**, condition key to fact mapping.
    Nothing is projected, renamed or re-ordered: the file's whole job is to be
    the recorded observation, and it is written with `json.dump(..., indent=2)`
    so a reader can edit it — which § Reproducing on another device explicitly
    invites, and calls the point of naming the file.

    **Written once, never rewritten.** An existing one is
    `E-REPRODUCE-EXPECTED-EXISTS` rather than a replacement, because replacing
    it would discard a human decision: core cannot tell a legitimately
    equivalent deployment from a substituted one, so the file is the reader's
    to change. **The reachable route to that state is a COMMITTED expectation
    file**, not a second `reproduce` into the same destination — Decision 9
    refuses an existing destination before this function is ever called, so a
    second run of the command cannot reach here. `configs/` is outside
    `HASHED_TREES`, so a committed one changes no `code_hash`, and a reader who
    edited the file and committed it is exactly the person this refusal exists
    for. Stated because *an unreachable refusal is a filing, not a pass*.

    **`provenance.apparatus` gains no key naming the expectation.** H6a Ruling
    C's refusal of a definition marker is the precedent: the reproduction's
    record carries what it **observed**, and a key naming what it was compared
    against would be a second source of truth for a comparison the checkout's
    own file already holds. Pinned by H9c Fixture Q, which compares a run with
    the file against a control run without it.
    """
    apparatus_block = (operand.doc.get("provenance") or {}).get("apparatus")
    if not isinstance(apparatus_block, dict):
        # A run with no declared probe records `apparatus: null` — the whole
        # block — which is every run of template `generic` and the worked
        # example both. Nothing to write, and it is said rather than passed
        # over in silence.
        return (["apparatus: this run measured through none; no expectation is written"], None)

    facts = apparatus_block.get("facts")
    if not isinstance(facts, dict):
        c.error(
            "E-IO-FAILED",
            str(operand.path),
            "records an `apparatus` block whose `facts` is not a mapping of condition "
            "key to fact mapping, so no expectation can be written from it",
        )
        return ([], EXIT_WRONG)

    config_dir = config_dir_in(operand, dest, c)
    if config_dir is None:
        return ([], EXIT_WRONG)
    target = config_dir / EXPECTED_FILENAME
    if target.exists():
        c.error(
            "E-REPRODUCE-EXPECTED-EXISTS",
            str(target),
            "already exists in the checkout, and `reproduce` writes this file once and "
            "never rewrites it — it is a file you may edit, so replacing it would "
            "discard a decision core cannot make for you. Move or delete it and "
            "reproduce into a fresh destination",
        )
        return ([], EXIT_WRONG)

    config_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    lines = [f"{EXPECTED_FILENAME}: written to {target}", ""]
    lines += _expectation_block(facts)
    return (lines, None)


# --------------------------------------------------------------------------
# The closing transcript. `docs/reference.md` § Reproducing, step 7.
# --------------------------------------------------------------------------


_CLOSING_COMMANDS = ("validate", "dry-run", "run")
"""The three commands, in the order § Reproducing on another device prints
them, and that order is the claim: `validate` reads without executing,
`dry-run` expands the plan without executing, `run` executes. Printing them in
any other order would advise a reader to pay for a run before checking it.

The column width is `len("validate")`, which is what produces the document's
own `dry-run  ` and `run      ` spacing — computed from the longest name rather
than written as three literals, so adding a fourth command cannot leave two
spellings of the alignment.
"""


def closing_transcript(
    *,
    prepared: Path | None,
    config_rel: str,
    required: list[str],
    edit_note: str,
) -> list[str]:
    """§ Reproducing on another device's step 7, verbatim to its own spacing.

    **`reproduce` stops rather than running**, because both remaining inputs
    need a person: core has no mechanism to transmit a secret and it will not
    fetch data. So this is the last thing the command prints, and it is
    instructions rather than actions.

    `prepared` is the derived destination in the record form and **`None`** in
    the config form, which prepared nothing and has nowhere to `cd` to — so
    that form gets neither the `Prepared …/` header nor the `cd` line. Both
    forms get the same three commands, which is Decision 13's *"the same
    closing instructions"*.

    **The `.env` row appears only when the template declares `required_env`.**
    § Reproducing says so in as many words — *"the transcript above lists only
    the paths because `generic` declares no `required_env`, and an experiment
    whose template does gets a `.env` line beside them"* — and the two rows are
    aligned against the longer of the two labels rather than against a literal
    width, so a long config path cannot run into its own note.
    """
    width = len(max(_CLOSING_COMMANDS, key=len))
    rows: list[tuple[str, str]] = [(config_rel, edit_note)]
    if required:
        rows.append((".env", ", ".join(required) + " — each needs a value"))
    label_width = max(len(label) for label, _ in rows)

    lines = [""]
    if prepared is not None:
        lines += [f"Prepared {prepared.name}/", ""]
    lines.append("Before running, edit:")
    lines += [f"  {label.ljust(label_width)}   {note}" for label, note in rows]
    lines += ["", "Then:"]
    if prepared is not None:
        lines.append(f"  cd {prepared.name}")
    lines += [f"  uv run publishable {cmd.ljust(width)} {config_rel}" for cmd in _CLOSING_COMMANDS]
    return lines


# --------------------------------------------------------------------------
# The config-operand form. Design Decision 13.
# --------------------------------------------------------------------------


_NOT_VERIFIED = (
    "code_hash: not verified — a config names no commit and no recorded digest, so the "
    "tree this would hash is the tree NOW, not the tree a run used",
    "input_manifest: not verified — a config records no manifest; `run` below builds one "
    "from whatever `data.input_dir` you set and compares it to nothing",
    "apparatus: not verified — a config records no facts, so no `apparatus.expected.json` "
    "is written and the next `run`'s first probe has nothing to be checked against",
)
"""The three things this form did not verify, each named rather than omitted.

§ Reproducing on another device's own sentence for the config form is that it
*"cannot verify a `code_hash` and says so, rather than reporting a match it
never made"*, and `diff`'s `not comparable` rows are the shipped precedent for
the other two — the wording here is deliberately close to
`diff._NOT_COMPARABLE_REASONS`' without being shared, because those strings are
row cells in a fixed-width table and these are transcript lines.

**Printed FIRST**, before anything this form does do. They stand in for steps
1-3 and for step 5's verification, which is where a reader of the numbered list
would look for them; putting them at the end would make the transcript read as
though the sync and the `.env` copy had verified something.

A fourth absence travels with the lockfile line below rather than here, because
it is about the environment step this form DOES run.
"""


def reproduce_config(operand: ConfigOperand, c: Collector) -> tuple[list[str], int | None]:
    """§ Reproducing on another device's steps 4 onward, in place. Decision 13.

    Returns `(transcript lines, exit code or None)` — the same contract every
    other step function here uses.

    **Nothing is created outside the repository the config sits in.** No
    destination is derived and nothing is cloned, so
    `E-REPRODUCE-DEST-EXISTS`, `E-REPRODUCE-DEST-IN-REPO` and
    `E-REPRODUCE-NO-REMOTE` are **unreachable from this form** — stated that
    way, and not as *cannot happen*: they are live refusals of the record form
    reached through `prepare_checkout`, which this function does not call. The
    same is true of `E-REPRODUCE-EXPECTED-EXISTS`: a config records no facts,
    so no expectation is written and `write_expectation` is never called.

    **The repository is found by walking up from the CONFIG PATH**, never from
    the working directory — `CLAUDE.md` § Invariants, and the same walk-up
    `validate` already performs for `data.input_dir`. `find_repo_root` RAISES
    `E-GIT-NO-REPO` rather than returning `None`, so it is caught **by code**
    here, the way `validate._check_data` and `study._refuse_if_in_repo` catch
    it, and re-reported through this collector rather than raised into `main`,
    whose handler applies no redaction pass. No code is minted for it: a config
    outside every repository has no environment to restore, and
    `E-GIT-NO-REPO` is the existing code for exactly that walk-up failing.

    **Decision 3's ranking degenerates here, and the transcript says so rather
    than reusing it silently.** That ranking is *the recorded `uv_lock_hash` is
    the authority, the run directory's byte copy is the preferred carrier, the
    committed lockfile is used only when it matches* — and a config records no
    `uv_lock_hash` and has no byte copy beside it, so **there is no authority
    and nothing to rank**. What is left is the repository's own lockfile, which
    `uv sync --locked` reads for itself. That absence is a printed fact, on
    Ruling AA's own terms: neither source is preferred silently.
    """
    lines: list[str] = list(_NOT_VERIFIED)

    try:
        repo = find_repo_root(operand.path.parent)
    except ContractError as exc:
        if exc.code != "E-GIT-NO-REPO":
            raise
        c.error(
            "E-GIT-NO-REPO",
            str(operand.path),
            f"is not inside a git repository, so there is no project to restore: "
            f"`reproduce` given a config prepares the checkout it is already standing "
            f"in, and {exc}",
        )
        return (lines, EXIT_WRONG)

    lines.append(f"repository: {repo}, found by walking up from {operand.path}")

    lockfile = repo / "uv.lock"
    if lockfile.is_file():
        lines.append(
            f"uv.lock: {lockfile} is the environment `uv sync --locked` will hold you to — "
            f"its digest is {_sha256_of(lockfile)}, and a config records none to check it "
            f"against, so nothing is ranked here"
        )
    else:
        lines.append(
            f"uv.lock: {repo} holds none, so `uv sync --locked` has nothing to be locked to "
            f"— a config records no `uv_lock_hash` either, so there is no second source to "
            f"fall back on"
        )

    sync = _uv_sync(repo)
    if sync.returncode != 0:
        c.error(
            "E-IO-FAILED",
            str(repo),
            f"`uv sync --locked` failed: {sync.stderr.strip() or sync.stdout.strip()}",
        )
        return (lines, EXIT_EXTERNAL)
    lines.append("uv sync: --locked, against the repository's own lockfile")

    try:
        doc = yaml.safe_load(operand.path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        c.error("E-IO-FAILED", str(operand.path), f"could not be read as YAML: {exc}")
        return (lines, EXIT_WRONG)
    more, code, required = env_and_required_env(
        doc if isinstance(doc, dict) else {}, repo, c, origin="the repository"
    )
    lines.extend(more)
    if code is not None:
        return (lines, code)

    try:
        config_rel = str(operand.path.resolve().relative_to(repo.resolve()))
    except ValueError:
        # A config reachable from the repository only through a symlink. The
        # absolute path is still a path the user can type, which is what the
        # closing block is for.
        config_rel = str(operand.path)
    lines.extend(
        closing_transcript(
            prepared=None,
            config_rel=config_rel,
            required=required,
            edit_note=(
                "data.input_dir, data.output_dir — this form wrote no config, so these "
                "are the values it already carried"
            ),
        )
    )
    return (lines, None)


# --------------------------------------------------------------------------
# The command. `docs/reference.md` § Reproducing on another device, steps 1-7.
# --------------------------------------------------------------------------


def command_reproduce(path: Path) -> int:
    """`reproduce`, end to end. Ruling Y: one path, no flags, no target device.

    The seven steps § Reproducing on another device numbers map onto the
    functions above in that document's own order: steps 1 and 2 are
    `prepare_checkout` (the remote, the derived destination, the clone and the
    detached checkout), step 3 is `verify_code_hash`, step 4 is
    `restore_environment`, step 5 is `write_config` and then `write_expectation`,
    and step 6 is `prepare_env`. Step 7 — the closing transcript — is plan task
    13's, one commit later.

    **Every step reports the same way**, which is what makes this loop possible
    at all: `(transcript lines, exit code or None)`. The lines are what the
    reader is told; the code is a refusal already appended to `c`. On a refusal
    the lines gathered so far are still printed, because the earlier steps'
    findings are how a reader understands the one that stopped — a clone that
    happened and a `code_hash` that matched are facts about the failure, not
    noise before it.

    **One `Collector`, credential-bearing, and nothing is raised into `main`.**
    `main`'s `except PublishableError` handler applies no redaction pass
    (measured by H9b, plan correction 21), so a refusal raised out of here
    would reach a reader un-redacted. `prepare_env` is the step that learns
    credential values — a project-local template it imports may raise carrying
    one — and it MERGES them into this collector rather than replacing them,
    so redaction covers whatever any step told the collector to look for.

    **The working directory is read exactly once, here.** Decision 9 derives
    the destination relative to where the user is standing; `Path.cwd()` at the
    one call site keeps that a property of the invocation rather than of any
    function below.
    """
    c = Collector()
    operand = classify_operand(path, c)
    if operand is None:
        print(c.render(), file=sys.stderr)
        return EXIT_WRONG
    if isinstance(operand, ConfigOperand):
        config_lines, config_code = reproduce_config(operand, c)
        if config_code is not None:
            return _stop(config_lines, c, config_code)
        if config_lines:
            print("\n".join(config_lines))
        return EXIT_OK

    prepared = prepare_checkout(operand, c, cwd=Path.cwd())
    if isinstance(prepared, Refused):
        print(c.render(), file=sys.stderr)
        return prepared.exit_code
    dest = prepared.dest

    lines: list[str] = []
    for step in (verify_code_hash, restore_environment, write_config, write_expectation):
        more, code = step(operand, dest, c)
        lines.extend(more)
        if code is not None:
            return _stop(lines, c, code)

    more, code, required = prepare_env(operand, dest, c)
    lines.extend(more)
    if code is not None:
        return _stop(lines, c, code)

    # `write_config` above already resolved and wrote into this directory, so
    # this call is the same pure derivation over the same record. It is called
    # again rather than threaded through the loop's uniform `(lines, code)`
    # contract, and its `None` branch is HANDLED rather than argued away — a
    # comment claiming a guarantee the code does not provide is this repo's
    # most-repeated habit.
    config_dir = config_dir_in(operand, dest, c)
    if config_dir is None:
        return _stop(lines, c, EXIT_WRONG)
    lines.extend(
        closing_transcript(
            prepared=dest,
            config_rel=str(config_dir.relative_to(dest) / "config.yaml"),
            required=required,
            edit_note="data.input_dir, data.output_dir",
        )
    )

    if lines:
        print("\n".join(lines))
    return EXIT_OK


def _stop(lines: list[str], c: Collector, code: int) -> int:
    """Print what the reader learned before the refusal, then the refusal.

    The transcript goes to stdout and the diagnostic to stderr, which is the
    split every other command here uses; the earlier lines are printed at all
    because a clone that happened and a `code_hash` that matched are facts
    about the failure rather than noise before it.
    """
    if lines:
        print("\n".join(lines))
    print(c.render(), file=sys.stderr)
    return code
