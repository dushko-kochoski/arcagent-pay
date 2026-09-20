from app.schemas import (
    AgentDecisionRequest,
    AgentRunResult,
)
from app.services.agent import decide_payment
from app.services.arc import execute_agent_payment
from app.services.errors import PaymentPolicyRejected


def run_agent_payment(
    request: AgentDecisionRequest,
) -> AgentRunResult:
    """
    Run one autonomous payment decision.

    The agent decides whether it wants to request a payment.
    The ArcAgentVault remains the final authority over whether
    that payment is permitted on-chain.
    """

    decision = decide_payment(request)

    if decision.decision == "reject":
        return AgentRunResult(
            agent_decision="reject",
            agent_reason=decision.reason,
            vault_result="not_requested",
            recipient=decision.recipient,
            amount_usdc=decision.amount_usdc,
            detail="Agent chose not to request a payment",
        )

    if decision.amount_usdc is None:
        return AgentRunResult(
            agent_decision="reject",
            agent_reason="Agent produced no payment amount",
            vault_result="not_requested",
            recipient=decision.recipient,
            amount_usdc=None,
            detail="No payment was requested",
        )

    try:
        payment = execute_agent_payment(
            recipient=decision.recipient,
            amount_usdc=decision.amount_usdc,
        )

    except PaymentPolicyRejected as exc:
        return AgentRunResult(
            agent_decision="pay",
            agent_reason=decision.reason,
            vault_result="rejected",
            recipient=decision.recipient,
            amount_usdc=decision.amount_usdc,
            detail=str(exc),
        )

    return AgentRunResult(
        agent_decision="pay",
        agent_reason=decision.reason,
        vault_result="approved",
        recipient=payment["recipient"],
        amount_usdc=decision.amount_usdc,
        tx_hash=payment["tx_hash"],
        explorer_url=payment["explorer_url"],
        detail="Payment approved by on-chain policy and executed",
    )