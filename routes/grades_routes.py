from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from hac.session import HACSession
from scramble import get_credentials
import logging

logger = logging.getLogger(__name__)
grades_bp = Blueprint("grades", __name__, url_prefix="/api")

@grades_bp.route("/getAverages", methods=["GET"])
@jwt_required()
def get_averages():
    session_id = get_jwt_identity()
    creds = get_credentials(session_id)

    if not creds:
        logger.warning(f"Session expired or credentials missing for session_id: {session_id} in /getAverages")
        return jsonify({"error": "Session expired or credentials missing"}), 401

    username = creds.get("username")
    password = creds.get("password")
    base_url = creds.get("base_url")

    if not all([username, password, base_url]):
        logger.error(
            f"Incomplete credentials for session_id: {session_id} in /getAverages. "
            f"Found: username?{'Y' if username else 'N'}, "
            f"password?{'Y' if password else 'N'}, "
            f"base_url?{'Y' if base_url else 'N'}"
        )
        return jsonify({"error": "Incomplete credentials found in session"}), 400

    try:
        session = HACSession(username, password, base_url)
        if not session.login():
            logger.warning(f"HAC login failed for user: {username} in /getAverages")
            return jsonify({"error": "HAC login failed"}), 401

        averages_data = session.get_averages()
        if averages_data is None: # Or check if it's an empty collection if that's a failure case
            logger.warning(f"Failed to retrieve averages or no averages found for user: {username}")
            # 404 if no data is expected, 500 if it implies an error
            return jsonify({"error": "Failed to retrieve averages"}), 404

        return jsonify(averages_data), 200

    except Exception as e:
        logger.exception(f"Exception during /getAverages for user: {username}")
        return jsonify({"error": str(e)}), 500