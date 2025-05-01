# routes/lookup_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from hac.session import HACSession
import os
import logging
import traceback
from bs4 import BeautifulSoup

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


def switch_student(self, student_id):
    if not self.logged_in:
        logger.info("🔒 Not logged in — attempting login")
        self.login()

    # Verify session is still valid
    test_url = self.base_url + "HomeAccess/Home"
    response = self.session.get(test_url, allow_redirects=False)
    if response.status_code in [301, 302] or "login" in response.text.lower():
        logger.info("🔄 Session expired, re-authenticating...")
        self.login()

    # Visit home to establish session context
    self.session.get(self.base_url + "HomeAccess/Home")

    url = self.base_url + "HomeAccess/Frame/StudentPicker"
    logger.info(f"📤 Switching to student ID: {student_id}")

    # Step 1: Load the student picker form
    response = self.session.get(url)
    if response.status_code != 200:
        logger.warning(f"❌ Failed to load StudentPicker page: {response.status_code}")
        return False

    soup = BeautifulSoup(response.text, "lxml")
    logger.debug("🧾 StudentPicker Page HTML (first 1000 chars):\n" + response.text[:1000])

    form = soup.find("form")
    if not form:
        logger.warning("❌ StudentPicker form missing — page might be incomplete or blocked.")
        return False

    payload = {}
    for input_field in form.find_all("input"):
        if input_field.get("name"):
            payload[input_field["name"]] = input_field.get("value", "")

    # Override with our specific student ID
    payload["studentId"] = student_id

    # Ensure CSRF token exists
    if "__RequestVerificationToken" not in payload:
        token_input = soup.find("input", {"name": "__RequestVerificationToken"})
        if token_input and token_input.get("value"):
            payload["__RequestVerificationToken"] = token_input["value"]
        else:
            logger.warning(f"❌ __RequestVerificationToken not found. Payload keys: {list(payload.keys())}")
            return False

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": url,
        "Origin": self.base_url.rstrip("/"),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    logger.debug(f"📤 POST payload for switch: {payload}")
    post_response = self.session.post(url, data=payload, headers=headers)
    logger.debug(f"🔁 POST response status: {post_response.status_code}")
    logger.debug(f"🔁 POST response preview:\n{post_response.text[:1000]}")

    # Attempt fallback if POST failed
    if post_response.status_code != 200:
        logger.info("⚠️ First attempt failed, trying fallback method…")
        direct_url = f"{self.base_url}HomeAccess/Frame/SwitchStudent?studentId={student_id}"
        alt_response = self.session.get(direct_url)
        logger.debug(f"🔄 Fallback GET status: {alt_response.status_code}")
        if alt_response.status_code in [200, 302]:
            logger.info("✅ Fallback method succeeded.")
            return True

    # Verify switch by checking home page
    if post_response.status_code in [200, 302]:
        verify_response = self.session.get(self.base_url + "HomeAccess/Home")
        if student_id in verify_response.text:
            logger.info("✅ Switch verified — student ID found in homepage.")
            return True
        else:
            logger.warning("❌ Switch likely failed — student ID not found in homepage.")
            return False

    logger.warning(f"❌ Student switch failed — unhandled response: {post_response.status_code}")
    return False



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
