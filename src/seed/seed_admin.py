"""
This script is intended for **development and testing purposes only**.  
It automatically creates an admin user with **hardcoded credentials**.  
**DO NOT** use this in production as it poses a security risk.
Instead, use the `flask createadmin` command for secure admin creation.
"""
from src.extensions import db
from src.models.user import UserModel
from src.modules.auth.models import RoleModel

def create_admin():
    """Creates an initial admin user if it does not exist."""
    admin = db.session.execute(db.select(UserModel).where(UserModel.username == "admin")).scalars().first()

    if not admin:
        admin = UserModel(username="admin", password="admin123", email="admin@gmail.com", is_active=True)

        admin_role = db.session.execute(db.select(RoleModel).where(RoleModel.name == "Administrator")).scalars().first()

        if admin_role:
            admin.roles.append(admin_role)
        
        db.session.add(admin)
        db.session.commit()
        
