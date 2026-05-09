import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.treasury_governance import TreasuryGovernance


def test_returns_dict():
    result = TreasuryGovernance().execute_transfer("0xRecipient", 500, "test payment")
    assert isinstance(result, dict)


def test_has_required_fields():
    result = TreasuryGovernance().execute_transfer("0xRecipient", 500, "test payment")
    for field in ["tx_hash", "status", "recipient", "amount", "reason"]:
        assert field in result


def test_recipient_preserved():
    result = TreasuryGovernance().execute_transfer("0xAlice", 1000, "salary")
    assert result["recipient"] == "0xAlice"


def test_amount_preserved():
    result = TreasuryGovernance().execute_transfer("0xBob", 9999, "invoice")
    assert result["amount"] == 9999


def test_reason_preserved():
    result = TreasuryGovernance().execute_transfer("0xBob", 100, "my reason")
    assert result["reason"] == "my reason"


def test_tx_hash_starts_with_0x():
    result = TreasuryGovernance().execute_transfer("0xBob", 500, "payment")
    assert result["tx_hash"].startswith("0x")


def test_simulation_mode_label():
    result = TreasuryGovernance().execute_transfer("0xBob", 500, "payment")
    assert result.get("mode", "simulation") in ["simulation", "rialo_node", "failed", None]


def test_deterministic_hash_same_input():
    t = TreasuryGovernance()
    r1 = t.execute_transfer("0xAlice", 500, "invoice")
    r2 = t.execute_transfer("0xAlice", 500, "invoice")
    if r1.get("mode") == "simulation":
        assert r1["tx_hash"] == r2["tx_hash"]


def test_different_input_different_hash():
    t = TreasuryGovernance()
    r1 = t.execute_transfer("0xAlice", 500, "invoice A")
    r2 = t.execute_transfer("0xAlice", 500, "invoice B")
    if r1.get("mode") == "simulation" and r2.get("mode") == "simulation":
        assert r1["tx_hash"] != r2["tx_hash"]


def test_zero_amount_handled():
    result = TreasuryGovernance().execute_transfer("0xBob", 0, "zero test")
    assert "tx_hash" in result


def test_large_amount_handled():
    result = TreasuryGovernance().execute_transfer("0xBob", 9_999_999, "large transfer")
    assert "tx_hash" in result
