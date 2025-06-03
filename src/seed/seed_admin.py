"""
This script is intended for **development and testing purposes only**.
It automatically creates an admin user with **hardcoded credentials**.
**DO NOT** use this in production as it poses a security risk.
Instead, use the `flask createadmin` command for secure admin creation.
"""

from src.extensions import db
from src.modules.auth.models import RoleModel, UserModel, GroupUserModel
from src.constants.admin import *


def create_admin():
    """Creates an initial admin user if it does not exist, and ensures group_id=1, name='ADMIN'."""
    # Ensure group with id=1 and name='ADMIN' exists
    admin_group = db.session.execute(
        db.select(GroupUserModel).where(GroupUserModel.id == 1)
    ).scalars().first()
    if not admin_group:
        admin_group = GroupUserModel(id=1, name="ADMIN")
        db.session.add(admin_group)
        db.session.commit()
    else:
        # Ensure name is correct
        if admin_group.name != "ADMIN":
            admin_group.name = "ADMIN"
            db.session.commit()

    admin = (
        db.session.execute(db.select(UserModel).where(UserModel.username == "admin"))
        .scalars()
        .first()
    )

    if not admin:
        admin = UserModel(
            username="admin",
            password="Admin1234@@",
            email="admin@gmail.com",
            is_active=True,
            group_id=1,
        )

        admin_role = (
            db.session.execute(db.select(RoleModel).where(RoleModel.name == ADMIN_ROLE))
            .scalars()
            .first()
        )

        if admin_role:
            admin.roles.append(admin_role)

        db.session.add(admin)
        db.session.commit()
    else:
        # Ensure admin is in group 1
        if admin.group_id != 1:
            admin.group_id = 1
            db.session.commit()
