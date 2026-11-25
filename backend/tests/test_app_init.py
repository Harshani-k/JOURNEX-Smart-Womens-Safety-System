from app import create_app

def test_app_creation_default():
    app = create_app("development")
    assert app is not None
    assert app.config["DEBUG"] is True
    assert app.config["API_VERSION"] == "v1"

def test_app_creation_testing(app):
    assert app is not None
    assert app.config["TESTING"] is True
    assert app.config["ENV"] == "testing"
