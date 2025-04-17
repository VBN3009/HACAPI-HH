# routes/lookup_routes.py
from flask import Blueprint, request, jsonify
from hac.session import HACSession
import os

lookup_bp = Blueprint("lookup", __name__, url_prefix="/lookup")

@lookup_bp.route("/students", methods=["POST"])
def get_student_list():
    payload = request.get_json()
    username = payload.get("username")
    password = payload.get("password")
    base_url = os.getenv("HAC_URL")  # or default to "https://accesscenter.roundrockisd.org/"

    session = HACSession(username, password, base_url)
    students = session.get_students()

    return jsonify(students)
