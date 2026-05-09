# { "Depends": "py-genlayer:latest" }
# ─────────────────────────────────────────────────────────────────────────────
# TreasuryGovernance — Rialo Intelligent Contract
#
# This contract runs on the Rialo GenVM. It uses native webcall to call
# the off-chain AI agent API (FastAPI on Railway) and records verdicts
# on-chain. No oracle needed — Rialo handles the HTTP call natively.
#
# Deploy status: SIMULATION MODE
#   - Contract logic is complete and tested locally.
#   - Awaiting Rialo Devnet access to deploy.
#   - To activate: set RIALO_RPC_URL in .env and run deploy script.
#
# Rialo docs: https://docs.rialo.io
# ─────────────────────────────────────────────────────────────────────────────

from genlayer import *  # Rialo uses genlayer-compatible runtime
import json


AGENT_API_URL = "https://autonomous-financial-governance-system-agfs-production.up.railway.app"


class TreasuryGovernance(gl.Contract):
    owner: gl.Address
    amount_thresholds: gl.TreeMap[u256, u32]
    verdict_log: gl.DynArray[str]
    active_policies: gl.TreeMap[str, str]

    def __init__(self, admin: gl.Address):
        self.owner = admin
        self.amount_thresholds = gl.TreeMap[u256, u32]()
        self.verdict_log = gl.DynArray[str]()
        self.active_policies = gl.TreeMap[str, str]()
        self.amount_thresholds[1000] = 1
        self.amount_thresholds[10000] = 2
        self.amount_thresholds[999999999] = 3

    @gl.public.view
    def get_required_signers(self, amount: u256) -> u32:
        if amount < 1000:
            return 1
        elif amount < 10000:
            return 2
        return 3

    @gl.public.view
    def verify_policy(self, intent_hash: str) -> str:
        return self.active_policies.get(intent_hash, "NOT_FOUND")

    @gl.public.view
    def get_verdict_count(self) -> u32:
        return len(self.verdict_log)

    @gl.public.write
    def evaluate_intent(self, intent_hash: str, amount: u256, recipient: str, description: str):
        payload = json.dumps({
            "user_address": str(self.owner),
            "amount": float(amount),
            "recipient": recipient,
            "intent_text": description,
        })
        response_raw = gl.get_webpage(
            f"{AGENT_API_URL}/intent",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=payload,
        )
        response = json.loads(response_raw)
        decision = response.get("status", "rejected")
        confidence = int(response.get("consensus_confidence", 0) * 100)
        policy_hash = f"policy_{intent_hash[:8]}_{decision}"
        entry = f"{intent_hash}|{decision}|{confidence}|{policy_hash}"
        self.verdict_log.append(entry)
        self.active_policies[intent_hash] = policy_hash

    @gl.public.write
    def record_verdict(self, intent_hash: str, decision: str, confidence: u256, policy_hash: str):
        entry = f"{intent_hash}|{decision}|{confidence}|{policy_hash}"
        self.verdict_log.append(entry)
        self.active_policies[intent_hash] = policy_hash

    @gl.public.write
    def update_threshold(self, limit: u256, signers: u32):
        self.amount_thresholds[limit] = signers
        self.verdict_log.append(f"POLICY_UPDATE|{limit}|{signers}")
