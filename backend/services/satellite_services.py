import requests

import time

CACHE = {
    "data": None,
    "timestamp": 0
}
CACHE_TTL = 60  # seconds

def _fetch_from_api(lat, lon):
    now = time.time()

    # 🔥 USE CACHE
    if CACHE["data"] and now - CACHE["timestamp"] < CACHE_TTL:
        return CACHE["data"]

    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly=pm10,pm2_5,sulphur_dioxide,ozone"
    )

    try:
        resp = requests.get(url, timeout=5)

        if resp.status_code != 200:
            return CACHE["data"]  # fallback to old data

        data = resp.json()
        hourly = data.get("hourly", {})

        def get_latest(values):
            if not values:
                return None
            for v in reversed(values):
                if v is not None:
                    return v
            return None

        result = {
            "pm10": get_latest(hourly.get("pm10")),
            "pm2_5": get_latest(hourly.get("pm2_5")),
            "so2": get_latest(hourly.get("sulphur_dioxide")),
            "o3": get_latest(hourly.get("ozone")),
        }

        # 🔥 SAVE CACHE
        CACHE["data"] = result
        CACHE["timestamp"] = now

        return result

    except:
        return CACHE["data"]