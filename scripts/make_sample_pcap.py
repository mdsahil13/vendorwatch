"""Generate a synthetic capture containing DNS queries and TLS SNI ClientHellos."""
from pathlib import Path
import sys
from scapy.all import IP, UDP, DNS, DNSQR, Ether, TCP, Raw, wrpcap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "samples" / "demo.pcap"

def build_client_hello(hostname: str) -> bytes:
    """Build a minimal structurally valid TLS ClientHello record with an SNI extension."""
    host = hostname.encode("ascii")
    server_name = b"\x00" + len(host).to_bytes(2, "big") + host
    name_list = len(server_name).to_bytes(2, "big") + server_name
    sni_extension = b"\x00\x00" + len(name_list).to_bytes(2, "big") + name_list
    version_random = b"\x03\x03" + bytes(range(32))
    session = b"\x00"
    ciphers = b"\x00\x02\x13\x01"
    compression = b"\x01\x00"
    extensions = sni_extension
    body = version_random + session + ciphers + compression + len(extensions).to_bytes(2, "big") + extensions
    handshake = b"\x01" + len(body).to_bytes(3, "big") + body
    return b"\x16\x03\x01" + len(handshake).to_bytes(2, "big") + handshake

def main() -> None:
    hosts = [
        "api.myapp.com", "app-measurement.com", "sdk.appsflyer.com",
        "graph.facebook.com", "doubleclick.net", "sentry.io",
        "api.mixpanel.com", "api2.branch.io", "collector.unknown-sdk.example",
    ]
    packets = []
    for index, host in enumerate(hosts, start=1):
        packets.append(Ether()/IP(src="192.0.2.10", dst="198.51.100.20")/
                       UDP(sport=53000 + index, dport=53)/
                       DNS(rd=1, qd=DNSQR(qname=host)))
        hello = build_client_hello(host)
        packets.append(Ether()/IP(src="192.0.2.10", dst="198.51.100.20")/
                       TCP(sport=40000 + index, dport=443, flags="PA", seq=1, ack=1)/
                       Raw(load=hello))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wrpcap(str(OUT), packets)
    print(f"Created synthetic sample capture: {OUT}")

if __name__ == "__main__":
    main()
