import os
import json
import urllib.request
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone, timedelta

BASE_URL = "https://opensky-network.org/api"

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

# ICAO 4-letter -> IATA 3-letter for common European airports
ICAO_TO_IATA = {
    "EGLL":"LHR","EGSS":"STN","EGGW":"LTN","EGKK":"LGW","EGCC":"MAN","EGGP":"LPL",
    "EGBB":"BHX","EGPH":"EDI","EGPF":"GLA","EGNX":"EMA","EGTE":"EXT","EGHI":"SOU",
    "EIDW":"DUB","EINN":"SNN","EICK":"ORK",
    "LFPG":"CDG","LFPO":"ORY","LFML":"MRS","LFMN":"NCE","LFLY":"LYS","LFBD":"BOD",
    "LFRS":"NTE","LFTW":"MPL","LFLL":"LYS","LFBZ":"BIQ","LFBT":"LDE",
    "EDDF":"FRA","EDDM":"MUC","EDDB":"BER","EDDH":"HAM","EDDK":"CGN","EDDL":"DUS",
    "EDDS":"STR","EDDG":"FMO","EDDN":"NUE",
    "EHAM":"AMS","EHRD":"RTM",
    "LEMD":"MAD","LEBL":"BCN","LEPA":"PMI","LEAL":"ALC","LEMG":"AGP","LEBB":"BIO",
    "LEVC":"VLC","LEZL":"SVQ","LEGE":"GRO","LERJ":"REU","LEGR":"GRX","LEIB":"IBZ",
    "GCLP":"LPA","GCFV":"FUE","GCTS":"TFS","GCXO":"TFN","GCRR":"ACE","GCLA":"SPC",
    "LIRF":"FCO","LIMC":"MXP","LIME":"BGY","LIRA":"CIA","LIPZ":"VCE","LIRN":"NAP",
    "LICC":"CTA","LICJ":"PMO","LICA":"SUF","LIBP":"PSR","LIBD":"BRI","LIBF":"FOG",
    "LOWW":"VIE","LOWI":"INN","LOWG":"GRZ","LOWS":"SZG",
    "LKPR":"PRG",
    "EPWA":"WAW","EPKK":"KRK","EPGD":"GDN","EPWR":"WRO","EPKT":"KTW",
    "LHBP":"BUD",
    "LROP":"OTP","LRCL":"CLJ",
    "LBSF":"SOF",
    "LDZA":"ZAG","LDSP":"SPU","LDDU":"DBV",
    "LYBT":"BEG",
    "LWSK":"SKP",
    "LTFM":"IST","LTAI":"AYT","LTBJ":"ADB","LTAC":"ESB","LTBA":"SAW",
    "LTFE":"BJV","LTBS":"DLM","LTCG":"TZX","LTBU":"TEQ",
    "EVRA":"RIX","EYVI":"VNO","EETN":"TLL",
    "EFHK":"HEL","ENGM":"OSL","EKCH":"CPH","ESSA":"ARN","ESGG":"GOT",
    "EBBR":"BRU","EBCI":"CRL",
    "ELLX":"LUX",
    "LSGG":"GVA","LSZH":"ZRH",
    "LPPT":"LIS","LPPR":"OPO","LPFR":"FAO",
    "LGAV":"ATH","LGTS":"SKG","LGIR":"HER","LGRP":"RHO","LGKF":"EFL","LGZA":"ZTH",
    "LCLK":"LCA","LCPH":"PFO",
    "LLBG":"TLV",
    "BIKF":"KEF",
    "LMML":"MLA",
    "HECA":"CAI",
    "DTMB":"MIR","DTTJ":"DJE","DTTZ":"TUN",
    "GMME":"RBA","GMMN":"CMN","GMAD":"AGA","GMFM":"FEZ",
    "DAAG":"ALG","DAOO":"ORN",
}

# Known valid IATA codes (3 uppercase letters)
def is_valid_iata(code):
    return code and len(code) == 3 and code.isalpha() and code.isupper()

def icao_to_iata(icao):
    if not icao:
        return None
    mapped = ICAO_TO_IATA.get(icao.upper())
    if mapped:
        return mapped
    return None  # Return None instead of guessing if not in our lookup

