from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from hac.session import HACSession
from scramble import get_credentials
import logging

logger = logging.getLogger(__name__)
lookup_bp = Blueprint("lookup", __name__, url_prefix="/lookup")

def _get_hac_session_from_jwt():
    """Helper to get credentials and initialize/login to HAC session."""
    session_id = get_jwt_identity()
    creds = get_credentials(session_id)

    if not creds:
        logger.warning(f"Session expired/missing credentials for session_id: {session_id}")
        return None, (jsonify({"error": "Session expired or credentials missing"}), 401)

    username = creds.get("username")
    password = creds.get("password")
    base_url = creds.get("base_url")

    if not all([username, password, base_url]):
        logger.error(f"Incomplete credentials for session_id: {session_id}")
        return None, (jsonify({"error": "Incomplete credentials found in session"}), 400)

    try:
        hac_session = HACSession(username, password, base_url)
        if not hac_session.login():
            logger.warning(f"HAC login failed for user: {username}")
            return None, (jsonify({"error": "HAC login failed"}), 401)
        return hac_session, None
    except Exception as e:
        logger.exception(f"Error during HAC session setup for user: {username}")
        return None, (jsonify({"error": str(e)}), 500)


@lookup_bp.route("/students", methods=["GET"])
@jwt_required()
def get_student_list():
    hac_session, error_response = _get_hac_session_from_jwt()
    if error_response:
        return error_response

    try:
        students = hac_session.get_students()
        if not students:
            logger.info(f"No students found for user: {hac_session.username}")
            return jsonify({"error": "No students found"}), 404
        return jsonify({"students": students}), 200
    except Exception as e:
        logger.exception(f"Error in /lookup/students for user: {hac_session.username if hac_session else 'unknown'}")
        return jsonify({"error": str(e)}), 500


@lookup_bp.route("/switch", methods=["POST"])
@jwt_required()
def switch_student():
    hac_session, error_response = _get_hac_session_from_jwt()
    if error_response:
        return error_response

    data = request.get_json()
    if not data or "student_id" not in data:
        return jsonify({"success": False, "error": "Missing student_id in request body"}), 400
    student_id_to_switch = data.get("student_id")

    try:
        success = hac_session.switch_student(student_id_to_switch)
        if success:
            logger.info(f"Switched to student_id: {student_id_to_switch} for user: {hac_session.username}")
            return jsonify({"success": True, "message": f"Switched to student {student_id_to_switch}"}), 200
        else:
            logger.warning(f"Failed to switch to student_id: {student_id_to_switch} for user: {hac_session.username}")
            return jsonify({"success": False, "error": f"Failed to switch to student ID {student_id_to_switch}"}), 400
    except Exception as e:
        logger.exception(f"Error in /lookup/switch for user: {hac_session.username}")
        return jsonify({"error": str(e)}), 500


@lookup_bp.route("/current", methods=["GET"])
@jwt_required()
def get_current_student():
    hac_session, error_response = _get_hac_session_from_jwt()
    if error_response:
        return error_response

    try:
        active_student = hac_session.get_active_student()
        if not active_student:
            logger.info(f"No active student found for user: {hac_session.username}")
            return jsonify({"success": False, "error": "No active student found"}), 404
        return jsonify({"success": True, "active_student": active_student}), 200
    except Exception as e:
        logger.exception(f"Error in /lookup/current for user: {hac_session.username}")
        return jsonify({"error": str(e)}), 500