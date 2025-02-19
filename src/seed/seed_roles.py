from src.extensions import db
from src.modules.auth.models import RoleModel, Permission

def insert_roles():
    """Predefine roles into the database and assign them permissions"""
    roles = {
        'User': [Permission.PERMISSION_1, Permission.PERMISSION_2],
        'Administrator': [Permission.PERMISSION_1, Permission.PERMISSION_2, Permission.ADMIN],
    }
    default_role = 'User'

    for r in roles:
        stm = db.select(RoleModel).where(RoleModel.name == r)
        role = db.session.execute(stm).scalars().first()
        
        if role is None:
            role = RoleModel(name=r, permissions=0)

        role.reset_permissions()
        for perm in roles[r]:
            role.add_permission(perm)
        role.default = (role.name == default_role)
        db.session.add(role)

    db.session.commit()
