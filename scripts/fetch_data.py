import os
import json
import urllib.request
import urllib.parse
import urllib.error
import base64
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta

BASE_URL = "https://opensky-network.org/api"
TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

OPENSKY_USER = os.environ.get("OPENSKY_USER", "")
OPENSKY_PASS = os.environ.get("OPENSKY_PASS", "")
OPENSKY_CLIENT_ID = os.environ.get("OPENSKY_CLIENT_ID", "")
OPENSKY_CLIENT_SECRET = os.environ.get("OPENSKY_CLIENT_SECRET", "")

print(f"Using OpenSky user: {OPENSKY_USER}")
print(f"OAuth2 client configured: {'yes' if OPENSKY_CLIENT_ID else 'no'}")

# ---------------------------------------------------------------------------
# OAuth2 token management
# ---------------------------------------------------------------------------
_token_cache = {"access_token": None, "expires_at": 0}

def get_access_token():
    """Fetch (and cache) an OAuth2 access token using client_credentials grant.
    Tokens last 30 minutes; refresh proactively after 20 minutes."""
    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    payload = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": OPENSKY_CLIENT_ID,
        "client_secret": OPENSKY_CLIENT_SECRET,
    }).encode()

    req = urllib.request.Request(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    print(f"  [auth] requesting token from {TOKEN_URL} ...")
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())
    print(f"  [auth] token response received")

    token = data["access_token"]
    expires_in = data.get("expires_in", 1800)
    _token_cache["access_token"] = token
    _token_cache["expires_at"] = now + min(expires_in - 300, expires_in * 0.66)
    print("  [auth] obtained new OAuth2 access token")
    return token

def get_auth_header():
    """Return the auth header dict, preferring OAuth2 if configured,
    falling back to Basic Auth otherwise."""
    if OPENSKY_CLIENT_ID and OPENSKY_CLIENT_SECRET:
        token = get_access_token()
        return {"Authorization": f"Bearer {token}", "User-Agent": "flight-report/1.0"}
    else:
        credentials = base64.b64encode(f"{OPENSKY_USER}:{OPENSKY_PASS}".encode()).decode()
        return {"Authorization": f"Basic {credentials}", "User-Agent": "flight-report/1.0"}

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

