from decimal import Decimal

from fastapi.testclient import TestClient

import app.main as main
from app.services.errors import PaymentPolicyRejected


client = TestClient(main.app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["name"] == "ArcAgent Pay"
    assert response.json()["status"] == "online"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_execute_payment_approved(monkeypatch):
    def fake_execute_agent_payment(
        recipient: str,
        amount_usdc: Decimal,
    ) -> dict:
        return {
            "status": "approved",
            "tx_hash": "0xtesthash",
            "explorer_url": (
                "https://explorer.testnet.arc.io/tx/0xtesthash"
            ),
            "recipient": recipient,
            "amount_usdc": float(amount_usdc),
        }

    monkeypatch.setattr(
        main,
        "execute_agent_payment",
        fake_execute_agent_payment,
    )

    monkeypatch.setattr(
        main,
        "record_payment",
        lambda **kwargs: 1,
    )

    response = client.post(
        "/payments/execute",
        json={
            "recipient": (
                "0x0804BeC55DdF4Da0613dFf53740F9Bd131ef8411"
            ),
            "amount_usdc": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "approved"
    assert data["tx_hash"] == "0xtesthash"
    assert data["amount_usdc"] == "1.0"


def test_execute_payment_policy_rejected(monkeypatch):
    def fake_execute_agent_payment(
        recipient: str,
        amount_usdc: Decimal,
    ) -> dict:
        raise PaymentPolicyRejected(
            "Payment rejected by on-chain policy"
        )

    monkeypatch.setattr(
        main,
        "execute_agent_payment",
        fake_execute_agent_payment,
    )

    monkeypatch.setattr(
        main,
        "record_payment",
        lambda **kwargs: 1,
    )

    response = client.post(
        "/payments/execute",
        json={
            "recipient": (
                "0x0804BeC55DdF4Da0613dFf53740F9Bd131ef8411"
            ),
            "amount_usdc": 2.5,
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Payment rejected by on-chain policy"
    }