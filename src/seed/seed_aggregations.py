from src.extensions import db
from src.modules.anonymisation.models import AggregationModel

def insert_aggregations():
    aggregations = [
        {"name": "min", "is_selected": False},
        {"name": "max", "is_selected": False},
        {"name": "mean", "is_selected": False},
        {"name": "median", "is_selected": False},
    ]

    for a in aggregations:
        existing = db.session.execute(
            db.select(AggregationModel).where(AggregationModel.name == a["name"])
        ).scalars().first()
        if existing:
            continue

        agg = AggregationModel(
            name=a["name"],
            is_selected=a["is_selected"]
        )
        db.session.add(agg)

    db.session.commit()
