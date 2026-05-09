from pydantic import BaseModel


class PolicyResult(BaseModel):
    threshold: int
    time_delay: int
    max_single: float
    rolling_window_sec: int


class PolicyEngine:
    def generate(self, amount: float, risk_score: float, consensus_margin: float) -> PolicyResult:
        if amount < 1000:
            threshold = 1
            delay = 0
        elif amount < 10000:
            threshold = 2
            delay = 86400
        else:
            threshold = 3
            delay = 172800

        if risk_score > 0.7:
            threshold += 1
            delay += 86400

        if consensus_margin < 0.7:
            delay += 43200

        threshold = min(threshold, 3)

        return PolicyResult(
            threshold=threshold,
            time_delay=delay,
            max_single=amount * 1.5,
            rolling_window_sec=604800,
        )
