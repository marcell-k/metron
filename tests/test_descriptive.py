"""Test ``descriptive.py``."""

from dataclasses import fields

import pytest

from metron.descriptive import QuartileSummary, Stats, descriptive_statistics

EPSILIN = 1e-2


def test_descriptive() -> None:
    true = Stats(
        8,
        47,
        2,
        11,
        9,
        5.875,
        5.5,
        2,
        10.86,
        3.3,
        3,
        QuartileSummary(2.75, 8.5, 5.75, (-5.875, 17.125)),
        0.32,
        -1.52,
    )

    data = [2, 3, 5, 2, 8, 11, 10, 6]
    stats = descriptive_statistics(data)

    for f in fields(Stats):
        got = getattr(stats, f.name)
        want = getattr(true, f.name)
        if f.name == "quartile_summary":
            assert got.q1 == pytest.approx(want.q1, rel=1e-2)
            assert got.q3 == pytest.approx(want.q3, rel=1e-2)
            assert got.iqr == pytest.approx(want.iqr, rel=1e-2)
            assert got.tukeys == pytest.approx(want.tukeys, rel=1e-2)
        else:
            assert got == pytest.approx(want, rel=1e-2), f.name
