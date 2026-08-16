"""Collected findings. See docs/reference.md § Exit codes and diagnostics."""

from dataclasses import dataclass, field

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
            lines.append(f"          {f.message}")
        n_err = sum(1 for f in self.findings if f.level == "error")
        n_warn = len(self.findings) - n_err
        total = len(self.findings)
        problem_noun = "problem" if total == 1 else "problems"
        error_noun = "error" if n_err == 1 else "errors"
        warning_noun = "warning" if n_warn == 1 else "warnings"
        lines.append(f"{total} {problem_noun} ({n_err} {error_noun}, {n_warn} {warning_noun})")
        return "\n".join(lines)
