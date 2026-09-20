# ArcAgent Pay MVP

## Core user story

As a wallet owner, I want to fund a vault with USDC and authorise an AI agent to make small payments without giving that agent unrestricted access to my funds.

## Demo story

1. Owner deploys ArcAgentVault.
2. Owner deposits a small amount of USDC.
3. Owner sets:
   - agent wallet
   - $10 per-transaction limit
   - $25 daily limit
   - one allowlisted merchant
4. Agent requests a $5 payment.
5. Payment succeeds.
6. Agent requests a $15 payment.
7. Contract rejects it because it exceeds the per-transaction limit.
8. Owner pauses the vault.
9. Further agent payment is rejected.

This gives the grant reviewer a simple, visible proof that the AI agent has useful autonomy without unrestricted custody.

## Not in v0.1

- arbitrary DeFi trading
- cross-chain routing
- complex subscription logic
- multi-agent governance
- custody of meaningful user funds
- upgradeable contracts

Those can be future milestones after the microgrant MVP works.
