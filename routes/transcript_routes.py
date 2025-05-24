from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from hac.session import HACSession
from scramble import get_credentials  # From Redis
import logging

# Consistent blueprint prefix
transcript_bp = Blueprint("transcript", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

@transcript_bp.route("/getTranscript", methods=["GET"])
@jwt_required()
def get_transcript():
    session_id = get_jwt_identity()
    creds = get_credentials(session_id)

    if not creds:
        logger.warning(f"Session expired or credentials missing for session_id: {session_id} in /getTranscript")
        return jsonify({"error": "Session expired or credentials missing"}), 401

    username = creds.get("username")
    password = creds.get("password")
    base_url = creds.get("base_url") # Use "base_url" for consistency

    if not username or not password or not base_url:
        logger.error(
            f"Incomplete credentials for session_id: {session_id} in /getTranscript. "
            f"Found: username?{'Y' if username else 'N'}, "
            f"password?{'Y' if password else 'N'}, "
            f"base_url?{'Y' if base_url else 'N'}"
        )
        return jsonify({"error": "Incomplete credentials found in session"}), 400

    logger.info(f"📄 Getting transcript for user: {username}")
    try:
        session = HACSession(username, password, base_url)
        if not session.login():
            logger.warning(f"HAC login failed for user: {username} in /getTranscript")
            return jsonify({"error": "HAC login failed"}), 401

        transcript_data = session.get_transcript()

        if not transcript_data: # Or transcript_data is None, depending on HACSession behavior
            logger.warning(f"Failed to fetch transcript for user: {username}")
            return jsonify({"error": "Failed to fetch transcript"}), 500 # Or 404 if more appropriate

        return jsonify(transcript_data), 200
    except Exception as e:
        logger.exception(f"Exception during /getTranscript for user: {username}")
        return jsonify({"error": str(e)}), 500


@transcript_bp.route("/getRank", methods=["GET"])
@jwt_required()
def get_rank():
    session_id = get_jwt_identity()
    creds = get_credentials(session_id)

    if not creds:
        logger.warning(f"Session expired or credentials missing for session_id: {session_id} in /getRank")
        return jsonify({"error": "Session expired or credentials missing"}), 401

    username = creds.get("username")
    password = creds.get("password")
    base_url = creds.get("base_url") # Use "base_url" for consistency

    if not username or not password or not base_url:
        logger.error(
            f"Incomplete credentials for session_id: {session_id} in /getRank. "
            f"Found: username?{'Y' if username else 'N'}, "
            f"password?{'Y' if password else 'N'}, "
            f"base_url?{'Y' if base_url else 'N'}"
        )
        return jsonify({"error": "Incomplete credentials found in session"}), 400

    logger.info(f"📊 Getting rank for user: {username}")
    try:
        session = HACSession(username, password, base_url)
        if not session.login():
            logger.warning(f"HAC login failed for user: {username} in /getRank")
            return jsonify({"error": "HAC login failed"}), 401

        rank_data = session.get_rank()

        if not rank_data and rank_data != 0: # Assuming rank can be 0 but not None/empty if failed
            logger.warning(f"Failed to fetch rank for user: {username}")
            return jsonify({"error": "Failed to fetch rank"}), 500 # Or 404

        return jsonify(rank_data), 200

    except Exception as e:
        logger.exception(f"Exception during /getRank for user: {username}")
        return jsonify({"error": str(e)}), 500