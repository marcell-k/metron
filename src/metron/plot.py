"""Terminal plotting."""

from dataclasses import dataclass, field
from enum import StrEnum
from itertools import pairwise
from typing import TYPE_CHECKING, Self

from metron.utils import bin_values, r

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence


BAR = "█"
DENSITY = " .:*#"  # empty -> densest
NO_VALUES = "No values to plot."

type Scaler = Callable[[float], int]
type Canvas = list[list[str]]


@dataclass(frozen=True, slots=True)
class Config:
    """Global config."""

    plot_width: int = 60
    plot_height: int = 17


config = Config()
WIDTH = config.plot_width
HEIGHT = config.plot_height


class Kind(StrEnum):
    """Layer kinds. Declaration order = draw order (first drawn = bottom)."""

    HLINE = "hline"
    VLINE = "vline"
    LINE = "line"
    SCATTER = "scatter"


Z_ORDER = {kind: i for i, kind in enumerate(Kind)}


@dataclass(frozen=True, slots=True)
class _Layer:
    kind: Kind
    x: tuple[float, ...]
    y: tuple[float, ...]
    char: str


def _scale(v: float, lo: float, span: float, n: int) -> int:
    """Map value to cell index in `[0, n)`."""
    return min(max(round((v - lo) / span * (n - 1)), 0), n - 1)


def _frame(
    canvas: Canvas, bounds: tuple[float, float, float, float], width: int, height: int
) -> str:
    """Add y labels, x axis, x labels to canvas. `bounds` = (min_x, max_x, min_y, max_y)."""
    min_x, max_x, min_y, max_y = bounds
    span_y = (max_y - min_y) or 1
    labels = [
        f"{max_y - span_y * i / max(height - 1, 1):.4g}" if i % 2 == 0 or i == height - 1 else ""
        for i in range(height)
    ]
    pad = max(map(len, labels))
    lines = [f"{label:>{pad}}│{''.join(row)}" for label, row in zip(labels, canvas, strict=True)]
    lines.append(" " * pad + "└" + "─" * width)
    lo, hi = f"{min_x:.7g}", f"{max_x:.7g}"  # no 1e+06
    gap = max(width - len(lo) - len(hi), 1)
    lines.append(" " * (pad + 1) + lo + " " * gap + hi)
    return "\n".join(lines)


@dataclass(slots=True)
class Figure:
    """Layered xy chart. Bounds = union of all layers. Chain calls, end with `render()`."""

    title: str = ""
    width: int = WIDTH
    height: int = HEIGHT
    _layers: list[_Layer] = field(default_factory=list, init=False, repr=False)

    def scatter(self, x: Sequence[float], y: Sequence[float]) -> Self:
        """Add points. Cell char shows point count."""
        self._layers.append(_Layer(Kind.SCATTER, tuple(x), tuple(y), "*"))
        return self

    def line(self, x: Sequence[float], y: Sequence[float], char: str = "*") -> Self:
        """Add line. Per column: min-max span. Empty columns interpolated."""
        self._layers.append(_Layer(Kind.LINE, tuple(x), tuple(y), char))
        return self

    def hline(self, y: float, char: str = "─") -> Self:
        """Add horizontal guide at `y`."""
        self._layers.append(_Layer(Kind.HLINE, (), (y,), char))
        return self

    def vline(self, x: float, char: str = "│") -> Self:
        """Add vertical guide at `x`."""
        self._layers.append(_Layer(Kind.VLINE, (x,), (), char))
        return self

    def _bounds(self) -> tuple[float, float, float, float]:
        """Union of all layers. `(min_x, max_x, min_y, max_y)`."""
        all_x = [v for layer in self._layers for v in layer.x]
        all_y = [v for layer in self._layers for v in layer.y]
        if not all_x or not all_y:
            raise ValueError(NO_VALUES)
        return min(all_x), max(all_x), min(all_y), max(all_y)

    def render(self) -> str:
        """Draw all layers."""
        min_x, max_x, min_y, max_y = self._bounds()
        w, h = self.width, self.height
        span_x, span_y = (max_x - min_x) or 1, (max_y - min_y) or 1

        def col(v: float) -> int:
            return _scale(v, min_x, span_x, w)

        def row(v: float) -> int:  # 0 = top
            return h - 1 - _scale(v, min_y, span_y, h)

        canvas = [[" "] * w for _ in range(h)]
        counts = [[0] * w for _ in range(h)]
        for layer in sorted(self._layers, key=lambda lyr: Z_ORDER[lyr.kind]):
            _draw_layer(canvas, counts, layer, col, row)
        _overlay_counts(canvas, counts)

        head = "\n" + self.title.center(w) + "\n" if self.title else ""
        return head + _frame(canvas, (min_x, max_x, min_y, max_y), w, h) + "\n"


def _draw_layer(
    canvas: Canvas, counts: list[list[int]], layer: _Layer, col: Scaler, row: Scaler
) -> None:
    """Draw one layer. Scatter points go to `counts`, rest straight to `canvas`."""
    match layer.kind:
        case Kind.HLINE:
            canvas[row(layer.y[0])] = [layer.char] * len(canvas[0])
        case Kind.VLINE:
            c = col(layer.x[0])
            for line in canvas:
                line[c] = layer.char
        case Kind.LINE:
            _draw_line(canvas, layer, col, row)
        case Kind.SCATTER:
            for px, py in zip(layer.x, layer.y, strict=True):
                counts[row(py)][col(px)] += 1


def _overlay_counts(canvas: Canvas, counts: list[list[int]]) -> None:
    """Draw scatter density chars over everything else."""
    peak = max(max(line) for line in counts)
    if not peak:
        return
    top = len(DENSITY) - 1
    for i, line in enumerate(counts):
        for j, c in enumerate(line):
            if c:
                canvas[i][j] = DENSITY[-(-c * top // peak)]


def _draw_line(canvas: Canvas, layer: _Layer, col: Scaler, row: Scaler) -> None:
    """Min-max span per column. Gaps between data columns linearly interpolated."""
    w = len(canvas[0])
    lo = [float("inf")] * w
    hi = [float("-inf")] * w
    for px, py in zip(layer.x, layer.y, strict=True):
        c = col(px)
        lo[c], hi[c] = min(lo[c], py), max(hi[c], py)

    filled = [c for c in range(w) if lo[c] <= hi[c]]
    if not filled:
        return
    for a, b in pairwise(filled):  # consecutive data columns
        ya, yb = (lo[a] + hi[a]) / 2, (lo[b] + hi[b]) / 2
        for c in range(a + 1, b):
            lo[c] = hi[c] = ya + (yb - ya) * (c - a) / (b - a)

    for c in range(filled[0], filled[-1] + 1):
        for rr in range(row(hi[c]), row(lo[c]) + 1):
            canvas[rr][c] = layer.char


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
    return f"{chart}\nRange: ({r(data[0])}, {r(data[-1])})   Bin width: {step:.4g}"
