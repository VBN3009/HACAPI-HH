from flask import Blueprint, request, jsonify
from supabase import create_client
import os

logs_bp = Blueprint("logs", __name__, url_prefix="/logs")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

@logs_bp.route("/checkout", methods=["POST"])
def log_checkout():
    payload = request.get_json()
    print("📥 Checkout Payload:", payload)

    record = {
        "student_name":  payload["student_name"],
        "class_name":    payload["class_name"],
        "period":        int(payload["period"]),
        "room":          payload["room"],
        "teacher":       payload["teacher"],
        "checkout_time": payload.get("checkout_time")
    }

    try:
        res = supabase.table("checkouts").insert(record).execute()
        if res.data:
            print("✅ Supabase insert success:", res.data[0])
            return jsonify(res.data[0]), 201
        else:
            print("❌ Supabase insert returned no data")
            return jsonify({"error": "Insert failed"}), 500
    except Exception as e:
        print("❌ Exception during insert:", str(e))
        return jsonify({"error": str(e)}), 500




@logs_bp.route("/checkin", methods=["POST"])
def log_checkin():
    payload = request.get_json()
    print("📥 Checkin Payload:", payload)

    try:
        res = supabase.table("checkouts") \
            .update({
                "checkin_time": payload["checkin_time"],
                "duration_sec": payload["duration_sec"]
            }) \
            .eq("id", payload["checkout_id"]) \
            .execute()

        if res.data:
            print("✅ Supabase update success:", res.data)
            return jsonify(res.data), 200
        else:
            print("❌ Supabase update returned no data")
            return jsonify({"error": "Update failed"}), 500
    except Exception as e:
        print("❌ Exception during update:", str(e))
        return jsonify({"error": str(e)}), 500

