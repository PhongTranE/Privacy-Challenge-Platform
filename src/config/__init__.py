import os

def get_config():
    """Dynamically loads the appropriate config class based on FLASK_ENV"""

    env = os.getenv("FLASK_ENV", "development")  # Default to development

    if env == "production":
        from .production import ProductionConfig
        return ProductionConfig()
    elif env == "staging":
        from .staging import StagingConfig
        return StagingConfig()
    else:
        from .development import DevelopmentConfig
        return DevelopmentConfig()