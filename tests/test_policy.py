import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from policy_engine.engine import PolicyEngine, PolicyResult


def test_small_amount_1_signer_no_delay():
    r = PolicyEngine().generate(amount=500, risk_score=0.2, consensus_margin=0.9)
    assert r.threshold == 1
    assert r.time_delay == 0


def test_medium_amount_2_signers_24h():
    r = PolicyEngine().generate(amount=5000, risk_score=0.3, consensus_margin=0.9)
    assert r.threshold == 2
    assert r.time_delay == 86400


def test_large_amount_3_signers_48h():
    r = PolicyEngine().generate(amount=50000, risk_score=0.3, consensus_margin=0.9)
    assert r.threshold == 3
    assert r.time_delay == 172800


def test_boundary_exactly_1000_is_medium():
    r = PolicyEngine().generate(amount=1000, risk_score=0.3, consensus_margin=0.9)
    assert r.threshold == 2
    assert r.time_delay == 86400


def test_boundary_exactly_10000_is_large():
    r = PolicyEngine().generate(amount=10000, risk_score=0.3, consensus_margin=0.9)
    assert r.threshold == 3
    assert r.time_delay == 172800


def test_high_risk_adds_signer_and_delay():
    r = PolicyEngine().generate(amount=500, risk_score=0.8, consensus_margin=0.9)
    assert r.threshold == 2
    assert r.time_delay == 86400


def test_risk_below_threshold_no_extra():
    r = PolicyEngine().generate(amount=500, risk_score=0.69, consensus_margin=0.9)
    assert r.threshold == 1
    assert r.time_delay == 0


def test_threshold_capped_at_3():
    r = PolicyEngine().generate(amount=50000, risk_score=0.9, consensus_margin=0.9)
    assert r.threshold == 3


def test_weak_consensus_adds_12h_delay():
    r = PolicyEngine().generate(amount=500, risk_score=0.2, consensus_margin=0.5)
    assert r.time_delay == 43200


def test_strong_consensus_no_extra_delay():
    r = PolicyEngine().generate(amount=500, risk_score=0.2, consensus_margin=0.8)
    assert r.time_delay == 0


def test_combined_risk_and_weak_consensus():
    r = PolicyEngine().generate(amount=500, risk_score=0.8, consensus_margin=0.5)
    assert r.time_delay == 86400 + 43200


def test_max_single_is_15x_amount():
    r = PolicyEngine().generate(amount=1000, risk_score=0.1, consensus_margin=0.9)
    assert r.max_single == 1500.0


def test_rolling_window_always_7_days():
    r = PolicyEngine().generate(amount=500, risk_score=0.1, consensus_margin=0.9)
    assert r.rolling_window_sec == 604800


def test_returns_policy_result_model():
    r = PolicyEngine().generate(amount=500, risk_score=0.2, consensus_margin=0.9)
    assert isinstance(r, PolicyResult)
    assert hasattr(r, "threshold")
    assert hasattr(r, "time_delay")
    assert hasattr(r, "max_single")
    assert hasattr(r, "rolling_window_sec")


def test_zero_amount_edge_case():
    r = PolicyEngine().generate(amount=0, risk_score=0.1, consensus_margin=0.9)
    assert r.threshold == 1
    assert r.time_delay == 0
