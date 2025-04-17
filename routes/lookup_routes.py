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
        print("🔍 Raw payload received:", payload)

        username = payload.get("username")
        password = payload.get("password")
        base_url = payload.get("base_url")
        student_id = payload.get("student_id")

        print("🔑 Username:", username)
        print("🔐 Password:", password)
        print("🌐 Base URL:", base_url)
        print("🎓 Student ID:", student_id)

        # Safety check
        if not base_url.startswith("https://accesscenter.roundrockisd.org"):
            return jsonify({"error": f"❌ Invalid HAC base URL: '{base_url}'"}), 400

        session = HACSession(username, password, base_url)
        success = session.switch_student(student_id)

        return jsonify({"success": success})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

