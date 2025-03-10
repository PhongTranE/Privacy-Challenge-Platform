import os
from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    @property
    def DEBUG(self):
        return True

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return os.getenv("DATABASE_URL", "sqlite:///dev.db")

    SEED_ADMIN = True

    MAIL_SERVER = 'localhost'
    # MAIL_SERVER = 'mailhog'
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None 
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER =  "noreply@example.com"

    SECRET_KEY = "lnguye01"
    SECURITY_PASSWORD_SALT = "e5f2c7b3a8d9e1f442d6a1c2b5e4f7a9"

    SERVER_NAME = '127.0.0.1:5000'
    PREFERRED_URL_SCHEME = 'http'
