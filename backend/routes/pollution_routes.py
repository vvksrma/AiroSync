from flask import Blueprint, jsonify, request, make_response
from backend.services.satellite_services import _fetch_from_api
from backend.models.database import get_db
import math
import time
import psycopg2
import psycopg2.extras

pollution = Blueprint("pollution", __name__)

def clamp(value, min_val, max_val):
    if value is None:
        return None
    try:
        v = float(value)
    except (ValueError, TypeError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return max(min_val, min(max_val, round(v, 2)))

PM25_BREAKPOINTS = [
    (0, 30, 0, 50),
    (30, 60, 51, 100),
    (60, 90, 101, 200),
    (90, 120, 201, 300),
    (120, 250, 301, 400),
    (250, float('inf'), 401, 500),
]

PM10_BREAKPOINTS = [
    (0, 50, 0, 50),
    (50, 100, 51, 100),
    (100, 250, 101, 200),
    (250, 350, 201, 300),
    (350, 430, 301, 400),
    (430, float('inf'), 401, 500),
]

SO2_BREAKPOINTS = [
    (0, 40, 0, 50),
    (41, 80, 51, 100),
    (81, 380, 101, 200),
    (381, 800, 201, 300),
    (801, 1600, 301, 400),
    (1601, 2000, 401, 500),
]

O3_BREAKPOINTS = [
    (0, 50, 0, 50),
    (51, 100, 51, 100),
    (101, 168, 101, 200),
    (169, 208, 201, 300),
    (209, 748, 301, 400),
    (749, 1000, 401, 500),
]

def calculate_sub_index(C, breakpoints):
    for bp_low, bp_high, aqi_low, aqi_high in breakpoints:
        if bp_low <= C <= bp_high:
            return ((aqi_high - aqi_low) / (bp_high - bp_low)) * (C - bp_low) + aqi_low
    return 500

def calculate_aqi(pm25, pm10, so2, o3):
    aqi_pm25 = calculate_sub_index(pm25, PM25_BREAKPOINTS)
    aqi_pm10 = calculate_sub_index(pm10, PM10_BREAKPOINTS)
    aqi_so2  = calculate_sub_index(so2, SO2_BREAKPOINTS)
    aqi_o3   = calculate_sub_index(o3, O3_BREAKPOINTS)
    return round(max(aqi_pm25, aqi_pm10, aqi_so2, aqi_o3))

def aqi_category(aqi_value):
    if aqi_value <= 50: return "Good"
    if aqi_value <= 100: return "Satisfactory"
    if aqi_value <= 200: return "Moderate"
    if aqi_value <= 300: return "Poor"
    if aqi_value <= 400: return "Very Poor"
    return "Severe"

@pollution.get("/api/air-quality/latest")
def get_air_quality():
    start_total = time.time()  # 🔥 total timer

    lat = request.args.get("lat", 27.209911)
    lon = request.args.get("lon", 77.992685)

    try:
        lat = float(lat)
        lon = float(lon)
    except:
        return jsonify({"error": "Invalid coordinates"}), 400

    # ---------------- SATELLITE FETCH ----------------
    sat_start = time.time()
    sat = None
    try:
        sat = _fetch_from_api(lat, lon)
    except Exception as e:
        print("Satellite error:", e)
    sat_end = time.time()

    pm25 = pm10 = so2 = o3 = None

    if sat:
        pm25 = clamp(sat.get("pm2_5"), 0, 300)
        pm10 = clamp(sat.get("pm10"), 0, 500)
        so2  = clamp(sat.get("so2"), 0, 1000)
        o3   = clamp(sat.get("o3"), 0, 1000)

    # fallback
    if None in (pm25, pm10, so2, o3):
        print("⚠️ Satellite failed, using fallback values")
        pm25 = pm25 or 10
        pm10 = 0 if pm10 is None else pm10
        so2  = 0 if so2 is None else so2
        o3   = 0 if o3 is None else o3

    # ---------------- AQI ----------------
    aqi_value = calculate_aqi(pm25, pm10, so2, o3)

    # ---------------- IoT FETCH ----------------
    db_start = time.time()
    iot_data = None
    conn = None

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT air, co, temp, hum, id
            FROM iot_readings
            ORDER BY id DESC LIMIT 1
        """)
        row = cur.fetchone()

        if row:
            iot_data = {
                "air": row["air"],
                "co": row["co"],
                "temp": row["temp"],
                "hum": row["hum"],
                "id": row["id"]
            }

    except Exception as e:
        print("IoT fetch error:", e)

    finally:
        if conn:
            conn.close()

    db_end = time.time()
    total_end = time.time()

    # ---------------- RESPONSE ----------------
    response = make_response(jsonify({
        "aqi": aqi_value,
        "category": aqi_category(aqi_value),
        "pollutants": {
            "pm2_5": pm25,
            "pm10": pm10,
            "so2": so2,
            "o3": o3
        },
        "iot": iot_data
    }))

    # 🔥 ADD THIS (MAIN PART)
    response.headers["Server-Timing"] = (
        f"sat;dur={(sat_end - sat_start)*1000:.1f}, "
        f"db;dur={(db_end - db_start)*1000:.1f}, "
        f"total;dur={(total_end - start_total)*1000:.1f}"
    )

    return response
    
last_request_time = 0
@pollution.post("/api/iot/ingest")
def ingest_iot():
    #rate limiter 
    global last_request_time
    now = time.time()

    if now - last_request_time < 2:
        return jsonify({"error": "Too many requests"}), 429

    last_request_time = now


    body = request.get_json(silent=True)

    if not body:
        return jsonify({"error": "Invalid JSON"}), 400

    required = ["air", "co", "temp", "hum"]
    missing = [k for k in required if k not in body]

    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400

    try:
        air = float(body["air"])
        co = float(body["co"])
        temp = float(body["temp"])
        hum = float(body["hum"])
    except:
        return jsonify({"error": "Invalid values"}), 422

    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            "INSERT INTO iot_readings (air, co, temp, hum) VALUES (%s, %s, %s, %s)",
            (air, co, temp, hum)
        )

        conn.commit()

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()

    return jsonify({"status": "saved"}), 201

@pollution.get("/api/iot/latest")
def get_latest_iot():
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT air, co, temp, hum, id
            FROM iot_readings
            ORDER BY id DESC LIMIT 1
        """)
        row = cur.fetchone()

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()

    if not row:
        return jsonify({"status": "no_data"}), 200

    return jsonify({
        "status": "ok",
        "data": {
            "air": row["air"],
            "co": row["co"],
            "temp": row["temp"],
            "hum": row["hum"],
            "id": row["id"]
        }
    }), 200