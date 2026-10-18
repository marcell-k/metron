"""Terminal plotting."""

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from metron.utils import bin_values, r

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

BAR = "█"
DENSITY = " .:*#"  # empty -> densest


@dataclass(frozen=True, slots=True)
class Config:
    """Global config."""

    plot_width: int = 60
    plot_height: int = 17


config = Config()
WIDTH = config.plot_width
HEIGHT = config.plot_height


class PlotType(StrEnum):
    """Types of plot."""

    HISTOGRAM = "histogram"
    LINE = "line"
    SCATTER = "scatter"


def _frame(canvas: list[list[str]], bounds: tuple[float, float, float, float]) -> str:
    """Add y labels, x axis, x labels to canvas. `bounds` = (min_x, max_x, min_y, max_y)."""
    min_x, max_x, min_y, max_y = bounds
    span_y = (max_y - min_y) or 1
    labels = [
        f"{max_y - span_y * i / max(HEIGHT - 1, 1):.4g}" if i % 2 == 0 or i == HEIGHT - 1 else ""
        for i in range(HEIGHT)
    ]
    pad = max(map(len, labels))
    lines = [f"{label:>{pad}}│{''.join(row)}" for label, row in zip(labels, canvas, strict=True)]
    lines.append(" " * pad + "└" + "─" * WIDTH)
    lo, hi = f"{min_x:.7g}", f"{max_x:.7g}"  # no 1e+06
    gap = max(WIDTH - len(lo) - len(hi), 1)
    lines.append(" " * (pad + 1) + lo + " " * gap + hi)
    return "\n".join(lines)


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
    values: Iterable[float], nmb_bins: int | None = None, size: int = 40, *, horizontal: bool = True
) -> str:
    """Draw histogram."""
    data = sorted(values)
    if not horizontal:
        size //= 2
    bins, step = bin_values(data, nmb_bins)
    last = len(bins) - 1
    labels = [
        f"[{r(data[0] + step * k):g}, {r(data[0] + step * (k + 1)):g}{']' if k == last else ')'}"
        for k in bins
    ]
    length = size if horizontal else max(size // 2, 1)
    chart = render(bins, length, horizontal=horizontal, labels=labels)
    return (
        f"{chart}\nRange: ({data[0]}, {data[-1]})   Bin width: {step:.4g}\n"
        "Bins: left-closed [lo, hi), last bin also includes max"
    )


def draw_line(
    x: Sequence[float], y: Sequence[float], width: int = WIDTH, height: int = HEIGHT
) -> str:
    """Draw line plot. Per column: min-max span of its points. Empty columns interpolated."""
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

    def to_row(v: float) -> int:
        return min(max(round((v - min_y) / span_y * (height - 1)), 0), height - 1)

    col_lo = [math.inf] * width
    col_hi = [-math.inf] * width
    for px, py in pairs:
        col = round((px - min_x) / span_x * max(width - 1, 1))
        col_lo[col] = min(col_lo[col], py)
        col_hi[col] = max(col_hi[col], py)

    canvas = [[" "] * width for _ in range(height)]
    i = 0
    for col in range(width):
        if col_lo[col] <= col_hi[col]:
            lo, hi = col_lo[col], col_hi[col]
        else:
            cx = min_x + span_x * col / max(width - 1, 1)
            while i < len(xs) - 2 and cx > xs[i + 1]:
                i += 1
            if len(xs) == 1:
                lo = hi = ys[0]
            else:
                a, b = xs[i], xs[i + 1]
                t = min(max((cx - a) / (b - a), 0.0), 1.0) if b != a else 0.0  # dup x guard
                lo = hi = (1 - t) * ys[i] + t * ys[i + 1]
        for row in range(to_row(lo), to_row(hi) + 1):
            canvas[height - 1 - row][col] = "*"

    return _frame(canvas, (min_x, max_x, min_y, max_y))


def draw_scatter(x: Sequence[float], y: Sequence[float]) -> str:
    """Draw scatter plot. Char shows point count per cell, no line between."""
    if not x:
        msg = "No values to plot."
        raise ValueError(msg)
    min_x, max_x = min(x), max(x)
    min_y, max_y = min(y), max(y)
    span_x = (max_x - min_x) or 1
    span_y = (max_y - min_y) or 1

    counts = [[0] * WIDTH for _ in range(HEIGHT)]
    for px, py in zip(x, y, strict=True):
        col = round((px - min_x) / span_x * (WIDTH - 1))
        row = round((py - min_y) / span_y * (HEIGHT - 1))
        counts[HEIGHT - 1 - row][col] += 1

    peak = max(max(line) for line in counts)
    top = len(DENSITY) - 1
    canvas = [[DENSITY[-(-c * top // peak)] if c else " " for c in line] for line in counts]

    return _frame(canvas, (min_x, max_x, min_y, max_y))


def plot(
    title: str,
    x: Sequence[float],
    y: Sequence[float] | None = None,
    plot_type: PlotType = PlotType.HISTOGRAM,
) -> str:
    """Dispatch by plot type. Histogram ignore `y`."""
    s = "\n" + title.center(WIDTH) + "\n"
    if plot_type == PlotType.HISTOGRAM:
        return s + draw_histogram(x, size=WIDTH) + "\n"
    if y is None:
        y = list(range(len(x)))
    if plot_type == PlotType.SCATTER:
        return s + draw_scatter(x, y) + "\n"
    return s + draw_line(x, y, WIDTH, HEIGHT) + "\n"
