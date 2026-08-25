"""`publishable demo` — the guided arc, built and then walked one command at a time.

`docs/reference.md` § What `demo` walks you through is the specification: six stops,
the middle three printing the real command, running it on `Enter`, and saying in two
or three lines what its output meant.

**The numbers this walkthrough prints are its own.** `demo` generates a real dataset,
scaffolds a real project and runs the real commands, so every figure a reader sees on
their screen is one their machine computed — which is why the recipe below is fixed
rather than sampled: the same 240 rows everywhere, so two people comparing screens are
comparing the same run.
"""

import os
import subprocess
import sys
from pathlib import Path

from publishable.diagnostics import EXIT_INVOCATION, EXIT_OK
from publishable.errors import ContractError
from publishable.materialize import materialize_config
from publishable.scaffold import scaffold_project
from publishable.templates.registry import get_template

# --- The dataset recipe, fixed. -------------------------------------------
#
# `random.Random` is the Mersenne Twister, whose stream the standard library
# documents as stable across platforms and versions, and `Random.gauss`'s
# algorithm is fixed in `random.py`. The arithmetic is IEEE-754 `+`, `*` and
# `math.sqrt` — the last correctly rounded — over the same operations in the
# same order. Both columns are rounded to six decimals before they are
# written, which is what makes the CSV the artifact of record: every
# downstream number is computed from the bytes on disk rather than from a
# float repr.
DEMO_DATA_SEED = 20260824
DEMO_RHO = 0.62
DEMO_UNITS = 240

# The twelve units `step03_analyze` hands back without recording. They become
# `failed` rather than `ineligible` — a unit handed to a recording execution
# and neither recorded nor `io.skip`ped is what `runner` counts as failed —
# and 12/240 = 0.05 sits under the materialized `max_failed_fraction` of 0.2,
# so the run still reaches `completed`. Attrition a newcomer can see is worth
# more than a clean 240, because every real cohort has some.
DEMO_UNRECORDED = tuple(f"u{i:03d}" for i in range(20, DEMO_UNITS + 1, 20))

DATA_DIRNAME = "publishable-demo-data"
PROJECT_DIRNAME = "publishable-demo"
PROGRESS_FILE = ".demo-progress"

EXPERIMENT_NAME = "correlation-pilot"
PACKAGE_NAME = "correlation_pilot"
TEMPLATE_NAME = "correlation"

# The one line `demo` appends to the demo repository's own `.gitignore`.
# It is deliberately NOT added to `publishable new`'s shipped `.gitignore`
# constant: `.demo-progress` is a file `demo` invents, and a project that
# never holds one would carry the line forever.
GITIGNORE_APPEND = (
    "\n# `publishable demo` tracks which stop you left at. Ignored so it can\n"
    "# never dirty the tree and push a run onto `draft`.\n"
    f"{PROGRESS_FILE}\n"
)

TEMPLATE_PY = '''\
# templates/correlation.py — a template only this project needs, discovered by path
from scipy.stats import kendalltau, pearsonr, spearmanr

from publishable import BaseTemplate, Param, register_template


@register_template("correlation")
class CorrelationTemplate(BaseTemplate):
    # One spec drives all three jobs: what `init` writes, what its inline
    # comments say, and what `validate` enforces.
    parameter_spec = {
        "analysis.method": Param(
            str,
            default="pearson",
            choices=["pearson", "spearman", "kendall"],
            help="Which correlation to compute over the recorded columns",
        ),
        "analysis.min_samples": Param(
            int, default=30, ge=2, help="Below this many paired rows, derive nothing"
        ),
    }

    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    default_repeats = 5

    def aggregate(self, units, cfg) -> dict:
        """Derive `r` from the columns the steps RECORDED, not from the unit
        attributes — a column a step wrote is a float this pipeline produced,
        while an attribute read out of `index.csv` arrives as a string. Core
        calls this on each resampled table too, which is what gives `r` a real
        interval rather than a bare point estimate."""
        if "pred" not in units.columns or "truth" not in units.columns:
            return {}
        pairs = [
            (float(p), float(t))
            for p, t in zip(units.pred, units.truth)
            if p is not None and t is not None
        ]
        if len(pairs) < cfg.parameters.analysis.min_samples:
            return {}
        fn = {"pearson": pearsonr, "spearman": spearmanr, "kendall": kendalltau}[
            cfg.parameters.analysis.method
        ]
        return {"r": float(fn([p for p, _ in pairs], [t for _, t in pairs])[0])}
'''

