"""Distribution and frequency."""

import math
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING

from metron.errors import MetronError
from metron.utils import r

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

from metron.descriptive import _calculate_percentile

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


def frequency_table[T: int | float](
    values: Iterable[T], nmb_bins: int | None = None
) -> FrequencyTable:
    """Visual representation of how often each unique value appears."""
    values = sorted(values)
    n = len(values)
    nmb_bins, step = _bin_layout(values, nmb_bins)
    # class | freq | rel. freq | cum. freq  | cum. rel. freq
    bins = {}.fromkeys(range(nmb_bins + 1), 0)
    start = min(values)
    for v in values:
        index = int((v - start) / step)
        bins[index] += 1

    _class = [f"({r(start + step * k)}, {r(start + step * (k + 1))})" for k in bins]
    freq = list(bins.values())
    rel_freq = [x / n for x in freq]
    cum_freq = [freq[0]]
    for i in range(1, len(rel_freq)):
        cum_freq.append(freq[i] + cum_freq[i - 1])

    cum_rel_freq = [rel_freq[0]]
    for i in range(1, len(rel_freq)):
        cum_rel_freq.append(rel_freq[i] + cum_rel_freq[i - 1])
    return FrequencyTable(_class, freq, rel_freq, cum_freq, cum_rel_freq)


def draw_histogram[T: int | float](
    values: Iterable[T], width: int = 40, nmb_bins: int | None = None, *, horizontal: bool = True
) -> str:
    """Draw histogram."""
    values = sorted(values)
    nmb_bins, step = _bin_layout(values, nmb_bins)
    bins: dict[int, int] = {}.fromkeys(range(nmb_bins + 1), 0)
    start = min(values)
    for v in values:
        index = int((v - start) / step)
        bins[index] += 1
    s = render(bins, width, horizontal=horizontal)
    s += f"\nRange: ({min(values)}, {max(values)})   Bin width: {step}"
    return s


def render(bins: dict[int, int], size: int = 10, *, horizontal: bool = True) -> str:
    """Render histogram. `size` = max bar length (width or height)."""
    peak = max(bins.values()) or 1
    counts = list(bins.values())

    if horizontal:
        lines = [
            f"{idx:>3} │{'█' * round(count / peak * size)} {count}" for idx, count in bins.items()
        ]
        lines.append("    └" + "─" * (size + 4))
        return "\n".join(lines)

    heights = [round(c / peak * size) for c in counts]
    lines = []
    for level in range(size, 0, -1):  # top row first
        row = "".join(" █ " if h >= level else "   " for h in heights)
        lines.append(f"    │{row}")
    lines.append("    └" + "───" * len(heights))
    lines.append("     " + "".join(f"{i:^3}" for i in bins))
    return "\n".join(lines)


def _bin_layout[T: int | float](values: list[T], nmb_bins: int | None) -> tuple[int, float]:
    """Return (nmb_bins, step) using Freedman-Diaconis if bins not given."""
    lo, hi = min(values), max(values)
    span = hi - lo
    if span == 0:  # all values equal
        return 1, 1.0

    if nmb_bins is None:
        iqr = _calculate_percentile(values, 75) - _calculate_percentile(values, 25)
        step = 2 * iqr / len(values) ** (1 / 3)
        nmb_bins = math.ceil(math.log2(len(values))) + 1 if step == 0 else math.ceil(span / step)

    nmb_bins = max(nmb_bins, 1)
    return nmb_bins, span / nmb_bins
