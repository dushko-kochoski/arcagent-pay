from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class Policy(BaseModel):
    per_transaction_limit: int = Field(gt=0)
    daily_limit: int = Field(gt=0)
    daily_spent: int = Field(ge=0, default=0)
    allowlist_enabled: bool = True
    allowed_recipients: set[str] = Field(default_factory=set)
    paused: bool = False
    expired: bool = False


class PaymentRequest(BaseModel):
    recipient: str = Field(min_length=1)
    amount: int = Field(gt=0)


class EvaluatePaymentRequest(BaseModel):
    policy: Policy
    payment: PaymentRequest


class EvaluationResult(BaseModel):
    allowed: bool
    reason: str
    remaining_daily_limit: int = Field(ge=0)


class ExecutePaymentRequest(BaseModel):
    recipient: str = Field(min_length=1)
    amount_usdc: Decimal = Field(gt=0)


class ExecutePaymentResult(BaseModel):
    status: Literal["approved"]
    tx_hash: str
    explorer_url: str
    recipient: str
    amount_usdc: Decimal


class VaultStatus(BaseModel):
    network: str
    chain_id: int
    vault_address: str
    owner: str
    agent: str

    balance_usdc: float = Field(ge=0)
    per_transaction_limit_usdc: float = Field(ge=0)
    daily_limit_usdc: float = Field(ge=0)
    spent_today_usdc: float = Field(ge=0)
    remaining_today_usdc: float = Field(ge=0)

    paused: bool
    allowlist_enabled: bool
    policy_expires_at: int = Field(ge=0)


class PaymentHistoryItem(BaseModel):
    id: int
    created_at: datetime
    status: Literal["approved", "rejected"]
    recipient: str
    amount_usdc: Decimal

    tx_hash: str | None = None
    explorer_url: str | None = None
    reason: str | None = None


class ErrorResponse(BaseModel):
    detail: str
class AgentDecisionRequest(BaseModel):
    objective: str = Field(min_length=1)
    recipient: str = Field(min_length=1)
    requested_amount_usdc: Decimal = Field(gt=0)


class AgentDecision(BaseModel):
    decision: Literal["pay", "reject"]
    recipient: str
    amount_usdc: Decimal | None = None
    reason: str
class AgentRunResult(BaseModel):
    agent_decision: Literal["pay", "reject"]
    agent_reason: str

    vault_result: Literal[
        "approved",
        "rejected",
        "not_requested",
    ]

    recipient: str
    amount_usdc: Decimal | None = None

    tx_hash: str | None = None
    explorer_url: str | None = None
    detail: str | None = None