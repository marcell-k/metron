"""Test ``descriptive.py``."""

import pytest

from metron.relationship import pearson_correlation, spearman_correlation

EPSILIN = 1e-2


def test_relationship() -> None:
    iq = [106, 100, 86, 101, 99, 103, 97, 113, 112, 110]
    hours = [7, 27, 2, 50, 28, 29, 20, 12, 6, 17]
    assert spearman_correlation(iq, hours) == pytest.approx(-0.17575757, EPSILIN)

    assert pearson_correlation(iq, hours) == pytest.approx(-0.0702, EPSILIN)
