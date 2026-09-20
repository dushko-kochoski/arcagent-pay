from app.schemas import EvaluationResult, PaymentRequest, Policy


def evaluate_payment(policy: Policy, payment: PaymentRequest) -> EvaluationResult:
    remaining = max(policy.daily_limit - policy.daily_spent, 0)

    if policy.paused:
        return EvaluationResult(
            allowed=False,
            reason="Vault is paused",
            remaining_daily_limit=remaining,
        )

    if policy.expired:
        return EvaluationResult(
            allowed=False,
            reason="Policy has expired",
            remaining_daily_limit=remaining,
        )

    if payment.amount > policy.per_transaction_limit:
        return EvaluationResult(
            allowed=False,
            reason="Payment exceeds per-transaction limit",
            remaining_daily_limit=remaining,
        )

    if payment.amount > remaining:
        return EvaluationResult(
            allowed=False,
            reason="Payment exceeds remaining daily limit",
            remaining_daily_limit=remaining,
        )

    if policy.allowlist_enabled and payment.recipient.lower() not in {
        item.lower() for item in policy.allowed_recipients
    }:
        return EvaluationResult(
            allowed=False,
            reason="Recipient is not allowlisted",
            remaining_daily_limit=remaining,
        )

    return EvaluationResult(
        allowed=True,
        reason="Payment satisfies policy",
        remaining_daily_limit=remaining - payment.amount,
    )
