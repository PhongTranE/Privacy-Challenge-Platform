from flask.views import MethodView
from flask_smorest import abort
from flask import jsonify
from http import HTTPStatus
from src.extensions import db
from src.modules.anonymisation.models import MetricModel
from src.modules.admin.resources import admin_blp
from sqlalchemy import select
from src.modules.anonymisation.schemas import MetricSchema
from sqlalchemy.exc import IntegrityError
from src.common.decorators import role_required
from src.constants.admin import *


@admin_blp.route("/metric/<string:metric_name>/toggle")
class MetricActivation(MethodView):
    """Toggle activation status of a metric."""
    @role_required([ADMIN_ROLE])
    def patch(self, metric_name):
        """Activates or deactivates a metric."""
        stmt = select(MetricModel).where(MetricModel.name == metric_name)
        metric = db.session.execute(stmt).scalars().first()

        if not metric:
            abort(HTTPStatus.NOT_FOUND, message="Metric not found.")

        metric.is_selected = not metric.is_selected
        db.session.commit()

        return jsonify({
            "message": f"Metric '{metric.name}' {'activated' if metric.is_selected else 'deactivated'}.",
            "metric_name": metric.name,
            "is_selected": metric.is_selected
        }), HTTPStatus.OK
    

@admin_blp.route("/metric")
class MetricList(MethodView):
    
    @role_required([ADMIN_ROLE])
    @admin_blp.arguments(MetricSchema)  
    @admin_blp.response(HTTPStatus.CREATED, MetricSchema)
    def post(self, data):
        """Creates a new metric."""
        metric_name = data["name"].strip()
        parameters = data.get("parameters", "{}")
        
        existing_metric = db.session.execute(
            select(MetricModel).where(MetricModel.name == metric_name)
        ).scalars().first()

        if existing_metric:
            abort(HTTPStatus.CONFLICT, message=f"Metric '{metric_name}' already exists.")

        new_metric = MetricModel(
            name=metric_name,
            parameters=parameters,
            is_selected=False
        )

        try:
            db.session.add(new_metric)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, message="Database error while creating metric.")

        return new_metric

    @role_required([ADMIN_ROLE])
    @admin_blp.response(HTTPStatus.OK, MetricSchema(many=True))  
    def get(self):
        """Retrieve all metrics."""
        stmt = select(MetricModel)
        metrics = db.session.execute(stmt).scalars().all()
        
        if not metrics:
            abort(HTTPStatus.NOT_FOUND, message="No metrics found.")

        return metrics  