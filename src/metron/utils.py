"""Utils."""


def clean_data(line: str, sep: str = ",") -> list[float]:
    """Split and clean data by seperator."""
    return [float(x) for x in line.split(sep=sep)]
