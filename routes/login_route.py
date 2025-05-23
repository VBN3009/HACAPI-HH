from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from hac.session import HACSession
from extensions import limiter

login_bp = Blueprint("login", __name__)

@login_bp.route("/api/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    base_url = data.get("base_url", "https://accesscenter.roundrockisd.org/")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    try:
        session = HACSession(username, password, base_url)
        if not session.login():
            return jsonify({"error": "Invalid credentials or HAC login failed"}), 401
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected login failure: {str(e)}"}), 500

    # Only include non-sensitive metadata
    token = create_access_token(identity=username, additional_claims={
        "base_url": base_url
    })

    return jsonify(token=token), 200
