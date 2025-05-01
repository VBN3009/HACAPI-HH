# routes/lookup_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from hac.session import HACSession
import os
import logging
import traceback

logger = logging.getLogger(__name__)

lookup_bp = Blueprint("lookup", __name__, url_prefix="/lookup")

@lookup_bp.route("/students", methods=["POST"])
@jwt_required() 
def get_student_list():
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        username = identity
        password = claims.get("password")
        base_url = claims.get("base_url") or os.getenv("HAC_URL")

        session = HACSession(username, password, base_url)
        students = session.get_students()

        if not students:
            return jsonify({"error": "No students found or login failed"}), 404

        return jsonify({"students": students}), 200

    except Exception as e:
        logger.error("Exception occurred: %s", traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@lookup_bp.route("/switch", methods=["POST"])
@jwt_required()
def switch_student():
    try:
        payload = request.get_json(force=True)
        student_id = payload.get("student_id")
        
        if not student_id:
            return jsonify({"success": False, "error": "Student ID is required"}), 400

        identity = get_jwt_identity()
        claims = get_jwt()
        username = identity
        password = claims.get("password")
        base_url = claims.get("base_url") or os.getenv("HAC_URL")

        if not base_url.endswith("/"):
            base_url += "/"

        if not base_url.startswith("https://accesscenter.roundrockisd.org"):
            return jsonify({"error": f"❌ Invalid HAC base URL: '{base_url}'"}), 400

        session = HACSession(username, password, base_url)
        
        # Initial login attempt
        if not session.login():
            return jsonify({"success": False, "error": "Initial authentication failed"}), 401

        # Verify active student
        active = session.get_active_student()
        if active and active.get("id") == student_id:
            return jsonify({"success": True, "message": "Already active student"})

        # Get and validate student list
        students = session.get_students()
        if not students:
            return jsonify({"success": False, "error": "Failed to retrieve students list"}), 400

        if student_id not in [s["id"] for s in students]:
            return jsonify({"success": False, "error": f"Student ID {student_id} not found"}), 400

        # Attempt student switch
        if session.switch_student(student_id):
            return jsonify({"success": True})
        
        return jsonify({"success": False, "error": "Failed to switch student"}), 500

    except Exception as e:
        logger.error("Exception in switch_student: %s", traceback.format_exc())
        return jsonify({"error": str(e), "success": False}), 500


@lookup_bp.route("/current", methods=["POST"])
@jwt_required()
def get_current_student():
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        username = identity
        password = claims.get("password")
        raw_base = claims.get("base_url", os.getenv("HAC_URL", ""))

        base_url = raw_base.rstrip("/") + "/"
        if not base_url.startswith("https://accesscenter.roundrockisd.org/"):
            return jsonify({"error": f"❌ Invalid HAC base URL: {base_url}"}), 400

        session = HACSession(username, password, base_url)
        active = session.get_active_student()

        if not active:
            return jsonify({"success": False, "error": "No active student found"}), 404

        return jsonify({"success": True, "active": active}), 200

    except Exception as e:
        logger.error("Exception in get_current_student: %s", traceback.format_exc())
        return jsonify({"error": str(e)}), 500
