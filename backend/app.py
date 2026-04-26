import os
import json
import threading
import paho.mqtt.client as mqtt_client
from flask import Flask
from flask_cors import CORS
from backend.models.database import init_db, get_db

# ============ MQTT CONFIG ============
MQTT_HOST = "7bcd8f21ec1c4a129367d93b499fd698.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "vvksrma"
MQTT_PASS = "Vvksrma@2027"
TOPIC     = "airosense/data"

# ============ MQTT CALLBACKS ============
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT Subscriber connected")
        client.subscribe(TOPIC)
    else:
        print(f"❌ MQTT connect failed rc={rc}")

def on_message(client, userdata, msg):
    try:
        body = json.loads(msg.payload.decode())
        print("📡 MQTT received:", body)

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO iot_readings (air, co, temp, hum) VALUES (%s, %s, %s, %s)",
            (body["air"], body["co"], body["temp"], body["hum"])
        )
        conn.commit()
        conn.close()
        print("💾 Saved to DB")

    except Exception as e:
        print("❌ MQTT save error:", e)

# ============ MQTT THREAD ============
def start_mqtt_subscriber():
    mqttc = mqtt_client.Client()
    mqttc.username_pw_set(MQTT_USER, MQTT_PASS)
    mqttc.tls_set()
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message

    try:
        mqttc.connect(MQTT_HOST, MQTT_PORT)
        mqttc.loop_forever()
    except Exception as e:
        print(f"❌ MQTT thread error: {e}")

# ============ APP FACTORY ============
def create_app():
    app = Flask(__name__)
    CORS(app)

    from backend.routes.pollution_routes import pollution
    app.register_blueprint(pollution)

    init_db()

    @app.get("/")
    def home():
        return {"status": "ok", "message": "AiroSense API is running"}

    return app

app = create_app()

# ============ START MQTT (after app is created) ============
threading.Thread(target=start_mqtt_subscriber, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)