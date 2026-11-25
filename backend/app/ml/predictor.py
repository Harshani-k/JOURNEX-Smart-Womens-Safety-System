"""
JOURNEX – ML Risk Predictor & Explainability Engine
Phase 7: Explainable ML Risk Analysis

Loads the trained Random Forest classifier, extracts non-PII journey telemetry features,
infers quantitative risk score and category, and generates human-readable explainability
factors.
"""

import os
import json
import math
import joblib
import numpy as np
from datetime import datetime, timezone

from app.models.journey import Journey
from app.models.journey_location import JourneyLocation
from app.models.checkin import CheckIn
from app.models.safety_event import SafetyEvent
from app.ml.dataset_generator import (
    FEATURE_NAMES,
    RISK_LABELS,
    LABEL_MAP,
    REV_LABEL_MAP
)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in meters."""
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return 2.0 * R * math.asin(math.sqrt(max(0.0, min(1.0, a))))

class RiskPredictor:
    """
    Singleton inference and explainability engine for journey risk analysis.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RiskPredictor, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        model_path = os.path.join(MODELS_DIR, "risk_model.joblib")
        features_path = os.path.join(MODELS_DIR, "feature_names.json")
        meta_path = os.path.join(MODELS_DIR, "model_meta.json")

        self.model_version = "1.0.0-rf"
        self.model = None
        self.feature_names = FEATURE_NAMES

        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
            except Exception as e:
                self.model = None

        if os.path.exists(features_path):
            try:
                with open(features_path, "r") as f:
                    self.feature_names = json.load(f)
            except Exception:
                pass

        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    self.model_version = meta.get("model_version", self.model_version)
            except Exception:
                pass

    def reload(self):
        """Force reload model artifacts from disk."""
        self._initialize()

    def extract_features(self, journey: Journey) -> tuple[dict, bool]:
        """
        Extract non-PII journey telemetry features from database records.
        Returns: (features_dict, is_insufficient_data)
        """
        locations = JourneyLocation.query.filter_by(journey_id=journey.id).order_by(JourneyLocation.recorded_at.desc()).limit(20).all()
        checkins = CheckIn.query.filter_by(journey_id=journey.id).all()
        safety_events = SafetyEvent.query.filter_by(journey_id=journey.id).all()

        # Check for insufficient data: no locations and no check-ins recorded
        if len(locations) < 2 and len(checkins) == 0 and len(safety_events) == 0:
            # Baseline placeholder features
            return {
                "missed_checkins_count": 0,
                "pending_checkins_count": 0,
                "is_delayed": 1 if journey.is_delayed else 0,
                "delay_minutes": 0.0,
                "route_deviation_count": 0,
                "max_deviation_distance": 0.0,
                "unexpected_stop_count": 0,
                "max_stop_duration_seconds": 0.0,
                "avg_gps_accuracy": 10.0,
                "journey_progress_pct": 0.0,
                "is_night_journey": 0
            }, True

        # 1. Missed & Pending check-ins
        missed_count = sum(1 for c in checkins if c.status == "MISSED")
        pending_count = sum(1 for c in checkins if c.status in ("SCHEDULED", "REMINDED"))

        # 2. Delay tracking
        is_delayed = 1 if journey.is_delayed else 0
        delay_minutes = 0.0
        now_utc = datetime.now(timezone.utc)
        if journey.expected_arrival_time:
            exp_time = journey.expected_arrival_time
            if exp_time.tzinfo is None:
                exp_time = exp_time.replace(tzinfo=timezone.utc)
            if now_utc > exp_time:
                diff_sec = (now_utc - exp_time).total_seconds()
                delay_minutes = round(max(0.0, diff_sec / 60.0), 1)

        # 3. Route deviations
        dev_events = [e for e in safety_events if e.event_type == "ROUTE_DEVIATION"]
        route_dev_count = len(dev_events)
        max_dev_dist = max([e.deviation_distance or 0.0 for e in dev_events], default=0.0)

        # 4. Unexpected stops
        stop_events = [e for e in safety_events if e.event_type == "UNEXPECTED_STOP"]
        unexp_stop_count = len(stop_events)
        max_stop_dur = max([float(e.duration_seconds or 0) for e in stop_events], default=0.0)

        # 5. GPS accuracy
        if locations:
            accuracies = [loc.accuracy for loc in locations if loc.accuracy is not None]
            avg_acc = float(np.mean(accuracies)) if accuracies else 15.0
        else:
            avg_acc = 15.0

        # 6. Journey progress percentage
        progress_pct = 0.0
        if (journey.start_latitude and journey.start_longitude and
            journey.destination_latitude and journey.destination_longitude and locations):
            total_dist = haversine_meters(
                journey.start_latitude, journey.start_longitude,
                journey.destination_latitude, journey.destination_longitude
            )
            latest_loc = locations[0]
            dist_to_dest = haversine_meters(
                latest_loc.latitude, latest_loc.longitude,
                journey.destination_latitude, journey.destination_longitude
            )
            if total_dist > 50.0:
                progress_pct = round(max(0.0, min(100.0, (1.0 - (dist_to_dest / total_dist)) * 100.0)), 1)

        # 7. Night journey indicator (between 22:00 and 06:00)
        hour = now_utc.hour
        is_night = 1 if (hour >= 22 or hour < 6) else 0

        features = {
            "missed_checkins_count": missed_count,
            "pending_checkins_count": pending_count,
            "is_delayed": is_delayed,
            "delay_minutes": float(delay_minutes),
            "route_deviation_count": route_dev_count,
            "max_deviation_distance": float(max_dev_dist),
            "unexpected_stop_count": unexp_stop_count,
            "max_stop_duration_seconds": float(max_stop_dur),
            "avg_gps_accuracy": round(avg_acc, 2),
            "journey_progress_pct": float(progress_pct),
            "is_night_journey": is_night
        }

        return features, False

    def predict(self, journey: Journey) -> dict:
        """
        Execute risk analysis pipeline on the given journey.
        """
        features, is_insufficient = self.extract_features(journey)

        if is_insufficient:
            return {
                "risk_score": 0.05,
                "risk_category": "LOW",
                "probabilities": {"LOW": 1.0, "MODERATE": 0.0, "HIGH": 0.0, "CRITICAL": 0.0},
                "contributing_factors": [
                    {
                        "factor": "Insufficient Telemetry",
                        "impact": "NEUTRAL",
                        "description": "Journey recently initiated; insufficient GPS and check-in history to assess risk."
                    }
                ],
                "feature_snapshot": features,
                "is_insufficient_data": True,
                "model_version": self.model_version
            }

        # Format input vector
        vector = np.array([[features[k] for k in self.feature_names]], dtype=np.float32)

        # Model inference
        if self.model is not None:
            proba = self.model.predict_proba(vector)[0]
            # Probabilities ordered by classes: 0=LOW, 1=MODERATE, 2=HIGH, 3=CRITICAL
            p_low = float(proba[0]) if len(proba) > 0 else 1.0
            p_mod = float(proba[1]) if len(proba) > 1 else 0.0
            p_high = float(proba[2]) if len(proba) > 2 else 0.0
            p_crit = float(proba[3]) if len(proba) > 3 else 0.0
        else:
            # Fallback heuristic calculation if model file is missing
            p_crit = 0.9 if features["missed_checkins_count"] > 0 and features["route_deviation_count"] > 0 else 0.0
            p_high = 0.8 if features["route_deviation_count"] > 0 or features["unexpected_stop_count"] > 0 else 0.0
            p_mod = 0.5 if features["is_delayed"] == 1 or features["pending_checkins_count"] > 0 else 0.0
            p_low = max(0.0, 1.0 - (p_crit + p_high + p_mod))

        # Calculate continuous weighted risk score (0.0 to 1.0)
        raw_score = 0.05 * p_low + 0.40 * p_mod + 0.70 * p_high + 0.95 * p_crit
        risk_score = round(max(0.0, min(1.0, raw_score)), 4)

        # Categorical threshold mapping
        if risk_score < 0.30:
            category = "LOW"
        elif risk_score < 0.55:
            category = "MODERATE"
        elif risk_score < 0.80:
            category = "HIGH"
        else:
            category = "CRITICAL"

        # Explainability & Contributing Factors
        factors = []
        if features["missed_checkins_count"] > 0:
            factors.append({
                "factor": "Missed Safety Check-In",
                "impact": "CRITICAL",
                "description": f"{features['missed_checkins_count']} safety check-in(s) missed without confirmation."
            })

        if features["route_deviation_count"] > 0 and features["max_deviation_distance"] > 250.0:
            factors.append({
                "factor": "Route Deviation Detected",
                "impact": "HIGH",
                "description": f"Vehicle diverted {int(features['max_deviation_distance'])}m from planned corridor."
            })

        if features["unexpected_stop_count"] > 0 and features["max_stop_duration_seconds"] >= 600.0:
            stop_mins = int(features["max_stop_duration_seconds"] / 60.0)
            factors.append({
                "factor": "Prolonged Unexpected Stop",
                "impact": "HIGH",
                "description": f"Stationary stop for {stop_mins} minutes away from destination."
            })

        if features["is_delayed"] == 1 and features["delay_minutes"] >= 10.0:
            factors.append({
                "factor": "Journey Schedule Delay",
                "impact": "MODERATE",
                "description": f"Travel delayed by {int(features['delay_minutes'])} minutes past estimated arrival time."
            })

        if features["pending_checkins_count"] > 0:
            factors.append({
                "factor": "Pending Check-In Acknowledgment",
                "impact": "MODERATE",
                "description": f"{features['pending_checkins_count']} check-in awaiting traveler confirmation."
            })

        if features["avg_gps_accuracy"] > 50.0:
            factors.append({
                "factor": "Degraded GPS Reception",
                "impact": "LOW",
                "description": f"Average GPS horizontal error elevated ({features['avg_gps_accuracy']:.1f}m)."
            })

        if features["is_night_journey"] == 1:
            factors.append({
                "factor": "Nighttime Travel Period",
                "impact": "LOW",
                "description": "Journey conducted during nighttime hours (10:00 PM – 6:00 AM)."
            })

        if not factors:
            factors.append({
                "factor": "Normal Route Adherence",
                "impact": "POSITIVE",
                "description": "Traveler is within planned corridor with prompt check-in responses."
            })

        return {
            "risk_score": risk_score,
            "risk_category": category,
            "probabilities": {
                "LOW": round(p_low, 4),
                "MODERATE": round(p_mod, 4),
                "HIGH": round(p_high, 4),
                "CRITICAL": round(p_crit, 4)
            },
            "contributing_factors": factors,
            "feature_snapshot": features,
            "is_insufficient_data": False,
            "model_version": self.model_version
        }

risk_predictor = RiskPredictor()
