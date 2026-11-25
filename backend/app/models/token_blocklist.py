from datetime import datetime, timezone
from app.extensions import db

class TokenBlocklist(db.Model):
    """
    Revoked and invalidated JWT tokens for proactive logout and revocation.
    """
    __tablename__ = "token_blocklist"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    token_type = db.Column(db.String(10), nullable=False)  # 'access' or 'refresh'
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<TokenBlocklist jti='{self.jti}' type='{self.token_type}'>"
