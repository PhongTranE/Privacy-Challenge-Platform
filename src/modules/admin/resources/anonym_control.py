from flask.views import MethodView
from flask_smorest import abort
from flask import jsonify, request
from http import HTTPStatus
from src.extensions import db
from src.modules.anonymisation.models import MetricModel, AggregationModel
from src.modules.admin.resources import admin_blp
from sqlalchemy import select
from src.modules.anonymisation.schemas import MetricSchema
from sqlalchemy.exc import IntegrityError
from src.common.decorators import role_required
from src.constants.admin import *
import json
from src.common.response_builder import ResponseBuilder


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

@admin_blp.route("/metric/<string:metric_name>/parameters")
class MetricParamUpdate(MethodView):
    """Update parameters of a metric"""
    @role_required([ADMIN_ROLE])
    def patch(self, metric_name):
        json_data = request.get_json()
        parameters = json_data.get("parameters")

        try:
            json.loads(parameters)
        except json.JSONDecodeError:
            abort(HTTPStatus.BAD_REQUEST, message="Parameters must be valid JSON.")

        stmt = select(MetricModel).where(MetricModel.name == metric_name)
        metric = db.session.execute(stmt).scalars().first()

        if not metric:
            abort(HTTPStatus.NOT_FOUND, message="Metric not found.")

        metric.parameters = parameters
        db.session.commit()

        return jsonify({
            "message": "Parameters updated.",
            "metric_name": metric.name,
            "parameters": metric.parameters
        }), HTTPStatus.OK



# ===== AGGREGATION ENDPOINTS =====
# ALLOWED_AGGREGATIONS = ["min", "max", "median", "mean"]

@admin_blp.route("/aggregation/<string:aggregation_name>/toggle")
class AggregationActivation(MethodView):
    """Toggle activation status of an aggregation."""
    @role_required([ADMIN_ROLE])
    def patch(self, aggregation_name):
        """Activates or deactivates an aggregation. Only one can be active at a time."""
        stmt = select(AggregationModel).where(AggregationModel.name == aggregation_name)
        aggregation = db.session.execute(stmt).scalars().first()

        if not aggregation:
            abort(HTTPStatus.NOT_FOUND, message="Aggregation not found.")

        if aggregation.is_selected:
            # Deactivate this aggregation
            aggregation.is_selected = False
        else:
            # Deactivate all others, then activate this one
            AggregationModel.query.update({"is_selected": False})
            aggregation.is_selected = True

        db.session.commit()

        return (
            ResponseBuilder()
            .success(
                message=f"Aggregation '{aggregation.name}' {'activated' if aggregation.is_selected else 'deactivated'}.",
                data={"name": aggregation.name, "is_selected": aggregation.is_selected},
                status_code=HTTPStatus.OK,
            )
            .build()
        )


@admin_blp.route("/aggregation")
class AggregationList(MethodView):
    @role_required([ADMIN_ROLE])
    def get(self):
        """Retrieve all aggregations."""
        stmt = select(AggregationModel)
        aggregations = db.session.execute(stmt).scalars().all()
        
        return jsonify([{
            "id": agg.id,
            "name": agg.name,
            "is_selected": agg.is_selected
        } for agg in aggregations])