from consensus.models import ConsensusResult


class OptimisticConsensus:
    def run(self, votes: list[bool], risk_score: float) -> ConsensusResult:
        approve_count = sum(votes)
        total = len(votes)
        margin = approve_count / total if total > 0 else 0
        appeal_required = margin < 0.7
        confidence = margin
        decision = "approve" if approve_count > total / 2 else "reject"
        if risk_score > 0.85 and decision == "approve":
            decision = "reject"
            appeal_required = True
        return ConsensusResult(
            decision=decision,
            confidence=confidence,
            margin=margin,
            quorum_met=approve_count > total / 2,
            appeal_required=appeal_required,
        )


MockConsensus = OptimisticConsensus
