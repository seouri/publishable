"""Collected findings. See docs/reference.md § Exit codes and diagnostics."""

from dataclasses import dataclass, field

from publishable.secrets import redact

EXIT_OK = 0
EXIT_WRONG = 1
EXIT_INVOCATION = 2
EXIT_PARTIAL = 3
EXIT_FAILED = 4
EXIT_EXTERNAL = 5


@dataclass(frozen=True)
class Diagnostic:
    level: str  # "error" | "warning"
    code: str
    path: str
    message: str


@dataclass
class Collector:
    """`validate` collects rather than stops, so findings are appended, never raised."""

    findings: list[Diagnostic] = field(default_factory=list)
    credentials: dict[str, str] = field(default_factory=dict)
    """The credential values core read for a DECLARED variable, if any were.

    Set by whoever knows them — `validate_config`, which resolves the same two
    declarations it checks, and `command_run` for the collectors it builds after
    it. Redaction happens at `render`, the one place a finding's text becomes
    output, rather than at each site that builds an exception string into a
    diagnostic: every one of those constructions reaches a reader through a
    `Collector`, whatever their number, and a site added later is covered
    without a second edit here. (Not every exception-interpolating site in core
    is a diagnostic — `main`'s catch-all is one that isn't, and redacting it is
    tracked separately in `spec-defects.md`.) `Diagnostic` stays a plain frozen
    record so a message is never rewritten before the collector that owns it
    decides to print.

    Empty is the default and the honest one: a collector nobody gave values to
    redacts nothing, because there is nothing it was told to look for.
    """

    def error(self, code: str, path: str, message: str) -> None:
        self.findings.append(Diagnostic("error", code, path, message))

    def warn(self, code: str, path: str, message: str) -> None:
        self.findings.append(Diagnostic("warning", code, path, message))

    @property
    def has_errors(self) -> bool:
        return any(f.level == "error" for f in self.findings)

    def exit_code(self) -> int:
        return EXIT_WRONG if self.has_errors else EXIT_OK

    def render(self) -> str:
        lines = []
        for f in self.findings:
            lines.append(f"  {f.level:<7} {f.code:<20} {f.path}")
            # `or f.message` narrows `str | None` to `str` for the type checker;
            # `redact` returns its argument unchanged when there is nothing to do.
            lines.append(f"          {redact(f.message, self.credentials) or f.message}")
        n_err = sum(1 for f in self.findings if f.level == "error")
        n_warn = len(self.findings) - n_err
        total = len(self.findings)
        problem_noun = "problem" if total == 1 else "problems"
        error_noun = "error" if n_err == 1 else "errors"
        warning_noun = "warning" if n_warn == 1 else "warnings"
        lines.append(f"{total} {problem_noun} ({n_err} {error_noun}, {n_warn} {warning_noun})")
        return "\n".join(lines)
