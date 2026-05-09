import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock


class MockTreeMap(dict):
    def get(self, key, default=None):
        return super().get(key, default)

class MockDynArray(list):
    pass

class MockAddress(str):
    pass


gl_mock = MagicMock()
gl_mock.Contract = object
gl_mock.Address = MockAddress
gl_mock.TreeMap = lambda *a, **kw: MockTreeMap()
gl_mock.DynArray = lambda *a, **kw: MockDynArray()
gl_mock.public = MagicMock()
gl_mock.public.view = lambda f: f
gl_mock.public.write = lambda f: f
gl_mock.get_webpage = MagicMock()

u256 = int
u32 = int

sys.modules["genlayer"] = MagicMock(gl=gl_mock, Contract=object, Address=MockAddress, TreeMap=MockTreeMap, DynArray=MockDynArray)
sys.modules["genlayer"].u256 = u256
sys.modules["genlayer"].u32 = u32

import builtins
builtins.gl = gl_mock
builtins.u256 = u256
builtins.u32 = u32

from contracts.treasury_governance import TreasuryGovernance


def make_contract():
    c = TreasuryGovernance.__new__(TreasuryGovernance)
    c.amount_thresholds = MockTreeMap()
    c.verdict_log = MockDynArray()
    c.active_policies = MockTreeMap()
    return c


def test_small_amount_requires_1_signer():
    assert make_contract().get_required_signers(500) == 1

def test_medium_amount_requires_2_signers():
    assert make_contract().get_required_signers(5000) == 2

def test_large_amount_requires_3_signers():
    assert make_contract().get_required_signers(50000) == 3

def test_boundary_999_is_small():
    assert make_contract().get_required_signers(999) == 1

def test_boundary_1000_is_medium():
    assert make_contract().get_required_signers(1000) == 2

def test_record_verdict_appends_to_log():
    c = make_contract()
    c.record_verdict("hash1", "approve", 85, "policy_abc")
    assert len(c.verdict_log) == 1

def test_record_verdict_format():
    c = make_contract()
    c.record_verdict("hash1", "approve", 85, "policy_abc")
    assert "hash1" in c.verdict_log[0]
    assert "approve" in c.verdict_log[0]

def test_record_verdict_stores_policy():
    c = make_contract()
    c.record_verdict("intent_abc", "approve", 90, "policy_xyz")
    assert c.active_policies["intent_abc"] == "policy_xyz"

def test_verify_policy_returns_stored():
    c = make_contract()
    c.active_policies["intent1"] = "policy_hash_1"
    assert c.verify_policy("intent1") == "policy_hash_1"

def test_verify_policy_not_found():
    assert make_contract().verify_policy("nonexistent") == "NOT_FOUND"

def test_update_threshold_changes_value():
    c = make_contract()
    c.update_threshold(5000, 2)
    assert c.amount_thresholds[5000] == 2

def test_update_threshold_logs_policy_update():
    c = make_contract()
    c.update_threshold(5000, 2)
    assert any("POLICY_UPDATE" in entry for entry in c.verdict_log)

def test_verdict_count_starts_at_zero():
    assert make_contract().get_verdict_count() == 0

def test_verdict_count_increments():
    c = make_contract()
    c.record_verdict("h1", "approve", 90, "p1")
    c.record_verdict("h2", "reject", 10, "p2")
    assert c.get_verdict_count() == 2
