"""Terminal plotting."""

from enum import StrEnum
from typing import TYPE_CHECKING

from metron.utils import bin_values, r

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

BAR = "█"


class PlotType(StrEnum):
    """Types of plot."""

    HISTOGRAM = "histogram"
    LINE = "line"


def render(
    bins: dict[int, int],
    size: int = 10,
    *,
    horizontal: bool = True,
    labels: Sequence[str] | None = None,
) -> str:
    """Render bins. `size` = max bar length (width or height). `labels` = row names."""
    peak = max(bins.values()) or 1

    def scale(count: int) -> int:
        return max(1, round(count / peak * size)) if count else 0

    if horizontal:
        names = list(labels) if labels else [str(i) for i in bins]
        pad = max(map(len, names))
        lines = [
            f"{name:>{pad}} │{BAR * scale(count)} {count}"
            for name, count in zip(names, bins.values(), strict=True)
        ]
        lines.append(" " * (pad + 1) + "└" + "─" * (size + 4))
        return "\n".join(lines)

    heights = [scale(c) for c in bins.values()]
    lines = []
    for level in range(size, 0, -1):  # top row first
        row = "".join(f" {BAR} " if h >= level else "   " for h in heights)
        lines.append(f"    │{row}")
    lines.append("    └" + "───" * len(heights))
    lines.append("     " + "".join(f"{i:^3}" for i in bins))
    return "\n".join(lines)


def draw_histogram(
    values: Iterable[float], size: int = 40, nmb_bins: int | None = None, *, horizontal: bool = True
) -> str:
    """Draw histogram."""
    data = sorted(values)
    bins, step = bin_values(data, nmb_bins)
    labels = [str(r(data[0] + step * k)) for k in bins]
    chart = render(bins, size, horizontal=horizontal, labels=labels)
    return f"{chart}\nRange: ({data[0]}, {data[-1]})   Bin width: {step:.4g}"


def draw_line(x: Sequence[float], y: Sequence[float], width: int = 60, height: int = 17) -> str:
    """Draw line plot. One column per char, linear interpolation between points."""
    pairs = sorted(zip(x, y, strict=True))
    if not pairs:
        msg = "No values to plot."
        raise ValueError(msg)
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    min_x, max_x = xs[0], xs[-1]
    min_y, max_y = min(ys), max(ys)
    span_x = (max_x - min_x) or 1
    span_y = (max_y - min_y) or 1

    canvas = [[" "] * width for _ in range(height)]
    i = 0
    for col in range(width):
        cx = min_x + span_x * col / max(width - 1, 1)
        while i < len(xs) - 2 and cx > xs[i + 1]:
            i += 1
        if len(xs) == 1:
            y_val = ys[0]
        else:
            a, b = xs[i], xs[i + 1]
            t = min(max((cx - a) / (b - a), 0.0), 1.0) if b != a else 0.0  # dup x guard
            y_val = (1 - t) * ys[i] + t * ys[i + 1]

        row = min(max(round((y_val - min_y) / span_y * (height - 1)), 0), height - 1)
        canvas[height - 1 - row][col] = "*"

    labels = [
        f"{max_y - span_y * i / max(height - 1, 1):.4g}" if i % 2 == 0 or i == height - 1 else ""
        for i in range(height)
    ]
    pad = max(map(len, labels))
    lines = [f"{label:>{pad}}│{''.join(row)}" for label, row in zip(labels, canvas, strict=True)]
    lines.append(" " * pad + "└" + "─" * width)
    lo, hi = f"{min_x:.4g}", f"{max_x:.4g}"
    gap = max(width - len(lo) - len(hi), 1)
    lines.append(" " * (pad + 1) + lo + " " * gap + hi)
    return "\n".join(lines)


def plot(
    x: Sequence[float],
    y: Sequence[float] | None = None,
    plot_type: PlotType = PlotType.HISTOGRAM,
    width: int = 60,
    height: int = 17,
) -> str:
    """Dispatch by plot type. Histogram ignore `y`."""
    if plot_type == PlotType.HISTOGRAM:
        return draw_histogram(x, size=width)
    if y is None:
        y = list(range(len(x)))
    return draw_line(x, y, width, height)
