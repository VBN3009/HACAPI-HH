# login_routes.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from hac.session import HACSession
from app import limiter  # Import the shared limiter instance

login_bp = Blueprint("login", __name__)

@login_bp.route("/api/login", methods=["POST"])
@limiter.limit("5 per minute")  # Apply rate limiting to the route
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    base_url = data.get("base_url", "https://accesscenter.roundrockisd.org/")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    try:
        session = HACSession(username, password, base_url)
        session.login()
        assert session.logged_in is True
    except PermissionError:
        return jsonify({"error": "Invalid credentials"}), 401
    except AssertionError:
        return jsonify({"error": "Login failed — session not authenticated"}), 401
    except Exception as e:
        return jsonify({"error": f"Unexpected login failure: {str(e)}"}), 500

    token = create_access_token(identity={
        "username": username,
        "password": password,
        "base_url": base_url
    })
    return jsonify(token=token), 200
