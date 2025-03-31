from flask import Blueprint, request, jsonify
from hac.session import HACSession

grades_bp = Blueprint("grades", __name__)

@grades_bp.route("/api/getAverages", methods=["GET"])
def get_averages():
    user = request.args.get('user')
    password = request.args.get('pass')
    link = request.args.get('link', 'https://accesscenter.roundrockisd.org/')

    session = HACSession(user, password, link)
    data = session.get_averages()
    return jsonify(data)
