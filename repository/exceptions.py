"""Domain exceptions for the AI Debugger repository package."""


class InvalidRepositoryURLError(ValueError):
    """Raised when a repository URL fails validation."""


class CloneFailedError(RuntimeError):
    """Raised when git clone exits with a non-zero return code."""
