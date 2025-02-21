import os

from flask import Flask
from flask_smorest import Api
from src.extensions import db, jwt, mail
from flask_migrate import Migrate

from src.config import get_config
from src.config.logging import configure_logger, configure_sql_logger

from src.commands import register_commands
from src.common.error_handlers import register_error_handlers, register_jwt_handlers

from src.modules.api import api_blp

def create_app(config=None):
    app = Flask(__name__)

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

    jwt.init_app(app)

    # Initialize Flask-Mail 
    mail.init_app(app)

    # Register CLI commands
    register_commands(app)
    register_error_handlers(app)
    register_jwt_handlers(jwt)

    api.register_blueprint(api_blp)
    
    return app

