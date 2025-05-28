import secrets
import string
from src.modules.admin.models import InviteKeyModel
from src.constants.admin import EXPIRATION_INVITE_KEY
from datetime import datetime, timezone, timedelta
from src.modules.auth.models import GroupUserModel, UserModel
from src.modules.anonymisation.models import AnonymModel
from src.modules.attack.models import AttackModel
from src.extensions import db
from sqlalchemy import func, select

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