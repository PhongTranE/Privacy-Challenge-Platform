from src.extensions import db
import sqlalchemy as sa
import sqlalchemy.orm as so 
from passlib.hash import pbkdf2_sha256

class UserModel(db.Model):
    """User model for authentication"""
    __tablename__ = "users"
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=False,
                                                unique=True)
    _password: so.Mapped[str] = so.mapped_column(sa.String(256), nullable=False)
    email: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=False, unique=True)
    roles: so.Mapped[list["RoleModel"]] = so.relationship(
        "RoleModel", back_populates="users", secondary="roles_users"
    )
    is_active: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False, server_default=sa.text("false"))

    @property
    def password(self):
        """Prevent direct access to the hashed password."""
        raise AttributeError("Password cannot be accessed directly.")

    @password.setter
    def password(self, raw_password: str):
        """Hash password before storing it."""
        self._password = pbkdf2_sha256.hash(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        """Verify if the given password matches the stored hashed password."""
        return pbkdf2_sha256.verify(raw_password, self._password)
    
    def __repr__(self):
        return '<User {}>'.format(self.username)