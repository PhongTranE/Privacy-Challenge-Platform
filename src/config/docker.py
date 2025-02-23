from .development import DevelopmentConfig

class DockerConfig(DevelopmentConfig):
    
    MAIL_SERVER = 'mailhog'

    SERVER_NAME = 'localhost'
    PREFERRED_URL_SCHEME = 'https'
    