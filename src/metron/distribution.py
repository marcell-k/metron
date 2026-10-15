"""Distribution and frequency."""

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

from metron.descriptive import _calculate_percentile

PADDING = 2


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
