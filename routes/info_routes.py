from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from hac.session import HACSession
from scramble import get_credentials
import logging

logger = logging.getLogger(__name__)
info_bp = Blueprint("info", __name__, url_prefix="/api")

@info_bp.route("/getInfo", methods=["GET"])
@jwt_required()
def get_info():
    session_id = get_jwt_identity()
    creds = get_credentials(session_id)

    if not creds:
        logger.warning(f"Session expired or credentials missing for session_id: {session_id} in /getInfo")
        return jsonify({"error": "Session expired or credentials missing"}), 401

    username = creds.get("username")
    password = creds.get("password")
    base_url = creds.get("base_url")

    if not all([username, password, base_url]):
        logger.error(
            f"Incomplete credentials for session_id: {session_id} in /getInfo. "
            f"Found: username?{'Y' if username else 'N'}, "
            f"password?{'Y' if password else 'N'}, "
            f"base_url?{'Y' if base_url else 'N'}"
        )
        return jsonify({"error": "Incomplete credentials found in session"}), 400

    try:
        session = HACSession(username, password, base_url)
        if not session.login():
            logger.warning(f"HAC login failed for user: {username} in /getInfo")
            return jsonify({"error": "HAC login failed"}), 401

        info_data = session.get_info()
        if info_data is None: # Assuming get_info might return None on failure or no data
            logger.warning(f"Failed to retrieve info or no info found for user: {username}")
            return jsonify({"error": "Failed to retrieve information"}), 404 # Or 500 depending on expectation

        return jsonify(info_data), 200

    except Exception as e:
        logger.exception(f"Exception during /getInfo for user: {username}")
        return jsonify({"error": str(e)}), 500