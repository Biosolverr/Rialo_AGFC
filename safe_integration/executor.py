import hashlib
import time
from policy_engine.engine import PolicyResult


class SafeExecutor:
    CHAIN_ID = 11155111  # Sepolia

    def build_tx(self, recipient: str, amount: float, policy: PolicyResult, intent_hash: str) -> dict:
        nonce = int(time.time())
        audit_input = f"{recipient}{amount}{nonce}{policy.threshold}{policy.time_delay}{intent_hash}"
        audit_hash = hashlib.sha256(audit_input.encode()).hexdigest()
        return {
            "to": recipient,
            "value_usd": amount,
            "required_signatures": policy.threshold,
            "execution_delay_sec": policy.time_delay,
            "max_single_tx": policy.max_single,
            "nonce": nonce,
            "audit_hash": f"0x{audit_hash}",
            "intent_hash": intent_hash,
            "chain_id": self.CHAIN_ID,
            "status": "pending_signatures",
        }
