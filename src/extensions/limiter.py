from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask_jwt_extended import get_jwt_identity

def get_user_id_or_ip():
    try:
        return get_jwt_identity() or get_remote_address()
    except Exception:
        return get_remote_address()
    
limiter = Limiter(
    key_func=get_user_id_or_ip,  # Require further config when using NGINX reverse proxy
    # default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://redis:6379/1"
)
