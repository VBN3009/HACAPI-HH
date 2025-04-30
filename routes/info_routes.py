from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from hac.session import HACSession

info_bp = Blueprint("info", __name__)

@info_bp.route("/api/getInfo", methods=["POST"])
@jwt_required()
def get_info():
    identity = get_jwt_identity()  # this will now just be the username
    claims = get_jwt()  # this gives access to additional_claims

    user = identity
    password = claims.get("password")
    base_url = claims.get("base_url")


    session = HACSession(user, password, base_url)
    data = session.get_info()
    return jsonify(data)
