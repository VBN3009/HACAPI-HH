# routes/lookup_routes.py
from flask import Blueprint, request, jsonify
from hac.session import HACSession
import os

lookup_bp = Blueprint("lookup", __name__, url_prefix="/lookup")

@lookup_bp.route("/students", methods=["POST"])
def get_student_list():
    try:
        payload = request.get_json()
        username = payload.get("username")
        password = payload.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        base_url = os.getenv("HAC_URL", "https://accesscenter.roundrockisd.org")
        session = HACSession(username, password, base_url)

        students = session.get_students()
        if not students:
            return jsonify({"error": "No students found or login failed"}), 404

        return jsonify({"students": students}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
