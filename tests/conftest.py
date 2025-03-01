import pytest
from src import create_app
from src.extensions import db
from src.config.testing import TestingConfig
import os
import shutil
import tempfile

@pytest.fixture(scope="session")
def app():
    """Create a new Flask app instance for testing."""
    app = create_app(TestingConfig())
    test_upload_dir = os.path.join(tempfile.gettempdir(), "uploads")
    
    shutil.rmtree(test_upload_dir, ignore_errors=True)
    os.makedirs(test_upload_dir, exist_ok=True)
    with app.app_context():
        db.create_all() 
        yield app  
        db.drop_all()  
    shutil.rmtree(test_upload_dir, ignore_errors=True)

@pytest.fixture(scope="class")
def client(app):
    """Return a test client for making HTTP requests."""
    return app.test_client()