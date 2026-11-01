
"""Application configuration loaded from the repository-root .env file."""

from pathlib import Path
import os
from dotenv import load_dotenv

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load environment variables from root .env file
load_dotenv(PROJECT_ROOT / ".env", override=True)

# --------------------------------
# TinyFish API Configuration
# --------------------------------

TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY", "").strip()

SEARCH_URL = "https://api.search.tinyfish.ai"
FETCH_URL = "https://api.fetch.tinyfish.ai"
AGENT_URL = "https://agent.tinyfish.ai/v1/automation/run-sse"

# --------------------------------
# Google Gemini Configuration
# --------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
).strip()

# --------------------------------
# Application Settings
# --------------------------------

try:
    MAX_WORKERS = max(
        1,
        min(16, int(os.getenv("MAX_WORKERS", "4")))
    )
except ValueError:
    MAX_WORKERS = 4

ALLOW_AGENT_FALLBACK = (
    os.getenv("ALLOW_AGENT_FALLBACK", "0")
    .strip()
    .lower() in {"1", "true", "yes"}
)

# --------------------------------
# Storage Configuration
# --------------------------------

CACHE_DB = PROJECT_ROOT / "cache" / "vendorwatch.db"

KNOWN_VENDORS_FILE = (
    PROJECT_ROOT / "data" / "known_vendors.json"
)

# --------------------------------
# Policy Analysis Configuration
# --------------------------------

MAX_POLICY_CHARS = 30000
