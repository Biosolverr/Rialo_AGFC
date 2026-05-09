import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from consensus.engine import OptimisticConsensus
from consensus.models import ConsensusResult


def test_unanimous_approve():
    r = OptimisticConsensus().run([True, True, True], risk_score=0.1)
    assert r.decision == "approve"
    assert r.quorum_met is True
    assert r.margin == 1.0
    assert r.appeal_required is False


def test_unanimous_reject():
    r = OptimisticConsensus().run([False, False, False], risk_score=0.9)
    assert r.decision == "reject"
    assert r.quorum_met is False
    assert r.margin == 0.0


def test_majority_approve_2_of_3():
    r = OptimisticConsensus().run([True, True, False], risk_score=0.3)
    assert r.decision == "approve"
    assert r.quorum_met is True
    assert round(r.margin, 2) == 0.67


def test_majority_reject_2_of_3():
    r = OptimisticConsensus().run([False, False, True], risk_score=0.8)
    assert r.decision == "reject"
    assert r.quorum_met is False


def test_split_vote_triggers_appeal():
    r = OptimisticConsensus().run([True, True, False], risk_score=0.5)
    assert r.appeal_required is True  # margin 0.66 < 0.7


def test_strong_majority_no_appeal():
    r = OptimisticConsensus().run([True, True, True], risk_score=0.2)
    assert r.appeal_required is False  # margin 1.0 >= 0.7


def test_high_risk_overrides_unanimous_approve():
    r = OptimisticConsensus().run([True, True, True], risk_score=0.9)
    assert r.decision == "reject"
    assert r.appeal_required is True


def test_risk_below_threshold_no_override():
    r = OptimisticConsensus().run([True, True, True], risk_score=0.84)
    assert r.decision == "approve"


def test_confidence_equals_margin():
    r = OptimisticConsensus().run([True, True, False], risk_score=0.2)
    assert r.confidence == r.margin


def test_confidence_in_range():
    r = OptimisticConsensus().run([True, False, False], risk_score=0.5)
    assert 0.0 <= r.confidence <= 1.0


def test_returns_consensus_result_model():
    r = OptimisticConsensus().run([True, True, True], risk_score=0.1)
    assert isinstance(r, ConsensusResult)
