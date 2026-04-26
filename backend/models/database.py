import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


def get_db():
    DATABASE_URL = os.getenv("DATABASE_URL")

    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )
    load_dotenv()
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # ✅ DO NOT DROP TABLES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS iot_readings (
        id SERIAL PRIMARY KEY,
        air FLOAT,
        co FLOAT,
        temp FLOAT,
        hum FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS satellite_readings (
        id SERIAL PRIMARY KEY,
        pm10 FLOAT,
        pm2_5 FLOAT,
        so2 FLOAT,
        o3 FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()