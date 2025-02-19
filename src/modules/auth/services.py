from password_validator import PasswordValidator
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from flask_mail import Message
from src.extensions.mail import mail
from werkzeug.exceptions import InternalServerError


from src.modules.auth.models import BlacklistedToken
from flask_jwt_extended import get_jwt
from src.extensions import db
from sqlalchemy import select

password_schema = PasswordValidator()
password_schema \
    .min(8) \
    .max(128) \
    .has().uppercase() \
    .has().lowercase() \
    .has().digits() \
    .has().symbols() \

def validate_password(password):
    if not password_schema.validate(password):
        raise ValueError("Password must be 8-128 characters long, contain uppercase, lowercase, a digit and a symbol.")

def generate_activation_token(email):
    """Generate a secure activation token."""
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt=current_app.config["SECURITY_PASSWORD_SALT"])

def verify_token(token, expiration=3600):
    """Verify and decode an activation token."""
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(token, salt=current_app.config["SECURITY_PASSWORD_SALT"], max_age=expiration)
        return email
    except Exception:
        return None


def send_activation_email(user_email):
    """Send an account activation email."""
    activation_token = generate_activation_token(user_email)
    
    # Direct backend API endpoint for activation
    activation_link = f"http://127.0.0.1:5000/api/auth/activation/{activation_token}"

    msg = Message(
        subject="Activate Your Account",
        sender="noreply@example.com",
        recipients=[user_email],
        body=f"Click the following link to activate your account via the backend API: {activation_link}"
    )

    try:
        mail.send(msg)
    except Exception as e:
        raise InternalServerError(f"Failed to send activation email: {str(e)}")

def send_password_reset_email(user_email):
    """Send a password reset email."""
    reset_token = generate_activation_token(user_email)
    
    reset_link = f"http://127.0.0.1:5000/api/auth/reset-password/{reset_token}"

    msg = Message(
        subject="Reset Your Password",
        sender="noreply@example.com",
        recipients=[user_email],
        body=f"Click the following link to reset your password: {reset_link}"
    )

    try:
        mail.send(msg)
    except Exception as e:
        raise RuntimeError(f"Failed to send reset email: {str(e)}")


def add_token_to_blacklist():
    """Adds the current JWT token to the database blacklist."""
    jti = get_jwt()["jti"]
    if not is_token_blacklisted(jti):  # Prevent duplicates
        blacklisted_token = BlacklistedToken(jti=jti)
        db.session.add(blacklisted_token)
        db.session.commit()

def is_token_blacklisted(jti):
    """Checks if a JWT token is in the blacklist."""
    stmt = select(BlacklistedToken).where(BlacklistedToken.jti == jti)
    return db.session.execute(stmt).scalar_one_or_none() is not None


