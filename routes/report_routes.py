from flask import Blueprint, request, jsonify
from hac.session import HACSession
import logging

logger = logging.getLogger(__name__)
report_bp = Blueprint("report", __name__)

@report_bp.route("/api/getReport", methods=["GET"])
def get_report():
    try:
        # Grab query parameters
        username = request.args.get("user")
        password = request.args.get("pass")
        link     = request.args.get("link")
        student_id = request.args.get("student_id")

        logger.info(f"📝 getReport request: user={username}, student_id={student_id}")

        if not username or not password or not link:
            return jsonify({"error": "Missing required parameters"}), 400

        session = HACSession(username, password, link)

        # 🔄 If student_id is provided, switch students before scraping
        if student_id:
            logger.info(f"🎓 Switching to student_id: {student_id}")
            success = session.switch_student(student_id)
            if not success:
                return jsonify({"error": f"Failed to switch to student {student_id}"}), 400

        report = session.get_report()

        if not report:
            return jsonify({"error": "Failed to retrieve report"}), 500

        logger.info("✅ Successfully retrieved report")
        return jsonify(report)

    except Exception as e:
        logger.exception("❌ Exception in /getReport")
        return jsonify({"error": str(e)}), 500

@report_bp.route("/api/getIpr", methods=["GET"])
def get_ipr():
    user = request.args.get('user')
    password = request.args.get('pass')
    link = request.args.get('link', 'https://accesscenter.roundrockisd.org/')

    session = HACSession(user, password, link)
    data = session.get_progress_report()
    return jsonify(data)
