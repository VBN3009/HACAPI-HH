from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from hac.session import HACSession
from scramble import get_credentials  # 🔐 Function to retrieve stored credentials
import logging

logger = logging.getLogger(__name__)
report_bp = Blueprint("report", __name__, url_prefix="/api")

@report_bp.route("/getReport", methods=["GET", "POST"])
@jwt_required()
def get_report():
    session_id = get_jwt_identity()
    creds = get_credentials(session_id)

    if not creds:
        logger.warning(f"Session expired or credentials missing for session_id: {session_id} in /getReport")
        return jsonify({"error": "Session expired or credentials missing"}), 401

    username = creds.get("username")
    password = creds.get("password")
    base_url = creds.get("base_url") # Consistent key name

    if not username or not password or not base_url:
        logger.error(
            f"Incomplete credentials for session_id: {session_id} in /getReport. "
            f"Found: username?{'Y' if username else 'N'}, "
            f"password?{'Y' if password else 'N'}, "
            f"base_url?{'Y' if base_url else 'N'}"
        )
        return jsonify({"error": "Incomplete credentials found in session"}), 400

    # Read student_id from either GET or POST
    student_id = None
    if request.method == "POST":
        data = request.get_json()
        if data:
            student_id = data.get("student_id")
    else: # GET request
        student_id = request.args.get("student_id")

    logger.info(f"Fetching report for user: {username}, student_id: {student_id}")
    try:
        session = HACSession(username, password, base_url)
        if not session.login():
            logger.warning(f"HAC login failed for user: {username} in /getReport")
            return jsonify({"error": "HAC login failed"}), 401

        if student_id:
            logger.info(f"Switching to student_id: {student_id} for user: {username}")
            if not session.switch_student(student_id):
                logger.warning(f"Failed to switch to student {student_id} for user: {username}")
                return jsonify({"error": f"Failed to switch to student {student_id}"}), 400

        report_data = session.get_report()
        if not report_data:
            logger.warning(f"Failed to retrieve report for user: {username}, student_id: {student_id}")
            return jsonify({"error": "Failed to retrieve report"}), 500 # Or 404 if more appropriate

        return jsonify(report_data), 200
    except Exception as e:
        logger.exception(f"Exception during /getReport for user: {username}")
        return jsonify({"error": str(e)}), 500


@report_bp.route("/getIpr", methods=["GET"])
@jwt_required() # Apply JWT protection
def get_ipr():
    session_id = get_jwt_identity()
    creds = get_credentials(session_id)

    if not creds:
        logger.warning(f"Session expired or credentials missing for session_id: {session_id} in /getIpr")
        return jsonify({"error": "Session expired or credentials missing"}), 401

    username = creds.get("username")
    password = creds.get("password")
    base_url = creds.get("base_url")

    if not username or not password or not base_url:
        logger.error(
            f"Incomplete credentials for session_id: {session_id} in /getIpr. "
            f"Found: username?{'Y' if username else 'N'}, "
            f"password?{'Y' if password else 'N'}, "
            f"base_url?{'Y' if base_url else 'N'}"
        )
        return jsonify({"error": "Incomplete credentials found in session"}), 400

    logger.info(f"Fetching IPR for user: {username}")
    try:
        session = HACSession(username, password, base_url)
        if not session.login():
            logger.warning(f"HAC login failed for user: {username} in /getIpr")
            return jsonify({"error": "HAC login failed"}), 401

        ipr_data = session.get_progress_report()
        if ipr_data is None: # Assuming get_progress_report might return None
            logger.warning(f"No IPR data found or failed to retrieve for user: {username}")
            # Consider if 404 (Not Found) is more appropriate if data truly doesn't exist vs. an error
            return jsonify({"error": "Failed to retrieve progress report"}), 500

        return jsonify(ipr_data), 200
    except Exception as e:
        logger.exception(f"Exception during /getIpr for user: {username}")
        return jsonify({"error": str(e)}), 500