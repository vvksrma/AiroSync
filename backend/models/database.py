import psycopg2
import os

def get_db():
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        raise Exception("DATABASE_URL not set")

    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS iot_readings (
        id SERIAL PRIMARY KEY,
        air REAL,
        co REAL,
        temp REAL,
        hum REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS satellite_readings (
        id SERIAL PRIMARY KEY,
        pm10 REAL,
        pm2_5 REAL,
        so2 REAL,
        o3 REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()