from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from hac.session import HACSession

info_bp = Blueprint("info", __name__)

@info_bp.route("/api/getInfo", methods=["POST"])
@jwt_required()
def get_info():
    identity = get_jwt_identity()  # pulls from the token
    user = identity.get("username")
    password = identity.get("password")
    base_url = identity.get("base_url")

    session = HACSession(user, password, base_url)
    data = session.get_info()
    return jsonify(data)