STEP01_PY = """\
# src/correlation_pilot/steps/step01_load_cohort.py — scope `run`
from publishable import BaseStep


class Step(BaseStep):
    # `run` scope: once for the whole sweep, before any condition exists.
    scope = "run"

    def run(self, cfg, io):
        return {"cohort_size": len(io.units)}
"""

STEP02_PY = """\
# src/correlation_pilot/steps/step02_fit_model.py — scope `condition`
from publishable import BaseStep


class Step(BaseStep):
    # `condition` scope: once per condition, so anything expensive that depends
    # on the swept parameter and not on the repeat belongs here.
    scope = "condition"

    def run(self, cfg, io):
        return {"rank_based": cfg.parameters.analysis.method != "pearson"}
"""

STEP03_PY = """\
# src/correlation_pilot/steps/step03_analyze.py — scope `repeat`
from publishable import BaseStep

# Twelve units this step hands back without recording. They land in `failed`,
# which is what a real cohort looks like.
UNRECORDED = {unrecorded}


class Step(BaseStep):
    # `repeat` scope: once per condition per repeat, which is where the seed
    # actually changes anything.
    scope = "repeat"

    # Declared because the step draws from `self.rng`: two seeds give two
    # answers, which is the whole point of a `seed` repeat.
    nondeterministic = True

    def run(self, cfg, io):
        for unit in io.units:
            if unit.key in UNRECORDED:
                continue
            # `self.rng` is core's per-execution stream, seeded from the design
            # digest and this repeat's seed. `.random()` draws a float in
            # [0, 1) — the jitter is what makes the five seeds differ.
            jitter = (self.rng.random() - 0.5) * 0.4
            io.record(unit.key, {{"pred": float(unit.x) + jitter, "truth": float(unit.y)}})
        return {{"analysis_complete": True}}
"""

EXPERIMENT_PY = """\
# src/correlation_pilot/experiment.py — order, nothing else
from publishable import BaseExperiment

from .steps.step01_load_cohort import Step as LoadCohort
from .steps.step02_fit_model import Step as FitModel
from .steps.step03_analyze import Step as Analyze

STEPS = [LoadCohort, FitModel, Analyze]


class CorrelationPilotExperiment(BaseExperiment):
    # Order, nothing else. Each step declares its own scope; core derives the
    # execution plan from that.
    steps = STEPS
"""

SWEEP_BLOCK = """\
sweep:
  # What varies across conditions. `baseline` is the condition every delta is
  # measured against; `grid` is the axis itself.
  baseline: {analysis.method: pearson}
  grid:
    analysis.method: [spearman, kendall]
"""

DEMO_DESCRIPTION = "The publishable demo: three correlation methods over one synthetic cohort"


def data_root() -> Path:
    """`~/publishable-demo-data`. Outside the repository `demo` creates, because
    that is where real data belongs and the rule is enforced rather than
    advised: `input_dir` and `output_dir` may never resolve inside the repo."""
    return Path.home() / DATA_DIRNAME


