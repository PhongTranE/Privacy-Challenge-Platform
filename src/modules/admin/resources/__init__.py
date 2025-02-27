from flask_smorest import Blueprint

# Create a global Admin Blueprint
admin_blp = Blueprint("admin_func", __name__, description="Main Admin Blueprint")

from src.modules.admin.resources.access_control import *
from src.modules.admin.resources.file_control import *
