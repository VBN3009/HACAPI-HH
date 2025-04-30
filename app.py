from flask import Flask, jsonify
from flask_cors import CORS
from routes import register_routes
from dotenv import load_dotenv
import os
from supabase import create_client
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

#Load environment variables from .env
load_dotenv()

# Initialize limiter before app to avoid circular imports
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",  # Will be overridden by REDIS_URL if set
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window",
)

#Supabase init
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

#Flask app instance
app = Flask(__name__)

# Configure limiter with Redis if URL is set
if os.getenv("REDIS_URL"):
    limiter.storage_uri = os.getenv("REDIS_URL")

#JWT config
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hour token expiry
jwt = JWTManager(app)

def create_app():
    CORS(app)
    register_routes(app)
    limiter.init_app(app) 

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
