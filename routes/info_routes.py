from flask import Blueprint, request, jsonify
from hac.session import HACSession

info_bp = Blueprint("info", __name__)

@info_bp.route("/api/getInfo", methods=["GET"])
def get_info():
    user = request.args.get('user')
    password = request.args.get('pass')
    link = request.args.get('link', 'https://accesscenter.roundrockisd.org/')

    session = HACSession(user, password, link)
    data = session.get_info()
    return jsonify(data)
