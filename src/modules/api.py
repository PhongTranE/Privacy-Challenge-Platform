from flask_smorest import Blueprint

from src.modules.auth.resources import blp as auth_blp
from src.modules.admin.resources import admin_blp
from src.modules.anonymisation.resources import blp as anonym_blp
from src.modules.attack.resources import blp as attack_blp
# Create a global API Blueprint
api_blp = Blueprint("api", __name__, url_prefix="/api", description="Main API Blueprint")

# Register the individual Blueprints under the main API Blueprint
api_blp.register_blueprint(auth_blp, url_prefix="/auth")
api_blp.register_blueprint(admin_blp, url_prefix="/admin")
api_blp.register_blueprint(anonym_blp, url_prefix="/anonym")
api_blp.register_blueprint(attack_blp, url_prefix="/attack")
