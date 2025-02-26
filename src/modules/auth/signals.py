from sqlalchemy import event
from flask import current_app
from src.modules.auth.models import UserModel
from src.modules.auth.listeners import user_register

@event.listens_for(UserModel, "after_insert")
def user_registered_listener(mapper, connection, target):
    """ Fires the signal when a new user is created. """
    try:
        with current_app.app_context():
            app = current_app._get_current_object()
            user_register.send(app, user_email=target.email)
            current_app.logger.info(f"Activation email triggered for {target.email}.")
    except Exception as e:
        current_app.logger.error(f"Failed to send activation email for {target.email}: {str(e)}.")