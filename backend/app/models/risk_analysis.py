import json
from datetime import datetime, timezone
from app.extensions import db

VALID_RISK_CATEGORIES = ("LOW", "MODERATE", "HIGH", "CRITICAL")

class RiskAnalysis(db.Model):
    """
    RiskAnalysis entity representing machine learning risk assessment evaluations
    for active journeys. Stores risk probability scores, categorical classifications,
    feature snapshots, model metadata, and explainability factors.
    """
    __tablename__ = "risk_analyses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    journey_id = db.Column(
        db.Integer,
        db.ForeignKey("journeys.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Quantitative Risk Assessment
    risk_score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    risk_category = db.Column(db.String(20), nullable=False, index=True)  # LOW, MODERATE, HIGH, CRITICAL
    
    # Explainability & Contributing Factors (stored as JSON array or text)
    contributing_factors = db.Column(db.JSON, nullable=False)
    
    # Feature snapshot at the moment of inference (for auditability and reproducibility)
    feature_snapshot = db.Column(db.JSON, nullable=True)
    
    # Model provenance
    model_version = db.Column(db.String(30), nullable=False, default="1.0.0-rf")
    
    # Timestamps
    analyzed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        db.Index("ix_risk_analyses_journey_analyzed", "journey_id", "analyzed_at"),
        db.Index("ix_risk_analyses_user_category", "user_id", "risk_category"),
    )

    journey = db.relationship("Journey", backref=db.backref("risk_analyses", cascade="all, delete-orphan", lazy="dynamic"))
    user = db.relationship("User", backref=db.backref("risk_analyses", cascade="all, delete-orphan", lazy="dynamic"))

    def to_dict(self) -> dict:
        """Safe serialization of RiskAnalysis for API responses."""
        factors = self.contributing_factors
        if isinstance(factors, str):
            try:
                factors = json.loads(factors)
            except Exception:
                factors = [factors]
                
        snapshot = self.feature_snapshot
        if isinstance(snapshot, str):
            try:
                snapshot = json.loads(snapshot)
            except Exception:
                snapshot = {}

        return {
            "id": self.id,
            "journey_id": self.journey_id,
            "user_id": self.user_id,
            "risk_score": round(self.risk_score, 4),
            "risk_category": self.risk_category,
            "contributing_factors": factors,
            "feature_snapshot": snapshot,
            "model_version": self.model_version,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
