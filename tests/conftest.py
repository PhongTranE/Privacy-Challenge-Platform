import pytest
from src import create_app
from src.extensions import db
from src.config.testing import TestingConfig

@pytest.fixture(scope="session")
def app():
    """Create a new Flask app instance for testing."""
    app = create_app(TestingConfig())
    with app.app_context():
        db.create_all() 
        yield app  
        db.drop_all()  

@pytest.fixture(scope="class")
def client(app):
    """Return a test client for making HTTP requests."""
    return app.test_client()