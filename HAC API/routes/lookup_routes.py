from flask import Blueprint, request, jsonify

lookup_bp = Blueprint('lookup', __name__)

# This would hit your database or a cache with current session data
@lookup_bp.route("/lookup", methods=["GET"])
def student_lookup():
    name = request.args.get("name", "").strip().lower()

    # Placeholder: your database would contain this info
    mock_data = {
        "john doe": {"class": "Physics", "room": "B101", "status": "In Class"},
        "jane smith": {"class": "Biology", "room": "C202", "status": "In Hall"},
    }

    student_info = mock_data.get(name)
    if not student_info:
        return jsonify({"error": "Student not found"}), 404

    return jsonify({"student": name.title(), "info": student_info})