def write_dataset(input_dir: Path) -> Path:
    """The 240-row `index.csv`, from a fixed seed, rounded to six decimals."""
    import math
    import random

    rng = random.Random(DEMO_DATA_SEED)
    scale = math.sqrt(1.0 - DEMO_RHO * DEMO_RHO)
    rows = ["unit_id,x,y"]
    for i in range(1, DEMO_UNITS + 1):
        x = rng.gauss(0, 1)
        y = DEMO_RHO * x + scale * rng.gauss(0, 1)
        rows.append(f"u{i:03d},{round(x, 6)},{round(y, 6)}")
    input_dir.mkdir(parents=True, exist_ok=True)
    path = input_dir / "index.csv"
    path.write_text("\n".join(rows) + "\n")
    return path


def _replace_line(lines: list[str], prefix: str, replacement: str) -> None:
    """Rewrite the one line starting with `prefix`, or refuse.

    Loud rather than silent: this function edits what `materialize_config`
    wrote, so a change there must fail here rather than produce a demo config
    that quietly lost its description.
    """
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = replacement
            return
    raise ContractError(
        f"`demo` could not find the line starting {prefix!r} in the materialized "
        "config — `materialize_config` has moved and `demo` must move with it",
        code="E-DEMO-CONFIG-SHAPE",
    )


def demo_config_text(repo_root: Path, input_dir: Path, output_dir: Path) -> str:
    """`init`'s own config for template `correlation`, with the demo's sweep.

    Built by editing what `materialize_config` writes rather than by hand, so
    the demo's config cannot drift from the one `publishable init` produces —
    the parameter block, the comments and every optional block are core's.
    """
    template = get_template(TEMPLATE_NAME, repo_root)
    if template is None:  # pragma: no cover - the demo registers it first
        raise ContractError(
            f"template {TEMPLATE_NAME!r} is not registered", code="E-TEMPLATE-UNKNOWN"
        )
    text = materialize_config(
        template=template,
        template_name=TEMPLATE_NAME,
        name=EXPERIMENT_NAME,
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        entrypoint=f"{PACKAGE_NAME}.experiment:CorrelationPilotExperiment",
    )
    lines = text.split("\n")
    _replace_line(lines, "  description:", f'  description: "{DEMO_DESCRIPTION}"')
    _replace_line(lines, "  authors:", '  authors: ["the publishable demo"]')
    _replace_line(
        lines, "    key:", "    key: unit_id                    # stable, unique identity"
    )
    _replace_line(
        lines,
        "    attributes:",
        "    attributes: [x, y]               # available for stratification and reporting",
    )
    _replace_line(
        lines,
        "    - {kind: seed",
        "    - {kind: seed, n: 5}             # seed | batch | fold",
    )
    _replace_line(
        lines,
        '  rationale: ""',
        '  rationale: "Five seeds, to show how much the pipeline itself moves"',
    )
    start = next(i for i, line in enumerate(lines) if line.startswith("sweep:"))
    end = next(i for i, line in enumerate(lines) if line.startswith("replication:"))
    lines[start:end] = SWEEP_BLOCK.rstrip("\n").split("\n") + [""]
    return "\n".join(lines)


def block_of(config_text: str, name: str) -> str:
    """One top-level block of a config, verbatim — what stop 2 prints.

    Read out of the file that was written rather than re-rendered, so what the
    reader sees is what `validate` will read.
    """
    lines = config_text.split("\n")
    start = next((i for i, line in enumerate(lines) if line.startswith(f"{name}:")), None)
    if start is None:
        raise ContractError(f"config has no `{name}` block to show", code="E-DEMO-CONFIG-SHAPE")
    end = start + 1
    while end < len(lines) and (lines[end].startswith((" ", "\t")) or not lines[end].strip()):
        end += 1
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    return "\n".join(lines[start:end])


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=you@example.com",
            "-c",
            "user.name=you",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )


