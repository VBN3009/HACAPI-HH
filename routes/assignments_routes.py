from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from hac.session import HACSession
from scramble import get_credentials
import logging

logger = logging.getLogger(__name__)
assignments_bp = Blueprint("assignments", __name__, url_prefix="/api")

@assignments_bp.route("/getAssignments", methods=["GET"])
@jwt_required()
def get_assignments():
    session_id = get_jwt_identity()
    creds = get_credentials(session_id)

    if not creds:
        logger.warning(f"Session expired or credentials missing for session_id: {session_id} in /getAssignments")
        return jsonify({"error": "Session expired or credentials missing"}), 401

    username = creds.get("username")
    password = creds.get("password")
    base_url = creds.get("base_url")

    if not all([username, password, base_url]):
        logger.error(
            f"Incomplete credentials for session_id: {session_id} in /getAssignments. "
            f"Found: username?{'Y' if username else 'N'}, "
            f"password?{'Y' if password else 'N'}, "
            f"base_url?{'Y' if base_url else 'N'}"
        )
        return jsonify({"error": "Incomplete credentials found in session"}), 400

    class_name_filter = request.args.get("class") # Parameter for filtering by class name

    try:
        session = HACSession(username, password, base_url)
        if not session.login():
            logger.warning(f"HAC login failed for user: {username} in /getAssignments")
            return jsonify({"error": "HAC login failed"}), 401

        assignments_data = None
        if class_name_filter:
            logger.info(f"Fetching assignments for class: '{class_name_filter}' for user: {username}")
            assignments_data = session.get_assignment_class(class_name_filter)
        else:
            logger.info(f"Fetching all assignments for user: {username}")
            assignments_data = session.fetch_class_assignments()
            
        if assignments_data is None:
            log_msg = f"No assignments found for user: {username}"
            if class_name_filter:
                log_msg += f" (class: {class_name_filter})"
            logger.warning(log_msg)
            # 404 might be appropriate if no assignments exist vs. an error fetching them
            return jsonify({"error": "No assignments found or failed to retrieve"}), 404

        return jsonify(assignments_data), 200

    except Exception as e:
        logger.exception(f"Exception during /getAssignments for user: {username}")
        return jsonify({"error": str(e)}), 500