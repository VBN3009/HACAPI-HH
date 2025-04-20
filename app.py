from flask import Flask, jsonify
from flask_cors import CORS
from routes import register_routes
from dotenv import load_dotenv
from hac.session import HACSession
import os
from supabase import create_client



load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def create_app():
    app = Flask(__name__)
    
    # Enable CORS for all domains (you can restrict this later)
    CORS(app)

    # Register all route blueprints
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
    base_url = os.getenv("HAC_URL")