def get_airline(callsign):
    if not callsign:
        return None
    return AIRLINE_CALLSIGNS.get(callsign.strip()[:3].upper())

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
    begin = int(yesterday.replace(hour=0,  minute=0, second=0, microsecond=0).timestamp())
    end   = int(yesterday.replace(hour=23, minute=59, second=59, microsecond=0).timestamp())

    print(f"Fetching OpenSky data for {date_str}...")

    all_flights = {}
    window = 2 * 3600
    t = begin
    while t < end:
        t_end = min(t + window, end)
        try:
            flights = api_get("/flights/all", {"begin": t, "end": t_end})
            if flights:
                label = datetime.fromtimestamp(t, tz=timezone.utc).strftime('%H:%M')
                print(f"  {label}: {len(flights)} flights")
                for f in flights:
                    key = f.get("icao24","") + "_" + (f.get("callsign") or "")
                    if key not in all_flights:
                        all_flights[key] = f
        except Exception as e:
            print(f"  Error: {e}")
        t = t_end

    print(f"Total unique flights: {len(all_flights)}")
    if not all_flights:
        print("ERROR: No flights returned")
        exit(1)

    # Group by airline
    airline_flights = defaultdict(list)
    for key, f in all_flights.items():
        name = get_airline(f.get("callsign"))
        if name:
            airline_flights[name].append(f)

    sorted_airlines = sorted(airline_flights.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    print(f"Top airlines: {[(k, len(v)) for k,v in sorted_airlines]}")

    if not airline_flights:
        print("No airlines matched")
        exit(1)

    top10 = []
    all_route_durations = []  # (dur, dep, arr, airline)

    for rank, (name, flights) in enumerate(sorted_airlines, 1):
        routes_with_dur = []
        total_dur = 0
        dur_count = 0

        for f in flights:
            dep = icao_to_iata(f.get("estDepartureAirport"))
            arr = icao_to_iata(f.get("estArrivalAirport"))
            t_dep = f.get("firstSeen")
            t_arr = f.get("lastSeen")

            dur = None
            if t_dep and t_arr:
                raw_dur = (t_arr - t_dep) / 3600
                if 0.3 < raw_dur < 16:
                    dur = round(raw_dur, 1)
                    total_dur += dur
                    dur_count += 1

            if dep and arr and dep != arr and is_valid_iata(dep) and is_valid_iata(arr):
                routes_with_dur.append((dur or 2.0, dep, arr))
                if dur:
                    all_route_durations.append((dur, dep, arr, name))

        total_hours = round(total_dur, 1) if dur_count > 0 else round(len(flights) * 2.0, 1)

        # Sort routes by duration for longest/shortest
        routes_with_dur.sort(key=lambda x: x[0], reverse=True)
        longest  = f"{routes_with_dur[0][1]} → {routes_with_dur[0][2]} ({routes_with_dur[0][0]:.1f}h)"  if routes_with_dur else "N/A"
        shortest = f"{routes_with_dur[-1][1]} → {routes_with_dur[-1][2]} ({routes_with_dur[-1][0]:.1f}h)" if routes_with_dur else "N/A"

        top10.append({
            "rank": rank,
            "airline": name,
            "flightCount": len(flights),
            "totalFlightHours": total_hours,
            "longestRoute": longest,
            "shortestRoute": shortest,
        })

    # Global longest/shortest using real durations
    all_route_durations.sort(key=lambda x: x[0], reverse=True)
    if all_route_durations:
        lng = all_route_durations[0]
        sht = all_route_durations[-1]
        longest_flight  = {"airline": lng[3], "route": f"{lng[1]} → {lng[2]}", "hours": lng[0]}
        shortest_flight = {"airline": sht[3], "route": f"{sht[1]} → {sht[2]}", "hours": sht[0]}
    else:
        longest_flight  = {"airline": "N/A", "route": "N/A", "hours": 0}
        shortest_flight = {"airline": "N/A", "route": "N/A", "hours": 0}

    total_flights = sum(a["flightCount"] for a in top10)
    total_hours   = round(sum(a["totalFlightHours"] for a in top10), 1)

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
    print(f"Top: {top10[0]['airline']} — {top10[0]['flightCount']} flights")
    print(f"Longest: {longest_flight}")
    print(f"Shortest: {shortest_flight}")
    print(f"Total: {total_flights} flights | {total_hours}h")

if __name__ == "__main__":
    main()
