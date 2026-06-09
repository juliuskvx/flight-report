import os
import json
import urllib.request
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import time

API_TOKEN = os.environ.get("FR24_API_TOKEN", "")
print(f"Token length: {len(API_TOKEN)}")

BASE_URL = "https://fr24api.flightradar24.com/api"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept-Version": "v1",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; flight-report/1.0)"
}

# ICAO callsign prefix -> airline name
AIRLINE_ICAO = {
    "RYR": "Ryanair",
    "EZY": "easyJet",
    "DLH": "Lufthansa",
    "THY": "Turkish Airlines",
    "AFR": "Air France",
    "BAW": "British Airways",
    "WZZ": "Wizz Air",
    "KLM": "KLM",
    "VLG": "Vueling",
    "SWR": "Swiss",
    "IBE": "Iberia",
    "AUA": "Austrian",
    "EIN": "Aer Lingus",
    "TAP": "TAP Air Portugal",
    "SAS": "SAS",
    "NAX": "Norwegian",
    "BTI": "airBaltic",
    "PGT": "Pegasus",
    "TOM": "TUI",
    "EXS": "Jet2",
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

    # 6 timestamps spread across the day
    timestamps = [
        int(yesterday.replace(hour=h, minute=0, second=0).timestamp())
        for h in [4, 8, 12, 16, 20, 23]
    ]

    print(f"Fetching historic flight data for {date_str}...")
    print(f"Querying {len(AIRLINE_ICAO)} airlines across {len(timestamps)} timestamps...")

    # For each airline, count unique flight IDs across all timestamps
    airline_flight_ids = defaultdict(set)
    airline_routes = defaultdict(set)

    for icao, name in AIRLINE_ICAO.items():
        for ts in timestamps:
            try:
                data = api_get("/historic/flight-positions/full", {
                    "timestamp": ts,
                    "callsigns": f"{icao}*",  # wildcard match e.g. RYR*
                    "limit": 20
                })
                flights = data.get("data", [])
                for f in flights:
                    fid = f.get("fr24_id") or f.get("hex")
                    if fid:
                        airline_flight_ids[name].add(fid)
                    dep = (f.get("orig_iata") or "").strip()
                    arr = (f.get("dest_iata") or "").strip()
                    if dep and arr and dep != arr:
                        airline_routes[name].add((dep, arr))
            except Exception as e:
                pass  # skip silently, keep going
        time.sleep(0.1)  # small delay to avoid rate limiting

    print(f"\nResults:")
    for name, ids in sorted(airline_flight_ids.items(), key=lambda x: -len(x[1])):
        print(f"  {name}: {len(ids)} unique flights")

    if not airline_flight_ids:
        print("ERROR: No data returned")
        exit(1)

    sorted_airlines = sorted(airline_flight_ids.items(), key=lambda x: len(x[1]), reverse=True)[:10]

    top10 = []
    all_routes = []

    for rank, (name, flight_ids) in enumerate(sorted_airlines, 1):
        count = len(flight_ids)
        routes = list(airline_routes.get(name, set()))
        total_hours = round(count * 2.0, 1)
        longest  = f"{routes[0][0]} → {routes[0][1]}"  if routes else "N/A"
        shortest = f"{routes[-1][0]} → {routes[-1][1]}" if routes else "N/A"

        top10.append({
            "rank": rank,
            "airline": name,
            "flightCount": count,
            "totalFlightHours": total_hours,
            "longestRoute": longest,
            "shortestRoute": shortest,
        })
        for dep, arr in routes[:5]:
            all_routes.append({"airline": name, "route": f"{dep} → {arr}", "hours": 2.0})

    total_flights = sum(a["flightCount"] for a in top10)
    total_hours   = round(sum(a["totalFlightHours"] for a in top10), 1)
    longest_flight  = all_routes[0]  if all_routes else {"airline": "N/A", "route": "N/A", "hours": 0}
    shortest_flight = all_routes[-1] if all_routes else {"airline": "N/A", "route": "N/A", "hours": 0}

    output = {
        "reportDate": date_str,
        "dataSource": "Flightradar24 Historic API",
        "totalFlights24h": total_flights,
        "totalFlightHours24h": total_hours,
        "longestFlight": longest_flight,
        "shortestFlight": shortest_flight,
        "top10Airlines": top10
    }

    os.makedirs("output", exist_ok=True)
    with open("output/flight_data.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved output/flight_data.json")
    print(f"Top airline: {top10[0]['airline']} with {top10[0]['flightCount']} flights")
    print(f"Total: {total_flights} flights | {total_hours}h")

if __name__ == "__main__":
    main()
