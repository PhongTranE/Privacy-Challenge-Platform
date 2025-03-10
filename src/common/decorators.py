from flask_jwt_extended import get_jwt, jwt_required
from flask_smorest import abort
from functools import wraps
from src.constants.app_msg import *
from src.modules.anonymisation.models import AnonymModel
from src.extensions import db
from sqlalchemy import select

def group_required():
    """
    Decorator to enforce Group-Based Access Control (GBAC).
    Ensures the user is part of the group that owns the anonymization entry.
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            jwt_claims = get_jwt()
            user_group = jwt_claims.get("group", None)  # Extract user's group from JWT
            anonym_id = kwargs.get("anonym_id")  # Get anonymization ID from route parameter
            print(anonym_id)
            if not user_group:
                abort(403, message="You must belong to a group to access this resource.")

            stmt = select(AnonymModel.group_id).where(AnonymModel.id == anonym_id)
            anonym_group_id = db.session.execute(stmt).scalar()

            if anonym_group_id is None or int(anonym_group_id) != int(user_group):
                print(anonym_group_id)
                print(user_group)
                abort(403, message=UNAUTHORIZED_ACCESS)

            return fn(*args, **kwargs)
        return wrapper
    return decorator

def role_required(required_roles):
    """
    Decorator to enforce Role-Based Access Control (RBAC).
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()  
        def wrapper(*args, **kwargs):
            jwt_claims = get_jwt()
            user_roles = jwt_claims.get("roles", [])

            if not any(role in user_roles for role in required_roles):
                abort(403, message=UNAUTHORIZED_ACCESS)

            return fn(*args, **kwargs)
        return wrapper
    return decorator