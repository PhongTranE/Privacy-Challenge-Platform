from flask import Blueprint

from src.modules.auth.resources import blp as auth_blp
from src.modules.admin.resources import blp as admin_blp

# Create a global API Blueprint
api_blp = Blueprint("api", __name__, url_prefix="/api")

# Register the individual Blueprints under the main API Blueprint
api_blp.register_blueprint(auth_blp, url_prefix="/auth")
api_blp.register_blueprint(admin_blp, url_prefix="/admin")