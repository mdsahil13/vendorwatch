"""Resolve vendor names and privacy-policy URLs."""
import json
from urllib.parse import urlparse
from vendorwatch import config
from vendorwatch.enrichment.tinyfish_client import TinyFishClient

def known_vendor(registrable: str) -> dict:
    try:
        with config.KNOWN_VENDORS_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        item = data.get(registrable, {})
        return item if isinstance(item, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def search_company(registrable: str, client: TinyFishClient | None = None) -> str:
    client = client or TinyFishClient()
    known = known_vendor(registrable)
    if known.get("company"):
        return str(known["company"])
    results = client.search(f"{registrable} company official website")
    for item in results:
        title = item.get("title") or item.get("name")
        if isinstance(title, str) and title.strip():
            return title.strip()
    return registrable

def find_policy_url(registrable: str, company: str,
                    client: TinyFishClient | None = None) -> str | None:
    client = client or TinyFishClient()
    results = client.search(f"{company or registrable} privacy policy")
    candidates: list[tuple[int, str]] = []
    for item in results:
        url = item.get("url") or item.get("link")
        title = str(item.get("title", ""))
        if not isinstance(url, str) or urlparse(url).scheme not in {"http", "https"}:
            continue
        score = 1 if "privacy" in (url + " " + title).lower() else 0
        candidates.append((score, url))
    candidates.sort(key=lambda pair: pair[0], reverse=True)
    return candidates[0][1] if candidates else None
