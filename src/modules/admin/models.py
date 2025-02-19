from src.extensions import db
import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime, timezone

class InviteKey(db.Model):
    __tablename__ = "invite_keys"
    key: so.Mapped[str] = so.mapped_column(sa.String(6), primary_key=True)
    created: so.Mapped[datetime] = so.mapped_column(sa.DateTime(), default=lambda:datetime.now(timezone.utc))

