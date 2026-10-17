"""CLI."""

import sys
from pathlib import Path
from typing import Annotated

import typer

from metron.descriptive import descriptive_statistics
from metron.distribution import (
    OutlierMethod,
    calculate_ecdf,
    calculate_zscore,
    frequency_table,
    outlier_detection,
)
from metron.errors import ParseError
from metron.plot import draw_histogram
from metron.relationship import analyze_relationship
from metron.utils import clean_data

app = typer.Typer(no_args_is_help=True)

Source = Annotated[
    str | None,
    typer.Argument(help="Input file. Default: stdin."),
]
Sep = Annotated[str, typer.Option("--sep", help="Separator.")]


def load(source: str | None, sep: str) -> list[float]:
    """Read and clean input."""
    if source is None:
        raw = sys.stdin.read()
    elif Path(source).exists():
        raw = Path(source).read_text()
    else:
        msg = "error in reading"
        raise ParseError(msg)
    return clean_data(raw, sep)


@app.command()
def descriptive(source: Source = None, sep: Sep = ",") -> None:
    """Mean, median, std."""
    typer.echo(descriptive_statistics(load(source, sep)))


@app.command()
def histogram(
    source: Source = None,
    sep: Sep = ",",
    bins: int = 10,
    size: int = 20,
    *,
    horizontal: bool = False,
) -> None:
    """Draw histogram."""
    typer.echo(draw_histogram(load(source, sep), bins, size, horizontal=horizontal))


@app.command()
def ecdf(source: Source = None, sep: Sep = ",") -> None:
    """Plot ECDF."""
    typer.echo(calculate_ecdf(load(source, sep)))


@app.command()
def zscore(source: Source = None, sep: Sep = ",") -> None:
    """Z-scores."""
    typer.echo(calculate_zscore(load(source, sep)))


@app.command()
def frequency(source: Source = None, sep: Sep = ",") -> None:
    """Frequency table."""
    typer.echo(frequency_table(load(source, sep)))


@app.command()
def outlier(
    source: Source = None, sep: Sep = ",", method: OutlierMethod = OutlierMethod.MAD
) -> None:
    """Outlier detection method can be `iqr` or `mad`."""
    typer.echo(outlier_detection(load(source, sep), method))


@app.command()
def relationship(var1: Source = None, var2: Source = None, sep: Sep = ",") -> None:
    """Frequency table."""
    typer.echo(analyze_relationship(load(var1, sep), load(var2, sep)))
