# VendorWatch

VendorWatch audits the **destinations contacted** by an app using a packet capture from your own device or a public sample capture. It extracts DNS query names and TLS ClientHello SNI, groups hosts by registrable domain, and optionally investigates vendor privacy policies.

> **Important limitation:** HTTPS payloads are encrypted. VendorWatch can show which hostnames were contacted, but it cannot see what data was sent. A network contact is not proof that data was collected, sold, stolen, or leaked. Policy conclusions are only as reliable as the retrieved policy text and verified quote.

## Features

- Parses `.pcap` and `.pcapng` files using Scapy.
- Extracts DNS query names and TLS SNI without decrypting traffic.
- Groups hostnames by registrable domain using offline `tldextract`.
- Skips investigation for domains you identify as your app's own.
- Uses TinyFish Search and Fetch to find and retrieve privacy policies.
- Optional metered TinyFish Agent fallback, disabled by default.
- Uses Claude to classify policy statements and locally verifies its evidence quote.
- Parallel vendor investigation, SQLite cache, per-vendor failure isolation.
- Streamlit dashboard, JSON download, and offline demo mode.

## Setup

Python 3.11 or newer is recommended.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and add your own keys:

```dotenv
TINYFISH_API_KEY=your_tinyfish_key
ANTHROPIC_API_KEY=your_anthropic_key
CLAUDE_MODEL=claude-sonnet-5-5
MAX_WORKERS=4
ALLOW_AGENT_FALLBACK=0
```

Never commit `.env` or share API keys. Confirm the selected Claude model is available to your Anthropic account. The TinyFish client uses defensive response parsing; verify the live API response fields against https://docs.tinyfish.ai/ on your first live run.

## Run the dashboard

```powershell
streamlit run app.py
```

Open the local URL printed by Streamlit. Enable **Demo mode** in the sidebar to explore the interface without API keys or network calls. Demo records are illustrative and are not real-time vendor findings.

## Generate a synthetic sample capture

```powershell
python scripts/make_sample_pcap.py
```

The generated capture is at `data/samples/demo.pcap`. It contains synthetic DNS queries and TLS ClientHello SNI names; it does not represent real app traffic. You can upload it in the dashboard and list `myapp.com` as an app-owned domain.

## Run tests

```powershell
pytest -q
```

Tests use mocks and synthetic packets. They do not require API keys or internet access.

## Architecture

```text
PCAP / PCAPNG
    |
    v
Scapy DPI: DNS query names + TLS ClientHello SNI
    |
    v
tldextract: registrable-domain grouping
    |
    +---- app-owned domains ---> first-party / skip
    |
    v
ThreadPoolExecutor (per vendor, isolated failures)
    |
    +--> SQLite cache
    |
    +--> known_vendors.json
    |
    +--> TinyFish Search: discover policy URL
    |
    +--> TinyFish Fetch: retrieve policy text
    |        |
    |        +--> optional TinyFish Agent fallback (metered, opt-in)
    |
    +--> Claude: strict JSON policy assessment
    |
    +--> local evidence quote verification
    |
    v
Streamlit report + JSON download
```

## Risk interpretation

- **High / medium / low** are policy-assessment labels returned by the model based on retrieved text; they are not proof of network behavior.
- **Unknown** means VendorWatch could not establish a reliable conclusion.
- **Sells/shares = Unknown** is deliberately different from No.
- Evidence is labelled verified only when the returned quote is found in the retrieved policy text after whitespace normalization and case-insensitive comparison.
- First-party means a domain matched the optional user-supplied app-domain list; it is not a legal determination.

## Limits

- DNS and SNI can be absent, encrypted (for example, encrypted DNS or ECH), or incomplete in a capture.
- A capture may include unrelated background traffic unless it was isolated to the app/device under review.
- Shared infrastructure and CDNs can serve many unrelated companies.
- Domain-to-company mappings are a convenience and may be incomplete.
- Privacy policies vary by jurisdiction, product, account type, and date. Always review the linked policy yourself.
- The current parser counts packet hits and packet lengths as observed traffic indicators; it does not attribute encrypted application payload bytes or prove a specific data transfer.
- The Agent fallback may be metered and should remain disabled unless explicitly approved.

## Cost control

1. Start with Demo mode to understand the interface.
2. Run parser-only tests before using API keys.
3. Search and Fetch are intended as the low-cost research path; check current TinyFish pricing and limits in your account.
4. SQLite caches vendor results by registrable domain (`v1:<domain>`). Delete `cache/vendorwatch.db` to clear the cache.
5. Keep `ALLOW_AGENT_FALLBACK=0` unless you intentionally want to use the metered Agent API.
6. Keep `MAX_WORKERS` conservative to avoid bursts and rate limits.

## Two-minute demo script

1. Open the dashboard with `streamlit run app.py`.
2. Enable **Demo mode** and click **Run audit**. Explain that this mode uses clearly illustrative sample data and no API calls.
3. Point to the four summary metrics and the results table.
4. Expand a high- or medium-risk row and show its evidence status and policy link.
5. Explain the honesty boundary: the capture reveals contacted hostnames, not encrypted payload contents.
6. For a live technical demo, generate `demo.pcap`, upload it, enter `myapp.com` as the first-party domain, and use configured API keys. Keep Agent fallback disabled unless the team has approved its cost.
