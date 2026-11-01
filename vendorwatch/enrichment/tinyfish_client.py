"""Defensive REST client for TinyFish Search, Fetch and optional Agent APIs."""
import json
from typing import Any, Optional
import requests
from vendorwatch import config

class TinyFishClient:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 45) -> None:
        self.api_key = (api_key if api_key is not None else config.TINYFISH_API_KEY).strip()
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("TINYFISH_API_KEY is missing. Add it to the project-root .env file.")
        return {"X-API-Key": self.api_key, "Accept": "application/json"}

    @staticmethod
    def _items(data: Any) -> list[dict]:
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            for key in ("results", "data", "items"):
                value = data.get(key)
                if isinstance(value, list):
                    return [x for x in value if isinstance(x, dict)]
            return [data]
        return []

    def search(self, query: str) -> list[dict]:
        response = requests.get(config.SEARCH_URL, params={"query": query},
                                headers=self._headers(), timeout=self.timeout)
        response.raise_for_status()
        return self._items(response.json())

    def fetch(self, url: str) -> Optional[str]:
        response = requests.post(config.FETCH_URL, json={"urls": [url]},
                                 headers=self._headers(), timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        items = self._items(data)
        if not items and isinstance(data, dict):
            items = [data]
        if not items:
            return None
        item = items[0]
        for key in ("markdown", "content", "text", "html"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return None

    def agent(self, url: str, goal: str) -> Optional[dict]:
        # Verify response field names against https://docs.tinyfish.ai/ on the first live run.
        response = requests.post(config.AGENT_URL, json={"url": url, "goal": goal},
                                 headers=self._headers(), timeout=self.timeout, stream=True)
        response.raise_for_status()
        last_event: Optional[dict] = None
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            raw = line[6:].strip()
            if raw == "[DONE]":
                continue
            try:
                event = json.loads(raw)
                if isinstance(event, dict):
                    last_event = event
            except json.JSONDecodeError:
                continue
        if not last_event:
            return None
        result = last_event.get("resultJson", last_event.get("result",
                 last_event.get("output", last_event)))
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                return parsed if isinstance(parsed, dict) else {"output": result}
            except json.JSONDecodeError:
                return {"output": result}
        return result if isinstance(result, dict) else {"output": result}
