
"""Analyze privacy-policy text with Gemini and verify evidence quotes locally."""

import json
import re

from google import genai
from google.genai import types

from vendorwatch import config


SYSTEM_PROMPT = """You analyze company privacy-policy text.

Return ONLY one valid JSON object with exactly these keys:
company, category, country, sells_or_shares_data, evidence, risk, reason.

Rules:
- category must be analytics, ads, crash, payment, cdn, or unknown.
- sells_or_shares_data must be true, false, or null.
- evidence must be one exact verbatim sentence from the supplied policy text, or null.
- risk must be low, medium, high, or unknown.
- Never paraphrase evidence.
- Use null when the policy does not clearly state the answer.
- Evidence must directly support the data-sharing conclusion.
- Do not classify a company as selling data without explicit policy evidence.
- Never claim data was sent, stolen, or leaked just because a network destination was contacted.
- A domain name alone is not evidence of a company's data practices.
- Do not invent company details, country, or policy statements.
- If the policy is unclear, use unknown rather than guessing.
"""


def _safe_default(company: str, reason: str) -> dict:
    """Return a safe unknown result when analysis cannot be completed."""
    return {
        "company": company,
        "category": "unknown",
        "country": None,
        "sells_or_shares_data": None,
        "evidence": None,
        "risk": "unknown",
        "reason": reason,
        "evidence_verified": False,
    }


def _extract_json(content: str) -> dict | None:
    """Extract a JSON object from Gemini's response."""
    if not content:
        return None

    try:
        value = json.loads(content.strip())
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, flags=re.DOTALL)

    if not match:
        return None

    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def _normalize(value: str) -> str:
    """Normalize whitespace and case for evidence verification."""
    return " ".join(value.split()).casefold()


def analyze_vendor(
    registrable: str,
    company: str,
    policy_text: str | None
) -> dict:
    """Analyze a vendor's privacy policy using Gemini."""

    # Do not call Gemini when no policy was retrieved.
    if not policy_text or not policy_text.strip():
        return {
            **_safe_default(
                company,
                "Privacy policy could not be retrieved. Data-sharing practices are unknown."
            ),
            "risk": "medium",
        }

    # Check API key only when analysis is actually needed.
    if not config.GEMINI_API_KEY:
        return _safe_default(
            company,
            "GEMINI_API_KEY is missing; policy verdict was not generated."
        )

    original_policy = policy_text[:config.MAX_POLICY_CHARS]

    prompt = (
        f"Company: {company}\n"
        f"Domain: {registrable}\n\n"
        f"Analyze only the following privacy policy.\n"
        f"Policy text:\n{original_policy}"
    )

    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)

        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.1,
                max_output_tokens=1200,
            ),
        )

        parsed = _extract_json(response.text or "")

        if parsed is None:
            return _safe_default(
                company,
                "Gemini returned an invalid JSON response."
            )

        # Validate category.
        allowed_categories = {
            "analytics",
            "ads",
            "crash",
            "payment",
            "cdn",
            "unknown",
        }

        category = parsed.get("category")

        if not isinstance(category, str):
            category = "unknown"
        else:
            category = category.strip().lower()

        if category not in allowed_categories:
            category = "unknown"

        # Validate data-sharing verdict.
        sell = parsed.get("sells_or_shares_data")

        if sell not in (True, False, None):
            sell = None

        # Validate risk.
        risk = parsed.get("risk")

        if not isinstance(risk, str):
            risk = "unknown"
        else:
            risk = risk.strip().lower()

        if risk not in {"low", "medium", "high", "unknown"}:
            risk = "unknown"

        # Validate evidence quote.
        evidence = parsed.get("evidence")

        if not isinstance(evidence, str) or not evidence.strip():
            evidence = None

        # Verify evidence against the original policy text.
        verified = bool(
            evidence
            and _normalize(evidence) in _normalize(original_policy)
        )

        reason = str(
            parsed.get("reason") or "No clear explanation was returned."
        )

        # Do not trust unsupported AI conclusions.
        if evidence and not verified:
            evidence = None
            sell = None
            risk = "unknown"
            reason = (
                "Gemini returned a quote that could not be verified "
                "in the original policy. Verdict marked unknown."
            )

        # A sharing verdict needs supporting evidence.
        if sell is not None and not verified:
            sell = None
            risk = "unknown"
            reason = (
                "Data-sharing conclusion could not be supported "
                "by a verified policy quote."
            )

        return {
            "company": str(parsed.get("company") or company),
            "category": category,
            "country": (
                parsed.get("country")
                if isinstance(parsed.get("country"), str)
                else None
            ),
            "sells_or_shares_data": sell,
            "evidence": evidence,
            "evidence_verified": verified,
            "risk": risk,
            "reason": reason,
        }

    except Exception as e:
        return _safe_default(
            company,
            f"Gemini analysis failed: {str(e)}"
        )
