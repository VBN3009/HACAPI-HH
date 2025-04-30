# login_routes.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from hac.session import HACSession  # your existing login logic

# Setup limiter
limiter = Limiter(key_func=get_remote_address)

# Create blueprint
login_bp = Blueprint("login", __name__)

@limiter.limit("5 per minute")  # Protect against brute force
@login_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # Validate input
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    try:
        # Attempt login using your existing session logic
        session = HACSession(username, password)
        session.login()  # This will raise if login fails
    except PermissionError:
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

    # If login succeeded, return a signed token
    token = create_access_token(identity={
        "username": username,
        "password": password
    })

    return jsonify(token=token), 200
