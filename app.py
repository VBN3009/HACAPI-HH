from flask import Flask, jsonify
from flask_cors import CORS
from routes import register_routes
from dotenv import load_dotenv
import os
from supabase import create_client
from extensions import limiter, jwt

#Load environment variables from .env
load_dotenv()

#Supabase init
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

#Flask app instance
app = Flask(__name__)

#JWT config
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hour token expiry

# Configure limiter with Redis if URL is set
if os.getenv("REDIS_URL"):
    limiter.storage_uri = os.getenv("REDIS_URL")

# Initialize extensions
jwt.init_app(app)
limiter.init_app(app)

# CORS: Restrict this to your Chrome Extension ID later
CORS(app, origins=["*"])

def create_app():
    CORS(app)
    register_routes(app)

    @app.route("/")
    def home():
        return jsonify({
            "success": True,
            "message": "Welcome to the HAC API."
        })

    return app

# Entry point
if __name__ == "__main__":
    app = create_app()
    app.run(debug=False, port=5000)
