from src.extensions import db
import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime, timezone
from src.modules.auth.models import GroupUserModel
from src.modules.attack.models import AttackModel
class AnonymModel(db.Model):
    """Tracks anonymization file processing activities."""
    __tablename__ = "anonymisations"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    footprint_file: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=True, unique=True)
    shuffled_file: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=True, unique=True)
    original_file: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    file_link: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False, unique=True)

    naive_attack: so.Mapped[float] = so.mapped_column(sa.Float(), nullable=False, default=0.0)
    utility: so.Mapped[float] = so.mapped_column(sa.Float(), nullable=False, default=0.0)

    status: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False, default="pending")
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now(timezone.utc))

    name: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=False, index=True)
    is_published: so.Mapped[bool] = so.mapped_column(sa.Boolean(), nullable=False, default=False, index=True)

    group_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("group_users.id", name="fk_anonym_group", ondelete="CASCADE"),
        nullable=True
    )    
    group: so.Mapped["GroupUserModel"] = so.relationship("GroupUserModel", back_populates="anonyms")
    
    attacks: so.Mapped[list["AttackModel"]] = so.relationship("AttackModel", back_populates="anonym")

    def __repr__(self):
        return f"<Anonymisation {self.name} - {self.status}>"
    
    

class MetricModel(db.Model):
    """Tracks evaluation metrics for anonymization."""
    __tablename__ = "metrics"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(32), nullable=False, unique=True, index=True)
    is_selected: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, index=True)

    parameters: so.Mapped[str] = so.mapped_column(sa.String(32), nullable=True, default="{}")

    def __repr__(self):
        return f"<Metric {self.name} - Selected: {self.is_selected}>"


class AggregationModel(db.Model):
    """Tracks different aggregation methods used for utility evaluation."""
    __tablename__ = "aggregations"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(32), nullable=False, unique=True, index=True)
    is_selected: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, index=True)

    def __repr__(self):
        return f"<Aggregation {self.name} - Selected: {self.is_selected}>"