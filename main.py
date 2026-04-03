from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests, re, math
from datetime import datetime, timezone, timedelta

app = FastAPI()

# Autoriser ton site (ou tout le monde)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

def query(target, center):
    now = datetime.now(timezone.utc)
    t0 = now.strftime("%Y-%m-%d %H:%M")
    t1 = (now + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M")

    params = {
        "format": "json",
        "COMMAND": f"'{target}'",
        "CENTER": f"'500@{center}'",
        "EPHEM_TYPE": "VECTORS",
        "VEC_TABLE": "3",
        "START_TIME": f"'{t0}'",
        "STOP_TIME": f"'{t1}'",
        "STEP_SIZE": "'1 m'",
        "OUT_UNITS": "KM-S",
        "OBJ_DATA": "NO",
        "CSV_FORMAT": "YES",
    }

    r = requests.get(HORIZONS_URL, params=params, timeout=10)
    raw = r.json()["result"]

    m = re.search(r"\$\$SOE(.*?)\$\$EOE", raw, re.DOTALL)
    if not m:
        return None

    for line in m.group(1).split("\n"):
        parts = line.strip().split(",")
        if len(parts) < 11:
            continue
        try:
            return {
                "vx": float(parts[5]),
                "vy": float(parts[6]),
                "vz": float(parts[7]),
                "RG": float(parts[9]),
            }
        except:
            continue
    return None


@app.get("/data")
def get_data():
    try:
        earth = query("-1024", "399")
        moon  = query("-1024", "301")

        if not earth:
            return {"error": "earth failed"}

        speed_kms = math.sqrt(
            earth["vx"]**2 +
            earth["vy"]**2 +
            earth["vz"]**2
        )

        return {
            "earth": earth["RG"],
            "moon": moon["RG"] if moon else None,
            "speed_kmh": speed_kms * 3600,
            "speed_kms": speed_kms,
            "time": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        return {"error": str(e)}