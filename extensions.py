from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window",
)

jwt = JWTManager()
