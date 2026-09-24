import requests
from .config import Config

class MassiveClient:
    BASE_URL = "https://api.massive.com"
    def __init__(self, config=None): self.config = config or Config()
    def daily_bars(self, ticker, start, end):
        if not self.config.massive_api_key: raise RuntimeError("MASSIVE_API_KEY is not configured")
        url = f"{self.BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        r = requests.get(url, params={"adjusted":"true","sort":"asc","apiKey":self.config.massive_api_key}, timeout=30)
        r.raise_for_status()
        return r.json()
