"""Parallel vendor investigation pipeline with per-vendor fault isolation."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse
from vendorwatch import config
from vendorwatch.models import Destination, VendorProfile
from vendorwatch.dpi.pcap_parser import parse_pcap, registrable_domain
from vendorwatch.enrichment.tinyfish_client import TinyFishClient
from vendorwatch.enrichment.resolver import known_vendor, search_company, find_policy_url
from vendorwatch.enrichment.policy import get_policy_text, site_root_for
from vendorwatch.analysis.risk import analyze_vendor
from vendorwatch.storage import cache

_RISK_ORDER = {"high": 0, "medium": 1, "unknown": 2, "low": 3}

def _profile_from_dict(data: dict) -> VendorProfile:
    allowed = {key: value for key, value in data.items() if key in VendorProfile.__dataclass_fields__}
    return VendorProfile(**allowed)

def investigate(dest: Destination) -> VendorProfile:
    # key = f"v1:{dest.registrable}
    key = f"v2:{dest.registrable}"
    cached = cache.get(key)
    if cached:
        profile = _profile_from_dict(cached)
        profile.hits = dest.hits
        profile.domains_seen = [dest.domain]
        return profile
    try:
        tf = TinyFishClient()
        known = known_vendor(dest.registrable)
        company = str(known.get("company") or search_company(dest.registrable, tf))
        category = str(known.get("category") or "unknown")
        policy_url = find_policy_url(dest.registrable, company, tf)
        policy_text, method, resolved_url = get_policy_text(
            policy_url, site_root_for(dest.registrable), tf
        )
        verdict = analyze_vendor(dest.registrable, company, policy_text)
        profile = VendorProfile(
            registrable=dest.registrable,
            company=str(verdict.get("company") or company),
            category=str(verdict.get("category") or category),
            country=verdict.get("country"),
            policy_url=resolved_url or policy_url,
            sells_or_shares_data=verdict.get("sells_or_shares_data"),
            evidence=verdict.get("evidence"),
            evidence_verified=bool(verdict.get("evidence_verified", False)),
            risk=str(verdict.get("risk") or "unknown"),
            reason=str(verdict.get("reason") or ""),
            method=method, hits=dest.hits, domains_seen=[dest.domain],
        )
    except Exception as exc:
        profile = VendorProfile(
            registrable=dest.registrable, company=dest.registrable,
            category=str(known_vendor(dest.registrable).get("category") or "unknown"),
            risk="unknown", reason=f"Vendor investigation failed safely: {type(exc).__name__}.",
            hits=dest.hits, domains_seen=[dest.domain],
        )
    cache.put(key, profile.to_dict())
    return profile

def _safe_investigate(dest: Destination) -> VendorProfile:
    try:
        return investigate(dest)
    except Exception as exc:
        return VendorProfile(dest.registrable, dest.registrable, risk="unknown",
                             reason=f"Vendor investigation failed safely: {type(exc).__name__}.",
                             hits=dest.hits, domains_seen=[dest.domain])

def run(pcap_path: str | Path, app_domains: list[str] | None = None,
        on_progress=None) -> list[VendorProfile]:
    destinations = parse_pcap(pcap_path)
    own = {registrable_domain(item) for item in (app_domains or []) if item.strip()}
    results: list[VendorProfile] = []
    third_party: list[Destination] = []
    for dest in destinations:
        if dest.registrable in own or dest.domain in own:
            results.append(VendorProfile(
                registrable=dest.registrable, company="App's own domain",
                category="first-party", risk="low", reason="App's own domain; investigation skipped.",
                hits=dest.hits, domains_seen=[dest.domain],
            ))
        else:
            third_party.append(dest)
    total = len(third_party)
    if total:
        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            futures = {executor.submit(_safe_investigate, dest): dest for dest in third_party}
            done = 0
            for future in as_completed(futures):
                dest = futures[future]
                results.append(future.result())
                done += 1
                if on_progress:
                    on_progress(done, total, dest.registrable)
    results.sort(key=lambda profile: (_RISK_ORDER.get(profile.risk, 2), -profile.hits, profile.registrable))
    return results

def summarize(profiles: list[VendorProfile]) -> dict:
    third_party = [p for p in profiles if p.category != "first-party"]
    return {
        "total_domains": len(profiles),
        "third_party": len(third_party),
        "high_risk": sum(p.risk == "high" for p in third_party),
        "sell_or_share": sum(p.sells_or_shares_data is True for p in third_party),
        "policy_not_found": sum(p.method == "none" for p in third_party),
    }
