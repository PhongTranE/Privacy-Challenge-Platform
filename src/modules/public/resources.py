from flask.views import MethodView
from flask_smorest import Blueprint
from http import HTTPStatus
from src.modules.auth.models import GroupUserModel
from src.common.response_builder import ResponseBuilder

blp = Blueprint("public_func", __name__, description="Public")

@blp.route("/ranking")
class PublicRanking(MethodView):
    def get(self):
        groups = GroupUserModel.query.all()
        data = []
        for group in groups:
            # Defense score
            published_anonyms = [a for a in group.anonyms if getattr(a, 'is_published', False)]
            defense_scores = []
            for anonym in published_anonyms:
                if anonym.attacks:
                    best_attack = max([atk.score for atk in anonym.attacks])
                else:
                    best_attack = 0
                defense_score_file = (1 - best_attack) * anonym.utility
                defense_scores.append(defense_score_file)
            defense_score = max(defense_scores) if defense_scores else 0.0

            # Attack score
            attack_score = 0.0
            for other_group in groups:
                if other_group.id == group.id:
                    continue
                other_published_anonyms = [a for a in other_group.anonyms if getattr(a, 'is_published', False)]
                max_scores = []
                for anonym in other_published_anonyms:
                    attacks = [atk for atk in anonym.attacks if atk.group_id == group.id]
                    if attacks:
                        max_score = max([atk.score for atk in attacks])
                    else:
                        max_score = 0.0
                    max_scores.append(max_score)
                if max_scores:
                    attack_score += min(max_scores)

            total_score = (defense_score + attack_score) / 2 if (defense_score > 0 or attack_score > 0) else 0.0

            data.append({
                "team_id": group.id,
                "team_name": group.name,
                "members": [
                    {"id": u.id, "username": u.username}
                    for u in group.users
                ],
                "defense_score": round(defense_score, 4),
                "attack_score": round(attack_score, 4),
                "total_score": round(total_score, 4),
            })
        return ResponseBuilder().success(
            message="Fetched public ranking.",
            data=data,
            status_code=HTTPStatus.OK
        ).build()
