"""Relationship."""

import math
from typing import TYPE_CHECKING

from metron.descriptive import Seperator
from metron.errors import MetronError
from metron.utils import calculate_std, r

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence


# TODO: fill missing None, nan values with mean
def calculate_covariance(x: Collection[float], y: Collection[float]) -> float:
    """Covariance, tells the linear Relationship between ``x``, and ``y``.

    Formula: `Cov (X,Y) = E[(X-E[X])(Y-E[Y])] = E[XY]-E[X]E[Y].`
    """
    mean_x, mean_y = sum(x) / len(x), sum(y) / len(y)
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(x, y, strict=True)) / len(x)


def pearson_correlation(x: Collection[float], y: Collection[float]) -> float:
    """Pearson correlation."""
    return pearson_correlation(_rank(list(x)), _rank(list(y)))


def spearman_correlation(x: Collection[float], y: Collection[float]) -> float:
    """Spearman correlation, uses ranks."""
    rank_x = _rank(list(x))
    rank_y = _rank(list(y))
    diffs = sum((x - y) ** 2 for x, y in zip(rank_x, rank_y, strict=True))
    return 1 - (6 * diffs) / (len(x) * (len(x) ** 2 - 1))


def confidence_interval(
    x: Collection[float], y: Collection[float], method: str
) -> tuple[float, float, float]:
    """Confidence interval using Fieller, and 95% confidence."""
    if method not in ("spearman", "pearson"):
        msg = f"invalid confidence interval, must be in `(spearman, pearson)`, got: {method}"
        raise MetronError(msg)
    if method == "spearman":
        rho = spearman_correlation(x, y)
        standard_error = math.sqrt((1 + rho**2 / 2) / (len(x) - 3))  #  Fieller
    else:
        rho = pearson_correlation(x, y)
        standard_error = 1 / math.sqrt(len(x) - 3)
    z = _fisher_transform(rho)
    delta = 1.96 * standard_error  # 1.96 is 95% confidence
    lower = math.tanh(z - delta)
    upper = math.tanh(z + delta)
    return rho, lower, upper


def _rank(v: Sequence[float]) -> list[float]:
    """Average ranks, 1-based. Tied values share mean of their positions."""
    order = sorted(range(len(v)), key=v.__getitem__)
    ranks = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _fisher_transform(value: float) -> float:
    if not -1 < value < 1:
        msg = f"value must be between `]-1, 1[`, got: {value}"
        raise MetronError(msg)
    return 0.5 * math.log((1 + value) / (1 - value))


def ols(x: Sequence[float], y: Sequence[float]) -> tuple[float, float]:
    """Return slope, intercept."""
    var_x = calculate_std(x) ** 2
    if var_x == 0:
        msg = "x has zero variance, cannot fit line"
        raise MetronError(msg)
    slope = calculate_covariance(x, y) / var_x
    intercept = sum(y) / len(y) - slope * sum(x) / len(x)
    return slope, intercept


def calculate_rsquare(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Compute r^2 of least-squares fit."""
    m, b = ols(xs, ys)
    linreg = [m * x + b for x in xs]
    mean = sum(ys) / len(ys)
    ssr = sum((y - lin) ** 2 for y, lin in zip(ys, linreg, strict=True))
    sst = sum((y - mean) ** 2 for y in ys)
    return 1 - ssr / sst


def analyze_relationship(x: Collection[float], y: Collection[float]) -> str:
    """Entry point for the full relationship analyzation."""
    if len(x) != len(y):
        msg = f"The two variable lens are different, got: {len(x), len(y)}"
        raise MetronError(msg)
    cov = calculate_covariance(x, y)
    p_corr, p_low, p_upp = confidence_interval(x, y, "pearson")
    s_corr, s_low, s_upp = confidence_interval(x, y, "spearman")
    r2 = calculate_rsquare(list(x), list(y))

    s = "Relationship analysis:\n"
    s += Seperator

    lines = [
        f"{'Covariance:':<14} {r(cov):>9}",
        f"{'Pearson:':<14} {r(p_corr):>9} (`{r(p_low)}`-`{r(p_upp)}`), 95% confidence",
        f"{'Spearman:':<14} {r(s_corr):>9} (`{r(s_low)}`-`{r(s_upp)}`), 95% confidence",
        f"{'R²:':<14} {r(r2):>9}",
    ]
    s += "\n".join(lines)
    return s
