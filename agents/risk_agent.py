from agents.base import BaseAgent

SYSTEM = """You are a financial risk analyst for a crypto treasury system.
Analyze transaction intents and return ONLY a JSON object, no explanation.
Format: {"score": 0.0-1.0, "approve": true/false, "flags": [], "reasoning": "short reason"}
Score guide: 0.0=no risk, 1.0=extreme risk. Approve if score < 0.6."""


class RiskAgent(BaseAgent):
    def evaluate(self, intent: dict) -> dict:
        prompt = (
            f"Transaction intent:\n"
            f"- Amount: {intent['amount']} USD\n"
            f"- Recipient: {intent['recipient']}\n"
            f"- Description: {intent['text']}\n"
            f"Assess the financial risk."
        )
        try:
            result = self._ask_llm(SYSTEM, prompt)
            result.setdefault("approve", result.get("score", 1.0) < 0.6)
            return result
        except Exception as e:
            return {"score": 1.0, "approve": False, "flags": ["llm_error"], "reasoning": str(e)}
