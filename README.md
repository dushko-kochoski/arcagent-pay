# ArcAgent Pay

[![Backend Tests](https://github.com/dushko-kochoski/arcagent-pay/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/dushko-kochoski/arcagent-pay/actions/workflows/backend-tests.yml)

On-chain USDC spending controls for autonomous AI agents on Arc.

ArcAgent Pay lets an AI agent decide when it wants to request a payment while an `ArcAgentVault` smart contract remains the final authority over whether that payment is allowed.

> The AI controls the payment request. The smart contract controls the AI.

## What it does

An autonomous agent can propose a USDC payment based on a task or objective.

Before funds can move, the vault enforces:

- authorised Agent address
- maximum amount per transaction
- daily spending limit
- optional recipient allowlist
- policy expiry
- emergency pause
- owner-controlled withdrawals
- on-chain daily spend accounting

The backend cannot bypass these controls.

Even when the AI requests a payment that violates policy, the transaction is rejected by the smart contract.

## Architecture

```text
                  Objective / task
                        |
                        v
                 Local AI Agent
                 Qwen3 via Ollama
                        |
                 payment request
                        |
                        v
                  FastAPI backend
                        |
                        | signed Agent transaction
                        v
                ArcAgentVault.sol
                   Arc Testnet
                        |
          +-------------+-------------+
          |             |             |
       Allowlist    Tx / Daily      Expiry /
         check        limits         Pause
          |             |             |
          +-------------+-------------+
                        |
                  APPROVE / REJECT
                        |
                        v
                       USDC
```

The AI never receives the wallet private key.

Signing and blockchain execution are handled separately by the backend.

## Live Arc Testnet deployment

Network:

```text
Arc Testnet
Chain ID: 5042002
RPC: https://rpc.testnet.arc.io
```

USDC:

```text
0x3600000000000000000000000000000000000000
```

ArcAgentVault:

```text
0xC1E27633Bb3aC44B73f67305Bc2c360221aC8Bfa
```

Explorer:

```text
https://explorer.testnet.arc.io/address/0xC1E27633Bb3aC44B73f67305Bc2c360221aC8Bfa
```

## Testnet proof

ArcAgent Pay has executed real test-USDC payments through the deployed vault.

Example approved autonomous AI payment:

```text
Amount: 0.1 USDC

Transaction:
0xb07673f338392d53e7dcc6b538e055d9b42744b9bc69119133e5ca90f24e94c0
```

Explorer:

```text
https://explorer.testnet.arc.io/tx/0xb07673f338392d53e7dcc6b538e055d9b42744b9bc69119133e5ca90f24e94c0
```

The same AI agent was also allowed to request a `2.5 USDC` payment while the vault had a `2 USDC` per-transaction limit.

The AI requested the payment.

The smart contract rejected it.

No USDC transfer occurred.

This demonstrates the central security model: AI intent and financial authority are separated.

## AI decision layer

The current autonomous-agent implementation uses:

```text
Ollama
Qwen3 4B
```

This keeps the demo local and avoids requiring a paid AI API.

The model receives only:

- objective
- recipient
- requested USDC amount

It decides whether it wants to request the proposed payment.

It does **not**:

- receive private keys
- sign blockchain transactions
- control the vault
- modify the recipient
- modify the requested amount
- override smart-contract policy

The vault remains the final authority.

## Dashboard

The React/Vite dashboard displays live Arc state including:

- vault USDC balance
- amount spent today
- remaining daily allowance
- per-transaction limit
- daily limit
- authorised Agent
- owner
- allowlist state
- policy status
- policy expiry
- payment history
- approved transaction links
- rejected payment reasons

A manual payment interface is also available for testing the same vault enforcement path.

## Backend API

FastAPI routes include:

```text
GET  /health
GET  /vault/status
GET  /payments/history

POST /payments/evaluate
POST /payments/execute

POST /agent/decide
POST /agent/run
```

### Autonomous payment flow

`POST /agent/run`

```text
1. AI evaluates the objective.
2. AI decides whether to request payment.
3. Backend submits the request using the authorised Agent wallet.
4. ArcAgentVault validates the request on-chain.
5. Vault approves or rejects.
6. Approved payments transfer USDC.
7. Result is written to local payment history.
```

## Repository structure

```text
arcagent-pay/
|
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- schemas.py
|   |   `-- services/
|   |       |-- agent.py
|   |       |-- arc.py
|   |       |-- errors.py
|   |       |-- history.py
|   |       |-- orchestrator.py
|   |       `-- policy.py
|   |
|   |-- tests/
|   `-- requirements.txt
|
|-- contracts/
|   |-- contracts/
|   |   |-- ArcAgentVault.sol
|   |   `-- MockUSDC.sol
|   |-- scripts/
|   |-- test/
|   |-- hardhat.config.ts
|   `-- package.json
|
|-- frontend/
|   |-- src/
|   |-- public/
|   `-- package.json
|
|-- docs/
|   |-- MVP.md
|   `-- TESTNET_PROOF.md
|
|-- .env.example
|-- .gitignore
`-- README.md
```

## Smart contract

`ArcAgentVault.sol` is responsible for enforcing payment policy.

Important controls include:

```text
Agent authorization
Recipient allowlist
Per-transaction limit
Daily spending limit
Policy expiry
Pause / emergency controls
SafeERC20 transfers
Reentrancy protection
```

Policy enforcement happens on-chain rather than relying on the AI or backend to behave correctly.

## Backend setup

From:

```text
C:\arcagent-pay\backend
```

Create and activate a virtual environment:

```cmd
py -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```cmd
pip install -r requirements.txt
```

Run tests:

```cmd
pytest -q
```

Start the API:

```cmd
uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Local AI setup

Install Ollama and pull the model:

```cmd
ollama pull qwen3:4b
```

Example backend configuration:

```text
AGENT_DECISION_PROVIDER=ollama
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:4b
```

Ollama must be running when using the autonomous AI decision mode.

## Smart-contract setup

From:

```text
C:\arcagent-pay\contracts
```

Install dependencies:

```cmd
npm install
```

Compile:

```cmd
npx hardhat compile
```

Run contract tests:

```cmd
npx hardhat test
```

## Frontend setup

From:

```text
C:\arcagent-pay\frontend
```

Install dependencies:

```cmd
npm install
```

Start development server:

```cmd
npm run dev
```

The development frontend proxies `/api` requests to:

```text
http://127.0.0.1:8000
```

## Security model

ArcAgent Pay assumes that AI output is untrusted.

The AI is allowed to express intent.

It is not allowed to define financial authority.

The smart contract independently enforces the actual spending policy.

This means a compromised, manipulated or simply incorrect AI decision still cannot exceed the restrictions configured in the vault.

### Private keys

Never commit:

```text
.env
private keys
seed phrases
production credentials
```

Real environment files, local databases, build outputs and dependency directories are excluded from Git.

For deployment beyond testnet, use dedicated wallets containing only the minimum funds required.

## Current status

Completed:

- Solidity vault policy engine
- Hardhat contract tests
- Arc Testnet deployment
- test-USDC funding
- approved on-chain payments
- rejected over-limit payments
- FastAPI Arc integration
- signed Agent transaction execution
- SQLite payment history
- React/Vite dashboard
- autonomous agent orchestration
- local Qwen3/Ollama decision layer
- end-to-end autonomous USDC payment proof
- Git security cleanup

Next:

- final test and security review
- public GitHub repository
- deployment packaging
- demo recording
- carefully controlled Arc mainnet prototype
- Arc ecosystem / microgrant submission

## Disclaimer

ArcAgent Pay is currently a prototype.

The deployed contract and application should undergo additional security review before holding meaningful funds or being used in production.