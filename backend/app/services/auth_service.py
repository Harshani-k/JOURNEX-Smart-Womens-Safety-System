import logging
from datetime import datetime, timezone
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db
from app.models.user import User
from app.models.token_blocklist import TokenBlocklist
from app.utils.exceptions import ConflictException, UnauthorizedException, NotFoundException

logger = logging.getLogger(__name__)

class AuthService:
    """Business logic for User Registration, Authentication, and Session Lifecycle."""

    @staticmethod
    def register_user(data: dict) -> dict:
        """Register a new user account with unique email and password hash."""
        email = data["email"]
        existing = User.query.filter_by(email=email).first()
        if existing:
            logger.warning("Registration attempt with existing email: %s", email)
            raise ConflictException(f"An account with email '{email}' already exists.")

        user = User(
            full_name=data["full_name"],
            email=email,
            phone_number=data["phone_number"]
        )
        user.set_password(data["password"])

        db.session.add(user)
        db.session.commit()
        logger.info("New user registered successfully: id=%d", user.id)

        # Generate access and refresh tokens
        identity_str = str(user.id)
        access_token = create_access_token(identity=identity_str)
        refresh_token = create_refresh_token(identity=identity_str)

        return {
            "user": user.to_dict(),
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer"
            }
        }

    @staticmethod
    def authenticate_user(email: str, password: str) -> dict:
        """Authenticate user credentials and issue fresh JWT session tokens."""
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            logger.warning("Failed login attempt for email: %s", email)
            raise UnauthorizedException("Invalid email or password.")

        if not user.is_active:
            logger.warning("Login attempt on deactivated user: id=%d", user.id)
            raise UnauthorizedException("Account is currently inactive. Contact support.")

        identity_str = str(user.id)
        access_token = create_access_token(identity=identity_str)
        refresh_token = create_refresh_token(identity=identity_str)

        logger.info("User authenticated successfully: id=%d", user.id)
        return {
            "user": user.to_dict(),
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer"
            }
        }

    @staticmethod
    def refresh_access_token(identity: str) -> dict:
        """Issue a new access token using a valid refresh token identity."""
        user = db.session.get(User, int(identity))
        if not user or not user.is_active:
            raise UnauthorizedException("User session is invalid or user no longer exists.")

        new_access_token = create_access_token(identity=str(user.id))
        return {
            "access_token": new_access_token,
            "token_type": "Bearer"
        }

    @staticmethod
    def get_user_profile(user_id: int) -> dict:
        """Fetch sanitized user profile for authenticated user."""
        user = db.session.get(User, user_id)
        if not user:
            raise NotFoundException("User profile not found.")
        return user.to_dict()

    @staticmethod
    def revoke_token(jwt_payload: dict) -> None:
        """Add token jti to revocation blocklist."""
        jti = jwt_payload.get("jti")
        token_type = jwt_payload.get("type", "access")
        exp_timestamp = jwt_payload.get("exp")
        user_identity = jwt_payload.get("sub")

        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) if exp_timestamp else datetime.now(timezone.utc)
        user_id = int(user_identity) if user_identity and str(user_identity).isdigit() else None

        blocklist_entry = TokenBlocklist(
            jti=jti,
            token_type=token_type,
            user_id=user_id,
            expires_at=expires_at
        )
        db.session.add(blocklist_entry)
        db.session.commit()
        logger.info("Token revoked successfully: jti=%s type=%s", jti, token_type)
