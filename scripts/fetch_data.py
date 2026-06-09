import os
import json
import urllib.request
import urllib.parse
from collections import defaultdict
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

# ICAO callsign prefix -> airline name
AIRLINE_ICAO = {
    "RYR": "Ryanair", "EZY": "easyJet", "DLH": "Lufthansa",
    "THY": "Turkish Airlines", "AFR": "Air France", "BAW": "British Airways",
    "WZZ": "Wizz Air", "KLM": "KLM", "VLG": "Vueling", "SWR": "Swiss",
    "IBE": "Iberia", "AZA": "ITA Airways", "SAS": "SAS",
    "NAX": "Norwegian", "BEL": "Brussels Airlines", "AUA": "Austrian",
    "EIN": "Aer Lingus", "TAP": "TAP Air Portugal", "AEE": "Aegean",
    "BTI": "airBaltic", "PGT": "Pegasus", "TOM": "TUI", "EXS": "Jet2",
    "CFG": "Condor", "GWI": "Germanwings", "SXS": "SunExpress",
}

def api_get(path, params=None):
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def get_airline_from_callsign(callsign):
    if not callsign:
        return None
    prefix = callsign[:3].upper()
    return AIRLINE_ICAO.get(prefix)

def main():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")

    # Query every 2 hours across yesterday = 12 snapshots
    # Use offset pagination to get more than 20 flights per snapshot
    timestamps = [
        int(yesterday.replace(hour=h, minute=0, second=0).timestamp())
        for h in [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
    ]

    print(f"Fetching historic flight data for {date_str}...")

    all_flights = {}  # fr24_id -> flight record

    for ts in timestamps:
        # Paginate with offsets to get more flights per timestamp
        for offset in [0, 20, 40, 60, 80]:
            try:
                data = api_get("/historic/flight-positions/full", {
                    "timestamp": ts,
                    "bounds": "72,34,-25,45",
                    "limit": 20,
                    "offset": offset
                })
                flights = data.get("data", [])
                if not flights:
                    break
                for f in flights:
                    fid = f.get("fr24_id") or f.get("hex")
                    if fid and fid not in all_flights:
                        all_flights[fid] = f
                if len(flights) < 20:
                    break
            except Exception as e:
                print(f"  Error ts={ts} offset={offset}: {e}")
                break

    print(f"Total unique flights: {len(all_flights)}")

    # Group by airline using callsign prefix
    airline_flights = defaultdict(list)
    unmatched_callsigns = set()

    for fid, f in all_flights.items():
        callsign = f.get("callsign") or ""
        name = get_airline_from_callsign(callsign)
        if name:
            airline_flights[name].append(f)
        else:
            if callsign:
                unmatched_callsigns.add(callsign[:3])

    print(f"Airlines matched: {dict((k, len(v)) for k,v in sorted(airline_flights.items(), key=lambda x: -len(x[1])))}")
    print(f"Unmatched prefixes (sample): {list(unmatched_callsigns)[:20]}")

    if not airline_flights:
        print("No airlines matched — check unmatched prefixes above")
        exit(1)

    sorted_airlines = sorted(airline_flights.items(), key=lambda x: len(x[1]), reverse=True)[:10]

    top10 = []
    all_routes = []

    for rank, (name, flights) in enumerate(sorted_airlines, 1):
        routes = []
        for f in flights:
            dep = (f.get("orig_iata") or "").strip()
            arr = (f.get("dest_iata") or "").strip()
            if dep and arr and dep != arr:
                routes.append((dep, arr))

        total_hours = round(len(flights) * 2.0, 1)
        unique_routes = list(set(routes))
        longest  = f"{unique_routes[0][0]} → {unique_routes[0][1]}"  if unique_routes else "N/A"
        shortest = f"{unique_routes[-1][0]} → {unique_routes[-1][1]}" if unique_routes else "N/A"

        top10.append({
            "rank": rank,
            "airline": name,
            "flightCount": len(flights),
            "totalFlightHours": total_hours,
            "longestRoute": longest,
            "shortestRoute": shortest,
        })

        for dep, arr in unique_routes[:5]:
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
