from flask_admin import Admin
from src.extensions import db
from src.extensions.admin_ui.views import SecureAdminIndexView, UserAdmin, RoleAdmin, BlacklistedTokenAdmin, InviteKeyAdmin
from src.modules.admin.models import InviteKeyModel
from src.modules.auth.models import BlacklistedToken, RoleModel, UserModel
from flask_admin.contrib.sqla import ModelView


def init_admin(app):
    """Register models with Flask-Admin, ensuring only one instance."""
    admin_panel = Admin(
        index_view=SecureAdminIndexView(),
        name="Privacy Challenge Admin",
        template_mode="bootstrap4",  
    )
    admin_panel.init_app(app)
    admin_panel.add_view(UserAdmin(UserModel, db.session))
    admin_panel.add_view(RoleAdmin(RoleModel, db.session))
    admin_panel.add_view(BlacklistedTokenAdmin(BlacklistedToken, db.session))
    admin_panel.add_view(InviteKeyAdmin(InviteKeyModel, db.session))

