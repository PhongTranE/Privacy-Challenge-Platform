from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_jwt_extended import get_jwt
from flask_smorest import abort
from src.extensions import db
from src.modules.auth.models import RoleModel, BlacklistedToken, UserModel
from src.modules.admin.models import InviteKeyModel
from src.modules.auth.models import Permission
import json
from src.constants.admin import ADMIN_ROLE
from src.constants.app_msg import UNAUTHORIZED_ACCESS
from src.modules.anonymisation.models import MetricModel
from wtforms import TextAreaField
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
class MetricAdmin(SecureModelView):
    """Flask-Admin Panel View for Managing Metrics"""
    
    column_list = ("id", "name", "is_selected", "parameters")  
    column_searchable_list = ("name",)  
    column_filters = ("is_selected",)  

    form_columns = ("name", "is_selected", "parameters")  
    # form_overrides = {"parameters": TextAreaField}  

    # # def on_model_change(self, form, model, is_created):
    # #     """Ensure JSON format for parameters before saving."""
    # #     try:
    # #         json.loads(model.parameters)  # Just to validate if it's proper JSON
    # #     except json.JSONDecodeError:
    # #         abort(400, message="Invalid JSON format for parameters.")

    # def format_parameters(self, context, model, name):
    #     """Pretty-print JSON parameters in the admin panel."""
    #     try:
    #         return json.dumps(json.loads(model.parameters), indent=2)
    #     except json.JSONDecodeError:
    #         return model.parameters  # If invalid, return as is

    # column_formatters = {"parameters": format_parameters}

class AnonymAdmin(SecureModelView):
    """Flask-Admin Panel View for Managing Anonymization Records"""
    
    column_list = (
        "id", "name", "status", "file_link", "original_file", 
        "footprint_file", "shuffled_file", "utility", "naive_attack", "is_published"
    )  
    column_searchable_list = ("name", "status")  
    column_filters = ("status", "is_published")  
    column_editable_list = ("status", "is_published")  

    form_columns = (
        "name", "status", "file_link", "original_file", 
        "footprint_file", "shuffled_file", "utility", "naive_attack", "is_published"
    )

    def on_model_change(self, form, model, is_created):
        """Hook to validate before saving changes."""
        if model.utility < 0 or model.utility > 1:
            raise ValueError("Utility score must be between 0 and 1.")

        if model.naive_attack < 0 or model.naive_attack > 1:
            raise ValueError("Naive attack score must be between 0 and 1.")

    def format_status(self, context, model, name):
        """Format status column."""
        return f"{model.status}" if model.status == "completed" else f" {model.status}"

    column_formatters = {"status": format_status}