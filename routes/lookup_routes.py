# routes/lookup_routes.py
from flask import Blueprint, request, jsonify
from hac.session import HACSession
import os

lookup_bp = Blueprint("lookup", __name__, url_prefix="/lookup")

@lookup_bp.route("/students", methods=["POST"])
def get_student_list():
    try:
        print("Raw content type:", request.content_type)
        print("Raw data received:", request.data)

        payload = request.get_json(force=True)
        print("Parsed JSON payload:", payload)

        username = payload.get("username")
        password = payload.get("password")
        base_url = payload.get("base_url") or os.getenv("HAC_URL", "https://accesscenter.roundrockisd.org")

        print("Username:", username)
        print("Password:", password)
        print("Base URL:", base_url)

        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        session = HACSession(username, password, base_url)

        students = session.get_students()
        print("Students:", students)

        if not students:
            return jsonify({"error": "No students found or login failed"}), 404

        return jsonify({"students": students}), 200

    except Exception as e:
        print("💥 Exception occurred:", e)
        return jsonify({"error": str(e)}), 500
    
@lookup_bp.route("/switch", methods=["POST"])
def switch_student():
    try:
        payload = request.get_json(force=True)
        username = payload.get("username")
        password = payload.get("password")
        student_id = payload.get("student_id")

        if not username or not password or not student_id:
            return jsonify({"error": "Username, password, and student ID required"}), 400

        base_url = os.getenv("HAC_URL", "https://accesscenter.roundrockisd.org")
        session = HACSession(username, password, base_url)

        switched = session.switch_student(student_id)
        if not switched:
            return jsonify({"error": "Failed to switch student"}), 500

        return jsonify({"success": True, "message": f"Switched to student ID {student_id}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

