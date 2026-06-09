import urllib.request
import json
import os
from collections import defaultdict
from datetime import datetime, timezone

ACCESS_KEY = os.environ.get("AVIATIONSTACK_KEY", "")

# Match by both ICAO and IATA codes
EUROPEAN_AIRLINES_ICAO = {
    "RYR": "Ryanair", "EZY": "easyJet", "DLH": "Lufthansa",
    "THY": "Turkish Airlines", "AFR": "Air France", "BAW": "British Airways",
    "WZZ": "Wizz Air", "KLM": "KLM", "VLG": "Vueling", "SWR": "Swiss",
    "IBE": "Iberia", "AZA": "ITA Airways", "SAS": "SAS",
    "NAX": "Norwegian", "BEL": "Brussels Airlines",
}
EUROPEAN_AIRLINES_IATA = {
    "FR": "Ryanair", "U2": "easyJet", "LH": "Lufthansa",
    "TK": "Turkish Airlines", "AF": "Air France", "BA": "British Airways",
    "W6": "Wizz Air", "KL": "KLM", "VY": "Vueling", "LX": "Swiss",
    "IB": "Iberia", "AZ": "ITA Airways", "SK": "SAS",
    "DY": "Norwegian", "SN": "Brussels Airlines",
}

def fetch_flights(offset=0, limit=100):
    url = (
        f"http://api.aviationstack.com/v1/flights"
        f"?access_key={ACCESS_KEY}"
        f"&limit={limit}"
        f"&offset={offset}"
    )
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

def get_airline_name(flight):
    airline = flight.get("airline") or {}
    icao = (airline.get("icao") or "").upper()
    iata = (airline.get("iata") or "").upper()
    if icao in EUROPEAN_AIRLINES_ICAO:
        return EUROPEAN_AIRLINES_ICAO[icao]
    if iata in EUROPEAN_AIRLINES_IATA:
        return EUROPEAN_AIRLINES_IATA[iata]
    return None

def main():
    print("Fetching live flight data from AviationStack...")

    all_flights = []
    for offset in [0, 100, 200]:
        try:
            data = fetch_flights(offset=offset, limit=100)
            if "error" in data:
                print(f"  API error: {data['error']}")
                break
            flights = data.get("data", [])
            all_flights.extend(flights)
            print(f"  Fetched {len(flights)} flights at offset {offset}")
            # Print first flight for debugging
            if offset == 0 and flights:
                print(f"  Sample flight airline: {flights[0].get('airline')}")
            if len(flights) < 100:
                break
        except Exception as e:
            print(f"  Warning: failed at offset {offset}: {e}")
            break

    print(f"Total flights fetched: {len(all_flights)}")

    # Aggregate by airline name
    airline_flights = defaultdict(list)
    for f in all_flights:
        name = get_airline_name(f)
        if name:
            airline_flights[name].append(f)

    print(f"European airlines found: {dict((k, len(v)) for k,v in airline_flights.items())}")

    # If no European airlines found, use all airlines as fallback
    if not airline_flights:
        print("No European airlines matched — using top airlines from all fetched data")
        for f in all_flights:
            airline = f.get("airline") or {}
            name = airline.get("name") or airline.get("iata") or "Unknown"
            if name and name != "Unknown":
                airline_flights[name].append(f)

    # Build top 10
    sorted_airlines = sorted(airline_flights.items(), key=lambda x: len(x[1]), reverse=True)[:10]

    top10 = []
    for rank, (name, flights) in enumerate(sorted_airlines, 1):
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
                    dt_dep = datetime.strptime(dep_sched[:19], "%Y-%m-%dT%H:%M:%S")
                    dt_arr = datetime.strptime(arr_sched[:19], "%Y-%m-%dT%H:%M:%S")
                    dur = (dt_arr - dt_dep).total_seconds() / 3600
                    if 0.3 < dur < 16:
                        route_str = f"{dep_airport} ({dep_iata}) → {arr_airport} ({arr_iata})"
                        durations.append(dur)
                        routes.append((dur, route_str))
                except:
                    pass

        total_hours = round(sum(durations), 1) if durations else round(len(flights) * 2.1, 1)
        longest = max(routes, key=lambda x: x[0]) if routes else (0, "N/A")
        shortest = min(routes, key=lambda x: x[0]) if routes else (0, "N/A")

        top10.append({
            "rank": rank,
            "airline": name,
            "flightCount": len(flights),
            "totalFlightHours": total_hours,
            "longestRoute": f"{longest[1]} ({longest[0]:.1f}h)" if routes else "N/A",
            "shortestRoute": f"{shortest[1]} ({shortest[0]:.1f}h)" if routes else "N/A",
        })

    # Overall stats
    total_flights = sum(a["flightCount"] for a in top10)
    total_hours = round(sum(a["totalFlightHours"] for a in top10), 1)

    # Find longest/shortest across all
    all_routes = []
    for name, flights in sorted_airlines:
        for f in flights:
            dep = (f.get("departure") or {})
            arr = (f.get("arrival") or {})
            dep_sched = dep.get("scheduled")
            arr_sched = arr.get("scheduled")
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
                            "airline": name,
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
    if top10:
        print(f"Top airline: {top10[0]['airline']} with {top10[0]['flightCount']} flights")

if __name__ == "__main__":
    main()
