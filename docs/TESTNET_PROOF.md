# ArcAgent Pay — Arc Testnet Proof

## Network

Arc Testnet

Chain ID: 5042002

## ArcAgentVault

Contract:

0xC1E27633Bb3aC44B73f67305Bc2c360221aC8Bfa

## Roles

Owner:

0x0804BeC55DdF4Da0613dFf53740F9Bd131ef8411

Agent:

0x9E4E9026Cc12685525e5FD4c80E87177EaA9d995

## Policy

Per-transaction limit: 2 USDC

Daily limit: 5 USDC

Recipient allowlist: enabled

## Test

Initial vault balance:

3 USDC

### Allowed payment

Agent requested:

1 USDC

Result:

SUCCESS

Transaction:

0x919f4cec954ab96b384e5c1fd0bf02652fbe22cfb7b16624de444a23a1118be1

Vault balance after:

2 USDC

### Forbidden payment

Agent requested:

2.5 USDC

Result:

REJECTED

Reason:

Payment exceeded the smart contract's 2 USDC per-transaction limit.

No transaction was executed and vault funds remained protected.

## Result

ArcAgent Pay successfully demonstrated delegated USDC spending where an
autonomous agent can execute permitted payments but cannot override
owner-defined on-chain spending policies.