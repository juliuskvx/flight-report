import os
import json
import urllib.request
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone, timedelta

API_TOKEN = os.environ.get("FR24_API_KEY", "")
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
    print(f"Fetching flight data for {date_str}...")

    airline_data = {}

    for iata, name in EUROPEAN_AIRLINES.items():
        try:
            data = api_get("/flight-summary/light", {
                "airline_icao": iata,
                "date_from": f"{date_str}T00:00:00Z",
                "date_to": f"{date_str}T23:59:59Z",
                "limit": 1000
            })
            flights = data.get("data", [])
            if flights:
                airline_data[name] = flights
                print(f"  {name}: {len(flights)} flights")
            else:
                print(f"  {name}: 0 flights")
        except Exception as e:
            print(f"  {name}: error - {e}")

    if not airline_data:
        print("No data — trying with airline_iata param instead...")
        for iata, name in EUROPEAN_AIRLINES.items():
            try:
                data = api_get("/flight-summary/light", {
                    "airline": iata,
                    "date_from": f"{date_str}T00:00:00Z",
                    "date_to": f"{date_str}T23:59:59Z",
                    "limit": 1000
                })
                flights = data.get("data", [])
                if flights:
                    airline_data[name] = flights
                    print(f"  {name}: {len(flights)} flights")
            except Exception as e:
                print(f"  {name}: error - {e}")

    if not airline_data:
        print("ERROR: No data returned from FR24 API. Check token and plan.")
        # Print a sample raw response for debugging
        try:
            data = api_get("/flight-summary/light", {
                "date_from": f"{date_str}T00:00:00Z",
                "date_to": f"{date_str}T06:00:00Z",
                "limit": 10
            })
            print(f"Raw sample response keys: {list(data.keys())}")
            if data.get("data"):
                print(f"Sample flight keys: {list(data['data'][0].keys())}")
        except Exception as e:
            print(f"Raw request error: {e}")
        exit(1)

    # Sort by flight count, take top 10
    sorted_airlines = sorted(airline_data.items(), key=lambda x: len(x[1]), reverse=True)[:10]

    top10 = []
    all_routes = []

    for rank, (name, flights) in enumerate(sorted_airlines, 1):
        durations = []
        routes = []

        for f in flights:
            dep_iata = f.get("origin") or f.get("departure_iata") or f.get("dep_iata") or "???"
            arr_iata = f.get("destination") or f.get("arrival_iata") or f.get("arr_iata") or "???"

            dep_time = f.get("actual_takeoff_time") or f.get("departure_time") or f.get("takeoff_time")
            arr_time = f.get("actual_landing_time") or f.get("arrival_time") or f.get("landing_time")

            if dep_time and arr_time:
                try:
                    if isinstance(dep_time, (int, float)):
                        dt_dep = datetime.fromtimestamp(dep_time, tz=timezone.utc)
                        dt_arr = datetime.fromtimestamp(arr_time, tz=timezone.utc)
                    else:
                        dt_dep = datetime.fromisoformat(str(dep_time).replace("Z", "+00:00"))
                        dt_arr = datetime.fromisoformat(str(arr_time).replace("Z", "+00:00"))
                    dur = (dt_arr - dt_dep).total_seconds() / 3600
                    if 0.3 < dur < 18:
                        route_str = f"{dep_iata} → {arr_iata}"
                        durations.append(dur)
                        routes.append((dur, route_str))
                        all_routes.append({"airline": name, "route": route_str, "hours": round(dur, 2)})
                except Exception as e:
                    pass

        total_hours = round(sum(durations), 1) if durations else round(len(flights) * 2.0, 1)
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

    total_flights = sum(a["flightCount"] for a in top10)
    total_hours = round(sum(a["totalFlightHours"] for a in top10), 1)
    longest_flight = max(all_routes, key=lambda x: x["hours"]) if all_routes else {"airline": "N/A", "route": "N/A", "hours": 0}
    shortest_flight = min(all_routes, key=lambda x: x["hours"]) if all_routes else {"airline": "N/A", "route": "N/A", "hours": 0}

    output = {
        "reportDate": date_str,
        "dataSource": "Flightradar24 API",
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
