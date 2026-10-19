"""Distribution and frequency."""

from bisect import bisect_right
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import TYPE_CHECKING, cast, override

from metron.descriptive import _calculate_mad, calculate_quartile_statistics
from metron.errors import MetronError
from metron.plot import WIDTH, Figure, draw_histogram
from metron.utils import bin_values, calculate_std, fmt, r

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

MAX_LISTED = 10
PADDING = 2


class OutlierMethod(StrEnum):
    """Outlier methods."""

    MAD = "mad"
    IQR = "iqr"


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
            yield cast("list[str | int | float]", getattr(self, f.name))

    @override
    def __str__(self) -> str:
        """Visualize table."""
        columns = [
            ("class", self._class),
            ("freq", self.freq),
            ("rel. freq", self.rel_freq),
            ("cum. freq", self.cum_freq),
            ("cum. rel. freq", self.cum_rel_freq),
        ]

        widths = [max(len(name), *(len(fmt(v)) for v in values)) + 2 for name, values in columns]
        header = (
            "|" + "|".join(n.center(w) for (n, _), w in zip(columns, widths, strict=True)) + "|"
        )
        separator = "+" + "+".join("-" * w for w in widths) + "+"
        rows = [
            "|" + "|".join(fmt(v).center(w) for v, w in zip(row, widths, strict=True)) + "|"
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
    """Calculate empirical cumulative distribution function (ECDF)."""
    values = sorted(values)
    n = len(values)
    out = [bisect_right(values, v) / n for v in values]
    return Figure("ECDF").line(values, out).render()


def calculate_zscore(values: Iterable[float]) -> str:
    """Calculate z-score and plot its distribution."""
    z_threshold = 3
    values = list(values)
    std = calculate_std(values)
    if std == 0:
        msg = "std must be above 0"
        raise MetronError(msg)
    mean = sum(values) / len(values)
    zscores = [(x - mean) / std for x in values]
    title = "Z-score distribution".center(WIDTH)
    chart = f"\n{title}\n{draw_histogram(zscores, size=WIDTH)}\n"
    flagged = sorted(
        (v for v, z in zip(values, zscores, strict=True) if abs(z) > z_threshold),
        key=lambda v: -abs(v - mean),
    )
    shown = list(map(r, flagged[:MAX_LISTED]))
    more = f", ... +{len(flagged) - MAX_LISTED} more" if len(flagged) > MAX_LISTED else ""
    return (
        f"{chart}\nmean: {mean:.4g} std: {std:.4g}\n"
        f"|z| > {z_threshold} ({len(flagged)}): {shown}{more}"
    )


def outlier_detection(values: Iterable[float], method: OutlierMethod) -> str:
    """Outlier detection."""
    c = 1.4826 * 2.5  # 3.7065 | 1.4826 * 3 = 4.4478
    values = list(values)
    median, mad = _calculate_mad(values)
    if method is OutlierMethod.IQR:
        summary = calculate_quartile_statistics(values)
        lower, upper = summary.tukeys[0], summary.tukeys[1]
    else:
        if mad == 0:
            msg = "MAD is 0, cannot detect outliers"
            raise MetronError(msg)
        lower, upper = median - mad * c, median + mad * c

    outliers = sorted(
        (v for v in values if not lower <= v <= upper),
        key=lambda v: -abs(v - median),
    )
    shown = outliers[:MAX_LISTED]
    more = f", ... +{len(outliers) - MAX_LISTED} more" if len(outliers) > MAX_LISTED else ""
    chart = (
        Figure(f"Outlier detection, using: {method}")
        .scatter(list(range(1, len(values) + 1)), values)
        .hline(lower, "┄")
        .hline(upper, "┄")
        .hline(median, "─")
        .render()
    )
    return (
        f"{chart}\n"
        f"Median: {median:.4g}   Fences: ({lower:.4g}, {upper:.4g})\n"
        f"Outliers ({len(outliers)}): {shown}{more}"
    )
