from decimal import Decimal

import pytest

from app.services.arc import _usdc_to_raw, usdc_to_float


def test_usdc_to_raw():
    assert _usdc_to_raw(Decimal("1")) == 1_000_000
    assert _usdc_to_raw(Decimal("0.25")) == 250_000
    assert _usdc_to_raw(Decimal("2.5")) == 2_500_000


def test_usdc_to_float():
    assert usdc_to_float(1_000_000) == 1.0
    assert usdc_to_float(250_000) == 0.25


def test_usdc_rejects_zero():
    with pytest.raises(
        ValueError,
        match="USDC amount must be greater than zero",
    ):
        _usdc_to_raw(Decimal("0"))


def test_usdc_rejects_more_than_six_decimals():
    with pytest.raises(
        ValueError,
        match="USDC amount cannot have more than 6 decimal places",
    ):
        _usdc_to_raw(Decimal("0.1234567"))