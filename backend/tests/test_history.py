from decimal import Decimal

import pytest

from app.services import history


@pytest.fixture
def history_db(tmp_path, monkeypatch):
    database_path = tmp_path / "arcagent_pay_test.db"

    monkeypatch.setattr(
        history,
        "DATA_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        history,
        "DATABASE_PATH",
        database_path,
    )

    history.init_history_db()

    return database_path


def test_history_starts_empty(history_db):
    assert history.list_payments() == []


def test_record_approved_payment(history_db):
    payment_id = history.record_payment(
        status="approved",
        recipient="0x0804BeC55DdF4Da0613dFf53740F9Bd131ef8411",
        amount_usdc=Decimal("0.25"),
        tx_hash="0xtesthash",
        explorer_url="https://explorer.testnet.arc.io/tx/0xtesthash",
    )

    assert payment_id == 1

    payments = history.list_payments()

    assert len(payments) == 1

    payment = payments[0]

    assert payment["status"] == "approved"
    assert payment["amount_usdc"] == "0.25"
    assert payment["tx_hash"] == "0xtesthash"
    assert payment["reason"] is None


def test_record_rejected_payment(history_db):
    payment_id = history.record_payment(
        status="rejected",
        recipient="0x0804BeC55DdF4Da0613dFf53740F9Bd131ef8411",
        amount_usdc=Decimal("2.5"),
        reason="Payment rejected by on-chain policy",
    )

    assert payment_id == 1

    payments = history.list_payments()

    assert len(payments) == 1

    payment = payments[0]

    assert payment["status"] == "rejected"
    assert payment["amount_usdc"] == "2.5"
    assert payment["tx_hash"] is None
    assert payment["explorer_url"] is None
    assert (
        payment["reason"]
        == "Payment rejected by on-chain policy"
    )