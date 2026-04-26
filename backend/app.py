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