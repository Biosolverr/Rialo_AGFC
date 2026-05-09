import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from safe_integration.executor import SafeExecutor
from policy_engine.engine import PolicyEngine


def make_policy(amount=5000, risk=0.3, margin=0.9):
    return PolicyEngine().generate(amount=amount, risk_score=risk, consensus_margin=margin)


def test_tx_has_all_required_fields():
    tx = SafeExecutor().build_tx("0xRecipient", 5000, make_policy(), "abc123")
    for field in ["to", "value_usd", "required_signatures", "execution_delay_sec",
                  "max_single_tx", "nonce", "audit_hash", "intent_hash", "chain_id", "status"]:
        assert field in tx


def test_recipient_and_amount_correct():
    tx = SafeExecutor().build_tx("0xAlice", 1234, make_policy(1234), "hash1")
    assert tx["to"] == "0xAlice"
    assert tx["value_usd"] == 1234


def test_chain_id_is_sepolia():
    tx = SafeExecutor().build_tx("0xBob", 500, make_policy(500), "hash2")
    assert tx["chain_id"] == 11155111


def test_status_pending_signatures():
    tx = SafeExecutor().build_tx("0xBob", 500, make_policy(500), "hash3")
    assert tx["status"] == "pending_signatures"


def test_audit_hash_starts_with_0x():
    tx = SafeExecutor().build_tx("0xBob", 500, make_policy(500), "hash4")
    assert tx["audit_hash"].startswith("0x")
    assert len(tx["audit_hash"]) == 66


def test_intent_hash_preserved():
    tx = SafeExecutor().build_tx("0xBob", 500, make_policy(500), "my_intent_hash")
    assert tx["intent_hash"] == "my_intent_hash"


def test_required_signatures_from_policy():
    policy = make_policy(amount=5000, risk=0.3, margin=0.9)
    tx = SafeExecutor().build_tx("0xBob", 5000, policy, "h1")
    assert tx["required_signatures"] == policy.threshold


def test_execution_delay_from_policy():
    policy = make_policy(amount=5000, risk=0.3, margin=0.9)
    tx = SafeExecutor().build_tx("0xBob", 5000, policy, "h2")
    assert tx["execution_delay_sec"] == policy.time_delay


def test_max_single_tx_from_policy():
    policy = make_policy(amount=5000)
    tx = SafeExecutor().build_tx("0xBob", 5000, policy, "h3")
    assert tx["max_single_tx"] == policy.max_single


def test_different_recipient_different_hash():
    policy = make_policy()
    tx1 = SafeExecutor().build_tx("0xAlice", 5000, policy, "same_hash")
    tx2 = SafeExecutor().build_tx("0xBob",   5000, policy, "same_hash")
    assert tx1["audit_hash"] != tx2["audit_hash"]


def test_different_intent_different_hash():
    policy = make_policy()
    tx1 = SafeExecutor().build_tx("0xAlice", 5000, policy, "intent_A")
    tx2 = SafeExecutor().build_tx("0xAlice", 5000, policy, "intent_B")
    assert tx1["audit_hash"] != tx2["audit_hash"]


def test_different_amount_different_hash():
    policy1 = make_policy(amount=1000)
    policy2 = make_policy(amount=9000)
    tx1 = SafeExecutor().build_tx("0xAlice", 1000, policy1, "same")
    tx2 = SafeExecutor().build_tx("0xAlice", 9000, policy2, "same")
    assert tx1["audit_hash"] != tx2["audit_hash"]


def test_nonce_is_integer():
    tx = SafeExecutor().build_tx("0xBob", 500, make_policy(500), "h")
    assert isinstance(tx["nonce"], int)
    assert tx["nonce"] > 0
