from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_jwt_extended import get_jwt
from flask_smorest import abort
from src.extensions import db
from src.models.user import UserModel
from src.modules.auth.models import RoleModel, BlacklistedToken
from src.modules.admin.models import InviteKeyModel
from src.modules.auth.models import Permission

from src.constants.admin import ADMIN_ROLE
from src.constants.messages import UNAUTHORIZED_ACCESS

# Secure Admin Panel Index Page 
class SecureAdminIndexView(AdminIndexView):
    """Restrict Admin Dashboard access to users with ADMIN_ROLE."""
    
    # def is_accessible(self):
    #     """Check if user has admin privileges."""
    #     jwt_claims = get_jwt()
    #     user_roles = jwt_claims.get("roles", [])
    #     return ADMIN_ROLE in user_roles  

    # def inaccessible_callback(self, name, **kwargs):
    #     return abort(403, message=UNAUTHORIZED_ACCESS)

    @expose("/")
    def index(self):
        return super().index()

# Secure General Model Views
class SecureModelView(ModelView):
    """Base secure model view for Flask-Admin."""
    
    # def is_accessible(self):
    #     jwt_claims = get_jwt()
    #     user_roles = jwt_claims.get("roles", [])
    #     return ADMIN_ROLE in user_roles  

    # def inaccessible_callback(self, name, **kwargs):
    #     return abort(403, message=UNAUTHORIZED_ACCESS)
    pass

class UserAdmin(SecureModelView):
    column_list = ("id", "username", "email", "roles", "is_active")
    form_excluded_columns = ("_password",)  
    column_searchable_list = ("username", "email")

    # def __init__(self, model, session, **kwargs):
    #     super().__init__(model, session, endpoint="admin_user", name="Users", **kwargs)

class RoleAdmin(SecureModelView):
    """Custom Role Management in Flask-Admin."""
    
    column_list = ("id", "name", "default", "permissions")
    
    def _list_permissions(self, context, model, name):
        """Show readable permission names instead of bit values."""
        perms = [
            perm_name for perm_name, perm_value in Permission.__dict__.items()
            if isinstance(perm_value, int) and model.permissions & perm_value
        ]
        return ", ".join(perms) if perms else "No Permissions"

    column_formatters = {"permissions": _list_permissions}

    # def __init__(self, model, session, **kwargs):
    #     super().__init__(model, session, endpoint="admin_role", name="Roles", **kwargs)


class BlacklistedTokenAdmin(SecureModelView):
    """Admin Panel View for Blacklisted Tokens."""
    
    column_list = ("id", "created_at")  
    column_searchable_list = ("created_at",) 
    column_filters = ("created_at",)  

    can_create = False  
    can_edit = False  
    can_delete = True  

    # def __init__(self, model, session, **kwargs):
    #     super().__init__(model, session, endpoint="admin_blacklisted_token", name="Blacklisted Tokens", **kwargs)

class InviteKeyAdmin(SecureModelView):
    """Admin Panel View for Invite Keys"""
    column_list = ("key", "created")  
    column_searchable_list = ("key", "created")  
    column_filters = ("created",)  

    can_edit = False  
    can_delete = True  
    can_create = True  

    # def __init__(self, model, session, **kwargs):
    #     super().__init__(model, session, endpoint="admin_invite_key", name="Invite Keys", **kwargs)

