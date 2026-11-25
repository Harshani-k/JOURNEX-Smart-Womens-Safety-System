from app.config import config_by_name, DevelopmentConfig, TestingConfig, ProductionConfig

def test_development_config():
    config = config_by_name["development"]
    assert config.DEBUG is True
    assert config.TESTING is False
    assert "sqlite" in config.SQLALCHEMY_DATABASE_URI

def test_testing_config():
    config = config_by_name["testing"]
    assert config.DEBUG is True
    assert config.TESTING is True
    assert config.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"

def test_production_config():
    config = config_by_name["production"]
    assert config.DEBUG is False
    assert config.TESTING is False