ICAO_TO_IATA = {
    # UK & Ireland
    "EGLL":"LHR","EGSS":"STN","EGGW":"LTN","EGKK":"LGW","EGCC":"MAN","EGGP":"LPL",
    "EGBB":"BHX","EGPH":"EDI","EGPF":"GLA","EGNX":"EMA","EGTE":"EXT","EGHI":"SOU",
    "EIDW":"DUB","EINN":"SNN","EICK":"ORK",
    # France
    "LFPG":"CDG","LFPO":"ORY","LFML":"MRS","LFMN":"NCE","LFLY":"LYS","LFBD":"BOD",
    "LFRS":"NTE","LFTW":"MPL","LFBZ":"BIQ","LFBT":"LDE","LFLL":"LYS","LFMO":"AVN",
    "LFMK":"CCF","LFMT":"MPL","LFSB":"BSL","LFST":"SXB","LFPB":"LBG",
    # Germany
    "EDDF":"FRA","EDDM":"MUC","EDDB":"BER","EDDH":"HAM","EDDK":"CGN","EDDL":"DUS",
    "EDDS":"STR","EDDG":"FMO","EDDN":"NUE","EDDT":"TXL","EDDP":"LEJ","EDDC":"DRS",
    "EDDF":"FRA","EDJA":"FDH","EDDV":"HAJ","ETSI":"IGS",
    # Netherlands
    "EHAM":"AMS","EHRD":"RTM","EHEH":"EIN",
    # Spain
    "LEMD":"MAD","LEBL":"BCN","LEPA":"PMI","LEAL":"ALC","LEMG":"AGP","LEBB":"BIO",
    "LEVC":"VLC","LEZL":"SVQ","LEGE":"GRO","LERJ":"REU","LEGR":"GRX","LEIB":"IBZ",
    "LERS":"RUS","LEMH":"MAH","LELN":"LEN","LESO":"EAS","LEAM":"LEI",
    # Canary Islands
    "GCLP":"LPA","GCFV":"FUE","GCTS":"TFS","GCXO":"TFN","GCRR":"ACE","GCLA":"SPC",
    "GCGM":"GMZ","GCHI":"VDE",
    # Italy
    "LIRF":"FCO","LIMC":"MXP","LIME":"BGY","LIRA":"CIA","LIPZ":"VCE","LIRN":"NAP",
    "LICC":"CTA","LICJ":"PMO","LIBD":"BRI","LIBF":"FOG","LIML":"LIN","LIPX":"VRN",
    "LIPT":"TSF","LIPE":"BLQ","LIPU":"PMF","LIRZ":"PEG","LICT":"TPS","LICB":"CIY",
    "LIDR":"RAN","LIPQ":"TRS","LICA":"SUF","LICG":"PNL",
    # Austria
    "LOWW":"VIE","LOWI":"INN","LOWG":"GRZ","LOWS":"SZG","LOWK":"KLU","LOXZ":"ZRS",
    # Czech Republic
    "LKPR":"PRG","LKTB":"BRQ","LKMT":"OSR",
    # Poland
    "EPWA":"WAW","EPKK":"KRK","EPGD":"GDN","EPWR":"WRO","EPKT":"KTW","EPPO":"POZ",
    "EPRZ":"RZE","EPBY":"BZG","EPLL":"LCJ","EPSC":"SZZ","EPLU":"LUZ",
    # Hungary
    "LHBP":"BUD","LHDC":"DEB",
    # Romania
    "LROP":"OTP","LRCL":"CLJ","LRTM":"TGM","LRSB":"SBZ","LRIA":"IAS","LRCK":"CND",
    # Bulgaria
    "LBSF":"SOF","LBPD":"PDV","LBWN":"VAR","LBBG":"BOJ",
    # Croatia
    "LDZA":"ZAG","LDSP":"SPU","LDDU":"DBV","LDPL":"PUY","LDZD":"ZAD",
    # Serbia & North Macedonia
    "LYBT":"BEG","LWSK":"SKP","BKPR":"PRN",
    # Turkey — comprehensive
    "LTFM":"IST","LTAI":"AYT","LTBJ":"ADB","LTAC":"ESB","LTBA":"SAW",
    "LTFE":"BJV","LTBS":"DLM","LTCG":"TZX","LTAG":"ADA","LTAN":"KYA",
    "LTAU":"VAS","LTAW":"TZX","LTAZ":"NEV","LTBF":"BAL","LTBH":"CKZ",
    "LTBL":"ADB","LTBO":"USQ","LTBQ":"KCO","LTBR":"BTC","LTBU":"TEQ",
    "LTBV":"OGU","LTBY":"ANK","LTCA":"EZS","LTCB":"OGU","LTCC":"DIY",
    "LTCD":"IGD","LTCE":"ERZ","LTCF":"KSY","LTCG":"TZX","LTCH":"SFQ",
    "LTCI":"KFS","LTCJ":"POS","LTCK":"MSR","LTCL":"SXZ","LTCM":"SIC",
    "LTCN":"KCM","LTCO":"VAN","LTCP":"GNY","LTCR":"AJI","LTCS":"CKS",
    "LTDA":"HTY","LTDB":"ISE","LTDC":"KYA","LTFE":"BJV",
    # Baltic states
    "EVRA":"RIX","EYVI":"VNO","EETN":"TLL","EVLA":"LPX","EVPA":"PNV",
    # Scandinavia & Finland
    "EFHK":"HEL","EFTU":"TKU","EFTP":"TMP","EFOU":"OUL","EFIV":"IVL",
    "ENGM":"OSL","ENBO":"BOO","ENBR":"BGO","ENKR":"KKN","ENVA":"TRD",
    "EKCH":"CPH","EKBI":"BLL","EKYT":"AAL","EKOD":"ODE","EKRN":"RNN",
    "ESSA":"ARN","ESGG":"GOT","ESMS":"MMX","ESNU":"UME","ESPE":"KRF",
    # Belgium & Luxembourg
    "EBBR":"BRU","EBCI":"CRL","ELLX":"LUX","EBAW":"ANR","EBLG":"LGG",
    # Switzerland
    "LSGG":"GVA","LSZH":"ZRH","LSZA":"LUG","LSZB":"BRN",
    # Portugal
    "LPPT":"LIS","LPPR":"OPO","LPFR":"FAO","LPPD":"PDL","LPLA":"TER",
    "LPMA":"FNC","LPFL":"FLW","LPGR":"GRW","LPHR":"HOR","LPPD":"PDL",
    # Greece
    "LGAV":"ATH","LGTS":"SKG","LGIR":"HER","LGRP":"RHO","LGKF":"EFL","LGZA":"ZTH",
    "LGKR":"CFU","LGKO":"KGS","LGHI":"JKH","LGMY":"MJT","LGKL":"KLX","LGPZ":"PVK",
    "LGAX":"AXD","LGIO":"IOA","LGKC":"KIT","LGKP":"AOK","LGLM":"LXS","LGMT":"MYK",
    "LGNX":"JNX","LGPA":"JPA","LGPL":"PPK","LGSM":"SMI","LGSO":"JSY","LGSP":"SPJ",
    "LGSR":"JTR","LGST":"JSH","LGTL":"SOH","LGTP":"KZI","LGTS":"SKG",
    # Cyprus, Israel, Iceland, Malta
    "LCLK":"LCA","LCPH":"PFO","LLBG":"TLV","BIKF":"KEF","LMML":"MLA",
    # North Africa
    "HECA":"CAI","DTMB":"MIR","DTTJ":"DJE","DTTZ":"TUN","DTTA":"TUN",
    "GMME":"RBA","GMMN":"CMN","GMAD":"AGA","DAAG":"ALG","DAOO":"ORN",
    "DAAB":"QSF","DAAS":"ABN","DABB":"AAE","DABS":"TMR","DAFH":"HME",
    # Jordan, Lebanon, Egypt extras
    "OJAI":"AMM","OLBA":"BEY","HESH":"SSH","HESN":"ASW",
}

