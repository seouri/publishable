# src/publishable/report.py
"""`BaseReport` and `Section`. docs/reference.md § A report override renders one
experiment's own figures, § The importable surface.

Nothing here dispatches: the real `report` command, override discovery, and the
standard sections arrive in later tasks. This module builds only the API every
override is written against — `BaseReport.sections` and the `Section` values it
yields — so its shape is load-bearing for every subclass that will ever be
written on top of it.
"""

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Section:
    """One titled block of a report: `title` and `body`, where `body` is
    markdown text or a mapping core knows how to render as a table.

    Frozen is a property of the *type*, not a sentence about intent: a plain
    value class would let a subclass reach into a re-yielded standard
    section and rebind `title` or `body` before it renders, changing a
    number core computed on the way out — and a safety argument in a
    comment is a claim that needs a mutation to back it, not a promise. A
    frozen dataclass guarantees exactly one thing: a re-yielded standard
    section cannot be rebound. It does **not** deep-freeze a `body` that is
    a mapping — the mapping object itself stays as mutable as any other
    dict, and this class makes no claim beyond field assignment.
    """

    title: str
    body: "str | Mapping[str, Any]"


class BaseReport:
    """A renderer override for one experiment. Subclass it, override
    `sections`, and compose the standard blocks with `yield from
    super().sections(run, io)` — see docs/reference.md § A report override.

    `format` has **no base default** here. `generate report` always writes
    the `format = "html" | "markdown"` line into the generated class, so a
    base default would be a value no generated class could ever be observed
    to take, and a class that declares none is refused at render rather than
    silently defaulted — the same reason `BaseTemplate.aggregate` has no
    base implementation returning `{}`.
    """

    def section(self, title: str, *, body: "str | Mapping[str, Any]") -> Section:
        """Construct a `Section`. Core's, so a subclass never has to import
        `Section` itself to build one — § A report override's worked block
        calls `self.section("Method agreement", body=...)` and nothing else.
        """
        return Section(title=title, body=body)

    def sections(self, run: Any, io: Any) -> Iterator[Section]:
        """A generator, yielding `Section` values. Core never materializes
        the list before rendering, so an override that yields a cheap
        section first and an expensive figure last prints the cheap one
        first.

        The base implementation yields nothing: the four standard sections
        this composes with `yield from super().sections(run, io)` are built
        elsewhere, over `run` and `io`, once the sections themselves exist.
        """
        yield from ()
