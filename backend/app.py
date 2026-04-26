import os
from flask import Flask
from flask_cors import CORS
from backend.models.database import init_db

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)