def build_demo_project(root: Path) -> Path:
    """Stop 1's whole effect: the data outside the repo, the project inside it,
    and one commit leaving the tree clean — so the first `run` a newcomer issues
    is a real run rather than a `draft`."""
    input_dir = data_root() / "input"
    output_dir = data_root() / "results"
    write_dataset(input_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    scaffold_project(root)

    (root / "templates" / f"{TEMPLATE_NAME}.py").write_text(TEMPLATE_PY)

    package = root / "src" / PACKAGE_NAME
    (package / "steps").mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text("")
    (package / "steps" / "__init__.py").write_text("")
    (package / "experiment.py").write_text(EXPERIMENT_PY)
    (package / "steps" / "step01_load_cohort.py").write_text(STEP01_PY)
    (package / "steps" / "step02_fit_model.py").write_text(STEP02_PY)
    (package / "steps" / "step03_analyze.py").write_text(
        STEP03_PY.format(unrecorded=repr(set(DEMO_UNRECORDED)))
    )

    # The config is materialized from the template's own spec, which means the
    # file just written has to be discovered first — `get_template` does that
    # walk itself, the same way `init` reaches a project-local template.
    config_dir = root / "configs" / EXPERIMENT_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"
    config_path.write_text(demo_config_text(root, input_dir, output_dir))

    with (root / ".gitignore").open("a") as handle:
        handle.write(GITIGNORE_APPEND)

    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "The publishable demo: data outside, experiment inside")
    return config_path


# --- The walk ---------------------------------------------------------------
#
# Six stops. Stops 3 through 5 each print the next command exactly as you would
# type it, wait, run it on `Enter`, and then say in two or three lines what its
# output meant. Every pause is proceed-or-quit: nothing a reader presses reaches
# the config, because a prompt that did would be a parameter flag in disguise.


def read_progress(root: Path) -> int:
    """The last stop completed, or 0. Resuming is a property of the directory."""
    path = root / PROGRESS_FILE
    if not path.is_file():
        return 0
    try:
        return int(path.read_text().strip().split()[-1])
    except (ValueError, IndexError):
        return 0


def write_progress(root: Path, stop: int) -> None:
    (root / PROGRESS_FILE).write_text(f"stop {stop}\n")


def _pause(next_line: str, action: str) -> bool:
    """Print what comes next and wait, unless nothing is attached to stdin.

    Unattended — piped, redirected, in CI — the identical sequence runs straight
    through. That is not a mode and takes no flag, because the pause changes
    presentation only and there is nothing for a second command name to
    distinguish.
    """
    print(f"Next:  {next_line}")
    if not sys.stdin.isatty():
        print()
        return True
    print(f"       [Enter] to {action} · q to stop here")
    try:
        answer = input()
    except EOFError:  # pragma: no cover - a tty that closes mid-walk
        return True
    print()
    return answer.strip().lower() != "q"


def walk_commands(config_rel: str) -> list[str]:
    """The commands the walk runs or prints, in order — what `q` hands you."""
    return [
        f"publishable validate {config_rel}",
        f"publishable dry-run {config_rel}",
        f"publishable run {config_rel}",
    ]


def _print_remaining(config_rel: str, after_stop: int) -> None:
    """`q` leaves you holding the whole path rather than half of it."""
    remaining = walk_commands(config_rel)[max(0, after_stop - 2) :]
    print("The rest of the walk, in order:")
    for command in remaining:
        print(f"  {command}")
    print("  publishable report <the run.yaml those write>")
    print()
    print("`publishable demo` from this directory picks up where you left off.")


