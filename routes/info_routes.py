from flask import Blueprint, request, jsonify
from hac.session import HACSession
import os

info_bp = Blueprint("info", __name__)

@info_bp.route("/api/getInfo", methods=["POST"])
def get_info():
    data = request.get_json()
    user = data.get('user')
    password = data.get('pass')
    link = os.getenv("HAC_URL", "https://accesscenter.roundrockisd.org/")

    session = HACSession(user, password, link)
    data = session.get_info()
    return jsonify(data)

# Test