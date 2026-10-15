"""Utils."""

import math


def clean_data(line: str, sep: str = ",") -> list[float]:
    """Split and clean data by seperator."""
    return [float(x) for x in line.split(sep=sep)]


def r(value: float, sig: int = 3) -> float:
    """Round."""
    return value if value == 0 else round(value, sig - 1 - math.floor(math.log10(abs(value))))
