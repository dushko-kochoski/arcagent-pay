# ArcAgent Pay

Programmable USDC spending controls for autonomous AI agents on Arc.

## Goal

ArcAgent Pay gives an AI agent permission to make USDC payments while a smart contract enforces hard limits on-chain:

- approved agent address
- per-transaction limit
- daily spending limit
- optional recipient allowlist
- policy expiry
- pause switch
- owner-controlled emergency withdrawal

The AI/backend can decide **what it wants to pay**, but it cannot bypass the smart-contract policy.

## MVP architecture

```text
User / Owner
    |
    | configures policy + deposits USDC
    v
ArcAgentVault.sol  <---- Arc
    ^
    |
AI Agent / FastAPI
    |
    +-- evaluates payment request
    +-- reads on-chain policy
    +-- submits only permitted payment transactions
```

## Repository

```text
arcagent-pay/
├─ contracts/
│  ├─ contracts/ArcAgentVault.sol
│  ├─ test/ArcAgentVault.ts
│  ├─ hardhat.config.ts
│  ├─ package.json
│  └─ tsconfig.json
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ schemas.py
│  │  └─ services/policy.py
│  ├─ tests/test_policy.py
│  └─ requirements.txt
├─ .env.example
└─ README.md
```

## Day 1

1. Create the repository.
2. Run the backend tests.
3. Install the contract dependencies.
4. Compile and test the Solidity contract.
5. Create a fresh development wallet for Arc testnet.
6. Add Arc testnet RPC/faucet values from the current official Arc/Circle docs.
7. Deploy the contract to testnet only after local tests pass.

## Backend

Windows PowerShell:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

Open:

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

## Contracts

```powershell
cd contracts
npm install
npx hardhat compile
npx hardhat test
```

Do not put wallet private keys in Git or source files.

## MVP milestones

### Phase 1 — Policy engine
- smart-contract spending controls
- local tests
- FastAPI mirror of policy checks

### Phase 2 — Arc testnet
- deploy vault
- deposit test USDC
- execute approved payment
- demonstrate rejected over-limit payment

### Phase 3 — Demo app
- wallet connect
- owner policy configuration
- agent payment request
- transaction history

### Phase 4 — Arc mainnet
- audit the final contract
- deploy with a very small amount of USDC
- publish contract address and Arc explorer links
- record demo
- submit to Arc Microgrants

## Security model

The first MVP intentionally keeps the policy simple. The smart contract is the final authority.

The backend must never be trusted to enforce limits by itself. If the backend is compromised, the on-chain per-transaction limit, daily limit, allowlist, expiry and pause state still apply.

For the grant demo, use a dedicated wallet with a very small balance. Never reuse a wallet containing meaningful funds.
