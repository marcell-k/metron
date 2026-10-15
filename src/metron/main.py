"""Entry."""

import sys
from enum import StrEnum
from pathlib import Path

import typer

from metron.descriptive import descriptive_statistics
from metron.distribution import draw_histogram
from metron.errors import ParseError
from metron.utils import clean_data


class Method(StrEnum):
    """Types."""

    DESCRIPTIVE = "descriptive"
    DISTRIBUTION = "distribution"
    RELATIONSHIP = "relationship"
    PROBABILITY = "probability"
    INFERENCE = "inference"


# NOTE: ``input`` can be a file or raw data
def main(method: Method, source: str | None = None, sep: str = ",") -> None:
    """Entry point."""
    if source is None:
        raw = sys.stdin.read()
    elif Path(source).exists():
        raw = Path(source).read_text()
    else:
        msg = "error in reading"
        raise ParseError(msg)
    data = clean_data(raw, sep)
    match method:
        case Method.DESCRIPTIVE:
            stats = descriptive_statistics(data)
            print(stats)
        case Method.DISTRIBUTION:
            print(draw_histogram(data, 40))
            print(draw_histogram(data, 20, horizontal=False))
            return
        case _:
            return


if __name__ == "__main__":
    typer.run(main)
