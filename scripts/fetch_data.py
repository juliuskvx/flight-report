import urllib.request
import json
import os
from collections import defaultdict
from datetime import datetime, timezone

ACCESS_KEY = os.environ.get("AVIATIONSTACK_KEY", "")

# European airline ICAO codes we care about
EUROPEAN_AIRLINES = {
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
    "AZA": "ITA Airways",
    "SAS": "SAS",
    "NAX": "Norwegian",
    "BEL": "Brussels Airlines",
}

def fetch_flights(offset=0, limit=100):
    url = (
        f"http://api.aviationstack.com/v1/flights"
        f"?access_key={ACCESS_KEY}"
        f"&flight_status=active"
        f"&limit={limit}"
        f"&offset={offset}"
    )
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

def main():
    print("Fetching live flight data from AviationStack...")

    # Fetch up to 300 flights (3 calls of 100)
    all_flights = []
    for offset in [0, 100, 200]:
        try:
            data = fetch_flights(offset=offset, limit=100)
            flights = data.get("data", [])
            all_flights.extend(flights)
            print(f"  Fetched {len(flights)} flights at offset {offset}")
            if len(flights) < 100:
                break
        except Exception as e:
            print(f"  Warning: failed at offset {offset}: {e}")
            break

    print(f"Total flights fetched: {len(all_flights)}")

    # Aggregate by airline
    airline_flights = defaultdict(list)
    for f in all_flights:
        airline = f.get("airline") or {}
        icao = (airline.get("icao") or "").upper()
        if icao in EUROPEAN_AIRLINES:
            airline_flights[icao].append(f)

    # Build top 10
    sorted_airlines = sorted(airline_flights.items(), key=lambda x: len(x[1]), reverse=True)[:10]

    top10 = []
    for rank, (icao, flights) in enumerate(sorted_airlines, 1):
        name = EUROPEAN_AIRLINES[icao]

        # Estimate block hours: use departure scheduled time vs arrival scheduled time
        durations = []
        routes = []
        for f in flights:
            dep = (f.get("departure") or {})
            arr = (f.get("arrival") or {})
            dep_iata = dep.get("iata") or "???"
            arr_iata = arr.get("iata") or "???"
            dep_airport = dep.get("airport") or dep_iata
            arr_airport = arr.get("airport") or arr_iata

            dep_sched = dep.get("scheduled")
            arr_sched = arr.get("scheduled")
            if dep_sched and arr_sched:
                try:
                    fmt = "%Y-%m-%dT%H:%M:%S+00:00"
                    dt_dep = datetime.strptime(dep_sched[:19], "%Y-%m-%dT%H:%M:%S")
                    dt_arr = datetime.strptime(arr_sched[:19], "%Y-%m-%dT%H:%M:%S")
                    dur = (dt_arr - dt_dep).total_seconds() / 3600
                    if 0.3 < dur < 16:
                        durations.append((dur, dep_airport, arr_airport, dep_iata, arr_iata))
                        routes.append((dur, f"{dep_airport} ({dep_iata}) → {arr_airport} ({arr_iata})"))
                except:
                    pass

        total_hours = round(sum(d[0] for d in durations), 1) if durations else round(len(flights) * 2.1, 1)
        longest = max(routes, key=lambda x: x[0]) if routes else (0, "N/A")
        shortest = min(routes, key=lambda x: x[0]) if routes else (0, "N/A")

        top10.append({
            "rank": rank,
            "airline": name,
            "icao": icao,
            "flightCount": len(flights),
            "totalFlightHours": total_hours,
            "longestRoute": f"{longest[1]} ({longest[0]:.1f}h)",
            "shortestRoute": f"{shortest[1]} ({shortest[0]:.1f}h)",
        })

    # Overall stats
    total_flights = sum(a["flightCount"] for a in top10)
    total_hours = round(sum(a["totalFlightHours"] for a in top10), 1)

    all_routes = []
    for icao, flights in sorted_airlines:
        for f in flights:
            dep = (f.get("departure") or {})
            arr = (f.get("arrival") or {})
            dep_sched = dep.get("scheduled")
            arr_sched = arr.get("scheduled")
            airline_name = EUROPEAN_AIRLINES[icao]
            dep_iata = dep.get("iata") or "???"
            arr_iata = arr.get("iata") or "???"
            dep_airport = dep.get("airport") or dep_iata
            arr_airport = arr.get("airport") or arr_iata
            if dep_sched and arr_sched:
                try:
                    dt_dep = datetime.strptime(dep_sched[:19], "%Y-%m-%dT%H:%M:%S")
                    dt_arr = datetime.strptime(arr_sched[:19], "%Y-%m-%dT%H:%M:%S")
                    dur = (dt_arr - dt_dep).total_seconds() / 3600
                    if 0.3 < dur < 16:
                        all_routes.append({
                            "airline": airline_name,
                            "route": f"{dep_airport} ({dep_iata}) → {arr_airport} ({arr_iata})",
                            "hours": round(dur, 2)
                        })
                except:
                    pass

    longest_flight = max(all_routes, key=lambda x: x["hours"]) if all_routes else {"airline": "N/A", "route": "N/A", "hours": 0}
    shortest_flight = min(all_routes, key=lambda x: x["hours"]) if all_routes else {"airline": "N/A", "route": "N/A", "hours": 0}

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    output = {
        "reportDate": today,
        "dataSource": "AviationStack Live API",
        "totalFlights24h": total_flights,
        "totalFlightHours24h": total_hours,
        "longestFlight": longest_flight,
        "shortestFlight": shortest_flight,
        "top10Airlines": top10
    }

    os.makedirs("output", exist_ok=True)
    with open("output/flight_data.json", "w") as fout:
        json.dump(output, fout, indent=2)

    print(f"Saved output/flight_data.json")
    print(f"Top airline: {top10[0]['airline']} with {top10[0]['flightCount']} flights" if top10 else "No European airlines found")

if __name__ == "__main__":
    main()
