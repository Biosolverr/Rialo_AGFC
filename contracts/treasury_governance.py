# { "Depends": "py-genlayer:latest" }
# Rialo GenVM-compatible Intelligent Contract
# Uses GenMap/GenArray instead of gl.TreeMap/gl.DynArray
# to avoid TypeError: function object is not subscriptable

import json

try:
    from genlayer import *
    _GENLAYER = True
except ImportError:
    _GENLAYER = False

from core.genvm import (
    GenMap,
    GenArray,
    GenVM,
    sign_policy,
    verify_policy_signature,
    ReplayProtection,
)

AGENT_API_URL = "https://autonomous-financial-governance-system-agfs-production.up.railway.app"


class TreasuryGovernance:
    """
    Rialo Intelligent Contract — Treasury Governance.

    State primitives use GenMap/GenArray for GenVM compatibility.
    When deployed on Rialo node these map to on-chain storage.
    When running locally they use in-memory Python containers.
    """

    def __init__(self, admin: str = "0xAdmin"):
        self.owner = admin
        self._genvm = GenVM()

        # GenVM-safe state primitives (no generics, no subscript errors)
        self.amount_thresholds: GenMap = GenMap()
        self.verdict_log: GenArray = GenArray()
        self.active_policies: GenMap = GenMap()
        self._replay = ReplayProtection()

        # Default thresholds
        self.amount_thresholds[1000] = 1
        self.amount_thresholds[10000] = 2
        self.amount_thresholds[999999999] = 3

    # ─────────────────────────────
    # READ
    # ─────────────────────────────

    def get_required_signers(self, amount: int) -> int:
        amount = int(amount)
        if amount < 1000:
            return 1
        elif amount < 10000:
            return 2
        return 3

    def verify_policy(self, intent_hash: str) -> str:
        record = self.active_policies.get(intent_hash)
        if record is None:
            return "NOT_FOUND"
        return record.get("policy_hash", "NOT_FOUND")

    def verify_policy_integrity(self, intent_hash: str) -> bool:
        """Verifies the stored policy signature is intact (not tampered)."""
        record = self.active_policies.get(intent_hash)
        if record is None:
            return False
        policy = record.get("policy", {})
        signature = record.get("signature", "")
        return verify_policy_signature(policy, signature)

    def get_verdict_count(self) -> int:
        return len(self.verdict_log)

    # ─────────────────────────────
    # WRITE
    # ─────────────────────────────

    def evaluate_intent(
        self,
        intent_hash: str,
        amount: int,
        recipient: str,
        description: str,
        nonce: int = 0,
    ):
        # Replay protection
        self._replay.check_and_register(intent_hash, nonce)

        payload = json.dumps({
            "user_address": str(self.owner),
            "amount": int(amount),
            "recipient": recipient,
            "intent_text": description,
        })

        if _GENLAYER:
            response_raw = gl.get_webpage(
                f"{AGENT_API_URL}/intent",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=payload,
            )
            response = json.loads(response_raw)
        else:
            response = {"status": "approved", "consensus_confidence": 0.8}

        decision = response.get("status", "rejected")
        confidence = int(response.get("consensus_confidence", 0) * 100)
        policy_hash = f"policy_{intent_hash[:8]}_{decision}"

        policy_dict = {"hash": policy_hash, "decision": decision, "confidence": confidence}
        signature = sign_policy(policy_dict)

        entry = f"{intent_hash}|{decision}|{confidence}|{policy_hash}"
        self.verdict_log.append(entry)
        self.active_policies[intent_hash] = {
            "policy_hash": policy_hash,
            "policy": policy_dict,
            "signature": signature,
        }

    def record_verdict(
        self,
        intent_hash: str,
        decision: str,
        confidence: int,
        policy_hash: str,
    ):
        policy_dict = {"hash": policy_hash, "decision": decision, "confidence": int(confidence)}
        signature = sign_policy(policy_dict)

        entry = f"{intent_hash}|{decision}|{confidence}|{policy_hash}"
        self.verdict_log.append(entry)
        self.active_policies[intent_hash] = {
            "policy_hash": policy_hash,
            "policy": policy_dict,
            "signature": signature,
        }

    def update_threshold(self, limit: int, signers: int):
        self.amount_thresholds[int(limit)] = int(signers)
        self.verdict_log.append(f"POLICY_UPDATE|{limit}|{signers}")
