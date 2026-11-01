"""Extract DNS names and TLS SNI from a packet capture; encrypted payloads stay opaque."""
from collections import defaultdict
from pathlib import Path
from typing import Optional
import ipaddress
import tldextract
from scapy.all import PcapReader, DNS, DNSQR, TCP, Raw
from vendorwatch.models import Destination

_EXTRACTOR = tldextract.TLDExtract(suffix_list_urls=())

def registrable_domain(host: str) -> str:
    """Return eTLD+1 when possible, otherwise a normalized hostname."""
    clean = host.strip().rstrip(".").lower()
    if not clean:
        return clean
    try:
        ipaddress.ip_address(clean)
        return clean
    except ValueError:
        pass
    try:
        result = _EXTRACTOR(clean)
        return result.top_domain_under_public_suffix or clean
    except Exception:
        return clean

def extract_sni(payload: bytes) -> Optional[str]:
    """Parse a TLS record containing a ClientHello and return its first SNI hostname."""
    try:
        if len(payload) < 9 or payload[0] != 0x16:
            return None
        record_len = int.from_bytes(payload[3:5], "big")
        record = payload[5:5 + record_len]
        if len(record) < 4 or record[0] != 0x01:
            return None
        hello_len = int.from_bytes(record[1:4], "big")
        hello = record[4:4 + hello_len]
        pos = 0
        if len(hello) < 34:
            return None
        pos += 2 + 32
        session_len = hello[pos]
        pos += 1 + session_len
        cipher_len = int.from_bytes(hello[pos:pos + 2], "big")
        pos += 2 + cipher_len
        compression_len = hello[pos]
        pos += 1 + compression_len
        if pos + 2 > len(hello):
            return None
        extensions_len = int.from_bytes(hello[pos:pos + 2], "big")
        pos += 2
        end = min(len(hello), pos + extensions_len)
        while pos + 4 <= end:
            ext_type = int.from_bytes(hello[pos:pos + 2], "big")
            ext_len = int.from_bytes(hello[pos + 2:pos + 4], "big")
            pos += 4
            ext = hello[pos:pos + ext_len]
            if len(ext) != ext_len:
                return None
            if ext_type == 0 and len(ext) >= 5:
                list_len = int.from_bytes(ext[0:2], "big")
                cursor = 2
                limit = min(len(ext), 2 + list_len)
                while cursor + 3 <= limit:
                    name_type = ext[cursor]
                    name_len = int.from_bytes(ext[cursor + 1:cursor + 3], "big")
                    cursor += 3
                    name = ext[cursor:cursor + name_len]
                    if len(name) != name_len:
                        return None
                    if name_type == 0:
                        hostname = name.decode("ascii").strip().rstrip(".").lower()
                        return hostname if hostname and " " not in hostname else None
                    cursor += name_len
            pos += ext_len
        return None
    except (IndexError, ValueError, UnicodeDecodeError, TypeError):
        return None
    except Exception:
        return None

def parse_pcap(path: str | Path) -> list[Destination]:
    """Stream a pcap and aggregate DNS queries and TLS SNI by registrable domain."""
    grouped: dict[str, Destination] = {}
    with PcapReader(str(path)) as reader:
        for packet in reader:
            names: list[tuple[str, str]] = []
            if packet.haslayer(DNS) and packet.haslayer(DNSQR):
                dns = packet[DNS]
                if int(dns.qr) == 0:
                    try:
                        qname = dns[DNSQR].qname.decode("utf-8", errors="ignore").rstrip(".").lower()
                        if qname:
                            names.append((qname, "dns"))
                    except Exception:
                        pass
            if packet.haslayer(TCP) and packet.haslayer(Raw):
                sni = extract_sni(bytes(packet[Raw].load))
                if sni:
                    names.append((sni, "sni"))
            for host, source in names:
                try:
                    ipaddress.ip_address(host)
                    continue
                except ValueError:
                    pass
                registrable = registrable_domain(host)
                if not registrable:
                    continue
                if registrable not in grouped:
                    grouped[registrable] = Destination(domain=host, registrable=registrable)
                item = grouped[registrable]
                item.sources.add(source)
                item.hits += 1
                item.bytes_out += len(bytes(packet))
                if len(host) > len(item.domain):
                    item.domain = host
    return sorted(grouped.values(), key=lambda item: (-item.hits, item.registrable))
