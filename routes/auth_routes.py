from flask import Blueprint, request, jsonify
from hac.session import HACSession
import os

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/api/getName", methods=["POST"])
def get_name():
    data = request.get_json()
    user = data.get('user')
    password = data.get('pass')
    link = os.getenv("HAC_URL", "https://accesscenter.roundrockisd.org/")  # use default or env

    if not user or not password:
        return jsonify({"error": "Missing username or password"}), 400

    try:
        session = HACSession(user, password, link)
        name = session.get_name()
        if name:
            return jsonify({"name": name})
        else:
            return jsonify({"error": "Unable to fetch name"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
