"""Distribution and frequency."""

from bisect import bisect_right
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import TYPE_CHECKING

from metron.descriptive import _calculate_mad, calculate_quartile_statistics
from metron.errors import MetronError
from metron.plot import PlotType, plot
from metron.utils import bin_values, calculate_std, fmt, r

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


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
            yield getattr(self, f.name)

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
    return plot("ECDF", values, out, plot_type=PlotType.LINE)


def calculate_zscore(values: Iterable[float]) -> str:
    """Calculate z-score and plot it."""
    z_threshold = 3
    values = list(values)
    std = calculate_std(values)
    if std == 0:
        msg = "std must be above 0"
        raise MetronError(msg)
    mean = sum(values) / len(values)
    zscores = [(x - mean) / std for x in values]
    chart = plot("Z-score distribution", zscores, plot_type=PlotType.HISTOGRAM)
    flagged = [v for v, z in zip(values, zscores, strict=True) if abs(z) > z_threshold]
    shown = list(map(r, flagged[:10]))
    more = f", ... +{len(flagged) - 10} more" if len(flagged) > 10 else ""  # noqa: PLR2004
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

    outliers = [v for v in values if not lower <= v <= upper]
    shown = list(map(r, outliers[:10]))
    more = f", ... +{len(outliers) - 10} more" if len(outliers) > 10 else ""  # noqa: PLR2004
    x = list(range(1, len(values) + 1))
    chart = plot(f"Outlier detection, using: {method}", x, values, PlotType.SCATTER)
    return (
        f"{chart}\n"
        f"Median: {median:.4g}   Fences: ({lower:.4g}, {upper:.4g})\n"
        f"Outliers ({len(outliers)}): {shown}{more}"
    )
