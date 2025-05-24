import redis
import os
import json
import certifi  # for SSL cert verification

# Load from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "gusc1-clean-sloth-31466.upstash.io")
REDIS_PORT = int(os.getenv("REDIS_PORT", 31466))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# Connect to Redis securely
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    ssl=True,
    ssl_cert_reqs="required",
    ssl_ca_certs=certifi.where()
)

def store_credentials(session_id, username, password, base_url, user_id=None):
    creds = {
        "username": username,
        "password": password,
        "base_url": base_url
    }
    if user_id:
        creds["user_id"] = user_id
    redis_client.setex(session_id, 300, json.dumps(creds))  # 5 minutes



def get_credentials(session_id):
    creds = redis_client.get(session_id)
    return json.loads(creds) if creds else None
