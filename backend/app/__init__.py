import os
import logging
from pathlib import Path
from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, cors, jwt, limiter
from app.utils.errors import register_error_handlers
from app.utils.response import api_response
from app.models.token_blocklist import TokenBlocklist
from app.models.user import User
from app.routes.health import health_bp
from app.routes.auth import auth_bp
from app.routes.profile import profile_bp
from app.routes.contacts import contacts_bp
from app.routes.journeys import journeys_bp
from app.routes.checkins import checkins_bp
from app.routes.emergency import emergency_bp

def create_app(config_name=None):
    """
    Flask Application Factory.
    Initializes configuration, database, migrations, CORS, JWT, rate limiter,
    error handlers, and REST API blueprints.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    config_class = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_class)
    app.config["ENV"] = config_name

    # Ensure instance folder exists for SQLite storage
    try:
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config.get("LOG_LEVEL", "INFO")),
        format="%(asctime)s [%(levelname)s] in %(module)s: %(message)s"
    )

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    limiter.init_app(app)
    jwt.init_app(app)

    # Configure JWT callbacks for blocklist and custom error envelopes
    _setup_jwt_callbacks(jwt)

    # Register centralized error handlers
    register_error_handlers(app)

    # Register Blueprints with /api/v1 version prefix
    api_prefix = f"/api/{app.config.get('API_VERSION', 'v1')}"
    app.register_blueprint(health_bp, url_prefix=api_prefix)
    app.register_blueprint(auth_bp, url_prefix=f"{api_prefix}/auth")
    app.register_blueprint(profile_bp, url_prefix=f"{api_prefix}/profile")
    app.register_blueprint(contacts_bp, url_prefix=f"{api_prefix}/contacts")
    app.register_blueprint(journeys_bp, url_prefix=f"{api_prefix}/journeys")
    app.register_blueprint(checkins_bp, url_prefix=f"{api_prefix}/checkins")
    app.register_blueprint(emergency_bp, url_prefix=f"{api_prefix}/emergency-events")

    return app

def _setup_jwt_callbacks(jwt_manager):
    """Register token revocation checking and standardized JSON error callbacks for JWT."""

    @jwt_manager.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_payload: dict):
        jti = jwt_payload.get("jti")
        token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
        return token is not None

    @jwt_manager.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data: dict):
        identity = jwt_data.get("sub")
        if not identity or not str(identity).isdigit():
            return None
        return db.session.get(User, int(identity))

    @jwt_manager.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_payload):
        return api_response(
            data=None,
            message="Token has expired. Please log in or refresh your session.",
            status_code=401,
            success=False,
            errors={"code": "TOKEN_EXPIRED", "description": "The JWT token has expired."}
        )

    @jwt_manager.invalid_token_loader
    def invalid_token_callback(error_str):
        return api_response(
            data=None,
            message="Invalid token signature or formatting.",
            status_code=401,
            success=False,
            errors={"code": "TOKEN_INVALID", "description": str(error_str)}
        )

    @jwt_manager.unauthorized_loader
    def missing_token_callback(error_str):
        return api_response(
            data=None,
            message="Authorization token is required to access this resource.",
            status_code=401,
            success=False,
            errors={"code": "AUTHORIZATION_REQUIRED", "description": str(error_str)}
        )

    @jwt_manager.revoked_token_loader
    def revoked_token_callback(_jwt_header, _jwt_payload):
        return api_response(
            data=None,
            message="Token has been revoked. Session is terminated.",
            status_code=401,
            success=False,
            errors={"code": "TOKEN_REVOKED", "description": "The token is in the revocation blocklist."}
        )
