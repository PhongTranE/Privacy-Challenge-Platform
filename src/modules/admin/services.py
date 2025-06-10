import secrets
import string
from src.modules.admin.models import InviteKeyModel, CompetitionModel, RawFileModel
from src.constants.admin import EXPIRATION_INVITE_KEY
from datetime import datetime, timezone, timedelta
from src.modules.auth.models import GroupUserModel, UserModel
from src.modules.anonymisation.models import AnonymModel, MetricModel, AggregationModel
from src.modules.admin.models import CompetitionModel
from src.modules.attack.models import AttackModel
from src.extensions import db
from sqlalchemy import func, select
from http import HTTPStatus
from src.common.response_builder import ResponseBuilder
from flask import abort
from functools import wraps
from flask_jwt_extended import get_jwt

def generate_invite_key():
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(6))

def is_invite_key_expired(invite_key: InviteKeyModel) -> bool:
    """Check if an invite key has expired."""
    if not isinstance(invite_key, InviteKeyModel) or not invite_key.created:
        return True  

    if invite_key.created.tzinfo is None:
        invite_created_aware = invite_key.created.replace(tzinfo=timezone.utc)
    else:
        invite_created_aware = invite_key.created

    expiration_time = invite_created_aware + timedelta(seconds=EXPIRATION_INVITE_KEY)
    return datetime.now(timezone.utc) > expiration_time

def group_not_banned_required():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            group_id = claims.get('group')
            if not group_id:
                abort(HTTPStatus.FORBIDDEN, message="User must be part of a group.")
            group = db.session.get(GroupUserModel, group_id)
            if not group:
                abort(HTTPStatus.FORBIDDEN, message="User's group not found.")
            if group.is_banned:
                response = ResponseBuilder().error(
                    message="Your group is banned by Admin, please contact Admin to resolve.",
                    status_code=HTTPStatus.FORBIDDEN
                ).build()
                return response
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def calculate_group_statistics(group_id: int) -> dict:
    """
    Calculate detailed statistics for a group
    """
    # Count anonymous files
    anonymous_count = db.session.execute(
        select(func.count(AnonymModel.id))
        .where(AnonymModel.group_id == group_id)
    ).scalar()
    
    # Count published anonymous files
    published_count = db.session.execute(
        select(func.count(AnonymModel.id))
        .where(AnonymModel.group_id == group_id, AnonymModel.is_published == True)
    ).scalar()
    
    # Count attack files
    attack_count = db.session.execute(
        select(func.count(AttackModel.id))
        .where(AttackModel.group_id == group_id)
    ).scalar()
    
    # Calculate defense score (average utility score of published anonymous files)
    defense_score_result = db.session.execute(
        select(func.avg(AnonymModel.utility))
        .where(AnonymModel.group_id == group_id, AnonymModel.is_published == True)
    ).scalar()
    defense_score = float(defense_score_result) if defense_score_result else 0.0
    
    # Calculate attack score (average score of attack files)
    attack_score_result = db.session.execute(
        select(func.avg(AttackModel.score))
        .where(AttackModel.group_id == group_id)
    ).scalar()
    attack_score = float(attack_score_result) if attack_score_result else 0.0
    
    # Calculate total score (can customize the formula)
    total_score = (defense_score + attack_score) / 2 if (defense_score > 0 or attack_score > 0) else 0.0
    
    return {
        'total_anonymous_files': anonymous_count or 0,
        'published_anonymous_files': published_count or 0,
        'total_attack_files': attack_count or 0,
        'defense_score': round(defense_score, 4),
        'attack_score': round(attack_score, 4),
        'total_score': round(total_score, 4)
    }

def get_group_files(group_id: int, file_type: str = None, limit: int = 10) -> list:
    """
    Get list of files of group (both anonymous and attack files)
    """
    files = []
    
    if not file_type or file_type == 'anonymous':
        # Get anonymous files
        anonymous_files = db.session.execute(
            select(AnonymModel)
            .where(AnonymModel.group_id == group_id)
            .order_by(AnonymModel.id.desc())
            .limit(limit)
        ).scalars().all()
        
        for anonym in anonymous_files:
            files.append({
                'id': anonym.id,
                'name': anonym.name,
                'file_type': 'anonymous',
                'created_at': None,  # AnonymModel does not have created_at
                'score': anonym.utility,
                'is_published': anonym.is_published,
                'file_path': anonym.file_link
            })
    
    if not file_type or file_type == 'attack':
        # Get attack files  
        attack_files = db.session.execute(
            select(AttackModel)
            .where(AttackModel.group_id == group_id)
            .order_by(AttackModel.id.desc())
            .limit(limit)
        ).scalars().all()
        
        for attack in attack_files:
            files.append({
                'id': attack.id,
                'name': f"Attack_{attack.id}",
                'file_type': 'attack',
                'created_at': None,  # AttackModel does not have created_at
                'score': attack.score,
                'is_published': True,  # Attack files are usually considered published
                'file_path': attack.file
            })
    
    return sorted(files, key=lambda x: x['id'], reverse=True)[:limit]

