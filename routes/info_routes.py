from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from hac.session import HACSession

info_bp = Blueprint("info", __name__)

@info_bp.route("/api/getInfo", methods=["POST"])
@jwt_required()
def get_info():
    creds = get_jwt_identity()
    session = HACSession(creds["username"], creds["password"], creds["base_url"])
    session.login()
    data = session.get_info()
    return jsonify(data)
