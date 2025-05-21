# login_routes.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from hac.session import HACSession
from extensions import limiter


login_bp = Blueprint("login", __name__)
# Test
@login_bp.route("/api/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    base_url = data.get("base_url", "https://accesscenter.roundrockisd.org/") # Default if not provided

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    if not base_url: # Explicitly check if base_url somehow became empty
        return jsonify({"error": "Missing base_url"}), 400

    try:
        session = HACSession(username, password, base_url)
        if not session.login(): # More explicit check
            # Login method itself logs errors, check for specific error messages if needed
            return jsonify({"error": "Invalid credentials or HAC login failed"}), 401
        # assert session.logged_in is True # session.login() now returns True/False
    except ValueError as ve: # Catch invalid base_url from HACSession constructor
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        # Consider logging 'e' for server-side diagnostics
        return jsonify({"error": f"Unexpected login failure: {str(e)}"}), 500

    token = create_access_token(identity=username, additional_claims={
        "password": password,
        "base_url": base_url
    })

    return jsonify(token=token), 200