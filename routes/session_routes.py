from datetime import datetime
from flask import Blueprint, request, jsonify

# Create a blueprint for session-related routes
session_bp = Blueprint('session', __name__)

# In-memory store (for development/testing; replace with DB in production)
active_sessions = {}

@session_bp.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    student_id = data.get("studentId")
    name = data.get("name")
    class_name = data.get("className")
    room_number = data.get("roomNumber")

    if not student_id:
        return jsonify({"error": "Missing studentId"}), 400

    now = datetime.utcnow()
    active_sessions[student_id] = {
        "checkoutTime": now,
        "name": name,
        "className": class_name,
        "roomNumber": room_number,
        "status": "Out"
    }

    return jsonify({
        "checkoutTime": now.isoformat() + "Z",
        "status": "Out"
    })


@session_bp.route('/return', methods=['POST'])
def return_student():
    data = request.get_json()
    student_id = data.get("studentId")

    if not student_id or student_id not in active_sessions:
        return jsonify({"error": "No active session found for studentId"}), 404

    now = datetime.utcnow()
    start_time = active_sessions[student_id]["checkoutTime"]
    duration = (now - start_time).total_seconds() / 60

    response_data = {
        "returnTime": now.isoformat() + "Z",
        "durationMinutes": round(duration, 2),
        "status": "In"
    }

    # Clear session after return
    del active_sessions[student_id]

    return jsonify(response_data)
