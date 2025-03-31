from flask import Blueprint, request, jsonify
from hac.session import HACSession

assignments_bp = Blueprint("assignments", __name__)

@assignments_bp.route("/api/getAssignments", methods=["GET"])
def get_assignments():
    user = request.args.get('user')
    password = request.args.get('pass')
    link = request.args.get('link', 'https://accesscenter.roundrockisd.org/')
    class_name = request.args.get('class')

    session = HACSession(user, password, link)
    if class_name:
        data = session.get_assignment_class(class_name)
    else:
        data = session.fetch_class_assignments()
    return jsonify(data)
