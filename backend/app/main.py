from fastapi import FastAPI, HTTPException, Query

from app.schemas import (
    AgentDecision,
    AgentDecisionRequest,
    AgentRunResult,
    ErrorResponse,
    EvaluatePaymentRequest,
    EvaluationResult,
    ExecutePaymentRequest,
    ExecutePaymentResult,
    PaymentHistoryItem,
    VaultStatus,
)
from app.services.agent import decide_payment

from app.services.arc import (
    execute_agent_payment,
    get_vault_status,
)

from app.services.orchestrator import run_agent_payment

from app.services.errors import (
    ArcConfigurationError,
    ArcConnectionError,
    PaymentExecutionError,
    PaymentPolicyRejected,
)
from app.services.history import (
    list_payments,
    record_payment,
)
from app.services.policy import evaluate_payment


app = FastAPI(
    title="ArcAgent Pay API",
    version="0.3.0",
    description=(
        "Programmable USDC spending controls "
        "for autonomous agents on Arc."
    ),
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "ArcAgent Pay",
        "status": "online",
        "network": "Arc Testnet",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/vault/status",
    response_model=VaultStatus,
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Arc service configuration error",
        },
        503: {
            "model": ErrorResponse,
            "description": "Arc Testnet unavailable",
        },
    },
)
def vault_status() -> VaultStatus:
    try:
        result = get_vault_status()
        return VaultStatus(**result)

    except ArcConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except ArcConfigurationError as exc:
        raise HTTPException(
            status_code=500,
            detail="Arc service configuration error",
        ) from exc
@app.post(
    "/agent/decide",
    response_model=AgentDecision,
)
def agent_decide(
    request: AgentDecisionRequest,
) -> AgentDecision:
    return decide_payment(request)


@app.post(
    "/agent/run",
    response_model=AgentRunResult,
)
def agent_run(
    request: AgentDecisionRequest,
) -> AgentRunResult:
    result = run_agent_payment(request)

    if result.vault_result == "approved":
        record_payment(
            status="approved",
            recipient=result.recipient,
            amount_usdc=result.amount_usdc,
            tx_hash=result.tx_hash,
            explorer_url=result.explorer_url,
        )

    elif result.vault_result == "rejected":
        record_payment(
            status="rejected",
            recipient=result.recipient,
            amount_usdc=result.amount_usdc,
            reason=result.detail,
        )

    return result


@app.post(
    "/payments/evaluate",
    response_model=EvaluationResult,
)
def evaluate(
    request: EvaluatePaymentRequest,
) -> EvaluationResult:
    return evaluate_payment(
        request.policy,
        request.payment,
    )

@app.get(
    "/payments/history",
    response_model=list[PaymentHistoryItem],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid history query",
        },
        503: {
            "model": ErrorResponse,
            "description": "Payment history unavailable",
        },
    },
)
def payment_history(
    limit: int = Query(default=50, ge=1, le=500),
) -> list[PaymentHistoryItem]:
    try:
        rows = list_payments(limit=limit)

        return [
            PaymentHistoryItem(**row)
            for row in rows
        ]

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not read payment history",
        ) from exc


@app.post(
    "/payments/execute",
    response_model=ExecutePaymentResult,
    responses={
        400: {
            "model": ErrorResponse,
            "description": (
                "Invalid payment or rejected by on-chain policy"
            ),
        },
        500: {
            "model": ErrorResponse,
            "description": "Arc service configuration error",
        },
        502: {
            "model": ErrorResponse,
            "description": "Payment execution failed",
        },
        503: {
            "model": ErrorResponse,
            "description": "Arc Testnet unavailable",
        },
    },
)
def execute_payment(
    request: ExecutePaymentRequest,
) -> ExecutePaymentResult:
    try:
        result = execute_agent_payment(
            recipient=request.recipient,
            amount_usdc=request.amount_usdc,
        )

        record_payment(
            status="approved",
            recipient=result["recipient"],
            amount_usdc=request.amount_usdc,
            tx_hash=result["tx_hash"],
            explorer_url=result["explorer_url"],
        )

        return ExecutePaymentResult(**result)

    except PaymentPolicyRejected as exc:
        record_payment(
            status="rejected",
            recipient=request.recipient,
            amount_usdc=request.amount_usdc,
            reason=str(exc),
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        record_payment(
            status="rejected",
            recipient=request.recipient,
            amount_usdc=request.amount_usdc,
            reason=str(exc),
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except ArcConfigurationError as exc:
        raise HTTPException(
            status_code=500,
            detail="Arc service configuration error",
        ) from exc

    except ArcConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except PaymentExecutionError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc