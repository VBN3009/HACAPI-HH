from flask import Blueprint, request, jsonify
from supabase import create_client
import os

logs_bp = Blueprint("logs", __name__, url_prefix="/logs")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

@logs_bp.route("/checkout", methods=["POST"])
def log_checkout():
    payload = request.get_json()
    record = {
        "student_name":  payload["student_name"],
        "class_name":    payload["class_name"],
        "period":        payload["period"],
        "room":          payload["room"],
        "teacher":       payload["teacher"],
        "checkout_time": payload.get("checkout_time")
    }
    res = supabase.table("checkouts").insert(record).execute()
    if res.error:
        return jsonify({"error": res.error.message}), 500
    return jsonify(res.data[0]), 201

@logs_bp.route("/checkin", methods=["POST"])
def log_checkin():
    payload = request.get_json()
    res = supabase.table("checkouts") \
        .update({
            "checkin_time": payload["checkin_time"],
            "duration_sec": payload["duration_sec"]
        }) \
        .eq("id", payload["checkout_id"]) \
        .execute()
    if res.error:
        return jsonify({"error": res.error.message}), 500
    return jsonify(res.data), 200
