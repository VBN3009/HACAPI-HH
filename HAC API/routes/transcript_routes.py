from flask import Blueprint, request, jsonify
from hac.session import HACSession

transcript_bp = Blueprint("transcript", __name__)

@transcript_bp.route("/api/getTranscript", methods=["GET"])
def get_transcript():
    user = request.args.get('user')
    password = request.args.get('pass')
    link = request.args.get('link', 'https://accesscenter.roundrockisd.org/')

    session = HACSession(user, password, link)
    data = session.get_transcript()
    return jsonify(data)

@transcript_bp.route("/api/getRank", methods=["GET"])
def get_rank():
    user = request.args.get('user')
    password = request.args.get('pass')
    link = request.args.get('link', 'https://accesscenter.roundrockisd.org/')

    session = HACSession(user, password, link)
    return jsonify({"rank": session.get_rank()})
