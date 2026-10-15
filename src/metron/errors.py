"""Errors."""


class MetronError(Exception):
    """Base class error."""


class ParseError(MetronError, ValueError):
    """Input cannot be parsed."""
