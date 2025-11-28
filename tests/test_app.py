import pytest
import sys
import os

# IMPORTANT: Set environment variables BEFORE importing app
os.environ['MONGO_URI'] = 'mongodb://localhost:27017/test_db'
os.environ['SECRET_KEY'] = 'test-secret-key'

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app

@pytest.fixture
def app():
    """Create application fixture"""
    flask_app.config.update({
        "TESTING": True,
    })
    yield flask_app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

def test_app_exists():
    """Test that the Flask app is created"""
    assert flask_app is not None

def test_app_has_secret_key(app):
    """Test that app has a secret key configured"""
    assert app.secret_key is not None

def test_app_in_testing_mode(app):
    """Test app is in testing mode"""
    assert app.config['TESTING'] == True

def test_routes_are_registered(app):
    """Test that routes are registered"""
    rules = [rule.rule for rule in app.url_map.iter_rules()]
    assert '/' in rules
    assert '/add' in rules
