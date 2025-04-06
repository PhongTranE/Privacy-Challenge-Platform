import os

from flask import Flask
from flask_smorest import Api
from src.extensions import db, jwt, mail, init_celery, limiter, cors
from flask_migrate import Migrate

from src.config import get_config
from src.config.logging import configure_logger, configure_sql_logger

from src.commands import register_commands
from src.common.error_handlers import register_error_handlers, register_jwt_handlers

from src.modules.api import api_blp
from src.extensions.admin_ui import init_admin
import src.modules.auth.signals 


def create_app(config=None):
    app = Flask(__name__, template_folder="templates")

    if config is None:
        config = get_config()  
    app.config.from_object(config)

    # Set up logging (Flask logs)
    log_path = os.path.join(app.config.get("LOG_DIR", "src/logs"), "app.log")
    app.logger = configure_logger(log_path, debug_mode=app.config["DEBUG"])

    # Set up structured SQL logging
    sql_log_path = os.path.join(app.config.get("LOG_DIR", "src/logs"), "sql.log")
    configure_sql_logger(sql_log_path)

    db.init_app(app)
    migrate = Migrate(app, db)
    api = Api(app)

    cors.init_app(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173"
            ]
        }
    }, supports_credentials=True)

    limiter.init_app(app)
    jwt.init_app(app)

    # Initialize Flask-Mail 
    mail.init_app(app)

    # Celery
    init_celery(app)

    # Initialize Flask-Admin
    init_admin(app)

    # Register CLI commands
    register_commands(app)
    register_error_handlers(app)
    register_jwt_handlers(jwt)

    api.register_blueprint(api_blp)
    
    return app

