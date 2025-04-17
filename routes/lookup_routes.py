# routes/lookup_routes.py
from flask import Blueprint, request, jsonify
from hac.session import HACSession
import os
import logging
import traceback

logger = logging.getLogger(__name__)

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
        print("🌐 Base URL:", base_url)
        print("🎓 Student ID:", student_id)

        # Normalize the base URL
        if base_url and not base_url.endswith('/'):
            base_url += '/'

        # Safety check
        if not base_url.startswith("https://accesscenter.roundrockisd.org"):
            return jsonify({"error": f"❌ Invalid HAC base URL: '{base_url}'"}), 400

        session = HACSession(username, password, base_url)
        
        # First verify we can get students list
        students = session.get_students()
        if not students:
            return jsonify({"success": False, "error": "Failed to retrieve students list"}), 400
            
        # Verify student_id is in the list
        student_ids = [s["id"] for s in students]
        if student_id not in student_ids:
            return jsonify({"success": False, "error": f"Student ID {student_id} not found in available students: {student_ids}"}), 400

        # Now try to switch
        success = session.switch_student(student_id)

        return jsonify({"success": success})

    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print("❌ Exception:", str(e))
        print("❌ Traceback:", traceback_str)
        return jsonify({"error": str(e)}), 500

@lookup_bp.route("/current", methods=["POST"])
def get_current_student():
    try:
        payload = request.get_json(force=True)
        print("🔍 [current] Raw payload:", payload)

        username = payload.get("username")
        password = payload.get("password")
        raw_base = payload.get("base_url", os.getenv("HAC_URL", ""))

        print(f"🔑 [current] username={username!r}  password={'*'*len(password) if password else None}")
        print(f"🌐 [current] raw_base_url={raw_base!r}")

        base_url = raw_base.rstrip("/") + "/"
        print(f"🛠️ [current] normalized base_url={base_url!r}")

        if not base_url.startswith("https://accesscenter.roundrockisd.org/"):
            return jsonify({"error": f"❌ Invalid HAC base URL: {base_url}"}), 400

        session = HACSession(username, password, base_url)

        print("📥 [current] fetching active student…")
        active = session.get_active_student()
        print("📥 [current] got active:", active)

        if not active:
            return jsonify({"success": False, "error": "No active student found"}), 404

        return jsonify({"success": True, "active": active}), 200

    except Exception as e:
        print("❌ [current] Exception:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