# Routes to exclude from spotlight (same-metro / trivial pairs)
SAME_METRO_PAIRS = {
    frozenset({"AMS", "RTM"}),
    frozenset({"IST", "SAW"}),
    frozenset({"CDG", "ORY"}),
    frozenset({"BGY", "MXP"}),
    frozenset({"CIA", "FCO"}),
    frozenset({"LTN", "LHR"}),
    frozenset({"LTN", "LGW"}),
    frozenset({"STN", "LHR"}),
    frozenset({"STN", "LGW"}),
    frozenset({"CRL", "BRU"}),
    frozenset({"TSF", "VCE"}),
    frozenset({"LIN", "MXP"}),
    frozenset({"GOT", "ARN"}),  # close but distinct
}

# Max credible duration for European / intra-continental flights
MAX_FLIGHT_HOURS = 6.0
MIN_FLIGHT_HOURS = 0.25  # below this is noise or taxi-only

def is_valid_iata(code):
    return code and len(code) == 3 and code.isalpha() and code.isupper()

def icao_to_iata(icao):
    if not icao:
        return None
    return ICAO_TO_IATA.get(icao.upper())

def get_airline(callsign):
    if not callsign:
        return None
    return AIRLINE_CALLSIGNS.get(callsign.strip()[:3].upper())

def is_same_metro(dep, arr):
    return frozenset({dep, arr}) in SAME_METRO_PAIRS

def api_get(path, params=None, timeout=60, retries=3, backoff=None):
    if backoff is None:
        backoff = int(os.environ.get("DEBUG_BACKOFF", "15"))
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(1, retries + 1):
        try:
            headers = get_auth_header()
            print(f"    [api] requesting {url} ...")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (401, 403) and OPENSKY_CLIENT_ID:
                _token_cache["access_token"] = None
            if attempt < retries:
                print(f"    Attempt {attempt} failed: HTTP Error {e.code}: {e.reason} — retrying in {backoff}s...")
                time.sleep(backoff)
            else:
                raise
        except Exception as e:
            if attempt < retries:
                print(f"    Attempt {attempt} failed: {e} — retrying in {backoff}s...")
                time.sleep(backoff)
            else:
                raise

