import os
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone, timedelta

API_TOKEN = os.environ.get("FR24_API_TOKEN", "")
print(f"Token length: {len(API_TOKEN)}")

BASE_URL = "https://fr24api.flightradar24.com/api"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept-Version": "v1",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; flight-report/1.0)"
}

def api_get(path, params=None):
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    print(f"Requesting: {url[:100]}")
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"Status: {resp.status}")
            print(f"Headers: {dict(resp.headers)}")
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        print(f"Response headers: {dict(e.headers)}")
        body = e.read().decode()
        print(f"Response body: {body[:500]}")
        raise

def main():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    timestamp = int(yesterday.replace(hour=12, minute=0, second=0).timestamp())

    try:
        data = api_get("/historic/flight-positions/light", {
            "timestamp": timestamp,
            "bounds": "72,34,-25,45",
            "limit": 5
        })
        print(f"Success! Keys: {list(data.keys())}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    main()
