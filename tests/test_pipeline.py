from unittest.mock import patch
from vendorwatch.models import Destination, VendorProfile
from vendorwatch import pipeline

def test_first_party_skip_exception_isolation_sort_and_summary(tmp_path):
    destinations = [
        Destination("api.myapp.com", "myapp.com", {"dns"}, 2, 100),
        Destination("tracker.example.com", "example.com", {"sni"}, 5, 200),
        Destination("bad.vendor.test", "vendor.test", {"dns"}, 9, 300),
    ]
    def fake_investigate(dest):
        if dest.registrable == "vendor.test":
            raise RuntimeError("isolated failure")
        return VendorProfile(dest.registrable, "Example Vendor", category="analytics",
                             risk="high", sells_or_shares_data=True, hits=dest.hits,
                             domains_seen=[dest.domain], method="fetch")
    with patch.object(pipeline, "parse_pcap", return_value=destinations), \
         patch.object(pipeline, "_safe_investigate", side_effect=fake_investigate):
        results = pipeline.run("unused.pcap", ["myapp.com"])
    assert results[0].category == "first-party" or results[0].risk == "high"
    assert any(p.category == "first-party" for p in results)
    assert any(p.registrable == "vendor.test" and p.risk == "unknown" for p in results) is False
    summary = pipeline.summarize(results)
    assert summary["third_party"] == 2
    assert summary["sell_or_share"] == 1

def test_safe_wrapper_returns_unknown():
    dest = Destination("bad.vendor.test", "vendor.test", {"dns"}, 1, 50)
    with patch.object(pipeline, "investigate", side_effect=RuntimeError("broken")):
        profile = pipeline._safe_investigate(dest)
    assert profile.risk == "unknown"
