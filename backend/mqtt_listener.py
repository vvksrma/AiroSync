import json
import psycopg2
import os
import paho.mqtt.client as mqtt

MQTT_BROKER = "7bcd8f21ec1c4a129367d93b499fd698.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "vvksrma"
MQTT_PASS = "Vvksrma@2027"

# DB
def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT")
    client.subscribe("airosense/data")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        print("Received:", data)

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO iot_readings (air, co, temp, hum) VALUES (%s, %s, %s, %s)",
            (data["air"], data["co"], data["temp"], data["hum"])
        )

        conn.commit()
        conn.close()

    except Exception as e:
        print("Error:", e)

client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASS)

client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT)

client.loop_forever()