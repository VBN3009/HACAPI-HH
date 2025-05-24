from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from supabase import create_client
from scramble import get_credentials
import os

logs_bp = Blueprint("logs", __name__, url_prefix="/logs")

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

@logs_bp.route("/checkout", methods=["POST"])
@jwt_required()
def log_checkout():
    session_id = get_jwt_identity()
    creds = get_credentials(session_id)

    if not creds:
        return jsonify({"error": "Session expired or credentials missing"}), 401

    payload = request.get_json()
    print("📥 Checkout Payload:", payload)

    student_id = payload.get("student_id")
    user_id = creds.get("user_id")

    if not student_id or not user_id:
        return jsonify({"error": "Missing student_id or user_id"}), 400

    record = {
        "student_id":    student_id,
        "student_name":  payload.get("student_name"),
        "class_name":    payload.get("class_name"),
        "period":        int(payload.get("period")),
        "room":          payload.get("room"),
        "teacher":       payload.get("teacher"),
        "checkout_time": payload.get("checkout_time"),
        "user_id":       user_id
    }

    # Set RLS user_id context (via set_config RPC)
    try:
        supabase.postgrest.rpc(
            "set_config",
            {
                "key": "app.user_id",
                "value": str(user_id),
                "is_local": True
            }
        ).execute()
    except Exception as e:
        print("❌ Failed to set RLS context:", str(e))
        return jsonify({"error": "Failed to set RLS context"}), 500

    # Insert checkout record
    try:
        res = supabase.table("checkouts").insert(record).execute()
        if res.data:
            print("✅ Supabase insert success:", res.data[0])
            return jsonify(res.data[0]), 201
        else:
            print("⚠️ Supabase insert returned no data")
            return jsonify({"error": "Insert failed"}), 500
    except Exception as e:
        print("❌ Exception during insert:", str(e))
        return jsonify({"error": str(e)}), 500


@logs_bp.route("/checkin", methods=["POST"])
@jwt_required()
def log_checkin():
    session_id = get_jwt_identity()
    creds = get_credentials(session_id)

    if not creds:
        return jsonify({"error": "Session expired or credentials missing"}), 401

    user_id = creds.get("user_id")
    payload = request.get_json()
    print("📥 Checkin Payload:", payload)

    # ✅ Set RLS user_id context using RPC
    try:
        supabase.postgrest.rpc(
            "set_config",
            {
                "key": "app.user_id",
                "value": str(user_id),
                "is_local": True
            }
        ).execute()
    except Exception as e:
        print("❌ Failed to set RLS context:", str(e))
        return jsonify({"error": "Failed to set RLS context"}), 500

    # ✅ Then update the row
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
            print("⚠️ Supabase update returned no data")
            return jsonify({"error": "Update failed"}), 500
    except Exception as e:
        print("❌ Exception during update:", str(e))
        return jsonify({"error": str(e)}), 500

