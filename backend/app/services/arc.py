import json
import os
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import ContractLogicError

from app.services.errors import (
    ArcConfigurationError,
    ArcConnectionError,
    PaymentExecutionError,
    PaymentPolicyRejected,
)


load_dotenv()


ARC_RPC_URL = os.environ["ARC_RPC_URL"]
ARC_CHAIN_ID = int(os.getenv("ARC_CHAIN_ID", "5042002"))

ARC_USDC_ADDRESS = Web3.to_checksum_address(
    os.environ["ARC_USDC_ADDRESS"]
)

ARC_AGENT_VAULT_ADDRESS = Web3.to_checksum_address(
    os.environ["ARC_AGENT_VAULT_ADDRESS"]
)

ARC_EXPLORER_URL = "https://explorer.testnet.arc.io"

USDC_DECIMALS = 6
USDC_SCALE = 10**USDC_DECIMALS


w3 = Web3(Web3.HTTPProvider(ARC_RPC_URL))


def _load_vault_abi() -> list:
    project_root = Path(__file__).resolve().parents[3]

    artifact_path = (
        project_root
        / "contracts"
        / "artifacts"
        / "contracts"
        / "ArcAgentVault.sol"
        / "ArcAgentVault.json"
    )

    if not artifact_path.exists():
        raise ArcConfigurationError(
            f"ArcAgentVault artifact not found: {artifact_path}"
        )

    try:
        with artifact_path.open("r", encoding="utf-8") as file:
            artifact = json.load(file)

        return artifact["abi"]

    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise ArcConfigurationError(
            "Could not load ArcAgentVault ABI"
        ) from exc


VAULT_ABI = _load_vault_abi()


vault = w3.eth.contract(
    address=ARC_AGENT_VAULT_ADDRESS,
    abi=VAULT_ABI,
)


USDC_ABI = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "account",
                "type": "address",
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


usdc = w3.eth.contract(
    address=ARC_USDC_ADDRESS,
    abi=USDC_ABI,
)


def usdc_to_float(value: int) -> float:
    return value / USDC_SCALE


def _ensure_arc_connection() -> int:
    try:
        connected = w3.is_connected()
    except Exception as exc:
        raise ArcConnectionError(
            "Could not connect to Arc Testnet"
        ) from exc

    if not connected:
        raise ArcConnectionError(
            "Could not connect to Arc Testnet"
        )

    try:
        chain_id = w3.eth.chain_id
    except Exception as exc:
        raise ArcConnectionError(
            "Could not read Arc Testnet chain ID"
        ) from exc

    if chain_id != ARC_CHAIN_ID:
        raise ArcConnectionError(
            f"Wrong chain. Expected {ARC_CHAIN_ID}, got {chain_id}"
        )

    return chain_id


def _usdc_to_raw(amount_usdc: Decimal) -> int:
    try:
        amount = Decimal(str(amount_usdc))
    except Exception as exc:
        raise ValueError(
            "Invalid USDC amount"
        ) from exc

    if amount <= 0:
        raise ValueError(
            "USDC amount must be greater than zero"
        )

    raw_amount = amount * USDC_SCALE

    if raw_amount != raw_amount.to_integral_value():
        raise ValueError(
            "USDC amount cannot have more than 6 decimal places"
        )

    return int(raw_amount)


def _get_agent_account():
    private_key = os.getenv("AGENT_PRIVATE_KEY")

    if not private_key:
        raise ArcConfigurationError(
            "AGENT_PRIVATE_KEY is not configured"
        )

    private_key = private_key.strip()

    try:
        account = w3.eth.account.from_key(private_key)
    except Exception as exc:
        raise ArcConfigurationError(
            "AGENT_PRIVATE_KEY is invalid"
        ) from exc

    return account, private_key


def get_vault_status() -> dict:
    chain_id = _ensure_arc_connection()

    try:
        balance = usdc.functions.balanceOf(
            ARC_AGENT_VAULT_ADDRESS
        ).call()

        owner = vault.functions.owner().call()
        agent = vault.functions.agent().call()

        per_transaction_limit = (
            vault.functions.perTransactionLimit().call()
        )

        daily_limit = vault.functions.dailyLimit().call()
        daily_spent = vault.functions.dailySpent().call()

        remaining_daily_limit = (
            vault.functions.remainingDailyLimit().call()
        )

        paused = vault.functions.paused().call()

        allowlist_enabled = (
            vault.functions.allowlistEnabled().call()
        )

        policy_expires_at = (
            vault.functions.policyExpiresAt().call()
        )

    except Exception as exc:
        raise ArcConnectionError(
            "Could not read ArcAgentVault state"
        ) from exc

    return {
        "network": "Arc Testnet",
        "chain_id": chain_id,
        "vault_address": ARC_AGENT_VAULT_ADDRESS,
        "owner": owner,
        "agent": agent,
        "balance_usdc": usdc_to_float(balance),
        "per_transaction_limit_usdc": usdc_to_float(
            per_transaction_limit
        ),
        "daily_limit_usdc": usdc_to_float(
            daily_limit
        ),
        "spent_today_usdc": usdc_to_float(
            daily_spent
        ),
        "remaining_today_usdc": usdc_to_float(
            remaining_daily_limit
        ),
        "paused": paused,
        "allowlist_enabled": allowlist_enabled,
        "policy_expires_at": policy_expires_at,
    }


