from app.schemas import PaymentRequest, Policy
from app.services.policy import evaluate_payment


RECIPIENT = "0x1111111111111111111111111111111111111111"


def base_policy(**overrides) -> Policy:
    values = dict(
        per_transaction_limit=100,
        daily_limit=250,
        daily_spent=50,
        allowlist_enabled=True,
        allowed_recipients={RECIPIENT},
        paused=False,
        expired=False,
    )
    values.update(overrides)
    return Policy(**values)


def test_valid_payment_is_allowed() -> None:
    result = evaluate_payment(
        base_policy(),
        PaymentRequest(recipient=RECIPIENT, amount=75),
    )
    assert result.allowed is True
    assert result.remaining_daily_limit == 125


def test_per_transaction_limit_is_enforced() -> None:
    result = evaluate_payment(
        base_policy(),
        PaymentRequest(recipient=RECIPIENT, amount=101),
    )
    assert result.allowed is False
    assert "per-transaction" in result.reason


def test_daily_limit_is_enforced() -> None:
    result = evaluate_payment(
        base_policy(daily_spent=225),
        PaymentRequest(recipient=RECIPIENT, amount=30),
    )
    assert result.allowed is False
    assert "daily" in result.reason


def test_allowlist_is_enforced() -> None:
    result = evaluate_payment(
        base_policy(),
        PaymentRequest(
            recipient="0x2222222222222222222222222222222222222222",
            amount=10,
        ),
    )
    assert result.allowed is False
    assert "allowlisted" in result.reason


def test_paused_vault_rejects_payment() -> None:
    result = evaluate_payment(
        base_policy(paused=True),
        PaymentRequest(recipient=RECIPIENT, amount=10),
    )
    assert result.allowed is False
    assert result.reason == "Vault is paused"


def test_expired_policy_rejects_payment() -> None:
    result = evaluate_payment(
        base_policy(expired=True),
        PaymentRequest(recipient=RECIPIENT, amount=10),
    )
    assert result.allowed is False
    assert result.reason == "Policy has expired"
