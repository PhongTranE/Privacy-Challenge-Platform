from src.extensions import db
import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime, timezone
from src.modules.auth.models import UserModel


class InviteKeyModel(db.Model):
    """Stores invite keys for user registration."""

    __tablename__ = "invite_keys"

    key: so.Mapped[str] = so.mapped_column(sa.String(6), primary_key=True)
    created: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    creator_id: so.Mapped[int | None] = so.mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    creator: so.Mapped["UserModel"] = so.relationship(
        "UserModel", back_populates="invitekeys"
    )

    def __repr__(self):
        return f"<InviteKey {self.key}>"
