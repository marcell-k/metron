"""Distribution and frequency."""

from dataclasses import dataclass, fields
from typing import TYPE_CHECKING

from metron.errors import MetronError
from metron.plot import PlotType, plot
from metron.utils import bin_values, r

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


PADDING = 2


@dataclass(frozen=True, slots=True)
class FrequencyTable:
    """Frequency table."""

    _class: list[str]
    freq: list[int]
    rel_freq: list[float]
    cum_freq: list[int]
    cum_rel_freq: list[float]

    def __post_init__(self) -> None:
        """Validate `Table` creation."""
        if not all(len(x) == len(self._class) for x in self):
            msg = "error in creating frequency table"
            raise MetronError(msg)

    def __iter__(self) -> Iterator[list[str | int | float]]:
        """Iterate over fields and yield values."""
        for f in fields(self):
            yield getattr(self, f.name)

    def __str__(self) -> str:
        """Visualize table."""
        s = ""
        columns = [
            ("class", self._class),
            ("freq", self.freq),
            ("rel. freq", self.rel_freq),
            ("cum. freq", self.cum_freq),
            ("cum. rel. freq", self.cum_rel_freq),
        ]

        width = 15
        header = "|" + "|".join(name.center(width) for name, _ in columns) + "|"
        separator = "+" + "+".join("-" * width for _ in columns) + "+"
        s += header + "\n"
        rows = [
            "|" + "|".join(str(value).center(width) for value in row) + "|"
            for row in zip(*(values for _, values in columns), strict=True)
        ]
        return "\n".join([header, separator, *rows])


def frequency_table(values: Iterable[float], nmb_bins: int | None = None) -> FrequencyTable:
    """Visual representation of how often each unique value appears."""
    values = sorted(values)
    start = values[0]
    bins, step = bin_values(values, nmb_bins)
    _class = [f"({r(start + step * k)}, {r(start + step * (k + 1))})" for k in bins]
    freq = list(bins.values())
    rel_freq = [x / len(values) for x in freq]
    cum_freq = [freq[0]]
    for i in range(1, len(rel_freq)):
        cum_freq.append(freq[i] + cum_freq[i - 1])

    cum_rel_freq = [rel_freq[0]]
    for i in range(1, len(rel_freq)):
        cum_rel_freq.append(rel_freq[i] + cum_rel_freq[i - 1])
    return FrequencyTable(_class, freq, rel_freq, cum_freq, cum_rel_freq)


def calculate_ecdf(values: Iterable[float]) -> str:
    """Calculate Empricial distribution function (ECDF)."""
    values = sorted(values)
    out = [0] * len(values)
    for i in range(1, len(values)):
        if values[i] > values[i - 1]:
            out[i] = out[i - 1] + 1

    return plot(out, plot_type=PlotType.LINE)
