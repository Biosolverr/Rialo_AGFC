# Autonomous Treasury — Rialo Edition

Multi-agent AI governance system for autonomous financial transactions,
built for the **Rialo** blockchain ecosystem.

## Architecture

User Intent → FastAPI
→ AI Agents (RiskAI + FraudDetect + ComplianceGuard)
→ OptimisticConsensus (Rialo-compatible)
→ PolicyEngine (deterministic rules)
→ SafeExecutor (Safe-compatible TX)
→ TreasuryGovernance (Rialo Intelligent Contract)

## Rialo Integration

The core innovation is `contracts/treasury_governance.py` — a Rialo
Intelligent Contract that uses **native webcall** to call the off-chain
AI agent API directly from inside the contract. No oracle required.

```python
# Inside the Rialo contract — HTTP call from on-chain
response_raw = gl.get_webpage(
    f"{AGENT_API_URL}/intent",
    method="POST",
    body=payload,
)
```

**Current status:** Simulation mode. Awaiting Rialo Devnet access.
**To activate:** Set `RIALO_RPC_URL` in `.env` and deploy the contract.

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| AI Agents | Groq LLM (llama-3.3-70b) |
| Consensus | Optimistic Democracy (Rialo-compatible) |
| Contract | Rialo Intelligent Contract |
| Execution | Safe-compatible TX builder |
| Deploy | Railway (backend) + Netlify (frontend) |

## Quick Start

```bash
git clone https://github.com/youruser/autonomous-treasury-rialo
cd autonomous-treasury-rialo
cp .env.example .env
# Add your GROQ_API_KEY to .env
pip install -r requirements.txt
uvicorn orchestrator.main:app --reload
```

## Run Tests

```bash
pytest tests/ -v
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key for LLM agents |
| `RIALO_RPC_URL` | ⬜ | Rialo Devnet RPC (simulation if empty) |
| `AGENT_API_URL` | ⬜ | Public URL of this API (used by Rialo contract webcall) |
| `TREASURY_ADDRESS` | ⬜ | Treasury wallet address |

## Deployed

- **Backend:** Railway
- **Frontend:** Netlify
- **Contract:** Simulation mode → Rialo Devnet (pending access)
