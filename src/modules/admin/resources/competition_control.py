from flask import request, jsonify
from flask.views import MethodView
from src.extensions import db
from src.modules.admin.models import CompetitionModel
from src.modules.admin.services import (
    validate_competition_start,
    start_submission_phase,
    end_submission_phase,
    start_attack_phase,
    end_competition,
    get_competition_status,
    pause_competition,
    resume_competition,
    restart_competition,
)
from src.common.response_builder import ResponseBuilder
from src.common.decorators import role_required
from http import HTTPStatus
from src.constants.admin import ADMIN_ROLE
from src.modules.admin.resources import admin_blp

@admin_blp.route("/competition/status")
class CompetitionStatus(MethodView):
    """Get competition status."""

    @role_required([ADMIN_ROLE])
    def get(self):
        """Get competition status."""
        comp = CompetitionModel.query.first()
        if not comp:
            admin_id = "1"
            comp = CompetitionModel(admin_id=admin_id)
            db.session.add(comp)
        status = get_competition_status()
        return ResponseBuilder().success(message="Competition status retrieved", data=status).build()

@admin_blp.route("/competition/phase")
class CompetitionPhaseControl(MethodView):
    """Control competition phases"""

    @role_required([ADMIN_ROLE])
    def post(self):
        """Start, pause, resume, or end competition phases."""
        data = request.get_json()
        action = data.get("action")  # start_submission, end_submission, start_attack, pause, resume, end
        
        comp = CompetitionModel.query.first()
        if not comp:
            admin_id = "1"
            comp = CompetitionModel(admin_id=admin_id)
            db.session.add(comp)

        try:
            if action == "start_submission":
                # Validate if conditions are met to start the submission phase
                validation_errors = validate_competition_start()
                if validation_errors:
                    return ResponseBuilder().error(
                        message="Competition setup is incomplete. " + "; ".join(validation_errors),
                        status_code=HTTPStatus.BAD_REQUEST,
                    ).build()

                # Start submission phase
                start_submission_phase(comp)
            
            elif action == "end_submission":
                if comp.current_phase != "submission":
                    return ResponseBuilder().error(
                        message="Cannot end submission phase. Phase must be active",
                        status_code=HTTPStatus.BAD_REQUEST,
                    ).build()

                # End submission phase manually without starting attack phase
                end_submission_phase(comp)

            elif action == "start_attack":
                if comp.current_phase != "finished_submission":
                    return ResponseBuilder().error(
                        message="Cannot start attack. Submission phase must be completed first",
                        status_code=HTTPStatus.BAD_REQUEST,
                    ).build()

                # Start attack phase
                start_attack_phase(comp)

            elif action == "pause":
                pause_competition(comp)

            elif action == "resume":
                resume_competition(comp)

            elif action == "end":
                # End the competition
                end_competition(comp)

            db.session.commit()

            return ResponseBuilder().success(
                message=f"Phase action '{action}' completed successfully",
                data={"phase": comp.current_phase},
            ).build()

        except Exception as e:
            db.session.rollback()
            return ResponseBuilder().error(
                message=f"Failed to execute phase action: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            ).build()

@admin_blp.route("/competition/restart")
class CompetitionRestart(MethodView):
    @role_required([ADMIN_ROLE])
    def post(self):
        comp = CompetitionModel.query.first()
        if comp:
            restart_competition(comp)
            db.session.commit()
        return {"message": "Competition restarted", "phase": comp.current_phase}
