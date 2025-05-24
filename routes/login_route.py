from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from hac.session import HACSession
from extensions import limiter
from uuid import uuid4
from scramble import store_credentials

login_bp = Blueprint("login", __name__)

@login_bp.route("/api/login", methods=["POST"], strict_slashes=False)
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    base_url = data.get("base_url", "https://accesscenter.roundrockisd.org/")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    # Attempt HAC login
    try:
        session = HACSession(username, password, base_url)
        if not session.login():
            return jsonify({"error": "Invalid credentials or HAC login failed"}), 401
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected login failure: {str(e)}"}), 500

    session_id = str(uuid4())
    user_id = str(uuid4())  # Optional: replace with actual user UUID if available

    # Store encrypted credentials securely
    try:
        store_credentials(session_id, username, password, base_url, user_id=user_id)
    except Exception as e:
        return jsonify({"error": f"Failed to store session credentials: {str(e)}"}), 500

    # Create JWT (optional: set expiration in config)
    token = create_access_token(identity=session_id, additional_claims={
        "username": username,
        "base_url": base_url,
        "user_id": user_id
    })

    return jsonify(token=token), 200
