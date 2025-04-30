# login_routes.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from hac.session import HACSession

limiter = Limiter(key_func=get_remote_address)
login_bp = Blueprint("login", __name__)

@limiter.limit("5 per minute")
@login_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    base_url = data.get("base_url", "https://accesscenter.roundrockisd.org/")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    try:
        # ✅ Only call login inside try
        session = HACSession(username, password, base_url)
        session.login()  # this raises on invalid credentials
    except PermissionError:
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

    # Only reaches here if login succeeds
    token = create_access_token(identity={
        "username": username,
        "password": password,
        "base_url": base_url
    })

    return jsonify(token=token), 200
