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

    # Sample 4 timestamps across yesterday for full day coverage
    timestamps = [
        int(yesterday.replace(hour=3,  minute=0, second=0).timestamp()),
        int(yesterday.replace(hour=9,  minute=0, second=0).timestamp()),
        int(yesterday.replace(hour=15, minute=0, second=0).timestamp()),
        int(yesterday.replace(hour=21, minute=0, second=0).timestamp()),
    ]

    print(f"Fetching historic flight data for {date_str}...")

    all_flights = {}  # fr24_id -> flight record

    for ts in timestamps:
        print(f"  Querying timestamp {ts}...")
        try:
            # Use FULL endpoint which includes airline_iata, origin, destination
            data = api_get("/historic/flight-positions/full", {
                "timestamp": ts,
                "bounds": "72,34,-25,45",
                "limit": 1500
            })
            flights = data.get("data", [])
            print(f"    Got {len(flights)} flights")
            if flights and ts == timestamps[0]:
                print(f"    Sample fields: {list(flights[0].keys())}")
                print(f"    Sample: {json.dumps(flights[0], indent=2)}")
            for f in flights:
                fid = f.get("fr24_id") or f.get("id") or f.get("hex")
                if fid and fid not in all_flights:
                    all_flights[fid] = f
        except Exception as e:
            print(f"    Error: {e}")

    print(f"Total unique flights: {len(all_flights)}")

    if not all_flights:
        print("ERROR: No flights returned")
        exit(1)

    # Group by airline
    airline_flights = defaultdict(list)
    for fid, f in all_flights.items():
        airline_iata = (
            f.get("airline_iata") or
            f.get("operating_airline_iata") or
            f.get("airline") or
            ""
        ).upper().strip()

        if airline_iata in EUROPEAN_AIRLINES:
            airline_flights[EUROPEAN_AIRLINES[airline_iata]].append(f)

    print(f"Airlines matched: {dict((k, len(v)) for k,v in sorted(airline_flights.items(), key=lambda x: -len(x[1]))[:10])}")

    if not airline_flights:
        print("No European airlines matched")
        exit(1)

    sorted_airlines = sorted(airline_flights.items(), key=lambda x: len(x[1]), reverse=True)[:10]

    top10 = []
    all_routes = []

    for rank, (name, flights) in enumerate(sorted_airlines, 1):
        routes = []
        for f in flights:
            dep = (f.get("origin") or f.get("dep_iata") or f.get("departure_airport_iata") or "").strip()
            arr = (f.get("destination") or f.get("arr_iata") or f.get("arrival_airport_iata") or "").strip()
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
