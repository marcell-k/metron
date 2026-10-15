"""Descriptive Statistics."""

import math
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from metron.errors import ParseError

if TYPE_CHECKING:
    from collections.abc import Iterable

SEPERATOR = "-" * 24 + "\n"


@dataclass(frozen=True, slots=True)
class QuartileSummary:
    """Quartile Summary."""

    q1: float
    q3: float
    iqr: float
    tukeys: tuple[float, float]


@dataclass(frozen=True, slots=True)
class Stats:
    """Dataclass containing stats."""

    count: int
    sum: float
    minimum: float
    maximum: float
    range: float
    mean: float
    median: float
    mode: float
    var: float  # for entire population
    std: float
    mad: float
    quartile_summary: QuartileSummary
    skewness: float
    kurtosis: float

    def __str__(self) -> str:
        """Visualize stats."""
        s = "Descriptive statistics:\n"
        s += SEPERATOR
        lines = [
            f"{'Count:':<14} {self.count:>9}",
            f"{'Sum:':<14} {self.sum:>9}",
            f"{'Minimum:':<14} {self.minimum:>9}",
            f"{'Maximum:':<14} {self.maximum:>9}",
            f"{'Range:':<14} {self.range:>9}",
            f"{'Mean:':<14} {self.mean:>9}",
            f"{'Median:':<14} {self.median:>9}",
            f"{'Mode:':<14} {self.mode:>9}",
        ]
        s += "\n".join(lines)
        s += "\n\nQuartile Summary:\n"
        s += SEPERATOR
        lines = [
            f"{'Variance:':<14} {self.var:>9}",
            f"{'Std:':<14} {self.std:>9}",
            f"{'MAD:':<14} {self.mad:>9}",
            f"{'Q1:':<14} {self.quartile_summary.q1:>9}",
            f"{'Q3:':<14} {self.quartile_summary.q3:>9}",
            f"{'IQR:':<14} {self.quartile_summary.iqr:>9}",
            f"{"Tukey's lower:":<14} {self.quartile_summary.tukeys[0]:>9}",
            f"{"Tukey's upper:":<14} {self.quartile_summary.tukeys[1]:>9}",
            f"{'Skewness:':<14} {self.skewness:>9}",
            f"{'kurtosis:':<14} {self.kurtosis:>9}",
        ]
        s += "\n".join(lines)
        return s


def descriptive_statistics[T: int | float](data: Iterable[T]) -> Stats:
    """Calculate and return descriptive statistics."""
    if len(list(data)) < 4:  # noqa: PLR2004
        msg = f"data must contain at least 4 data points, got: `{len(list(data))}`"
        raise ParseError(msg)
    data = sorted(data)
    total = 0
    n = len(data)
    minimum = data[0]
    maximum = data[0]
    for val in data:
        minimum = min(minimum, val)
        maximum = max(maximum, val)
        total += val

    data_range = maximum - minimum
    mode = Counter(data).most_common()[0][0]
    mean = total / n
    median = _calculate_median(data)

    var = sum([(x - mean) ** 2 for x in data]) / n
    std = var**0.5
    mad = _calculate_mad(data, median)
    quartile_summary = calculate_quartile_statistics(data)
    skewness = round(_calculate_skewness(data, mean, std), 3)
    kurtosis = round(_calculate_kurtosis(data, mean), 3)

    return Stats(
        n,
        r(total),
        r(minimum),
        r(maximum),
        r(data_range),
        r(mean),
        r(median),
        r(mode),
        r(var),
        r(std),
        r(mad),
        QuartileSummary(
            q1=r(quartile_summary.q1),
            q3=r(quartile_summary.q3),
            iqr=r(quartile_summary.iqr),
            tukeys=(r(quartile_summary.tukeys[0]), r(quartile_summary.tukeys[1])),
        ),
        r(skewness),
        r(kurtosis),
    )


def r(value: float, sig: int = 3) -> float:
    """Round."""
    return value if value == 0 else round(value, sig - 1 - math.floor(math.log10(abs(value))))


def _calculate_mad[T: int | float](values: Iterable[T], median: T) -> float:
    """Median absolute deiation (MAD)."""
    diffs = [abs(x - median) for x in values]
    diffs = sorted(diffs)
    return _calculate_median(diffs)


def _calculate_median[T: int | float](values: list[T]) -> float:
    n = len(values)
    mid_idx = n // 2
    return values[mid_idx] if n % 2 == 1 else (values[mid_idx] + values[mid_idx - 1]) / 2


def calculate_quartile_statistics[T: int | float](values: list[T]) -> QuartileSummary:
    """Calculate quartile statistics summary."""
    q1 = _calculate_percentile(values, 25)
    q3 = _calculate_percentile(values, 75)
    iqr = q3 - q1
    tukeys = (q1 - 1.5 * iqr, q3 + 1.5 * iqr)
    return QuartileSummary(q1, q3, iqr, tukeys)


def _calculate_percentile[T: int | float](values: list[T], percentile: float = 25) -> float:
    """Calculate percentile use interpolation."""
    if not 0 < percentile <= 100:  # noqa: PLR2004
        msg = f"percentile must be between 0 and 100, got: `{percentile}`"
        raise ParseError(msg)
    int_index, frac_index = divmod((len(values) - 1) * percentile / 100, 1)
    int_index = int(int_index)
    return values[int_index] + (values[int_index + 1] - values[int_index]) * frac_index


def _calculate_skewness[T: int | float](values: list[T], mean: float, std: float) -> float:
    """Calcualte Adjusted Fisher-Pearson (Small-Sample Bias Correction)."""
    n = len(values)
    moment_3 = sum((x - mean) ** 3 for x in values) / n
    correction = (n * (n - 1)) ** 0.5 / (n - 2)
    return correction * moment_3 / std**3


def _calculate_kurtosis[T: int | float](values: list[T], mean: float) -> float:
    """Calculate bias-corrected excess kurtosis."""
    n = len(values)
    moment_2 = sum((x - mean) ** 2 for x in values) / n
    moment_4 = sum((x - mean) ** 4 for x in values) / n
    excess_kurtosis = moment_4 / moment_2**2 - 3
    return (n - 1) / ((n - 2) * (n - 3)) * ((n + 1) * excess_kurtosis + 6)
