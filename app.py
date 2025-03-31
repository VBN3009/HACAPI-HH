from flask import Flask, jsonify
from flask_cors import CORS
from routes import register_routes
from dotenv import load_dotenv
from hac.session import HACSession
import os

load_dotenv()

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
            "message": "Welcome to the HAC API. Visit https://homeaccesscenterapi-docs.vercel.app/"
        })

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False, port=5000)
    username = os.getenv("HAC_USERNAME")
    password = os.getenv("HAC_PASSWORD")
    base_url = os.getenv("HAC_URL")
    session = HACSession(username, password, base_url)