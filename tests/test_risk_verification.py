import json
from types import SimpleNamespace
from unittest.mock import patch
from vendorwatch.analysis import risk

POLICY = "This company may share personal information with service providers."

def fake_response(quote):
    payload = {
        "company": "Example Inc", "category": "analytics", "country": "US",
        "sells_or_shares_data": True, "evidence": quote, "risk": "high",
        "reason": "The policy describes sharing with service providers."
    }
    return SimpleNamespace(content=[SimpleNamespace(text=json.dumps(payload))])

def test_quote_present_is_verified():
    with patch.object(risk.config, "ANTHROPIC_API_KEY", "test-key"), \
         patch.object(risk, "Anthropic") as client_cls:
        client_cls.return_value.messages.create.return_value = fake_response(POLICY)
        result = risk.analyze_vendor("example.com", "Example Inc", POLICY)
    assert result["evidence_verified"] is True

def test_fabricated_quote_is_not_verified():
    with patch.object(risk.config, "ANTHROPIC_API_KEY", "test-key"), \
         patch.object(risk, "Anthropic") as client_cls:
        client_cls.return_value.messages.create.return_value = fake_response("We sell all personal data.")
        result = risk.analyze_vendor("example.com", "Example Inc", POLICY)
    assert result["evidence_verified"] is False
    assert "[quote could not be verified in policy text]" in result["reason"]