def main():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    begin = int(yesterday.replace(hour=0,  minute=0, second=0, microsecond=0).timestamp())
    end   = int(yesterday.replace(hour=23, minute=59, second=59, microsecond=0).timestamp())

    print(f"Fetching OpenSky data for {date_str}...")

    max_windows = int(os.environ.get("DEBUG_MAX_WINDOWS", "12"))

    all_flights = {}
    failed_windows = 0
    window = 2 * 3600
    t = begin
    windows_done = 0
    while t < end and windows_done < max_windows:
        t_end = min(t + window, end)
        label = datetime.fromtimestamp(t, tz=timezone.utc).strftime('%H:%M')
        try:
            flights = api_get("/flights/all", {"begin": t, "end": t_end})
            if flights:
                print(f"  {label}: {len(flights)} flights")
                for f in flights:
                    key = f.get("icao24","") + "_" + (f.get("callsign") or "")
                    if key not in all_flights:
                        all_flights[key] = f
            else:
                print(f"  {label}: 0 flights (empty response)")
        except Exception as e:
            print(f"  {label}: FAILED after {3} attempts — {e}")
            failed_windows += 1
        t = t_end
        windows_done += 1

    total_windows = windows_done
    print(f"\nTotal unique flights: {len(all_flights)}")
    print(f"Windows failed: {failed_windows}/{total_windows}")

    if failed_windows == total_windows:
        print("ERROR: All windows failed — OpenSky is unreachable today")
        exit(1)

    if not all_flights:
        print("ERROR: No flights returned")
        exit(1)

    if failed_windows > total_windows // 2:
        print(f"WARNING: More than half the windows failed — data may be incomplete")

    airline_flights = defaultdict(list)
    for key, f in all_flights.items():
        name = get_airline(f.get("callsign"))
        if name:
            airline_flights[name].append(f)

    sorted_airlines = sorted(airline_flights.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    print(f"Top airlines: {[(k, len(v)) for k,v in sorted_airlines]}")

    if not sorted_airlines:
        print("No airlines matched")
        exit(1)

    top10 = []
    all_route_durations = []  # for global longest/shortest spotlight

    for rank, (name, flights) in enumerate(sorted_airlines, 1):
        routes_with_dur = []
        route_counts = defaultdict(int)  # for most-frequent route
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
                # FIX 1: Cap at MAX_FLIGHT_HOURS to filter lastSeen noise
                if MIN_FLIGHT_HOURS < raw_dur <= MAX_FLIGHT_HOURS:
                    dur = round(raw_dur, 1)
                    total_dur += dur
                    dur_count += 1

            if dep and arr and dep != arr and is_valid_iata(dep) and is_valid_iata(arr):
                # FIX 2: Track route frequency for "most frequent route"
                route_key = f"{dep} → {arr}"
                route_counts[route_key] += 1

                # Only include routes with valid duration in the duration list
                if dur and not is_same_metro(dep, arr):
                    routes_with_dur.append((dur, dep, arr))
                    all_route_durations.append((dur, dep, arr, name))

        total_hours = round(total_dur, 1) if dur_count > 0 else round(len(flights) * 2.0, 1)

        # Longest / shortest from valid duration routes (same-metro already excluded)
        routes_with_dur.sort(key=lambda x: x[0], reverse=True)
        longest  = f"{routes_with_dur[0][1]} → {routes_with_dur[0][2]} ({routes_with_dur[0][0]:.1f}h)"  if routes_with_dur else "N/A"
        shortest = f"{routes_with_dur[-1][1]} → {routes_with_dur[-1][2]} ({routes_with_dur[-1][0]:.1f}h)" if routes_with_dur else "N/A"

        # FIX 3: Most frequent route per airline
        if route_counts:
            top_route, top_count = max(route_counts.items(), key=lambda x: x[1])
            top_route_display = f"{top_route} ({top_count}x)"
        else:
            top_route_display = "N/A"

        top10.append({
            "rank": rank,
            "airline": name,
            "flightCount": len(flights),
            "totalFlightHours": total_hours,
            "longestRoute": longest,
            "shortestRoute": shortest,
            "topRoute": top_route_display,  # NEW: most frequent route
        })

    # Global spotlight: exclude same-metro pairs AND routes below minimum duration
    all_route_durations.sort(key=lambda x: x[0], reverse=True)

    # FIX 4: Filter spotlight for same-metro and very short routes
    valid_long  = [(d,dep,arr,a) for d,dep,arr,a in all_route_durations if not is_same_metro(dep,arr)]
    valid_short = [(d,dep,arr,a) for d,dep,arr,a in reversed(all_route_durations) if not is_same_metro(dep,arr) and d >= MIN_FLIGHT_HOURS]

    if valid_long:
        lng = valid_long[0]
        longest_flight  = {"airline": lng[3], "route": f"{lng[1]} → {lng[2]}", "hours": lng[0]}
    else:
        longest_flight  = {"airline": "N/A", "route": "N/A", "hours": 0}

    if valid_short:
        sht = valid_short[0]
        shortest_flight = {"airline": sht[3], "route": f"{sht[1]} → {sht[2]}", "hours": sht[0]}
    else:
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