def get_group_detail(group_id: int) -> dict:
    """
    Get detailed information of group
    """
    group = db.session.get(GroupUserModel, group_id)
    if not group:
        return None
    
    # Get members
    members = []
    for user in group.users:
        members.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active
        })
    
    # Get statistics
    statistics = calculate_group_statistics(group_id)
    
    # Get recent files
    recent_files = get_group_files(group_id, limit=5)
    
    return {
        'group': {
            'id': group.id,
            'name': group.name,
            'is_banned': group.is_banned,
            'member_count': len(members)
        },
        'members': members,
        'statistics': statistics,
        'recent_files': recent_files
    }

def update_group_name(group_id: int, new_name: str) -> bool:
    """
    Update group name
    """
    group = db.session.get(GroupUserModel, group_id)
    if not group:
        return False
    
    group.name = new_name
    db.session.commit()
    return True

def get_selected_metrics():
    """Get currently selected metrics."""
    return MetricModel.query.filter_by(is_selected=True).all()

def get_selected_aggregations():
    """Get currently selected aggregations."""
    return AggregationModel.query.filter_by(is_selected=True).all()

def get_active_raw_file():
    """Get currently active raw file."""
    from src.modules.admin.models import RawFileModel
    return RawFileModel.query.filter_by(is_active=True).first()

def validate_competition_start():
    """Validate if competition can start the submission phase."""
    errors = []

    # Check if at least one metric is selected
    if not get_selected_metrics():
        errors.append("No metrics selected. Please select at least one metric.")

    # Check if exactly one aggregation is selected
    if not get_selected_aggregations():
        errors.append("No aggregation selected. Please select exactly one aggregation.")

    # Check if raw file is active
    if not get_active_raw_file():
        errors.append("No active raw file. Please upload or activate a raw file.")

    return errors

def start_submission_phase(competition: CompetitionModel):
    """Start submission phase."""
    competition.current_phase = "submission"
    competition.metrics_locked = True  # Lock metrics settings during the active phase
    competition.aggregation_locked = True  # Lock aggregation settings during the active phase
    db.session.commit()

def end_submission_phase(competition: CompetitionModel):
    """Manually ends the submission phase without starting attack phase"""
    if competition.current_phase != "submission":
        abort(400, message="Cannot end submission phase. It is not active.")
    
    competition.current_phase = "finished_submission"
    competition.is_paused = False
    db.session.commit()

def start_attack_phase(competition: CompetitionModel):
    """Start attack phase."""
    competition.current_phase = "attack"
    db.session.commit()

def end_competition(competition: CompetitionModel):
    """End the competition."""
    competition.current_phase = "finished"
    competition.metrics_locked = False  # Unlock metrics settings after competition ends
    competition.aggregation_locked = False  # Unlock aggregation settings after competition ends
    db.session.commit()

def get_competition_status():
    """Get competition status."""
    comp = CompetitionModel.query.first()
    if not comp:
        return {
            "phase": "setup",
            "is_paused": False,
            "metrics_locked": False,
            "metrics": [],
            "aggregations": [],
            "active_raw_file": None
        }

    metrics = get_selected_metrics()
    aggregations = get_selected_aggregations()
    raw_file = get_active_raw_file()

    return {
        "phase": comp.current_phase,
        "is_paused": comp.is_paused,
        "metrics_locked": comp.metrics_locked,
        "aggregation_locked": comp.aggregation_locked,
        "metrics": [{"name": m.name, "is_selected": m.is_selected} for m in metrics],
        "aggregations": [{"name": a.name, "is_selected": a.is_selected} for a in aggregations],
        "active_raw_file": raw_file.filename if raw_file else None
    }

def pause_competition(competition: CompetitionModel):
    """Pause the competition."""
    if competition.current_phase not in ['submission', 'attack']:
        abort(400, message="Cannot pause. Current phase is not suitable for pausing.")
    competition.is_paused = True
    db.session.commit()

def resume_competition(competition: CompetitionModel):
    """Resume the competition."""
    if competition.current_phase not in ['submission', 'attack']:
        abort(400, message="Cannot resume. Current phase is not suitable for resuming.")
    competition.is_paused = False
    db.session.commit()


def restart_competition(competition: CompetitionModel):
    """Restart the competition."""
    competition.current_phase = "setup"
    competition.metrics_locked = False
    competition.aggregation_locked = False
    competition.is_paused = False
    db.session.commit()