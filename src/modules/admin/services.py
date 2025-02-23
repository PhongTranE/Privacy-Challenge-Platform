import secrets
import string
from src.modules.admin.models import InviteKeyModel
from src.constants.admin import EXPIRATION_INVITE_KEY
from datetime import datetime, timezone, timedelta

def generate_invite_key():
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(6))

def is_invite_key_expired(invite_key: InviteKeyModel) -> bool:
    """Check if an invite key has expired."""
    if not isinstance(invite_key, InviteKeyModel) or not invite_key.created:
        return True  

    if invite_key.created.tzinfo is None:
        invite_created_aware = invite_key.created.replace(tzinfo=timezone.utc)
    else:
        invite_created_aware = invite_key.created

    expiration_time = invite_created_aware + timedelta(seconds=EXPIRATION_INVITE_KEY)
    return datetime.now(timezone.utc) > expiration_time