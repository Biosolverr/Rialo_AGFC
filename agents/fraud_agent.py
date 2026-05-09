from agents.base import BaseAgent

SYSTEM = """You are a fraud detection specialist for a crypto treasury.
Look for suspicious patterns: structuring, unusual recipients, anomalous descriptions.
Return ONLY JSON: {"score": 0.0-1.0, "approve": true/false, "flags": [], "reasoning": "short reason"}
Score: 0=clean, 1=clear fraud. Approve if score < 0.5."""


class FraudAgent(BaseAgent):
    def evaluate(self, intent: dict) -> dict:
        prompt = (
            f"Transaction to review:\n"
            f"- Amount: {intent['amount']} USD\n"
            f"- Recipient: {intent['recipient']}\n"
            f"- Description: {intent['text']}\n"
            f"Detect fraud or suspicious patterns."
        )
        try:
            result = self._ask_llm(SYSTEM, prompt)
            result.setdefault("approve", result.get("score", 1.0) < 0.5)
            return result
        except Exception as e:
            return {"score": 1.0, "approve": False, "flags": ["llm_error"], "reasoning": str(e)}
