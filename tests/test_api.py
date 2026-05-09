import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

MOCK_APPROVE = {"score": 0.2, "approve": True,  "flags": [],            "reasoning": "looks good"}
MOCK_REJECT  = {"score": 0.9, "approve": False, "flags": ["high_risk"], "reasoning": "suspicious"}

with patch("agents.risk_agent.RiskAgent.evaluate", return_value=MOCK_APPROVE), \
     patch("agents.fraud_agent.FraudAgent.evaluate", return_value=MOCK_APPROVE), \
     patch("agents.compliance_agent.ComplianceAgent.evaluate", return_value=MOCK_APPROVE):
    from orchestrator.main import app

client = TestClient(app)


def test_root_returns_200():
    assert client.get("/").status_code == 200

def test_root_has_name():
    assert "Autonomous Treasury" in client.get("/").json()["name"]

def test_root_has_rialo_mode():
    assert "rialo_mode" in client.get("/").json()

def test_health_returns_200():
    assert client.get("/health").status_code == 200

def test_health_status_ok():
    assert client.get("/health").json()["status"] == "ok"

def test_health_has_agents():
    data = client.get("/health").json()
    assert "agents" in data
    assert len(data["agents"]) == 3

def test_health_has_consensus():
    assert "consensus" in client.get("/health").json()

def test_health_has_rialo_node_status():
    assert "rialo_node" in client.get("/health").json()


@patch("agents.risk_agent.RiskAgent.evaluate", return_value=MOCK_APPROVE)
@patch("agents.fraud_agent.FraudAgent.evaluate", return_value=MOCK_APPROVE)
@patch("agents.compliance_agent.ComplianceAgent.evaluate", return_value=MOCK_APPROVE)
def test_intent_approve_returns_200(m1, m2, m3):
    r = client.post("/intent", json={"user_address": "0xUser", "amount": 500, "recipient": "0xRecipient", "intent_text": "Invoice"})
    assert r.status_code == 200

@patch("agents.risk_agent.RiskAgent.evaluate", return_value=MOCK_APPROVE)
@patch("agents.fraud_agent.FraudAgent.evaluate", return_value=MOCK_APPROVE)
@patch("agents.compliance_agent.ComplianceAgent.evaluate", return_value=MOCK_APPROVE)
def test_intent_approve_status(m1, m2, m3):
    r = client.post("/intent", json={"user_address": "0xUser", "amount": 500, "recipient": "0xRecipient", "intent_text": "Invoice"})
    assert r.json()["approved"] is True
    assert r.json()["status"] == "approved"

@patch("agents.risk_agent.RiskAgent.evaluate", return_value=MOCK_APPROVE)
@patch("agents.fraud_agent.FraudAgent.evaluate", return_value=MOCK_APPROVE)
@patch("agents.compliance_agent.ComplianceAgent.evaluate", return_value=MOCK_APPROVE)
def test_intent_approve_has_safe_tx(m1, m2, m3):
    r = client.post("/intent", json={"user_address": "0xUser", "amount": 500, "recipient": "0xRecipient", "intent_text": "Invoice"})
    assert r.json()["safe_tx"] is not None
    assert r.json()["tx_hash"] is not None

@patch("agents.risk_agent.RiskAgent.evaluate", return_value=MOCK_APPROVE)
@patch("agents.fraud_agent.FraudAgent.evaluate", return_value=MOCK_APPROVE)
@patch("agents.compliance_agent.ComplianceAgent.evaluate", return_value=MOCK_APPROVE)
def test_intent_approve_has_policy(m1, m2, m3):
    r = client.post("/intent", json={"user_address": "0xUser", "amount": 500, "recipient": "0xRecipient", "intent_text": "Invoice"})
    assert r.json()["policy"] is not None
    assert "threshold" in r.json()["policy"]

@patch("agents.risk_agent.RiskAgent.evaluate", return_value=MOCK_REJECT)
@patch("agents.fraud_agent.FraudAgent.evaluate", return_value=MOCK_REJECT)
@patch("agents.compliance_agent.ComplianceAgent.evaluate", return_value=MOCK_REJECT)
def test_intent_reject_status(m1, m2, m3):
    r = client.post("/intent", json={"user_address": "0xH", "amount": 9999999, "recipient": "0xDark", "intent_text": "Offshore"})
    assert r.json()["approved"] is False
    assert r.json()["status"] == "rejected"

@patch("agents.risk_agent.RiskAgent.evaluate", return_value=MOCK_REJECT)
@patch("agents.fraud_agent.FraudAgent.evaluate", return_value=MOCK_REJECT)
@patch("agents.compliance_agent.ComplianceAgent.evaluate", return_value=MOCK_REJECT)
def test_intent_reject_no_safe_tx(m1, m2, m3):
    r = client.post("/intent", json={"user_address": "0xH", "amount": 9999999, "recipient": "0xDark", "intent_text": "Offshore"})
    assert r.json()["safe_tx"] is None
    assert r.json()["tx_hash"] is None

@patch("agents.risk_agent.RiskAgent.evaluate", return_value=MOCK_APPROVE)
@patch("agents.fraud_agent.FraudAgent.evaluate", return_value=MOCK_APPROVE)
@patch("agents.compliance_agent.ComplianceAgent.evaluate", return_value=MOCK_APPROVE)
def test_response_has_all_fields(m1, m2, m3):
    r = client.post("/intent", json={"user_address": "0xUser", "amount": 500, "recipient": "0xRecipient", "intent_text": "Payment"})
    for field in ["status", "risk_score", "approved", "reason", "agents", "consensus_confidence", "rialo_mode"]:
        assert field in r.json()

@patch("agents.risk_agent.RiskAgent.evaluate", return_value=MOCK_APPROVE)
@patch("agents.fraud_agent.FraudAgent.evaluate", return_value=MOCK_APPROVE)
@patch("agents.compliance_agent.ComplianceAgent.evaluate", return_value=MOCK_APPROVE)
def test_response_has_3_agents(m1, m2, m3):
    r = client.post("/intent", json={"user_address": "0xUser", "amount": 500, "recipient": "0xRecipient", "intent_text": "Payment"})
    names = [a["agent"] for a in r.json()["agents"]]
    assert len(names) == 3
    assert "RiskAI" in names
    assert "FraudDetect" in names
    assert "ComplianceGuard" in names

def test_missing_field_returns_422():
    r = client.post("/intent", json={"user_address": "0xUser", "amount": 500})
    assert r.status_code == 422

def test_invalid_amount_type_returns_422():
    r = client.post("/intent", json={"user_address": "0xUser", "amount": "bad", "recipient": "0xR", "intent_text": "P"})
    assert r.status_code == 422
