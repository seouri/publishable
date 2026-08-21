# src/publishable/study.py
"""`study new`. docs/reference.md § Studies: what a paper reports,
§ Building one.

A study is a publication artifact, sibling to the paper, never inside the
git repository the code lives in — `study new` refuses a bundle path
resolving inside one, the same walk-up `input_dir`/`output_dir` already use
(`provenance.find_repo_root`), and refuses a bundle that already exists.

`cli.py` imports this module's functions inside its own `study` arm,
joining `report.py`'s own precedent of importing nothing from `cli` at all
— this module is the same shape, so `cli` depends on it and it never
depends back.
"""

from pathlib import Path

import yaml

from publishable.errors import ContractError
from publishable.provenance import find_repo_root


def _refuse_if_in_repo(path: Path, code: str, what: str) -> None:
    """Measured at `ebf642a` (§ Corrections, correction 12):
    `provenance.find_repo_root` RAISES `E-GIT-NO-REPO` rather than
    returning `None` when no repository is found, so "outside every repo"
    is implemented as the walk-up FAILING with that one code — caught
    specifically — rather than as a `None` return, and every other
    `ContractError` it might raise propagates unexamined. The walk-up form
    of this check is rejected as a mutation for the identical reason
    `E-DATA-IN-REPO`'s own guard is: above a path outside any repo it would
    be caught by a crash rather than by the property.
    """
    try:
        repo_root = find_repo_root(path)
    except ContractError as exc:
        if exc.code == "E-GIT-NO-REPO":
            return
        raise
    raise ContractError(
        f"{path} resolves inside the git repository at {repo_root} — {what} belongs "
        "beside the manuscript it supports, never inside the code repository it "
        "cites (docs/reference.md § Why not in the repo)",
        code=code,
    )


def study_new(bundle: Path, title: str) -> None:
    """`publishable study new <bundle> --title "..."`. Writes
    `<bundle>/study.yaml` with `title`, `authors: []` and `runs: {}` — no
    `code` block, because `code.commit` is one run's and there is no run
    yet.

    Both refusals happen before anything reaches disk, in the order the
    document states them: outside any repo, then not already a bundle.
    "Existing" means a `study.yaml` FILE is already there — not that the
    directory exists, since `~/papers/x/study` beside a manuscript is a
    directory a person may well have made first, and `study new` must
    still succeed onto it.
    """
    _refuse_if_in_repo(bundle, "E-STUDY-IN-REPO", "a study")
    if (bundle / "study.yaml").exists():
        raise ContractError(
            f"{bundle} already holds a study.yaml — `study new` never overwrites an "
            "existing bundle; choose a different path, or add runs to the one "
            "already there with `study add`",
            code="E-STUDY-EXISTS",
        )
    bundle.mkdir(parents=True, exist_ok=True)
    doc = {"title": title, "authors": [], "runs": {}}
    (bundle / "study.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))
