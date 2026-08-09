"""The exception tree core raises. See docs/reference.md § Errors core raises."""


class PublishableError(Exception):
    """Catch this to catch everything core raises."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class ContractError(PublishableError):
    """Your code asked for, or handed back, something its declarations don't allow."""


class ArtifactError(PublishableError):
    """Core will not write this."""


class ArtifactExistsError(ArtifactError):
    """...because the target is already there."""
