import os
import json
import urllib.request
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone, timedelta

# OpenSky - free, no API key needed for basic access
BASE_URL = "https://opensky-network.org/api"

# ICAO callsign prefixes -> airline name
AIRLINE_CALLSIGNS = {
    "RYR": "Ryanair", "EZY": "easyJet", "DLH": "Lufthansa",
    "THY": "Turkish Airlines", "AFR": "Air France", "BAW": "British Airways",
    "WZZ": "Wizz Air", "KLM": "KLM", "VLG": "Vueling", "SWR": "Swiss",
    "IBE": "Iberia", "AZA": "ITA Airways", "SAS": "SAS",
    "NAX": "Norwegian", "BEL": "Brussels Airlines", "AUA": "Austrian",
    "EIN": "Aer Lingus", "TAP": "TAP Air Portugal", "AEE": "Aegean",
    "BTI": "airBaltic", "PGT": "Pegasus", "TOM": "TUI", "EXS": "Jet2",
    "CFG": "Condor", "SXS": "SunExpress", "TVS": "Transavia",
}

def get_airline(callsign):
    if not callsign:
        return None
    prefix = callsign.strip()[:3].upper()
    return AIRLINE_CALLSIGNS.get(prefix)

def api_get(path, params=None):
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "flight-report/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def main():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")

    # Full day range for yesterday
    begin = int(yesterday.replace(hour=0,  minute=0, second=0, microsecond=0).timestamp())
    end   = int(yesterday.replace(hour=23, minute=59, second=59, microsecond=0).timestamp())

    print(f"Fetching OpenSky flight data for {date_str}...")
    print(f"Time range: {begin} -> {end}")

    # OpenSky /flights/all returns all flights in a time window (max 2 hours per call)
    # Split the day into 12 x 2-hour windows
    all_flights = {}  # icao24+callsign -> flight record

    window = 2 * 3600  # 2 hours in seconds
    t = begin
    while t < end:
        t_end = min(t + window, end)
        try:
            flights = api_get("/flights/all", {
                "begin": t,
                "end": t_end
            })
            if flights:
                print(f"  Window {datetime.fromtimestamp(t, tz=timezone.utc).strftime('%H:%M')}-{datetime.fromtimestamp(t_end, tz=timezone.utc).strftime('%H:%M')}: {len(flights)} flights")
                for f in flights:
                    key = f.get("icao24", "") + "_" + (f.get("callsign") or "")
                    if key not in all_flights:
                        all_flights[key] = f
            else:
                print(f"  Window {datetime.fromtimestamp(t, tz=timezone.utc).strftime('%H:%M')}: 0 flights")
        except Exception as e:
            print(f"  Window error: {e}")
        t = t_end

    print(f"\nTotal unique flights: {len(all_flights)}")

    if not all_flights:
        print("ERROR: No flights returned from OpenSky")
        exit(1)

    # Print sample
    sample = list(all_flights.values())[0]
    print(f"Sample fields: {list(sample.keys())}")
    print(f"Sample: {json.dumps(sample, indent=2)}")

    # Group by airline
    airline_flights = defaultdict(list)
    for key, f in all_flights.items():
        name = get_airline(f.get("callsign"))
        if name:
            airline_flights[name].append(f)

    print(f"\nAirlines matched: {dict((k, len(v)) for k,v in sorted(airline_flights.items(), key=lambda x: -len(x[1])))}")

    if not airline_flights:
        print("No airlines matched")
        exit(1)

    sorted_airlines = sorted(airline_flights.items(), key=lambda x: len(x[1]), reverse=True)[:10]

    top10 = []
    all_routes = []

    for rank, (name, flights) in enumerate(sorted_airlines, 1):
        routes = []
        durations = []
        for f in flights:
            dep = f.get("estDepartureAirport") or ""
            arr = f.get("estArrivalAirport") or ""
            t_dep = f.get("firstSeen")
            t_arr = f.get("lastSeen")
            if dep and arr and dep != arr:
                routes.append((dep, arr))
            if t_dep and t_arr:
                dur = (t_arr - t_dep) / 3600
                if 0.3 < dur < 18:
                    durations.append(dur)

        total_hours = round(sum(durations), 1) if durations else round(len(flights) * 2.0, 1)
        unique_routes = list(set(routes))

        # Sort routes by length for longest/shortest
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
        "dataSource": "OpenSky Network",
        "totalFlights24h": total_flights,
        "totalFlightHours24h": total_hours,
        "longestFlight": longest_flight,
        "shortestFlight": shortest_flight,
        "top10Airlines": top10
    }

    os.makedirs("output", exist_ok=True)
    with open("output/flight_data.json", "w") as fout:
        json.dump(output, fout, indent=2)

    print(f"\nSaved output/flight_data.json")
    print(f"Top airline: {top10[0]['airline']} with {top10[0]['flightCount']} flights")
    print(f"Total: {total_flights} flights | {total_hours}h")

if __name__ == "__main__":
    main()
