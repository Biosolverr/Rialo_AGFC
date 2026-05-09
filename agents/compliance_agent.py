from agents.base import BaseAgent

SYSTEM = """You are a compliance officer reviewing crypto transactions.
Check if the transaction description seems legitimate and policy-compliant.
Return ONLY JSON: {"score": 0.0-1.0, "approve": true/false, "flags": [], "reasoning": "short reason"}
Score: 0=fully compliant, 1=non-compliant. Approve if score < 0.5."""


class ComplianceAgent(BaseAgent):
    def evaluate(self, intent: dict) -> dict:
        prompt = (
            f"Transaction for compliance review:\n"
            f"- Amount: {intent['amount']} USD\n"
            f"- Recipient: {intent['recipient']}\n"
            f"- Description: {intent['text']}\n"
            f"Is this transaction compliant and legitimate?"
        )
        try:
            result = self._ask_llm(SYSTEM, prompt)
            result.setdefault("approve", result.get("score", 1.0) < 0.5)
            return result
        except Exception as e:
            return {"score": 1.0, "approve": False, "flags": ["llm_error"], "reasoning": str(e)}
