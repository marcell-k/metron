"""Utils."""

import math
from typing import TYPE_CHECKING

from metron.errors import ParseError

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence


def fmt(value: object) -> str:
    """Format cell. Floats to 2 decimals."""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def clean_data(line: str, sep: str = ",") -> list[float]:
    """Split and clean data by seperator."""
    return [float(x) for x in line.split(sep=sep)]


def r(value: float, sig: int = 3) -> float:
    """Round."""
    return value if value == 0 else round(value, sig - 1 - math.floor(math.log10(abs(value))))


def calculate_percentile(values: Sequence[float], percentile: float = 25) -> float:
    """Calculate percentile use interpolation."""
    if not 0 < percentile <= 100:  # noqa: PLR2004
        msg = f"percentile must be between 0 and 100, got: `{percentile}`"
        raise ParseError(msg)
    int_index, frac_index = divmod((len(values) - 1) * percentile / 100, 1)
    int_index = int(int_index)
    return values[int_index] + (values[int_index + 1] - values[int_index]) * frac_index


def calculate_std(values: Collection[float]) -> float:
    """Calculate std."""
    mean = sum(values) / len(values)
    var = sum((x - mean) ** 2 for x in values) / len(values)
    return var**0.5


# ----- histogram binning -----


def bin_layout(values: list[float], nmb_bins: int | None) -> tuple[int, float]:
    """Return (nmb_bins, step), Freedman-Diaconis if bins not given."""
    lo, hi = min(values), max(values)
    span = hi - lo
    if span == 0:  # all values equal
        return 1, 1.0

    if nmb_bins is None:
        iqr = calculate_percentile(values, 75) - calculate_percentile(values, 25)
        step = 2 * iqr / len(values) ** (1 / 3)
        nmb_bins = math.ceil(math.log2(len(values))) + 1 if step == 0 else math.ceil(span / step)

    nmb_bins = max(nmb_bins, 1)
    return nmb_bins, span / nmb_bins


def bin_values(
    values: Sequence[float], nmb_bins: int | None = None
) -> tuple[dict[int, int], float]:
    """Count values per bin. Return (bins, step)."""
    data = sorted(values)
    if not data:
        msg = "No values to bin."
        raise ValueError(msg)
    nmb_bins, step = bin_layout(data, nmb_bins)
    bins = dict.fromkeys(range(nmb_bins), 0)
    start = data[0]
    for v in data:
        bins[min(int((v - start) / step), nmb_bins - 1)] += 1
    return bins, step
