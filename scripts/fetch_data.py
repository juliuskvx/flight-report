import os
import json
import urllib.request
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone, timedelta

API_TOKEN = os.environ.get("FR24_API_TOKEN", "")
print(f"Token length: {len(API_TOKEN)}")
print(f"Token starts with: {API_TOKEN[:20] if API_TOKEN else 'EMPTY'}")

BASE_URL = "https://fr24api.flightradar24.com/api"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept-Version": "v1",
    "Content-Type": "application/json"
}

EUROPEAN_AIRLINES = {
    "FR": "Ryanair", "U2": "easyJet", "LH": "Lufthansa",
    "TK": "Turkish Airlines", "AF": "Air France", "BA": "British Airways",
    "W6": "Wizz Air", "KL": "KLM", "VY": "Vueling", "LX": "Swiss",
    "IB": "Iberia", "AZ": "ITA Airways", "SK": "SAS",
    "DY": "Norwegian", "SN": "Brussels Airlines", "OS": "Austrian",
    "EI": "Aer Lingus", "TP": "TAP Air Portugal", "A3": "Aegean",
    "BT": "airBaltic", "PC": "Pegasus",
}

def api_get(path, params=None):
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def main():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    # Use midday yesterday as timestamp
    timestamp = int(yesterday.replace(hour=12, minute=0, second=0).timestamp())
    print(f"Fetching historic flight data for {date_str} (timestamp: {timestamp})...")

    airline_counts = {}

    for iata, name in EUROPEAN_AIRLINES.items():
        try:
            data = api_get("/historic/flight-positions/light", {
                "timestamp": timestamp,
                "airline_icao": iata,
                "bounds": "72,34,-25,45",  # Europe
                "limit": 1000
            })
            flights = data.get("data", [])
            if flights:
                airline_counts[name] = len(flights)
                print(f"  {name}: {len(flights)} flights")
            else:
                # Try with airline_iata
                data2 = api_get("/historic/flight-positions/light", {
                    "timestamp": timestamp,
                    "airline": iata,
                    "bounds": "72,34,-25,45",
                    "limit": 1000
                })
                flights2 = data2.get("data", [])
                if flights2:
                    airline_counts[name] = len(flights2)
                    print(f"  {name}: {len(flights2)} flights")
                else:
                    print(f"  {name}: 0 flights")
        except Exception as e:
            print(f"  {name}: error - {e}")

    # If nothing worked, print debug info
    if not airline_counts:
        print("No data — printing raw response for debug...")
        try:
            data = api_get("/historic/flight-positions/light", {
                "timestamp": timestamp,
                "bounds": "72,34,-25,45",
                "limit": 5
            })
            print(f"Response keys: {list(data.keys())}")
            if data.get("data"):
                print(f"Sample fields: {list(data['data'][0].keys())}")
                print(f"Sample record: {json.dumps(data['data'][0], indent=2)}")
        except Exception as e:
            print(f"Debug request error: {e}")
        exit(1)

    sorted_airlines = sorted(airline_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    top10 = []
    for rank, (name, count) in enumerate(sorted_airlines, 1):
        top10.append({
            "rank": rank,
            "airline": name,
            "flightCount": count,
            "totalFlightHours": round(count * 2.0, 1),
            "longestRoute": "N/A",
            "shortestRoute": "N/A",
        })

    total_flights = sum(a["flightCount"] for a in top10)
    total_hours = round(sum(a["totalFlightHours"] for a in top10), 1)

    output = {
        "reportDate": date_str,
        "dataSource": "Flightradar24 Historic API",
        "totalFlights24h": total_flights,
        "totalFlightHours24h": total_hours,
        "longestFlight": {"airline": top10[0]["airline"], "route": "N/A", "hours": 0},
        "shortestFlight": {"airline": top10[-1]["airline"], "route": "N/A", "hours": 0},
        "top10Airlines": top10
    }

    os.makedirs("output", exist_ok=True)
    with open("output/flight_data.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved output/flight_data.json")
    print(f"Top airline: {top10[0]['airline']} with {top10[0]['flightCount']} flights")

if __name__ == "__main__":
    main()
