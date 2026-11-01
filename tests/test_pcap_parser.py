from scapy.all import Ether, IP, UDP, DNS, DNSQR, wrpcap
from vendorwatch.dpi.pcap_parser import extract_sni, registrable_domain, parse_pcap
from scripts.make_sample_pcap import build_client_hello

def test_extract_sni_from_client_hello():
    assert extract_sni(build_client_hello("api.example.com")) == "api.example.com"

def test_extract_sni_invalid_payloads():
    assert extract_sni(b"") is None
    assert extract_sni(b"not tls data") is None
    assert extract_sni(b"\x16\x03\x01\x00\x10broken") is None

def test_registrable_domain_co_uk():
    assert registrable_domain("a.b.example.co.uk") == "example.co.uk"

def test_parse_pcap_expected_domains(tmp_path):
    path = tmp_path / "tiny.pcap"
    packets = [
        Ether()/IP(src="192.0.2.1", dst="198.51.100.1")/UDP(sport=53000,dport=53)/
        DNS(rd=1, qd=DNSQR(qname="api.example.com")),
        Ether()/IP(src="192.0.2.1", dst="198.51.100.1")/UDP(sport=53001,dport=53)/
        DNS(rd=1, qd=DNSQR(qname="cdn.example.net")),
    ]
    wrpcap(str(path), packets)
    found = {item.registrable for item in parse_pcap(path)}
    assert found == {"example.com", "example.net"}
