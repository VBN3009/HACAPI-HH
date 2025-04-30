from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from supabase import create_client
from routes import register_routes
from extensions import limiter, jwt

# Load .env variables
load_dotenv()

# Supabase init
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def create_app():
    app = Flask(__name__)

    # JWT config
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    app.config["JWT_HEADER_NAME"] = "Authorization"
    app.config["JWT_HEADER_TYPE"] = "Bearer"

    # Redis rate limiter
    if os.getenv("REDIS_URL"):
        limiter.storage_uri = os.getenv("REDIS_URL")

    # Init extensions
    jwt.init_app(app)
    limiter.init_app(app)
    CORS(app, origins=["*"])

    # Register all routes
    register_routes(app)

    @app.route("/")
    def home():
        return jsonify({
            "success": True,
            "message": "Welcome to the HAC API."
        })

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False, port=5000)
