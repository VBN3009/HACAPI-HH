from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",  # Will be overridden by REDIS_URL if set
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window",
)
