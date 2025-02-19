import os
from .base import BaseConfig

class StagingConfig(BaseConfig):
    @property
    def DEBUG(self):
        return False

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return os.getenv("DATABASE_URL", "sqlite:///staging.db")
    