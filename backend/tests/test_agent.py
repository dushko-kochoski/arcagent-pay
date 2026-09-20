from decimal import Decimal

from app.schemas import AgentDecisionRequest
from app.services.agent import decide_payment


def test_agent_requests_payment():
    request = AgentDecisionRequest(
        objective="Pay the approved contributor",
        recipient="0x0804BeC55DdF4Da0613dFf53740F9Bd131ef8411",
        requested_amount_usdc=Decimal("0.1"),
    )

    decision = decide_payment(request)

    assert decision.decision == "pay"
    assert decision.recipient == request.recipient
    assert decision.amount_usdc == Decimal("0.1")
    assert "on-chain policy" in decision.reason


def test_agent_does_not_enforce_vault_limit():
    request = AgentDecisionRequest(
        objective="Pay the approved contributor",
        recipient="0x0804BeC55DdF4Da0613dFf53740F9Bd131ef8411",
        requested_amount_usdc=Decimal("2.5"),
    )

    decision = decide_payment(request)

    assert decision.decision == "pay"
    assert decision.amount_usdc == Decimal("2.5")