import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import hashlib
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from agents.risk_agent import RiskAgent
from agents.fraud_agent import FraudAgent
from agents.compliance_agent import ComplianceAgent
from consensus.engine import OptimisticConsensus
from policy_engine.engine import PolicyEngine
from safe_integration.executor import SafeExecutor
from core.treasury_governance import TreasuryGovernance

load_dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(load_dotenv_path):
    from dotenv import load_dotenv
    load_dotenv(load_dotenv_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Таймаут на каждый LLM-агент в секундах
AGENT_TIMEOUT_SEC = int(os.getenv("AGENT_TIMEOUT_SEC", "30"))

# Fallback-ответ если агент завис или упал
AGENT_FALLBACK = {"score": 1.0, "approve": False, "flags": ["timeout"], "reasoning": "agent timeout"}

app = FastAPI(
    title="Autonomous Treasury — Rialo Edition",
    description="Multi-agent financial governance system with Rialo Intelligent Contract layer",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Пул потоков для запуска синхронных агентов параллельно
_executor = ThreadPoolExecutor(max_workers=3)


class IntentRequest(BaseModel):
    user_address: str
    amount: float
    recipient: str
    intent_text: str


class AgentDecision(BaseModel):
    agent: str
    approve: bool
    score: float
    flags: List[str]
    reasoning: str


class IntentResponse(BaseModel):
    status: str
    risk_score: float
    approved: bool
    reason: str
    agents: List[AgentDecision]
    consensus_confidence: float
    policy: Optional[dict] = None
    safe_tx: Optional[dict] = None
    tx_hash: Optional[str] = None
    rialo_mode: str = "simulation"


def _run_agent(agent_cls, intent_data: dict) -> dict:
    """Запускает агент синхронно — вызывается из ThreadPoolExecutor."""
    try:
        return agent_cls().evaluate(intent_data)
    except Exception as e:
        logger.warning(f"Agent {agent_cls.__name__} error: {e}")
        return {**AGENT_FALLBACK, "reasoning": str(e)}


async def _call_agent(agent_cls, intent_data: dict) -> dict:
    """Запускает агент в отдельном потоке с таймаутом AGENT_TIMEOUT_SEC."""
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(_executor, _run_agent, agent_cls, intent_data),
            timeout=AGENT_TIMEOUT_SEC,
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Agent {agent_cls.__name__} timed out after {AGENT_TIMEOUT_SEC}s")
        return {**AGENT_FALLBACK, "reasoning": f"timeout after {AGENT_TIMEOUT_SEC}s"}


@app.get("/")
def root():
    rialo_connected = bool(os.getenv("RIALO_RPC_URL"))
    return {
        "name": "Autonomous Treasury — Rialo Edition",
        "version": "2.0.0",
        "status": "running",
        "rialo_mode": "devnet" if rialo_connected else "simulation",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    rialo_connected = bool(os.getenv("RIALO_RPC_URL"))
    return {
        "status": "ok",
        "agents": ["RiskAI", "FraudDetect", "ComplianceGuard"],
        "consensus": "OptimisticConsensus (Rialo-compatible)",
        "rialo_node": "connected" if rialo_connected else "simulation",
        "contract": "contracts/treasury_governance.py",
    }


@app.post("/intent", response_model=IntentResponse)
async def process_intent(req: IntentRequest):
    logger.info(f"Intent: amount={req.amount}, recipient={req.recipient}")

    intent_data = {
        "amount": req.amount,
        "recipient": req.recipient,
        "text": req.intent_text,
        "user_address": req.user_address,
    }

    # Все три агента запускаются параллельно с таймаутом — не висят вечно
    risk_result, fraud_result, compliance_result = await asyncio.gather(
        _call_agent(RiskAgent, intent_data),
        _call_agent(FraudAgent, intent_data),
        _call_agent(ComplianceAgent, intent_data),
    )

    agent_decisions = [
        AgentDecision(
            agent="RiskAI",
            approve=bool(risk_result.get("approve", False)),
            score=float(risk_result.get("score", 1.0)),
            flags=risk_result.get("flags", []),
            reasoning=risk_result.get("reasoning", ""),
        ),
        AgentDecision(
            agent="FraudDetect",
            approve=bool(fraud_result.get("approve", False)),
            score=float(fraud_result.get("score", 1.0)),
            flags=fraud_result.get("flags", []),
            reasoning=fraud_result.get("reasoning", ""),
        ),
        AgentDecision(
            agent="ComplianceGuard",
            approve=bool(compliance_result.get("approve", False)),
            score=float(compliance_result.get("score", 1.0)),
            flags=compliance_result.get("flags", []),
            reasoning=compliance_result.get("reasoning", ""),
        ),
    ]

    votes = [d.approve for d in agent_decisions]
    avg_risk = sum(d.score for d in agent_decisions) / len(agent_decisions)

    consensus = OptimisticConsensus()
    consensus_result = consensus.run(votes, avg_risk)
    approved = consensus_result.decision == "approve"

    policy_engine = PolicyEngine()
    policy = policy_engine.generate(req.amount, avg_risk, consensus_result.margin)

    intent_hash = hashlib.sha256(
        f"{req.user_address}{req.amount}{req.recipient}{req.intent_text}".encode()
    ).hexdigest()

    safe_tx = None
    tx_hash = None
    rialo_mode = "simulation"

    voted_yes = sum(1 for v in votes if v)
    reason = (
        f"{voted_yes}/{len(votes)} agents approved. "
        f"Confidence: {consensus_result.confidence:.0%}. "
        f"Risk: {risk_result.get('reasoning', '')}. "
        f"Fraud: {fraud_result.get('reasoning', '')}. "
        f"Compliance: {compliance_result.get('reasoning', '')}."
    )

    if approved:
        executor = SafeExecutor()
        safe_tx = executor.build_tx(req.recipient, req.amount, policy, intent_hash)
        tx_hash = safe_tx["audit_hash"]
        treasury = TreasuryGovernance()
        tx_result = treasury.execute_transfer(req.recipient, req.amount, req.intent_text)
        rialo_mode = tx_result.get("mode", "simulation")
        reason += f" Safe TX built. Signers required: {policy.threshold}."
        logger.info(f"TX approved: {tx_hash}, mode: {rialo_mode}")
    else:
        logger.info(f"TX rejected: {intent_hash}")

    return IntentResponse(
        status="approved" if approved else "rejected",
        risk_score=avg_risk,
        approved=approved,
        reason=reason,
        agents=agent_decisions,
        consensus_confidence=float(consensus_result.confidence),
        policy=policy.model_dump(),
        safe_tx=safe_tx,
        tx_hash=tx_hash,
        rialo_mode=rialo_mode,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Autonomous Treasury (Rialo Edition) on port {port}")
    uvicorn.run("orchestrator.main:app", host="0.0.0.0", port=port, reload=False)
