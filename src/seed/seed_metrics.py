import json
from pathlib import Path
from src.extensions import db
from src.modules.anonymisation.models import MetricModel

def insert_metrics():
    metrics_dir = Path(__file__).parent.parent / 'core' / 'metrics'

    metric_files = [
        f.stem for f in metrics_dir.iterdir()
        if f.is_file() and f.suffix == '.py' and f.name != '__init__.py' and f.name != '__pycache__'
    ]

    for metric_name in metric_files:
        existing = db.session.execute(
            db.select(MetricModel).where(MetricModel.name == metric_name)
        ).scalars().first()

        if existing:
            continue

        metric = MetricModel(
            name=metric_name,
            parameters=json.dumps({}),
            is_selected=False
        )
        db.session.add(metric)

    db.session.commit()
