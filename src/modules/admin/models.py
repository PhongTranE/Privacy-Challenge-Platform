from src.extensions import db
import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from src.modules.auth.models import UserModel

# Tạo timezone Việt Nam
VIETNAM_TZ = ZoneInfo('Asia/Ho_Chi_Minh')

def get_vietnam_time():
    """Get current time in Vietnam timezone"""
    return datetime.now(VIETNAM_TZ)

competition_metrics = db.Table(
    "competition_metrics",
    db.Column("competition_id", db.Integer, db.ForeignKey("competitions.id", ondelete="CASCADE"), primary_key=True),
    db.Column("metric_id", db.Integer, db.ForeignKey("metrics.id", ondelete="CASCADE"), primary_key=True)
)

class InviteKeyModel(db.Model):
    """Stores invite keys for user registration."""

    __tablename__ = "invite_keys"

    key: so.Mapped[str] = so.mapped_column(sa.String(6), primary_key=True)
    created: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=get_vietnam_time
    )
    creator_id: so.Mapped[int | None] = so.mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    creator: so.Mapped["UserModel"] = so.relationship(
        "UserModel", back_populates="invitekeys"
    )

    def __repr__(self):
        return f"<InviteKey {self.key}>"


class RawFileModel(db.Model):
    """Stores uploaded files for anonymization."""

    __tablename__ = "files"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    filename: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False, unique=True)
    original_filename: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    file_path: so.Mapped[str] = so.mapped_column(
        sa.String(255), nullable=False, unique=True
    )
    uploaded_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=get_vietnam_time
    )
    is_active: so.Mapped[bool] = so.mapped_column(
        sa.Boolean, default=True, index=True
    )
    
    # Link to creator (admin user)
    creator_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    creator: so.Mapped["UserModel"] = so.relationship(
        "UserModel", back_populates="files"
    )

    def __repr__(self):
        return f"<RawFile {self.filename}>"

class CompetitionModel(db.Model):
    """Manage phases and settings of the competition"""
    __tablename__ = "competitions"

    id = db.Column(db.Integer, primary_key=True)

    # ===== ADMIN MANAGEMENT =====
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    admin = db.relationship("UserModel", backref="competition_admin")

    # ===== PHASE CONTROL =====
    current_phase = db.Column(db.String(20), default="setup")  # "setup", "submission", "finished_submission", "attack"
    is_paused = db.Column(db.Boolean, default=False)

    # ===== SETTINGS LOCK =====
    metrics_locked = db.Column(db.Boolean, default=False)
    aggregation_locked = db.Column(db.Boolean, default=False)

    metrics = db.relationship(
        "MetricModel",
        secondary="competition_metrics",
        backref="competitions"
    )

    aggregation_id = db.Column(db.Integer, db.ForeignKey("aggregations.id", ondelete="SET NULL"))
    aggregation = db.relationship("AggregationModel", backref="competition", uselist=False)

    def __repr__(self):
        return f"<Competition {self.current_phase}>"