def command_demo(into: Path | None = None) -> int:
    """Build the worked example, then walk it one command at a time."""
    root = (into or Path.cwd() / PROJECT_DIRNAME).resolve()
    config_rel = f"configs/{EXPERIMENT_NAME}/config.yaml"
    stop = read_progress(root)

    if stop == 0:
        try:
            build_demo_project(root)
        except ContractError as exc:
            print(f"{exc.code}: {exc}", file=sys.stderr)
            return EXIT_INVOCATION
        write_progress(root, 1)
        shown = root if into is not None else Path(".") / PROJECT_DIRNAME
        print(f"Created {shown}/")
        print(f"  {DEMO_UNITS} synthetic units      ~/{DATA_DIRNAME}/input/")
        print(f"  template                 templates/{TEMPLATE_NAME}.py")
        print(f"  experiment               src/{PACKAGE_NAME}/")
        print(f"  config                   {config_rel}")
        print()
        print("Your data sits outside the repo, where real data belongs. Everything from")
        print("here is the CLI you'd use on an experiment of your own.")
        print()
    else:
        print(f"Resuming the demo in {root} at stop {stop + 1}.")
        print()

    config_path = root / config_rel
    if not config_path.is_file():
        print(
            f"E-DEMO-NO-PROJECT: {root} holds a {PROGRESS_FILE} but no "
            f"{config_rel} — this is not a demo directory",
            file=sys.stderr,
        )
        return EXIT_INVOCATION

    if stop < 2:
        if not _pause("a look at the config that describes this run", "continue"):
            _print_remaining(config_rel, 2)
            return EXIT_OK
        text = config_path.read_text()
        print(block_of(text, "sweep"))
        print()
        print(block_of(text, "replication"))
        print()
        print("That is the whole description of what is about to run: three conditions")
        print("on one axis, five seed repeats each. Read the config, don't edit a step —")
        print("`code_hash` covers `src/**` and `templates/**`, so an edited step would")
        print("dirty the tree and make the run at stop 5 refuse.")
        print()
        write_progress(root, 2)

    return _walk(root, config_rel, stop)


def _run_in_project(root: Path, argv: list[str]) -> int:
    """Run one real command, in this process, from the demo repository.

    In-process through the same `main` the console script calls, rather than as
    a subprocess: the walkthrough's whole claim is *these are the commands you
    would type*, and a subprocess would make its output depend on how
    `publishable` was installed. The working directory is the demo repository
    for the same reason — the command printed above the output is the command
    that ran, relative path and all.

    The directory is restored by identity in a `finally`, never by remembering
    a position: user code runs inside this window (the project's own steps),
    and a step that chdirs would otherwise leave the walk somewhere else.
    """
    from publishable.cli import main

    previous = Path.cwd()
    try:
        os.chdir(root)
        return main(argv)
    finally:
        os.chdir(previous)


def _render_summary(run_yaml: Path, metric: str = "r") -> list[str]:
    """`demo`'s own stop-5 summary, read out of the record `run` just wrote.

    `run` prints no results table, no progress indication and no banner — its
    whole stdout for a successful run is the warning block and one
    `run.yaml → <path>` line. So this is `demo` saying what that output meant,
    which is what stops 3 through 5 are; `run` is not changed and `report` is
    not invoked (Decision 7).
    """
    import yaml

    doc = yaml.safe_load(run_yaml.read_text())
    conditions = doc["results"]["conditions"]
    lines = ["  condition             r       95% CI            vs baseline (paired, 95% CI)"]
    attrition: dict[str, int] = {}
    spread: tuple[str, float] | None = None
    for cond in conditions:
        label = f"{cond['index']:02d}_{cond['label']}"
        block = next(iter(cond["aggregated"].values()))
        entry = block[metric]
        attrition = entry["n"]
        value = f"{entry['value']:.3f}"
        interval = f"[{entry['ci95'][0]:.3f}, {entry['ci95'][1]:.3f}]"
        delta = "—"
        against = cond.get("vs_baseline") or {}
        for step_block in against.values():
            if metric in step_block:
                d = step_block[metric]
                delta = (
                    f"{d['delta']:+.3f}  [{d['ci95'][0]:.3f}, {d['ci95'][1]:.3f}]"
                    if d.get("ci95")
                    else f"{d['delta']:+.3f}  (no interval)"
                )
        lines.append(f"  {label:<21} {value:<7} {interval:<17} {delta}")
        for name, other in block.items():
            # The spread reported is a RECORDED column's. A derived metric
            # carries no `repeat_spread` at all — core computes one only where
            # a column was recorded per repeat — so reporting `r`'s would be
            # reporting a key that is not in the record.
            if name != metric and other.get("repeat_spread") and spread is None:
                spread = (name, other["repeat_spread"]["std"])
    lines.append("")
    tail = (
        f"  intervals over {attrition['completed']} of {attrition['resolved']} units "
        f"({attrition['failed']} failed)"
    )
    if spread is not None:
        tail += f" · seed spread std {spread[1]:.3f} of recorded `{spread[0]}`"
    lines.append(tail)
    return lines


