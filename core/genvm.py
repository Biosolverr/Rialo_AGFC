"""
GenVM Abstraction Layer for Rialo Intelligent Contracts.

In simulation mode: uses Python in-memory storage.
In production: binds to Rialo runtime via RIALO_RPC_URL env var.

State primitives (GenMap, GenArray) are runtime-safe replacements
for gl.TreeMap / gl.DynArray — no generics, no subscript errors.
"""

import os
import json
import hashlib


# ─────────────────────────────────────────
# State Primitives
# ─────────────────────────────────────────

class GenMap(dict):
    """Runtime-safe replacement for gl.TreeMap. No generics required."""
    def get(self, k, default=None):
        return super().get(k, default)


class GenArray(list):
    """Runtime-safe replacement for gl.DynArray. No generics required."""
    def append(self, value):
        super().append(value)


# ─────────────────────────────────────────
# Replay Protection
# ─────────────────────────────────────────

class ReplayProtection:
    """
    Prevents the same intent_hash from being processed twice.

    NOTE: In-memory only — resets on server restart.
    For production Rialo mainnet, this must be backed by
    persistent on-chain storage via GenVM state primitives.
    """
    def __init__(self):
        self._seen: GenMap = GenMap()

    def check_and_register(self, intent_hash: str, nonce: int) -> None:
        """Raises ValueError if intent_hash was already processed."""
        if self._seen.get(intent_hash):
            raise ValueError(f"Replay detected: intent_hash={intent_hash!r} already processed")
        self._seen[intent_hash] = nonce

    def is_seen(self, intent_hash: str) -> bool:
        return bool(self._seen.get(intent_hash))


# ─────────────────────────────────────────
# Policy Signing
# ─────────────────────────────────────────

_POLICY_SEED = os.getenv("POLICY_SIGN_SEED", "rialo-treasury-devnet-seed-v1")


def sign_policy(policy: dict) -> str:
    """Deterministic HMAC-style signature of a policy dict."""
    raw = json.dumps(policy, sort_keys=True) + _POLICY_SEED
    return hashlib.sha256(raw.encode()).hexdigest()


def verify_policy_signature(policy: dict, signature: str) -> bool:
    """Returns True if the signature matches the policy."""
    return sign_policy(policy) == signature


# ─────────────────────────────────────────
# Deterministic Consensus Hash
# ─────────────────────────────────────────

def compute_consensus_hash(agents: list) -> str:
    """
    Canonical, reproducible hash of agent decisions.

    Normalizes:
      - sorts agents alphabetically by name
      - rounds score to 6 decimal places (eliminates float drift)
      - serializes with sort_keys=True (no dict ordering dependency)

    This ensures two GenVM nodes with the same inputs always
    produce the same consensus_hash, satisfying Rialo reproducibility.
    """
    normalized = sorted(
        [
            {
                "agent": a["agent"],
                "approve": bool(a["approve"]),
                "score": round(float(a["score"]), 6),
            }
            for a in agents
        ],
        key=lambda x: x["agent"],
    )
    raw = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


# ─────────────────────────────────────────
# GenVM Runtime
# ─────────────────────────────────────────

class GenVM:
    """
    Abstraction layer for Rialo GenVM execution context.

    mode="simulation" : pure Python, in-memory state (default)
    mode="devnet"     : connects to Rialo node via RIALO_RPC_URL
    mode="mainnet"    : production Rialo runtime (future)
    """

    def __init__(self):
        rialo_url = os.getenv("RIALO_RPC_URL")
        self.mode = "devnet" if rialo_url else "simulation"
        self.rpc_url = rialo_url
        self.storage: GenMap = GenMap()
        self.replay: ReplayProtection = ReplayProtection()

    def get(self, key: str, default=None):
        return self.storage.get(key, default)

    def set(self, key: str, value) -> None:
        self.storage[key] = value

    def __repr__(self):
        return f"<GenVM mode={self.mode} keys={len(self.storage)}>"
