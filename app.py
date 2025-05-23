from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from routes import register_routes
from dotenv import load_dotenv
from hac.session import HACSession
import os
from supabase import create_client
from flask_jwt_extended import JWTManager

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key")  # Change in prod

    # 🔐 Initialize JWTManager
    from flask_jwt_extended import JWTManager
    jwt = JWTManager(app)

    # Fix headers so request.is_secure works behind Render's proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Enable CORS for all domains (can restrict later)
    CORS(app)

    # Register all your routes
    register_routes(app)

    # Enforce HTTPS redirect for all incoming requests (only in prod)
    if os.getenv("FLASK_ENV") != "development":
        @app.before_request
        def enforce_https():
            if not request.is_secure:
                return redirect(request.url.replace("http://", "https://"), code=301)

    @app.route("/")
    def home():
        return jsonify({
            "success": True,
            "message": "Welcome to the HAC API."
        })

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)