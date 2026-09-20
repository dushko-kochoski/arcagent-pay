from decimal import Decimal

from app.schemas import AgentDecisionRequest
from app.services import orchestrator
from app.services.errors import PaymentPolicyRejected


RECIPIENT = "0x0804BeC55DdF4Da0613dFf53740F9Bd131ef8411"


def test_agent_run_vault_approved(monkeypatch):
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
        orchestrator,
        "execute_agent_payment",
        fake_execute_agent_payment,
    )

    request = AgentDecisionRequest(
        objective="Pay contributor for completed work",
        recipient=RECIPIENT,
        requested_amount_usdc=Decimal("0.1"),
    )

    result = orchestrator.run_agent_payment(request)

    assert result.agent_decision == "pay"
    assert result.vault_result == "approved"
    assert result.amount_usdc == Decimal("0.1")
    assert result.tx_hash == "0xtesthash"
    assert result.explorer_url is not None


def test_agent_run_vault_rejected(monkeypatch):
    def fake_execute_agent_payment(
        recipient: str,
        amount_usdc: Decimal,
    ) -> dict:
        raise PaymentPolicyRejected(
            "Payment rejected by on-chain policy"
        )

    monkeypatch.setattr(
        orchestrator,
        "execute_agent_payment",
        fake_execute_agent_payment,
    )

    request = AgentDecisionRequest(
        objective="Pay contributor for completed work",
        recipient=RECIPIENT,
        requested_amount_usdc=Decimal("2.5"),
    )

    result = orchestrator.run_agent_payment(request)

    assert result.agent_decision == "pay"
    assert result.vault_result == "rejected"
    assert result.amount_usdc == Decimal("2.5")
    assert result.tx_hash is None
    assert result.explorer_url is None
    assert (
        result.detail
        == "Payment rejected by on-chain policy"
    )