def _walk(root: Path, config_rel: str, stop: int) -> int:
    """Stops 3 through 6. Each of 3, 4 and 5 prints the command, waits, runs it,
    and then says what its output meant."""
    commands = walk_commands(config_rel)
    for index, command in enumerate(commands, start=3):
        if stop >= index:
            continue
        if not _pause(command, "run it"):
            _print_remaining(config_rel, index)
            return EXIT_OK
        code = _run_in_project(root, command.split()[1:])
        if code != EXIT_OK:
            print(
                f"`{command}` exited {code}. The walk stops here rather than "
                "pretending the next stop would mean anything.",
                file=sys.stderr,
            )
            return code
        print()
        for line in _commentary(root, index):
            print(line)
        print()
        write_progress(root, index)

    if stop >= 6:
        print("This demo is finished. Delete the directory to start over.")
        return EXIT_OK
    run_yaml = latest_run_yaml(root)
    if not _pause("the run.yaml all of this produced, and who reads it", "continue"):
        _print_remaining(config_rel, 6)
        return EXIT_OK
    print(f"The record is {run_yaml}")
    print("It carries the results AND everything needed to regenerate them. On any")
    print("other machine, a collaborator runs:")
    print()
    print(f"  publishable reproduce {run_yaml}")
    print()
    print("Not run here, and that is the lesson: `reproduce` clones the repository")
    print("`provenance.git.remote` names, and this demo repo has one local commit and")
    print("no remote. It is what somebody ELSE runs, on a machine holding neither your")
    print("data nor your credentials.")
    write_progress(root, 6)
    return EXIT_OK


def latest_run_yaml(root: Path) -> Path:
    """The record stop 5 produced — the newest run under the demo's output dir."""
    runs = sorted((data_root() / "results").glob("run_*/run.yaml"))
    if not runs:
        raise ContractError(
            "no run record found under the demo's output directory",
            code="E-DEMO-NO-RUN",
        )
    return runs[-1]


def _commentary(root: Path, stop: int) -> list[str]:
    """Two or three lines saying what the command's output meant."""
    if stop == 3:
        return [
            "validate read your config and your data. It created nothing and reached",
            "nothing off this machine — the 240 units it resolved came from the",
            "index.csv outside the repo, and `input_dir` being outside is enforced.",
        ]
    if stop == 4:
        return [
            "3 conditions × 5 repeats = 15 repeat-scoped executions, and 19 in all —",
            "the plan also runs step01_load_cohort once for the whole sweep and",
            "step02_fit_model once per condition. Still creates nothing.",
        ]
    lines = [
        "W-ENV-UNLOCKED fired because this project has no uv.lock: its pyproject",
        "depends on `publishable`, which cannot resolve until the package is",
        "published, so there is nothing to pin yet. Nothing was suppressed.",
        "",
        "run printed no table — its whole output is that warning and the path to the",
        "record. Everything below is `demo` reading the record back:",
        "",
    ]
    lines.extend(_render_summary(latest_run_yaml(root)))
    lines.extend(
        [
            "",
            "  `pred` and `truth` are recorded columns, so each publishes its own",
            "  metric and joins the correction family beside `r` — six members, and",
            "  two of them nobody reads. A template that derived twenty diagnostics",
            "  would correct every interval in the run for numbers nobody reads.",
        ]
    )
    return lines
