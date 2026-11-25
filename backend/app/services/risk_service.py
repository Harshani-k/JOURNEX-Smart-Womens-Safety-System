"""
JOURNEX – Risk Analysis Service
Phase 7: Explainable ML Risk Analysis

Orchestrates on-demand and telemetry-driven risk inference, database persistence,
history retrieval, and journey ownership validation.
"""

from datetime import datetime, timezone
from app.extensions import db
from app.models.journey import Journey
from app.models.journey_location import JourneyLocation
from app.models.safety_event import SafetyEvent
from app.models.risk_analysis import RiskAnalysis
from app.ml.predictor import risk_predictor
from app.utils.exceptions import NotFoundException, ForbiddenException

def evaluate_journey_risk(journey_id: int, user_id: int, force_recompute: bool = False) -> RiskAnalysis:
    """
    Execute machine learning risk evaluation for an active journey.
    Guarantees user ownership, avoids redundant inferences when data is identical,
    and commits a persistent RiskAnalysis record.
    """
    journey = Journey.query.filter_by(id=journey_id).first()
    if not journey:
        raise NotFoundException("Journey not found.")

    if journey.user_id != user_id:
        raise ForbiddenException("You do not have permission to analyze this journey.")

    now_utc = datetime.now(timezone.utc)

    # Check for recent analysis to avoid redundant computation
    latest = RiskAnalysis.query.filter_by(journey_id=journey.id).order_by(RiskAnalysis.analyzed_at.desc()).first()
    if latest and not force_recompute:
        latest_analyzed = latest.analyzed_at
        if latest_analyzed.tzinfo is None:
            latest_analyzed = latest_analyzed.replace(tzinfo=timezone.utc)

        # Check time elapsed since last inference
        elapsed_sec = (now_utc - latest_analyzed).total_seconds()
        if elapsed_sec < 60:
            # Check if any new location or safety event occurred since last analysis
            latest_loc = JourneyLocation.query.filter_by(journey_id=journey.id).order_by(JourneyLocation.recorded_at.desc()).first()
            latest_event = SafetyEvent.query.filter_by(journey_id=journey.id).order_by(SafetyEvent.detected_at.desc()).first()

            has_new_loc = latest_loc and latest_loc.recorded_at and latest_loc.recorded_at.replace(tzinfo=timezone.utc if latest_loc.recorded_at.tzinfo is None else latest_loc.recorded_at.tzinfo) > latest_analyzed
            has_new_event = latest_event and latest_event.detected_at and latest_event.detected_at.replace(tzinfo=timezone.utc if latest_event.detected_at.tzinfo is None else latest_event.detected_at.tzinfo) > latest_analyzed

            if not has_new_loc and not has_new_event:
                return latest

    # Run ML prediction
    prediction = risk_predictor.predict(journey)

    analysis = RiskAnalysis(
        journey_id=journey.id,
        user_id=user_id,
        risk_score=prediction["risk_score"],
        risk_category=prediction["risk_category"],
        contributing_factors=prediction["contributing_factors"],
        feature_snapshot=prediction["feature_snapshot"],
        model_version=prediction["model_version"],
        analyzed_at=now_utc
    )

    db.session.add(analysis)
    db.session.commit()
    return analysis

def get_latest_risk_analysis(journey_id: int, user_id: int) -> RiskAnalysis | None:
    """
    Retrieve the most recent risk analysis record for a journey.
    If none exists and journey is active, triggers initial baseline analysis.
    """
    journey = Journey.query.filter_by(id=journey_id).first()
    if not journey:
        raise NotFoundException("Journey not found.")

    if journey.user_id != user_id:
        raise ForbiddenException("You do not have permission to view risk analysis for this journey.")

    latest = RiskAnalysis.query.filter_by(journey_id=journey.id).order_by(RiskAnalysis.analyzed_at.desc()).first()
    if not latest and journey.status == "ACTIVE":
        latest = evaluate_journey_risk(journey_id, user_id)

    return latest

def get_risk_analysis_history(journey_id: int, user_id: int, limit: int = 20) -> list[RiskAnalysis]:
    """
    Retrieve chronological history of risk analyses for a journey.
    """
    journey = Journey.query.filter_by(id=journey_id).first()
    if not journey:
        raise NotFoundException("Journey not found.")

    if journey.user_id != user_id:
        raise ForbiddenException("You do not have permission to view risk history for this journey.")

    return RiskAnalysis.query.filter_by(journey_id=journey.id).order_by(RiskAnalysis.analyzed_at.desc()).limit(limit).all()
