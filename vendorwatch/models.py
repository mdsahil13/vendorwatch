"""Typed data models used throughout VendorWatch."""
from dataclasses import asdict, dataclass, field
from typing import Optional

@dataclass
class Destination:
    domain: str
    registrable: str
    sources: set[str] = field(default_factory=set)
    hits: int = 0
    bytes_out: int = 0

@dataclass
class VendorProfile:
    registrable: str
    company: str
    category: str = "unknown"
    country: Optional[str] = None
    policy_url: Optional[str] = None
    sells_or_shares_data: Optional[bool] = None
    evidence: Optional[str] = None
    evidence_verified: bool = False
    risk: str = "unknown"
    reason: str = ""
    method: str = "none"
    hits: int = 0
    domains_seen: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
