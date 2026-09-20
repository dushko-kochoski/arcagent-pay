import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"
DATABASE_PATH = DATA_DIR / "arcagent_pay.db"


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def init_history_db() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS payment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                recipient TEXT NOT NULL,
                amount_usdc TEXT NOT NULL,
                tx_hash TEXT,
                explorer_url TEXT,
                reason TEXT
            )
            """
        )

        connection.commit()


def record_payment(
    *,
    status: str,
    recipient: str,
    amount_usdc: Decimal,
    tx_hash: str | None = None,
    explorer_url: str | None = None,
    reason: str | None = None,
) -> int:
    created_at = datetime.now(timezone.utc).isoformat()

    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO payment_history (
                created_at,
                status,
                recipient,
                amount_usdc,
                tx_hash,
                explorer_url,
                reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                status,
                recipient,
                str(amount_usdc),
                tx_hash,
                explorer_url,
                reason,
            ),
        )

        connection.commit()

        return int(cursor.lastrowid)


def list_payments(limit: int = 50) -> list[dict]:
    if limit < 1:
        raise ValueError("limit must be at least 1")

    if limit > 500:
        raise ValueError("limit cannot exceed 500")

    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                created_at,
                status,
                recipient,
                amount_usdc,
                tx_hash,
                explorer_url,
                reason
            FROM payment_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


init_history_db()