import os
import redis
import json
import certifi
import uuid
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from supabase import create_client

# Load env
load_dotenv()

# Fernet key
FERNET_KEY = os.getenv("FERNET_KEY").encode()
fernet = Fernet(FERNET_KEY)

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "gusc1-clean-sloth-31466.upstash.io")
REDIS_PORT = int(os.getenv("REDIS_PORT", 31466))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    ssl=True,
    ssl_cert_reqs="required",
    ssl_ca_certs=certifi.where()
)

def store_credentials(session_id, username, password, base_url, user_id=None):
    plain_data = {
        "username": username,
        "password": password,
        "base_url": base_url
    }
    if user_id:
        plain_data["user_id"] = user_id

    # Encrypt credentials
    encrypted = fernet.encrypt(json.dumps(plain_data).encode()).decode()

    # Save in Supabase
    record_id = str(uuid.uuid4())
    supabase.table("secure_sessions").insert({
        "id": record_id,
        "session_id": session_id,
        "encrypted": encrypted
    }).execute()

    # Store only record_id in Redis (short-lived)
    redis_client.setex(session_id, 300, record_id)  # 5 min TTL

def get_credentials(session_id):
    record_id = redis_client.get(session_id)
    if not record_id:
        return None

    record_id = record_id.decode()
    result = supabase.table("secure_sessions").select("encrypted").eq("id", record_id).limit(1).execute()
    if not result.data:
        return None

    encrypted = result.data[0]["encrypted"]
    decrypted = fernet.decrypt(encrypted.encode()).decode()
    return json.loads(decrypted)
