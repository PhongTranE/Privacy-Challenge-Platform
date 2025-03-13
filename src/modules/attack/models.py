from src.extensions import db
import sqlalchemy as sa
import sqlalchemy.orm as so


class AttackModel(db.Model):
    __tablename__ = "attacks"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    score: so.Mapped[float] = so.mapped_column(sa.Float(), nullable=False, default=0.0)
    file: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False, unique=True)

    anonym_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('anonymisations.id', ondelete='CASCADE'),
        nullable=False
    )
    anonym: so.Mapped["AnonymModel"] = so.relationship("AnonymModel", back_populates="attacks")

    group_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("group_users.id", name="fk_attack_group", ondelete="CASCADE"),
        nullable=False
    )    
    group: so.Mapped["GroupUserModel"] = so.relationship("GroupUserModel", back_populates="attacks")
    
    def __repr__(self):
        return f"Attack {self.id} against {self.anonym_id}"