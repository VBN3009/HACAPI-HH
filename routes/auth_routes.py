from flask import Blueprint, request, jsonify
from hac.session import HACSession

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/api/getName", methods=["POST"])
def get_name():
    user = request.args.get('user')
    password = request.args.get('pass')
    link = request.args.get('link', 'https://accesscenter.roundrockisd.org/')
    
    session = HACSession(user, password, link)
    return jsonify({"name": session.get_name()})
