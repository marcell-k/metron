"""Entry."""

import sys

import typer

from metron.cli import app
from metron.errors import ParseError


def main() -> None:
    """Entry point."""
    try:
        app()
    except ParseError as e:
        typer.echo(f"error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
