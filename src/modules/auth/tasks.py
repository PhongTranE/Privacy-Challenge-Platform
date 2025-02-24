from src.modules.auth.services import send_activation_email as send_activation_email_service
from src.modules.auth.services import send_password_reset_email as send_password_reset_email_service

from celery import shared_task


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5})
def send_activation_email_task(self, user_email: str) -> None:
    """ Celery task to send an activation email. """
    if not user_email:
        raise ValueError("Invalid email address")
    send_activation_email_service(user_email)

@shared_task
def send_password_reset_email_task(user_email: str) -> None:
    """ Celery task to send a password reset email. """
    send_password_reset_email_service(user_email)