def execute_agent_payment(
    recipient: str,
    amount_usdc: Decimal,
) -> dict:
    chain_id = _ensure_arc_connection()

    try:
        recipient_address = Web3.to_checksum_address(
            recipient
        )
    except ValueError as exc:
        raise ValueError(
            "Invalid recipient address"
        ) from exc

    amount_raw = _usdc_to_raw(amount_usdc)

    agent_account, private_key = _get_agent_account()

    local_agent_address = Web3.to_checksum_address(
        agent_account.address
    )

    try:
        vault_agent_address = Web3.to_checksum_address(
            vault.functions.agent().call()
        )
    except Exception as exc:
        raise ArcConnectionError(
            "Could not read authorised vault Agent"
        ) from exc

    if local_agent_address != vault_agent_address:
        raise ArcConfigurationError(
            "Configured Agent signer does not match "
            "the Agent authorised by the vault"
        )

    #
    # Preflight the exact payment against the smart contract.
    #
    # No transaction is sent when validatePayment() rejects it.
    #
    try:
        validation_result = vault.functions.validatePayment(
            recipient_address,
            amount_raw,
        ).call(
            {
                "from": local_agent_address,
            }
        )

    except ContractLogicError as exc:
        raise PaymentPolicyRejected(
            "Payment rejected by on-chain policy"
        ) from exc

    except Exception as exc:
        raise ArcConnectionError(
            "Could not validate payment against ArcAgentVault"
        ) from exc

    if isinstance(validation_result, (tuple, list)):
        payment_allowed = (
            bool(validation_result[0])
            if validation_result
            else False
        )
    else:
        payment_allowed = bool(validation_result)

    if not payment_allowed:
        raise PaymentPolicyRejected(
            "Payment rejected by on-chain policy"
        )

    payment_function = vault.functions.executePayment(
        recipient_address,
        amount_raw,
    )

    #
    # Gas estimation performs another contract simulation before
    # anything is signed or broadcast.
    #
    try:
        estimated_gas = payment_function.estimate_gas(
            {
                "from": local_agent_address,
            }
        )

    except ContractLogicError as exc:
        raise PaymentPolicyRejected(
            "Payment rejected by on-chain policy"
        ) from exc

    except Exception as exc:
        raise PaymentExecutionError(
            "Could not estimate payment transaction gas"
        ) from exc

    gas_limit = int(estimated_gas * 1.20)

    try:
        nonce = w3.eth.get_transaction_count(
            local_agent_address,
            "pending",
        )

        transaction = payment_function.build_transaction(
            {
                "from": local_agent_address,
                "chainId": chain_id,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": w3.eth.gas_price,
            }
        )

        signed_transaction = (
            w3.eth.account.sign_transaction(
                transaction,
                private_key,
            )
        )

        tx_hash = w3.eth.send_raw_transaction(
            signed_transaction.raw_transaction
        )

    except Exception as exc:
        raise PaymentExecutionError(
            "Could not broadcast payment transaction"
        ) from exc

    tx_hash_hex = w3.to_hex(tx_hash)

    try:
        receipt = w3.eth.wait_for_transaction_receipt(
            tx_hash,
            timeout=120,
        )
    except Exception as exc:
        raise PaymentExecutionError(
            f"Payment transaction was broadcast but "
            f"receipt could not be confirmed: {tx_hash_hex}"
        ) from exc

    if receipt.status != 1:
        raise PaymentExecutionError(
            f"Payment transaction failed on-chain: "
            f"{tx_hash_hex}"
        )

    return {
        "status": "approved",
        "tx_hash": tx_hash_hex,
        "explorer_url": (
            f"{ARC_EXPLORER_URL}/tx/{tx_hash_hex}"
        ),
        "recipient": recipient_address,
        "amount_usdc": float(
            Decimal(str(amount_usdc))
        ),
    }