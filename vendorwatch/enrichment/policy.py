"""Retrieve policy text with a guarded, opt-in metered Agent fallback."""
from urllib.parse import urlparse
from vendorwatch import config
from vendorwatch.enrichment.tinyfish_client import TinyFishClient

AGENT_GOAL = (
    "Find this company's privacy policy or data processing page. Check the website footer, "
    "Legal, Privacy, and Do Not Sell My Info links. Return JSON with keys policy_url, "
    "policy_text (verbatim section about sharing or selling personal data), and company_country. "
    "Do not infer statements that are not present."
)

def get_policy_text(url: str | None, site_root: str,
                    client: TinyFishClient | None = None) -> tuple[str | None, str, str | None]:
    client = client or TinyFishClient()
    if url:
        try:
            text = client.fetch(url)
            if text and len(text.strip()) >= 1500:
                return text[:config.MAX_POLICY_CHARS], "fetch", url
        except Exception:
            pass
    if config.ALLOW_AGENT_FALLBACK:
        try:
            result = client.agent(site_root, AGENT_GOAL)
            if result:
                policy_text = result.get("policy_text")
                resolved_url = result.get("policy_url") or url
                if isinstance(policy_text, str) and policy_text.strip():
                    return policy_text[:config.MAX_POLICY_CHARS], "agent", resolved_url
        except Exception:
            pass
    return None, "none", url

def site_root_for(domain: str) -> str:
    return f"https://{domain.strip().strip('/')}"
