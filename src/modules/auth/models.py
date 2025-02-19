from src.extensions import db
import sqlalchemy as sa
import sqlalchemy.orm as so 
from datetime import datetime, timezone

class Permission:
    """Defines permission bit flags for RBAC"""
    PERMISSION_1 = 1
    PERMISSION_2 = 2
    PERMISSION_3 = 4
    ADMIN = 8

class RoleModel(db.Model):
    """User roles for RBAC"""
    __tablename__ = "roles"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, nullable=False)
    default: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, index=True)
    permissions: so.Mapped[int] = so.mapped_column(sa.Integer, default=0, nullable=False)
    users: so.Mapped[list["UserModel"]] = so.relationship(
        "UserModel", back_populates="roles", secondary="roles_users"
    )

    def __repr__(self):
        return '<RoleModel {}>'.format(self.name)

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm


class RoleUserModel(db.Model):
    """Association table for User-RoleModel many-to-many relationship"""
    __tablename__ = "roles_users"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    role_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("roles.id"), nullable=False)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("users.id"), nullable=False)


class BlacklistedToken(db.Model):
    __tablename__ = "blacklisted_tokens"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    jti: so.Mapped[str] = so.mapped_column(sa.String(36), unique=True, nullable=False)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=lambda: datetime.now(timezone.utc))
