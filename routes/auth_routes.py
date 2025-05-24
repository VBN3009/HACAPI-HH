from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from hac.session import HACSession
from scramble import get_credentials
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/api")

@auth_bp.route("/getName", methods=["GET"])
@jwt_required()
def get_name():
    session_id = get_jwt_identity()
    creds = get_credentials(session_id)

    if not creds:
        logger.warning(f"Session expired or credentials missing for session_id: {session_id} in /getName")
        return jsonify({"error": "Session expired or credentials missing"}), 401

    username = creds.get("username")
    password = creds.get("password")
    base_url = creds.get("base_url")

    if not all([username, password, base_url]):
        logger.error(
            f"Incomplete credentials for session_id: {session_id} in /getName. "
            f"Found: username?{'Y' if username else 'N'}, "
            f"password?{'Y' if password else 'N'}, "
            f"base_url?{'Y' if base_url else 'N'}"
        )
        return jsonify({"error": "Incomplete credentials found in session"}), 400

    try:
        session = HACSession(username, password, base_url)
        if not session.login():
            logger.warning(f"HAC login failed for user: {username} in /getName")
            return jsonify({"error": "HAC login failed"}), 401

        name = session.get_name()
        if name:
            logger.info(f"Successfully fetched name for user: {username}")
            return jsonify({"name": name}), 200
        else:
            logger.warning(f"Unable to fetch name for user: {username} after successful login.")
            return jsonify({"error": "Unable to fetch name"}), 404 # Name not found or empty

    except Exception as e:
        logger.exception(f"Exception during /getName for user: {username}")
        return jsonify({"error": str(e)}), 500